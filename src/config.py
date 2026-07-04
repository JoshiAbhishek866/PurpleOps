import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Bedrock
    BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    KNOWLEDGE_BASE_ID = os.getenv("KNOWLEDGE_BASE_ID")

    # DynamoDB Tables
    DYNAMODB_TABLE_CAMPAIGNS = os.getenv("DYNAMODB_TABLE_CAMPAIGNS", "CampaignSessions")
    DYNAMODB_TABLE_AUDIT     = os.getenv("DYNAMODB_TABLE_AUDIT", "AuditLogs")

    # S3
    S3_BUCKET_REPORTS = os.getenv("S3_BUCKET_REPORTS", "purpleops-artifacts")

    # IAM Roles
    RED_AGENT_ROLE_ARN   = os.getenv("RED_AGENT_ROLE_ARN", "")
    BLUE_AGENT_ROLE_ARN  = os.getenv("BLUE_AGENT_ROLE_ARN", "")
    COORD_AGENT_ROLE_ARN = os.getenv("COORD_AGENT_ROLE_ARN", "")

    # Bedrock Model Settings
    BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.7"))
    BEDROCK_MAX_TOKENS  = int(os.getenv("BEDROCK_MAX_TOKENS", "4096"))
    BEDROCK_TOP_P       = float(os.getenv("BEDROCK_TOP_P", "0.9"))

    # Coordinator / Campaign Defaults
    DEFAULT_MAX_ATTACK_TURNS = int(os.getenv("DEFAULT_MAX_ATTACK_TURNS", "5"))
    DEFAULT_MAX_DEFENSE_TURNS = int(os.getenv("DEFAULT_MAX_DEFENSE_TURNS", "5"))
    DEFAULT_MAX_TOTAL_TURNS  = int(os.getenv("DEFAULT_MAX_TOTAL_TURNS", "15"))
    DEFAULT_TOKEN_BUDGET     = int(os.getenv("DEFAULT_TOKEN_BUDGET", "50000"))

    # Agent Mode: "default" (AgentExecutor) or "langgraph"
    AGENT_MODE = os.getenv("AGENT_MODE", "default")

    # n8n Workflow Automation
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")
    N8N_API_KEY     = os.getenv("N8N_API_KEY", "")

    # Registry
    AGENT_REGISTRY_TABLE = os.getenv("AGENT_REGISTRY_TABLE", "SentinelAgentRegistry")
