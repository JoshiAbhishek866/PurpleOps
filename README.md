# Sentinel AI — Autonomous Purple Teaming Platform

> *Attack to Defend. Autonomously.*

Sentinel AI deploys AI agents to **find real vulnerabilities, apply real remediations, and verify the fix worked** — without human intervention.

---

## How It Works

```
Your Target URL
      │
      ▼
 Coordinator Agent  ──→  Red Agent (attacks)
      │                       │ SQL injection, XSS,
      │                       │ auth bypass, headers
      │                       ▼
      └──────────────→  Blue Agent (defends)
                              │ WAF rules, IP block,
                              │ verify fix, SOC 2 report
```

After every Blue remediation, the Coordinator **re-runs the Red attack** to verify the fix. HTTP 403 = confirmed. Still works = escalate.

---

## Quickest Way to Run It

### 1. Spin up a vulnerable test target

```bash
docker run -d -p 8888:80 vulnerables/web-dvwa
```

### 2. Run Sentinel AI

```bash
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI

# Install
pip install -r requirements.txt

# Configure AWS (minimum needed: region + credentials)
cp .env.example .env
# Edit .env: set AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

# Start the API
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 3. Run your first campaign

```bash
curl -X POST http://localhost:8000/campaigns/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://localhost:8888",
    "target_description": "DVWA local test",
    "max_attack_turns": 2,
    "max_defense_turns": 2,
    "token_budget": 20000
  }'
```

**What comes back:**
```json
{
  "campaign_id": "abc-123",
  "status": "COMPLETED",
  "summary": {
    "findings": {
      "vulnerabilities": 3,
      "remediations": 3,
      "unresolved": 0
    },
    "coordinator_decisions": [
      "Turn 1: Red Agent found 2 new vulnerabilities.",
      "Turn 1: Blue Agent applied 2 remediations.",
      "Turn 1 verification: 2/3 remediations confirmed."
    ]
  }
}
```

---

## Or Run With Docker

```bash
docker build -t sentinel-ai .
docker run -p 8000:8000 --env-file .env sentinel-ai
```

---

## Prerequisites

- Python 3.11+ (or Docker)
- AWS account with **Bedrock access** enabled (Claude 3.5 Sonnet)
- AWS credentials (`AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`)

> **No WAF/DynamoDB/S3 needed for basic testing.** Only required for full remediation + compliance reports.

---

## Environment Variables (Minimum)

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

Full list in `.env.example`.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/campaigns/start` | Run a purple team campaign |
| `GET` | `/campaigns/{id}` | Get campaign results |
| `GET` | `/health` | Health check |
| `GET` | `/registry/agents` | List registered agents |

**Campaign parameters:**

| Parameter | Default | Description |
|---|---|---|
| `target_url` | required | Sandbox/staging URL to test |
| `max_attack_turns` | 5 | Max Red Agent turns |
| `max_defense_turns` | 5 | Max Blue Agent turns |
| `token_budget` | 50000 | Bedrock token limit (~$1.50) |

---

## What Gets Tested

**Red Agent (real HTTP requests via httpx):**
- SQL injection — detects SQL errors in response body
- XSS — checks if payloads reflect unencoded
- Authentication bypass — enumerates `/admin`, `/.env`, `/api/users`
- Security headers — checks for missing CSP, HSTS, X-Frame-Options

**Blue Agent (real AWS SDK calls via boto3):**
- WAF IP block — `wafv2.create_ip_set`
- WAF managed rule — `wafv2.update_web_acl` (SQLi/XSS rule groups)
- Re-verification — re-runs attack, confirms HTTP 403
- SOC 2 report — JSON uploaded to S3

---

## Deploy to AWS (Optional)

For full production deployment with WAF, CI/CD, and compliance reports:

```bash
# One-time setup
bash infrastructure/bootstrap.sh

# Deploy
cd infrastructure
terraform init
terraform apply -var-file="terraform.tfvars"
```

See `infrastructure/README.md` for full steps.

---

## Supported Test Targets

**Only point at sandboxes — never production.**

| Target | Docker command |
|---|---|
| DVWA | `docker run -p 8888:80 vulnerables/web-dvwa` |
| OWASP Juice Shop | `docker run -p 3000:3000 bkimminich/juice-shop` |
| WebGoat | `docker run -p 8080:8080 webgoat/webgoat` |

---

## Architecture

```
src/
├── agents/
│   ├── coordinator_agent.py  # Supervisor — owns state, prevents loops
│   ├── red_agent.py          # HTTP attacks (httpx)
│   └── blue_agent.py         # AWS remediations (boto3) + verify
├── core/
│   ├── agent_registry.py     # Bedrock AgentCore registry
│   └── orchestrator.py       # 13-agent system
└── main.py                   # FastAPI app
infrastructure/               # Terraform IaC (AWS full stack)
```

---

## License

MIT
