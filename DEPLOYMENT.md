# 🚀 Sentinel AI — Deployment & Execution Guide

## Quick Start (Local — 5 Minutes)

### Prerequisites
- Python 3.11+
- MongoDB running locally (`mongod`)
- Ollama installed ([ollama.com](https://ollama.com))

### Steps

```bash
# 1. Clone and install
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI
pip install -r requirements.txt

# 2. Start MongoDB
mongod --dbpath ./data/db

# 3. Start Ollama + pull a model
ollama serve
ollama pull llama2

# 4. Configure environment
cp .env.example .env
# Edit .env and set these (use random 32+ char strings):
#   JWT_SECRET=<random-string>
#   ADMIN_JWT_SECRET=<random-string>
#   SECRET_KEY=<random-string>

# 5. Run the server
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000

# 6. Open API docs
# http://localhost:8000/docs
```

---

## Docker Deployment

```bash
# Build
docker build -t sentinel-ai .

# Run (requires MongoDB + Ollama available on the network)
docker run -d \
  --name sentinel-ai \
  -p 8000:8000 \
  --env-file .env \
  sentinel-ai
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Sentinel AI API                      │
│                  (FastAPI, port 8000)                    │
├───────────┬───────────┬──────────────┬──────────────────┤
│ Red Agent │ Blue Agent│ Orchestrator │ Knowledge Store   │
│ (Attack)  │ (Defend)  │ (Coordinate) │ (ChromaDB RAG)   │
├───────────┴───────────┴──────────────┴──────────────────┤
│                    Core Services                        │
│  LLM Provider │ Memory │ MITRE ATT&CK │ Threat Intel   │
├─────────────────────────────────────────────────────────┤
│              External Dependencies                      │
│  MongoDB │ Ollama/Bedrock/OpenAI │ AWS (DynamoDB, S3)   │
└─────────────────────────────────────────────────────────┘
```

---

## Required Environment Variables

### Must Set (App Won't Start Without These)
| Variable | Example | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `a1b2c3d4e5...` (32+ chars) | Client JWT signing key |
| `ADMIN_JWT_SECRET` | `f6g7h8i9j0...` (32+ chars) | Admin JWT signing key |
| `SECRET_KEY` | `k1l2m3n4o5...` | App encryption key |

### MongoDB
| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB` | `sentinel_ai` | Database name |

### LLM Provider (Choose One)
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama`, `openai`, `bedrock`, or `azure_openai` |
| `LLM_MODEL` | `llama2` | Model name |
| `LLM_URL` | `http://localhost:11434` | Ollama URL (if using Ollama) |
| `OPENAI_API_KEY` | (empty) | OpenAI key (if using OpenAI) |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-...` | Bedrock model (if using AWS) |

### AWS (Optional — Features Degrade Gracefully Without)
| Variable | Description |
|----------|-------------|
| `AWS_REGION` | AWS region (default: `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `DYNAMODB_TABLE_CAMPAIGNS` | Campaign storage table |
| `DYNAMODB_TABLE_AUDIT` | Audit log table |
| `S3_BUCKET_REPORTS` | S3 bucket for compliance reports |

### Agent Enhancements (Optional)
| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_MODE` | `default` | `default` or `langgraph` (multi-step reasoning) |
| `AGENT_KILL_SWITCH` | `false` | Set `true` to block all offensive operations |
| `CHROMADB_PATH` | `./data/chromadb` | Local knowledge store path |
| `NVD_API_KEY` | (empty) | NVD API key for higher rate limits |

---

## Usage Workflow

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@yourorg.com", "password": "securepassword", "name": "Admin"}'
# Save the returned token
```

### 2. Start a Security Campaign
```bash
curl -X POST http://localhost:8000/campaigns/start \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://your-app.com",
    "target_description": "Main web application",
    "iam_role": "arn:aws:iam::123456:role/ScanRole",
    "actor_id": "security-team"
  }'
# Returns campaign_id
```

### 3. Check Campaign Results
```bash
curl http://localhost:8000/campaigns/<campaign_id> \
  -H "Authorization: Bearer <your-token>"
```

### 4. Run Individual Agents
```bash
# Red Agent (Offensive)
curl -X POST http://localhost:8000/agents/execute/red \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"target": "https://your-app.com"}'

# Blue Agent (Defensive)
curl -X POST http://localhost:8000/agents/execute/blue \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"threat": "SQL Injection found on /api/users"}'
```

---

## AWS Setup (For Full Features)

### DynamoDB Tables
Create these tables in the AWS Console or via CLI:

```bash
# Campaign Sessions
aws dynamodb create-table \
  --table-name CampaignSessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Audit Logs
aws dynamodb create-table \
  --table-name AuditLogs \
  --attribute-definitions AttributeName=audit_id,AttributeType=S \
  --key-schema AttributeName=audit_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Campaign Memory
aws dynamodb create-table \
  --table-name SentinelAI_CampaignMemory \
  --attribute-definitions \
    AttributeName=target,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=target,KeyType=HASH \
    AttributeName=created_at,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

### S3 Bucket
```bash
aws s3 mb s3://sentinel-ai-artifacts
```

### Enable Bedrock
1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to `anthropic.claude-3-5-sonnet`
3. Wait for approval (usually instant)

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx python-jose[cryptography]
python -m pytest tests/ -v
```

---

## Cost Estimates (Monthly)

| Tier | Components | Cost |
|------|-----------|------|
| **Free** | Ollama + local MongoDB + local server | $0 |
| **Light** | MongoDB Atlas free + AWS free tier + Ollama | ~$0-5 |
| **Standard** | MongoDB Atlas M10 + Bedrock + EC2 t3.medium | ~$50-100 |
| **Production** | Managed everything + OpenAI/Claude + monitoring | ~$150-300 |

> **Tip**: Start with the Free tier locally. Only add AWS/cloud when you need real scanning or multi-user access.

---

## Emergency: Kill Switch

If agents are doing something unexpected:

```bash
# Set in .env and restart:
AGENT_KILL_SWITCH=true

# Or set at runtime (requires restart):
export AGENT_KILL_SWITCH=true
```

This **immediately blocks all offensive agent operations**.

---

## ⚠️ Legal Notice

> **Only scan systems you own or have explicit written authorization to test.**
> Unauthorized scanning is illegal under computer fraud laws (CFAA in US, IT Act in India, etc.).
> Always get a signed scope agreement before running Red Agent against any target.
