# 🚀 Sentinel AI — Quickstart Guide

> **Attack to Defend. Autonomously.**

Get Sentinel AI running in under 5 minutes.

---

## Option 1: Docker (Recommended — Fastest)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- AWS credentials with Bedrock access

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI

# 2. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials:
#   AWS_ACCESS_KEY_ID=AKIA...
#   AWS_SECRET_ACCESS_KEY=...

# 3. Launch everything
docker compose up -d

# 4. Verify
curl http://localhost:8000/health
```

This starts:
| Service | URL | Description |
|---------|-----|-------------|
| **Sentinel AI** | `http://localhost:8000` | Main API |
| **MongoDB** | `localhost:27017` | Database |
| **DVWA** | `http://localhost:8888` | Test target (Damn Vulnerable Web App) |
| **Juice Shop** | `http://localhost:3000` | Test target (OWASP Juice Shop) |

### Run Your First Campaign

```bash
curl -X POST http://localhost:8000/campaigns/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://dvwa:80",
    "target_description": "DVWA local test",
    "max_attack_turns": 3,
    "max_defense_turns": 3
  }'
```

Poll status:
```bash
curl http://localhost:8000/campaigns/<campaign_id>/status
```

---

## Option 2: Local Python

### Prerequisites
- Python 3.11+
- AWS credentials configured (`aws configure` or `.env`)

### Steps

```bash
# 1. Clone
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your AWS credentials

# 5. Run
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Option 3: Production Deployment

```bash
# Use the production compose file (no test targets, resource limits)
docker compose -f docker-compose.prod.yml up -d
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `GET` | `/config` | Configuration summary |
| `POST` | `/campaigns/start` | Start a campaign |
| `GET` | `/campaigns/{id}` | Get campaign details |
| `GET` | `/campaigns/{id}/status` | Poll campaign status |
| `POST` | `/campaigns/{id}/abort` | Abort a running campaign |
| `GET` | `/registry/agents` | List registered agents |

---

## Architecture

```
Coordinator (Supervisor)
├── Red Agent (10 attack categories)
│   ├── SQL Injection (80+ payloads)
│   ├── XSS (60+ payloads)
│   ├── Auth Bypass
│   ├── Security Headers
│   ├── Path Traversal
│   ├── SSRF
│   ├── Command Injection
│   ├── Open Redirect
│   ├── CORS Misconfiguration
│   └── XXE Injection
└── Blue Agent (Defensive)
    ├── WAF Remediation
    ├── Security Hub Integration
    ├── Evidence Chain
    └── Compliance Reporting
```

---

## Environment Variables

See [.env.example](.env.example) for all options. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `AWS_REGION` | ✅ | AWS region (default: us-east-1) |
| `AWS_ACCESS_KEY_ID` | ✅ | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ | AWS secret key |
| `BEDROCK_MODEL_ID` | ✅ | Bedrock model ID |
| `DRY_RUN` | ❌ | Set `true` to skip real attacks |
| `MONGO_URL` | ❌ | MongoDB connection string |

---

## Dry Run Mode

Test without executing real attacks:

```bash
# Via environment variable
DRY_RUN=true docker compose up -d

# Via API request
curl -X POST http://localhost:8000/campaigns/start \
  -d '{"target_url": "http://example.com", "dry_run": true}'
```
