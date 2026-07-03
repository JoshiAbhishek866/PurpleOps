# Requirements Specification: PurpleOps
## Autonomous Purple Teaming Platform

**Project Name:** PurpleOps  
**Tagline:** "Attack to Defend. Autonomously."  
**Version:** 2.0  
**Date:** March 16, 2026

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for PurpleOps, an autonomous purple teaming platform with dual-model AI agents, a 12-agent orchestration system, lifecycle hooks, persistent campaign memory, and a full web platform.

### 1.2 Scope
PurpleOps addresses the reactive nature of traditional cybersecurity by implementing:
- Offensive (Red Team) and defensive (Blue Team) AI agents with an attack-defense feedback loop
- 12 specialized security agents (5 offensive, 5 defensive, 2 core infrastructure)
- A full-stack web platform with admin panel, client dashboard, blog, SEO, and notification system
- Lifecycle hooks and persistent campaign memory for cross-session learning

### 1.3 Problem Statement
Traditional cybersecurity is reactive, manual, and generates high false positives. Standard AWS native tools (like GuardDuty) are passive observers that alert but do not validate or auto-remediate complex vulnerabilities. Existing security platforms lack persistent memory across engagements.

### 1.4 Solution
An Autonomous Purple Teaming Platform with:
1. **Dual AI agents** — Red Team exploits vulnerabilities; Blue Team auto-remediates
2. **Attack-Defense Feedback Loop** — Red probes Blue's past patches; Blue responds to Red's latest findings
3. **12-Agent Orchestrator** — Specialized agents for recon, scanning, vulnerability detection, compliance, incident response, etc.
4. **Campaign Memory** — Persistent DynamoDB-backed memory enabling cross-session learning with 90-day TTL
5. **Lifecycle Hooks** — Automatic context loading and result persistence across all agent executions

---

## 2. Functional Requirements (EARS Notation)

### 2.1 Purple Teaming Loop

#### FR-001: Campaign Initiation (Event-Driven)
**WHEN** an administrator initiates a campaign via `POST /campaigns/start`, **THE SYSTEM SHALL** deploy the Red Agent with session identity (`session_id`, `actor_id`), load prior target history from campaign memory, and initialize the attack-defense feedback loop.

#### FR-002: Attack Vector Planning (Ubiquitous)
**THE SYSTEM SHALL** utilize Amazon Bedrock (Claude 3.5 Sonnet) or Ollama (local fallback) to analyze the target and formulate attack payloads including SQL injection, XSS, privilege escalation, and API abuse vectors, enriched with memory context from prior campaigns.

#### FR-003: Offensive Execution (Event-Driven)
**WHEN** the Red Agent formulates an attack payload, **THE SYSTEM SHALL** execute the attack using LangChain `@tool` function calling against the target infrastructure while logging all actions to DynamoDB with proper session/actor IDs.

#### FR-004: Attack-Defense Feedback Loop (Event-Driven)
**WHEN** the Red Agent completes its execution, **THE SYSTEM SHALL**:
1. Persist Red Agent findings to campaign memory via `SecurityHookProvider`
2. Load Red Agent findings + Blue Team's prior defenses as context for Blue Agent via `AttackDefenseFeedbackHook`
3. Execute the Blue Agent with enriched context
4. Persist Blue Agent findings to campaign memory
5. Return combined campaign results

#### FR-005: RAG Knowledge Query (Event-Driven)
**WHEN** any agent requires contextual knowledge, **THE SYSTEM SHALL** query ChromaDB or Bedrock Knowledge Bases to retrieve relevant attack patterns, CVE data, and mitigation strategies.

#### FR-006: Auto-Remediation (Event-Driven)
**WHEN** the Blue Agent identifies a mitigation strategy, **THE SYSTEM SHALL** automatically apply patches including WAF ACL rule updates, security group modifications, or IAM policy restrictions via AWS SDK.

#### FR-007: Session State Persistence (Ubiquitous)
**THE SYSTEM SHALL** log all attack outcomes, defense actions, and timestamps to DynamoDB with session correlation IDs for audit trail purposes. Campaign memory entries SHALL have a 90-day TTL.

