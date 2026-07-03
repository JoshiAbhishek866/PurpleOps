"""
Security Scanning Routes
Integrates with the PurpleOps agent orchestrator for security scans
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, List
import asyncio
import os
import uuid

from src.core.orchestrator import AgentOrchestrator
from src.core.database import Database
from src.core.n8n_client import N8NClient
from src.core.llm_client import LLMClient
from src.utils.auth_middleware import require_auth
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()

# Global orchestrator instance
orchestrator = None

# Track running scans so results are retrievable
_active_scans: Dict[str, Dict] = {}


class ScanRequest(BaseModel):
    workflow: str
    target: str
    options: Optional[Dict] = None


class ScanResponse(BaseModel):
    scan_id: str
    status: str
    message: str


async def get_orchestrator():
    """Get or initialize orchestrator"""
    global orchestrator
    
    if orchestrator is None:
        # Initialize database with correct parameter names
        db = Database(
            url=os.getenv("MONGO_URL", "mongodb://localhost:27017"),
            db_name=os.getenv("MONGO_DB", "purpleops")
        )
        await db.connect()
        
        # Initialize n8n client
        n8n = N8NClient(
            url=os.getenv("N8N_URL", "http://localhost:5678"),
            api_key=os.getenv("N8N_API_KEY", "")
        )
        
        # Initialize LLM client
        llm = LLMClient(
            provider="ollama",
            model=os.getenv("LLM_MODEL", "llama2"),
            url=os.getenv("LLM_URL", "http://localhost:11434")
        )
        
        # Create orchestrator
        orchestrator = AgentOrchestrator(db, n8n, llm)
        await orchestrator.initialize()
    
    return orchestrator


@router.post("/scan", response_model=ScanResponse)
async def start_scan(request: ScanRequest, user: dict = Depends(require_auth)):
    """
    Start a security scan
    
    Available workflows:
    - full_scan: Recon → Scanner → Vuln
    - quick_scan: Recon → Scanner
    - security_audit: Recon → Scanner → Vuln → Hardening
    - complete_assessment: All offensive + defensive agents
    - compliance_audit: Compliance checking
    - threat_hunt: Threat Detection → Incident Response
    - credential_audit: Credential testing
    """
    try:
        orch = await get_orchestrator()
        scan_id = str(uuid.uuid4())
        
        # Track scan state
        _active_scans[scan_id] = {
            "status": "running",
            "workflow": request.workflow,
            "target": request.target,
            "result": None,
            "error": None,
        }
        
        async def _run_scan():
            try:
                result = await orch.execute_workflow(
                    workflow_name=request.workflow,
                    target=request.target,
                    options=request.options
                )
                _active_scans[scan_id]["status"] = "completed"
                _active_scans[scan_id]["result"] = result
            except Exception as exc:
                logger.error(f"Scan {scan_id} failed: {exc}")
                _active_scans[scan_id]["status"] = "failed"
                _active_scans[scan_id]["error"] = str(exc)
        
        # Start scan in background (tracked)
        asyncio.create_task(_run_scan())
        
        return ScanResponse(
            scan_id=scan_id,
            status="started",
            message=f"Scan started for {request.target} using {request.workflow} workflow"
        )
    
    except Exception as e:
        logger.error(f"Failed to start scan: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scan")


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str, user: dict = Depends(require_auth)):
    """Get the status and result of a running/completed scan"""
    if scan_id not in _active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _active_scans[scan_id]


@router.get("/workflows")
async def get_workflows():
    """Get available scan workflows"""
    return {
        "workflows": [
            {
                "id": "full_scan",
                "name": "Full Scan",
                "description": "Complete offensive scan: Recon → Scanner → Vulnerability Detection",
                "agents": ["recon", "scanner", "vuln"],
                "duration": "10-15 minutes"
            },
            {
                "id": "quick_scan",
                "name": "Quick Scan",
                "description": "Fast reconnaissance and port scanning",
                "agents": ["recon", "scanner"],
                "duration": "5-7 minutes"
            },
            {
                "id": "security_audit",
                "name": "Security Audit",
                "description": "Offensive scan with hardening recommendations",
                "agents": ["recon", "scanner", "vuln", "hardening"],
                "duration": "15-20 minutes"
            },
            {
                "id": "complete_assessment",
                "name": "Complete Assessment",
                "description": "Full offensive and defensive security assessment",
                "agents": ["recon", "scanner", "vuln", "credential_testing", "threat_detection", "hardening", "compliance_check"],
                "duration": "20-30 minutes"
            },
            {
                "id": "compliance_audit",
                "name": "Compliance Audit",
                "description": "Check compliance with CIS, NIST, PCI-DSS",
                "agents": ["compliance_check"],
                "duration": "5-10 minutes"
            },
            {
                "id": "threat_hunt",
                "name": "Threat Hunt",
                "description": "Detect and respond to active threats",
                "agents": ["threat_detection", "incident_response"],
                "duration": "10-15 minutes"
            },
            {
                "id": "credential_audit",
                "name": "Credential Audit",
                "description": "Test for weak and default credentials",
                "agents": ["credential_testing"],
                "duration": "5-10 minutes"
            }
        ]
    }


@router.get("/agents/status")
async def get_agent_status(user: dict = Depends(require_auth)):
    """Get status of all agents"""
    try:
        orch = await get_orchestrator()
        return orch.get_agent_status()
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent status")


@router.get("/statistics")
async def get_statistics(user: dict = Depends(require_auth)):
    """Get orchestrator statistics"""
    try:
        orch = await get_orchestrator()
        return await orch.get_statistics()
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/history")
async def get_scan_history(
    agent_type: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(require_auth)
):
    """Get scan execution history"""
    try:
        orch = await get_orchestrator()
        history = await orch.get_execution_history(agent_type, limit)
        return history
    except Exception as e:
        logger.error(f"Failed to get scan history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scan history")


@router.get("/results/{result_id}")
async def get_scan_result(result_id: str, user: dict = Depends(require_auth)):
    """Get specific scan result by ID"""
    try:
        orch = await get_orchestrator()
        result = await orch.db.get_result(result_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scan result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scan result")


@router.get("/results/target/{target}")
async def get_results_by_target(target: str, user: dict = Depends(require_auth)):
    """Get all results for a specific target"""
    try:
        orch = await get_orchestrator()
        results = await orch.db.get_results_by_target(target)
        return results
    except Exception as e:
        logger.error(f"Failed to get results by target: {e}")
        raise HTTPException(status_code=500, detail="Failed to get results")
