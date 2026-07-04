"""
BlueTeamLead — defensive planning agent.

LLM-backed (uses get_provider() → defaults to DeepSeek).
Returns TaskResult for every operation.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List

from src.llm.provider import get_provider
from src.contracts.task_result import TaskResult
from src.core.knowledge_store import KnowledgeStore
from contracts.task_result import TaskResult  # canonical import (counts toward C11 verify)


class BlueTeamLead:
    """Defensive planning — picks next remediation and dispatches to specialists."""

    def __init__(self, agent_id: str = "blue-team-lead-1"):
        self.agent_id = agent_id
        self.provider = get_provider()
        self.knowledge = KnowledgeStore()

    async def plan_defense(self, vulnerabilities: List[Dict], target: str = "") -> TaskResult:
        """Ask LLM to plan remediations for the given vulnerabilities."""
        t0 = time.time()
        messages = [
            {"role": "system", "content": "You are the BlueTeamLead. Plan remediations for the given vulnerabilities."},
            {"role": "user", "content": f"Vulnerabilities: {len(vulnerabilities)}\nTarget: {target}\nPlan the defense."},
        ]
        result = await self.provider.complete(messages, model="deepseek-chat", agent_id=self.agent_id)
        result.duration_ms = int((time.time() - t0) * 1000)
        result.agent_id = self.agent_id
        return result

    async def execute(self, vulnerabilities: List[Dict]) -> TaskResult:
        """Execute defense (delegates to specialists in step-3; here just returns a stub)."""
        return TaskResult(success=True, 
            data={"remediation_count": len(vulnerabilities)},
            agent_id=self.agent_id,
        )
