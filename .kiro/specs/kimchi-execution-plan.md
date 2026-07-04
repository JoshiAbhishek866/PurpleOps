# PurpleOps — Kimchi Execution Plan
> **Status:** Active Execution Checklist
> **Target:** Kimchi (Lead Execution Agent)

This document contains the step-by-step technical execution checkpoints synthesized from the strategy documents (`.kiro/research/01-rca-and-technical-debt.md`, `02-gtm-strategy-and-value-proposition.md`, and `03-agent-hierarchy-and-architecture.md`). 

Several items from the original RCA have already been completed (e.g., Rebranding, Dead Code deletion, BlueAgent lazy loading). This plan focuses on the remaining action items, organized logically for autonomous execution.

---

## Phase A: Fix & Simplify (Immediate Priorities)

This phase stabilizes the existing codebase for the new Hybrid Architecture (Cloud Brain + Local Client) and removes expensive or overly complex dependencies (AWS DynamoDB, Bedrock).

### Checkpoint A1: LLM Provider Factory
*Goal: Remove hard dependency on AWS Bedrock to drastically reduce costs and enable local testing.*
- `[ ]` Create `src/core/llm_factory.py` with a `get_llm()` function.
- `[ ]` Implement support for `DeepSeek` (via `langchain-deepseek` or OpenAI compatible endpoint).
- `[ ]` Implement support for `Ollama` (via `langchain-community.chat_models.ChatOllama`) for local, zero-cost dev.
- `[ ]` Implement fallback support for `AWS Bedrock` (existing `ChatBedrock`).
- `[ ]` Read `LLM_PROVIDER` from `.env` to determine which LLM to instantiate.
- `[ ]` Update `RedAgent`, `BlueAgent`, and `CoordinatorAgent` to use `get_llm()` instead of directly instantiating `ChatBedrock`.

### Checkpoint A2: MongoDB Migration for Coordinator
*Goal: Remove AWS DynamoDB dependency so the cloud server can run entirely on Railway + MongoDB Atlas (Free Tier).*
- `[ ]` Review `src/agents/coordinator_agent.py` and identify all DynamoDB interactions (state loading, saving).
- `[ ]` Update `CoordinatorAgent` to use `src/core/database.py` (MongoDB) for loading and saving campaign states instead of DynamoDB.
- `[ ]` Ensure backward compatibility with existing campaign state JSON structures.
- `[ ]` Remove DynamoDB table definitions and environment variables from `config.py` if no longer needed by other agents.

### Checkpoint A3: Campaign API Route (Client-Server Bridge)
*Goal: Create the HTTP API endpoints that the local CLI client will use to communicate with the Cloud Brain.*
- `[ ]` Create `src/routes/campaigns.py` as an APIRouter.
- `[ ]` Add `POST /api/campaigns/start` to instantiate the Coordinator and return the first set of execution instructions.
- `[ ]` Add `POST /api/campaigns/{id}/results` to submit local agent findings (JSON) to the Coordinator and get the next set of instructions.
- `[ ]` Add `GET /api/campaigns/{id}/status` to check the status of an ongoing campaign.
- `[ ]` Add `GET /api/campaigns/{id}/report` to fetch the final compliance/security report.
- `[ ]` Register the new router in `src/main.py`.

### Checkpoint A4: Token Budget Enforcement
*Goal: Prevent runaway LLM costs during long campaign loops.*
- `[ ]` In `src/agents/coordinator_agent.py`, locate the `tokens_used` state variable.
- `[ ]` After each LLM invocation in the campaign loop, extract the token usage from the response metadata.
- `[ ]` Increment `self.tokens_used`.
- `[ ]` Ensure `is_budget_exhausted()` correctly halts the campaign if the limit is reached.

### Checkpoint A5: TaskResult Dataclass
*Goal: Standardize the communication contract between local deterministic tools and cloud LLM agents.*
- `[ ]` Create `src/models/task_result.py`.
- `[ ]` Define `@dataclass TaskResult` (agent_id, task_id, campaign_id, status, findings, metrics, timestamp).
- `[ ]` Define `@dataclass Finding` (finding_id, severity, category, title, description, evidence, cwe_id, mitre_id, remediation).

