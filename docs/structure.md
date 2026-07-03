# PurpleOps - Project Structure
- **Security**: AWS WAF, IAM, KMS, JWT (python-jose), bcrypt
+-- .kiro/                              # AI-DLC steering & rules framework
�   +-- steering/
�   �   +-- aws-aidlc-rules/
�   �       +-- core-workflow.md
�   +-- aws-aidlc-rule-details/
�       +-- common/
�       �   +-- depth-levels.md
�       �   +-- question-format-guide.md
�       �   +-- session-continuity.md
�       �   +-- welcome-message.md
�       +-- inception/
�       �   +-- workspace-detection.md
�       �   +-- requirements-analysis.md
�       �   +-- user-stories.md
�       �   +-- application-design.md
�       �   +-- units-generation.md
�       +-- construction/
�       �   +-- functional-design.md
�       �   +-- nfr-requirements.md
�       �   +-- nfr-design.md
�       �   +-- code-generation.md
�       �   +-- build-and-test.md
�       +-- operations/
�           +-- operations.md
# PurpleOps - Project Structure

## Consolidated Directory Layout

```text
purpleops/
├── src/                                # Source code (FastAPI backend)
│   ├── __init__.py
│   ├── main.py                        # Unified API entry point
│   ├── config.py                      # Configuration management
│   ├── agents/                        # Dual AI & Orchestrator Agents
│   │   ├── __init__.py               
│   │   ├── base_agent.py             # Base orchestrator agent
│   │   ├── red_agent.py              # Offensive AI 
│   │   ├── blue_agent.py             # Defensive AI 
│   │   ├── offensive/                # 5 Offensive Agents
│   │   │   ├── recon_agent.py
│   │   │   ├── scanner_agent.py
│   │   │   ├── vuln_agent.py
│   │   │   ├── credential_testing_agent.py
│   │   │   └── report_generator_agent.py
│   │   ├── defensive/                # 5 Defensive Agents
│   │   │   ├── threat_detection_agent.py
│   │   │   ├── hardening_agent.py
│   │   │   ├── vuln_prioritization_agent.py
│   │   │   ├── incident_response_agent.py
│   │   │   └── compliance_check_agent.py
│   │   └── core/                     # 2 Core Infrastructure Agents
│   │       ├── sandbox_manager_agent.py
│   │       └── dashboard_reporter_agent.py
│   ├── core/                          # Shared Core Systems
│   │   ├── database.py               # DynamoDB database client
│   │   ├── dual_llm_orchestrator.py  # Dual LLM management
│   │   ├── hooks.py                  # Agent lifecycle & feedback loops
│   │   ├── llm_client.py             # Bedrock/Ollama LLM client
│   │   ├── memory.py                 # DynamoDB persistent memory
│   │   ├── n8n_client.py             # Workflow automation client
│   │   ├── orchestrator.py           # 12-agent orchestration engine
│   │   └── rag_client.py             # Vector RAG client
│   ├── routes/                        # 14 Web Platform API Routes
│   │   ├── admin_auth.py
│   │   ├── admin_notifications.py
│   │   ├── architecture.py
│   │   ├── blog.py
│   │   ├── client_auth.py
│   │   ├── client_dashboard.py
│   │   ├── clients.py
│   │   ├── content.py
│   │   ├── demo_requests.py
│   │   ├── notifications.py
│   │   ├── password_reset.py
│   │   ├── security.py
│   │   ├── seo.py
│   │   └── uploads.py
│   ├── models/                        # Pydantic data schemas
│   └── utils/                         # Helper utilities (logger, helpers)
│
├── frontend/                           # Vue.js 3 client dashboard
├── admin/                              # Vue.js 3 admin dashboard
├── n8n_workflows/                      # 5 security automation JSON workflows
├── docs/                               # Core documentation mapping
│   ├── DEPLOYMENT.md                  # Detailed deployment guide
│   ├── structure.md                   # This file (tree map)
│   └── research/                       # Moved research PDFs, CSVs, TXTs
├── .env.example                        # Environment requirements
├── Dockerfile                          # Container setup
├── requirements.txt                    # Unified pip dependencies
├── README.md                           # Top-level introduction
├── design.md                           # System design & architecture summary
└── requirements.md                     # Functional spec requirements
```

## Technology Stack

- **Backend**: Python 3.11, FastAPI, LangChain
- **AI Engine**: Amazon Bedrock (Claude 3.5 Sonnet) + Ollama local fallback
- **Agent Intelligence**: Dual AI Feedback Loop + 12-Agent Workflow + Lifecycle Hooks
- **Memory & Storage**: DynamoDB (90-day TTL campaign memory), MongoDB (web platform), S3
- **RAG System**: ChromaDB, Bedrock Knowledge Bases
- **Compute**: AWS App Runner (Docker Container)
- **Frontend/Admin**: Vue.js 3, Three.js, Vite, CoreUI
- **Workflows**: n8n (5 security automation workflows)
- **Security**: AWS WAF, IAM, KMS, JWT (python-jose), bcrypt
