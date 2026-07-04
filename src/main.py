"""
PurpleOps - Autonomous Purple Teaming Platform
=================================================
FastAPI application entry point.

Architecture:
  - CoordinatorAgent: Supervisor that orchestrates Red/Blue agents
  - AgentRegistry: AWS Bedrock AgentCore registry for agent versioning
  - RedAgent: Offensive LangChain agent (Bedrock-powered)
  - BlueAgent: Defensive LangChain agent (Bedrock-powered)
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

import boto3
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from src.config import Config
from src.agents.coordinator_agent import CoordinatorAgent
from src.core.agent_registry import AgentRegistry, register_sentinel_agents
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="PurpleOps",
    description="Autonomous Purple Teaming Platform — Attack to Defend. Autonomously.",
    version="2.0.0",
)

# ── Singletons ───────────────────────────────────────────────────────────────
coordinator = CoordinatorAgent()
registry = AgentRegistry()

dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
campaigns_table = dynamodb.Table(Config.DYNAMODB_TABLE_CAMPAIGNS)


# ── Request / Response Models ────────────────────────────────────────────────

class CampaignRequest(BaseModel):
    target_url: str
    target_description: str
    iam_role: str = "test-role"
    max_attack_turns: int = 5
    max_defense_turns: int = 5
    max_total_turns: int = 15
    token_budget: int = 50000


class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    summary: dict
    timestamp: str


# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Register all agents in the registry on startup."""
    logger.info("[STARTUP] Registering PurpleOps agents in registry...")
    try:
        results = await register_sentinel_agents(registry)
        logger.info(f"[STARTUP] ✅ Registered {len(results)} agents")
    except Exception as e:
        logger.warning(f"[STARTUP] Agent registration skipped: {e}")


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "PurpleOps",
        "tagline": "Attack to Defend. Autonomously.",
        "version": "2.0.0",
        "status": "operational",
        "architecture": {
            "coordinator": "Central Supervisor Agent (LangGraph pattern)",
            "red_agent": "Offensive AI (Bedrock Claude 3.5 Sonnet)",
            "blue_agent": "Defensive AI (Bedrock Claude 3.5 Sonnet)",
            "registry": "AWS Bedrock AgentCore Registry",
        },
    }


@app.post("/campaigns/start", response_model=CampaignResponse)
async def start_campaign(request: CampaignRequest):
    """
    Start a supervised purple-teaming campaign.

    The Coordinator Agent manages the full Red↔Blue loop:
    - Enforces token budgets and turn limits
    - Prevents infinite attack/defense loops
    - Generates deterministic audit trails
    - Produces final compliance report
    """
    campaign_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    try:
        options = {
            "max_attack_turns": request.max_attack_turns,
            "max_defense_turns": request.max_defense_turns,
            "max_total_turns": request.max_total_turns,
            "token_budget": request.token_budget,
        }

        # Run the supervised campaign via Coordinator
        state = await coordinator.run_campaign(
            campaign_id=campaign_id,
            target=request.target_url,
            options=options,
        )

        summary = coordinator.get_campaign_summary(state)

        return CampaignResponse(
            campaign_id=campaign_id,
            status=state.phase.value,
            summary=summary,
            timestamp=timestamp,
        )

    except Exception as e:
        logger.error(f"Campaign {campaign_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Campaign failed: {str(e)}")


@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    """Retrieve campaign details from DynamoDB."""
    try:
        response = campaigns_table.get_item(Key={"campaign_id": campaign_id})
        if "Item" not in response:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return response["Item"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Registry Routes ──────────────────────────────────────────────────────────

@app.get("/registry/agents")
async def list_registry_agents(agent_type: Optional[str] = None, capability: Optional[str] = None):
    """
    List all agents in the PurpleOps registry.
    Equivalent to browsing Docker Hub for cybersecurity agents.
    """
    try:
        agents = await registry.list_agents(agent_type=agent_type, capability=capability)
        return {
            "total": len(agents),
            "agents": agents,
            "registry": "AWS Bedrock AgentCore + DynamoDB",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/registry/agents/{agent_id}")
async def get_registry_agent(agent_id: str, version: str = "latest"):
    """
    Pull an agent manifest from the registry.
    Equivalent to `docker pull sentinel-red-agent:latest`.
    """
    try:
        manifest = await registry.pull_agent(agent_id, version)
        if not manifest:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id}:{version} not found")
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/registry/agents/{agent_id}/deprecate")
async def deprecate_registry_agent(agent_id: str, version: str):
    """Deprecate an agent version in the registry."""
    try:
        success = await registry.deprecate_agent(agent_id, version)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"status": "deprecated", "agent_id": agent_id, "version": version}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "coordinator": "operational",
            "registry": "operational",
            "bedrock": "connected",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
