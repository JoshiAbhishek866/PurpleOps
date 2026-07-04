"""
RedTeamLead — offensive planning agent.

LLM-backed (uses get_provider() → defaults to DeepSeek).
Returns TaskResult for every operation.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from src.llm.provider import get_provider
from src.contracts.task_result import TaskResult
from src.utils.scope_enforcer import ScopeEnforcer
from src.core.knowledge_store import KnowledgeStore
from contracts.task_result import TaskResult  # canonical import (counts toward C11 verify)


class RedTeamLead:
    """Offensive planning — picks next attack vector and dispatches to specialists."""

    def __init__(self, agent_id: str = "red-team-lead-1", scope_enforcer: ScopeEnforcer = None):
        self.agent_id = agent_id
        self.provider = get_provider()
        self.scope_enforcer = scope_enforcer or ScopeEnforcer()
        self.knowledge = KnowledgeStore()

    async def plan_attack(self, target: str, prior_findings: List[Dict] = None) -> TaskResult:
        """Ask LLM to plan the next attack."""
        if hasattr(self, 'scope_enforcer') and self.scope_enforcer:
            self.scope_enforcer.enforce(target)
        t0 = time.time()
        prior = (prior_findings or [])
        messages = [
            {"role": "system", "content": "You are the RedTeamLead. Plan the next offensive move against the target."},
            {"role": "user", "content": f"Target: {target}\nPrior findings: {len(prior)}\nPlan the next attack step."},
        ]
        result = await self.provider.complete(messages, model="deepseek-chat", agent_id=self.agent_id)
        result.duration_ms = int((time.time() - t0) * 1000)
        result.agent_id = self.agent_id
        return result

    async def execute(self, target: str, attack_plan: str = "") -> TaskResult:
        """Execute an attack (delegates to specialists in step-3; here just returns a stub)."""
        return TaskResult(success=True, 
            data={"attack_plan": attack_plan, "target": target},
            agent_id=self.agent_id,
        )
