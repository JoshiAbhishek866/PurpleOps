"""
Sandbox Manager Agent — ENHANCED v2.0
Docker-based isolated environment management

Changes from v1.0:
  - Replaced datetime.utcnow() with datetime.now(timezone.utc)
  - Replaced hashlib.md5 with uuid.uuid4 for sandbox ID generation
  - Added structured JSON-compatible logging throughout
  - Added try/except guards with specific exception types
  - Added input validation on execute() and public methods
  - Added exponential backoff retry on Docker operations
  - Added sandbox health-check method
  - Added ENHANCED v2.0 markers on all new additions
  - Preserved ALL existing functionality and APIs
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent

# ENHANCED: structured logger
_logger = logging.getLogger(__name__)

# ENHANCED: default retry configuration
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_BASE_DELAY: float = 0.5  # seconds


class SandboxManagerAgent(BaseAgent):
    """
    Sandbox Manager Agent — ENHANCED v2.0

    Capabilities:
    - Docker container management
    - Isolated environment creation
    - Resource allocation
    - Network isolation
    - Automatic cleanup
    - Security controls
    - Multi-sandbox orchestration

    ENHANCED v2.0 additions:
    - Timezone-aware timestamps (UTC)
    - UUID4-based sandbox identifiers (replaces MD5)
    - Exponential backoff retry for Docker operations
    - Input validation on all public methods
    - Structured JSON logging
    - Sandbox health-check support
    - Configurable retry parameters
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("sandbox_manager", config)
        self.default_config = {
            "timeout": 300,
            "max_sandboxes": 10,
            "default_memory_limit": "512m",
            "default_cpu_limit": 1.0,
            "network_isolation": True,
            "auto_cleanup": True,
            "cleanup_timeout": 3600,  # 1 hour
            "use_docker": True,
            # ENHANCED: retry configuration (opt-in via config)
            "max_retries": _DEFAULT_MAX_RETRIES,
            "retry_base_delay": _DEFAULT_RETRY_BASE_DELAY,
        }
        self.config = {**self.default_config, **(config or {})}

        # Track active sandboxes
        self.active_sandboxes: Dict[str, Dict] = {}

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """Execute sandbox management operation"""

        # ENHANCED: input validation
        if not target or not isinstance(target, str):
            _logger.warning(json.dumps({
                "event": "sandbox_invalid_target",
                "target": str(target),
            }))
            return {"error": "target must be a non-empty string"}

        operation = options.get("operation", "create") if options else "create"

        self.logger.progress(f"Sandbox operation: {operation}")

        # ENHANCED: structured log
        _logger.info(json.dumps({
            "event": "sandbox_operation_start",
            "operation": operation,
            "target": target,
        }))

        if operation == "create":
            return await self.create_sandbox(target, options)
        elif operation == "destroy":
            sandbox_id = options.get("sandbox_id") if options else None
            return await self.destroy_sandbox(sandbox_id)
        elif operation == "list":
            return await self.list_sandboxes()
        elif operation == "cleanup":
            return await self.cleanup_old_sandboxes()
        # ENHANCED: health-check operation
        elif operation == "health_check":
            sandbox_id = options.get("sandbox_id") if options else None
            return await self.health_check(sandbox_id)
        else:
            _logger.warning(json.dumps({
                "event": "sandbox_unknown_operation",
                "operation": operation,
            }))
            return {"error": f"Unknown operation: {operation}"}

    async def create_sandbox(self, target: str, options: Optional[Dict] = None) -> Dict:
        """Create isolated sandbox environment"""

        self.logger.progress(f"Creating sandbox for {target}...")

        # Check sandbox limit
        if len(self.active_sandboxes) >= self.config["max_sandboxes"]:
            _logger.warning(json.dumps({
                "event": "sandbox_limit_reached",
                "active": len(self.active_sandboxes),
                "max": self.config["max_sandboxes"],
            }))
            return {
                "error": "Maximum sandbox limit reached",
                "max_sandboxes": self.config["max_sandboxes"]
            }

        # Generate sandbox ID
        sandbox_id = self._generate_sandbox_id(target)

        # Configure sandbox
        sandbox_config: Dict[str, Any] = {
            "sandbox_id": sandbox_id,
            "target": target,
            # ENHANCED: timezone-aware UTC timestamp
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "creating",
            "resources": {
                "memory_limit": options.get("memory_limit", self.config["default_memory_limit"]) if options else self.config["default_memory_limit"],
                "cpu_limit": options.get("cpu_limit", self.config["default_cpu_limit"]) if options else self.config["default_cpu_limit"]
            },
            "network": {
                "isolated": self.config["network_isolation"],
                "internal_ip": None,
                "exposed_ports": []
            },
            "security": {
                "read_only_root": True,
                "no_new_privileges": True,
                "drop_capabilities": ["ALL"]
            }
        }

        # ENHANCED: create Docker container with retry
        try:
            container_info = await self._create_docker_container_with_retry(sandbox_config)
        except RuntimeError as exc:
            _logger.error(json.dumps({
                "event": "sandbox_create_failed",
                "sandbox_id": sandbox_id,
                "error": str(exc),
            }))
            return {"error": f"Container creation failed after retries: {exc}"}

        sandbox_config["container_id"] = container_info["container_id"]
        sandbox_config["status"] = "running"
        sandbox_config["network"]["internal_ip"] = container_info["ip_address"]

        # Store sandbox info
        self.active_sandboxes[sandbox_id] = sandbox_config

        self.logger.success(f"Sandbox created: {sandbox_id}")

        # ENHANCED: structured log
        _logger.info(json.dumps({
            "event": "sandbox_created",
            "sandbox_id": sandbox_id,
            "target": target,
            "container_id": container_info["container_id"],
        }))

        return {
            "sandbox_id": sandbox_id,
            "status": "running",
            "container_id": container_info["container_id"],
            "ip_address": container_info["ip_address"],
            "resources": sandbox_config["resources"],
            "created_at": sandbox_config["created_at"]
        }

    async def destroy_sandbox(self, sandbox_id: str) -> Dict:
        """Destroy sandbox environment"""

        if not sandbox_id:
            return {"error": "Sandbox ID required"}

        if sandbox_id not in self.active_sandboxes:
            return {"error": f"Sandbox not found: {sandbox_id}"}

        self.logger.progress(f"Destroying sandbox: {sandbox_id}")

        sandbox = self.active_sandboxes[sandbox_id]

        # ENHANCED: guard container destruction
        try:
            await self._destroy_docker_container(sandbox["container_id"])
        except (OSError, RuntimeError) as exc:
            _logger.error(json.dumps({
                "event": "sandbox_destroy_container_failed",
                "sandbox_id": sandbox_id,
                "error": str(exc),
            }))
            # Continue to remove from tracking even if Docker removal fails

        # Remove from active sandboxes
        del self.active_sandboxes[sandbox_id]

        self.logger.success(f"Sandbox destroyed: {sandbox_id}")

        # ENHANCED: structured log
        _logger.info(json.dumps({
            "event": "sandbox_destroyed",
            "sandbox_id": sandbox_id,
        }))

        return {
            "sandbox_id": sandbox_id,
            "status": "destroyed",
            # ENHANCED: timezone-aware UTC timestamp
            "destroyed_at": datetime.now(timezone.utc).isoformat()
        }

    async def list_sandboxes(self) -> Dict:
        """List all active sandboxes"""

        sandboxes: List[Dict] = []

        for sandbox_id, sandbox in self.active_sandboxes.items():
            sandboxes.append({
                "sandbox_id": sandbox_id,
                "target": sandbox["target"],
                "status": sandbox["status"],
                "created_at": sandbox["created_at"],
                "container_id": sandbox.get("container_id"),
                "ip_address": sandbox.get("network", {}).get("internal_ip")
            })

        return {
            "total_sandboxes": len(sandboxes),
            "sandboxes": sandboxes
        }

    async def cleanup_old_sandboxes(self) -> Dict:
        """Cleanup old/stale sandboxes"""

        self.logger.progress("Cleaning up old sandboxes...")

        cleaned: List[str] = []
        # ENHANCED: timezone-aware UTC timestamp
        current_time = datetime.now(timezone.utc)

        for sandbox_id, sandbox in list(self.active_sandboxes.items()):
            try:
                created_at = datetime.fromisoformat(sandbox["created_at"])
                # ENHANCED: ensure created_at is tz-aware for safe comparison
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                age_seconds = (current_time - created_at).total_seconds()

                if age_seconds > self.config["cleanup_timeout"]:
                    await self.destroy_sandbox(sandbox_id)
                    cleaned.append(sandbox_id)
            except (ValueError, KeyError, TypeError) as exc:
                _logger.warning(json.dumps({
                    "event": "sandbox_cleanup_skip",
                    "sandbox_id": sandbox_id,
                    "error": str(exc),
                }))

        self.logger.success(f"Cleaned up {len(cleaned)} sandboxes")

        return {
            "cleaned_count": len(cleaned),
            "cleaned_sandboxes": cleaned
        }

    # ENHANCED: sandbox health-check ──────────────────────────────────────────

    async def health_check(self, sandbox_id: Optional[str] = None) -> Dict:
        """ENHANCED: check health status of one or all sandboxes.

        Args:
            sandbox_id: specific sandbox to check; None = check all.

        Returns:
            Dict with health results per sandbox.
        """
        targets = (
            {sandbox_id: self.active_sandboxes[sandbox_id]}
            if sandbox_id and sandbox_id in self.active_sandboxes
            else dict(self.active_sandboxes)
        )

        results: Dict[str, str] = {}
        for sid, sandbox in targets.items():
            try:
                # In production, would exec a health-check command inside the container
                await asyncio.sleep(0.05)
                results[sid] = "healthy" if sandbox.get("status") == "running" else "unhealthy"
            except (OSError, RuntimeError):
                results[sid] = "unreachable"

        _logger.info(json.dumps({
            "event": "sandbox_health_check",
            "checked": len(results),
            "results": results,
        }))

        return {
            "checked": len(results),
            "results": results,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── ID generation ────────────────────────────────────────────────────────

    def _generate_sandbox_id(self, target: str) -> str:
        """Generate unique sandbox ID.

        ENHANCED v2.0: uses uuid4 instead of MD5 for non-predictable IDs.
        """
        # ENHANCED: uuid4 replaces MD5
        return f"sandbox-{uuid.uuid4().hex[:8]}"

    # ── Docker operations ────────────────────────────────────────────────────

    async def _create_docker_container_with_retry(self, config: Dict) -> Dict:
        """ENHANCED: create Docker container with exponential backoff retry."""
        max_retries = int(self.config.get("max_retries", _DEFAULT_MAX_RETRIES))
        base_delay = float(self.config.get("retry_base_delay", _DEFAULT_RETRY_BASE_DELAY))
        last_exc: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                return await self._create_docker_container(config)
            except (OSError, RuntimeError) as exc:
                last_exc = exc
                delay = base_delay * (2 ** (attempt - 1))
                _logger.warning(json.dumps({
                    "event": "docker_create_retry",
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "delay_s": delay,
                    "error": str(exc),
                }))
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"Docker container creation failed after {max_retries} attempts: {last_exc}"
        )

    async def _create_docker_container(self, config: Dict) -> Dict:
        """Create Docker container (simulated)"""

        # In production, this would use Docker SDK
        # docker.from_env().containers.run(...)

        self.logger.progress("Creating Docker container...")

        # Simulate container creation
        await asyncio.sleep(0.5)

        container_id = f"container-{config['sandbox_id']}"
        ip_address = f"172.17.0.{len(self.active_sandboxes) + 2}"

        return {
            "container_id": container_id,
            "ip_address": ip_address,
            "status": "running"
        }

    async def _destroy_docker_container(self, container_id: str) -> None:
        """Destroy Docker container (simulated)"""

        # In production, this would use Docker SDK
        # container.stop()
        # container.remove()

        self.logger.progress(f"Destroying container: {container_id}")

        # Simulate container destruction
        await asyncio.sleep(0.3)

    async def execute_in_sandbox(
        self,
        sandbox_id: str,
        command: str
    ) -> Dict:
        """Execute command in sandbox"""

        # ENHANCED: input validation
        if not sandbox_id or not isinstance(sandbox_id, str):
            return {"error": "sandbox_id must be a non-empty string"}
        if not command or not isinstance(command, str):
            return {"error": "command must be a non-empty string"}

        if sandbox_id not in self.active_sandboxes:
            return {"error": f"Sandbox not found: {sandbox_id}"}

        self.logger.progress(f"Executing in sandbox {sandbox_id}: {command}")

        # In production, this would use Docker SDK
        # container.exec_run(command)

        # Simulate command execution
        await asyncio.sleep(0.2)

        # ENHANCED: structured log
        _logger.info(json.dumps({
            "event": "sandbox_command_executed",
            "sandbox_id": sandbox_id,
            "command": command[:120],
        }))

        return {
            "sandbox_id": sandbox_id,
            "command": command,
            "exit_code": 0,
            "output": "Command executed successfully (simulated)"
        }

    async def get_sandbox_logs(self, sandbox_id: str) -> Dict:
        """Get sandbox logs"""

        if sandbox_id not in self.active_sandboxes:
            return {"error": f"Sandbox not found: {sandbox_id}"}

        # In production, this would fetch actual container logs

        return {
            "sandbox_id": sandbox_id,
            "logs": [
                "Sandbox initialized",
                "Security controls applied",
                "Network isolation enabled",
                "Ready for operations"
            ]
        }

    async def get_sandbox_stats(self, sandbox_id: str) -> Dict:
        """Get sandbox resource usage stats"""

        if sandbox_id not in self.active_sandboxes:
            return {"error": f"Sandbox not found: {sandbox_id}"}

        # In production, this would fetch actual container stats

        return {
            "sandbox_id": sandbox_id,
            "cpu_usage": "15%",
            "memory_usage": "128MB / 512MB",
            "network_io": {
                "rx_bytes": 1024,
                "tx_bytes": 2048
            },
            "disk_io": {
                "read_bytes": 4096,
                "write_bytes": 8192
            }
        }
