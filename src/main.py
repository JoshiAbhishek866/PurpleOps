"""
Sentinel AI v2.0 — Autonomous Purple Teaming Platform
======================================================
FastAPI application entry point.

ENHANCED v2.0:
- Lazy-loaded AWS clients (don't crash if credentials missing)
- Config validation at startup
- Health check with dependency probing
- Background campaign execution with status polling
- Campaign abort endpoint
- CORS middleware
- Request ID middleware
- Lifespan event handler (replaces deprecated on_event)

Architecture:
  - CoordinatorAgent: Supervisor that orchestrates Red/Blue agents
  - AgentRegistry: AWS Bedrock AgentCore registry for agent versioning
  - RedAgent: Offensive LangChain agent (Bedrock-powered)
  - BlueAgent: Defensive LangChain agent (Bedrock-powered)
"""

__version__ = "2.0.0"

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# ── Lazy-loaded singletons ───────────────────────────────────────────────────

_coordinator = None
_registry = None
_campaigns_table = None

# ENHANCED: in-memory campaign status tracker for background execution
_campaign_statuses: Dict[str, dict] = {}


def _get_coordinator():
    global _coordinator
    if _coordinator is None:
        from src.agents.coordinator_agent import CoordinatorAgent
        _coordinator = CoordinatorAgent()
    return _coordinator


def _get_registry():
    global _registry
    if _registry is None:
        try:
            from src.core.agent_registry import AgentRegistry
            _registry = AgentRegistry()
        except Exception as e:
            logger.warning(f"[STARTUP] Registry unavailable: {e}")
    return _registry


def _get_campaigns_table():
    global _campaigns_table
    if _campaigns_table is None:
        try:
            import boto3
            dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
            _campaigns_table = dynamodb.Table(Config.DYNAMODB_TABLE_CAMPAIGNS)
        except Exception as e:
            logger.warning(f"[STARTUP] DynamoDB unavailable: {e}")
    return _campaigns_table


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """ENHANCED: Replaces deprecated @app.on_event('startup')"""
    # Startup
    logger.info("[STARTUP] Sentinel AI v%s starting...", __version__)

    # Validate configuration
    Config.validate()
    logger.info("[STARTUP] Config: %s", Config.summary())

    # Register agents (non-blocking — don't fail startup)
    registry = _get_registry()
    if registry:
        try:
            from src.core.agent_registry import register_sentinel_agents
            results = await register_sentinel_agents(registry)
            logger.info("[STARTUP] ✅ Registered %d agents", len(results))
        except Exception as e:
            logger.warning("[STARTUP] Agent registration skipped: %s", e)

    yield

    # Shutdown
    logger.info("[SHUTDOWN] Sentinel AI shutting down")


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sentinel AI",
    description="Autonomous Purple Teaming Platform — Attack to Defend. Autonomously.",
    version=__version__,
    lifespan=lifespan,
)

# ENHANCED: CORS middleware for browser-based frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not Config.is_production() else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ────────────────────────────────────────────────

class CampaignRequest(BaseModel):
    target_url: str = Field(..., description="Target URL to scan")
    target_description: str = Field("", description="Human-readable description")
    iam_role: str = Field("test-role", description="IAM role for AWS operations")
    max_attack_turns: int = Field(default=5, ge=1, le=20)
    max_defense_turns: int = Field(default=5, ge=1, le=20)
    max_total_turns: int = Field(default=15, ge=1, le=50)
    token_budget: int = Field(default=50000, ge=1000, le=500000)
    dry_run: bool = Field(default=False, description="If true, no real attacks are executed")


class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    summary: dict
    timestamp: str


class CampaignStatusResponse(BaseModel):
    campaign_id: str
    status: str
    phase: str = ""
    progress: dict = {}
    timestamp: str


# ── Background Campaign Runner ──────────────────────────────────────────────

