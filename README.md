# PurpleOps — Autonomous Purple Teaming Platform

> *Attack to Defend. Autonomously.*

PurpleOps deploys an 11-agent AI hierarchy to **find real vulnerabilities, apply real remediations, and verify the fix worked** — without human intervention.

---

## The Undeniable Value Proposition

Traditional security audits cost $30k and take weeks, delivering only a PDF report. 
PurpleOps delivers an **automated proof of fix**:
1. **Attack:** Deterministic and LLM agents probe the target (SQLi, XSS, etc.)
2. **Defend:** Defensive agents analyze findings and apply AWS WAF remediations.
3. **Verify:** The Red agent re-runs the exact attack. If it gets an HTTP 403, the fix is verified.

---

## 🏗 Architecture (Hybrid AI + Deterministic)

PurpleOps has moved to a robust, cost-effective **Hybrid Architecture** that ensures "One Agent, One Job" and separates AI reasoning from deterministic execution.

**Cloud Brain (LLM Decision Makers)**
- `Campaign Coordinator`: Central routing and campaign state management.
- `Red Team Lead`: Formulates attack strategies based on recon data.
- `Blue Team Lead`: Formulates defense strategies based on vulnerability data.
- **Primary LLM:** DeepSeek (Default - highly cost-effective) with fallbacks to Ollama (local) and AWS Bedrock.

**Local Execution (Deterministic Workers)**
- 8 specialized agents (Recon, Scanner, Attack, Threat Detection, Hardening, Compliance, etc.) executing specialized tasks without LLM reasoning.
- Unified communication via the strict `TaskResult` contract.

---

## Quickstart

### 1. Spin up a vulnerable test target (Only test on sandboxes!)

```bash
docker run -d -p 8888:80 vulnerables/web-dvwa
```

### 2. Install & Configure PurpleOps

```bash
git clone https://github.com/JoshiAbhishek866/PurpleOps.git
cd PurpleOps

# Install dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
```

**Edit `.env`** to set your LLM provider:
```env
# Choose: deepseek, bedrock, or ollama
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key_here

# Required for WAF remediation capabilities:
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

### 3. Start the API

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 4. Run a Campaign

```bash
curl -X POST http://localhost:8000/api/v1/campaigns/start \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://localhost:8888",
    "target_description": "DVWA local test",
    "max_attack_turns": 2,
    "max_defense_turns": 2
  }'
```

---

## Core Infrastructure

- **`src/llm/provider.py`**: Abstract LLM factory allowing instant switching between DeepSeek, Bedrock, and Ollama.
- **`src/agents/coordinator.py`**: State machine supervising the Red/Blue Team Leads.
- **`src/models/`**: Defines the `TaskResult` contract, providing a universal schema enabling deterministic agents to communicate flawlessly with the Cloud Brain.

---

## Roadmap

- [x] Unify Red/Blue systems into a single Coordinator hierarchy
- [x] Abstraction layer for LLM (DeepSeek integration)
- [x] Standardize Agent Communication (`TaskResult` contract)
- [ ] Migrate Campaign State from DynamoDB to MongoDB
- [ ] Build and release standalone `purpleops` CLI package
- [ ] Deploy Cloud Brain to Railway

## License

MIT
