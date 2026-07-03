"""
Tests for health check endpoints (no auth required).
"""
import pytest


@pytest.mark.unit
async def test_root_endpoint(async_client):
    """GET / should return service info."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "PurpleOps"
    assert data["status"] == "operational"


@pytest.mark.unit
async def test_api_health_endpoint(async_client):
    """GET /api/health should return OK."""
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"


@pytest.mark.unit
async def test_health_endpoint(async_client):
    """GET /health should return healthy status."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
