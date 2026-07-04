"""Campaign API routes — POST start, GET status, POST stop."""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from src.agents.coordinator_agent import CoordinatorAgent, CampaignState
from src.config import Config

router = APIRouter()


class CampaignStartRequest(BaseModel):
    target_url: str
    target_description: str = ""
    iam_role: str = "test-role"
    max_attack_turns: int = 5
    max_defense_turns: int = 5
    max_total_turns: int = 15
    token_budget: int = 50000


class CampaignStartResponse(BaseModel):
    campaign_id: str
    status: str
    summary: dict
    timestamp: str


class CampaignStatusResponse(BaseModel):
    campaign_id: str
    status: str
    target: Optional[str] = None
    current_turn: int = 0
    tokens_used: int = 0
    vulnerabilities_found: int = 0
    remediations_applied: int = 0


class CampaignStopResponse(BaseModel):
    campaign_id: str
    status: str


# ── In-memory campaign store (test-friendly; replace with DynamoDB in prod) ──
_campaign_store: dict[str, dict] = {}
_state_lock = asyncio.Lock()


def _get_table(request: Request):
    """Get DynamoDB table from app state, or fall back to in-memory store."""
    table = getattr(request.app.state, "campaigns_table", None)
    return table


@router.post("/campaigns/start", response_model=CampaignStartResponse)
async def start_campaign(
    req: CampaignStartRequest, background_tasks: BackgroundTasks
):
    campaign_id = str(uuid.uuid4())
    state = CampaignState(
        campaign_id=campaign_id,
        target=req.target_url,
        max_attack_turns=req.max_attack_turns,
        max_defense_turns=req.max_defense_turns,
        max_total_turns=req.max_total_turns,
        token_budget=req.token_budget,
    )

    async def _run():
        try:
            coordinator = CoordinatorAgent()
            await coordinator.run_campaign(state)
        except Exception as exc:
            state.coordinator_decisions.append(f"error: {exc!s}")

    background_tasks.add_task(_run)

    record = {
        "campaign_id": campaign_id,
        "status": "started",
        "target": req.target_url,
        "current_turn": 0,
        "tokens_used": 0,
        "vulnerabilities_found": 0,
        "remediations_applied": 0,
    }
    async with _state_lock:
        _campaign_store[campaign_id] = record

    return CampaignStartResponse(
        campaign_id=campaign_id,
        status="started",
        summary={"target": req.target_url, "iam_role": req.iam_role},
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignStatusResponse)
async def get_campaign(campaign_id: str, request: Request):
    async with _state_lock:
        record = _campaign_store.get(campaign_id)

    table = _get_table(request)
    if table is not None:
        try:
            resp = table.get_item(Key={"campaign_id": campaign_id})
            item = resp.get("Item")
            if item:
                record = {
                    "campaign_id": campaign_id,
                    "status": item.get("status", "unknown"),
                    "target": item.get("target"),
                    "current_turn": int(item.get("current_turn", 0)),
                    "tokens_used": int(item.get("tokens_used", 0)),
                    "vulnerabilities_found": len(item.get("vulnerabilities_found", [])),
                    "remediations_applied": len(item.get("remediations_applied", [])),
                }
        except Exception:
            pass

    if not record:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    return CampaignStatusResponse(**record)


@router.post("/campaigns/{campaign_id}/stop", response_model=CampaignStopResponse)
async def stop_campaign(campaign_id: str, request: Request):
    async with _state_lock:
        record = _campaign_store.get(campaign_id)

    if not record:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    record["status"] = "aborted"
    async with _state_lock:
        _campaign_store[campaign_id] = record

    return CampaignStopResponse(campaign_id=campaign_id, status="aborted")
