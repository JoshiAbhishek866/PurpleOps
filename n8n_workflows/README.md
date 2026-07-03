# N8N Workflows Index

## Overview

This directory contains all n8n workflow templates for PurpleOps security automation platform.

---

## Workflows

### 1. Security Scan Orchestration

**File:** `1_security_scan_orchestration.json`

**Purpose:** Orchestrate multi-agent security scans

**Trigger:** Webhook (POST)

**Webhook Path:** `/webhook/security-scan`

**Flow:**

```
Webhook → Parse Variables → Recon Agent → Scanner Agent →
Vulnerability Agent → Merge Results → Save to MongoDB → Respond
```

**Input:**

```json
{
  "target": "example.com",
  "scan_type": "full_scan",
  "execution_id": "exec_123"
}
```

**Output:**

```json
{
  "status": "success",
  "execution_id": "exec_123",
  "message": "Security scan completed",
  "results": { ... }
}
```

**Use Case:** Main workflow for coordinating security scans across multiple agents

---

### 2. AI Vulnerability Analysis

**File:** `2_ai_vulnerability_analysis.json`

**Purpose:** AI-powered vulnerability analysis using Ollama LLM

**Trigger:** Webhook (POST)

**Webhook Path:** `/webhook/ai-vulnerability-analysis`

**Flow:**

```
Webhook → Parse Vulnerability → Ollama Analysis →
Parse AI Response → Save to DB → Respond
```

**Input:**

```json
{
  "title": "SQL Injection in Login Form",
  "cve": "CVE-2024-0001",
  "description": "...",
  "cvss": 9.8
}
```

**Output:**

```json
{
  "status": "success",
  "vulnerability_id": "CVE-2024-0001",
  "analysis": {
    "severity": "high",
    "impact": "...",
    "recommendations": [...]
  }
}
```

**Use Case:** Deep AI analysis of discovered vulnerabilities

---

### 3. Automated Patch Recommendation

**File:** `3_automated_patch_recommendation.json`

**Purpose:** Generate AI-powered patch recommendations

**Trigger:** Webhook (POST)

**Webhook Path:** `/webhook/patch-recommendation`

**Flow:**

```
Webhook → Parse CVE → Ollama Generate Patch →
Format Recommendations → Save Patch → Update Vulnerability → Respond
```

**Input:**

```json
{
  "cve": "CVE-2024-0001",
  "title": "SQL Injection",
  "description": "...",
  "component": "auth/login.php",
  "cvss": 9.8
}
```

**Output:**

```json
{
  "status": "success",
  "patch_id": "patch_123",
  "message": "Patch recommendations generated",
  "patch": {
    "title": "Security Update 2024-01",
    "version": "1.2.3",
    "actions": [...],
    "checklist": [...],
    "estimated_time_minutes": 30
  }
}
```

**Use Case:** Automated generation of remediation steps

---

### 4. Incident Response Automation

**File:** `4_incident_response_automation.json`

**Purpose:** Automated incident response with ticketing and notifications

**Trigger:** Webhook (POST)

**Webhook Path:** `/webhook/incident-response`

**Flow:**

```
Webhook → Parse Incident → Check Severity → Ollama Analyze →
Parse Analysis → Save Incident → Create JIRA Ticket →
Send Notification → Update Record → Respond
```

**Input:**

```json
{
  "title": "Suspicious Login Attempts",
  "severity": "high",
  "description": "Multiple failed logins from IP 192.168.1.100",
  "source_ip": "192.168.1.100",
  "target_system": "auth.example.com"
}
```

**Output:**

```json
{
  "status": "success",
  "incident_id": "inc_123",
  "ticket_id": "JIRA-1234",
  "ticket_url": "https://jira.example.com/browse/JIRA-1234",
  "ai_analysis": {
    "summary": "...",
    "threat_level": "high",
    "immediate_actions": [...]
  }
}
```

**Use Case:** Automated incident detection, analysis, and response

---

### 5. Compliance Report Generation

**File:** `5_compliance_report_generation.json`

**Purpose:** Automated weekly compliance reports

**Trigger:** Schedule (Cron: Every Monday at midnight)

**Cron Expression:** `0 0 * * 1`

**Flow:**

```
Schedule Trigger → Fetch Scan Results → Fetch Vulnerabilities →
Fetch Patches → Merge Data → Prepare Report → Ollama Generate Summary →
Format Report → Save to DB → Send Email
```

