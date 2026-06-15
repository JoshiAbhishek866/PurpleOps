"""
Agent Lifecycle Hooks for Sentinel AI

Inspired by the Strands HookProvider pattern — provides automatic
context loading before agent execution and result persistence after.
Removes manual glue from the orchestrator.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ==================== Event Types ====================

class AgentEvent:
    """Base event passed to hook callbacks."""
    def __init__(self, agent_type: str, target: str, **kwargs):
        self.agent_type = agent_type
        self.target = target
        self.timestamp = datetime.now(timezone.utc)
        self.extra = kwargs


class AgentInitEvent(AgentEvent):
    """Fired before an agent starts execution."""
    def __init__(self, agent_type: str, target: str, campaign_id: str,
                 actor_id: str, session_id: str, **kwargs):
        super().__init__(agent_type, target, **kwargs)
        self.campaign_id = campaign_id
        self.actor_id = actor_id
        self.session_id = session_id


class AgentCompleteEvent(AgentEvent):
    """Fired after an agent finishes execution (success or fail)."""
    def __init__(self, agent_type: str, target: str, campaign_id: str,
                 actor_id: str, result: Dict, status: str, **kwargs):
        super().__init__(agent_type, target, **kwargs)
        self.campaign_id = campaign_id
        self.actor_id = actor_id
        self.result = result
        self.status = status


# ==================== Hook Provider ====================

class SecurityHookProvider:
    """
    Lifecycle hook provider for Sentinel AI agents.

    Responsibilities:
    - on_agent_init:  Load prior findings for the target from campaign
                      memory and return contextual prompt augmentation.
    - on_agent_complete: Auto-persist results to campaign memory,
                         trigger n8n workflow, request LLM analysis.
    """

    def __init__(self, memory_manager=None, n8n_client=None, llm_client=None, database=None):
        self.memory = memory_manager
        self.n8n = n8n_client
        self.llm = llm_client
        self.db = database

    # ---------- Pre-execution ----------

    async def on_agent_init(self, event: AgentInitEvent) -> Optional[str]:
        """
        Called before agent execution.

        Returns a context string that the caller can inject into the agent's
        prompt / options.  Returns None if no relevant history.
        """
        if not self.memory:
            return None

        try:
            history = await self.memory.retrieve_target_history(
                target=event.target,
                agent_type=event.agent_type,
                limit=5,
            )
            if not history:
                logger.info(f"No prior history for {event.agent_type} on {event.target}")
                return None

            # Build a concise textual summary
            lines = []
            for entry in history:
                finding = entry.get("finding", {})
                date = entry.get("created_at", "unknown")
                summary = str(finding.get("output", finding.get("simulated_result", "")))[:200]
                if summary:
                    lines.append(f"  [{date}] {summary}")

            if not lines:
                return None

            context = (
                f"\n## Prior {event.agent_type.upper()} findings for {event.target}:\n"
                + "\n".join(lines)
            )
            logger.info(
                f"✅ Loaded {len(lines)} prior {event.agent_type} findings for {event.target}"
            )
            return context

        except Exception as e:
            logger.error(f"Hook on_agent_init error: {e}")
            return None

    # ---------- Post-execution ----------

    async def on_agent_complete(self, event: AgentCompleteEvent) -> None:
        """
        Called after agent execution.

        Auto-persists results and triggers downstream enrichment.
        """
        # 1. Persist to campaign memory
        if self.memory:
            try:
                await self.memory.store_finding(
                    target=event.target,
                    agent_type=event.agent_type,
                    finding=event.result,
                    campaign_id=event.campaign_id,
                    actor_id=event.actor_id,
                )
            except Exception as e:
                logger.error(f"Hook memory persist error: {e}")

        # 2. Trigger n8n workflow (only on success)
        if self.n8n and event.status == "success":
            try:
                await self.n8n.trigger_agent_workflow(
                    event.agent_type, event.target, event.result
                )
            except Exception as e:
                logger.warning(f"Hook n8n trigger skipped: {e}")

        # 3. Request LLM analysis (skip report/dashboard agents)
        if self.llm and event.agent_type not in ("report_generator", "dashboard_reporter"):
            try:
                analysis = await self.llm.analyze_scan_results(
                    event.agent_type, event.result
                )
                event.result["llm_insights"] = analysis
            except Exception as e:
                logger.warning(f"Hook LLM analysis skipped: {e}")

        # 4. Save full result to operational DB
        if self.db:
            try:
                result_id = await self.db.save_result(event.result)
                event.result["result_id"] = result_id
            except Exception as e:
                logger.error(f"Hook DB save error: {e}")

        logger.info(
            f"🪝 Post-execution hooks completed for {event.agent_type} on {event.target}"
        )


# ==================== Attack-Defense Feedback Hook ====================

class AttackDefenseFeedbackHook:
    """
    Specialised hook that builds the Red↔Blue feedback loop.

    Before Red Agent: loads Blue's past patches so Red can probe new vectors.
    Before Blue Agent: loads Red's latest findings so Blue can respond precisely.
    """

    def __init__(self, memory_manager=None):
        self.memory = memory_manager

    async def get_red_context(self, target: str) -> Optional[str]:
        """Context injected into Red Agent before a campaign."""
        if not self.memory:
            return None

        try:
            ctx = await self.memory.retrieve_attack_defense_context(target)
            defenses = ctx.get("past_defenses", [])
            if not defenses:
                return None

            lines = [f"  - {d['summary']}" for d in defenses[:5] if d.get("summary")]
            if not lines:
                return None

            return (
                "\n## Blue Team's prior defenses on this target (find gaps in these):\n"
                + "\n".join(lines)
            )
        except Exception as e:
            logger.error(f"Feedback hook (red context) error: {e}")
            return None

    async def get_blue_context(self, target: str, red_result: Dict = None) -> Optional[str]:
        """Context injected into Blue Agent before defending."""
        if not self.memory:
            return None

        parts = []

        # Current Red findings (from this campaign)
        if red_result:
            current = str(red_result.get("output", red_result.get("simulated_result", "")))[:500]
            if current:
                parts.append(f"## Current Red Team findings:\n{current}")

        # Historical Red findings
        try:
            ctx = await self.memory.retrieve_attack_defense_context(target)
            attacks = ctx.get("past_attacks", [])
            if attacks:
                lines = [f"  - {a['summary']}" for a in attacks[:5] if a.get("summary")]
                if lines:
                    parts.append(
                        "## Historical Red Team attacks on this target:\n" + "\n".join(lines)
                    )

            defenses = ctx.get("past_defenses", [])
            if defenses:
                lines = [f"  - {d['summary']}" for d in defenses[:3] if d.get("summary")]
                if lines:
                    parts.append(
                        "## Your prior defenses (avoid repeating; build on these):\n"
                        + "\n".join(lines)
                    )
        except Exception as e:
            logger.error(f"Feedback hook (blue context) error: {e}")

        return "\n\n".join(parts) if parts else None
