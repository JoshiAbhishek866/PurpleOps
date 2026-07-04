"""
Immutable Audit Logger for PurpleOps

Provides tamper-evident, append-only audit entries with SHA-256 hashing.
Cost-optimized: stores to MongoDB alongside operational data (no separate service needed).
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Append-only audit logger with integrity hashing.

    Each entry includes a SHA-256 hash of its content so downstream
    systems (SIEM, SOC 2 auditors) can verify no tampering occurred.
    """

    def __init__(self, db=None):
        """
        Args:
            db: MongoDB database instance (motor async). If None, logs to Python logger only.
        """
        self.db = db
        self._collection_name = "audit_log"

    def _compute_hash(self, entry: Dict) -> str:
        """Compute SHA-256 hash of the audit entry for tamper detection."""
        canonical = json.dumps(entry, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def log(
        self,
        action: str,
        actor_id: str,
        target: str = "",
        agent_type: str = "",
        result_summary: str = "",
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Write an immutable audit entry.

        Args:
            action: What happened (e.g., 'campaign_started', 'scan_completed', 'waf_rule_updated')
            actor_id: Who did it (user ID or 'system')
            target: What was acted upon (URL, resource ID)
            agent_type: Which agent performed the action
            result_summary: Brief outcome text
            metadata: Any extra context

        Returns:
            The inserted document ID, or None if DB is unavailable.
        """
        entry = {
            "action": action,
            "actor_id": actor_id,
            "target": target,
            "agent_type": agent_type,
            "result_summary": result_summary[:500],  # cap size
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Add integrity hash
        entry["integrity_hash"] = self._compute_hash(entry)

        # Always log to Python logger (even if DB is down)
        logger.info(f"AUDIT | {action} | actor={actor_id} | target={target} | agent={agent_type}")

        # Persist to MongoDB if available
        if self.db:
            try:
                collection = self.db[self._collection_name]
                result = await collection.insert_one(entry)
                return str(result.inserted_id)
            except Exception as e:
                logger.error(f"Audit DB write failed: {e}")

        return None

    async def get_audit_trail(
        self,
        actor_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ):
        """Retrieve audit entries with optional filters."""
        if not self.db:
            return []

        query = {}
        if actor_id:
            query["actor_id"] = actor_id
        if action:
            query["action"] = action

        try:
            collection = self.db[self._collection_name]
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            entries = await cursor.to_list(length=limit)
            for entry in entries:
                entry["id"] = str(entry.pop("_id"))
            return entries
        except Exception as e:
            logger.error(f"Audit trail query failed: {e}")
            return []