#### FR-008: Lifecycle Hooks (Ubiquitous)
**THE SYSTEM SHALL** execute `on_agent_init` before every agent execution (loading prior findings) and `on_agent_complete` after every agent execution (persisting results, triggering n8n, requesting LLM analysis) via the `SecurityHookProvider`.

### 2.2 Multi-Agent Orchestrator

#### FR-009: Agent Orchestration (Ubiquitous)
**THE SYSTEM SHALL** manage 12 specialized agents through a central orchestrator that handles agent lifecycle, workflow coordination, n8n integration, LLM enhancement, and database persistence.

#### FR-010: Offensive Agent Execution (Event-Driven)
**WHEN** a security scan is initiated, **THE SYSTEM SHALL** execute offensive agents in sequence:
1. **Recon Agent** — async DNS enumeration, concurrent subdomain discovery (10×), port scanning (20×)
2. **Scanner Agent** — async port scanning (50-concurrent via semaphore), Nmap or socket fallback
3. **Vulnerability Agent** — NVD API queries with rate limiting (Semaphore(5)), exponential backoff on 403, API key support
4. **Credential Testing Agent** — simulation mode credential checks, clearly labeled as `mode: simulation`
5. **Report Generator Agent** — aggregated reports in JSON, HTML (XSS-safe via `html.escape()`), Markdown

#### FR-011: Defensive Agent Execution (Event-Driven)
**WHEN** threats are detected, **THE SYSTEM SHALL** execute defensive agents:
1. **Threat Detection Agent** — log analysis, anomaly detection, IOC matching, pattern recognition
2. **Hardening Agent** — CIS/NIST/PCI-DSS compliance checking, remediation script generation
3. **Vulnerability Prioritization Agent** — CVSS-based risk prioritization
4. **Incident Response Agent** — automated incident classification, ticket creation, playbook execution
5. **Compliance Check Agent** — framework-based compliance assessment and audit reporting

#### FR-012: Agent Execution Timeout (Ubiquitous)
**THE SYSTEM SHALL** enforce a configurable execution timeout on all agents via `asyncio.wait_for()` (default: 300 seconds). Timed-out agents SHALL return a result with `status: "timeout"`.

#### FR-013: Non-Blocking Agent Execution (Ubiquitous)
**THE SYSTEM SHALL** ensure all network I/O operations (socket calls, DNS resolution) run via `asyncio.run_in_executor()` to prevent event loop blocking.

### 2.3 Web Platform

#### FR-014: Admin Authentication (Ubiquitous)
**THE SYSTEM SHALL** provide admin authentication with JWT tokens, bcrypt password hashing, and session management.

#### FR-015: Client Dashboard (Ubiquitous)
**THE SYSTEM SHALL** provide a Vue.js dashboard with real-time campaign monitoring, agent status, attack visualization, and compliance reports.

#### FR-016: Real-Time Notifications (Event-Driven)
**WHEN** a security event occurs, **THE SYSTEM SHALL** deliver real-time WebSocket notifications to connected clients via the `ConnectionManager` and persist notification history in MongoDB.

#### FR-017: Blog CMS (Ubiquitous)
**THE SYSTEM SHALL** provide a blog system with CRUD operations, slug generation, categorization, and draft/published status management.

#### FR-018: SEO Management (Ubiquitous)
**THE SYSTEM SHALL** provide SEO management for meta descriptions, keywords, and page optimization.

#### FR-019: File Uploads (Ubiquitous)
**THE SYSTEM SHALL** support secure file uploads with proper validation and storage.

### 2.4 Automated Compliance

#### FR-020: Compliance Report Generation (Event-Driven)
**WHEN** a validation campaign completes, **THE SYSTEM SHALL** auto-generate SOC 2 and ISO 27001 audit reports based on simulated attacks and successful auto-remediations.

#### FR-021: Report XSS Safety (Ubiquitous)
**THE SYSTEM SHALL** escape all user-controlled content in HTML reports via `html.escape()` to prevent cross-site scripting vulnerabilities.

### 2.5 n8n Workflow Automation

#### FR-022: Workflow Integration (Event-Driven)
**WHEN** an agent completes execution, **THE SYSTEM SHALL** trigger the appropriate n8n security workflow for downstream processing, either directly or via lifecycle hooks.

### 2.6 Cost Optimization

