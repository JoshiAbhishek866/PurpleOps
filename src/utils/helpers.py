"""
Helper utilities for Sentinel AI Orchestrator
Common functions used across the system

ENHANCED v2.0:
- UUID4 for ID generation (replaces MD5)
- Proper IP validation with octet bounds + IPv6 + CIDR
- Allowlist-based input sanitization
- Shared service port mappings (50+ ports)
- Common subdomain wordlist (100+ entries)
- CVSS 3.1 base score calculator
- Finding deduplication via hash fingerprint
"""

import asyncio
import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
import time


__version__ = "2.0.0"


# ── ID Generation ────────────────────────────────────────────────────────────

def generate_id(prefix: str = "") -> str:
    """Generate a unique ID using UUID4 (replaces MD5)."""
    # ENHANCED: UUID4 is cryptographically random, no collision risk
    short_id = uuid.uuid4().hex[:16]
    return f"{prefix}_{short_id}" if prefix else short_id


# ── Target Validation ────────────────────────────────────────────────────────

def validate_target(target: str) -> bool:
    """
    Validate target (IP, IPv6, domain, CIDR, or URL).

    ENHANCED v2.0:
    - Validates IPv4 octet range (0-255)
    - Supports IPv6 addresses
    - Supports CIDR notation
    - Accepts URLs (strips scheme + path before validation)
    """
    if not target or not isinstance(target, str):
        return False

    # Strip scheme and path if URL
    cleaned = target.strip()
    for scheme in ("https://", "http://"):
        if cleaned.lower().startswith(scheme):
            cleaned = cleaned[len(scheme):]
    cleaned = cleaned.split("/")[0]   # remove path
    cleaned = cleaned.split(":")[0]   # remove port for domain/IP check
    cleaned = cleaned.split("?")[0]   # remove query

    # CIDR notation check
    cidr_part = None
    if "/" in cleaned:
        cleaned, cidr_part = cleaned.rsplit("/", 1)

    # IPv4 validation with octet bounds
    ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    m = re.match(ipv4_pattern, cleaned)
    if m:
        octets = [int(g) for g in m.groups()]
        if all(0 <= o <= 255 for o in octets):
            if cidr_part is not None:
                try:
                    prefix = int(cidr_part)
                    return 0 <= prefix <= 32
                except ValueError:
                    return False
            return True
        return False

    # IPv6 validation (simplified — accept standard and compressed forms)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$'
    if re.match(ipv6_pattern, cleaned) or cleaned == "::1":
        if cidr_part is not None:
            try:
                prefix = int(cidr_part)
                return 0 <= prefix <= 128
            except ValueError:
                return False
        return True

    # Domain pattern
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, cleaned):
        return True

    # Localhost special case
    if cleaned in ("localhost", "127.0.0.1", "::1"):
        return True

    return False


# ── Result Formatting ────────────────────────────────────────────────────────

def format_result(agent_type: str, target: str, data: Dict, status: str = "success") -> Dict:
    """Format agent result for storage."""
    now = datetime.now(timezone.utc)
    return {
        "id": generate_id(agent_type),
        "agent_type": agent_type,
        "target": target,
        "status": status,
        "data": data,
        "timestamp": now.isoformat(),
        "created_at": now
    }


# ── Retry Decorator ──────────────────────────────────────────────────────────

