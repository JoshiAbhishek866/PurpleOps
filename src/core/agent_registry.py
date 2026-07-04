"""
AWS Bedrock AgentCore Registry Integration - PurpleOps
=========================================================
Implements the "ECR for AI Agents" concept using AWS Bedrock AgentCore.

This allows PurpleOps's Red/Blue/Coordinator agents to be:
  - Versioned and stored in a central registry
  - Discovered and pulled by any AWS account
  - Deployed consistently across environments
  - Tracked with full metadata (capabilities, IAM requirements, cost)

Think of it as: Docker Hub for Cybersecurity Agents.

Usage:
  registry = AgentRegistry()

  # Register an agent version
  await registry.register_agent(
      agent_id="sentinel-red-agent",
      version="1.2.0",
      agent_type="offensive",
      capabilities=["sql_injection", "xss", "privilege_escalation"]
  )

  # Pull and instantiate an agent
  agent = await registry.pull_agent("sentinel-red-agent", version="latest")

  # List all available agents
  agents = await registry.list_agents()

References:
  - AWS Bedrock AgentCore: https://aws.amazon.com/bedrock/agentcore/
  - Agent Registry (preview): Part of Bedrock AgentCore suite
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

import boto3
from botocore.exceptions import ClientError

from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ─────────────────────────────────────────────
# Agent Manifest (Registry Schema)
# ─────────────────────────────────────────────

@dataclass
class AgentManifest:
    """
    Defines an agent's full specification for registry storage.
    Maps to AWS Bedrock AgentCore agent definition schema.
    """
    agent_id: str
    version: str
    display_name: str
    description: str
    agent_type: str                    # "offensive" | "defensive" | "coordinator"
    capabilities: List[str]            # e.g. ["sql_injection", "xss"]
    model_id: str                      # Bedrock model used
    tool_schema: List[Dict]            # LangChain tool definitions
    iam_requirements: Dict             # Required IAM permissions
    resource_requirements: Dict        # CPU, memory, timeout
    cost_per_run_usd: float            # Estimated cost per execution
    tags: Dict[str, str]               # Metadata tags
    created_at: str = ""
    updated_at: str = ""
    status: str = "active"             # "active" | "deprecated" | "beta"

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["created_at"] = d.get("created_at") or datetime.now(timezone.utc).isoformat()
        d["updated_at"] = datetime.now(timezone.utc).isoformat()
        return d


# ─────────────────────────────────────────────
# Agent Registry
# ─────────────────────────────────────────────

class AgentRegistry:
    """
    Central registry for PurpleOps agents.

    Storage backends:
    1. AWS Bedrock AgentCore (primary, when available in your region)
    2. DynamoDB (fallback / local development)
    3. S3 (agent artifact storage)

    The registry enables:
    - Version-controlled agent deployments
    - Cross-account agent sharing
    - Capability-based agent discovery
    - Cost tracking per agent version
    """

    REGISTRY_TABLE = "SentinelAgentRegistry"
    REGISTRY_BUCKET_PREFIX = "purpleops-agent-registry"

    def __init__(self):
        self.region = Config.AWS_REGION
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.s3 = boto3.client("s3", region_name=self.region)
        self.bedrock_agent = boto3.client("bedrock-agent", region_name=self.region)
        self._table = None

    # ── Table Bootstrap ──────────────────────────────────────────────────────

    def _get_table(self):
        """Get or create the registry DynamoDB table."""
        if self._table:
            return self._table
        try:
            table = self.dynamodb.Table(self.REGISTRY_TABLE)
            table.load()
            self._table = table
            return table
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.info(f"Creating registry table: {self.REGISTRY_TABLE}")
                table = self.dynamodb.create_table(
                    TableName=self.REGISTRY_TABLE,
                    KeySchema=[
                        {"AttributeName": "agent_id", "KeyType": "HASH"},
                        {"AttributeName": "version", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "agent_id", "AttributeType": "S"},
                        {"AttributeName": "version", "AttributeType": "S"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
                table.wait_until_exists()
                self._table = table
                return table
            raise

    # ── Register Agent ───────────────────────────────────────────────────────

    async def register_agent(
        self,
        agent_id: str,
        version: str,
        display_name: str,
        description: str,
        agent_type: str,
        capabilities: List[str],
        tool_schema: Optional[List[Dict]] = None,
        iam_requirements: Optional[Dict] = None,
        resource_requirements: Optional[Dict] = None,
        cost_per_run_usd: float = 0.05,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Register a new agent version in the registry.

        This is equivalent to `docker push` for agents.
        """
        manifest = AgentManifest(
            agent_id=agent_id,
            version=version,
            display_name=display_name,
            description=description,
            agent_type=agent_type,
            capabilities=capabilities,
            model_id=Config.BEDROCK_MODEL_ID,
            tool_schema=tool_schema or [],
            iam_requirements=iam_requirements or self._default_iam(agent_type),
            resource_requirements=resource_requirements or {
                "cpu": "1 vCPU",
                "memory": "2 GB",
                "timeout_seconds": 300,
            },
            cost_per_run_usd=cost_per_run_usd,
            tags=tags or {"project": "purpleops", "env": "production"},
        )

        manifest_dict = manifest.to_dict()

        # 1. Store in DynamoDB (always available)
        table = self._get_table()
        table.put_item(Item={
            **manifest_dict,
            "tool_schema": json.dumps(manifest_dict["tool_schema"]),
            "iam_requirements": json.dumps(manifest_dict["iam_requirements"]),
            "resource_requirements": json.dumps(manifest_dict["resource_requirements"]),
            "tags": json.dumps(manifest_dict["tags"]),
        })

        # 2. Try AWS Bedrock AgentCore (preview — graceful fallback)
        bedrock_result = await self._register_in_bedrock_agentcore(manifest_dict)

        logger.info(
            f"[REGISTRY] ✅ Registered {agent_id}:{version} "
            f"(type={agent_type}, capabilities={capabilities})"
        )

        return {
            "status": "registered",
            "agent_id": agent_id,
            "version": version,
            "registry_backend": "dynamodb",
            "bedrock_agentcore": bedrock_result,
            "manifest": manifest_dict,
        }

    # ── Pull Agent ───────────────────────────────────────────────────────────

    async def pull_agent(
        self,
        agent_id: str,
        version: str = "latest"
    ) -> Optional[Dict]:
        """
        Pull an agent manifest from the registry.

        This is equivalent to `docker pull` for agents.
        Returns the manifest dict; caller instantiates the agent class.
        """
        table = self._get_table()

        if version == "latest":
            # Scan for latest version of this agent
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("agent_id").eq(agent_id),
                ScanIndexForward=False,
                Limit=1,
            )
            items = response.get("Items", [])
        else:
            response = table.get_item(Key={"agent_id": agent_id, "version": version})
            items = [response["Item"]] if "Item" in response else []

        if not items:
            logger.warning(f"[REGISTRY] Agent not found: {agent_id}:{version}")
            return None

        item = items[0]

        # Deserialize JSON fields
        for field in ["tool_schema", "iam_requirements", "resource_requirements", "tags"]:
            if isinstance(item.get(field), str):
                item[field] = json.loads(item[field])

        logger.info(f"[REGISTRY] 📦 Pulled {agent_id}:{item['version']}")
        return item

    # ── List Agents ──────────────────────────────────────────────────────────

    async def list_agents(
        self,
        agent_type: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> List[Dict]:
        """
        List all registered agents, optionally filtered by type or capability.

        This is equivalent to browsing Docker Hub for agents.
        """
        table = self._get_table()
        response = table.scan()
        items = response.get("Items", [])

        # Deserialize JSON fields
        for item in items:
            for field in ["tool_schema", "iam_requirements", "resource_requirements", "tags"]:
                if isinstance(item.get(field), str):
                    try:
                        item[field] = json.loads(item[field])
                    except Exception:
                        pass

        # Filter
        if agent_type:
            items = [i for i in items if i.get("agent_type") == agent_type]
        if capability:
            items = [
                i for i in items
                if capability in i.get("capabilities", [])
            ]

        logger.info(f"[REGISTRY] Listed {len(items)} agents")
        return items

    # ── Deprecate Agent ──────────────────────────────────────────────────────

    async def deprecate_agent(self, agent_id: str, version: str) -> bool:
        """Mark an agent version as deprecated."""
        table = self._get_table()
        try:
            table.update_item(
                Key={"agent_id": agent_id, "version": version},
                UpdateExpression="SET #s = :s, updated_at = :u",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={
                    ":s": "deprecated",
                    ":u": datetime.now(timezone.utc).isoformat(),
                },
            )
            logger.info(f"[REGISTRY] Deprecated {agent_id}:{version}")
            return True
        except Exception as e:
            logger.error(f"[REGISTRY] Deprecation failed: {e}")
            return False

    # ── Bedrock AgentCore Integration ────────────────────────────────────────

    async def _register_in_bedrock_agentcore(self, manifest: Dict) -> Dict:
        """
        Register agent in AWS Bedrock AgentCore (preview).

        Falls back gracefully if AgentCore is not available in the region.
        Reference: https://aws.amazon.com/bedrock/agentcore/
        """
        try:
            # AWS Bedrock AgentCore Agent Registry API (preview)
            # This API is in preview — structure may change
            response = self.bedrock_agent.create_agent(
                agentName=f"{manifest['agent_id']}-{manifest['version']}",
                description=manifest["description"],
                foundationModel=manifest["model_id"],
                instruction=self._build_agent_instruction(manifest),
                agentResourceRoleArn=Config.RED_AGENT_ROLE_ARN or "",
                tags=manifest.get("tags", {}),
            )

            agent_arn = response.get("agent", {}).get("agentArn", "")
            logger.info(f"[REGISTRY] ✅ Registered in Bedrock AgentCore: {agent_arn}")

            return {
                "status": "registered",
                "agent_arn": agent_arn,
                "bedrock_agent_id": response.get("agent", {}).get("agentId", ""),
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["AccessDeniedException", "ValidationException", "ResourceNotFoundException"]:
                logger.warning(
                    f"[REGISTRY] Bedrock AgentCore not available ({error_code}). "
                    f"Using DynamoDB registry only."
                )
                return {"status": "skipped", "reason": error_code}
            logger.error(f"[REGISTRY] Bedrock AgentCore error: {e}")
            return {"status": "failed", "error": str(e)}

        except Exception as e:
            logger.warning(f"[REGISTRY] Bedrock AgentCore unavailable: {e}")
            return {"status": "skipped", "reason": str(e)}

    def _build_agent_instruction(self, manifest: Dict) -> str:
        """Build the instruction string for Bedrock AgentCore registration."""
        caps = ", ".join(manifest.get("capabilities", []))
        return (
            f"You are a {manifest['agent_type']} security agent for PurpleOps. "
            f"Your capabilities include: {caps}. "
            f"Always log actions to the audit trail. "
            f"Never target production systems without explicit authorization."
        )

    def _default_iam(self, agent_type: str) -> Dict:
        """Return default IAM requirements based on agent type."""
        if agent_type == "offensive":
            return {
                "allow": ["ec2:Describe*", "waf:Get*", "dynamodb:PutItem"],
                "deny": ["waf:UpdateWebACL", "ec2:Modify*", "iam:*"],
                "note": "Read-only access to target infrastructure"
            }
        elif agent_type == "defensive":
            return {
                "allow": [
                    "waf:UpdateWebACL",
                    "ec2:ModifySecurityGroupRules",
                    "iam:UpdateAssumeRolePolicy",
                    "dynamodb:PutItem",
                    "s3:PutObject"
                ],
                "deny": [],
                "note": "Write access to security controls only"
            }
        else:  # coordinator
            return {
                "allow": ["dynamodb:*", "bedrock:InvokeModel", "s3:PutObject"],
                "deny": ["ec2:*", "iam:*"],
                "note": "Orchestration and state management only"
            }


# ─────────────────────────────────────────────
# Pre-built Agent Definitions
# ─────────────────────────────────────────────

async def register_sentinel_agents(registry: AgentRegistry) -> Dict:
    """
    Register all PurpleOps agents in the registry.
    Call this once during deployment / bootstrap.

    This is the equivalent of pushing your Docker images to ECR.
    """
    results = {}

    # 1. Coordinator Agent
    results["coordinator"] = await registry.register_agent(
        agent_id="sentinel-coordinator",
        version="1.0.0",
        display_name="PurpleOps Coordinator",
        description=(
            "Central supervisor agent that orchestrates Red/Blue agents. "
            "Implements LangGraph Supervisor pattern with token budget enforcement, "
            "turn limits, and deterministic audit trails."
        ),
        agent_type="coordinator",
        capabilities=[
            "campaign_orchestration",
            "token_budget_enforcement",
            "turn_limit_control",
            "audit_trail_generation",
            "agent_routing",
            "state_management",
        ],
        cost_per_run_usd=0.02,
        tags={"role": "supervisor", "project": "purpleops"},
    )

    # 2. Red Agent
    results["red_agent"] = await registry.register_agent(
        agent_id="sentinel-red-agent",
        version="1.0.0",
        display_name="PurpleOps Red Agent",
        description=(
            "Offensive security agent powered by Amazon Bedrock (Claude 3.5 Sonnet). "
            "Executes controlled SQL injection, XSS, and privilege escalation tests."
        ),
        agent_type="offensive",
        capabilities=[
            "sql_injection",
            "xss_testing",
            "privilege_escalation",
            "api_abuse_testing",
        ],
        tool_schema=[
            {
                "name": "execute_sql_injection",
                "description": "Test SQL injection vulnerabilities",
                "parameters": {"target_url": "string", "payload": "string"},
            },
            {
                "name": "test_xss_vulnerability",
                "description": "Test XSS vulnerabilities",
                "parameters": {"target_url": "string", "payload": "string"},
            },
            {
                "name": "test_privilege_escalation",
                "description": "Test IAM privilege escalation",
                "parameters": {"iam_role": "string"},
            },
        ],
        cost_per_run_usd=0.08,
        tags={"role": "offensive", "project": "purpleops"},
    )

    # 3. Blue Agent
    results["blue_agent"] = await registry.register_agent(
        agent_id="sentinel-blue-agent",
        version="1.0.0",
        display_name="PurpleOps Blue Agent",
        description=(
            "Defensive security agent powered by Amazon Bedrock (Claude 3.5 Sonnet). "
            "Auto-remediates vulnerabilities via WAF updates, security group modifications, "
            "and compliance report generation."
        ),
        agent_type="defensive",
        capabilities=[
            "waf_rule_management",
            "security_group_modification",
            "rag_knowledge_query",
            "compliance_report_generation",
            "auto_remediation",
        ],
        tool_schema=[
            {
                "name": "update_waf_acl",
                "description": "Update WAF ACL rules",
                "parameters": {"rule_name": "string", "attack_type": "string", "action": "string"},
            },
            {
                "name": "modify_security_group",
                "description": "Modify security group rules",
                "parameters": {"group_id": "string", "rule_action": "string", "port": "integer"},
            },
            {
                "name": "query_knowledge_base",
                "description": "Query RAG knowledge base",
                "parameters": {"attack_vector": "string"},
            },
            {
                "name": "generate_compliance_report",
                "description": "Generate SOC 2 compliance report",
                "parameters": {"campaign_id": "string", "findings": "string"},
            },
        ],
        cost_per_run_usd=0.06,
        tags={"role": "defensive", "project": "purpleops"},
    )

    logger.info(f"[REGISTRY] ✅ Registered {len(results)} PurpleOps agents")
    return results
