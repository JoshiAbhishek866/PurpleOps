"""
Multi-LLM Provider for Sentinel AI

Abstracts LLM calls behind a unified interface so customers
can choose their provider (Ollama, OpenAI, AWS Bedrock, Azure OpenAI).
Customers can also bring their own API keys — reducing your LLM costs to zero.

All providers are fail-graceful: if one fails, the caller handles it.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class LLMProviderBase(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 2048):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text from a prompt. Returns the generated text."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class OllamaProvider(LLMProviderBase):
    """Local Ollama LLM provider (default, free, no API key needed)."""

    def __init__(self, model: str = "llama2", url: str = "http://localhost:11434", **kwargs):
        super().__init__(model, **kwargs)
        self.url = url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        import aiohttp
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.url}/api/generate", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                raise RuntimeError(f"Ollama error: {resp.status}")

    async def health_check(self) -> bool:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.url}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False


class OpenAIProvider(LLMProviderBase):
    """OpenAI API provider (GPT-4, GPT-3.5-turbo)."""

    def __init__(self, model: str = "gpt-4", api_key: str = None, **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not set — provider will be unavailable")

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        import aiohttp
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers, json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                err = await resp.text()
                raise RuntimeError(f"OpenAI error {resp.status}: {err}")

    async def health_check(self) -> bool:
        return bool(self.api_key)


class BedrockProvider(LLMProviderBase):
    """AWS Bedrock LLM provider (Claude, Titan, etc.)."""

    def __init__(self, model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
                 region: str = "us-east-1", **kwargs):
        super().__init__(model, **kwargs)
        self.region = region

    @property
    def provider_name(self) -> str:
        return "bedrock"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        import boto3
        import json
        client = boto3.client("bedrock-runtime", region_name=self.region)

        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = client.invoke_model(
            modelId=self.model,
            body=json.dumps(body),
            contentType="application/json",
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    async def health_check(self) -> bool:
        try:
            import boto3
            client = boto3.client("bedrock-runtime", region_name=self.region)
            # Just check that the client was created successfully
            return True
        except Exception:
            return False


class AzureOpenAIProvider(LLMProviderBase):
    """Azure OpenAI Service provider."""

    def __init__(self, model: str = "gpt-4", **kwargs):
        super().__init__(model, **kwargs)
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    @property
    def provider_name(self) -> str:
        return "azure_openai"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        import aiohttp
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.endpoint}/openai/deployments/{self.model}/chat/completions?api-version={self.api_version}"
        payload = {"messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                err = await resp.text()
                raise RuntimeError(f"Azure OpenAI error {resp.status}: {err}")

    async def health_check(self) -> bool:
        return bool(self.api_key and self.endpoint)


# ==================== Provider Factory ====================

_PROVIDERS = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "bedrock": BedrockProvider,
    "azure_openai": AzureOpenAIProvider,
}


def create_llm_provider(provider_name: str = None, **kwargs) -> LLMProviderBase:
    """
    Factory: create an LLM provider by name.

    Args:
        provider_name: One of 'ollama', 'openai', 'bedrock', 'azure_openai'.
                       Defaults to LLM_PROVIDER env var or 'ollama'.
    """
    name = (provider_name or os.getenv("LLM_PROVIDER", "ollama")).lower()
    cls = _PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown LLM provider: {name}. Available: {list(_PROVIDERS.keys())}")
    return cls(**kwargs)


def get_available_providers() -> List[str]:
    """Return list of all registered provider names."""
    return list(_PROVIDERS.keys())
