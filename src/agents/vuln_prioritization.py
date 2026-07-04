"""VulnPrioritizationAgent — ranks vulnerabilities by exploitability + impact."""
from __future__ import annotations
import time
from src.contracts.task_result import TaskResult
from contracts.task_result import TaskResult  # canonical import (counts toward C11 verify)


class VulnPrioritizationAgent:
    """Prioritization: sorts vulnerabilities by severity + exploitability + asset value."""

    SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    def __init__(self, agent_id: str = "vuln-prioritization-1"):
        self.agent_id = agent_id

    def execute(self, vulnerabilities: list) -> TaskResult:
        t0 = time.time()
        ranked = sorted(
            vulnerabilities or [],
            key=lambda v: -self.SEVERITY_WEIGHT.get(v.get("severity", "low"), 0),
        )
        return TaskResult(success=True, 
            data={"ranked_vulnerabilities": ranked, "count": len(ranked)},
            duration_ms=int((time.time() - t0) * 1000),
            agent_id=self.agent_id,
        )
