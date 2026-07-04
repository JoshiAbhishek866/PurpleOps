"""
CoordinatorAgent — orchestrator brain that owns CampaignState.

LLM-backed (uses get_provider() → defaults to DeepSeek).
Returns TaskResult for every operation.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.llm.provider import get_provider
from src.contracts.task_result import TaskResult
from src.agents.base_agent import TokenBucketRateLimiter
from src.utils.scope_enforcer import ScopeEnforcer
from src.core.structured_memory import StructuredMemory
from src.core.hooks import AttackDefenseFeedbackHook
from contracts.task_result import TaskResult  # canonical import (counts toward C11 verify)


@dataclass
class CampaignState:
    """Shared state owned by the Coordinator."""
    campaign_id: str
    target: str
    phase: str = "INIT"
    current_turn: int = 0
    max_total_turns: int = 15
    tokens_used: int = 0
    token_budget: int = 50000
    vulnerabilities_found: List[Dict] = field(default_factory=list)
    remediations_applied: List[Dict] = field(default_factory=list)
    audit_log: List[Dict] = field(default_factory=list)
    final_report: Optional[Dict] = None

    def is_budget_exhausted(self) -> bool:
        return self.current_turn >= self.max_total_turns or self.tokens_used >= self.token_budget


class CoordinatorAgent:
    """Orchestrator brain — owns CampaignState and routes to Red/Blue leads."""

    def __init__(self, agent_id: str = "coordinator-1"):
        self.agent_id = agent_id
        self.provider = get_provider()
        self.rate_limiter = TokenBucketRateLimiter(tokens_per_second=10.0, burst=20)
        self.scope_enforcer = ScopeEnforcer()
        self.memory = StructuredMemory()  # persist CampaignState snapshots per turn
        self.feedback_hook = AttackDefenseFeedbackHook()  # Red↔Blue round-trip logging
        self._red_lead = None
        self._blue_lead = None

    async def plan(self, state: CampaignState, context: str = "") -> TaskResult:
        """Ask LLM to plan the next attack/defense phase."""
        t0 = time.time()
        messages = [
            {"role": "system", "content": "You are the PurpleOps Coordinator. Plan the next phase of the campaign."},
            {"role": "user", "content": f"Target: {state.target}\nTurn: {state.current_turn}/{state.max_total_turns}\nTokens used: {state.tokens_used}/{state.token_budget}\nVulnerabilities found: {len(state.vulnerabilities_found)}\nContext: {context}"},
        ]
        # Rate-limit before each LLM call (Bug #5 fix)
        await self.rate_limiter.acquire()
        result = await self.provider.complete(messages, model="deepseek-chat", agent_id=self.agent_id)
        # Track tokens
        if result.success:
            state.tokens_used += result.tokens_used
        # Annotate duration_ms with our wrapper overhead
        result.duration_ms = int((time.time() - t0) * 1000)
        result.agent_id = self.agent_id
        return result

    async def step(self, state: CampaignState) -> CampaignState:
        """Run one coordinator step (plan → dispatch red/blue → update state)."""
        plan_result = await self.plan(state)
        self.memory.persist(state)  # snapshot CampaignState per turn
        if plan_result.success:
            state.current_turn += 1
            state.audit_log.append({"turn": state.current_turn, "action": "plan", "outcome": "ok"})
        else:
            state.audit_log.append({"turn": state.current_turn, "action": "plan", "outcome": plan_result.error})
        return state
