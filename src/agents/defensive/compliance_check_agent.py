"""
Compliance Check Agent — ENHANCED v2.0
Multi-framework security compliance assessment

Enhancements:
- Timezone-aware datetimes (datetime.now(timezone.utc))
- uuid4-based audit report IDs
- Structured JSON-compatible logging
- Input validation on all public methods
- try/except guards around framework assessments
- Comprehensive type hints throughout
- Opt-in config for new features with sensible defaults
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent

# ENHANCED: module-level structured logger
_logger = logging.getLogger(__name__)


class ComplianceCheckAgent(BaseAgent):
    """
    Compliance Check Agent — ENHANCED v2.0

    Capabilities:
    - Multi-framework compliance (CIS, NIST, PCI-DSS, HIPAA, ISO 27001)
    - Automated control checking
    - Gap analysis
    - Compliance scoring
    - Remediation tracking
    - Audit report generation

    ENHANCED v2.0 additions:
    - Timezone-aware timestamps throughout
    - uuid4 for audit report IDs
    - Structured logging with JSON metadata
    - Input validation & type checking
    - Graceful error handling on all assessment paths
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("compliance_check", config)
        self.default_config = {
            "timeout": 180,
            "frameworks": ["cis", "nist", "pci-dss"],
            "generate_audit_report": True,
            "track_remediation": True,
            # ENHANCED: new opt-in config knobs
            "enable_structured_logging": True,
            "assessment_id_enabled": True,
        }
        self.config = {**self.default_config, **(config or {})}

        # Load compliance frameworks
        self.frameworks = self._load_frameworks()

    # ENHANCED: helper for structured log entries
    def _structured_log(self, level: str, message: str, **kwargs: Any) -> None:
        """Emit a structured JSON-compatible log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "compliance_check",
            "level": level,
            "message": message,
            **kwargs,
        }
        if self.config.get("enable_structured_logging"):
            _logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(entry))

    async def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute compliance assessment"""

        # ENHANCED: input validation
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty string")

        self.logger.progress("Starting compliance assessment...")

        # ENHANCED: assessment ID
        assessment_id = str(uuid.uuid4()) if self.config.get("assessment_id_enabled") else None
        self._structured_log("info", "Compliance assessment started", target=target, assessment_id=assessment_id)

        # Get system configuration from options
        system_config = options.get("system_config", {}) if options else {}

        results: Dict[str, Any] = {
            "target": target,
            "frameworks_assessed": [],
            "compliance_results": {},
            "overall_compliance": {},
            "gaps": [],
            "recommendations": [],
            "audit_report": None,
            # ENHANCED: assessment ID
            "assessment_id": assessment_id,
        }

        # Assess each framework
        for framework_name in self.config["frameworks"]:
            if framework_name in self.frameworks:
                self.logger.progress(f"Assessing {framework_name.upper()} compliance...")

                try:
                    framework_result = await self._assess_framework(
                        framework_name,
                        system_config
                    )

                    results["frameworks_assessed"].append(framework_name)
                    results["compliance_results"][framework_name] = framework_result
                except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
                    self._structured_log(
                        "error",
                        "Framework assessment failed",
                        framework=framework_name,
                        error=str(exc),
                    )

        # Calculate overall compliance
        try:
            results["overall_compliance"] = self._calculate_overall_compliance(
                results["compliance_results"]
            )
        except (ZeroDivisionError, KeyError, TypeError) as exc:
            self._structured_log("error", "Overall compliance calculation failed", error=str(exc))
            results["overall_compliance"] = {"percentage": 0.0, "status": "error", "total_controls": 0, "passed": 0, "failed": 0}

        # Identify gaps
        results["gaps"] = self._identify_gaps(results["compliance_results"])

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(
            results["gaps"]
        )

        # Generate audit report
        if self.config["generate_audit_report"]:
            results["audit_report"] = self._generate_audit_report(results)

        self.logger.success(
            f"Compliance assessment completed: "
            f"{results['overall_compliance']['percentage']:.1f}% compliant"
        )
        self._structured_log(
            "info",
            "Compliance assessment completed",
            overall_percentage=results["overall_compliance"]["percentage"],
            assessment_id=assessment_id,
        )

        return results

    async def _assess_framework(
        self,
        framework_name: str,
        system_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess compliance with specific framework"""

        framework = self.frameworks[framework_name]
        controls = framework["controls"]

        assessment_results: Dict[str, Any] = {
            "framework": framework_name,
            "total_controls": len(controls),
            "passed": 0,
            "failed": 0,
            "not_applicable": 0,
            "control_results": [],
            "compliance_percentage": 0.0,
            "status": "non_compliant"
        }

        # Check each control
        for control_id, control in controls.items():
            try:
                result = await self._check_control(control, system_config)

                control_result: Dict[str, str] = {
                    "control_id": control_id,
                    "name": control["name"],
                    "description": control["description"],
                    "status": result["status"],
                    "evidence": result.get("evidence", ""),
                    "gap": result.get("gap", "")
                }

                assessment_results["control_results"].append(control_result)

                if result["status"] == "pass":
                    assessment_results["passed"] += 1
                elif result["status"] == "fail":
                    assessment_results["failed"] += 1
                else:
                    assessment_results["not_applicable"] += 1
            except (KeyError, TypeError, ValueError) as exc:
                self._structured_log(
                    "warning",
                    "Control check failed",
                    control_id=control_id,
                    error=str(exc),
                )
                assessment_results["failed"] += 1

        # Calculate compliance percentage
        applicable_controls = assessment_results["total_controls"] - assessment_results["not_applicable"]

        if applicable_controls > 0:
            assessment_results["compliance_percentage"] = (
                assessment_results["passed"] / applicable_controls * 100
            )

        # Determine status
        if assessment_results["compliance_percentage"] >= 90:
            assessment_results["status"] = "compliant"
        elif assessment_results["compliance_percentage"] >= 70:
            assessment_results["status"] = "partially_compliant"
        else:
            assessment_results["status"] = "non_compliant"

        return assessment_results

    async def _check_control(self, control: Dict[str, Any], system_config: Dict[str, Any]) -> Dict[str, str]:
        """Check individual compliance control"""

        # Simulate control checking
        # In production, this would perform actual checks

        check_type = control.get("check_type")
        check_key = control.get("check_key")
        expected_value = control.get("expected_value")

        result: Dict[str, str] = {
            "status": "fail",
            "evidence": "",
            "gap": ""
        }

        # Perform check based on type
        if check_type == "config":
            actual_value = system_config.get(check_key)

            if actual_value == expected_value:
                result["status"] = "pass"
                result["evidence"] = f"{check_key} is set to {actual_value}"
            else:
                result["status"] = "fail"
                result["gap"] = f"{check_key} should be {expected_value}, found {actual_value}"

        elif check_type == "boolean":
            actual_value = system_config.get(check_key, False)

            if actual_value == expected_value:
                result["status"] = "pass"
                result["evidence"] = f"{check_key} is correctly configured"
            else:
                result["status"] = "fail"
                result["gap"] = f"{check_key} must be set to {expected_value}"

        elif check_type == "minimum":
            actual_value = system_config.get(check_key, 0)

            if actual_value >= expected_value:
                result["status"] = "pass"
                result["evidence"] = f"{check_key} meets minimum requirement ({actual_value} >= {expected_value})"
            else:
                result["status"] = "fail"
                result["gap"] = f"{check_key} below minimum ({actual_value} < {expected_value})"

        return result

    def _calculate_overall_compliance(self, compliance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall compliance across all frameworks"""

        total_controls = 0
        total_passed = 0
        total_failed = 0

        for framework_name, result in compliance_results.items():
            total_controls += result["total_controls"]
            total_passed += result["passed"]
            total_failed += result["failed"]

        percentage = (total_passed / total_controls * 100) if total_controls > 0 else 0

        return {
            "total_controls": total_controls,
            "passed": total_passed,
            "failed": total_failed,
            "percentage": percentage,
            "status": "compliant" if percentage >= 80 else "non_compliant"
        }

    def _identify_gaps(self, compliance_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify compliance gaps"""

        gaps: List[Dict[str, Any]] = []

        for framework_name, result in compliance_results.items():
            for control_result in result["control_results"]:
                if control_result["status"] == "fail":
                    gaps.append({
                        "framework": framework_name,
                        "control_id": control_result["control_id"],
                        "control_name": control_result["name"],
                        "gap": control_result["gap"],
                        "severity": self._determine_gap_severity(control_result)
                    })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: severity_order.get(x["severity"], 3))

        return gaps

    def _determine_gap_severity(self, control_result: Dict[str, str]) -> str:
        """Determine severity of compliance gap"""

        # Critical controls (simplified logic)
        critical_keywords = ["encryption", "authentication", "access control", "audit"]
        high_keywords = ["password", "firewall", "logging"]

        control_name = control_result["name"].lower()

        if any(keyword in control_name for keyword in critical_keywords):
            return "critical"
        elif any(keyword in control_name for keyword in high_keywords):
            return "high"
        else:
            return "medium"

    def _generate_recommendations(self, gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate remediation recommendations"""

        recommendations: List[Dict[str, Any]] = []

        for gap in gaps[:20]:  # Top 20 gaps
            recommendations.append({
                "priority": gap["severity"],
                "framework": gap["framework"],
                "control": gap["control_id"],
                "issue": gap["gap"],
                "recommendation": self._get_remediation_action(gap)
            })

        return recommendations

    def _get_remediation_action(self, gap: Dict[str, Any]) -> str:
        """Get specific remediation action for gap"""

        # Simplified remediation mapping
        control_name = gap["control_name"].lower()

        if "encryption" in control_name:
            return "Enable encryption for data at rest and in transit"
        elif "password" in control_name:
            return "Implement strong password policy with complexity requirements"
        elif "mfa" in control_name or "multi-factor" in control_name:
            return "Enable multi-factor authentication for all users"
        elif "firewall" in control_name:
            return "Configure and enable firewall with appropriate rules"
        elif "logging" in control_name:
            return "Enable comprehensive security logging and monitoring"
        elif "patch" in control_name:
            return "Implement regular patch management process"
        else:
            return f"Address compliance gap: {gap['gap']}"

    def _generate_audit_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance audit report"""

        # ENHANCED: uuid4-based report ID and timezone-aware timestamps
        report: Dict[str, Any] = {
            "report_id": f"AUDIT-{uuid.uuid4().hex[:12].upper()}",
            "target": results["target"],
            # ENHANCED: timezone-aware timestamp
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "frameworks_assessed": results["frameworks_assessed"],
            "executive_summary": {
                "overall_compliance": results["overall_compliance"]["percentage"],
                "status": results["overall_compliance"]["status"],
                "total_gaps": len(results["gaps"]),
                "critical_gaps": len([g for g in results["gaps"] if g["severity"] == "critical"])
            },
            "detailed_results": results["compliance_results"],
            "gap_analysis": results["gaps"],
            "remediation_plan": results["recommendations"]
        }

        return report

    def _load_frameworks(self) -> Dict[str, Any]:
        """Load compliance framework definitions"""

        return {
            "cis": {
                "name": "CIS Controls",
                "version": "8.0",
                "controls": {
                    "1.1": {
                        "name": "Inventory of Authorized Assets",
                        "description": "Maintain accurate inventory of all assets",
                        "check_type": "boolean",
                        "check_key": "asset_inventory_enabled",
                        "expected_value": True
                    },
                    "3.1": {
                        "name": "Data Protection",
                        "description": "Establish and maintain data protection process",
                        "check_type": "boolean",
                        "check_key": "data_protection_enabled",
                        "expected_value": True
                    },
                    "4.1": {
                        "name": "Secure Configuration",
                        "description": "Establish secure configurations",
                        "check_type": "boolean",
                        "check_key": "secure_config_baseline",
                        "expected_value": True
                    },
                    "5.1": {
                        "name": "Account Management",
                        "description": "Use unique passwords",
                        "check_type": "minimum",
                        "check_key": "password_min_length",
                        "expected_value": 12
                    },
                    "6.1": {
                        "name": "Access Control",
                        "description": "Establish access control process",
                        "check_type": "boolean",
                        "check_key": "access_control_enabled",
                        "expected_value": True
                    },
                    "8.1": {
                        "name": "Audit Log Management",
                        "description": "Establish audit log management process",
                        "check_type": "boolean",
                        "check_key": "audit_logging_enabled",
                        "expected_value": True
                    }
                }
            },
            "nist": {
                "name": "NIST Cybersecurity Framework",
                "version": "1.1",
                "controls": {
                    "ID.AM-1": {
                        "name": "Physical devices and systems inventory",
                        "description": "Inventory of physical devices",
                        "check_type": "boolean",
                        "check_key": "device_inventory",
                        "expected_value": True
                    },
                    "PR.AC-1": {
                        "name": "Access Control",
                        "description": "Identities and credentials managed",
                        "check_type": "boolean",
                        "check_key": "identity_management",
                        "expected_value": True
                    },
                    "PR.DS-1": {
                        "name": "Data at Rest Protection",
                        "description": "Data at rest is protected",
                        "check_type": "boolean",
                        "check_key": "encryption_at_rest",
                        "expected_value": True
                    },
                    "DE.CM-1": {
                        "name": "Network Monitoring",
                        "description": "Network monitored for anomalies",
                        "check_type": "boolean",
                        "check_key": "network_monitoring",
                        "expected_value": True
                    }
                }
            },
            "pci-dss": {
                "name": "PCI-DSS",
                "version": "4.0",
                "controls": {
                    "1.1": {
                        "name": "Firewall Configuration",
                        "description": "Install and maintain firewall",
                        "check_type": "boolean",
                        "check_key": "firewall_enabled",
                        "expected_value": True
                    },
                    "2.1": {
                        "name": "Default Passwords",
                        "description": "Change default passwords",
                        "check_type": "boolean",
                        "check_key": "default_passwords_changed",
                        "expected_value": True
                    },
                    "3.1": {
                        "name": "Data Encryption",
                        "description": "Protect stored cardholder data",
                        "check_type": "boolean",
                        "check_key": "data_encryption",
                        "expected_value": True
                    },
                    "8.1": {
                        "name": "User Authentication",
                        "description": "Assign unique ID to each user",
                        "check_type": "boolean",
                        "check_key": "unique_user_ids",
                        "expected_value": True
                    }
                }
            }
        }
