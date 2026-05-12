# Requirements Specification: Sentinel AI
## Autonomous Purple Teaming Platform

**Project Name:** Sentinel AI  
**Tagline:** "Attack to Defend. Autonomously."  
**Version:** 1.0  
**Date:** February 15, 2026

---

## 1. Introduction

### 1.1 Purpose
This document specifies the functional and non-functional requirements for Sentinel AI, an autonomous purple teaming platform that deploys dual-model AI agents to validate vulnerabilities through active exploitation and auto-remediation.

### 1.2 Scope
Sentinel AI addresses the reactive nature of traditional cybersecurity by implementing offensive (Red Team) and defensive (Blue Team) AI agents that operate in real-time on AWS serverless infrastructure.

### 1.3 Problem Statement
Traditional cybersecurity is reactive, manual, and generates high false positives. Standard AWS native tools (like GuardDuty) are passive observers that alert but do not validate or auto-remediate complex vulnerabilities.

### 1.4 Solution
An Autonomous Purple Teaming Platform with dual-model AI agents battling in real-time. The Offensive Agent actively (and safely) exploits vulnerabilities to validate risk, while the Defensive Agent auto-patches the infrastructure and learns from the attack.

---

## 2. Functional Requirements (EARS Notation)

### 2.1 Purple Teaming Loop

#### FR-001: Campaign Initiation (Event-Driven)
**WHEN** an administrator initiates a validation campaign from the Amplify UI, **THE SYSTEM SHALL** deploy the Red Agent with isolated IAM credentials and initialize a new attack session in DynamoDB.

#### FR-002: Attack Vector Planning (Ubiquitous)
**THE SYSTEM SHALL** utilize Amazon Bedrock (Claude 3.5 Sonnet) to analyze the target infrastructure and formulate attack payloads including SQL injection, XSS, privilege escalation, and API abuse vectors.

#### FR-003: Offensive Execution (Event-Driven)
**WHEN** the Red Agent formulates an attack payload, **THE SYSTEM SHALL** execute the attack using LangChain @tool function calling against the target AWS infrastructure while logging all actions to DynamoDB.

#### FR-004: Anomaly Detection (Event-Driven)
**WHEN** AWS WAF or CloudWatch detects an anomaly from the Red Agent attack, **THE SYSTEM SHALL** trigger the Blue Agent within 5 seconds with full context of the detected threat.

#### FR-005: RAG Knowledge Query (Event-Driven)
**WHEN** the Blue Agent is triggered, **THE SYSTEM SHALL** query the Knowledge Bases for Amazon Bedrock to retrieve relevant mitigation strategies from past attack patterns and CVE databases.

#### FR-006: Auto-Remediation (Event-Driven)
**WHEN** the Blue Agent identifies a mitigation strategy, **THE SYSTEM SHALL** automatically apply patches including WAF ACL rule updates, security group modifications, or IAM policy restrictions via AWS SDK.

#### FR-007: Session State Persistence (Ubiquitous)
**THE SYSTEM SHALL** log all attack outcomes, defense actions, and timestamps to DynamoDB with session correlation IDs for audit trail purposes.

#### FR-008: Knowledge Base Evolution (Event-Driven)
**WHEN** an attack is successfully mitigated, **THE SYSTEM SHALL** update the RAG Knowledge Base with the attack vector signature and successful remediation playbook to prevent future occurrences.

### 2.2 Automated Compliance

#### FR-009: Compliance Report Generation (Event-Driven)
**WHEN** a validation campaign completes, **THE SYSTEM SHALL** auto-generate SOC 2 and ISO 27001 audit reports based on simulated attacks and successful auto-remediations.

#### FR-010: Report Storage (Ubiquitous)
**THE SYSTEM SHALL** store all generated compliance reports in Amazon S3 with encryption at rest and versioning enabled.

#### FR-011: Compliance Dashboard (State-Driven)
**WHILE** a validation campaign is active, **THE SYSTEM SHALL** display real-time compliance metrics on the Vue.js dashboard including attack success rate, remediation time, and coverage percentage.

### 2.3 Agent Intelligence

