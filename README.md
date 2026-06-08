# Sentinel AI — Autonomous Purple Teaming Platform

> *Attack to Defend. Autonomously.*

Sentinel AI is a startup-grade autonomous security platform that deploys AI agents to find real vulnerabilities, apply real remediations, and **verify the fix worked** — all without human intervention.

Inspired by [XBOW](https://xbow.com/). Built for the J-curve.

---

## How It Works

```
Target URL
    │
    ▼
┌─────────────────────────────────────────────────────┐
│           Coordinator Agent (Supervisor)             │
│  Enforces token budgets · Prevents infinite loops    │
│  Owns CampaignState · Generates audit trail          │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
        ┌──────▼──────┐       ┌───────▼──────┐
        │  Red Agent  │       │  Blue Agent  │
        │  (Offensive)│       │  (Defensive) │
        ├─────────────┤       ├──────────────┤
        │ SQL injection│      │ WAF IP block  │
        │ XSS testing  │      │ Add SQLi rule │
        │ Auth bypass  │      │ Verify fix    │
        │ Header audit │      │ SOC 2 report  │
        └─────────────┘       └──────────────┘
               │                      │
               └──────────┬───────────┘
                           │
                    ┌──────▼──────┐
                    │  Verify     │
                    │  Loop       │
                    │ Re-run attack│
                    │ after fix   │
                    └─────────────┘
```

**The proof loop:** After every Blue remediation, the Coordinator re-runs the Red attack. If the attack returns `HTTP 403` → fix confirmed. If it still works → escalate. Only verified fixes are marked resolved.

---

## What Makes This Real

| Before (simulated) | Now (real) |
|---|---|
| `"simulated_result": "Vulnerability detected"` | Real `httpx` HTTP requests, real SQL error signatures in response body |
| `"WAF rule created to BLOCK SQL Injection attacks"` | Real `boto3 wafv2.update_web_acl()` call |
| No verification | `verify_remediation()` re-runs the attack, checks for HTTP 403 |
| Text file report | JSON uploaded to S3 with `PASSED/REMEDIATION_PENDING` status |

---

## Architecture

```
Coordinator Agent (LangGraph Supervisor pattern)
├── CampaignState — single source of truth
├── Turn limits (max 5 attack, 5 defense, 15 total)
├── Token budget enforcement (~$1.50/campaign default)
└── Immutable audit trail in DynamoDB

Red Agent (httpx-based real attacks)
├── test_sql_injection — SQLi payloads + SQL error detection
├── test_xss — script reflection detection
├── test_auth_bypass — admin path enumeration
└── test_security_headers — missing CSP/HSTS/X-Frame-Options

Blue Agent (boto3-based real remediation)
├── block_ip_in_waf — real WAF IP set creation
├── add_waf_sql_injection_rule — AWS managed SQLi rule group
├── verify_remediation — re-runs attack, confirms HTTP 403
└── generate_compliance_report — SOC 2 JSON → S3

Agent Registry (AWS Bedrock AgentCore)
├── Version-controlled agent storage ("ECR for AI Agents")
├── Cross-account agent discovery and pull
└── Cost tracking per agent version
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11, FastAPI |
| AI Engine | Amazon Bedrock (Claude 3.5 Sonnet) |
| Agent Framework | LangChain + LangGraph (opt-in) |
| HTTP Attacks | httpx |
| AWS Remediations | boto3 (WAF, S3, DynamoDB) |
| Workflow Automation | n8n |
| Database | DynamoDB (on-demand) |
| Storage | S3 (encrypted, versioned) |
| Infrastructure | Terraform (ECR, App Runner, WAF, CI/CD, EventBridge) |
| Registry | AWS Bedrock AgentCore + DynamoDB fallback |

---

## Quick Start

### Prerequisites

- Python 3.11+
- AWS Account with Bedrock access (Claude 3.5 Sonnet model enabled)
- AWS credentials configured

### Local Setup

```bash
git clone https://github.com/JoshiAbhishek866/Sentinal-AI.git
cd Sentinal-AI

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your AWS credentials

uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t sentinel-ai .
docker run -p 8000:8000 --env-file .env sentinel-ai
```

### AWS Deployment (Terraform)

```bash
# 1. Bootstrap remote state (run once)
bash infrastructure/bootstrap.sh

# 2. Init and deploy
cd infrastructure
terraform init
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/campaigns/start` | Start supervised purple team campaign |
| `GET` | `/campaigns/{id}` | Get campaign results |
| `GET` | `/registry/agents` | List all registered agents |
| `GET` | `/registry/agents/{id}` | Pull agent manifest |

### Start a Campaign

```bash
curl -X POST http://localhost:8000/campaigns/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://your-sandbox.example.com",
    "target_description": "Web application security test",
    "max_attack_turns": 3,
    "max_defense_turns": 3,
    "token_budget": 30000
  }'
