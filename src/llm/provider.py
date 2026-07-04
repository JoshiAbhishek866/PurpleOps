"""LLM provider abstraction.

Three providers:
- DeepSeekProvider (PRIMARY, default): https://api.deepseek.com/v1
- OllamaProvider (local-dev): http://localhost:11434
- BedrockProvider (switchable alternative for users with prior commitments)

Factory `get_provider()` reads LLM_PROVIDER env var and defaults to deepseek.
"""
from __future__ import annotations

import os
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# TaskResult contract (used by every provider)
# ─────────────────────────────────────────────

@dataclass
class TaskResult:
    """
    Standardized result returned by every LLMProvider.complete() call.
    Fields: success, data, error, tokens_used, duration_ms, agent_id, timestamp.
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0
    agent_id: str = ""
    timestamp: str = field(default_factory=lambda: __import__("datetime").datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────
# Abstract base
# ─────────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract LLM provider. Implementations: DeepSeekProvider, OllamaProvider, BedrockProvider."""

    name: str = "abstract"

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        agent_id: str = "",
        **kwargs,
    ) -> TaskResult:
        """Run a chat completion. Returns a TaskResult with tokens_used populated."""

    async def stream(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a completion. Default impl falls back to complete()."""
        result = await self.complete(
            messages, model=model, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        if result.success and isinstance(result.data, str):
            for chunk in result.data.split(" "):
                yield chunk + " "
        else:
            yield result.error or ""

    def count_tokens(self, text: str) -> int:
        """Approximate token count. Default impl uses char/4 heuristic."""
        return max(1, len(text) // 4)


# ─────────────────────────────────────────────
# DeepSeek provider (PRIMARY, DEFAULT)
# ─────────────────────────────────────────────

class DeepSeekProvider(LLMProvider):
    """DeepSeek API provider (https://api.deepseek.com/v1). DEFAULT in PurpleOps."""

    name = "deepseek"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: str = "deepseek-chat",
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = (base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")).rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        agent_id: str = "",
        **kwargs,
    ) -> TaskResult:
        if not self.api_key:
            return TaskResult(
                success=False,
                error="DEEPSEEK_API_KEY not set",
                agent_id=agent_id,
            )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            return TaskResult(
                success=False,
                error=f"DeepSeek HTTP error: {exc}",
                duration_ms=int((time.time() - t0) * 1000),
                agent_id=agent_id,
            )

        duration_ms = int((time.time() - t0) * 1000)
        usage = body.get("usage", {}) or {}
        tokens_used = int(
            usage.get("total_tokens", 0)
            or (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))
        )
        text = ""
        for choice in body.get("choices", []):
            text += choice.get("message", {}).get("content", "") or ""

        return TaskResult(
            success=True,
            data=text,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            agent_id=agent_id,
        )


# ─────────────────────────────────────────────
# Ollama provider (LOCAL DEV)
# ─────────────────────────────────────────────

class OllamaProvider(LLMProvider):
    """Ollama local provider (http://localhost:11434). Use for local-dev / no API key."""

    name = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_model: str = "llama3.1",
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        agent_id: str = "",
        **kwargs,
    ) -> TaskResult:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        t0 = time.time()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            return TaskResult(
                success=False,
                error=f"Ollama HTTP error: {exc}",
                duration_ms=int((time.time() - t0) * 1000),
                agent_id=agent_id,
            )

        duration_ms = int((time.time() - t0) * 1000)
        text = body.get("message", {}).get("content", "") or ""
        # Ollama reports prompt_eval_count + eval_count
        tokens_used = int(
            body.get("eval_count", 0) + body.get("prompt_eval_count", 0)
        )
        return TaskResult(
            success=True,
            data=text,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            agent_id=agent_id,
        )


# ─────────────────────────────────────────────
# Bedrock provider (SWITCHABLE ALTERNATIVE)
# ─────────────────────────────────────────────

class BedrockProvider(LLMProvider):
    """AWS Bedrock provider. SWITCHABLE alternative (LLM_PROVIDER=bedrock) — NOT default."""

    name = "bedrock"

    def __init__(
        self,
        region: Optional[str] = None,
        default_model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
    ):
        try:
            import boto3  # lazy import — preserves Bug #1 fix
        except ImportError as exc:
            raise ImportError("boto3 required for BedrockProvider") from exc
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.default_model = default_model
        self._client = None  # lazy

    def _get_client(self):
        if self._client is None:
            import boto3
            self._client = boto3.client("bedrock-runtime", region_name=self.region)
        return self._client

    async def complete(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        agent_id: str = "",
        **kwargs,
    ) -> TaskResult:
        import asyncio
        client = self._get_client()
        model_id = model or self.default_model

        # Convert messages to Bedrock converse format
        converse_messages = []
        system_parts = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append({"text": content})
            else:
                converse_messages.append({"role": role, "content": [{"text": content}]})

        request = {
            "modelId": model_id,
            "messages": converse_messages,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
        }
        if system_parts:
            request["system"] = system_parts

        t0 = time.time()
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.converse(**request))
        except Exception as exc:
            return TaskResult(
                success=False,
                error=f"Bedrock converse error: {exc}",
                duration_ms=int((time.time() - t0) * 1000),
                agent_id=agent_id,
            )

        duration_ms = int((time.time() - t0) * 1000)
        text = ""
        try:
            output = response.get("output", {}).get("message", {}).get("content", [])
            for block in output:
                text += block.get("text", "") or ""
        except Exception:
            pass
        usage = response.get("usage", {}) or {}
        tokens_used = int(usage.get("inputTokens", 0) + usage.get("outputTokens", 0))

        return TaskResult(
            success=True,
            data=text,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            agent_id=agent_id,
        )


# ─────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────

_PROVIDERS = {
    "deepseek": DeepSeekProvider,
    "ollama": OllamaProvider,
    "bedrock": BedrockProvider,
}

_DEFAULT = "deepseek"


def get_provider(name: Optional[str] = None, **kwargs) -> LLMProvider:
    """
    Factory: get the active LLM provider.

    Resolution order:
      1. Explicit `name` argument
      2. LLM_PROVIDER env var
      3. Default: "deepseek" (hard-cut primary)

    Bedrock must be EXPLICITLY opted into via LLM_PROVIDER=bedrock.
    """
    chosen = (name or os.getenv("LLM_PROVIDER", _DEFAULT)).lower().strip()
    cls = _PROVIDERS.get(chosen, _PROVIDERS[_DEFAULT])
    if chosen not in _PROVIDERS:
        logger.warning(
            "Unknown LLM_PROVIDER=%r; falling back to DeepSeekProvider (default)",
            chosen,
        )
    return cls(**kwargs)


__all__ = [
    "LLMProvider",
    "DeepSeekProvider",
    "OllamaProvider",
    "BedrockProvider",
    "TaskResult",
    "get_provider",
]
