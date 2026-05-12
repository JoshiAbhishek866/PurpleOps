"""
Logging utility for Sentinel AI Orchestrator
Provides colored console output and file logging
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import colorlog


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with colored console output and file logging
    
    Args:
        name: Logger name (usually __name__)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
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
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger


class AgentLogger:
    """Specialized logger for agent operations"""
    
    def __init__(self, agent_name: str):
        self.logger = setup_logger(f"agent.{agent_name}")
        self.agent_name = agent_name
    
    def start(self, target: str):
        """Log agent start"""
        self.logger.info(f"🚀 Starting {self.agent_name} for target: {target}")
    
    def progress(self, message: str):
        """Log progress"""
        self.logger.info(f"⏳ {message}")
    
    def success(self, message: str):
        """Log success"""
        self.logger.info(f"✅ {message}")
    
    def warning(self, message: str):
        """Log warning"""
        self.logger.warning(f"⚠️  {message}")
    
    def error(self, message: str):
        """Log error"""
        self.logger.error(f"❌ {message}")
    
    def complete(self, duration: float):
        """Log completion"""
        self.logger.info(f"🎉 {self.agent_name} completed in {duration:.2f}s")
