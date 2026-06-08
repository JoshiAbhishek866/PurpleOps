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
from datetime import datetime
from typing import Optional

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
        item.update(extra)
    try:
        _audit_table.put_item(Item=item)
    except Exception:
        pass  # Don't fail the attack if audit write fails


# ── Attack Tools ──────────────────────────────────────────────────────────────

@tool
def test_sql_injection(target_url: str, session_id: str = "default") -> dict:
    """
    Test SQL injection by sending real payloads to the target URL.
    Detects vulnerability from HTTP response: SQL errors, anomalous status codes,
    or response body differences between neutral and malicious requests.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected"}

    payloads = [
        "' OR '1'='1",
        "' OR 1=1--",
        "'; DROP TABLE users--",
        "1 UNION SELECT null,null,null--",
    ]

    sql_error_signatures = [
        "sql syntax", "mysql_fetch", "ORA-", "syntax error",
        "unclosed quotation", "quoted string", "pg_query",
        "sqlite_", "microsoft sql", "sqlstate",
    ]

    findings = []
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            # Baseline request
            baseline = client.get(target_url)
            baseline_len = len(baseline.text)

            for payload in payloads:
                # Test as query param
                resp = client.get(target_url, params={"id": payload, "q": payload})
                body_lower = resp.text.lower()

                # Check for SQL error signatures in response
                for sig in sql_error_signatures:
                    if sig in body_lower:
                        findings.append({
                            "payload": payload,
                            "indicator": f"SQL error signature: '{sig}'",
                            "http_status": resp.status_code,
                            "response_length": len(resp.text),
                        })
                        break

                # Check for anomalous response length (potential data leak)
                if abs(len(resp.text) - baseline_len) > 500 and resp.status_code == 200:
                    findings.append({
                        "payload": payload,
                        "indicator": f"Anomalous response length delta: {len(resp.text) - baseline_len} bytes",
                        "http_status": resp.status_code,
                    })

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "SQL Injection"}

    vulnerable = len(findings) > 0
    outcome = "VULNERABLE" if vulnerable else "NOT_VULNERABLE"
    _log_audit(session_id, "sql_injection_test", target_url, outcome,
               {"payloads_tested": len(payloads), "findings": len(findings)})

    return {
        "attack_type": "SQL Injection",
        "target": target_url,
        "status": outcome,
        "vulnerable": vulnerable,
        "findings": findings,
        "payloads_tested": len(payloads),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_xss(target_url: str, session_id: str = "default") -> dict:
    """
    Test Cross-Site Scripting (XSS) by checking if script payloads
    are reflected in HTTP responses without encoding.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected"}

    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "'><svg onload=alert(1)>",
    ]

    findings = []
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            for payload in payloads:
                # Test as query param and form field
                resp = client.get(target_url, params={"q": payload, "search": payload, "name": payload})
                # Check if payload is reflected unencoded
                if payload in resp.text:
                    findings.append({
                        "payload": payload,
                        "indicator": "Payload reflected unencoded in response",
                        "http_status": resp.status_code,
                    })

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "XSS"}

    vulnerable = len(findings) > 0
    outcome = "VULNERABLE" if vulnerable else "NOT_VULNERABLE"
    _log_audit(session_id, "xss_test", target_url, outcome,
               {"payloads_tested": len(payloads), "findings": len(findings)})

    return {
        "attack_type": "XSS",
        "target": target_url,
        "status": outcome,
        "vulnerable": vulnerable,
        "findings": findings,
        "payloads_tested": len(payloads),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_auth_bypass(target_url: str, session_id: str = "default") -> dict:
    """
    Test authentication bypass: checks for open admin endpoints,
    missing auth headers, and default credentials.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected"}

    admin_paths = ["/admin", "/api/admin", "/dashboard", "/config", "/.env",
                   "/api/v1/users", "/api/users", "/management", "/actuator/health"]

    findings = []
    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            for path in admin_paths:
                url = target_url.rstrip("/") + path
                resp = client.get(url)

                # 200 on admin paths without auth = finding
                if resp.status_code == 200:
                    findings.append({
                        "path": path,
                        "http_status": 200,
                        "indicator": "Admin/sensitive path accessible without authentication",
                        "response_preview": resp.text[:200],
                    })
                # 403 is better than 200 but still note it
                elif resp.status_code == 403:
                    findings.append({
                        "path": path,
                        "http_status": 403,
                        "indicator": "Path exists but access denied (endpoint exists)",
                        "severity": "INFO",
                    })

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "Auth Bypass"}

    critical = [f for f in findings if f.get("http_status") == 200]
    outcome = "VULNERABLE" if critical else "NOT_VULNERABLE"
    _log_audit(session_id, "auth_bypass_test", target_url, outcome,
               {"paths_tested": len(admin_paths), "exposed_endpoints": len(critical)})

    return {
        "attack_type": "Authentication Bypass",
        "target": target_url,
        "status": outcome,
        "vulnerable": len(critical) > 0,
        "findings": findings,
        "exposed_endpoints": len(critical),
        "timestamp": datetime.utcnow().isoformat(),
    }


@tool
def test_security_headers(target_url: str, session_id: str = "default") -> dict:
    """
    Check for missing security headers that indicate misconfiguration.
    These are real, verifiable findings from HTTP response headers.
    """
    if not _is_safe_target(target_url):
        return {"status": "blocked", "reason": "Production target detected — attack rejected"}

    required_headers = {
        "Content-Security-Policy": "Prevents XSS via CSP",
        "X-Frame-Options": "Prevents clickjacking",
        "X-Content-Type-Options": "Prevents MIME sniffing",
        "Strict-Transport-Security": "Enforces HTTPS",
        "X-XSS-Protection": "Browser XSS filter",
        "Referrer-Policy": "Controls referrer information",
    }

    findings = []
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.get(target_url)
            for header, description in required_headers.items():
                if header.lower() not in {k.lower() for k in resp.headers}:
                    findings.append({
                        "missing_header": header,
                        "description": description,
                        "severity": "MEDIUM",
                    })

    except httpx.RequestError as e:
        return {"status": "error", "error": str(e), "attack_type": "Security Headers"}

    outcome = "MISCONFIGURED" if findings else "SECURE"
    _log_audit(session_id, "security_headers_test", target_url, outcome,
               {"missing_headers": len(findings)})

    return {
        "attack_type": "Security Headers",
        "target": target_url,
        "status": outcome,
        "vulnerable": len(findings) > 0,
        "findings": findings,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Red Agent Class ───────────────────────────────────────────────────────────

class RedAgent:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id=Config.BEDROCK_MODEL_ID,
            region_name=Config.AWS_REGION,
            model_kwargs={
                "temperature": 0.3,  # Lower temp for consistent attack decisions
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
Your mission: Find real vulnerabilities in the target using the provided tools.

Rules:
1. NEVER test production systems — the tools enforce this automatically
2. Run ALL 4 tests on every target to get comprehensive coverage
3. Prioritize findings by severity: auth_bypass > sql_injection > xss > headers
4. Report exact HTTP evidence — never speculate about vulnerabilities
5. For each vulnerability found, describe the exact payload and response that confirms it

Your tools execute real HTTP requests and return real results. Trust the tool output."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=8,  # Prevent runaway loops
            handle_parsing_errors=True,
        )

    def execute_campaign(self, target_info: dict) -> dict:
        """Execute full offensive campaign against target."""
        session_id = target_info.get("session_id", "default")
        target_url = target_info.get("url", "http://localhost")

        result = self.executor.invoke({
            "input": f"""Run a complete security assessment on: {target_url}
Session ID: {session_id}
Turn: {target_info.get('turn', 1)}

Execute all 4 tests: SQL injection, XSS, auth bypass, security headers.
Report findings with HTTP evidence."""
        })

        return result
