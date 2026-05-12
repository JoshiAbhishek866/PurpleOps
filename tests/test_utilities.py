"""
Tests for PII redaction and scope enforcement utilities.
"""
import pytest
import os


class TestPIIRedactor:
    """Test PII redaction utility."""

    def test_redacts_email(self):
        from src.utils.pii_redactor import redact_string
        assert "[REDACTED_EMAIL]" in redact_string("Contact admin@example.com for access")

    def test_redacts_ssn(self):
        from src.utils.pii_redactor import redact_string
        assert "[REDACTED_SSN]" in redact_string("SSN: 123-45-6789")

    def test_redacts_credit_card(self):
        from src.utils.pii_redactor import redact_string
        assert "[REDACTED_CC]" in redact_string("Card: 4111-1111-1111-1111")

    def test_redacts_aws_key(self):
        from src.utils.pii_redactor import redact_string
        assert "[REDACTED_AWS_KEY]" in redact_string("Key: AKIAIOSFODNN7EXAMPLE")

    def test_recursive_dict_redaction(self):
        from src.utils.pii_redactor import redact_scan_results
        data = {
            "findings": {
                "emails_found": ["admin@corp.com", "user@test.org"],
                "data": "SSN 123-45-6789 found"
            }
        }
        result = redact_scan_results(data)
        assert "[REDACTED_EMAIL]" in str(result)
        assert "[REDACTED_SSN]" in str(result)
        assert "123-45-6789" not in str(result)

    def test_safe_with_no_pii(self):
        from src.utils.pii_redactor import redact_string
        text = "No sensitive data here, just normal text"
        assert redact_string(text) == text


class TestScopeEnforcer:
    """Test target scope enforcement."""

    def test_kill_switch_blocks_all(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        os.environ["AGENT_KILL_SWITCH"] = "true"
        enforcer = ScopeEnforcer(allowed_targets=["example.com"])
        assert enforcer.is_allowed("example.com") is False
        del os.environ["AGENT_KILL_SWITCH"]

    def test_empty_allowlist_allows_all(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        enforcer = ScopeEnforcer(allowed_targets=[])
        assert enforcer.is_allowed("anything.com") is True

    def test_exact_domain_match(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        enforcer = ScopeEnforcer(allowed_targets=["test.example.com"])
        assert enforcer.is_allowed("test.example.com") is True
        assert enforcer.is_allowed("other.example.com") is False

    def test_wildcard_domain_match(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        enforcer = ScopeEnforcer(allowed_targets=["*.example.com"])
        assert enforcer.is_allowed("sub.example.com") is True
        assert enforcer.is_allowed("deep.sub.example.com") is True
        assert enforcer.is_allowed("evil.com") is False

    def test_cidr_match(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        enforcer = ScopeEnforcer(allowed_targets=["10.0.0.0/8"])
        assert enforcer.is_allowed("10.1.2.3") is True
        assert enforcer.is_allowed("192.168.1.1") is False

    def test_url_with_protocol(self):
        from src.utils.scope_enforcer import ScopeEnforcer
        enforcer = ScopeEnforcer(allowed_targets=["*.example.com"])
        assert enforcer.is_allowed("https://api.example.com/v1/users") is True
        assert enforcer.is_allowed("http://evil.com/attack") is False