#### FR-012: Tool Function Calling (Ubiquitous)
**THE SYSTEM SHALL** enable LangChain agents to execute local scripts including Nmap scans, AWS SDK operations, and vulnerability scanners through Bedrock's native @tool function calling.

#### FR-013: Attack Payload Validation (Unwanted Behavior)
**IF** the Red Agent generates an attack payload that targets production customer data, **THEN THE SYSTEM SHALL** reject the payload and log a security violation to DynamoDB.

#### FR-014: Defense Strategy Selection (Event-Driven)
**WHEN** multiple mitigation strategies are available, **THE SYSTEM SHALL** select the strategy with the highest success rate from historical RAG data and lowest infrastructure impact.

### 2.4 User Interface

#### FR-015: Campaign Dashboard (Ubiquitous)
**THE SYSTEM SHALL** provide a Vue.js dashboard hosted on AWS Amplify displaying active campaigns, agent status, attack vectors, and defense actions in real-time.

#### FR-016: Manual Override (Optional Feature)
**WHERE** an administrator requires manual intervention, **THE SYSTEM SHALL** provide controls to pause agents, approve high-risk remediations, or terminate campaigns.

#### FR-017: Historical Analysis (State-Driven)
**WHILE** viewing past campaigns, **THE SYSTEM SHALL** display attack timelines, defense response times, and knowledge base evolution metrics with filterable date ranges.

### 2.5 Cost Optimization

#### FR-018: Auto-Scaling (State-Driven)
**WHILE** no validation campaigns are active, **THE SYSTEM SHALL** scale AWS App Runner instances to zero to minimize compute costs.

#### FR-019: Bedrock Token Management (Ubiquitous)
**THE SYSTEM SHALL** implement token usage tracking and caching strategies to maintain Amazon Bedrock costs under $50 per month for 5 enterprise customers.

---

## 3. Non-Functional Requirements

### 3.1 Security

#### NFR-001: IAM Role Separation (Ubiquitous)
**THE SYSTEM SHALL** strictly separate IAM roles for Offensive and Defensive agents with the Red Agent having read-only access to production and the Blue Agent having write access to security controls only.

#### NFR-002: Encryption (Ubiquitous)
**THE SYSTEM SHALL** encrypt all data at rest in DynamoDB and S3 using AWS KMS and all data in transit using TLS 1.3.

#### NFR-003: Audit Logging (Ubiquitous)
**THE SYSTEM SHALL** maintain immutable audit logs in DynamoDB with CloudWatch Logs integration for all agent actions and administrative operations.

### 3.2 Performance

#### NFR-004: Response Time (Ubiquitous)
**THE SYSTEM SHALL** trigger the Blue Agent within 5 seconds of anomaly detection by AWS WAF or CloudWatch.

#### NFR-005: Remediation Time (Ubiquitous)
**THE SYSTEM SHALL** complete auto-remediation actions within 30 seconds of Blue Agent strategy selection.

#### NFR-006: RAG Query Latency (Ubiquitous)
**THE SYSTEM SHALL** return relevant mitigation strategies from Knowledge Bases for Amazon Bedrock within 2 seconds.

### 3.3 Scalability

#### NFR-007: Concurrent Campaigns (Ubiquitous)
**THE SYSTEM SHALL** support up to 10 concurrent validation campaigns per enterprise customer without performance degradation.

#### NFR-008: Knowledge Base Growth (Ubiquitous)
**THE SYSTEM SHALL** scale the RAG Knowledge Base to store at least 10,000 attack patterns and mitigation playbooks without query performance impact.

### 3.4 Cost Constraints

#### NFR-009: Unit Economics (Ubiquitous)
**THE SYSTEM SHALL** operate under $200 per month total infrastructure cost for 5 enterprise customers ($40 per customer).

#### NFR-010: MVP Cost Target (Ubiquitous)
**THE SYSTEM SHALL** maintain a sub-$25 monthly cost during MVP phase by leveraging AWS Free Tier and scale-to-zero capabilities.

### 3.5 Availability

