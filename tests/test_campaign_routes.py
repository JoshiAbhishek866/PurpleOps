"""Tests for src/routes/campaigns.py — POST start, GET status, POST stop."""
import os
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")

from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.routes import campaigns as campaigns_routes


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(campaigns_routes.router, prefix="/api/v1")
    # Mock app.state.campaigns_table to None to avoid AWS calls
    app.state.campaigns_table = None
    return TestClient(app)


def test_start_campaign_returns_id(client):
    """POST /api/v1/campaigns/start returns campaign_id, status, summary, timestamp."""
    with patch.object(campaigns_routes, "CoordinatorAgent") as MockCoord:
        mock_inst = MagicMock()
        mock_inst.run_campaign = AsyncMock(return_value=None)
        MockCoord.return_value = mock_inst

        resp = client.post(
            "/api/v1/campaigns/start",
            json={
                "target_url": "https://example.com",
                "target_description": "Test target",
                "max_attack_turns": 3,
                "max_defense_turns": 3,
                "max_total_turns": 5,
                "token_budget": 10000,
            },
        )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "campaign_id" in data
    assert data["status"] == "started"
    assert "summary" in data
    assert "timestamp" in data


def test_get_campaign_returns_record(client):
    """POST start, then GET — record is returned."""
    with patch.object(campaigns_routes, "CoordinatorAgent") as MockCoord:
        mock_inst = MagicMock()
        mock_inst.run_campaign = AsyncMock(return_value=None)
        MockCoord.return_value = mock_inst

        start_resp = client.post(
            "/api/v1/campaigns/start",
            json={"target_url": "https://example.com"},
        )
    cid = start_resp.json()["campaign_id"]

    get_resp = client.get(f"/api/v1/campaigns/{cid}")
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["campaign_id"] == cid


def test_get_campaign_404_if_missing(client):
    """GET nonexistent campaign → 404."""
    resp = client.get("/api/v1/campaigns/nonexistent-id-xyz")
    assert resp.status_code == 404


def test_stop_campaign_aborts(client):
    """POST start, then POST stop → status='aborted'."""
    with patch.object(campaigns_routes, "CoordinatorAgent") as MockCoord:
        mock_inst = MagicMock()
        mock_inst.run_campaign = AsyncMock(return_value=None)
        MockCoord.return_value = mock_inst

        start_resp = client.post(
            "/api/v1/campaigns/start",
            json={"target_url": "https://example.com"},
        )
    cid = start_resp.json()["campaign_id"]

    stop_resp = client.post(f"/api/v1/campaigns/{cid}/stop")
    assert stop_resp.status_code == 200, stop_resp.text
    assert stop_resp.json()["status"] == "aborted"


def test_stop_campaign_404_if_missing(client):
    """POST stop on nonexistent → 404."""
    resp = client.post("/api/v1/campaigns/nonexistent-id-xyz/stop")
    assert resp.status_code == 404


def test_routes_defined(client):
    """All 3 routes are registered under the campaigns router."""
    paths = [r.path for r in campaigns_routes.router.routes]
    assert "/campaigns/start" in paths
    assert any("/campaigns/{campaign_id}" in p for p in paths)
    assert any("/campaigns/{campaign_id}/stop" in p for p in paths)