#### FR-023: Auto-Scaling (State-Driven)
**WHILE** no validation campaigns are active, **THE SYSTEM SHALL** scale AWS App Runner instances to zero to minimize compute costs.

#### FR-024: Bedrock Token Management (Ubiquitous)
**THE SYSTEM SHALL** implement token usage tracking and caching strategies to maintain Amazon Bedrock costs under $50 per month for 5 enterprise customers.

#### FR-025: NVD API Rate Management (Ubiquitous)
**THE SYSTEM SHALL** rate-limit NVD API calls to maximum 5 concurrent requests with exponential backoff on 403 responses, and support configuration of an NVD API key for higher rate limits.

---

## 3. Non-Functional Requirements

### 3.1 Security

#### NFR-001: IAM Role Separation (Ubiquitous)
**THE SYSTEM SHALL** strictly separate IAM roles for Offensive and Defensive agents with the Red Agent having read-only access to production and the Blue Agent having write access to security controls only.

#### NFR-002: Encryption (Ubiquitous)
**THE SYSTEM SHALL** encrypt all data at rest in DynamoDB and S3 using AWS KMS and all data in transit using TLS 1.3.

#### NFR-003: Audit Logging (Ubiquitous)
**THE SYSTEM SHALL** maintain immutable audit logs in DynamoDB with CloudWatch Logs integration for all agent actions and administrative operations.

#### NFR-004: Input Sanitization (Ubiquitous)
**THE SYSTEM SHALL** sanitize all user-controlled content before rendering in HTML reports to prevent XSS.

### 3.2 Performance

#### NFR-005: Agent Execution Timeout (Ubiquitous)
**THE SYSTEM SHALL** enforce a configurable timeout (default 300 seconds) on all agent executions to prevent hung processes.

#### NFR-006: Non-Blocking I/O (Ubiquitous)
**THE SYSTEM SHALL** run all blocking socket and DNS operations via `asyncio.run_in_executor()` to prevent event loop blocking under load.

#### NFR-007: Concurrent Scanning (Ubiquitous)
**THE SYSTEM SHALL** support concurrent port scanning (up to 50 simultaneous checks) and subdomain discovery (up to 10 simultaneous lookups) via asyncio semaphores.

#### NFR-008: Response Time (Ubiquitous)
**THE SYSTEM SHALL** trigger the Blue Agent within 5 seconds of anomaly detection by AWS WAF or CloudWatch.

#### NFR-009: Remediation Time (Ubiquitous)
**THE SYSTEM SHALL** complete auto-remediation actions within 30 seconds of Blue Agent strategy selection.

### 3.3 Scalability

#### NFR-010: Concurrent Campaigns (Ubiquitous)
**THE SYSTEM SHALL** support up to 10 concurrent validation campaigns per enterprise customer without performance degradation.

#### NFR-011: Knowledge Base Growth (Ubiquitous)
**THE SYSTEM SHALL** scale the RAG Knowledge Base to store at least 10,000 attack patterns and mitigation playbooks without query performance impact.

#### NFR-012: Campaign Memory TTL (Ubiquitous)
**THE SYSTEM SHALL** automatically expire campaign memory entries after 90 days to prevent unbounded storage growth.

### 3.4 Cost Constraints

#### NFR-013: Unit Economics (Ubiquitous)
**THE SYSTEM SHALL** operate under $200 per month total infrastructure cost for 5 enterprise customers ($40 per customer).

#### NFR-014: MVP Cost Target (Ubiquitous)
**THE SYSTEM SHALL** maintain a sub-$25 monthly cost during MVP phase.

### 3.5 Availability

#### NFR-015: Uptime (Ubiquitous)
**THE SYSTEM SHALL** maintain 99.5% uptime for the dashboard and API services during business hours.

#### NFR-016: Disaster Recovery (Unwanted Behavior)
**IF** a critical service failure occurs, **THEN THE SYSTEM SHALL** gracefully degrade by pausing active campaigns and preserving session state.

### 3.6 Compliance

#### NFR-017: SOC 2 Type II Alignment (Ubiquitous)
**THE SYSTEM SHALL** implement controls aligned with SOC 2 Type II requirements including access controls, encryption, and audit logging.

#### NFR-018: ISO 27001 Alignment (Ubiquitous)
**THE SYSTEM SHALL** implement security controls aligned with ISO 27001 standards.