#### NFR-011: Uptime (Ubiquitous)
**THE SYSTEM SHALL** maintain 99.5% uptime for the Amplify dashboard and App Runner services during business hours (9 AM - 6 PM EST).

#### NFR-012: Disaster Recovery (Unwanted Behavior)
**IF** a critical AWS service failure occurs, **THEN THE SYSTEM SHALL** gracefully degrade by pausing active campaigns and preserving session state in DynamoDB.

### 3.6 Compliance

#### NFR-013: SOC 2 Type II Alignment (Ubiquitous)
**THE SYSTEM SHALL** implement controls aligned with SOC 2 Type II requirements including access controls, encryption, and audit logging.

#### NFR-014: ISO 27001 Alignment (Ubiquitous)
**THE SYSTEM SHALL** implement security controls aligned with ISO 27001 standards for information security management.

---

## 4. Constraints

### 4.1 Technical Constraints
- **TC-001:** The system MUST use serverless-first architecture (NO Kubernetes/EKS).
- **TC-002:** The system MUST use AWS App Runner for compute hosting.
- **TC-003:** The system MUST use Amazon Bedrock with Claude 3.5 Sonnet model.
- **TC-004:** The system MUST use Python LangChain for agent framework.
- **TC-005:** The system MUST use Knowledge Bases for Amazon Bedrock for RAG implementation.

### 4.2 Business Constraints
- **BC-001:** The MVP must be deployable within Hackathon timeframe (48-72 hours).
- **BC-002:** The system must demonstrate clear ROI through automated compliance report generation.
- **BC-003:** The system must differentiate from passive monitoring tools (GuardDuty, Security Hub).

### 4.3 Operational Constraints
- **OC-001:** The system must require zero manual infrastructure management (zero-ops).
- **OC-002:** The system must scale to zero when idle to minimize costs.
- **OC-003:** The system must support deployment in a single AWS region initially.

---

## 5. Assumptions and Dependencies

### 5.1 Assumptions
- **A-001:** Administrators have AWS accounts with sufficient permissions to deploy App Runner, Bedrock, and DynamoDB.
- **A-002:** Target infrastructure for validation campaigns is non-production or isolated sandbox environments.
- **A-003:** Amazon Bedrock Claude 3.5 Sonnet is available in the deployment region.

### 5.2 Dependencies
- **D-001:** AWS App Runner service availability.
- **D-002:** Amazon Bedrock API access with Claude 3.5 Sonnet model.
- **D-003:** Knowledge Bases for Amazon Bedrock service availability.
- **D-004:** Python 3.11+ runtime environment.
- **D-005:** LangChain library compatibility with Bedrock.

---

## 6. Acceptance Criteria

### 6.1 MVP Success Criteria
1. Red Agent successfully executes at least 3 different attack vectors (SQL injection, XSS, privilege escalation).
2. Blue Agent detects and auto-remediates all 3 attacks within 30 seconds.
3. RAG Knowledge Base demonstrates learning by blocking repeat attacks automatically.
4. Compliance report is generated and stored in S3 after campaign completion.
5. Total infrastructure cost remains under $25 for MVP deployment.

### 6.2 Hackathon Demo Criteria
1. Live demonstration of Purple Teaming Loop from campaign initiation to auto-remediation.
2. Real-time dashboard showing agent battle and defense actions.
3. Generated SOC 2 compliance report displayed to judges.
4. Cost breakdown showing unit economics under $40 per customer.

---

## 7. Glossary

- **Purple Teaming:** Combined offensive (Red Team) and defensive (Blue Team) security testing.
- **EARS Notation:** Easy Approach to Requirements Syntax for structured requirement writing.
- **RAG:** Retrieval-Augmented Generation for AI knowledge retrieval.
- **CVE:** Common Vulnerabilities and Exposures database.
- **WAF:** Web Application Firewall.
- **IAM:** Identity and Access Management.
- **ACL:** Access Control List.

---

**Document Control:**
- **Author:** Kiro AI Assistant
- **Reviewed By:** [Abhishek Joshi]
- **Approved By:** [Abhishek Joshi]
- **Next Review Date:** [30-02-2026]
