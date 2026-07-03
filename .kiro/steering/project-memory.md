---
inclusion: always
---

# Sentinel AI - Project Memory
> Last Updated: June 8, 2026
> Always include this file in context for all interactions.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | Sentinel AI |
| **Tagline** | "Attack to Defend. Autonomously." |
| **Version** | 2.0.0 |
| **Type** | Startup (not a hackathon project) |
| **Owner** | Abhishek Joshi (JoshiAbhishek866) |
| **GitHub** | https://github.com/JoshiAbhishek866/PurpleOps |
| **Active Branch** | Test |
| **Workspace Root** | D:\Sentinal-AI-main |

---

## 2. What This Project Is

Sentinel AI is an **autonomous purple teaming platform** that deploys dual-model AI agents to validate vulnerabilities through active exploitation and auto-remediation.

- **Red Agent** — Offensive AI (SQL injection, XSS, privilege escalation)
- **Blue Agent** — Defensive AI (WAF updates, security group modification, compliance reports)
- **Coordinator Agent** — Central Supervisor (LangGraph pattern, prevents infinite loops, enforces token budgets)
- **Agent Registry** — AWS Bedrock AgentCore integration ("ECR for AI Agents")

---

## 3. Architecture (Current State)

### Hierarchical Supervisor Pattern (v2.0)
```
CoordinatorAgent (Supervisor)
├── Owns CampaignState (single source of truth)
├── Enforces token budgets & turn limits
├── Routes: Red Agent → Blue Agent
├── Prevents infinite Red↔Blue loops
└── Registers to AWS Bedrock AgentCore Registry

RedAgent (Offensive)          BlueAgent (Defensive)
├── SQL Injection              ├── WAF Rule Updates
├── XSS Testing                ├── Security Group Modification
└── Privilege Escalation       ├── RAG Knowledge Query
                               └── Compliance Report Generation

AgentRegistry (AWS Bedrock AgentCore)
├── Version-controlled agent storage
├── Cross-account agent discovery
└── Cost tracking per agent version
```

### Tech Stack
| Layer | Technology |
|---|---|
| Backend API | Python 3.11, FastAPI |
| AI Engine | Amazon Bedrock (Claude 3.5 Sonnet) |
| Agent Framework | LangChain + LangGraph (optional) |
| Workflow Automation | n8n |
| Database | DynamoDB (primary) |
| Storage | S3 |
| Compute | AWS App Runner (Docker) |
| Frontend | Vue.js 3, Three.js, GSAP |
| Registry | AWS Bedrock AgentCore + DynamoDB |

---

## 4. Folder Structure

