"""Test that TokenBucketRateLimiter is wired into CoordinatorAgent.plan() (Bug #5 regression)."""
import os
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")

import asyncio
from unittest.mock import MagicMock, AsyncMock

from src.agents.coordinator import CoordinatorAgent
from src.agents.coordinator import CampaignState


def test_rate_limiter_instantiated_in_coordinator():
    """CoordinatorAgent.__init__ instantiates a TokenBucketRateLimiter."""
    coord = CoordinatorAgent()
    assert hasattr(coord, "rate_limiter")
    assert coord.rate_limiter is not None


def test_rate_limiter_acquire_called_before_llm():
    """CoordinatorAgent.plan() calls rate_limiter.acquire() before provider.complete()."""
    coord = CoordinatorAgent()

    # Mock the rate limiter to track acquire() calls
    coord.rate_limiter = MagicMock()
    coord.rate_limiter.acquire = AsyncMock()

    # Mock the provider to return a fake TaskResult
    fake_result = MagicMock(success=True, tokens_used=10, data="hello", error=None, duration_ms=0, agent_id="x")
    coord.provider = MagicMock()
    coord.provider.complete = AsyncMock(return_value=fake_result)

    state = CampaignState(campaign_id="t", target="https://example.com")
    result = asyncio.run(coord.plan(state, context=""))

    # Verify acquire was called at least once
    assert coord.rate_limiter.acquire.call_count >= 1
    # Verify provider.complete was called after acquire
    assert coord.provider.complete.call_count >= 1
