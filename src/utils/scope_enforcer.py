"""
Target Scope Enforcer for PurpleOps

Validates that scan targets are within the allowed scope before
any offensive agent executes. Supports domain wildcards, IP CIDRs,
and a global kill switch.

Cost-optimized: no external dependencies, pure Python.
"""

import os
import re
import ipaddress
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ScopeEnforcer:
    """
    Validates targets against an allowlist before scanning.

    Features:
    - Domain matching with wildcards (*.example.com)
    - IP range matching via CIDR (10.0.0.0/8)
    - Explicit URL matching
    - Global kill switch (AGENT_KILL_SWITCH env var)
    """

    def __init__(self, allowed_targets: Optional[List[str]] = None):
        self.allowed_domains: List[str] = []
        self.allowed_cidrs: List[ipaddress.IPv4Network] = []
        self.allowed_urls: List[str] = []

        if allowed_targets:
            self._parse_allowlist(allowed_targets)

    def _parse_allowlist(self, targets: List[str]):
        """Categorize allowlist entries into domains, CIDRs, and URLs."""
        for entry in targets:
            entry = entry.strip()
            if not entry:
                continue

            # CIDR notation (e.g., 10.0.0.0/8, 192.168.1.0/24)
            try:
                network = ipaddress.ip_network(entry, strict=False)
                self.allowed_cidrs.append(network)
                continue
            except ValueError:
                pass

            # Wildcard domain (e.g., *.example.com)
            if entry.startswith("*."):
                self.allowed_domains.append(entry)
                continue

            # Plain domain or URL
            self.allowed_urls.append(entry.lower())

    @staticmethod
    def is_kill_switch_active() -> bool:
        """Check if the global kill switch is engaged."""
        return os.getenv("AGENT_KILL_SWITCH", "").lower() in ("1", "true", "yes")

    def is_allowed(self, target: str) -> bool:
        """
        Check if a target is within the allowed scope.

        Args:
            target: URL, domain, or IP to validate.

        Returns:
            True if the target is allowed, False otherwise.
        """
        # Kill switch overrides everything
        if self.is_kill_switch_active():
            logger.warning("🛑 Kill switch is ACTIVE — all scans blocked")
            return False

        # If no allowlist configured, allow all (backward compat)
        if not self.allowed_domains and not self.allowed_cidrs and not self.allowed_urls:
            return True

        target_lower = target.lower().strip()

        # Extract hostname from URL
        hostname = self._extract_hostname(target_lower)

        # Check exact URL match
        if target_lower in self.allowed_urls:
            return True

        # Check hostname match
        if hostname and hostname in self.allowed_urls:
            return True

        # Check wildcard domain match (*.example.com)
        if hostname:
            for pattern in self.allowed_domains:
                suffix = pattern[1:]  # Remove the *
                if hostname.endswith(suffix) or hostname == suffix[1:]:
                    return True

        # Check IP CIDR match
        ip = self._extract_ip(hostname or target_lower)
        if ip:
            for cidr in self.allowed_cidrs:
                if ip in cidr:
                    return True

        logger.warning(f"⛔ Target '{target}' is NOT in allowed scope")
        return False

    @staticmethod
    def _extract_hostname(url: str) -> Optional[str]:
        """Extract hostname from a URL string."""
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        # Remove path, port, query
        hostname = url.split('/')[0].split(':')[0].split('?')[0]
        return hostname if hostname else None

    @staticmethod
    def _extract_ip(text: str) -> Optional[ipaddress.IPv4Address]:
        """Try to parse text as an IPv4 address."""
        try:
            return ipaddress.ip_address(text)
        except ValueError:
            return None
