"""
Sentinel AI v2.0 — Application Configuration
==============================================
Centralized configuration loaded from environment variables.

ENHANCED v2.0:
- Validation of critical settings at import time
- MongoDB configuration for Docker deployment
- Dry-run mode support
- Security Hub / WAF configuration
- RAG / ChromaDB configuration
- Application environment detection
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """
    Central configuration class.
    All values are loaded from environment variables with sensible defaults.
    """

    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
    API_SECRET_KEY = os.getenv("API_SECRET_KEY", "change-me-to-a-random-secret-key")

    # ── AWS ──────────────────────────────────────────────────────────────────
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # ── AWS Bedrock LLM ──────────────────────────────────────────────────────
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")
    BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.2"))
    BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
    BEDROCK_TOP_P = float(os.getenv("BEDROCK_TOP_P", "0.9"))

    # ── DynamoDB Tables ──────────────────────────────────────────────────────
    DYNAMODB_TABLE_CAMPAIGNS = os.getenv("DYNAMODB_TABLE_CAMPAIGNS", "sentinel-campaigns")
    DYNAMODB_TABLE_AUDIT = os.getenv("DYNAMODB_TABLE_AUDIT", "sentinel-audit")

    # ── S3 ───────────────────────────────────────────────────────────────────
    S3_BUCKET_REPORTS = os.getenv("S3_BUCKET_REPORTS", "sentinel-ai-artifacts")

    # ── IAM Roles ────────────────────────────────────────────────────────────
    RED_AGENT_ROLE_ARN = os.getenv("RED_AGENT_ROLE_ARN", "")
    BLUE_AGENT_ROLE_ARN = os.getenv("BLUE_AGENT_ROLE_ARN", "")
    COORD_AGENT_ROLE_ARN = os.getenv("COORD_AGENT_ROLE_ARN", "")

    # ── Coordinator / Campaign Defaults ──────────────────────────────────────
    DEFAULT_MAX_ATTACK_TURNS = int(os.getenv("MAX_ATTACK_TURNS", os.getenv("DEFAULT_MAX_ATTACK_TURNS", "5")))
    DEFAULT_MAX_DEFENSE_TURNS = int(os.getenv("MAX_DEFENSE_TURNS", os.getenv("DEFAULT_MAX_DEFENSE_TURNS", "5")))
    DEFAULT_MAX_TOTAL_TURNS = int(os.getenv("MAX_TOTAL_TURNS", os.getenv("DEFAULT_MAX_TOTAL_TURNS", "15")))
    DEFAULT_TOKEN_BUDGET = int(os.getenv("TOKEN_BUDGET", os.getenv("DEFAULT_TOKEN_BUDGET", "50000")))

    # ── Agent Mode ───────────────────────────────────────────────────────────
    AGENT_MODE = os.getenv("AGENT_MODE", "default")

    # ── n8n Workflow Automation ──────────────────────────────────────────────
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")

    # ── Registry ─────────────────────────────────────────────────────────────
    AGENT_REGISTRY_TABLE = os.getenv("AGENT_REGISTRY_TABLE", "SentinelAgentRegistry")

    # ── MongoDB (ENHANCED v2.0) ──────────────────────────────────────────────
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "sentinel_ai")

    # ── WAF Configuration (ENHANCED v2.0) ────────────────────────────────────
    WAF_ACL_NAME = os.getenv("WAF_ACL_NAME", "")
    WAF_ACL_ID = os.getenv("WAF_ACL_ID", "")
    WAF_SCOPE = os.getenv("WAF_SCOPE", "REGIONAL")

    # ── Security Hub (ENHANCED v2.0) ─────────────────────────────────────────
    SECURITY_HUB_PRODUCT_ARN = os.getenv("SECURITY_HUB_PRODUCT_ARN", "")

    # ── RAG / Vector Store (ENHANCED v2.0) ───────────────────────────────────
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() in ("true", "1", "yes")

    # ── Validation ───────────────────────────────────────────────────────────

    @classmethod
    def validate(cls) -> bool:
        """
        ENHANCED v2.0: Validate critical configuration at startup.
        Returns True if valid, logs warnings for missing optional config.
        """
        warnings = []
        errors = []

        # Critical: AWS region must be set
        if not cls.AWS_REGION:
            errors.append("AWS_REGION is not set")

        # Critical: Bedrock model must be set
        if not cls.BEDROCK_MODEL_ID:
            errors.append("BEDROCK_MODEL_ID is not set")

        # Warning: API secret key should be changed from default
        if cls.API_SECRET_KEY == "change-me-to-a-random-secret-key":
            warnings.append("API_SECRET_KEY is still the default — change it for production")

        # Warning: DynamoDB tables
        if not cls.DYNAMODB_TABLE_CAMPAIGNS:
            warnings.append("DYNAMODB_TABLE_CAMPAIGNS is not set")

        # Warning: n8n webhook
        if not cls.N8N_WEBHOOK_URL:
            warnings.append("N8N_WEBHOOK_URL is not configured — workflow triggers disabled")

        # Log results
        for w in warnings:
            logger.warning("[CONFIG] ⚠️  %s", w)
        for e in errors:
            logger.error("[CONFIG] ❌ %s", e)

        if errors:
            logger.error("[CONFIG] Configuration validation FAILED with %d error(s)", len(errors))
            return False

        logger.info("[CONFIG] ✅ Configuration validated (%d warning(s))", len(warnings))
        return True

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.APP_ENV.lower() in ("production", "prod")

    @classmethod
    def is_dry_run(cls) -> bool:
        """Check if dry-run mode is enabled."""
        return cls.DRY_RUN

    @classmethod
    def summary(cls) -> dict:
        """
        ENHANCED v2.0: Return a summary of configuration (with secrets redacted).
        """
        return {
            "app_env": cls.APP_ENV,
            "aws_region": cls.AWS_REGION,
            "bedrock_model": cls.BEDROCK_MODEL_ID,
            "agent_mode": cls.AGENT_MODE,
            "dry_run": cls.DRY_RUN,
            "debug": cls.DEBUG,
            "mongo_url": cls.MONGO_URL.split("@")[-1] if "@" in cls.MONGO_URL else cls.MONGO_URL,
            "mongo_db": cls.MONGO_DB,
            "rag_enabled": cls.RAG_ENABLED,
            "n8n_configured": bool(cls.N8N_WEBHOOK_URL),
            "waf_configured": bool(cls.WAF_ACL_NAME and cls.WAF_ACL_ID),
            "max_attack_turns": cls.DEFAULT_MAX_ATTACK_TURNS,
            "max_defense_turns": cls.DEFAULT_MAX_DEFENSE_TURNS,
            "token_budget": cls.DEFAULT_TOKEN_BUDGET,
        }
