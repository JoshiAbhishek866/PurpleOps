"""
Helper utilities for PurpleOps Orchestrator
Common functions used across the system
"""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from functools import wraps
import time


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID"""
    timestamp = datetime.utcnow().isoformat()
    hash_input = f"{prefix}{timestamp}".encode()
    return f"{prefix}_{hashlib.md5(hash_input).hexdigest()[:12]}"


def validate_target(target: str) -> bool:
    """Validate target (IP or domain)"""
    import re
    
    # IP address pattern
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # Domain pattern
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    
    return bool(re.match(ip_pattern, target) or re.match(domain_pattern, target))


def format_result(agent_type: str, target: str, data: Dict, status: str = "success") -> Dict:
    """Format agent result for storage"""
    return {
        "id": generate_id(agent_type),
        "agent_type": agent_type,
        "target": target,
        "status": status,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow()
    }


def retry_async(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_exception
        return wrapper
    return decorator


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


def sanitize_input(data: Any) -> Any:
    """Sanitize input data"""
    if isinstance(data, str):
        # Remove potentially dangerous characters
        return data.replace(";", "").replace("&", "").replace("|", "")
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data


def parse_scan_output(output: str, format_type: str = "nmap") -> Dict:
    """Parse scan output into structured data"""
    if format_type == "nmap":
        return {
            "raw_output": output,
            "parsed": True,
            "format": format_type
        }
    return {"raw_output": output}


def calculate_risk_score(vulnerabilities: List[Dict]) -> float:
    """Calculate overall risk score from vulnerabilities"""
    if not vulnerabilities:
        return 0.0
    
    total_score = 0.0
    for vuln in vulnerabilities:
        cvss = vuln.get("cvss_score", 0.0)
        total_score += cvss
    
    return min(total_score / len(vulnerabilities), 10.0)


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


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


async def run_with_timeout(coro, timeout: float):
    """Run coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {timeout}s")


def merge_results(results: List[Dict]) -> Dict:
    """Merge multiple agent results"""
    merged = {
        "combined_results": results,
        "total_count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }
    return merged
