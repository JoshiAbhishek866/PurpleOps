"""
TaskResult and TaskRequest — inter-agent communication contracts.

Every agent in the 11-agent hierarchy (3 LLM + 8 deterministic) returns a TaskResult.
Every request to an agent is wrapped in a TaskRequest.

Field semantics:
  - success: True iff the agent completed its task without an unrecoverable error
  - data: arbitrary payload (str, dict, list, nested dataclass, etc.)
  - error: human-readable error message if success=False; None otherwise
  - tokens_used: LLM token count for this task (0 for deterministic agents)
  - duration_ms: wall-clock time the agent spent on this task
  - agent_id: identifier of the agent that produced this result (e.g. "coordinator-1")
  - timestamp: ISO-8601 UTC timestamp of when the result was produced
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional


def _utcnow_iso() -> str:
    """UTC timestamp in ISO-8601 format."""
    return datetime.utcnow().isoformat()


@dataclass
class TaskRequest:
    """Request envelope passed into an agent."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""            # e.g. "scan", "remediate", "report"
    target: str = ""                # URL, hostname, finding_id, etc.
    params: Dict[str, Any] = field(default_factory=dict)
    requested_by: str = ""          # agent_id of the caller
    timestamp: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskResult:
    """Result envelope returned by every agent in the 11-agent hierarchy."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0
    agent_id: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def ok(cls, *, data: Any = None, tokens_used: int = 0, duration_ms: int = 0, agent_id: str = "") -> "TaskResult":
        """Shorthand factory for a successful result."""
        return cls(success=True, data=data, tokens_used=tokens_used, duration_ms=duration_ms, agent_id=agent_id)

    @classmethod
    def fail(cls, *, error: str, agent_id: str = "", duration_ms: int = 0) -> "TaskResult":
        """Shorthand factory for a failed result."""
        return cls(success=False, error=error, agent_id=agent_id, duration_ms=duration_ms)


__all__ = ["TaskRequest", "TaskResult"]
