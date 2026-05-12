"""
Tests for authentication enforcement on protected endpoints.
"""
import pytest


@pytest.mark.unit
async def test_campaigns_requires_auth(async_client):
    """POST /campaigns/start should return 401 without token."""
    response = await async_client.post("/campaigns/start", json={
        "target_url": "http://test.example.com",
        "target_description": "Test target",
        "iam_role": "test-role",
        "actor_id": "tester"
    })
    assert response.status_code == 401


@pytest.mark.unit
async def test_campaigns_get_requires_auth(async_client):
    """GET /campaigns/{id} should return 401 without token."""
    response = await async_client.get("/campaigns/some-campaign-id")
    assert response.status_code == 401


@pytest.mark.unit
async def test_agent_execute_requires_auth(async_client):
    """POST /agents/execute/{type} should return 401 without token."""
    response = await async_client.post("/agents/execute/recon", json={"target": "test"})
    assert response.status_code == 401


@pytest.mark.unit
async def test_agent_status_requires_auth(async_client):
    """GET /agents/status should return 401 without token."""
    response = await async_client.get("/agents/status")
    assert response.status_code == 401


@pytest.mark.unit
async def test_results_requires_auth(async_client):
    """GET /results/{id} should return 401 without token."""
    response = await async_client.get("/results/some-result-id")
    assert response.status_code == 401


@pytest.mark.unit
async def test_workflows_requires_auth(async_client):
    """GET /workflows should return 401 without token."""
    response = await async_client.get("/workflows")
    assert response.status_code == 401


@pytest.mark.unit
async def test_expired_token_rejected(async_client, expired_token):
    """Expired token should return 401."""
    response = await async_client.get(
        "/agents/status",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.unit
async def test_invalid_token_rejected(async_client):
    """Garbage token should return 401."""
    response = await async_client.get(
        "/agents/status",
        headers={"Authorization": "Bearer not.a.valid.token"}
    )
    assert response.status_code == 401


@pytest.mark.unit
async def test_security_scan_requires_auth(async_client):
    """POST /api/security/scan should return 401 without token."""
    response = await async_client.post("/api/security/scan", json={
        "workflow": "quick_scan",
        "target": "test.example.com"
    })
    assert response.status_code == 401