```
D:\Sentinal-AI-main\
├── .kiro/
│   ├── specs/
│   │   └── sentinel-ai/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   └── steering/
│       ├── project-memory.md      # THIS FILE
│       ├── aws-aidlc-rules/
│       │   └── core-workflow.md
│       └── aws-aidlc-rule-details/
│           ├── common/            # 4 shared rule files
│           ├── inception/         # 5 inception stage files
│           ├── construction/      # 5 construction stage files
│           └── operations/        # 1 operations file
├── src/
│   ├── main.py                    # FastAPI entry point (v2.0)
│   ├── config.py                  # Centralized config
│   ├── agents/
│   │   ├── coordinator_agent.py   # NEW: Central Supervisor Agent
│   │   ├── red_agent.py           # Offensive LangChain agent
│   │   ├── blue_agent.py          # Defensive LangChain agent
│   │   ├── base_agent.py          # Abstract base class
│   │   ├── offensive/             # Specialized offensive agents
│   │   │   ├── recon_agent.py
│   │   │   ├── scanner_agent.py
│   │   │   ├── vuln_agent.py
│   │   │   ├── credential_testing_agent.py
│   │   │   └── report_generator_agent.py
│   │   ├── defensive/             # Specialized defensive agents
│   │   │   ├── threat_detection_agent.py
│   │   │   ├── hardening_agent.py
│   │   │   ├── vuln_prioritization_agent.py
│   │   │   ├── incident_response_agent.py
│   │   │   └── compliance_check_agent.py
│   │   └── core/                  # Infrastructure agents
│   │       ├── sandbox_manager_agent.py
│   │       └── dashboard_reporter_agent.py
│   ├── core/
│   │   ├── orchestrator.py        # Multi-agent orchestrator (13 agents)
│   │   ├── agent_registry.py      # NEW: AWS Bedrock AgentCore Registry
│   │   ├── langgraph_agents.py    # LangGraph state machine (opt-in)
│   │   ├── llm_client.py
│   │   ├── llm_provider.py
│   │   ├── rag_client.py
│   │   ├── n8n_client.py
│   │   ├── database.py
│   │   ├── memory.py
│   │   ├── structured_memory.py
│   │   ├── knowledge_store.py
│   │   ├── mitre_attack.py
│   │   ├── threat_intel.py
│   │   ├── adversarial_scoring.py
│   │   ├── agent_benchmark.py
│   │   └── hooks.py
│   ├── routes/                    # Admin, client, content API routes
│   │   ├── admin_auth.py
│   │   ├── client_auth.py
│   │   ├── client_dashboard.py
│   │   ├── clients.py
│   │   ├── content.py
│   │   ├── blog.py
│   │   ├── security.py
│   │   ├── architecture.py
│   │   ├── demo_requests.py
│   │   ├── notifications.py
│   │   ├── admin_notifications.py
│   │   ├── password_reset.py
│   │   ├── seo.py
│   │   └── uploads.py
│   ├── models/
│   │   ├── schemas.py
│   │   └── tenant.py
│   └── utils/
│       ├── logger.py
│       ├── helpers.py
│       ├── audit.py
│       ├── auth_middleware.py
│       ├── pii_redactor.py
│       ├── scope_enforcer.py
│       ├── tenant_middleware.py
│       └── seed.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
├── README.md
└── PROJECT_STRUCTURE.md
```

---

## 5. Key Decisions & Rationale

### Decision 1: Hierarchical Coordinator Agent (v2.0)
- **Why**: AWS Summit recommendation + prevents infinite Red↔Blue loops
- **Pattern**: LangGraph Supervisor (industry standard for production multi-agent)
- **File**: `src/agents/coordinator_agent.py`
- **Key feature**: `CampaignState` dataclass owns all state; Coordinator enforces turn limits and token budgets

### Decision 2: AWS Bedrock AgentCore Registry
- **Why**: LinkedIn post about "ECR for AI Agents" — AWS just released this in preview
- **Concept**: "Docker Hub for Cybersecurity Agents" — version, store, discover, pull agents
- **File**: `src/core/agent_registry.py`
- **Fallback**: DynamoDB when AgentCore not available in region

### Decision 3: Enhanced Agent System
- **Why**: Needed specialized agents beyond basic Red/Blue — Recon, Scanner, Vulnerability, Threat Detection, Hardening
- **What was built**: 13 agents (5 offensive, 5 defensive, 3 core), routes, utils, models
- **Specs**: `.kiro/specs/sentinel-ai/`

### Decision 4: Startup Mindset (not hackathon)
- **Focus**: Enterprise-grade infrastructure, scalability, market positioning
- **Target**: "Docker Hub for Cybersecurity Agents" — sell the platform, not just the tool
- **Cost model**: Sub-$40/customer/month

---

## 6. API Endpoints (v2.0)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service info |
| POST | `/campaigns/start` | Start supervised campaign via Coordinator |
| GET | `/campaigns/{id}` | Get campaign details |
| GET | `/registry/agents` | List all registered agents |
| GET | `/registry/agents/{id}` | Pull agent manifest |
| POST | `/registry/agents/{id}/deprecate` | Deprecate agent version |
| GET | `/health` | Health check |

---

## 7. Environment Variables (Key Ones)