---

## Phase B: Hybrid Hierarchy & CLI Implementation

This phase implements the architectural separation: deterministic execution runs locally, while LLM decision-making runs in the cloud.

### Checkpoint B1: Build the CLI Client (`purpleops`)
*Goal: Build the pip-installable local client that users will run on their machines.*
- `[ ]` Create a new directory structure for the CLI (e.g., `cli/` or `src/cli/`).
- `[ ]` Implement `cli.py` using `click` or `argparse`.
- `[ ]` Add commands: `purpleops auth`, `purpleops scan --target <ip>`, and `purpleops report`.
- `[ ]` Implement `client.py` to handle HTTPS communication with the Cloud API (`/api/campaigns/*`).
- `[ ]` Move the deterministic specialist agents (Recon, Scanner, Vuln, ThreatDetection, Hardening) into the CLI execution path.

### Checkpoint B2: Refactor Specialist Agents to `TaskResult`
*Goal: Update all local agents to speak the new universal contract.*
- `[ ]` Update `ReconAgent`, `ScannerAgent`, `VulnAgent`, etc. to return instances of the `TaskResult` dataclass instead of raw ad-hoc dictionaries.
- `[ ]` Ensure JSON serialization works perfectly for transmission over the API.

### Checkpoint B3: Build Team Leads (Cloud Supervisors)
*Goal: Reduce the cognitive load on the Coordinator by delegating to specialized Leads.*
- `[ ]` Create `src/agents/red_team_lead.py` (LLM-powered). It analyzes local agent findings and plans the next attack sequence.
- `[ ]` Create `src/agents/blue_team_lead.py` (LLM-powered). It analyzes findings and plans remediation strategies.
- `[ ]` Update `CoordinatorAgent` to delegate tasks to the Red/Blue Team Leads rather than managing the 10+ sub-agents directly.

### Checkpoint B4: Wire ScopeEnforcer & Memory Hooks
*Goal: Ensure safety and enable cross-campaign learning.*
- `[ ]` Instantiate `ScopeEnforcer` in both the local CLI and the cloud Coordinator to provide defense-in-depth against scanning out-of-scope targets.
- `[ ]` Wire up `StructuredMemory` and `AttackDefenseFeedbackHook` in the Coordinator to persist learnings across campaigns.

---

## Phase C: Deployment & GTM

This phase focuses on getting the product live and executing the Go-To-Market strategy.

### Checkpoint C1: Cloud Deployment
*Goal: Deploy the Cloud Brain to production.*
- `[ ]` Configure `Dockerfile` and `railway.json` (or `railway.toml`) for deployment.
- `[ ]` Deploy the FastAPI backend to Railway ($5/mo tier).
- `[ ]` Provision and connect MongoDB Atlas M0 (Free Tier).

### Checkpoint C2: Client Publishing
*Goal: Make the CLI available to users.*
- `[ ]` Write `setup.py` or `pyproject.toml` for the `purpleops` package.
- `[ ]` Publish the package to PyPI.

### Checkpoint C3: Launch Artifacts
*Goal: Execute the Peter Steinberger / HackerNews launch playbook.*
- `[ ]` Create a 60-second Loom/demo video showing an attack → fix → verify loop.
- `[ ]` Deploy the frontend to Netlify and create a `demo.purpleops.io` landing page.
- `[ ]` Draft the HackerNews "Show HN" post text, emphasizing the "automated proof of fix" value proposition.

---

## Kimchi's Execution Protocol

When Kimchi is invoked to work on these tasks, it should:
1. Claim a checkpoint (e.g., "Starting Checkpoint A1").
2. Perform necessary code changes, focusing strictly on the requirements of that checkpoint.
3. Test locally where possible (e.g., verifying `llm_factory.py` loads correctly).
4. Mark the checkpoint as `[x]` upon completion.
5. Provide a brief summary of the completed checkpoint before moving to the next.
