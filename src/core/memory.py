"""
Campaign Memory Manager for Sentinel AI

Provides cross-session memory persistence using DynamoDB.
Inspired by Bedrock AgentCore Memory patterns — adapted for
security domain: remembers attack findings, defense patches,
and scan results per target across multiple campaigns.
"""

import boto3
from typing import Dict, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging

from src.config import Config

logger = logging.getLogger(__name__)


class CampaignMemoryManager:
    """
    Persistent security intelligence memory per target.
    
    Stores and retrieves:
    - Red Agent attack findings per target
    - Blue Agent remediation actions per target
    - Orchestrator scan results per target
    - Combined attack-defense summaries for feedback loops
    """

    def __init__(self, table_name: str = None, region: str = None):
        self.region = region or Config.AWS_REGION
        self.table_name = table_name or "SentinelAI_CampaignMemory"
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"CampaignMemoryManager initialized: {self.table_name}")

    # ==================== Store ====================

    async def store_finding(
        self,
        target: str,
        agent_type: str,
        finding: Dict,
        campaign_id: str,
        actor_id: str = "default_user",
        session_id: str = None,
    ) -> bool:
        """
        Persist an agent's finding for a target.

        Args:
            target: The scanned target (URL / IP / domain)
            agent_type: 'red', 'blue', or any orchestrator agent name
            finding: The result dict from the agent
            campaign_id: Campaign this belongs to
            actor_id: Who initiated the campaign
            session_id: Session identifier
        """
        try:
            # Sanitise for DynamoDB (no floats)
            sanitised = json.loads(json.dumps(finding, default=str), parse_float=Decimal)

            item = {
                "target": target,
                "sort_key": f"{agent_type}#{datetime.now(timezone.utc).isoformat()}",
                "agent_type": agent_type,
                "campaign_id": campaign_id,
                "actor_id": actor_id,
                "session_id": session_id or campaign_id,
                "finding": sanitised,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ttl": int(datetime.now(timezone.utc).timestamp()) + 90 * 86400,  # 90-day retention
            }

            self.table.put_item(Item=item)
            logger.info(f"💾 Stored {agent_type} finding for target={target}")
            return True
        except Exception as e:
            logger.error(f"Failed to store finding: {e}")
            return False

    # ==================== Retrieve ====================

    async def retrieve_target_history(
        self,
        target: str,
        agent_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Get past findings for a target, optionally filtered by agent type.
        """
        try:
            key_condition = boto3.dynamodb.conditions.Key("target").eq(target)
            if agent_type:
                key_condition &= boto3.dynamodb.conditions.Key("sort_key").begins_with(f"{agent_type}#")

            response = self.table.query(
                KeyConditionExpression=key_condition,
                ScanIndexForward=False,  # newest first
                Limit=limit,
            )
            items = response.get("Items", [])
            # Convert Decimals back to native types
            return [json.loads(json.dumps(item, default=str)) for item in items]
        except Exception as e:
            logger.error(f"Failed to retrieve history for {target}: {e}")
            return []

    async def retrieve_attack_defense_context(self, target: str) -> Dict:
        """
        Build a combined context summary of all Red + Blue interactions
        for a target.  This is what gets injected into agent prompts to
        close the attack-defense feedback loop.
        """
        red_history = await self.retrieve_target_history(target, agent_type="red", limit=5)
        blue_history = await self.retrieve_target_history(target, agent_type="blue", limit=5)

        # Build concise summaries
        past_attacks = []
        for entry in red_history:
            finding = entry.get("finding", {})
            summary = finding.get("output", finding.get("simulated_result", str(finding)[:200]))
            past_attacks.append({
                "campaign_id": entry.get("campaign_id"),
                "date": entry.get("created_at"),
                "summary": summary[:300],
            })

        past_defenses = []
        for entry in blue_history:
            finding = entry.get("finding", {})
            summary = finding.get("output", finding.get("message", str(finding)[:200]))
            past_defenses.append({
                "campaign_id": entry.get("campaign_id"),
                "date": entry.get("created_at"),
                "summary": summary[:300],
            })

        return {
            "target": target,
            "past_attacks": past_attacks,
            "past_defenses": past_defenses,
            "total_campaigns": len(set(
                e.get("campaign_id") for e in red_history + blue_history
            )),
        }

    # ==================== Table Bootstrap ====================

    @classmethod
    def ensure_table_exists(cls, region: str = None, table_name: str = None):
        """
        Create the DynamoDB table if it does not exist.
        Idempotent — safe to call on every startup.
        """
        region = region or Config.AWS_REGION
        table_name = table_name or "SentinelAI_CampaignMemory"
        client = boto3.client("dynamodb", region_name=region)

        existing = client.list_tables().get("TableNames", [])
        if table_name in existing:
            logger.info(f"DynamoDB table {table_name} already exists")
            return

        try:
            client.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "target", "KeyType": "HASH"},
                    {"AttributeName": "sort_key", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "target", "AttributeType": "S"},
                    {"AttributeName": "sort_key", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
                TimeToLiveSpecification={
                    "Enabled": True,
                    "AttributeName": "ttl"
                },
            )
            logger.info(f"✅ Created DynamoDB table: {table_name}")
        except Exception as e:
            logger.warning(f"Table creation skipped: {e}")
