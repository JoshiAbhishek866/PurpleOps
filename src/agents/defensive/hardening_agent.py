"""
System Hardening Agent — ENHANCED v2.0
Provides security hardening recommendations and compliance checking

Enhancements:
- Structured JSON-compatible logging
- Input validation on all public methods
- try/except guards around checks
- Comprehensive type hints
- ENHANCED v2.0 docstring markers
- uuid4-based assessment IDs
- Opt-in config for new features with sensible defaults
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any

from src.agents.base_agent import BaseAgent

# ENHANCED: module-level structured logger
_logger = logging.getLogger(__name__)


class HardeningAgent(BaseAgent):
    """
    System Hardening Agent — ENHANCED v2.0

    Capabilities:
    - Configuration analysis
    - Security baseline comparison
    - Compliance checking (CIS, NIST)
    - Hardening recommendations
    - Remediation scripts generation
    - Best practices validation

    ENHANCED v2.0 additions:
    - Structured logging with JSON metadata
    - Input validation & type checking
    - Graceful error handling on all check paths
    - Assessment IDs via uuid4
    - Opt-in config for new features
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("hardening", config)
        self.default_config = {
            "compliance_standards": ["cis", "nist"],
            "severity_threshold": "medium",
            "auto_remediate": False,
            "generate_scripts": True,
            # ENHANCED: new opt-in config knobs
            "enable_structured_logging": True,
            "assessment_id_enabled": True,
        }
        self.config = {**self.default_config, **(config or {})}

        # Hardening checks
        self.checks = self._load_hardening_checks()

        # Compliance baselines
        self.baselines = self._load_compliance_baselines()

    # ENHANCED: helper for structured log entries
    def _structured_log(self, level: str, message: str, **kwargs: Any) -> None:
        """Emit a structured JSON-compatible log entry."""
        entry = {
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            "agent": "hardening",
            "level": level,
            "message": message,
            **kwargs,
        }
        if self.config.get("enable_structured_logging"):
            _logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(entry))

    async def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute security hardening assessment"""

        # ENHANCED: input validation
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty string")

        self.logger.progress("Starting security hardening assessment...")

        # ENHANCED: assessment ID
        assessment_id = str(uuid.uuid4()) if self.config.get("assessment_id_enabled") else None
        self._structured_log("info", "Hardening assessment started", target=target, assessment_id=assessment_id)

        # Get system configuration from options
        system_config = options.get("system_config", {}) if options else {}
        services = options.get("services", []) if options else []
        os_type = options.get("os_type", "linux") if options else "linux"

        # Perform hardening assessment
        results: Dict[str, Any] = {
            "target": target,
            "os_type": os_type,
            "checks_performed": [],
            "findings": [],
            "recommendations": [],
            "compliance_status": {},
            "remediation_scripts": [],
            "hardening_score": 0.0,
            # ENHANCED: assessment ID in results
            "assessment_id": assessment_id,
        }

        # Run hardening checks
        try:
            findings = await self.run_hardening_checks(system_config, os_type)
            results["findings"] = findings
            results["checks_performed"] = list(self.checks.keys())
        except (TypeError, KeyError, ValueError) as exc:
            self._structured_log("error", "Hardening checks failed", error=str(exc))
            findings = []

        # Check compliance
        for standard in self.config["compliance_standards"]:
            try:
                compliance = await self.check_compliance(findings, standard)
                results["compliance_status"][standard] = compliance
            except (KeyError, ZeroDivisionError, TypeError) as exc:
                self._structured_log("error", "Compliance check failed", standard=standard, error=str(exc))

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(findings)

        # Generate remediation scripts
        if self.config["generate_scripts"]:
            results["remediation_scripts"] = self._generate_remediation_scripts(
                findings,
                os_type
            )

        # Calculate hardening score
        results["hardening_score"] = self._calculate_hardening_score(findings)

        # Summary
        results["summary"] = {
            "total_checks": len(results["checks_performed"]),
            "total_findings": len(findings),
            "critical": len([f for f in findings if f.get("severity") == "critical"]),
            "high": len([f for f in findings if f.get("severity") == "high"]),
            "medium": len([f for f in findings if f.get("severity") == "medium"]),
            "low": len([f for f in findings if f.get("severity") == "low"]),
            "hardening_score": f"{results['hardening_score']:.1f}/100"
        }

        self.logger.success(
            f"Hardening assessment completed: {len(findings)} findings "
            f"(Score: {results['hardening_score']:.1f}/100)"
        )
        self._structured_log("info", "Hardening assessment completed", summary=results["summary"], assessment_id=assessment_id)

        return results

    async def run_hardening_checks(
        self,
        system_config: Dict[str, Any],
        os_type: str
    ) -> List[Dict[str, Any]]:
        """Run all hardening checks"""
        # ENHANCED: input validation
        if not isinstance(system_config, dict):
            raise TypeError("system_config must be a dict")
        if not isinstance(os_type, str) or os_type not in ("linux", "windows", "macos"):
            self._structured_log("warning", "Unrecognised os_type, defaulting checks", os_type=os_type)

        self.logger.progress("Running hardening checks...")

        findings: List[Dict[str, Any]] = []

        # Network hardening
        try:
            network_findings = self._check_network_hardening(system_config)
            findings.extend(network_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "Network hardening check failed", error=str(exc))

        # Service hardening
        try:
            service_findings = self._check_service_hardening(system_config)
            findings.extend(service_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "Service hardening check failed", error=str(exc))

        # Authentication hardening
        try:
            auth_findings = self._check_authentication_hardening(system_config)
            findings.extend(auth_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "Auth hardening check failed", error=str(exc))

        # File system hardening
        try:
            fs_findings = self._check_filesystem_hardening(system_config)
            findings.extend(fs_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "Filesystem hardening check failed", error=str(exc))

        # Logging and auditing
        try:
            audit_findings = self._check_logging_auditing(system_config)
            findings.extend(audit_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "Logging/auditing check failed", error=str(exc))

        # OS-specific checks
        try:
            if os_type == "linux":
                linux_findings = self._check_linux_specific(system_config)
                findings.extend(linux_findings)
            elif os_type == "windows":
                windows_findings = self._check_windows_specific(system_config)
                findings.extend(windows_findings)
        except (KeyError, TypeError) as exc:
            self._structured_log("error", "OS-specific check failed", os_type=os_type, error=str(exc))

        return findings

    def _check_network_hardening(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check network security hardening"""
        findings: List[Dict[str, Any]] = []

        # Firewall check
        if not config.get("firewall_enabled", False):
            findings.append({
                "category": "network",
                "check": "firewall_enabled",
                "status": "fail",
                "severity": "high",
                "description": "Firewall is not enabled",
                "recommendation": "Enable and configure firewall",
                "cis_control": "9.2.1"
            })

        # IP forwarding
        if config.get("ip_forwarding_enabled", False):
            findings.append({
                "category": "network",
                "check": "ip_forwarding",
                "status": "fail",
                "severity": "medium",
                "description": "IP forwarding is enabled",
                "recommendation": "Disable IP forwarding unless required",
                "cis_control": "3.1.1"
            })

        # ICMP redirects
        if config.get("icmp_redirects_enabled", True):
            findings.append({
                "category": "network",
                "check": "icmp_redirects",
                "status": "fail",
                "severity": "low",
                "description": "ICMP redirects are enabled",
                "recommendation": "Disable ICMP redirects",
                "cis_control": "3.2.2"
            })

        return findings

    def _check_service_hardening(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check service security hardening"""
        findings: List[Dict[str, Any]] = []

        # Unnecessary services
        running_services = config.get("running_services", [])
        unnecessary_services = ["telnet", "ftp", "rsh", "rlogin"]

        for service in running_services:
            if service.lower() in unnecessary_services:
                findings.append({
                    "category": "services",
                    "check": "unnecessary_services",
                    "status": "fail",
                    "severity": "high",
                    "description": f"Insecure service '{service}' is running",
                    "recommendation": f"Disable {service} and use secure alternatives",
                    "cis_control": "2.2"
                })

        # SSH configuration
        ssh_config = config.get("ssh_config", {})

        if ssh_config.get("permit_root_login", True):
            findings.append({
                "category": "services",
                "check": "ssh_root_login",
                "status": "fail",
                "severity": "high",
                "description": "SSH root login is permitted",
                "recommendation": "Set PermitRootLogin to 'no' in sshd_config",
                "cis_control": "5.2.10"
            })

        if ssh_config.get("password_authentication", True):
            findings.append({
                "category": "services",
                "check": "ssh_password_auth",
                "status": "warn",
                "severity": "medium",
                "description": "SSH password authentication is enabled",
                "recommendation": "Use key-based authentication only",
                "cis_control": "5.2.11"
            })

        return findings

    def _check_authentication_hardening(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check authentication security"""
        findings: List[Dict[str, Any]] = []

        # Password policy
        password_policy = config.get("password_policy", {})

        if password_policy.get("min_length", 0) < 12:
            findings.append({
                "category": "authentication",
                "check": "password_length",
                "status": "fail",
                "severity": "high",
                "description": "Minimum password length is too short",
                "recommendation": "Set minimum password length to 12 characters",
                "cis_control": "5.3.1"
            })

        if not password_policy.get("complexity_required", False):
            findings.append({
                "category": "authentication",
                "check": "password_complexity",
                "status": "fail",
                "severity": "high",
                "description": "Password complexity is not enforced",
                "recommendation": "Require complex passwords (uppercase, lowercase, numbers, symbols)",
                "cis_control": "5.3.2"
            })

        # Account lockout
        if not config.get("account_lockout_enabled", False):
            findings.append({
                "category": "authentication",
                "check": "account_lockout",
                "status": "fail",
                "severity": "medium",
                "description": "Account lockout policy is not configured",
                "recommendation": "Configure account lockout after failed login attempts",
                "cis_control": "5.3.3"
            })

        # MFA
        if not config.get("mfa_enabled", False):
            findings.append({
                "category": "authentication",
                "check": "multi_factor_auth",
                "status": "warn",
                "severity": "high",
                "description": "Multi-factor authentication is not enabled",
                "recommendation": "Enable MFA for all user accounts",
                "cis_control": "6.3"
            })

        return findings

    def _check_filesystem_hardening(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check filesystem security"""
        findings: List[Dict[str, Any]] = []

        # Partition mounting options
        partitions = config.get("partitions", [])

        for partition in partitions:
            mount_point = partition.get("mount_point")
            options = partition.get("options", [])

            # /tmp should be noexec, nosuid, nodev
            if mount_point == "/tmp":
                if "noexec" not in options:
                    findings.append({
                        "category": "filesystem",
                        "check": "tmp_noexec",
                        "status": "fail",
                        "severity": "medium",
                        "description": "/tmp is not mounted with noexec",
                        "recommendation": "Mount /tmp with noexec option",
                        "cis_control": "1.1.3"
                    })

        # World-writable files
        if config.get("world_writable_files", 0) > 0:
            findings.append({
                "category": "filesystem",
                "check": "world_writable_files",
                "status": "fail",
                "severity": "high",
                "description": f"{config['world_writable_files']} world-writable files found",
                "recommendation": "Remove world-writable permissions from files",
                "cis_control": "6.1.10"
            })

        return findings

    def _check_logging_auditing(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check logging and auditing"""
        findings: List[Dict[str, Any]] = []

        # Audit daemon
        if not config.get("auditd_enabled", False):
            findings.append({
                "category": "logging",
                "check": "auditd_enabled",
                "status": "fail",
                "severity": "medium",
                "description": "Audit daemon (auditd) is not enabled",
                "recommendation": "Enable and configure auditd",
                "cis_control": "4.1.1"
            })

        # Log rotation
        if not config.get("log_rotation_configured", False):
            findings.append({
                "category": "logging",
                "check": "log_rotation",
                "status": "fail",
                "severity": "low",
                "description": "Log rotation is not configured",
                "recommendation": "Configure log rotation to prevent disk space issues",
                "cis_control": "4.2.1"
            })

        return findings

    def _check_linux_specific(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Linux-specific hardening checks"""
        findings: List[Dict[str, Any]] = []

        # SELinux/AppArmor
        if not config.get("selinux_enabled", False) and not config.get("apparmor_enabled", False):
            findings.append({
                "category": "linux",
                "check": "mandatory_access_control",
                "status": "fail",
                "severity": "high",
                "description": "No mandatory access control (SELinux/AppArmor) enabled",
                "recommendation": "Enable and configure SELinux or AppArmor",
                "cis_control": "1.6.1"
            })

        return findings

    def _check_windows_specific(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Windows-specific hardening checks"""
        findings: List[Dict[str, Any]] = []

        # Windows Defender
        if not config.get("windows_defender_enabled", False):
            findings.append({
                "category": "windows",
                "check": "antivirus",
                "status": "fail",
                "severity": "critical",
                "description": "Windows Defender is not enabled",
                "recommendation": "Enable Windows Defender or install antivirus",
                "cis_control": "8.1"
            })

        return findings

    async def check_compliance(self, findings: List[Dict[str, Any]], standard: str) -> Dict[str, Any]:
        """Check compliance with security standard"""
        # ENHANCED: input validation
        if not isinstance(standard, str) or not standard.strip():
            raise ValueError("standard must be a non-empty string")

        self.logger.progress(f"Checking {standard.upper()} compliance...")

        baseline = self.baselines.get(standard, {})
        total_controls = len(baseline)

        # Count passed/failed controls
        failed_controls = [f for f in findings if f.get("cis_control") in baseline]
        passed_controls = total_controls - len(failed_controls)

        compliance_percentage = (passed_controls / total_controls * 100) if total_controls > 0 else 0

        return {
            "standard": standard.upper(),
            "total_controls": total_controls,
            "passed": passed_controls,
            "failed": len(failed_controls),
            "compliance_percentage": f"{compliance_percentage:.1f}%",
            "status": "compliant" if compliance_percentage >= 80 else "non-compliant"
        }

    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            findings,
            key=lambda x: severity_order.get(x.get("severity", "low"), 3)
        )

        recommendations: List[Dict[str, Any]] = []

        for finding in sorted_findings[:20]:  # Top 20
            recommendations.append({
                "priority": finding.get("severity"),
                "category": finding.get("category"),
                "issue": finding.get("description"),
                "action": finding.get("recommendation"),
                "cis_control": finding.get("cis_control")
            })

        return recommendations

    def _generate_remediation_scripts(
        self,
        findings: List[Dict[str, Any]],
        os_type: str
    ) -> List[Dict[str, Any]]:
        """Generate remediation scripts"""
        scripts: List[Dict[str, Any]] = []

        for finding in findings:
            check = finding.get("check")
            script: Optional[str] = None

            if os_type == "linux":
                script = self._generate_linux_script(check)
            elif os_type == "windows":
                script = self._generate_windows_script(check)

            if script:
                scripts.append({
                    "check": check,
                    "description": finding.get("description"),
                    "script": script,
                    "os_type": os_type
                })

        return scripts

    def _generate_linux_script(self, check: Optional[str]) -> Optional[str]:
        """Generate Linux remediation script"""
        scripts = {
            "firewall_enabled": "sudo ufw enable",
            "ip_forwarding": "echo 'net.ipv4.ip_forward = 0' | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            "ssh_root_login": "sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && sudo systemctl restart sshd",
            "auditd_enabled": "sudo systemctl enable auditd && sudo systemctl start auditd"
        }

        return scripts.get(check) if check else None

    def _generate_windows_script(self, check: Optional[str]) -> Optional[str]:
        """Generate Windows remediation script"""
        scripts = {
            "windows_defender_enabled": "Set-MpPreference -DisableRealtimeMonitoring $false"
        }

        return scripts.get(check) if check else None

    def _calculate_hardening_score(self, findings: List[Dict[str, Any]]) -> float:
        """Calculate overall hardening score (0-100)"""
        if not findings:
            return 100.0

        # Deduct points based on severity
        total_deduction = 0

        for finding in findings:
            severity = finding.get("severity", "low")
            if severity == "critical":
                total_deduction += 10
            elif severity == "high":
                total_deduction += 5
            elif severity == "medium":
                total_deduction += 2
            else:
                total_deduction += 1

        score = max(0, 100 - total_deduction)
        return score

    def _load_hardening_checks(self) -> Dict[str, str]:
        """Load hardening check definitions"""
        return {
            "firewall_enabled": "Firewall configuration",
            "ip_forwarding": "IP forwarding settings",
            "ssh_root_login": "SSH root login",
            "password_length": "Password minimum length",
            "mfa_enabled": "Multi-factor authentication",
            "auditd_enabled": "Audit daemon",
            "selinux_enabled": "SELinux/AppArmor"
        }

    def _load_compliance_baselines(self) -> Dict[str, Dict[str, str]]:
        """Load compliance baseline controls"""
        return {
            "cis": {
                "1.1.3": "Ensure /tmp is configured",
                "3.1.1": "Ensure IP forwarding is disabled",
                "5.2.10": "Ensure SSH root login is disabled",
                "5.3.1": "Ensure password creation requirements are configured"
            },
            "nist": {
                "AC-2": "Account Management",
                "AU-2": "Audit Events",
                "SC-7": "Boundary Protection"
            }
        }
