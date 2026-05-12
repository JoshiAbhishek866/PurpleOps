# Sentinel AI - Project Structure

## Directory Layout

```
sentinel-ai/
├── .kiro/                              # Kiro IDE configuration
│   ├── specs/                          # Feature specifications
│   │   └── sentinel-ai/
│   │       ├── requirements.md         # Requirements specification
│   │       ├── design.md              # Design document
│   │       └── tasks.md               # Implementation tasks
│   └── steering/                       # AI-DLC steering rules
│       ├── aws-aidlc-rules/
│       │   └── core-workflow.md       # Main workflow orchestration
│       └── aws-aidlc-rule-details/
│           ├── common/                 # Shared rules
│           │   ├── depth-levels.md
│           │   ├── question-format-guide.md
│           │   ├── session-continuity.md
│           │   └── scope-message.md
│           ├── inception/              # Inception stage rules
│           │   ├── workspace-detection.md
│           │   ├── requirements-analysis.md
│           │   ├── user-stories.md
│           │   ├── application-design.md
│           │   └── units-generation.md
│           ├── construction/           # Construction stage rules
│           │   ├── functional-design.md
│           │   ├── nfr-requirements.md
│           │   ├── nfr-design.md
│           │   ├── code-generation.md
│           │   └── build-and-test.md
│           └── operations/             # Operations stage rules
│               └── operations.md
│
├── src/                                # Source code
│   ├── __init__.py
│   ├── main.py                        # FastAPI application entry point
│   ├── config.py                      # Configuration management
│   └── agents/                        # AI agents
│       ├── __init__.py
│       ├── red_agent.py              # Offensive AI agent
│       └── blue_agent.py             # Defensive AI agent
│
├── docs/                               # Documentation
│   ├── ARCHITECTURE.md                # System architecture
│   └── DEPLOYMENT.md                  # Deployment guide
│
├── tests/                              # Test suite (to be created)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── infrastructure/                     # IaC (to be created)
│   └── cdk/                           # AWS CDK stacks
│
├── frontend/                           # Vue.js dashboard (to be created)
│   └── src/
│
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore rules
├── Dockerfile                          # Container image definition
├── requirements.txt                    # Python dependencies
├── README.md                           # Project overview
└── PROJECT_STRUCTURE.md               # This file
```

## v2.0 Architecture: Hierarchical Supervisor Pattern

```
CoordinatorAgent (Supervisor)
├── Owns CampaignState (single source of truth)
├── Enforces token budgets & turn limits (prevents infinite loops)
├── Routes tasks → Red Agent or Blue Agent
├── Generates deterministic audit trails
└── Registers campaigns to AWS Bedrock AgentCore Registry

RedAgent (Offensive Worker)          BlueAgent (Defensive Worker)
├── SQL Injection                    ├── WAF Rule Updates
├── XSS Testing                      ├── Security Group Modification
└── Privilege Escalation             ├── RAG Knowledge Query
                                     └── Compliance Report Generation

AgentRegistry (AWS Bedrock AgentCore)
├── Version-controlled agent storage ("ECR for AI Agents")
├── Cross-account agent discovery
├── Capability-based agent lookup
└── Cost tracking per agent version
```

## Key Components

### 1. Kiro Configuration (`.kiro/`)

- **specs/**: Feature specifications following spec-driven development
  - `requirements.md`: Functional and non-functional requirements (EARS notation)
  - `design.md`: Detailed system design and architecture
  - `tasks.md`: Implementation task breakdown

- **steering/**: AI Development Lifecycle (AI-DLC) rules
  - Organized by development stages: inception, construction, operations
  - Provides guidance for AI-assisted development workflow

### 2. Source Code (`src/`)

- **main.py**: FastAPI server with campaign management endpoints
- **config.py**: Centralized configuration using environment variables
- **agents/**: LangChain-based AI agents
  - `red_agent.py`: Offensive testing (SQL injection, XSS, privilege escalation)
  - `blue_agent.py`: Defensive response (WAF updates, remediation, reporting)

### 3. Documentation (`docs/`)

- **ARCHITECTURE.md**: System architecture and component diagrams
- **DEPLOYMENT.md**: Step-by-step deployment instructions

### 4. Infrastructure (To Be Created)

- AWS CDK stacks for infrastructure as code
- DynamoDB tables, S3 buckets, IAM roles, etc.

### 5. Frontend (To Be Created)

- Vue.js 3 dashboard for campaign management
- Real-time monitoring and compliance reporting

## Development Workflow

1. **Requirements** → Define in `.kiro/specs/sentinel-ai/requirements.md`
2. **Design** → Document in `.kiro/specs/sentinel-ai/design.md`
3. **Tasks** → Break down in `.kiro/specs/sentinel-ai/tasks.md`
4. **Implementation** → Code in `src/`
5. **Testing** → Tests in `tests/`
6. **Deployment** → Follow `docs/DEPLOYMENT.md`

## Getting Started

1. Review `README.md` for project overview
2. Read `.kiro/specs/sentinel-ai/requirements.md` for requirements
3. Study `.kiro/specs/sentinel-ai/design.md` for architecture
4. Follow `docs/DEPLOYMENT.md` for setup instructions

## Technology Stack

- **Backend**: Python 3.11, FastAPI, LangChain
- **AI**: Amazon Bedrock (Claude 3.5 Sonnet)
- **Data**: DynamoDB, S3, Knowledge Bases for Amazon Bedrock
- **Compute**: AWS App Runner (Docker)
- **Frontend**: Vue.js 3, AWS Amplify
- **IaC**: AWS CDK (Python)
- **Security**: AWS WAF, IAM, KMS

## Next Steps

1. Set up local development environment
2. Configure AWS credentials
3. Create DynamoDB tables and S3 buckets
4. Deploy to AWS App Runner
5. Build Vue.js frontend dashboard
