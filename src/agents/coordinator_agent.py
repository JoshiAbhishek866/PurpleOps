"""
Central Coordinator Agent - PurpleOps
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
import httpx
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
# Coordinator Agent (Phase 3 wrapper)
# ─────────────────────────────────────────────

class CoordinatorAgent:
    """
    Thin wrapper around AgentOrchestrator (Phase 3 unification).

    The orchestrator (`src.core.orchestrator.AgentOrchestrator`) is the single
    entrypoint for all campaign execution. This wrapper preserves the legacy
    `CoordinatorAgent` API (including `_track_tokens`, used by Phase 2 step-3
    regression tests) for the 3 existing consumers:
      - src/main.py
      - src/routes/campaigns.py
      - tests/test_coordinator_tokens.py

    For new code, prefer importing AgentOrchestrator directly from
    `src.core.orchestrator`.
    """

    def __init__(self):
        # Lazy: do NOT instantiate AgentOrchestrator here, because its
        # __init__ requires Database/N8NClient/LLMClient args that legacy
        # callers don't pass. Only instantiate when an orchestrator method
        # is actually invoked. The Phase 2 step-3 tests only call
        # `_track_tokens`, which is inlined below.
        self._orch = None

    def _get_orchestrator(self):
        if self._orch is None:
            from src.core.orchestrator import AgentOrchestrator
            self._orch = AgentOrchestrator()
        return self._orch

    @property
    def orchestrator(self):
        """Expose the underlying AgentOrchestrator for callers that need it."""
        return self._get_orchestrator()

    async def run_campaign(self, state):
        """Delegate to AgentOrchestrator.step()."""
        return await self._get_orchestrator().step(state)

    async def start_campaign(self, **kwargs):
        """Delegate to AgentOrchestrator.start_campaign()."""
        return await self._get_orchestrator().start_campaign(**kwargs)

    async def stop(self, state):
        """Delegate to AgentOrchestrator.stop()."""
        return await self._get_orchestrator().stop(state)

    # ── Legacy helpers preserved for backward compatibility ────────────────

    def _track_tokens(self, state, response) -> int:
        """
        Token-tracking helper preserved for Phase 2 step-3 unit tests.
        Direct port of the original implementation from coordinator_agent.py.

        Handles:
        - dict with 'usage_metadata' or 'llm_output' or 'usage' keys
        - LangChain AIMessage with .usage_metadata attribute or .response_metadata.token_usage
        - ChatBedrock result dict with 'usage' key (Bedrock shape: {'input_tokens': N, 'output_tokens': N})
        - Bedrock Converse API: response['usage'] = {'inputTokens': N, 'outputTokens': N}
        - Raw int (treated as total_tokens)
        - Anything else: returns 0, no exception

        Returns: number of tokens added to state.tokens_used (0 if none).
        """
        if response is None:
            return 0

        usage: dict = {}

        # Case 1: raw int -> treat as total_tokens
        if isinstance(response, int):
            state.tokens_used += response
            return response

        # Case 2: dict response
        if isinstance(response, dict):
            # Bedrock shape: {'usage': {'inputTokens': N, 'outputTokens': N}}
            bedrock = response.get("usage") or {}
            if isinstance(bedrock, dict) and ("inputTokens" in bedrock or "outputTokens" in bedrock):
                usage = {
                    "input_tokens": bedrock.get("inputTokens", 0) or bedrock.get("input_tokens", 0),
                    "output_tokens": bedrock.get("outputTokens", 0) or bedrock.get("output_tokens", 0),
                }
            else:
                # LangChain / generic shape
                raw = response.get("usage_metadata") or response.get("llm_output") or response.get("usage") or {}
                if isinstance(raw, dict):
                    usage = raw

        # Case 3: object with attributes (LangChain AIMessage)
        else:
            # AIMessage has .usage_metadata (LangChain >=0.1) or .response_metadata
            meta = getattr(response, "usage_metadata", None)
            if isinstance(meta, dict) and meta:
                usage = meta
            else:
                resp_meta = getattr(response, "response_metadata", None)
                if isinstance(resp_meta, dict):
                    token_usage = resp_meta.get("usage") or resp_meta.get("token_usage")
                    if isinstance(token_usage, dict):
                        usage = token_usage

        if not usage:
            return 0

        # Compute total from total_tokens or (input_tokens + output_tokens)
        total = (
            usage.get("total_tokens", 0)
            or usage.get("totalTokens", 0)
            or (usage.get("input_tokens", 0) or usage.get("inputTokens", 0))
               + (usage.get("output_tokens", 0) or usage.get("outputTokens", 0))
        )

        if total and total > 0:
            state.tokens_used += int(total)
            return int(total)
        return 0