**Output:**

```json
{
  "report_id": "report_123",
  "title": "Weekly Security Compliance Report",
  "period": "Last 7 Days",
  "statistics": {
    "total_scans": 45,
    "total_vulnerabilities": 120,
    "by_severity": { ... }
  },
  "ai_analysis": {
    "executive_summary": "...",
    "security_posture": 85,
    "compliance_scores": {
      "cis": 80,
      "nist": 75,
      "pci_dss": 70
    }
  }
}
```

**Use Case:** Weekly automated compliance reporting

---

## Import Instructions

### 1. Access n8n

```
http://localhost:5678
```

### 2. Import Workflow

1. Click **Workflows** in sidebar
2. Click **Import from File**
3. Select JSON file
4. Click **Import**

### 3. Configure Workflow

1. Update MongoDB credentials (if using MongoDB nodes)
2. Update API endpoints if needed
3. Verify Ollama URL: `http://localhost:11434`

### 4. Activate Workflow

1. Click **Activate** toggle (top right)
2. Note the webhook URL (for webhook-triggered workflows)

---

## Webhook URLs

After importing and activating, your webhooks will be available at:

```
http://localhost:5678/webhook/security-scan
http://localhost:5678/webhook/ai-vulnerability-analysis
http://localhost:5678/webhook/patch-recommendation
http://localhost:5678/webhook/incident-response
```

---

## Testing Workflows

### Test Workflow 1 (Security Scan)

```powershell
curl -X POST http://localhost:5678/webhook/security-scan `
  -H "Content-Type: application/json" `
  -d '{
    "target": "example.com",
    "scan_type": "quick_scan",
    "execution_id": "test_001"
  }'
```

### Test Workflow 2 (AI Analysis)

```powershell
curl -X POST http://localhost:5678/webhook/ai-vulnerability-analysis `
  -H "Content-Type: application/json" `
  -d '{
    "title": "SQL Injection",
    "cve": "CVE-2024-0001",
    "description": "SQL injection in login form",
    "cvss": 9.8
  }'
```

### Test Workflow 3 (Patch Recommendation)

```powershell
curl -X POST http://localhost:5678/webhook/patch-recommendation `
  -H "Content-Type: application/json" `
  -d '{
    "cve": "CVE-2024-0001",
    "title": "SQL Injection",
    "description": "Vulnerability description",
    "component": "auth/login.php",
    "cvss": 9.8
  }'
```

### Test Workflow 4 (Incident Response)

```powershell
curl -X POST http://localhost:5678/webhook/incident-response `
  -H "Content-Type: application/json" `
  -d '{
    "title": "Suspicious Login Attempts",
    "severity": "high",
    "description": "Multiple failed logins",
    "source_ip": "192.168.1.100",
    "target_system": "auth.example.com"
  }'
```

---

## Customization

### Modify LLM Model

In any workflow using Ollama, change the model:

```json
{
  "model": "llama2" // Change to: mistral, codellama, etc.
}
```

### Adjust Timeouts

For slower LLM responses:

```json
{
  "options": {
    "timeout": 90000 // 90 seconds
  }
}
```

### Add Error Handling

Add error handling nodes after HTTP requests to catch failures.

---

## Monitoring

### View Execution History

1. Go to **Executions** in n8n
2. Filter by workflow
3. View execution details and logs

### Debug Mode

1. Click **Execute Workflow** (manual trigger)
2. View step-by-step execution
3. Check node outputs

---

## Dependencies

- **n8n:** v1.0.0+
- **Ollama:** Running on port 11434
- **MongoDB:** Running on port 27017 (for workflows 5)
- **PurpleOps Backend:** Running on port 8000

---

## Troubleshooting

### Workflow Not Triggering

- Check if workflow is activated (green toggle)
- Verify webhook URL is correct
- Check n8n logs: `docker logs n8n`

### Ollama Timeout

- Increase timeout in HTTP Request node
- Use a faster model (mistral instead of llama2)
- Check Ollama is running: `ollama list`

### MongoDB Connection Failed

- Update MongoDB credentials in workflow
- Verify MongoDB is running
- Check connection string

---

## Next Steps

1. Import all 5 workflows
2. Activate each workflow
3. Test with sample data
4. Integrate with PurpleOps backend
5. Monitor execution logs
6. Customize prompts for better AI responses
