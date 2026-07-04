"""
Report Generator Agent
AI-powered security findings summary and report generation
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json
import html as html_module

from src.agents.base_agent import BaseAgent


class ReportGeneratorAgent(BaseAgent):
    """
    Report Generator Agent
    
    Capabilities:
    - AI-powered summary generation
    - Executive summary
    - Technical details
    - Recommendations
    - PDF/HTML generation
    - Multiple report formats
    - Customizable templates
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
        """Generate comprehensive security report"""
        
        self.logger.progress("Generating security report...")
        
        # Get all agent results from options
        agent_results = options.get("agent_results", {}) if options else {}
        
        if not agent_results:
            self.logger.warning("No agent results provided for report generation")
            return {
                "error": "No results to generate report from",
                "status": "failed"
            }
        
        # Generate report sections
        report = {
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
            report["executive_summary"] = await self._generate_executive_summary(
                agent_results
            )
        
        # Findings Overview
        report["findings_overview"] = self._generate_findings_overview(agent_results)
        
        # Detailed Findings
        if self.config["include_technical_details"]:
            report["detailed_findings"] = self._generate_detailed_findings(agent_results)
        
        # Risk Assessment
        report["risk_assessment"] = self._generate_risk_assessment(agent_results)
        
        # Recommendations
        if self.config["include_recommendations"]:
            report["recommendations"] = self._generate_recommendations(agent_results)
        
        # Technical Appendix
        report["technical_appendix"] = self._generate_technical_appendix(agent_results)
        
        # Generate different formats
        for format_type in self.config["formats"]:
            if format_type == "json":
                report["formats"]["json"] = json.dumps(report, indent=2, default=str)
            elif format_type == "html":
                report["formats"]["html"] = self._generate_html_report(report)
            elif format_type == "markdown":
                report["formats"]["markdown"] = self._generate_markdown_report(report)
        
        self.logger.success("Security report generated successfully")
        
        return report
    
    def _generate_metadata(self, target: str) -> Dict:
        """Generate report metadata"""
        return {
            "report_id": f"RPT-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            "target": target,
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "Comprehensive Security Assessment",
            "version": "1.0"
        }
    
    async def _generate_executive_summary(self, agent_results: Dict) -> Dict:
        """Generate AI-powered executive summary"""
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
        
        summary = {
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
        """Generate overview of all findings"""
        overview = {
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
        """Generate detailed findings section"""
        detailed = {}
        
        for agent_type, result in agent_results.items():
            data = result.get("data", {})
            
            detailed[agent_type] = {
                "agent": agent_type,
                "status": result.get("status"),
                "duration": data.get("duration"),
                "findings": []
            }
            
            # Extract findings based on agent type
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
        
        return detailed
    
    def _generate_risk_assessment(self, agent_results: Dict) -> Dict:
        """Generate risk assessment"""
        risk_factors = []
        
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
        """Generate prioritized recommendations"""
        all_recommendations = []
        
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
        """Generate technical appendix"""
        return {
            "raw_results": agent_results,
            "methodology": "Multi-agent security assessment using offensive and defensive techniques",
            "tools_used": list(agent_results.keys()),
            "scan_parameters": "Comprehensive assessment with ethical testing controls"
        }
    
    def _extract_key_concerns(self, agent_results: Dict) -> List[str]:
        """Extract key security concerns"""
        concerns = []
        
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
        """Extract immediate action items"""
        actions = []
        
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
        findings = []
        
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
        findings = []
        
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
        findings = []
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
        """Generate HTML format report (XSS-safe)"""
        esc = html_module.escape  # Shorthand for readability
        
        target = esc(str(report['metadata']['target']))
        generated_at = esc(str(report['metadata']['generated_at']))
        risk_level = esc(str(report['executive_summary']['overall_risk_level']))
        risk_class = esc(risk_level.lower())
        total_findings = int(report['findings_overview']['total_findings'])
        
        # Build recommendation list items (escaped)
        rec_items = ""
        for rec in report['recommendations'][:10]:
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
            <td>{int(report['executive_summary']['critical_findings'])}</td>
        </tr>
        <tr>
            <td class="high">High</td>
            <td>{int(report['executive_summary']['high_findings'])}</td>
        </tr>
        <tr>
            <td class="medium">Medium</td>
            <td>{int(report['executive_summary']['medium_findings'])}</td>
        </tr>
        <tr>
            <td class="low">Low</td>
            <td>{int(report['executive_summary']['low_findings'])}</td>
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
        """Generate Markdown format report"""
        md = f"""# Security Assessment Report

## Metadata
- **Target:** {report['metadata']['target']}
- **Generated:** {report['metadata']['generated_at']}
- **Report ID:** {report['metadata']['report_id']}

## Executive Summary

**Overall Risk Level:** {report['executive_summary']['overall_risk_level']}

### Findings Summary
- **Critical:** {report['executive_summary']['critical_findings']}
- **High:** {report['executive_summary']['high_findings']}
- **Medium:** {report['executive_summary']['medium_findings']}
- **Low:** {report['executive_summary']['low_findings']}

### Key Concerns
{"".join([f"- {concern}\n" for concern in report['executive_summary']['key_concerns']])}

## Recommendations

{"".join([f"{i+1}. **{rec['priority'].upper()}:** {rec['recommendation']}\n" for i, rec in enumerate(report['recommendations'][:10])])}

## Detailed Findings

Total findings across all agents: {report['findings_overview']['total_findings']}

---
*Report generated by PurpleOps Security Platform*
"""
        return md