```

**Response includes:**
- `vulnerabilities_found` — real HTTP evidence per finding
- `remediations_applied` — boto3 call results
- `verified` — whether re-test confirmed the fix
- `final_report.s3_path` — SOC 2 compliance report location

---

## Environment Variables

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
DYNAMODB_TABLE_CAMPAIGNS=CampaignSessions
DYNAMODB_TABLE_AUDIT=AuditLogs
S3_BUCKET_REPORTS=sentinel-ai-artifacts
RED_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-red-agent-role
BLUE_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-blue-agent-role
COORD_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-coordinator-role
AGENT_MODE=default
AGENT_REGISTRY_TABLE=SentinelAgentRegistry
```

See `.env.example` for the full list.

---

## Project Structure

```
Sentinal-AI/
├── src/
│   ├── main.py                     # FastAPI entry point (v2.0)
│   ├── config.py                   # Centralized config
│   ├── agents/
│   │   ├── coordinator_agent.py    # Central Supervisor (LangGraph pattern)
│   │   ├── red_agent.py            # Real HTTP attacks (httpx)
│   │   ├── blue_agent.py           # Real WAF remediation (boto3) + verify
│   │   ├── base_agent.py           # Abstract base class
│   │   ├── offensive/              # Specialized offensive agents
│   │   ├── defensive/              # Specialized defensive agents
│   │   └── core/                   # Infrastructure agents
│   ├── core/
│   │   ├── agent_registry.py       # AWS Bedrock AgentCore registry
│   │   ├── orchestrator.py         # Multi-agent coordinator (13 agents)
│   │   ├── langgraph_agents.py     # LangGraph state machine (opt-in)
│   │   └── ...
│   └── routes/                     # Admin, client, content API routes
├── infrastructure/                 # Terraform IaC
│   ├── main.tf                     # Core: DynamoDB, S3, KMS, IAM, App Runner
│   ├── ecr.tf                      # Docker image registry
│   ├── bedrock.tf                  # Knowledge Base + OpenSearch
│   ├── waf.tf                      # WAF with SQLi + rate limiting
│   ├── cicd.tf                     # CodePipeline: GitHub → ECR → App Runner
│   ├── eventbridge.tf              # Blue Agent WAF anomaly trigger
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars
│   └── bootstrap.sh                # Creates S3 state backend (run once)
├── .kiro/
│   ├── specs/sentinel-ai/          # Requirements, design, tasks
│   ├── steering/
│   │   ├── project-memory.md       # Project context (auto-loaded by Kiro)
│   │   └── karpathy-principles.md  # Coding principles (auto-loaded)
├── .kiroignore                     # Kiro context exclusions
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Security Model

- **Red Agent** — safety checks block production targets; read-only AWS access
- **Blue Agent** — write access to WAF and security controls only
- **Coordinator** — no direct AWS resource access, orchestration only
- **All actions** — logged to immutable DynamoDB audit trail
- **Data encryption** — KMS at rest, TLS in transit

---

## Cost

| Scenario | Monthly |
|---|---|
| MVP (1 customer) | ~$18 |
| Production (5 customers) | ~$28/customer |
| Per campaign | ~$0.15–$1.50 |

---

## Roadmap

- [ ] Free public demo at `demo.sentinelai.io`
- [ ] SaaS tier with free 3 campaigns/month
- [ ] CI/CD integration (GitHub PR → auto purple team)
- [ ] AWS Marketplace listing
- [ ] Agent Marketplace (publish/sell custom agents)

---

## License

MIT
