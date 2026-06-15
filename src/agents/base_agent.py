"""
Base Agent Class — Sentinel AI v2.0
Foundation for all offensive and defensive agents.

ENHANCED v2.0:
- Exponential backoff with jitter for retries
- Configurable model_id, max_tokens, region, timeout
- Agent lifecycle hooks (on_start, on_complete, on_error)
- Structured JSON logging
- Token bucket rate limiter
- Safe mode and scope enforcement
- Redacted config in get_status()
"""

__version__ = "2.0.0"

import asyncio
import json
import random
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.utils.logger import AgentLogger
from src.utils.helpers import generate_id, format_result


# ── Token Bucket Rate Limiter ────────────────────────────────────────────────

class TokenBucketRateLimiter:
    """
    ENHANCED: Async token-bucket rate limiter.
    Use `await limiter.acquire()` before each request.
    """

    def __init__(self, tokens_per_second: float = 10.0, burst: int = 0):
        self.rate = tokens_per_second
        self.max_tokens = burst if burst > 0 else max(int(tokens_per_second * 2), 1)
        self._tokens = float(self.max_tokens)
        self._last_refill = asyncio.get_event_loop().time() if asyncio._get_running_loop() else 0.0
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Wait until *tokens* are available, then consume them."""
        async with self._lock:
            while True:
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_refill
                self._tokens = min(self.max_tokens, self._tokens + elapsed * self.rate)
                self._last_refill = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                wait = (tokens - self._tokens) / self.rate
                await asyncio.sleep(wait)


# ── Base Agent ───────────────────────────────────────────────────────────────

# Patterns for redacting sensitive config keys
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(key|secret|password|token|credential|auth)", re.IGNORECASE
)


class BaseAgent(ABC):
    """
    Base class for all agents.

    ENHANCED v2.0 additions:
    - Lifecycle hooks: on_start, on_complete, on_error
    - Structured logging via _log()
    - Exponential backoff retry via _retry_with_backoff()
    - Safe mode flag
    - Scope enforcement
    - Rate limiter integration
    """

    def __init__(self, agent_type: str, config: Optional[Dict] = None):
        self.agent_type = agent_type
        self.config = config or {}
        self.logger = AgentLogger(agent_type)
        self.status = "idle"
        self.current_execution_id = None

        # ENHANCED: safe mode — when True, destructive operations are blocked
        self.safe_mode = self.config.get("safe_mode", False)

        # ENHANCED: rate limiter (configurable tokens per second)
        rps = self.config.get("requests_per_second", 10.0)
        self._rate_limiter = TokenBucketRateLimiter(tokens_per_second=rps)

    @abstractmethod
    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Execute the agent.
        Must be implemented by subclasses.

        Args:
            target: Target to scan/analyze
            options: Additional options for execution

        Returns:
            Dict containing execution results
        """
        pass

    # ── Lifecycle Hooks (override in subclasses) ─────────────────────────────

    async def on_start(self, target: str, options: Optional[Dict] = None) -> None:
        """ENHANCED: Called before execute(). Override for setup logic."""
        pass

    async def on_complete(self, result: Dict) -> None:
        """ENHANCED: Called after successful execute(). Override for teardown."""
        pass

    async def on_error(self, error: Exception) -> None:
        """ENHANCED: Called when execute() raises. Override for cleanup."""
        pass

    # ── Core Run Method ──────────────────────────────────────────────────────

    async def run(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Run the agent with error handling, timeout, lifecycle hooks, and logging.

        Args:
            target: Target to scan/analyze
            options: Additional options

        Returns:
            Formatted result dictionary
        """
        self.current_execution_id = generate_id(self.agent_type)
        self.status = "running"
        start_time = datetime.now(timezone.utc)
        timeout = self.config.get("timeout", 300)  # default 5 min

        self.logger.start(target)
        self._log("info", "Agent execution started", target=target, timeout=timeout)

        try:
            # ENHANCED: lifecycle hook
            await self.on_start(target, options)

            # Execute the agent with a hard timeout
            result_data = await asyncio.wait_for(
                self.execute(target, options),
                timeout=timeout
            )

            # Calculate duration
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.complete(duration)

            # Format result
            result = format_result(
                agent_type=self.agent_type,
                target=target,
                data={
                    **result_data,
                    "duration": duration,
                    "execution_id": self.current_execution_id
                },
                status="success"
            )

            self.status = "completed"
            self._log("info", "Agent execution completed", duration=duration)

            # ENHANCED: lifecycle hook
            await self.on_complete(result)

            return result

        except asyncio.TimeoutError:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.error(f"Execution timed out after {timeout}s")
            self._log("warning", "Agent execution timed out", timeout=timeout, duration=duration)

            result = format_result(
                agent_type=self.agent_type,
                target=target,
                data={
                    "error": f"Agent timed out after {timeout} seconds",
                    "duration": duration,
                    "execution_id": self.current_execution_id
                },
                status="timeout"
            )
            self.status = "timeout"
            return result

        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.error(f"Execution failed: {str(e)}")
            self._log("error", "Agent execution failed", error=str(e), duration=duration)

            # ENHANCED: lifecycle hook
            await self.on_error(e)

            # Format error result
            result = format_result(
                agent_type=self.agent_type,
                target=target,
                data={
                    "error": str(e),
                    "duration": duration,
                    "execution_id": self.current_execution_id
                },
                status="failed"
            )

            self.status = "failed"
            return result

    # ── Structured Logging ───────────────────────────────────────────────────

    def _log(self, level: str, message: str, **kwargs) -> None:
        """
        ENHANCED: Structured JSON-compatible logging.
        Includes agent_type, execution_id, timestamp, and any extra kwargs.
        """
        entry = {
            "agent_type": self.agent_type,
            "execution_id": self.current_execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            **kwargs
        }
        log_fn = getattr(self.logger.logger, level, self.logger.logger.info)
        log_fn(json.dumps(entry, default=str))

    # ── Retry with Exponential Backoff ───────────────────────────────────────

    async def _retry_with_backoff(
        self,
        func,
        *args,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        retryable_exceptions: tuple = (Exception,),
        **kwargs,
    ):
        """
        ENHANCED: Retry an async callable with exponential backoff + jitter.
        Useful for transient failures (API throttling, network errors).
        """
        last_exc = None
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exc = e
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.5)
                    wait = delay + jitter
                    self._log(
                        "warning",
                        f"Retry {attempt + 1}/{max_retries} after {wait:.1f}s",
                        error=str(e),
                    )
                    await asyncio.sleep(wait)
        raise last_exc

    # ── Scope Enforcement ────────────────────────────────────────────────────

    def scope_validator(self, url: str, allowed_scope: Optional[List[str]] = None) -> bool:
        """
        ENHANCED: Check whether a target URL is within the allowed scope.
        *allowed_scope* is a list of domain patterns (e.g. ["example.com", "*.test.io"]).
        If allowed_scope is None or empty, all targets are allowed (backward compat).
        """
        if not allowed_scope:
            return True

        from urllib.parse import urlparse
        try:
            parsed = urlparse(url if "://" in url else f"https://{url}")
            hostname = (parsed.hostname or "").lower()
        except Exception:
            return False

        for pattern in allowed_scope:
            pattern = pattern.lower().strip()
            if pattern.startswith("*."):
                # Wildcard: *.example.com matches sub.example.com
                suffix = pattern[2:]
                if hostname == suffix or hostname.endswith("." + suffix):
                    return True
            else:
                if hostname == pattern:
                    return True
        return False

    # ── Status ───────────────────────────────────────────────────────────────

    def get_status(self) -> Dict:
        """
        Get current agent status.
        ENHANCED: redacts sensitive config values.
        """
        safe_config = {}
        for k, v in self.config.items():
            if _SENSITIVE_KEY_PATTERN.search(k):
                safe_config[k] = "***REDACTED***"
            else:
                safe_config[k] = v

        return {
            "agent_type": self.agent_type,
            "status": self.status,
            "execution_id": self.current_execution_id,
            "config": safe_config,
            "version": __version__,
        }

    async def validate_target(self, target: str) -> bool:
        """Validate target before execution"""
        from src.utils.helpers import validate_target
        return validate_target(target)

    def update_config(self, config: Dict):
        """Update agent configuration"""
        self.config.update(config)
        self.logger.logger.info(f"Configuration updated: {list(config.keys())}")
