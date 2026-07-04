"""Tests for src/llm/provider.py — request shape and token-usage flow into TaskResult."""
import os
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key-123")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_REGION", "us-east-1")

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from src.llm.provider import (
    LLMProvider,
    DeepSeekProvider,
    OllamaProvider,
    BedrockProvider,
    get_provider,
    TaskResult,
)


# ─────────────────────────────────────────────
# Factory tests
# ─────────────────────────────────────────────

class TestGetProviderFactory:
    def setup_method(self):
        # Ensure LLM_PROVIDER doesn't leak between tests
        for k in ("LLM_PROVIDER", "DEEPSEEK_API_KEY", "OLLAMA_BASE_URL"):
            os.environ.pop(k, None)

    def test_default_factory_returns_deepseek(self):
        os.environ.pop("LLM_PROVIDER", None)
        provider = get_provider()
        assert isinstance(provider, DeepSeekProvider)
        assert provider.name == "deepseek"

    def test_factory_returns_bedrock_when_opted_in(self):
        os.environ["LLM_PROVIDER"] = "bedrock"
        provider = get_provider()
        assert isinstance(provider, BedrockProvider)
        assert provider.name == "bedrock"

    def test_factory_returns_ollama_when_opted_in(self):
        os.environ["LLM_PROVIDER"] = "ollama"
        provider = get_provider()
        assert isinstance(provider, OllamaProvider)
        assert provider.name == "ollama"

    def test_factory_falls_back_to_deepseek_on_unknown(self):
        os.environ["LLM_PROVIDER"] = "gibberish-provider"
        provider = get_provider()
        assert isinstance(provider, DeepSeekProvider)


# ─────────────────────────────────────────────
# DeepSeek request shape (mock httpx)
# ─────────────────────────────────────────────

class TestDeepSeekRequestShape:
    def test_request_url_headers_body(self):
        """Sync wrapper around async test — asserts URL, headers, body shape."""
        asyncio.run(self._async_test_request_url_headers_body())

    async def _async_test_request_url_headers_body(self):
        captured = {}

        async def fake_post(self, url, json=None, headers=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            req = MagicMock()
            req.status_code = 200
            req.json.return_value = {
                "choices": [{"message": {"content": "Hello from DeepSeek"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
            req.raise_for_status = MagicMock()
            return req

        provider = DeepSeekProvider(api_key="test-key-123", base_url="https://api.deepseek.com/v1")

        with patch.object(httpx.AsyncClient, "post", fake_post):
            result = await provider.complete(
                messages=[{"role": "user", "content": "Hi"}],
                model="deepseek-chat",
                temperature=0.5,
                max_tokens=100,
                agent_id="test-agent",
            )

        # URL shape
        assert captured["url"] == "https://api.deepseek.com/v1/chat/completions"
        # Headers shape
        assert captured["headers"]["Authorization"] == "Bearer test-key-123"
        assert captured["headers"]["Content-Type"] == "application/json"
        # Body shape
        assert captured["json"]["model"] == "deepseek-chat"
        assert captured["json"]["messages"] == [{"role": "user", "content": "Hi"}]
        assert captured["json"]["temperature"] == 0.5
        assert captured["json"]["max_tokens"] == 100
        assert captured["json"]["stream"] is False

        # TaskResult shape
        assert result.success is True
        assert result.data == "Hello from DeepSeek"
        assert result.tokens_used == 15  # ← usage.total_tokens flows into TaskResult.tokens_used
        assert result.agent_id == "test-agent"
        assert result.duration_ms >= 0

    def test_usage_total_tokens_flows_into_taskresult(self):
        """Sync wrapper — CRITICAL assertion: usage.total_tokens → TaskResult.tokens_used."""
        asyncio.run(self._async_test_usage_total_tokens_flows_into_taskresult())

    async def _async_test_usage_total_tokens_flows_into_taskresult(self):
        provider = DeepSeekProvider(api_key="k")

        async def fake_post(self, url, json=None, headers=None, **kwargs):
            req = MagicMock()
            req.status_code = 200
            req.json.return_value = {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
            req.raise_for_status = MagicMock()
            return req

        with patch.object(httpx.AsyncClient, "post", fake_post):
            result = await provider.complete(
                messages=[{"role": "user", "content": "x"}],
            )

        assert result.tokens_used == 150

    def test_missing_api_key_returns_failure(self):
        """Sync wrapper — without DEEPSEEK_API_KEY, returns TaskResult(success=False)."""
        asyncio.run(self._async_test_missing_api_key_returns_failure())

    async def _async_test_missing_api_key_returns_failure(self):
        provider = DeepSeekProvider(api_key="")  # explicitly empty
        result = await provider.complete(messages=[{"role": "user", "content": "x"}])
        assert result.success is False
        assert "DEEPSEEK_API_KEY" in (result.error or "")


# ─────────────────────────────────────────────
# count_tokens
# ─────────────────────────────────────────────

class TestCountTokens:
    def test_deepseek_count_tokens_heuristic(self):
        provider = DeepSeekProvider(api_key="k")
        assert provider.count_tokens("hello world") >= 1
        assert provider.count_tokens("") >= 1  # min 1

    def test_base_count_tokens_heuristic(self):
        # LLMProvider is abstract; DeepSeekProvider inherits the default count_tokens unchanged.
        # Base impl uses char/4 heuristic.
        provider = DeepSeekProvider(api_key="k")
        assert provider.count_tokens("abcdefgh") == 2  # 8/4
