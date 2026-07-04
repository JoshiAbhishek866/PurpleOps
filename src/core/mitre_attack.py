"""
MITRE ATT&CK Mapping for PurpleOps

Maps agent actions to MITRE ATT&CK technique IDs for enterprise
credibility and standardized threat classification.

Reference: https://attack.mitre.org/techniques/enterprise/
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


# ==================== ATT&CK Technique Database ====================
# Curated subset relevant to PurpleOps's agent capabilities.
# Full MITRE ATT&CK has 200+ techniques — we map only what our agents do.

ATTACK_TECHNIQUES: Dict[str, Dict] = {
    # ── Reconnaissance (TA0043) ──
    "T1595": {
        "name": "Active Scanning",
        "tactic": "Reconnaissance",
        "tactic_id": "TA0043",
        "description": "Adversaries scan victim infrastructure to gather information.",
        "subtechniques": {
            "T1595.001": "Scanning IP Blocks",
            "T1595.002": "Vulnerability Scanning",
            "T1595.003": "Wordlist Scanning",
        }
    },
    "T1592": {
        "name": "Gather Victim Host Information",
        "tactic": "Reconnaissance",
        "tactic_id": "TA0043",
        "description": "Gather information about target hosts (OS, software, patches).",
        "subtechniques": {
            "T1592.001": "Hardware",
            "T1592.002": "Software",
            "T1592.004": "Client Configurations",
        }
    },
    "T1589": {
        "name": "Gather Victim Identity Information",
        "tactic": "Reconnaissance",
        "tactic_id": "TA0043",
        "description": "Gather target credentials, employee names, email addresses.",
        "subtechniques": {
            "T1589.001": "Credentials",
            "T1589.002": "Email Addresses",
        }
    },

    # ── Initial Access (TA0001) ──
    "T1190": {
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "tactic_id": "TA0001",
        "description": "Exploit vulnerabilities in internet-facing applications.",
        "subtechniques": {}
    },
    "T1078": {
        "name": "Valid Accounts",
        "tactic": "Initial Access",
        "tactic_id": "TA0001",
        "description": "Use stolen or weak credentials to gain access.",
        "subtechniques": {
            "T1078.001": "Default Accounts",
            "T1078.003": "Local Accounts",
            "T1078.004": "Cloud Accounts",
        }
    },

    # ── Execution (TA0002) ──
    "T1059": {
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "tactic_id": "TA0002",
        "description": "Execute commands and scripts on target systems.",
        "subtechniques": {
            "T1059.001": "PowerShell",
            "T1059.004": "Unix Shell",
            "T1059.007": "JavaScript",
        }
    },

    # ── Privilege Escalation (TA0004) ──
    "T1548": {
        "name": "Abuse Elevation Control Mechanism",
        "tactic": "Privilege Escalation",
        "tactic_id": "TA0004",
        "description": "Circumvent mechanisms designed to control elevated privileges.",
        "subtechniques": {
            "T1548.002": "Bypass User Account Control",
            "T1548.004": "Elevated Execution with Prompt",
        }
    },
    "T1068": {
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
        "tactic_id": "TA0004",
        "description": "Exploit software vulnerabilities to escalate privileges.",
        "subtechniques": {}
    },

    # ── Defense Evasion (TA0005) ──
    "T1562": {
        "name": "Impair Defenses",
        "tactic": "Defense Evasion",
        "tactic_id": "TA0005",
        "description": "Disable or modify security tools and infrastructure.",
        "subtechniques": {
            "T1562.001": "Disable or Modify Tools",
            "T1562.004": "Disable or Modify System Firewall",
        }
    },

    # ── Credential Access (TA0006) ──
    "T1110": {
        "name": "Brute Force",
        "tactic": "Credential Access",
        "tactic_id": "TA0006",
        "description": "Use brute force techniques to gain valid credentials.",
        "subtechniques": {
            "T1110.001": "Password Guessing",
            "T1110.003": "Password Spraying",
            "T1110.004": "Credential Stuffing",
        }
    },
    "T1552": {
        "name": "Unsecured Credentials",
        "tactic": "Credential Access",
        "tactic_id": "TA0006",
        "description": "Search for insecurely stored credentials.",
        "subtechniques": {
            "T1552.001": "Credentials In Files",
            "T1552.005": "Cloud Instance Metadata API",
        }
    },

    # ── Impact (TA0040) ──
    "T1499": {
        "name": "Endpoint Denial of Service",
        "tactic": "Impact",
        "tactic_id": "TA0040",
        "description": "Perform DoS attacks against endpoint resources.",
        "subtechniques": {
            "T1499.002": "Service Exhaustion Flood",
        }
    },
}


# ==================== Agent Action → ATT&CK Mapping ====================

# Maps PurpleOps agent action names to MITRE ATT&CK technique IDs
ACTION_TO_TECHNIQUE: Dict[str, List[str]] = {
    # Red Agent actions
    "sql_injection_attempt":      ["T1190"],
    "xss_test":                   ["T1190", "T1059.007"],
    "privilege_escalation_test":  ["T1068", "T1548"],
    "credential_test":            ["T1110", "T1078"],
    "brute_force":                ["T1110.001"],
    "password_spray":             ["T1110.003"],
    "credential_stuffing":        ["T1110.004"],

    # Offensive Orchestrator agents
    "recon_scan":                 ["T1595", "T1592"],
    "port_scan":                  ["T1595.001"],
    "vulnerability_scan":         ["T1595.002"],
    "directory_enum":             ["T1595.003"],
    "host_discovery":             ["T1592.002"],
    "credential_discovery":       ["T1589.001"],

    # Blue Agent / Defensive actions
    "waf_rule_update":            ["T1562.004"],  # Defensive mapping (modifying firewall)
    "security_group_modification": ["T1562.004"],
    "threat_detection":           ["T1595"],      # Detecting recon
    "incident_response":          ["T1562.001"],  # Responding to attacks
}


class MitreAttackMapper:
    """
    Maps PurpleOps agent actions to MITRE ATT&CK framework techniques.

    Usage:
        mapper = MitreAttackMapper()
        enriched = mapper.enrich_finding(action="sql_injection_attempt", finding={...})
    """

    def get_techniques_for_action(self, action: str) -> List[Dict]:
        """Get ATT&CK technique details for a given agent action."""
        technique_ids = ACTION_TO_TECHNIQUE.get(action, [])
        techniques = []
        for tid in technique_ids:
            technique = ATTACK_TECHNIQUES.get(tid)
            if technique:
                techniques.append({
                    "technique_id": tid,
                    "name": technique["name"],
                    "tactic": technique["tactic"],
                    "tactic_id": technique["tactic_id"],
                })
        return techniques

    def enrich_finding(self, action: str, finding: Dict) -> Dict:
        """
        Enrich an agent finding with MITRE ATT&CK technique references.

        Returns the original finding dict with a 'mitre_attack' key added.
        """
        techniques = self.get_techniques_for_action(action)
        finding["mitre_attack"] = {
            "techniques": techniques,
            "mapped_at": datetime.now(timezone.utc).isoformat(),
        }
        return finding

    def get_campaign_attack_coverage(self, actions: List[str]) -> Dict:
        """
        Summarize ATT&CK coverage for a set of campaign actions.

        Returns tactics covered and percentage of ATT&CK matrix exercised.
        """
        all_tactics = set()
        all_techniques = set()
        for action in actions:
            technique_ids = ACTION_TO_TECHNIQUE.get(action, [])
            for tid in technique_ids:
                all_techniques.add(tid)
                tech = ATTACK_TECHNIQUES.get(tid)
                if tech:
                    all_tactics.add(tech["tactic"])

        return {
            "tactics_covered": sorted(all_tactics),
            "techniques_used": sorted(all_techniques),
            "technique_count": len(all_techniques),
            "total_techniques_in_db": len(ATTACK_TECHNIQUES),
            "coverage_percent": round(len(all_techniques) / len(ATTACK_TECHNIQUES) * 100, 1),
        }

    @staticmethod
    def get_all_techniques() -> Dict:
        """Return the full ATT&CK technique database."""
        return ATTACK_TECHNIQUES