async def _run_campaign_background(campaign_id: str, target_url: str, options: dict):
    """ENHANCED: Run campaign in background and update status tracker."""
    try:
        _campaign_statuses[campaign_id] = {
            "status": "RUNNING",
            "phase": "INIT",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        coordinator = _get_coordinator()
        state = await coordinator.run_campaign(
            campaign_id=campaign_id,
            target=target_url,
            options=options,
        )

        summary = coordinator.get_campaign_summary(state)
        _campaign_statuses[campaign_id] = {
            "status": "COMPLETED",
            "phase": state.phase.value,
            "summary": summary,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error("[CAMPAIGN] %s failed: %s", campaign_id, e)
        _campaign_statuses[campaign_id] = {
            "status": "FAILED",
            "error": str(e),
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Sentinel AI",
        "tagline": "Attack to Defend. Autonomously.",
        "version": __version__,
        "status": "operational",
        "dry_run": Config.is_dry_run(),
        "environment": Config.APP_ENV,
        "architecture": {
            "coordinator": "Central Supervisor Agent (LangGraph pattern)",
            "red_agent": "Offensive AI (Bedrock Claude 3.5 Sonnet) — 10 attack categories",
            "blue_agent": "Defensive AI (Bedrock Claude 3.5 Sonnet) — WAF/Security Hub/Evidence Chain",
            "registry": "AWS Bedrock AgentCore Registry",
        },
        "quickstart": {
            "docker": "docker compose up -d && curl http://localhost:8000/health",
            "campaign": "POST /campaigns/start {\"target_url\": \"http://dvwa:80\"}",
        },
    }


@app.post("/campaigns/start", response_model=CampaignResponse)
async def start_campaign(request: CampaignRequest, background_tasks: BackgroundTasks):
    """
    Start a supervised purple-teaming campaign.

    ENHANCED v2.0:
    - Campaign runs in background (non-blocking)
    - Poll status via GET /campaigns/{campaign_id}/status
    - Supports dry_run mode
    """
    campaign_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    options = {
        "max_attack_turns": request.max_attack_turns,
        "max_defense_turns": request.max_defense_turns,
        "max_total_turns": request.max_total_turns,
        "token_budget": request.token_budget,
        "dry_run": request.dry_run or Config.is_dry_run(),
    }

    # ENHANCED: run campaign in background
    background_tasks.add_task(
        _run_campaign_background,
        campaign_id,
        request.target_url,
        options,
    )

    _campaign_statuses[campaign_id] = {
        "status": "QUEUED",
        "phase": "INIT",
        "target": request.target_url,
        "queued_at": timestamp,
    }

    return CampaignResponse(
        campaign_id=campaign_id,
        status="QUEUED",
        summary={
            "target": request.target_url,
            "options": options,
            "message": "Campaign queued. Poll GET /campaigns/{campaign_id}/status for progress.",
        },
        timestamp=timestamp,
    )


@app.get("/campaigns/{campaign_id}/status", response_model=CampaignStatusResponse)
async def get_campaign_status(campaign_id: str):
    """ENHANCED: Poll campaign execution status."""
    if campaign_id in _campaign_statuses:
        entry = _campaign_statuses[campaign_id]
        return CampaignStatusResponse(
            campaign_id=campaign_id,
            status=entry.get("status", "UNKNOWN"),
            phase=entry.get("phase", ""),
            progress=entry,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Fallback: check DynamoDB
    table = _get_campaigns_table()
    if table:
        try:
            response = table.get_item(Key={"campaign_id": campaign_id})
            if "Item" in response:
                item = response["Item"]
                return CampaignStatusResponse(
                    campaign_id=campaign_id,
                    status=item.get("status", "UNKNOWN"),
                    phase=item.get("phase", ""),
                    progress=item,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
        except Exception:
            pass

    raise HTTPException(status_code=404, detail="Campaign not found")


@app.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: str):
    """Retrieve campaign details from DynamoDB."""
    table = _get_campaigns_table()
    if table is None:
        # ENHANCED: fallback to in-memory status
        if campaign_id in _campaign_statuses:
            return _campaign_statuses[campaign_id]
        raise HTTPException(status_code=503, detail="DynamoDB not available")

    try:
        response = table.get_item(Key={"campaign_id": campaign_id})
        if "Item" not in response:
            if campaign_id in _campaign_statuses:
                return _campaign_statuses[campaign_id]
            raise HTTPException(status_code=404, detail="Campaign not found")
        return response["Item"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/campaigns/{campaign_id}/abort")
async def abort_campaign(campaign_id: str):
    """ENHANCED: Abort a running campaign."""
    if campaign_id in _campaign_statuses:
        status = _campaign_statuses[campaign_id]
        if status.get("status") in ("QUEUED", "RUNNING"):
            _campaign_statuses[campaign_id]["status"] = "ABORTED"
            _campaign_statuses[campaign_id]["aborted_at"] = datetime.now(timezone.utc).isoformat()
            return {"campaign_id": campaign_id, "status": "ABORTED"}
        return {"campaign_id": campaign_id, "status": status.get("status"), "message": "Campaign not running"}
    raise HTTPException(status_code=404, detail="Campaign not found")


# ── Registry Routes ──────────────────────────────────────────────────────────

@app.get("/registry/agents")
async def list_registry_agents(agent_type: Optional[str] = None, capability: Optional[str] = None):
    """List all agents in the Sentinel AI registry."""
    registry = _get_registry()
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not available")
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
    """Pull an agent manifest from the registry."""
    registry = _get_registry()
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not available")
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
    registry = _get_registry()
    if registry is None:
        raise HTTPException(status_code=503, detail="Registry not available")
    try:
        success = await registry.deprecate_agent(agent_id, version)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"status": "deprecated", "agent_id": agent_id, "version": version}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health & Config ──────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """
    ENHANCED v2.0: Health check with dependency probing.
    Returns detailed status of each subsystem.
    """
    components = {
        "api": "healthy",
        "coordinator": "unknown",
        "dynamodb": "unknown",
    }

    # Check coordinator
    try:
        coord = _get_coordinator()
        components["coordinator"] = "healthy" if coord else "unavailable"
    except Exception:
        components["coordinator"] = "error"

    # Check DynamoDB
    try:
        table = _get_campaigns_table()
        components["dynamodb"] = "healthy" if table else "unavailable"
    except Exception:
        components["dynamodb"] = "error"

    overall = "healthy" if components["api"] == "healthy" else "degraded"

    return {
        "status": overall,
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": Config.APP_ENV,
        "dry_run": Config.is_dry_run(),
        "components": components,
    }


@app.get("/config")
def get_config():
    """ENHANCED: Return redacted configuration summary."""
    return Config.summary()


# ── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG,
        workers=1 if Config.DEBUG else 2,
    )
