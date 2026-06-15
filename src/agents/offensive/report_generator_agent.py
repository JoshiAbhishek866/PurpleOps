"""
Report Generator Agent — ENHANCED v2.0
AI-powered security findings summary and report generation

ENHANCED v2.0:
- Structured JSON-compatible logging via _log()
- Timezone-aware datetimes (datetime.now(timezone.utc)) replacing datetime.utcnow()
- UUID4-based report ID generation
- Input validation on agent_results
- try/except with specific exception types
- Detailed docstrings on every method
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json
import uuid
import html as html_module

from src.agents.base_agent import BaseAgent


class ReportGeneratorAgent(BaseAgent):
    """
    Report Generator Agent — ENHANCED v2.0

    Capabilities:
    - AI-powered summary generation
    - Executive summary
    - Technical details
    - Recommendations
    - PDF/HTML generation
    - Multiple report formats
    - Customizable templates

    ENHANCED v2.0 additions:
    - Structured logging with JSON context
    - Timezone-aware timestamps (no more datetime.utcnow())
    - UUID4-based report IDs
    - Input validation on agent_results
    - Specific exception handling in format generation
    - Safe HTML escaping for XSS prevention
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("report_generator", config)
        self.default_config = {
            "timeout": 120,
            "formats": ["json", "html", "markdown"],
            "include_executive_summary": True,
            "include_technical_details": True,
            "include_recommendations": True,
            "include_charts": True,
            "ai_enhanced": True
        }
        self.config = {**self.default_config, **(config or {})}

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Generate comprehensive security report from agent results.

        Args:
            target: Hostname or IP that was assessed.
            options: Must include 'agent_results' dict keyed by agent type.

        Returns:
            Dict with metadata, executive_summary, findings_overview,
            detailed_findings, risk_assessment, recommendations,
            technical_appendix, and formatted output in multiple formats.
        """

        # ENHANCED: structured log with report tracking
        report_tracking_id = uuid.uuid4().hex[:12]
        self._log("info", "Report generation started", target=target,
                  report_tracking_id=report_tracking_id)
        self.logger.progress("Generating security report...")

        # Get all agent results from options
        agent_results = options.get("agent_results", {}) if options else {}

        if not agent_results:
            self.logger.warning("No agent results provided for report generation")
            return {
                "error": "No results to generate report from",
                "status": "failed",
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # ENHANCED: validate agent_results structure
        if not isinstance(agent_results, dict):
            self._log("warning", "agent_results is not a dict", target=target)
            return {
                "error": "agent_results must be a dictionary",
                "status": "failed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Generate report sections
        report: Dict[str, Any] = {
            "metadata": self._generate_metadata(target),
            "executive_summary": None,
            "findings_overview": None,
            "detailed_findings": None,
            "risk_assessment": None,
            "recommendations": None,
            "technical_appendix": None,
            "formats": {}
        }

        # Executive Summary
        if self.config["include_executive_summary"]:
            try:
                report["executive_summary"] = await self._generate_executive_summary(
                    agent_results
                )
            except (KeyError, TypeError) as e:
                # ENHANCED: specific error handling
                self._log("warning", "Executive summary generation error",
                          target=target, error=str(e))
                report["executive_summary"] = {
                    "overview": "Error generating executive summary",
                    "overall_risk_level": "Unknown",
                    "risk_score": 0,
                    "critical_findings": 0, "high_findings": 0,
                    "medium_findings": 0, "low_findings": 0,
                    "key_concerns": [], "immediate_actions": []
                }

        # Findings Overview
        try:
            report["findings_overview"] = self._generate_findings_overview(agent_results)
        except (KeyError, TypeError) as e:
            self._log("warning", "Findings overview generation error", error=str(e))
            report["findings_overview"] = {
                "agents_executed": 0, "total_findings": 0,
                "by_agent": {}, "by_severity": {}
            }

        # Detailed Findings
        if self.config["include_technical_details"]:
            try:
                report["detailed_findings"] = self._generate_detailed_findings(agent_results)
            except (KeyError, TypeError) as e:
                self._log("warning", "Detailed findings generation error", error=str(e))
                report["detailed_findings"] = {}

        # Risk Assessment
        try:
            report["risk_assessment"] = self._generate_risk_assessment(agent_results)
        except (KeyError, TypeError) as e:
            self._log("warning", "Risk assessment generation error", error=str(e))
            report["risk_assessment"] = {"risk_factors": [], "overall_assessment": "Error"}

        # Recommendations
        if self.config["include_recommendations"]:
            try:
                report["recommendations"] = self._generate_recommendations(agent_results)
            except (KeyError, TypeError) as e:
                self._log("warning", "Recommendations generation error", error=str(e))
                report["recommendations"] = []

        # Technical Appendix
        try:
            report["technical_appendix"] = self._generate_technical_appendix(agent_results)
        except (KeyError, TypeError) as e:
            self._log("warning", "Technical appendix generation error", error=str(e))
            report["technical_appendix"] = {}

        # Generate different formats
        for format_type in self.config["formats"]:
            try:
                if format_type == "json":
                    report["formats"]["json"] = json.dumps(report, indent=2, default=str)
                elif format_type == "html":
                    report["formats"]["html"] = self._generate_html_report(report)
                elif format_type == "markdown":
                    report["formats"]["markdown"] = self._generate_markdown_report(report)
            except (KeyError, TypeError, ValueError) as e:
                # ENHANCED: per-format error handling
                self._log("warning", f"Format generation failed: {format_type}", error=str(e))
                report["formats"][format_type] = f"Error generating {format_type} report: {e}"

        self._log("info", "Report generation completed", target=target,
                  report_tracking_id=report_tracking_id,
                  formats_generated=list(report["formats"].keys()))
        self.logger.success("Security report generated successfully")

        return report

    def _generate_metadata(self, target: str) -> Dict:
        """
        Generate report metadata with timezone-aware timestamps.

        Args:
            target: Assessed target hostname or IP.

        Returns:
            Dict with report_id, target, generated_at, report_type, and version.
        """
        # ENHANCED: replaced datetime.utcnow() with datetime.now(timezone.utc)
        # ENHANCED: UUID4-based report ID instead of timestamp-based
        now = datetime.now(timezone.utc)
        return {
            "report_id": f"RPT-{uuid.uuid4().hex[:12].upper()}",
            "target": target,
            "generated_at": now.isoformat(),
            "report_type": "Comprehensive Security Assessment",
            "version": "2.0"
        }

    async def _generate_executive_summary(self, agent_results: Dict) -> Dict:
        """
        Generate AI-powered executive summary from all agent results.

        Args:
            agent_results: Dict keyed by agent type with result data.

        Returns:
            Dict with overview, risk level, severity counts, concerns, and actions.
        """
        self.logger.progress("Generating executive summary...")

        # Count findings by severity
        total_critical = 0
        total_high = 0
        total_medium = 0
        total_low = 0

        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            # Count vulnerabilities
            if "vulnerabilities" in data:
                for vuln in data["vulnerabilities"]:
                    severity = vuln.get("severity", "").lower()
                    if "critical" in severity:
                        total_critical += 1
                    elif "high" in severity:
                        total_high += 1
                    elif "medium" in severity:
                        total_medium += 1
                    else:
                        total_low += 1

            # Count threats
            if "threats_detected" in data:
                total_high += len([t for t in data["threats_detected"] if t.get("severity") == "high"])

            # Count findings
            if "findings" in data:
                total_high += len([f for f in data["findings"] if f.get("severity") == "high"])

        # Calculate overall risk
        risk_score = (total_critical * 10 + total_high * 5 + total_medium * 2 + total_low * 1)

        if risk_score >= 50:
            overall_risk = "Critical"
        elif risk_score >= 20:
            overall_risk = "High"
        elif risk_score >= 10:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"

        summary: Dict[str, Any] = {
            "overview": f"Security assessment identified {total_critical + total_high + total_medium + total_low} total findings across multiple security domains.",
            "overall_risk_level": overall_risk,
            "risk_score": risk_score,
            "critical_findings": total_critical,
            "high_findings": total_high,
            "medium_findings": total_medium,
            "low_findings": total_low,
            "key_concerns": self._extract_key_concerns(agent_results),
            "immediate_actions": self._extract_immediate_actions(agent_results)
        }

        return summary

    def _generate_findings_overview(self, agent_results: Dict) -> Dict:
        """
        Generate overview of all findings across agents.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            Dict with agents_executed, total_findings, by_agent, and by_severity.
        """
        overview: Dict[str, Any] = {
            "agents_executed": len(agent_results),
            "total_findings": 0,
            "by_agent": {},
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }

        for agent_type, result in agent_results.items():
            data = result.get("data", {})
            agent_findings = 0

            # Count different types of findings
            if "vulnerabilities" in data:
                agent_findings += len(data["vulnerabilities"])
            if "threats_detected" in data:
                agent_findings += len(data["threats_detected"])
            if "findings" in data:
                agent_findings += len(data["findings"])
            if "weak_credentials" in data:
                agent_findings += len(data["weak_credentials"])

            overview["by_agent"][agent_type] = agent_findings
            overview["total_findings"] += agent_findings

        return overview

    def _generate_detailed_findings(self, agent_results: Dict) -> Dict:
        """
        Generate detailed findings section per agent.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            Dict mapping agent type to its detailed findings.
        """
        detailed: Dict[str, Any] = {}

        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            detailed[agent_type] = {
                "agent": agent_type,
                "status": result.get("status"),
                "duration": data.get("duration"),
                "findings": []
            }

            # Extract findings based on agent type
            try:
                if agent_type == "recon":
                    detailed[agent_type]["findings"] = self._extract_recon_findings(data)
                elif agent_type == "scanner":
                    detailed[agent_type]["findings"] = self._extract_scanner_findings(data)
                elif agent_type == "vuln":
                    detailed[agent_type]["findings"] = self._extract_vuln_findings(data)
                elif agent_type == "credential_testing":
                    detailed[agent_type]["findings"] = self._extract_cred_findings(data)
                elif agent_type == "threat_detection":
                    detailed[agent_type]["findings"] = self._extract_threat_findings(data)
                elif agent_type == "hardening":
                    detailed[agent_type]["findings"] = self._extract_hardening_findings(data)
            except (KeyError, TypeError) as e:
                # ENHANCED: per-agent extraction error handling
                self._log("warning", f"Finding extraction failed for {agent_type}",
                          error=str(e))
                detailed[agent_type]["findings"] = []

        return detailed

    def _generate_risk_assessment(self, agent_results: Dict) -> Dict:
        """
        Generate risk assessment from agent risk scores.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            Dict with risk_factors, overall_assessment, and business_impact.
        """
        risk_factors: List[Dict] = []

        # Analyze each agent's results
        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            if "risk_score" in data:
                risk_factors.append({
                    "category": agent_type,
                    "score": data["risk_score"],
                    "description": f"Risk from {agent_type} assessment"
                })

        return {
            "risk_factors": risk_factors,
            "overall_assessment": "Comprehensive risk analysis based on multiple security domains",
            "business_impact": "Potential impact on business operations and data security"
        }

    def _generate_recommendations(self, agent_results: Dict) -> List[Dict]:
        """
        Generate prioritized recommendations from all agent results.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            Sorted list of recommendation dicts (max 20).
        """
        all_recommendations: List[Dict] = []

        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            if "recommendations" in data:
                for rec in data["recommendations"]:
                    if isinstance(rec, str):
                        all_recommendations.append({
                            "priority": "high",
                            "category": agent_type,
                            "recommendation": rec
                        })
                    elif isinstance(rec, dict):
                        all_recommendations.append({
                            "priority": rec.get("priority", "medium"),
                            "category": agent_type,
                            "recommendation": rec.get("action", rec.get("recommendation", ""))
                        })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_recs = sorted(
            all_recommendations,
            key=lambda x: priority_order.get(x.get("priority", "medium"), 2)
        )

        return sorted_recs[:20]  # Top 20

    def _generate_technical_appendix(self, agent_results: Dict) -> Dict:
        """
        Generate technical appendix with raw results and methodology.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            Dict with raw_results, methodology, tools_used, and scan_parameters.
        """
        return {
            "raw_results": agent_results,
            "methodology": "Multi-agent security assessment using offensive and defensive techniques",
            "tools_used": list(agent_results.keys()),
            "scan_parameters": "Comprehensive assessment with ethical testing controls"
        }

    def _extract_key_concerns(self, agent_results: Dict) -> List[str]:
        """
        Extract key security concerns from agent results.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            List of concern strings (max 5).
        """
        concerns: List[str] = []

        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            # Check for critical issues
            if "vulnerabilities" in data:
                critical_vulns = [v for v in data["vulnerabilities"] if v.get("cvss_score", 0) >= 9.0]
                if critical_vulns:
                    concerns.append(f"Critical vulnerabilities detected ({len(critical_vulns)})")

            if "default_credentials" in data and data["default_credentials"]:
                concerns.append("Default credentials in use")

            if "threats_detected" in data:
                high_threats = [t for t in data["threats_detected"] if t.get("severity") == "high"]
                if high_threats:
                    concerns.append(f"Active threats detected ({len(high_threats)})")

        return concerns[:5]  # Top 5

    def _extract_immediate_actions(self, agent_results: Dict) -> List[str]:
        """
        Extract immediate action items from agent results.

        Args:
            agent_results: Dict keyed by agent type.

        Returns:
            List of action strings (max 5).
        """
        actions: List[str] = []

        for agent_type, result in agent_results.items():
            data = result.get("data", {})

            if "default_credentials" in data and data["default_credentials"]:
                actions.append("Change all default credentials immediately")

            if "vulnerabilities" in data:
                critical = [v for v in data["vulnerabilities"] if v.get("cvss_score", 0) >= 9.0]
                if critical:
                    actions.append(f"Patch {len(critical)} critical vulnerabilities within 24 hours")

        return actions[:5]

    def _extract_recon_findings(self, data: Dict) -> List[Dict]:
        """Extract reconnaissance findings"""
        findings: List[Dict] = []

        if data.get("subdomains"):
            findings.append({
                "type": "subdomain_discovery",
                "count": len(data["subdomains"]),
                "details": f"Discovered {len(data['subdomains'])} subdomains"
            })

        if data.get("open_ports"):
            findings.append({
                "type": "open_ports",
                "count": len(data["open_ports"]),
                "details": f"Found {len(data['open_ports'])} open ports"
            })

        return findings

    def _extract_scanner_findings(self, data: Dict) -> List[Dict]:
        """Extract scanner findings"""
        findings: List[Dict] = []

        if data.get("services"):
            findings.append({
                "type": "services_detected",
                "count": len(data["services"]),
                "details": f"Identified {len(data['services'])} running services"
            })

        return findings

    def _extract_vuln_findings(self, data: Dict) -> List[Dict]:
        """Extract vulnerability findings"""
        return data.get("vulnerabilities", [])[:10]  # Top 10

    def _extract_cred_findings(self, data: Dict) -> List[Dict]:
        """Extract credential testing findings"""
        findings: List[Dict] = []
        findings.extend(data.get("default_credentials", []))
        findings.extend(data.get("weak_credentials", []))
        return findings

    def _extract_threat_findings(self, data: Dict) -> List[Dict]:
        """Extract threat detection findings"""
        return data.get("threats_detected", [])[:10]

    def _extract_hardening_findings(self, data: Dict) -> List[Dict]:
        """Extract hardening findings"""
        return data.get("findings", [])[:10]

    def _generate_html_report(self, report: Dict) -> str:
        """
        Generate HTML format report (XSS-safe).

        Args:
            report: Full report dict with all sections populated.

        Returns:
            HTML string with escaped user-supplied content.
        """
        esc = html_module.escape  # Shorthand for readability

        target = esc(str(report['metadata']['target']))
        generated_at = esc(str(report['metadata']['generated_at']))

        # ENHANCED: safe access to executive_summary with fallbacks
        exec_summary = report.get('executive_summary') or {}
        risk_level = esc(str(exec_summary.get('overall_risk_level', 'Unknown')))
        risk_class = esc(risk_level.lower())
        total_findings = int(report.get('findings_overview', {}).get('total_findings', 0))

        critical_findings = int(exec_summary.get('critical_findings', 0))
        high_findings = int(exec_summary.get('high_findings', 0))
        medium_findings = int(exec_summary.get('medium_findings', 0))
        low_findings = int(exec_summary.get('low_findings', 0))

        # Build recommendation list items (escaped)
        rec_items = ""
        for rec in (report.get('recommendations') or [])[:10]:
            priority = esc(str(rec.get('priority', '')).upper())
            recommendation = esc(str(rec.get('recommendation', '')))
            rec_items += f"<li><strong>{priority}:</strong> {recommendation}</li>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Assessment Report - {target}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        .critical {{ color: #d32f2f; font-weight: bold; }}
        .high {{ color: #f57c00; font-weight: bold; }}
        .medium {{ color: #fbc02d; }}
        .low {{ color: #388e3c; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Security Assessment Report</h1>
    <p><strong>Target:</strong> {target}</p>
    <p><strong>Generated:</strong> {generated_at}</p>
    
    <h2>Executive Summary</h2>
    <p><strong>Overall Risk:</strong> <span class="{risk_class}">{risk_level}</span></p>
    <p><strong>Total Findings:</strong> {total_findings}</p>
    
    <h2>Findings Overview</h2>
    <table>
        <tr>
            <th>Severity</th>
            <th>Count</th>
        </tr>
        <tr>
            <td class="critical">Critical</td>
            <td>{critical_findings}</td>
        </tr>
        <tr>
            <td class="high">High</td>
            <td>{high_findings}</td>
        </tr>
        <tr>
            <td class="medium">Medium</td>
            <td>{medium_findings}</td>
        </tr>
        <tr>
            <td class="low">Low</td>
            <td>{low_findings}</td>
        </tr>
    </table>
    
    <h2>Recommendations</h2>
    <ol>
        {rec_items}
    </ol>
</body>
</html>
"""
        return html

    def _generate_markdown_report(self, report: Dict) -> str:
        """
        Generate Markdown format report.

        Args:
            report: Full report dict with all sections populated.

        Returns:
            Markdown-formatted string.
        """
        # ENHANCED: safe access to executive_summary with fallbacks
        exec_summary = report.get('executive_summary') or {}
        recommendations = report.get('recommendations') or []
        findings_overview = report.get('findings_overview') or {}
        key_concerns = exec_summary.get('key_concerns', [])

        md = f"""# Security Assessment Report

## Metadata
- **Target:** {report['metadata']['target']}
- **Generated:** {report['metadata']['generated_at']}
- **Report ID:** {report['metadata']['report_id']}

## Executive Summary

**Overall Risk Level:** {exec_summary.get('overall_risk_level', 'Unknown')}

### Findings Summary
- **Critical:** {exec_summary.get('critical_findings', 0)}
- **High:** {exec_summary.get('high_findings', 0)}
- **Medium:** {exec_summary.get('medium_findings', 0)}
- **Low:** {exec_summary.get('low_findings', 0)}

### Key Concerns
{"".join([f"- {concern}\n" for concern in key_concerns])}

## Recommendations

{"".join([f"{i+1}. **{rec.get('priority', 'medium').upper()}:** {rec.get('recommendation', '')}\n" for i, rec in enumerate(recommendations[:10])])}

## Detailed Findings

Total findings across all agents: {findings_overview.get('total_findings', 0)}

---
*Report generated by Sentinel AI Security Platform v2.0*
"""
        return md
