"""
Red Agent — Sentinel AI
========================
Offensive AI agent that executes real HTTP-based security tests.

All attacks are real HTTP requests against the target URL.
Results are based on actual HTTP responses — not simulations.
Safety: targets must be explicitly allowlisted (non-production only).
"""

import httpx
import re
import time
from datetime import datetime
from typing import Optional, List, Dict

import boto3
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool

from src.config import Config

# ── AWS clients ──────────────────────────────────────────────────────────────
_dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
_audit_table = _dynamodb.Table(Config.DYNAMODB_TABLE_AUDIT)

# ── Safety: block production-looking targets ──────────────────────────────────
_BLOCKED_PATTERNS = re.compile(
    r"(prod|production|live|customer|billing|payment|bank|finance)",
    re.IGNORECASE,
)

def _is_safe_target(url: str) -> bool:
    """Return True only if the target looks like a non-production sandbox."""
    return not _BLOCKED_PATTERNS.search(url)

def _log_audit(session_id: str, action: str, target: str, outcome: str, extra: dict = None):
    item = {
        "session_id": session_id,
        "event_timestamp": int(datetime.utcnow().timestamp()),
        "agent_type": "RED",
        "action": action,
        "target": target,
        "outcome": outcome,
    }
    if extra:
        item.update({k: v for k, v in extra.items() if isinstance(v, (str, int, float, bool))})
    try:
        _audit_table.put_item(Item=item)
    except Exception:
        pass  # Audit failure must never break the attack


# ── Attack Tools ──────────────────────────────────────────────────────────────

