"""PurpleOps LLM provider abstraction.

Hard-cut to DeepSeek as primary/default. Bedrock stays available as a
switchable alternative for users with prior commitments via LLM_PROVIDER=bedrock.
Ollama is the local-dev fallback.
"""
from src.llm.provider import (
    LLMProvider,
    DeepSeekProvider,
    OllamaProvider,
    BedrockProvider,
    get_provider,
    TaskResult,
)

__all__ = [
    "LLMProvider",
    "DeepSeekProvider",
    "OllamaProvider",
    "BedrockProvider",
    "get_provider",
    "TaskResult",
]
