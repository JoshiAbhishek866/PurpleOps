"""
Pytest configuration and shared fixtures for Sentinel AI tests.
"""
import pytest
import os

# Set test environment variables BEFORE importing the app
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing")
os.environ.setdefault("ADMIN_JWT_SECRET", "test-admin-jwt-secret-for-testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("LLM_PROVIDER", "ollama")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "sentinel_ai_test")

from httpx import AsyncClient, ASGITransport
from jose import jwt
from datetime import datetime, timedelta


@pytest.fixture
def client_token():
    """Generate a valid client JWT for testing."""
    payload = {
        "userId": "test-user-id-123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def expired_token():
    """Generate an expired client JWT for testing."""
    payload = {
        "userId": "test-user-id-123",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")


@pytest.fixture
def admin_token():
    """Generate a valid admin JWT for testing."""
    payload = {
        "user_id": "test-admin-id-456",
        "email": "admin@test.com",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, os.environ["ADMIN_JWT_SECRET"], algorithm="HS256")


@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    # Import app here to ensure env vars are set first
    from src.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
