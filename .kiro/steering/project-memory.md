---
inclusion: always
---

# Sentinel AI - Project Memory
> Last Updated: May 13, 2026
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
| **GitHub** | https://github.com/JoshiAbhishek866/Sentinal-AI |
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
│   │   ├── sentinel-ai/           # Core specs
│   │   │   ├── requirements.md
│   │   │   ├── design.md
│   │   │   └── tasks.md
│   │   └── havosec-integration/   # Integration specs
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
│   │   ├── offensive/             # HavoSec offensive agents
│   │   │   ├── recon_agent.py
│   │   │   ├── scanner_agent.py
│   │   │   ├── vuln_agent.py
│   │   │   ├── credential_testing_agent.py
│   │   │   └── report_generator_agent.py
│   │   ├── defensive/             # HavoSec defensive agents
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
│   ├── routes/                    # HavoSec API routes
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
├── HavoSec-Main-main/             # Source project (analyzed, integrated)
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── .env.example
├── .gitignore
├── Dockerfile
├── requirements.txt
├── README.md
├── PROJECT_STRUCTURE.md
└── HAVOSEC_INTEGRATION_SUMMARY.md
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

### Decision 3: HavoSec Integration
- **Why**: HavoSec had advanced multi-agent system, 3D visualization, n8n workflows
- **What was merged**: 13 agents (5 offensive, 5 defensive, 3 core), routes, utils, models
- **Specs**: `.kiro/specs/havosec-integration/`
- **Source**: `HavoSec-Main-main/` (still present, not deleted)

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
- **Active branch**: Test
- **Last push**: Successfully pushed to Test branch
- **Auth method**: HTTPS with Personal Access Token
- **Note**: Cached credentials were for "AbhishekScale" — use token in URL for pushes

---

## 9. Pending Work

### High Priority
- [ ] Delete addressed files from `HavoSec-Main-main/` (user requested, pending)
- [ ] Wire HavoSec routes into `src/main.py`
- [ ] Add WebSocket support for real-time campaign updates
- [ ] Build Vue.js frontend with 3D architecture visualization

### Medium Priority
- [ ] Create DynamoDB tables via CDK/CLI
- [ ] Set up n8n Docker deployment
- [ ] Implement LangGraph Supervisor fully (currently opt-in via `AGENT_MODE=langgraph`)
- [ ] Add MCP (Model Context Protocol) tool standardization

### Low Priority
- [ ] Multi-tenancy support
- [ ] Custom workflow builder UI
- [ ] Mobile app
- [ ] Multi-cloud support (Azure, GCP)

---

## 10. Cost Model

| Scenario | Monthly Cost |
|---|---|
| MVP (1 customer) | ~$18 |
| Production (5 customers) | ~$140 total / $28 per customer |
| Target | Sub-$40/customer |

---

## 11. Compliance Targets

- SOC 2 Type II aligned
- ISO 27001 aligned
- Auto-generated compliance reports after each campaign

---

## 12. Important Notes for AI Assistant

1. **This is a startup project** — not a hackathon. Think enterprise-grade.
2. **Coordinator Agent is the entry point** for all campaigns — never call Red/Blue directly from API.
3. **HavoSec-Main-main/** is still present — user wants to delete addressed files but hasn't confirmed yet.
4. **Git auth**: Use `https://TOKEN@github.com/JoshiAbhishek866/Sentinal-AI.git` format for pushes.
5. **Agent Registry** uses DynamoDB as fallback when Bedrock AgentCore is not available.
6. **LangGraph** is opt-in via `AGENT_MODE=langgraph` env var — default uses AgentExecutor.
7. **13 total agents**: 5 offensive + 5 defensive + 3 core (from HavoSec integration).
8. **Always check `src/core/orchestrator.py`** for the full 13-agent workflow system.
