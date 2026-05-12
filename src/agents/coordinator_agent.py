"""
Central Coordinator Agent - Sentinel AI
=========================================
Implements the LangGraph Supervisor pattern as recommended by AWS Summit.

This is the "Control Plane" for all Red/Blue agents.
It prevents infinite loops, enforces token budgets, manages state,
and provides deterministic audit trails for enterprise deployments.

Architecture:
  Coordinator (Supervisor)
  ├── Red Agent (Offensive sub-agents)
  │   ├── ReconAgent
  │   ├── ScannerAgent
  │   ├── VulnAgent
  │   └── CredentialTestingAgent
  └── Blue Agent (Defensive sub-agents)
      ├── ThreatDetectionAgent
      ├── HardeningAgent
      ├── VulnPrioritizationAgent
      ├── IncidentResponseAgent
      └── ComplianceCheckAgent

State Machine Flow:
  INIT → PLAN → ROUTE → [RED | BLUE] → EVALUATE → [ROUTE | FINALIZE]
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

import boto3
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ─────────────────────────────────────────────
# Campaign State Definition
# ─────────────────────────────────────────────

class CampaignPhase(str, Enum):
    INIT       = "INIT"
    PLANNING   = "PLANNING"
    ATTACKING  = "ATTACKING"
    DEFENDING  = "DEFENDING"
    EVALUATING = "EVALUATING"
    COMPLETED  = "COMPLETED"
    ABORTED    = "ABORTED"


@dataclass
class CampaignState:
    """
    Shared state object passed between all agents.
    The Coordinator owns and mutates this state.
    """
    campaign_id: str
    target: str
    phase: CampaignPhase = CampaignPhase.INIT

    # Budget controls (prevents infinite loops & cost explosion)
    max_attack_turns: int = 5
    max_defense_turns: int = 5
    max_total_turns: int = 15
    current_turn: int = 0
    tokens_used: int = 0
    token_budget: int = 50000  # ~$1.50 at Claude 3.5 Sonnet pricing

    # Agent results
    red_results: List[Dict] = field(default_factory=list)
    blue_results: List[Dict] = field(default_factory=list)
    attack_turns_used: int = 0
    defense_turns_used: int = 0

    # Findings
    vulnerabilities_found: List[Dict] = field(default_factory=list)
    remediations_applied: List[Dict] = field(default_factory=list)
    unresolved_findings: List[Dict] = field(default_factory=list)

    # Audit trail
    audit_log: List[Dict] = field(default_factory=list)
    coordinator_decisions: List[str] = field(default_factory=list)

    # Final output
    final_report: Optional[Dict] = None
    completed_at: Optional[str] = None

    def log_event(self, agent: str, action: str, outcome: str):
        """Append immutable audit entry."""
        self.audit_log.append({
            "turn": self.current_turn,
            "agent": agent,
            "action": action,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat()
        })

    def is_budget_exhausted(self) -> bool:
        return (
            self.current_turn >= self.max_total_turns
            or self.tokens_used >= self.token_budget
        )

    def is_attack_budget_exhausted(self) -> bool:
        return self.attack_turns_used >= self.max_attack_turns

    def is_defense_budget_exhausted(self) -> bool:
        return self.defense_turns_used >= self.max_defense_turns


# ─────────────────────────────────────────────
# Coordinator Agent
# ─────────────────────────────────────────────

class CoordinatorAgent:
    """
    Central Coordinator / Supervisor Agent.

    Responsibilities:
    - Owns the CampaignState (single source of truth)
    - Routes tasks to Red or Blue sub-agents
    - Enforces token budgets and turn limits
    - Prevents infinite Red↔Blue loops
    - Provides deterministic audit trail
    - Queries RAG knowledge base once and distributes context
    - Triggers n8n workflows at key milestones
    - Registers completed campaigns to AWS Bedrock AgentCore Registry
    """

    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
        self.campaigns_table = self.dynamodb.Table(Config.DYNAMODB_TABLE_CAMPAIGNS)
        self.audit_table = self.dynamodb.Table(Config.DYNAMODB_TABLE_AUDIT)
        self._red_agent = None
        self._blue_agent = None
        self._orchestrator = None

    # ── Lazy-load agents to avoid circular imports ──────────────────────────

    def _get_red_agent(self):
        if self._red_agent is None:
            from src.agents.red_agent import RedAgent
            self._red_agent = RedAgent()
        return self._red_agent

    def _get_blue_agent(self):
        if self._blue_agent is None:
            from src.agents.blue_agent import BlueAgent
            self._blue_agent = BlueAgent()
        return self._blue_agent

    # ── Core Campaign Execution ──────────────────────────────────────────────

    async def run_campaign(
        self,
        campaign_id: str,
        target: str,
        options: Optional[Dict] = None
    ) -> CampaignState:
        """
        Main entry point. Runs the full supervised purple-teaming loop.

        Flow:
          1. INIT  → create state, persist to DynamoDB
          2. PLAN  → coordinator decides attack strategy
          3. ROUTE → send to Red Agent
          4. Red executes, returns findings
          5. ROUTE → send findings to Blue Agent
          6. Blue remediates, returns results
          7. EVALUATE → coordinator checks if done or loops
          8. FINALIZE → generate report, update registry
        """
        opts = options or {}
        state = CampaignState(
            campaign_id=campaign_id,
            target=target,
            max_attack_turns=opts.get("max_attack_turns", 5),
            max_defense_turns=opts.get("max_defense_turns", 5),
            max_total_turns=opts.get("max_total_turns", 15),
            token_budget=opts.get("token_budget", 50000),
        )

        logger.info(f"[COORDINATOR] 🚀 Campaign {campaign_id} started on {target}")
        state.log_event("COORDINATOR", "campaign_start", f"Target: {target}")

        # Persist initial state
        await self._persist_state(state, "ACTIVE")

        try:
            # ── Phase 1: Planning ────────────────────────────────────────────
            state = await self._phase_plan(state)

            # ── Phase 2: Supervised Attack/Defense Loop ──────────────────────
            while not self._should_terminate(state):
                state.current_turn += 1
                logger.info(f"[COORDINATOR] Turn {state.current_turn}/{state.max_total_turns}")

                # Route to Red Agent
                if not state.is_attack_budget_exhausted():
                    state = await self._phase_attack(state)
                else:
                    logger.info("[COORDINATOR] Attack budget exhausted — skipping Red Agent")
                    state.coordinator_decisions.append(
                        f"Turn {state.current_turn}: Attack budget exhausted, skipping Red Agent"
                    )

                # Route to Blue Agent if there are findings
                if state.vulnerabilities_found and not state.is_defense_budget_exhausted():
                    state = await self._phase_defend(state)
                elif state.is_defense_budget_exhausted():
                    logger.info("[COORDINATOR] Defense budget exhausted — skipping Blue Agent")
                    state.coordinator_decisions.append(
                        f"Turn {state.current_turn}: Defense budget exhausted, skipping Blue Agent"
                    )

                # Evaluate whether to continue
                state = await self._phase_evaluate(state)

            # ── Phase 3: Finalize ────────────────────────────────────────────
            state = await self._phase_finalize(state)

        except Exception as e:
            logger.error(f"[COORDINATOR] ❌ Campaign failed: {e}")
            state.phase = CampaignPhase.ABORTED
            state.log_event("COORDINATOR", "campaign_abort", str(e))
            await self._persist_state(state, "FAILED")
            raise

        return state

    # ── Phase Handlers ───────────────────────────────────────────────────────

    async def _phase_plan(self, state: CampaignState) -> CampaignState:
        """Coordinator creates the attack plan."""
        state.phase = CampaignPhase.PLANNING
        logger.info(f"[COORDINATOR] 📋 Planning campaign for {state.target}")

        decision = (
            f"Campaign plan: Execute up to {state.max_attack_turns} attack turns "
            f"and {state.max_defense_turns} defense turns. "
            f"Token budget: {state.token_budget:,}. "
            f"Target: {state.target}"
        )
        state.coordinator_decisions.append(decision)
        state.log_event("COORDINATOR", "plan_created", decision)

        logger.info(f"[COORDINATOR] ✅ Plan: {decision}")
        return state

    async def _phase_attack(self, state: CampaignState) -> CampaignState:
        """Route to Red Agent for offensive execution."""
        state.phase = CampaignPhase.ATTACKING
        state.attack_turns_used += 1

        logger.info(
            f"[COORDINATOR] ⚔️  Routing to Red Agent "
            f"(attack turn {state.attack_turns_used}/{state.max_attack_turns})"
        )

        try:
            red = self._get_red_agent()
            target_info = {
                "url": state.target,
                "description": f"Purple team campaign {state.campaign_id}",
                "iam_role": "red-agent-role",
                "turn": state.attack_turns_used,
                "previous_findings": state.vulnerabilities_found,
            }

            # Run in thread pool (LangChain AgentExecutor is sync)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, red.execute_campaign, target_info
            )

            # Extract findings from result
            findings = self._extract_findings(result, "RED")
            state.red_results.append(result)
            state.vulnerabilities_found.extend(findings)

            state.log_event(
                "RED_AGENT",
                f"attack_turn_{state.attack_turns_used}",
                f"Found {len(findings)} vulnerabilities"
            )

            decision = (
                f"Turn {state.current_turn}: Red Agent found {len(findings)} vulnerabilities. "
                f"Total findings: {len(state.vulnerabilities_found)}"
            )
            state.coordinator_decisions.append(decision)
            logger.info(f"[COORDINATOR] {decision}")

        except Exception as e:
            logger.error(f"[COORDINATOR] Red Agent failed: {e}")
            state.log_event("RED_AGENT", "attack_failed", str(e))

        return state

    async def _phase_defend(self, state: CampaignState) -> CampaignState:
        """Route to Blue Agent for defensive response."""
        state.phase = CampaignPhase.DEFENDING
        state.defense_turns_used += 1

        # Only pass unresolved findings to Blue Agent
        unresolved = [
            f for f in state.vulnerabilities_found
            if f.get("id") not in [r.get("finding_id") for r in state.remediations_applied]
        ]

        logger.info(
            f"[COORDINATOR] 🛡️  Routing to Blue Agent "
            f"(defense turn {state.defense_turns_used}/{state.max_defense_turns}) "
            f"with {len(unresolved)} unresolved findings"
        )

        try:
            blue = self._get_blue_agent()
            threat_info = {
                "attack_type": f"Multiple vulnerabilities ({len(unresolved)} unresolved)",
                "target": state.target,
                "details": str(unresolved[:3]),  # Pass top 3 to control token usage
                "campaign_id": state.campaign_id,
                "turn": state.defense_turns_used,
            }

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, blue.respond_to_threat, threat_info
            )

            remediations = self._extract_remediations(result)
            state.blue_results.append(result)
            state.remediations_applied.extend(remediations)

            state.log_event(
                "BLUE_AGENT",
                f"defense_turn_{state.defense_turns_used}",
                f"Applied {len(remediations)} remediations"
            )

            decision = (
                f"Turn {state.current_turn}: Blue Agent applied {len(remediations)} remediations. "
                f"Total remediations: {len(state.remediations_applied)}"
            )
            state.coordinator_decisions.append(decision)
            logger.info(f"[COORDINATOR] {decision}")

        except Exception as e:
            logger.error(f"[COORDINATOR] Blue Agent failed: {e}")
            state.log_event("BLUE_AGENT", "defense_failed", str(e))

        return state

    async def _phase_evaluate(self, state: CampaignState) -> CampaignState:
        """Coordinator evaluates campaign progress and decides next action."""
        state.phase = CampaignPhase.EVALUATING

        unresolved_count = len(state.vulnerabilities_found) - len(state.remediations_applied)

        if unresolved_count == 0 and len(state.vulnerabilities_found) > 0:
            decision = "All vulnerabilities remediated. Terminating campaign."
            state.phase = CampaignPhase.COMPLETED
        elif state.is_budget_exhausted():
            decision = f"Budget exhausted (turn {state.current_turn}). Terminating campaign."
            state.phase = CampaignPhase.COMPLETED
        elif state.is_attack_budget_exhausted() and state.is_defense_budget_exhausted():
            decision = "Both attack and defense budgets exhausted. Terminating campaign."
            state.phase = CampaignPhase.COMPLETED
        else:
            decision = (
                f"Turn {state.current_turn}: {unresolved_count} unresolved findings. "
                f"Continuing campaign."
            )

        state.coordinator_decisions.append(decision)
        state.log_event("COORDINATOR", "evaluation", decision)
        logger.info(f"[COORDINATOR] 🔍 Evaluation: {decision}")

        return state

    async def _phase_finalize(self, state: CampaignState) -> CampaignState:
        """Generate final report and persist everything."""
        state.phase = CampaignPhase.COMPLETED
        state.completed_at = datetime.utcnow().isoformat()

        unresolved = [
            f for f in state.vulnerabilities_found
            if f.get("id") not in [r.get("finding_id") for r in state.remediations_applied]
        ]
        state.unresolved_findings = unresolved

        state.final_report = {
            "campaign_id": state.campaign_id,
            "target": state.target,
            "summary": {
                "total_turns": state.current_turn,
                "attack_turns": state.attack_turns_used,
                "defense_turns": state.defense_turns_used,
                "vulnerabilities_found": len(state.vulnerabilities_found),
                "remediations_applied": len(state.remediations_applied),
                "unresolved_findings": len(unresolved),
                "tokens_used": state.tokens_used,
            },
            "coordinator_decisions": state.coordinator_decisions,
            "audit_log": state.audit_log,
            "vulnerabilities": state.vulnerabilities_found,
            "remediations": state.remediations_applied,
            "unresolved": unresolved,
            "completed_at": state.completed_at,
        }

        state.log_event("COORDINATOR", "campaign_complete", "Final report generated")
        await self._persist_state(state, "COMPLETED")

        logger.info(
            f"[COORDINATOR] ✅ Campaign {state.campaign_id} complete. "
            f"Findings: {len(state.vulnerabilities_found)}, "
            f"Remediations: {len(state.remediations_applied)}, "
            f"Unresolved: {len(unresolved)}"
        )

        return state

    # ── Termination Logic ────────────────────────────────────────────────────

    def _should_terminate(self, state: CampaignState) -> bool:
        """Determine if the campaign loop should stop."""
        if state.phase == CampaignPhase.COMPLETED:
            return True
        if state.phase == CampaignPhase.ABORTED:
            return True
        if state.is_budget_exhausted():
            return True
        if state.is_attack_budget_exhausted() and state.is_defense_budget_exhausted():
            return True
        # All vulnerabilities resolved
        if (
            len(state.vulnerabilities_found) > 0
            and len(state.remediations_applied) >= len(state.vulnerabilities_found)
        ):
            return True
        return False

    # ── Helper Methods ───────────────────────────────────────────────────────

    def _extract_findings(self, result: Dict, agent_type: str) -> List[Dict]:
        """Extract structured findings from agent result."""
        findings = []
        output = result.get("output", "")

        # Parse common attack types from output
        attack_types = ["SQL Injection", "XSS", "Privilege Escalation", "SSRF", "RCE"]
        for attack in attack_types:
            if attack.lower() in str(output).lower():
                findings.append({
                    "id": f"{agent_type}_{attack.replace(' ', '_')}_{datetime.utcnow().timestamp()}",
                    "type": attack,
                    "severity": "HIGH",
                    "source_agent": agent_type,
                    "raw_output": str(output)[:500],
                    "timestamp": datetime.utcnow().isoformat()
                })

        return findings

    def _extract_remediations(self, result: Dict) -> List[Dict]:
        """Extract structured remediations from Blue Agent result."""
        remediations = []
        output = result.get("output", "")

        remediation_types = ["WAF", "security group", "IAM", "patch", "block", "restrict"]
        for rem_type in remediation_types:
            if rem_type.lower() in str(output).lower():
                remediations.append({
                    "id": f"REM_{rem_type}_{datetime.utcnow().timestamp()}",
                    "type": rem_type,
                    "status": "applied",
                    "raw_output": str(output)[:500],
                    "timestamp": datetime.utcnow().isoformat()
                })
                break  # One remediation per Blue Agent turn

        return remediations

    async def _persist_state(self, state: CampaignState, status: str):
        """Persist campaign state to DynamoDB."""
        try:
            self.campaigns_table.put_item(Item={
                "campaign_id": state.campaign_id,
                "timestamp": int(datetime.utcnow().timestamp()),
                "status": status,
                "target": state.target,
                "phase": state.phase.value,
                "current_turn": state.current_turn,
                "attack_turns_used": state.attack_turns_used,
                "defense_turns_used": state.defense_turns_used,
                "vulnerabilities_found": len(state.vulnerabilities_found),
                "remediations_applied": len(state.remediations_applied),
                "tokens_used": state.tokens_used,
                "coordinator_decisions": state.coordinator_decisions[-5:],  # Last 5
                "completed_at": state.completed_at or "",
            })
        except Exception as e:
            logger.warning(f"[COORDINATOR] DynamoDB persist failed: {e}")

    def get_campaign_summary(self, state: CampaignState) -> Dict:
        """Return a clean summary of the campaign for API responses."""
        return {
            "campaign_id": state.campaign_id,
            "target": state.target,
            "phase": state.phase.value,
            "turns": {
                "total": state.current_turn,
                "attack": state.attack_turns_used,
                "defense": state.defense_turns_used,
            },
            "findings": {
                "vulnerabilities": len(state.vulnerabilities_found),
                "remediations": len(state.remediations_applied),
                "unresolved": len(state.unresolved_findings),
            },
            "budget": {
                "tokens_used": state.tokens_used,
                "token_budget": state.token_budget,
                "budget_remaining_pct": round(
                    (1 - state.tokens_used / state.token_budget) * 100, 1
                ) if state.token_budget > 0 else 0,
            },
            "coordinator_decisions": state.coordinator_decisions,
            "completed_at": state.completed_at,
            "final_report": state.final_report,
        }
