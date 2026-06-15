"""
Logging utility for Sentinel AI v2.0
Provides colored console output and structured file logging.

ENHANCED v2.0:
- Graceful fallback when colorlog is not installed
- JSON file logging option for production
- Log rotation support
- Configurable log level from environment
- Campaign-scoped logging
"""

import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# ENHANCED: graceful fallback if colorlog is not installed
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logger(name: str, log_level: str = None) -> logging.Logger:
    """
    Set up a logger with colored console output and file logging.

    ENHANCED v2.0:
    - Reads LOG_LEVEL from environment if not provided
    - Uses RotatingFileHandler (10MB max, 5 backups)
    - Graceful fallback when colorlog is not installed

    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Falls back to LOG_LEVEL env var, then INFO.

    Returns:
        Configured logger instance
    """
    # ENHANCED: read from environment if not provided
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # ── Console handler ──────────────────────────────────────────────────
    if HAS_COLORLOG:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s%(reset)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_format)
    else:
        # ENHANCED: fallback to plain formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)

    logger.addHandler(console_handler)

    # ── File handler with rotation ───────────────────────────────────────
    log_dir = Path("logs")
    try:
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"sentinel_{datetime.now().strftime('%Y%m%d')}.log"

        # ENHANCED: RotatingFileHandler (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # ENHANCED: don't crash if log directory is not writable
        logger.warning(f"File logging disabled: {e}")

    return logger


class AgentLogger:
    """
    Specialized logger for agent operations.

    ENHANCED v2.0:
    - Structured JSON audit entries
    - Campaign-scoped log context
    - Metric-style timing logs
    """

    def __init__(self, agent_name: str):
        self.logger = setup_logger(f"agent.{agent_name}")
        self.agent_name = agent_name
        self._campaign_id: str = ""

    def set_campaign(self, campaign_id: str) -> None:
        """ENHANCED: Set campaign context for all subsequent log entries."""
        self._campaign_id = campaign_id

    def _prefix(self) -> str:
        if self._campaign_id:
            return f"[{self._campaign_id[:8]}] "
        return ""

    def start(self, target: str):
        """Log agent start"""
        self.logger.info(f"{self._prefix()}🚀 Starting {self.agent_name} for target: {target}")

    def progress(self, message: str):
        """Log progress"""
        self.logger.info(f"{self._prefix()}⏳ {message}")

    def success(self, message: str):
        """Log success"""
        self.logger.info(f"{self._prefix()}✅ {message}")

    def warning(self, message: str):
        """Log warning"""
        self.logger.warning(f"{self._prefix()}⚠️  {message}")

    def error(self, message: str):
        """Log error"""
        self.logger.error(f"{self._prefix()}❌ {message}")

    def complete(self, duration: float):
        """Log completion"""
        self.logger.info(f"{self._prefix()}🎉 {self.agent_name} completed in {duration:.2f}s")

    def audit(self, action: str, target: str, outcome: str, **extra) -> None:
        """
        ENHANCED: Structured audit log entry (JSON format).
        Useful for compliance and post-incident review.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": self.agent_name,
            "campaign_id": self._campaign_id,
            "action": action,
            "target": target,
            "outcome": outcome,
            **extra,
        }
        self.logger.info(f"AUDIT: {json.dumps(entry, default=str)}")

    def metric(self, name: str, value: float, unit: str = "") -> None:
        """
        ENHANCED: Metric-style log for monitoring/alerting.
        """
        self.logger.info(
            f"{self._prefix()}📊 METRIC {name}={value}{unit}"
        )