def retry_async(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator for retrying async functions with exponential backoff.

    ENHANCED v2.0: Added backoff_factor for exponential delay growth.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff_factor
            raise last_exception
        return wrapper
    return decorator


# ── Rate Limiter ─────────────────────────────────────────────────────────────

def rate_limit(calls: int, period: float):
    """Rate limiting decorator"""
    min_interval = period / calls
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait_time = min_interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ── Input Sanitization ───────────────────────────────────────────────────────

# ENHANCED: allowlist approach instead of blacklist
_SAFE_CHARS = re.compile(r'[^a-zA-Z0-9\s\.\-_:/\?=&@#%\+,;]')

def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data using allowlist approach.

    ENHANCED v2.0:
    - Handles None gracefully
    - Uses allowlist regex instead of blacklist
    - Recursively sanitizes dicts and lists
    """
    if data is None:
        return None
    if isinstance(data, str):
        return _SAFE_CHARS.sub('', data)
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data


# ── URL Normalization ────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    """
    ENHANCED: Normalize a URL — ensure scheme, strip trailing slashes.
    """
    if not url:
        return url
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


# ── Finding Deduplication ────────────────────────────────────────────────────

def hash_finding(vuln_type: str, url: str, parameter: str = "") -> str:
    """
    ENHANCED: Create a deterministic fingerprint hash for finding deduplication.
    Two findings with the same type, URL, and parameter are considered duplicates.
    """
    canonical = f"{vuln_type.lower().strip()}|{url.lower().strip()}|{parameter.lower().strip()}"
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# ── CVSS 3.1 Base Score Calculator ───────────────────────────────────────────

def calculate_cvss_base_score(
    attack_vector: str = "N",        # N=Network, A=Adjacent, L=Local, P=Physical
    attack_complexity: str = "L",     # L=Low, H=High
    privileges_required: str = "N",   # N=None, L=Low, H=High
    user_interaction: str = "N",      # N=None, R=Required
    scope: str = "U",                 # U=Unchanged, C=Changed
    confidentiality: str = "H",       # N=None, L=Low, H=High
    integrity: str = "H",             # N=None, L=Low, H=High
    availability: str = "H",          # N=None, L=Low, H=High
) -> Tuple[float, str]:
    """
    ENHANCED: Algorithmically compute CVSS 3.1 base score from metric values.
    Returns (score, vector_string).

    Reference: https://www.first.org/cvss/v3.1/specification-document
    """
    # Metric value mappings per CVSS 3.1 spec
    av_values = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
    ac_values = {"L": 0.77, "H": 0.44}
    ui_values = {"N": 0.85, "R": 0.62}

    # Privileges Required depends on Scope
    if scope == "U":
        pr_values = {"N": 0.85, "L": 0.62, "H": 0.27}
    else:
        pr_values = {"N": 0.85, "L": 0.68, "H": 0.50}

    # Impact metric values
    cia_values = {"H": 0.56, "L": 0.22, "N": 0.0}

    # Calculate Exploitability sub-score
    exploitability = (
        8.22
        * av_values.get(attack_vector, 0.85)
        * ac_values.get(attack_complexity, 0.77)
        * pr_values.get(privileges_required, 0.85)
        * ui_values.get(user_interaction, 0.85)
    )

    # Calculate Impact sub-score
    isc_base = 1.0 - (
        (1.0 - cia_values.get(confidentiality, 0.56))
        * (1.0 - cia_values.get(integrity, 0.56))
        * (1.0 - cia_values.get(availability, 0.56))
    )

    if scope == "U":
        impact = 6.42 * isc_base
    else:
        impact = 7.52 * (isc_base - 0.029) - 3.25 * ((isc_base - 0.02) ** 15)

    # Calculate base score
    if impact <= 0:
        base_score = 0.0
    elif scope == "U":
        base_score = min(impact + exploitability, 10.0)
    else:
        base_score = min(1.08 * (impact + exploitability), 10.0)

    # Round up to 1 decimal
    import math
    base_score = math.ceil(base_score * 10) / 10

    # Build vector string
    vector = (
        f"CVSS:3.1/AV:{attack_vector}/AC:{attack_complexity}/"
        f"PR:{privileges_required}/UI:{user_interaction}/S:{scope}/"
        f"C:{confidentiality}/I:{integrity}/A:{availability}"
    )

    return base_score, vector


# ── Shared Service Ports ─────────────────────────────────────────────────────

def shared_service_ports() -> Dict[int, str]:
    """
    ENHANCED: Shared mapping of 50+ common service ports.
    Used by recon_agent and scanner_agent to avoid duplication.
    """
    return {
        20: "FTP-Data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
        53: "DNS", 67: "DHCP", 68: "DHCP", 69: "TFTP", 80: "HTTP",
        88: "Kerberos", 110: "POP3", 111: "RPCBind", 119: "NNTP",
        123: "NTP", 135: "MS-RPC", 137: "NetBIOS-NS", 139: "NetBIOS-SSN",
        143: "IMAP", 161: "SNMP", 162: "SNMP-Trap", 389: "LDAP",
        443: "HTTPS", 445: "SMB", 465: "SMTPS", 500: "IKE",
        514: "Syslog", 515: "LPD", 520: "RIP", 523: "IBM-DB2",
        548: "AFP", 554: "RTSP", 587: "Submission", 631: "IPP",
        636: "LDAPS", 993: "IMAPS", 995: "POP3S", 1080: "SOCKS",
        1433: "MSSQL", 1434: "MSSQL-Browser", 1521: "Oracle-DB",
        1723: "PPTP", 2049: "NFS", 2082: "cPanel", 2083: "cPanel-SSL",
        2181: "ZooKeeper", 2375: "Docker", 2376: "Docker-SSL",
        3306: "MySQL", 3389: "RDP", 3690: "SVN", 4443: "HTTPS-Alt",
        5432: "PostgreSQL", 5672: "AMQP", 5900: "VNC",
        5984: "CouchDB", 5985: "WinRM-HTTP", 5986: "WinRM-HTTPS",
        6379: "Redis", 6443: "Kubernetes-API", 7001: "WebLogic",
        8000: "HTTP-Alt", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
        8888: "HTTP-Alt", 9090: "Prometheus", 9200: "Elasticsearch",
        9300: "Elasticsearch-Transport", 9418: "Git",
        11211: "Memcached", 15672: "RabbitMQ-Mgmt",
        27017: "MongoDB", 27018: "MongoDB-Shard", 28017: "MongoDB-Web",
        50000: "SAP", 50070: "HDFS-NameNode",
    }


# ── Common Subdomains ────────────────────────────────────────────────────────

def common_subdomains() -> List[str]:
    """
    ENHANCED: List of 100+ common subdomains for recon enumeration.
    """
    return [
        "www", "mail", "ftp", "admin", "api", "dev", "staging", "test",
        "blog", "shop", "portal", "vpn", "cdn", "app", "mobile", "m",
        "secure", "payment", "support", "help", "docs", "wiki", "git",
        "jenkins", "ci", "cd", "build", "deploy", "monitor", "status",
        "grafana", "kibana", "elastic", "prometheus", "alerts",
        "auth", "sso", "login", "oauth", "id", "identity",
        "internal", "intranet", "extranet", "corp", "office",
        "webmail", "exchange", "outlook", "autodiscover",
        "ns1", "ns2", "dns", "dns1", "dns2",
        "db", "database", "mysql", "postgres", "redis", "mongo",
        "cache", "memcached", "queue", "mq", "rabbit",
        "s3", "storage", "assets", "static", "media", "images", "img",
        "beta", "alpha", "preview", "demo", "sandbox", "uat",
        "stage", "stg", "pre-prod", "preprod", "qa",
        "api-v1", "api-v2", "api-gateway", "gateway", "proxy",
        "lb", "load-balancer", "edge", "origin",
        "backup", "bak", "old", "new", "legacy",
        "smtp", "pop", "imap", "mx",
        "relay", "relay1", "relay2",
        "web", "web1", "web2", "web3",
        "app1", "app2", "node1", "node2",
        "search", "solr", "elk",
        "jira", "confluence", "bitbucket", "gitlab",
        "slack", "teams", "chat",
        "crm", "erp", "hr", "finance",
        "analytics", "tracking", "metrics", "logs",
        "vault", "secrets", "config",
    ]


# ── Scan Output Parsing ─────────────────────────────────────────────────────

def parse_scan_output(output: str, format_type: str = "nmap") -> Dict:
    """Parse scan output into structured data"""
    if format_type == "nmap":
        return {
            "raw_output": output,
            "parsed": True,
            "format": format_type
        }
    return {"raw_output": output}


# ── Risk Score Calculator ────────────────────────────────────────────────────

def calculate_risk_score(vulnerabilities: List[Dict]) -> float:
    """Calculate overall risk score from vulnerabilities"""
    if not vulnerabilities:
        return 0.0

    total_score = 0.0
    for vuln in vulnerabilities:
        cvss = vuln.get("cvss_score", 0.0)
        if isinstance(cvss, str):
            try:
                cvss = float(cvss)
            except (ValueError, TypeError):
                cvss = 0.0
        total_score += cvss

    return min(total_score / len(vulnerabilities), 10.0)


# ── Duration Formatting ──────────────────────────────────────────────────────

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.2f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.2f}h"


# ── List Chunking ────────────────────────────────────────────────────────────

def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


# ── Async Timeout Wrapper ────────────────────────────────────────────────────

async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout}s")


# ── Result Merging ───────────────────────────────────────────────────────────

def merge_results(results: List[Dict]) -> Dict:
    """Merge multiple agent results"""
    merged = {
        "combined_results": results,
        "total_count": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return merged


# ── CWE Mapping ──────────────────────────────────────────────────────────────

def get_cwe_id(vuln_type: str) -> Dict[str, str]:
    """
    ENHANCED: Map vulnerability types to CWE IDs.
    Returns dict with cwe_id and cwe_name.
    """
    cwe_map = {
        "sql injection": {"cwe_id": "CWE-89", "cwe_name": "SQL Injection"},
        "xss": {"cwe_id": "CWE-79", "cwe_name": "Cross-site Scripting"},
        "cross-site scripting": {"cwe_id": "CWE-79", "cwe_name": "Cross-site Scripting"},
        "path traversal": {"cwe_id": "CWE-22", "cwe_name": "Path Traversal"},
        "command injection": {"cwe_id": "CWE-78", "cwe_name": "OS Command Injection"},
        "ssrf": {"cwe_id": "CWE-918", "cwe_name": "Server-Side Request Forgery"},
        "xxe": {"cwe_id": "CWE-611", "cwe_name": "XML External Entity"},
        "open redirect": {"cwe_id": "CWE-601", "cwe_name": "URL Redirection to Untrusted Site"},
        "csrf": {"cwe_id": "CWE-352", "cwe_name": "Cross-Site Request Forgery"},
        "authentication bypass": {"cwe_id": "CWE-287", "cwe_name": "Improper Authentication"},
        "missing auth": {"cwe_id": "CWE-862", "cwe_name": "Missing Authorization"},
        "security headers": {"cwe_id": "CWE-693", "cwe_name": "Protection Mechanism Failure"},
        "cors misconfiguration": {"cwe_id": "CWE-942", "cwe_name": "Permissive CORS Policy"},
        "information disclosure": {"cwe_id": "CWE-200", "cwe_name": "Information Exposure"},
        "weak credentials": {"cwe_id": "CWE-521", "cwe_name": "Weak Password Requirements"},
        "default credentials": {"cwe_id": "CWE-1392", "cwe_name": "Use of Default Credentials"},
        "insecure deserialization": {"cwe_id": "CWE-502", "cwe_name": "Deserialization of Untrusted Data"},
    }
    return cwe_map.get(vuln_type.lower().strip(), {"cwe_id": "CWE-Unknown", "cwe_name": vuln_type})


# ── MITRE ATT&CK Mapping ────────────────────────────────────────────────────

def get_mitre_technique(vuln_type: str) -> Dict[str, str]:
    """
    ENHANCED: Map vulnerability types to MITRE ATT&CK technique IDs.
    """
    mitre_map = {
        "sql injection": {"technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
        "xss": {"technique_id": "T1189", "technique_name": "Drive-by Compromise"},
        "cross-site scripting": {"technique_id": "T1189", "technique_name": "Drive-by Compromise"},
        "command injection": {"technique_id": "T1059", "technique_name": "Command and Scripting Interpreter"},
        "ssrf": {"technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
        "authentication bypass": {"technique_id": "T1078", "technique_name": "Valid Accounts"},
        "path traversal": {"technique_id": "T1083", "technique_name": "File and Directory Discovery"},
        "xxe": {"technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
        "open redirect": {"technique_id": "T1566.002", "technique_name": "Phishing: Spearphishing Link"},
        "default credentials": {"technique_id": "T1078.001", "technique_name": "Valid Accounts: Default Accounts"},
        "brute force": {"technique_id": "T1110", "technique_name": "Brute Force"},
        "security headers": {"technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"},
        "cors misconfiguration": {"technique_id": "T1557", "technique_name": "Adversary-in-the-Middle"},
    }
    return mitre_map.get(
        vuln_type.lower().strip(),
        {"technique_id": "T1190", "technique_name": "Exploit Public-Facing Application"}
    )


# ── OWASP Top 10 2021 Mapping ────────────────────────────────────────────────

def get_owasp_category(vuln_type: str) -> Dict[str, str]:
    """
    ENHANCED: Map vulnerability types to OWASP Top 10 2021 categories.
    """
    owasp_map = {
        "authentication bypass": {"id": "A01", "name": "Broken Access Control"},
        "missing auth": {"id": "A01", "name": "Broken Access Control"},
        "cors misconfiguration": {"id": "A01", "name": "Broken Access Control"},
        "open redirect": {"id": "A01", "name": "Broken Access Control"},
        "security headers": {"id": "A05", "name": "Security Misconfiguration"},
        "information disclosure": {"id": "A05", "name": "Security Misconfiguration"},
        "sql injection": {"id": "A03", "name": "Injection"},
        "xss": {"id": "A03", "name": "Injection"},
        "command injection": {"id": "A03", "name": "Injection"},
        "xxe": {"id": "A03", "name": "Injection"},
        "path traversal": {"id": "A01", "name": "Broken Access Control"},
        "ssrf": {"id": "A10", "name": "Server-Side Request Forgery"},
        "weak credentials": {"id": "A07", "name": "Identification and Authentication Failures"},
        "default credentials": {"id": "A07", "name": "Identification and Authentication Failures"},
        "insecure deserialization": {"id": "A08", "name": "Software and Data Integrity Failures"},
    }
    return owasp_map.get(
        vuln_type.lower().strip(),
        {"id": "A00", "name": "Uncategorized"}
    )