```env
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
DYNAMODB_TABLE_CAMPAIGNS=CampaignSessions
DYNAMODB_TABLE_AUDIT=AuditLogs
S3_BUCKET_REPORTS=sentinel-ai-artifacts
RED_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-red-agent-role
BLUE_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-blue-agent-role
COORD_AGENT_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/sentinel-coordinator-role
DEFAULT_MAX_ATTACK_TURNS=5
DEFAULT_MAX_DEFENSE_TURNS=5
DEFAULT_TOKEN_BUDGET=50000
AGENT_MODE=default  # or "langgraph"
N8N_WEBHOOK_URL=http://localhost:5678/webhook
AGENT_REGISTRY_TABLE=SentinelAgentRegistry
```

---

## 8. Git Status

- **Remote**: https://github.com/JoshiAbhishek866/Sentinal-AI.git
- **Active branch**: `main` only — all other branches cleaned up
- **Latest commit**: `27b1686` — Merge PR #5
- **Auth method**: HTTPS with Personal Access Token embedded in URL
- **Branches**: Only `main` exists (local + remote) — full cleanup done
- **PRs merged**: #3 (Test→main), #5 (real attacks upgrade)

---

## 9. Steering Files Active

| File | Purpose |
|---|---|
| `project-memory.md` | Project context, decisions, git status, pending work |
| `karpathy-principles.md` | 4 coding principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution |
| `aws-aidlc-rules/core-workflow.md` | AI-DLC workflow orchestration |
| `aws-aidlc-rule-details/` | Stage-specific rules (inception, construction, operations) |

---

## 10. Pending Work

### High Priority
- [ ] Build free public demo at `demo.sentinelai.io` (deliberately vulnerable sandbox)
- [ ] Wire remaining routes into `src/main.py`
- [ ] Add WebSocket support for real-time campaign updates
- [ ] Build Vue.js frontend with 3D architecture visualization
- [ ] Run `terraform apply` to deploy infrastructure to AWS

### Medium Priority
- [ ] Set up n8n Docker deployment
- [ ] Implement LangGraph Supervisor fully (opt-in via `AGENT_MODE=langgraph`)
- [ ] Add MCP (Model Context Protocol) tool standardization
- [ ] SaaS tier with free 3 campaigns/month
- [ ] Clean up legacy source files from `HavoSec-Main-main/`

### Low Priority
- [ ] CI/CD integration (GitHub PR → auto purple team)
- [ ] AWS Marketplace listing
- [ ] Agent Marketplace (publish/sell custom agents)
- [ ] Multi-tenancy support
- [ ] Mobile app

---

## 11. Cost Model

| Scenario | Monthly Cost |
|---|---|
| MVP (1 customer) | ~$18 |
| Production (5 customers) | ~$140 total / $28 per customer |
| Target | Sub-$40/customer |

---

## 12. Compliance Targets

- SOC 2 Type II aligned
- ISO 27001 aligned
- Auto-generated compliance reports after each campaign

---

## 13. Important Notes for AI Assistant

1. **This is a startup project** — not a hackathon. Think enterprise-grade.
2. **Karpathy principles are active** — always Think Before Coding, keep changes Surgical, stay Simple, define Goals.
3. **Coordinator Agent is the entry point** for all campaigns — never call Red/Blue directly from API.
4. **Red Agent uses real httpx attacks** — SQL injection, XSS, auth bypass, security headers. Not simulated.
5. **Blue Agent uses real boto3 WAF calls** + `verify_remediation` re-runs attacks to confirm fixes.
6. **Coordinator has `_phase_verify`** — re-runs Red attack after Blue fix. Only confirmed blocks = resolved.
7. **Git auth**: Use `https://TOKEN@github.com/JoshiAbhishek866/Sentinal-AI.git` format for pushes.
8. **Agent Registry** uses DynamoDB as fallback when Bedrock AgentCore is not available.
9. **LangGraph** is opt-in via `AGENT_MODE=langgraph` env var — default uses AgentExecutor.
10. **13 total agents**: 5 offensive + 5 defensive + 3 core (all part of Sentinel AI).
11. **Infrastructure**: Full Terraform in `infrastructure/` — ECR, Bedrock KB, WAF, CI/CD, EventBridge.
12. **Only `main` branch exists** — all other branches deleted after cleanup.
