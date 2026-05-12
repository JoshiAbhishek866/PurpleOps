"""
Main Orchestrator
Coordinates all 13 security agents and integrations
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from src.core.database import Database
from src.core.n8n_client import N8NClient
from src.core.llm_client import LLMClient

# Import all offensive agents
from src.agents.offensive import (
    ReconAgent,
    ScannerAgent,
    VulnAgent,
    CredentialTestingAgent,
    ReportGeneratorAgent
)

# Import all defensive agents
from src.agents.defensive import (
    ThreatDetectionAgent,
    HardeningAgent,
    VulnPrioritizationAgent,
    IncidentResponseAgent,
    ComplianceCheckAgent
)

# Import core agents
from src.agents.core import (
    SandboxManagerAgent,
    DashboardReporterAgent
)

from src.utils.logger import setup_logger
from src.utils.helpers import generate_id

logger = setup_logger(__name__)


class AgentOrchestrator:
    """
    Main Orchestrator for Sentinel AI Multi-Agent System
    
    Manages all 13 agents:
    - 5 Offensive Agents
    - 5 Defensive Agents
    - 3 Core Infrastructure Agents
    
    Responsibilities:
    - Agent lifecycle management
    - Workflow coordination
    - n8n integration
    - LLM enhancement
    - Database persistence
    - Real-time updates
    """
    
    def __init__(
        self,
        database: Database,
        n8n_client: N8NClient,
        llm_client: LLMClient,
        hook_provider=None
    ):
        self.db = database
        self.n8n = n8n_client
        self.llm = llm_client
        self.hook_provider = hook_provider
        
        # Initialize agents
        self.agents = {}
        self.execution_queue = asyncio.Queue()
        self.active_executions = {}
        
        logger.info("Agent Orchestrator initialized")
    
    async def initialize(self):
        """Initialize all 13 agents"""
        logger.info("Initializing all agents...")
        
        # Load configurations from database
        configs = {}
        agent_types = [
            "recon", "scanner", "vuln", "credential_testing", "report_generator",
            "threat_detection", "hardening", "vuln_prioritization", 
            "incident_response", "compliance_check",
            "sandbox_manager", "dashboard_reporter"
        ]
        
        for agent_type in agent_types:
            configs[agent_type] = await self.db.get_agent_config(agent_type) or {}
        
        # Initialize offensive agents
        self.agents["recon"] = ReconAgent(configs["recon"])
        self.agents["scanner"] = ScannerAgent(configs["scanner"])
        self.agents["vuln"] = VulnAgent(configs["vuln"])
        self.agents["credential_testing"] = CredentialTestingAgent(configs["credential_testing"])
        self.agents["report_generator"] = ReportGeneratorAgent(configs["report_generator"])
        
        # Initialize defensive agents
        self.agents["threat_detection"] = ThreatDetectionAgent(configs["threat_detection"])
        self.agents["hardening"] = HardeningAgent(configs["hardening"])
        self.agents["vuln_prioritization"] = VulnPrioritizationAgent(configs["vuln_prioritization"])
        self.agents["incident_response"] = IncidentResponseAgent(configs["incident_response"])
        self.agents["compliance_check"] = ComplianceCheckAgent(configs["compliance_check"])
        
        # Initialize core infrastructure agents
        self.agents["sandbox_manager"] = SandboxManagerAgent(configs["sandbox_manager"])
        self.agents["dashboard_reporter"] = DashboardReporterAgent(configs["dashboard_reporter"])
        
        logger.info(f"✅ Initialized {len(self.agents)} agents (5 offensive, 5 defensive, 3 core)")
    
    async def execute_agent(
        self,
        agent_type: str,
        target: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """Execute a specific agent with lifecycle hook integration"""
        if agent_type not in self.agents:
            logger.error(f"Unknown agent type: {agent_type}")
            return {"error": f"Unknown agent: {agent_type}"}
        
        execution_id = generate_id("exec")
        
        logger.info(f"🚀 Starting {agent_type} execution: {execution_id}")
        
        # Save execution record
        execution_record = {
            "execution_id": execution_id,
            "agent_type": agent_type,
            "target": target,
            "status": "running",
            "started_at": datetime.utcnow()
        }
        
        await self.db.save_execution(execution_record)
        self.active_executions[execution_id] = execution_record
        
        try:
            # --- Pre-execution hook: load context ---
            extra_context = None
            if self.hook_provider:
                try:
                    from src.core.hooks import AgentInitEvent
                    event = AgentInitEvent(
                        agent_type=agent_type,
                        target=target,
                        campaign_id=execution_id,
                        actor_id="orchestrator",
                        session_id=execution_id,
                    )
                    extra_context = await self.hook_provider.on_agent_init(event)
                except Exception as e:
                    logger.warning(f"Pre-execution hook failed: {e}")
            
            # Execute agent
            agent = self.agents[agent_type]
            result = await agent.run(target, options)
            
            # --- Post-execution hook: persist + enrich ---
            if self.hook_provider:
                try:
                    from src.core.hooks import AgentCompleteEvent
                    event = AgentCompleteEvent(
                        agent_type=agent_type,
                        target=target,
                        campaign_id=execution_id,
                        actor_id="orchestrator",
                        result=result,
                        status=result.get("status", "unknown"),
                    )
                    await self.hook_provider.on_agent_complete(event)
                except Exception as e:
                    logger.warning(f"Post-execution hook failed: {e}")
            
            # Send to n8n for workflow processing (fallback if hooks not present)
            if not self.hook_provider and result.get("status") == "success":
                n8n_result = await self.n8n.trigger_agent_workflow(
                    agent_type, target, result
                )
                result["n8n_processing"] = n8n_result
            
            # Get LLM insights (fallback if hooks not present)
            if not self.hook_provider and agent_type not in ["report_generator", "dashboard_reporter"]:
                llm_analysis = await self.llm.analyze_scan_results(agent_type, result)
                result["llm_insights"] = llm_analysis
            
            # Save result to database
            result_id = await self.db.save_result(result)
            result["result_id"] = result_id
            
            # Update execution record
            await self.db.update_execution(execution_id, {
                "status": "completed",
                "result_id": result_id,
                "completed_at": datetime.utcnow()
            })
            
            logger.info(f"✅ {agent_type} execution completed: {execution_id}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ {agent_type} execution failed: {e}")
            
            await self.db.update_execution(execution_id, {
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow()
            })
            
            return {
                "error": str(e),
                "status": "failed",
                "execution_id": execution_id
            }
        
        finally:
            self.active_executions.pop(execution_id, None)
    
    async def execute_workflow(
        self,
        workflow_name: str,
        target: str,
        options: Optional[Dict] = None
    ) -> Dict:
        """
        Execute a predefined workflow (chain of agents)
        
        Available workflows:
        - full_scan: Recon → Scanner → Vuln
        - quick_scan: Recon → Scanner
        - security_audit: Recon → Scanner → Vuln → Hardening
        - complete_assessment: All offensive + defensive agents
        - compliance_audit: Compliance Check → Report
        - threat_hunt: Threat Detection → Incident Response
        - credential_audit: Credential Testing → Report
        """
        logger.info(f"🔄 Executing workflow: {workflow_name} on {target}")
        
        workflows = {
            "full_scan": ["recon", "scanner", "vuln"],
            "quick_scan": ["recon", "scanner"],
            "vuln_only": ["vuln"],
            "security_audit": ["recon", "scanner", "vuln", "hardening"],
            "threat_monitoring": ["threat_detection"],
            "complete_assessment": [
                "recon", "scanner", "vuln", "credential_testing",
                "threat_detection", "hardening", "compliance_check"
            ],
            "compliance_audit": ["compliance_check"],
            "threat_hunt": ["threat_detection", "incident_response"],
            "credential_audit": ["credential_testing"],
            "full_defensive": ["threat_detection", "hardening", "compliance_check"]
        }
        
        if workflow_name not in workflows:
            return {"error": f"Unknown workflow: {workflow_name}"}
        
        agent_sequence = workflows[workflow_name]
        results = {}
        
        # Create sandbox if needed
        sandbox_id = None
        if options and options.get("use_sandbox", True):
            sandbox_result = await self.execute_agent(
                "sandbox_manager",
                target,
                {"operation": "create"}
            )
            sandbox_id = sandbox_result.get("data", {}).get("sandbox_id")
            logger.info(f"Created sandbox: {sandbox_id}")
        
        # Execute agents in sequence
        for agent_type in agent_sequence:
            logger.info(f"⏳ Running {agent_type} in workflow...")
            
            agent_options = options or {}
            
            if agent_type == "vuln" and "scanner" in results:
                agent_options["services"] = results["scanner"].get("data", {}).get("services", [])
            
            if agent_type == "vuln_prioritization" and "vuln" in results:
                agent_options["vulnerabilities"] = results["vuln"].get("data", {}).get("vulnerabilities", [])
            
            if agent_type == "incident_response":
                agent_options["findings"] = []
                agent_options["threats"] = results.get("threat_detection", {}).get("data", {}).get("threats_detected", [])
                agent_options["vulnerabilities"] = results.get("vuln", {}).get("data", {}).get("vulnerabilities", [])
            
            result = await self.execute_agent(agent_type, target, agent_options)
            results[agent_type] = result
            
            if result.get("status") == "failed":
                logger.warning(f"⚠️ Workflow stopped due to {agent_type} failure")
                break
        
        # Generate report if workflow completed successfully
        if all(r.get("status") == "success" for r in results.values()):
            report_result = await self.execute_agent(
                "report_generator",
                target,
                {"agent_results": results}
            )
            results["report"] = report_result
        
        # Generate dashboard data
        dashboard_result = await self.execute_agent(
            "dashboard_reporter",
            target,
            {"agent_results": results}
        )
        results["dashboard"] = dashboard_result
        
        # Cleanup sandbox
        if sandbox_id:
            await self.execute_agent(
                "sandbox_manager",
                target,
                {"operation": "destroy", "sandbox_id": sandbox_id}
            )
            logger.info(f"Destroyed sandbox: {sandbox_id}")
        
        combined = {
            "workflow": workflow_name,
            "target": target,
            "sandbox_id": sandbox_id,
            "results": results,
            "completed_agents": len(results),
            "total_agents": len(agent_sequence),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Workflow completed: {workflow_name}")
        
        return combined
    
    async def execute_concurrent(
        self,
        agent_type: str,
        targets: List[str],
        max_concurrent: int = 5
    ) -> List[Dict]:
        """Execute agent on multiple targets concurrently"""
        logger.info(f"🔄 Concurrent execution: {agent_type} on {len(targets)} targets")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(target):
            async with semaphore:
                return await self.execute_agent(agent_type, target)
        
        tasks = [execute_with_semaphore(target) for target in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = [r for r in results if isinstance(r, dict)]
        
        logger.info(f"✅ Concurrent execution completed: {len(valid_results)}/{len(targets)} successful")
        
        return valid_results
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        status = {
            "offensive_agents": {},
            "defensive_agents": {},
            "core_agents": {}
        }
        
        offensive = ["recon", "scanner", "vuln", "credential_testing", "report_generator"]
        defensive = ["threat_detection", "hardening", "vuln_prioritization", "incident_response", "compliance_check"]
        core = ["sandbox_manager", "dashboard_reporter"]
        
        for agent_type in offensive:
            if agent_type in self.agents:
                status["offensive_agents"][agent_type] = self.agents[agent_type].get_status()
        
        for agent_type in defensive:
            if agent_type in self.agents:
                status["defensive_agents"][agent_type] = self.agents[agent_type].get_status()
        
        for agent_type in core:
            if agent_type in self.agents:
                status["core_agents"][agent_type] = self.agents[agent_type].get_status()
        
        status["summary"] = {
            "total_agents": len(self.agents),
            "offensive": len(offensive),
            "defensive": len(defensive),
            "core": len(core),
            "active_executions": len(self.active_executions),
            "queue_size": self.execution_queue.qsize()
        }
        
        return status
    
    async def get_execution_history(
        self,
        agent_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get execution history"""
        return await self.db.get_execution_history(agent_type, limit)
    
    async def get_results_by_target(self, target: str) -> List[Dict]:
        """Get all results for a specific target"""
        return await self.db.get_results_by_target(target)
    
    async def update_agent_config(self, agent_type: str, config: Dict) -> bool:
        """Update agent configuration"""
        if agent_type not in self.agents:
            return False
        
        self.agents[agent_type].update_config(config)
        return await self.db.save_agent_config(agent_type, config)
    
    async def shutdown(self):
        """Shutdown orchestrator"""
        logger.info("🛑 Shutting down orchestrator...")
        
        if self.active_executions:
            logger.info(f"⏳ Waiting for {len(self.active_executions)} active executions...")
            await asyncio.sleep(2)
        
        sandbox_result = await self.execute_agent(
            "sandbox_manager",
            "cleanup",
            {"operation": "cleanup"}
        )
        
        logger.info("✅ Orchestrator shutdown complete")
    
    async def get_statistics(self) -> Dict:
        """Get orchestrator statistics"""
        db_stats = await self.db.get_stats()
        
        stats = {
            **db_stats,
            "agents": {
                "total": len(self.agents),
                "offensive": 5,
                "defensive": 5,
                "core": 3,
                "types": list(self.agents.keys())
            },
            "executions": {
                "active": len(self.active_executions),
                "queued": self.execution_queue.qsize()
            },
            "capabilities": {
                "offensive": [
                    "Reconnaissance",
                    "Port Scanning",
                    "Vulnerability Detection",
                    "Credential Testing",
                    "Report Generation"
                ],
                "defensive": [
                    "Threat Detection",
                    "System Hardening",
                    "Vulnerability Prioritization",
                    "Incident Response",
                    "Compliance Checking"
                ],
                "infrastructure": [
                    "Sandbox Management",
                    "Dashboard Reporting"
                ]
            }
        }
        
        return stats
