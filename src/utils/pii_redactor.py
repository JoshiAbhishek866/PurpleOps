"""
PII Redaction Utility for Sentinel AI

Scans scan results for sensitive data patterns and redacts them
before storage or display. Cost-optimized: regex-based, no ML models needed.
"""

import re
from typing import Any, Dict, Union


# Compiled patterns for performance
_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "credit_card": re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
    "phone_us": re.compile(r'\b(?:\+1[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
    "aws_key": re.compile(r'(?:AKIA|ASIA)[A-Z0-9]{16}'),
    "jwt_token": re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'),
    "ipv4_private": re.compile(r'\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b'),
}

_REDACTION_LABELS = {
    "email": "[REDACTED_EMAIL]",
    "ssn": "[REDACTED_SSN]",
    "credit_card": "[REDACTED_CC]",
    "phone_us": "[REDACTED_PHONE]",
    "aws_key": "[REDACTED_AWS_KEY]",
    "jwt_token": "[REDACTED_TOKEN]",
    "ipv4_private": "[REDACTED_IP]",
}


def redact_string(text: str) -> str:
    """Redact all PII patterns from a string."""
    for name, pattern in _PATTERNS.items():
        text = pattern.sub(_REDACTION_LABELS[name], text)
    return text


def redact_scan_results(data: Any) -> Any:
    """
    Recursively traverse a dict/list and redact PII in all string values.

    Works on nested dicts, lists, and primitives.
    """
    if isinstance(data, str):
        return redact_string(data)
    elif isinstance(data, dict):
        return {k: redact_scan_results(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_scan_results(item) for item in data]
    else:
        return data