---

## 4. Constraints

### 4.1 Technical Constraints
- **TC-001:** The system MUST use serverless-first architecture (NO Kubernetes/EKS).
- **TC-002:** The system MUST use AWS App Runner for compute hosting.
- **TC-003:** The system MUST use Amazon Bedrock (Claude 3.5 Sonnet) with Ollama as local fallback.
- **TC-004:** The system MUST use Python LangChain for the Red/Blue agent framework.
- **TC-005:** The system MUST use a custom multi-agent orchestrator for the 12 specialized agents.
- **TC-006:** All blocking I/O operations MUST be wrapped in `asyncio.run_in_executor()`.
- **TC-007:** Campaign memory MUST use DynamoDB with a 90-day TTL.

### 4.2 Business Constraints
- **BC-001:** The system must demonstrate clear ROI through automated compliance report generation.
- **BC-002:** The system must differentiate from passive monitoring tools (GuardDuty, Security Hub).

### 4.3 Operational Constraints
- **OC-001:** The system must require zero manual infrastructure management (zero-ops).
- **OC-002:** The system must scale to zero when idle to minimize costs.
- **OC-003:** The system must support deployment in a single AWS region initially.

---

## 5. Assumptions and Dependencies

### 5.1 Assumptions
- **A-001:** Administrators have AWS accounts with sufficient permissions for App Runner, Bedrock, and DynamoDB.
- **A-002:** Target infrastructure for validation campaigns is non-production or isolated.
- **A-003:** Amazon Bedrock Claude 3.5 Sonnet is available in the deployment region.
- **A-004:** MongoDB is available for the web platform features (blog, clients, notifications, SEO).

### 5.2 Dependencies
- **D-001:** AWS App Runner service availability
- **D-002:** Amazon Bedrock API access with Claude 3.5 Sonnet model
- **D-003:** DynamoDB for campaigns, executions, and campaign memory
- **D-004:** MongoDB for web platform data (auth, blog, clients, notifications)
- **D-005:** Python 3.11+ runtime environment
- **D-006:** LangChain library compatibility with Bedrock
- **D-007:** n8n instance for workflow automation
- **D-008:** NVD API availability (rate-limited: 5/30s without key, 50/30s with key)

---

## 6. Acceptance Criteria

### 6.1 Core Success Criteria
1. Red Agent successfully executes at least 3 different attack vectors (SQL injection, XSS, privilege escalation).
2. Blue Agent detects and auto-remediates all 3 attacks within 30 seconds.
3. Attack-defense feedback loop demonstrates learning across campaigns.
4. Campaign memory persists findings across sessions with 90-day TTL.
5. Lifecycle hooks auto-load context and persist results for all agent executions.
6. All 12 orchestrator agents execute successfully with timeout protection.
7. Compliance report is generated and stored after campaign completion.

### 6.2 Production Readiness Criteria
1. No blocking socket calls in async agents (all via `run_in_executor()`).
2. All agents have configurable execution timeouts.
3. NVD API rate limiting with exponential backoff.
4. HTML reports are XSS-safe via `html.escape()`.
5. Credential testing results clearly labeled as simulation.
6. No bare `except:` clauses in the codebase.
7. Zero stale imports across all modules.

---

## 7. Glossary

- **Purple Teaming:** Combined offensive (Red Team) and defensive (Blue Team) security testing.
- **EARS Notation:** Easy Approach to Requirements Syntax for structured requirement writing.
- **RAG:** Retrieval-Augmented Generation for AI knowledge retrieval.
- **CVE:** Common Vulnerabilities and Exposures database.
- **NVD:** National Vulnerability Database.
- **WAF:** Web Application Firewall.
- **IAM:** Identity and Access Management.
- **Lifecycle Hooks:** Automatic pre/post execution callbacks (`on_agent_init`, `on_agent_complete`).
- **Campaign Memory:** Persistent DynamoDB storage of per-target findings with TTL.
- **Feedback Loop:** Red Agent probes Blue's past defenses; Blue responds to Red's latest findings.

---

**Document Control:**
- **Author:** Abhishek Joshi
- **Version:** 2.0 (Updated March 16, 2026)
- **Previous Version:** 1.0 (February 15, 2026) — Pre-integration
