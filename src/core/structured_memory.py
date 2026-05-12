"""
Structured Agent Memory for Sentinel AI

Extends CampaignMemoryManager with three memory types:
1. Episodic: Full campaign transcripts (what was tried, what happened)
2. Semantic: Embedded general security knowledge (via ChromaDB)
3. Procedural: Reusable attack/defense playbooks that proved effective

All stored in MongoDB (not DynamoDB) for simplicity — one database.
Fail-graceful: works without any database if needed.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StructuredMemory:
    """
    Three-tier agent memory system.

    Agents that remember don't repeat mistakes and reuse proven strategies.
    """

    def __init__(self, db=None, knowledge_store=None):
        """
        Args:
            db: MongoDB database instance (motor async).
            knowledge_store: KnowledgeStore instance for semantic embeddings.
        """
        self.db = db
        self.knowledge_store = knowledge_store

    # ==================== Episodic Memory ====================
    # Full campaign transcripts: what was tried, what worked, what failed

    async def store_episode(
        self,
        campaign_id: str,
        target: str,
        agent_type: str,
        actions: List[Dict],
        outcome: str,
        actor_id: str = "system",
    ) -> Optional[str]:
        """Store a complete campaign episode."""
        if not self.db:
            return None
        episode = {
            "campaign_id": campaign_id,
            "target": target,
            "agent_type": agent_type,
            "actions": actions,
            "outcome": outcome,
            "actor_id": actor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "memory_type": "episodic",
        }
        try:
            result = await self.db.episodic_memory.insert_one(episode)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to store episode: {e}")
            return None

    async def recall_episodes(
        self, target: str, agent_type: str = None, limit: int = 5
    ) -> List[Dict]:
        """Recall past episodes for a target."""
        if not self.db:
            return []
        query = {"target": target}
        if agent_type:
            query["agent_type"] = agent_type
        try:
            cursor = self.db.episodic_memory.find(query).sort("timestamp", -1).limit(limit)
            episodes = await cursor.to_list(length=limit)
            for ep in episodes:
                ep["id"] = str(ep.pop("_id"))
            return episodes
        except Exception as e:
            logger.error(f"Failed to recall episodes: {e}")
            return []

    # ==================== Semantic Memory ====================
    # Embedded knowledge accessible via similarity search

    async def store_knowledge(
        self,
        text: str,
        category: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Store a piece of general security knowledge into the semantic layer."""
        if not self.knowledge_store:
            return False
        meta = metadata or {}
        meta["category"] = category
        meta["memory_type"] = "semantic"
        return self.knowledge_store.store_finding(
            finding_text=text, metadata=meta
        )

    async def recall_knowledge(
        self, query: str, n_results: int = 5
    ) -> List[Dict]:
        """Recall relevant security knowledge for a query."""
        if not self.knowledge_store:
            return []
        return self.knowledge_store.query_relevant(
            query_text=query,
            n_results=n_results,
            filter_metadata={"memory_type": "semantic"},
        )

    # ==================== Procedural Memory ====================
    # Reusable playbooks — proven attack/defense strategies

    async def store_playbook(
        self,
        name: str,
        agent_type: str,
        steps: List[str],
        success_rate: float,
        applicable_to: List[str],
        source_campaign_id: str = None,
    ) -> Optional[str]:
        """
        Store a proven attack or defense playbook.

        Args:
            name: Playbook name (e.g., "SQL Injection via search parameter")
            agent_type: 'red' or 'blue'
            steps: Ordered list of actions
            success_rate: Historical success rate (0.0 - 1.0)
            applicable_to: What targets/scenarios this applies to
            source_campaign_id: The campaign this was derived from
        """
        if not self.db:
            return None
        playbook = {
            "name": name,
            "agent_type": agent_type,
            "steps": steps,
            "success_rate": success_rate,
            "applicable_to": applicable_to,
            "source_campaign_id": source_campaign_id,
            "uses": 0,
            "last_used": None,
            "timestamp": datetime.utcnow().isoformat(),
            "memory_type": "procedural",
        }
        try:
            result = await self.db.procedural_memory.insert_one(playbook)
            # Also embed in semantic layer for discovery
            if self.knowledge_store:
                self.knowledge_store.store_finding(
                    finding_text=f"Playbook: {name}\nSteps: {'; '.join(steps)}\nSuccess rate: {success_rate}",
                    metadata={"category": "playbook", "agent_type": agent_type, "memory_type": "semantic"},
                )
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to store playbook: {e}")
            return None

    async def find_playbooks(
        self, agent_type: str = None, target_type: str = None, min_success_rate: float = 0.0
    ) -> List[Dict]:
        """Find relevant playbooks based on criteria."""
        if not self.db:
            return []
        query = {"success_rate": {"$gte": min_success_rate}}
        if agent_type:
            query["agent_type"] = agent_type
        if target_type:
            query["applicable_to"] = target_type
        try:
            cursor = self.db.procedural_memory.find(query).sort("success_rate", -1).limit(10)
            playbooks = await cursor.to_list(length=10)
            for pb in playbooks:
                pb["id"] = str(pb.pop("_id"))
            return playbooks
        except Exception as e:
            logger.error(f"Failed to find playbooks: {e}")
            return []

    async def record_playbook_use(self, playbook_id: str, succeeded: bool) -> bool:
        """Record that a playbook was used and whether it succeeded."""
        if not self.db:
            return False
        try:
            from bson import ObjectId
            update = {
                "$inc": {"uses": 1},
                "$set": {"last_used": datetime.utcnow().isoformat()},
            }
            # Adjust success rate with exponential moving average
            if not succeeded:
                update["$mul"] = {"success_rate": 0.95}  # Decay on failure
            await self.db.procedural_memory.update_one(
                {"_id": ObjectId(playbook_id)}, update
            )
            return True
        except Exception as e:
            logger.error(f"Failed to record playbook use: {e}")
            return False

    # ==================== Memory Distillation ====================

    async def distill_episodes_to_playbooks(
        self, target: str = None, min_episodes: int = 3
    ) -> int:
        """
        Analyze past episodes and auto-generate playbooks from successful patterns.
        This is the learning step: raw experience → reusable knowledge.

        Returns number of playbooks created.
        """
        if not self.db:
            return 0

        query = {"outcome": "success"}
        if target:
            query["target"] = target
        try:
            cursor = self.db.episodic_memory.find(query).sort("timestamp", -1).limit(50)
            episodes = await cursor.to_list(length=50)
        except Exception:
            return 0

        if len(episodes) < min_episodes:
            return 0

        # Group by agent_type and extract common patterns
        from collections import defaultdict
        by_agent = defaultdict(list)
        for ep in episodes:
            by_agent[ep["agent_type"]].append(ep)

        created = 0
        for agent_type, agent_episodes in by_agent.items():
            if len(agent_episodes) < min_episodes:
                continue

            # Extract action sequences (simplified pattern extraction)
            all_actions = []
            for ep in agent_episodes[:10]:  # Limit for performance
                actions = ep.get("actions", [])
                action_names = [a.get("action", a.get("tool", "?")) for a in actions if isinstance(a, dict)]
                if action_names:
                    all_actions.append(action_names)

            if all_actions:
                # Use the most common sequence as the playbook
                most_common = max(all_actions, key=lambda x: all_actions.count(x))
                result = await self.store_playbook(
                    name=f"Auto-distilled {agent_type} playbook for {target or 'general'}",
                    agent_type=agent_type,
                    steps=most_common,
                    success_rate=0.8,
                    applicable_to=[target] if target else ["general"],
                )
                if result:
                    created += 1

        logger.info(f"Distilled {created} playbooks from {len(episodes)} episodes")
        return created

    # ==================== Build Context for Agents ====================

    async def build_agent_context(
        self, target: str, agent_type: str, max_items: int = 3
    ) -> str:
        """
        Build a comprehensive memory context for an agent.
        Combines episodic, semantic, and procedural memory.
        """
        sections = []

        # Episodic: What happened in past campaigns
        episodes = await self.recall_episodes(target, agent_type, limit=max_items)
        if episodes:
            sections.append("=== Past Campaign Episodes ===")
            for ep in episodes:
                outcome = ep.get("outcome", "unknown")
                ts = ep.get("timestamp", "?")[:10]
                sections.append(f"[{ts}] Outcome: {outcome}")
                for action in ep.get("actions", [])[:3]:
                    if isinstance(action, dict):
                        sections.append(f"  - {action.get('action', '?')}: {str(action.get('result', ''))[:100]}")

        # Procedural: What playbooks are available
        playbooks = await self.find_playbooks(agent_type=agent_type, min_success_rate=0.6)
        if playbooks:
            sections.append("\n=== Available Playbooks ===")
            for pb in playbooks[:3]:
                sections.append(f"Playbook: {pb['name']} (success: {pb['success_rate']:.0%})")
                sections.append(f"  Steps: {' → '.join(pb['steps'][:5])}")

        # Semantic: What relevant knowledge exists
        if self.knowledge_store:
            rag_context = self.knowledge_store.build_rag_context(target, agent_type, max_items)
            if rag_context:
                sections.append(f"\n{rag_context}")

        return "\n".join(sections) if sections else ""