@tool
def test_sql_injection(target_url: str, session_id: str = "default") -> dict:
    """
    Test SQL injection against the target URL using real HTTP requests.
    Detects: SQL error signatures in body, anomalous response length deltas.
    Returns structured findings with exact HTTP evidence.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected",
                "attack_type": "SQL Injection", "vulnerable": False, "findings": []}

    payloads = [
        "' OR '1'='1",
        "' OR 1=1--",
        "'; DROP TABLE users--",
        "1 UNION SELECT null,null,null--",
        "' AND SLEEP(2)--",  # Time-based blind SQLi
    ]

    sql_error_signatures = [
        "sql syntax", "mysql_fetch", "ora-", "syntax error",
        "unclosed quotation", "quoted string not properly", "pg_query",
        "sqlite_", "microsoft sql", "sqlstate", "invalid query",
        "you have an error in your sql",
    ]

    findings = []
    baseline_len = 0

    try:
        with httpx.Client(timeout=12, follow_redirects=True) as client:
            # Baseline: neutral request
            try:
                baseline = client.get(target_url, timeout=8)
                baseline_len = len(baseline.text)
            except httpx.RequestError:
                baseline_len = 0

            for payload in payloads:
                try:
                    start = time.monotonic()
                    resp = client.get(
                        target_url,
                        params={"id": payload, "q": payload, "search": payload},
                        timeout=10,
                    )
                    elapsed = time.monotonic() - start
                    body_lower = resp.text.lower()

                    # 1. SQL error signature in body
                    matched_sig = next((s for s in sql_error_signatures if s in body_lower), None)
                    if matched_sig:
                        findings.append({
                            "payload": payload,
                            "indicator": f"SQL error signature detected: '{matched_sig}'",
                            "http_status": resp.status_code,
                            "response_length": len(resp.text),
                            "evidence": resp.text[:300],
                        })
                        continue

                    # 2. Time-based: >2s delay suggests blind SQLi
                    if "SLEEP" in payload and elapsed > 2.0:
                        findings.append({
                            "payload": payload,
                            "indicator": f"Time-based SQLi: response delayed {elapsed:.1f}s",
                            "http_status": resp.status_code,
                            "elapsed_seconds": round(elapsed, 2),
                        })
                        continue

                    # 3. Anomalous response length vs baseline
                    delta = abs(len(resp.text) - baseline_len)
                    if baseline_len > 0 and delta > 500 and resp.status_code == 200:
                        findings.append({
                            "payload": payload,
                            "indicator": f"Anomalous response delta: {delta} bytes (possible data leak)",
                            "http_status": resp.status_code,
                            "response_length": len(resp.text),
                            "baseline_length": baseline_len,
                        })

                except httpx.TimeoutException:
                    # Timeout itself can be a time-based SQLi signal
                    if "SLEEP" in payload:
                        findings.append({
                            "payload": payload,
                            "indicator": "Request timed out — likely time-based SQLi",
                            "http_status": None,
                        })
                except httpx.RequestError:
                    continue

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "SQL Injection",
                "vulnerable": False, "findings": []}

    # Deduplicate by payload
    seen_payloads = set()
    unique_findings = []
    for f in findings:
        if f["payload"] not in seen_payloads:
            seen_payloads.add(f["payload"])
            unique_findings.append(f)

    vulnerable = len(unique_findings) > 0
    outcome = "VULNERABLE" if vulnerable else "NOT_VULNERABLE"
    _log_audit(session_id, "sql_injection_test", target_url, outcome,
               {"payloads_tested": len(payloads), "findings_count": len(unique_findings)})

    return {
        "attack_type": "SQL Injection",
        "target": target_url,
        "status": outcome,
        "vulnerable": vulnerable,
        "findings": unique_findings,
        "payloads_tested": len(payloads),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_xss(target_url: str, session_id: str = "default") -> dict:
    """
    Test Cross-Site Scripting (XSS): checks GET params, POST body, and
    JSON body for unencoded payload reflection.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected",
                "attack_type": "XSS", "vulnerable": False, "findings": []}

    payloads = [
        "<script>alert('sentinel-xss')</script>",
        "<img src=x onerror=alert(1)>",
        "'><svg onload=alert(1)>",
        "javascript:alert(document.cookie)",
        "\"><script>alert(1)</script>",
    ]

    findings = []
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            for payload in payloads:
                # Test 1: GET query params
                try:
                    resp = client.get(
                        target_url,
                        params={"q": payload, "search": payload, "name": payload, "input": payload},
                        timeout=8,
                    )
                    if payload in resp.text:
                        findings.append({
                            "vector": "GET parameter",
                            "payload": payload,
                            "indicator": "Payload reflected unencoded in GET response",
                            "http_status": resp.status_code,
                            "evidence": resp.text[max(0, resp.text.find(payload)-50):
                                                   resp.text.find(payload)+len(payload)+50],
                        })
                        continue
                except httpx.RequestError:
                    pass

                # Test 2: POST form body
                try:
                    resp = client.post(
                        target_url,
                        data={"q": payload, "comment": payload, "message": payload},
                        timeout=8,
                    )
                    if payload in resp.text:
                        findings.append({
                            "vector": "POST form body",
                            "payload": payload,
                            "indicator": "Payload reflected unencoded in POST response",
                            "http_status": resp.status_code,
                        })
                except httpx.RequestError:
                    pass

    except Exception as e:
        return {"status": "error", "error": str(e), "attack_type": "XSS",
                "vulnerable": False, "findings": []}

    # Deduplicate by payload
    seen = set()
    unique = [f for f in findings if not (f["payload"] in seen or seen.add(f["payload"]))]

    vulnerable = len(unique) > 0
    outcome = "VULNERABLE" if vulnerable else "NOT_VULNERABLE"
    _log_audit(session_id, "xss_test", target_url, outcome,
               {"payloads_tested": len(payloads), "findings_count": len(unique)})

    return {
        "attack_type": "XSS",
        "target": target_url,
        "status": outcome,
        "vulnerable": vulnerable,
        "findings": unique,
        "payloads_tested": len(payloads),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_auth_bypass(target_url: str, session_id: str = "default") -> dict:
    """
    Test authentication bypass: checks common admin/sensitive paths via GET and POST.
    Flags HTTP 200 responses on paths that should require authentication.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected",
                "attack_type": "Authentication Bypass", "vulnerable": False, "findings": []}

    sensitive_paths = [
        "/admin", "/api/admin", "/dashboard", "/config",
        "/.env", "/.git/config", "/api/v1/users", "/api/users",
        "/management", "/actuator/health", "/actuator/env",
        "/graphql", "/api/graphql", "/swagger.json", "/openapi.json",
    ]

    findings = []
    try:
        with httpx.Client(timeout=8, follow_redirects=False) as client:
            for path in sensitive_paths:
                url = target_url.rstrip("/") + path
                try:
                    # Test GET
                    resp = client.get(url, timeout=6)
                    if resp.status_code == 200:
                        findings.append({
                            "path": path,
                            "method": "GET",
                            "http_status": 200,
                            "severity": "HIGH",
                            "indicator": "Sensitive path accessible without authentication",
                            "response_preview": resp.text[:200],
                        })
                    elif resp.status_code == 403:
                        findings.append({
                            "path": path,
                            "method": "GET",
                            "http_status": 403,
                            "severity": "INFO",
                            "indicator": "Endpoint exists but access denied",
                        })

                    # Test POST on API paths
                    if "/api/" in path or "/graphql" in path:
                        resp_post = client.post(url, json={}, timeout=6)
                        if resp_post.status_code == 200:
                            findings.append({
                                "path": path,
                                "method": "POST",
                                "http_status": 200,
                                "severity": "HIGH",
                                "indicator": "API endpoint accessible via POST without authentication",
                            })

                except httpx.RequestError:
                    continue

    except Exception as e:
        return {"status": "error", "error": str(e), "attack_type": "Authentication Bypass",
                "vulnerable": False, "findings": []}

    critical = [f for f in findings if f.get("severity") == "HIGH"]
    outcome = "VULNERABLE" if critical else "NOT_VULNERABLE"
    _log_audit(session_id, "auth_bypass_test", target_url, outcome,
               {"paths_tested": len(sensitive_paths), "exposed_endpoints": len(critical)})

    return {
        "attack_type": "Authentication Bypass",
        "target": target_url,
        "status": outcome,
        "vulnerable": len(critical) > 0,
        "findings": findings,
        "critical_findings": len(critical),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_security_headers(target_url: str, session_id: str = "default") -> dict:
    """
    Audit HTTP response headers for missing security controls.
    Returns verifiable findings from actual HTTP response headers.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected",
                "attack_type": "Security Headers", "vulnerable": False, "findings": []}

    required_headers = {
        "Content-Security-Policy": {"severity": "HIGH", "description": "Prevents XSS via CSP directives"},
        "Strict-Transport-Security": {"severity": "HIGH", "description": "Enforces HTTPS (HSTS)"},
        "X-Frame-Options": {"severity": "MEDIUM", "description": "Prevents clickjacking attacks"},
        "X-Content-Type-Options": {"severity": "MEDIUM", "description": "Prevents MIME type sniffing"},
        "Referrer-Policy": {"severity": "LOW", "description": "Controls referrer information leakage"},
        "Permissions-Policy": {"severity": "LOW", "description": "Controls browser feature permissions"},
    }

    dangerous_headers = {
        "Server": "Exposes server software version",
        "X-Powered-By": "Exposes application framework",
        "X-AspNet-Version": "Exposes ASP.NET version",
    }

    findings = []
    present_headers = {}
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.get(target_url, timeout=8)
            resp_header_keys = {k.lower() for k in resp.headers}
            present_headers = dict(resp.headers)

            # Missing security headers
            for header, meta in required_headers.items():
                if header.lower() not in resp_header_keys:
                    findings.append({
                        "type": "missing_security_header",
                        "header": header,
                        "severity": meta["severity"],
                        "description": meta["description"],
                    })

            # Dangerous information-disclosure headers
            for header, description in dangerous_headers.items():
                if header.lower() in resp_header_keys:
                    findings.append({
                        "type": "information_disclosure_header",
                        "header": header,
                        "value": resp.headers.get(header, ""),
                        "severity": "LOW",
                        "description": description,
                    })

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "Security Headers",
                "vulnerable": False, "findings": []}

    high_findings = [f for f in findings if f.get("severity") == "HIGH"]
    outcome = "MISCONFIGURED" if findings else "SECURE"
    _log_audit(session_id, "security_headers_test", target_url, outcome,
               {"total_issues": len(findings), "high_severity": len(high_findings)})

    return {
        "attack_type": "Security Headers",
        "target": target_url,
        "status": outcome,
        "vulnerable": len(high_findings) > 0,
        "findings": findings,
        "total_issues": len(findings),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Red Agent Class ───────────────────────────────────────────────────────────

class RedAgent:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id=Config.BEDROCK_MODEL_ID,
            region_name=Config.AWS_REGION,
            model_kwargs={
                "temperature": 0.2,  # Low — deterministic attack decisions
                "max_tokens": Config.BEDROCK_MAX_TOKENS,
                "top_p": Config.BEDROCK_TOP_P,
            },
        )

        self.tools = [
            test_sql_injection,
            test_xss,
            test_auth_bypass,
            test_security_headers,
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Red Team AI agent for Sentinel AI.
Your mission: Find real vulnerabilities using the provided tools.

RULES:
1. NEVER test production systems — the tools enforce safety automatically
2. Run ALL 4 tests on every campaign (SQLi, XSS, auth bypass, security headers)
3. Pass the session_id from the campaign context to every tool call
4. Report ONLY findings where tools returned vulnerable=True
5. Include exact HTTP evidence: status codes, payloads, response snippets
6. Prioritize by severity: Authentication Bypass > SQL Injection > XSS > Headers

Each tool makes real HTTP requests. Trust the tool output — do not invent findings."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True,  # Needed for structured findings extraction
        )

    def execute_campaign(self, target_info: dict) -> dict:
        """Execute full offensive campaign against target. Returns LLM output + tool results."""
        session_id = target_info.get("session_id", target_info.get("campaign_id", "default"))
        target_url = target_info.get("url", "http://localhost")
        turn = target_info.get("turn", 1)

        result = self.executor.invoke({
            "input": (
                f"Run a complete security assessment.\n"
                f"Target URL: {target_url}\n"
                f"Session ID: {session_id}\n"
                f"Turn: {turn}\n\n"
                f"Run all 4 tests passing session_id='{session_id}' to each tool.\n"
                f"Report only confirmed vulnerabilities with HTTP evidence."
            )
        })

        # Attach structured tool results for coordinator extraction
        result["tool_results"] = self._extract_tool_results(result)
        result["session_id"] = session_id
        return result

    def _extract_tool_results(self, result: dict) -> List[Dict]:
        """Extract structured tool outputs from intermediate steps."""
        tool_results = []
        for step in result.get("intermediate_steps", []):
            if len(step) == 2:
                action, observation = step
                if isinstance(observation, dict):
                    tool_results.append(observation)
                elif isinstance(observation, str):
                    try:
                        import json
                        parsed = json.loads(observation)
                        if isinstance(parsed, dict):
                            tool_results.append(parsed)
                    except Exception:
                        pass
        return tool_results
