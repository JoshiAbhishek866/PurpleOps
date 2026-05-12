# Sentinel AI — Autonomous Purple Teaming Platform

> *Attack to Defend. Autonomously.*

Sentinel AI deploys dual AI agents (Red Team + Blue Team) powered by **AWS Bedrock (Claude)** to validate security vulnerabilities through controlled exploitation and auto-remediation.

## How It Works

```
Target URL ──▶ Red Agent (Attack) ──▶ Blue Agent (Defend) ──▶ Report
                  │                        │
                  ├─ SQL Injection          ├─ WAF Rule Updates
                  ├─ XSS Testing           ├─ Security Group Fixes
                  └─ Privilege Escalation   └─ Compliance Report
```

1. **Red Agent** — Offensive AI that runs controlled attacks (SQL injection, XSS, privilege escalation) against your target
2. **Blue Agent** — Defensive AI that detects Red's attacks and auto-remediates (WAF rules, security groups, compliance reports)
3. **Campaign** — A full Red → Blue cycle, logged to DynamoDB with audit trail

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python) |
| AI/LLM | AWS Bedrock (Claude 3.5 Sonnet) via LangChain |
| Database | AWS DynamoDB |
| Reports | AWS S3 |
| Security | AWS WAF, IAM |
| Container | Docker |

## Quick Start

### Prerequisites

- Python 3.11+
- AWS Account with **Bedrock access enabled** (Claude model)
- AWS credentials configured (`aws configure` or env vars)

### Setup

```bash
# Clone
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your AWS credentials

# Run
python main.py
# or
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t sentinel-ai .
docker run -p 8000:8000 --env-file .env sentinel-ai
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/campaigns/start` | Start a purple team campaign |
| `GET` | `/campaigns/{id}` | Get campaign results |

### Start a Campaign

```bash
curl -X POST http://localhost:8000/campaigns/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://your-app.example.com",
    "target_description": "Web application security test",
    "iam_role": "your-iam-role"
  }'
```

## AWS Setup

### Required Resources

| Resource | Purpose |
|----------|---------|
| **Amazon Bedrock** | Claude 3.5 Sonnet for agent reasoning |
| **DynamoDB** | `CampaignSessions` + `AuditLogs` tables |
| **S3** | `sentinel-ai-artifacts` bucket for compliance reports |
| **IAM Roles** | Separate roles for Red and Blue agents |

### Environment Variables

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
KNOWLEDGE_BASE_ID=your_kb_id
DYNAMODB_TABLE_CAMPAIGNS=CampaignSessions
DYNAMODB_TABLE_AUDIT=AuditLogs
S3_BUCKET_REPORTS=sentinel-ai-artifacts
```

## Project Structure

```
src/
├── main.py              # FastAPI app + campaign endpoints
├── config.py            # AWS configuration
└── agents/
    ├── red_agent.py     # Offensive agent (SQL injection, XSS, priv esc)
    └── blue_agent.py    # Defensive agent (WAF, security groups, compliance)
```

## Security

- Red Agent has **read-only** simulated access — never modifies production data
- Blue Agent has **write access** to security controls only (WAF, security groups)
- All actions logged to **immutable DynamoDB audit trail**
- Safety checks reject production targets by default

## License

MIT
