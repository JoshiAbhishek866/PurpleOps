"""
Dashboard Reporter Agent — ENHANCED v2.0
Real-time metrics and visualization data for frontend dashboard

Changes from v1.0:
  - Replaced datetime.utcnow() with datetime.now(timezone.utc)
  - Added uuid4-based alert IDs instead of sequential counters
  - Added structured JSON-compatible logging throughout
  - Added try/except guards with specific exception types in execute()
  - Added input validation on execute() parameters
  - Added _safe_get_data() helper for defensive dict access
  - Added historical trend computation from metrics cache
  - Added ENHANCED v2.0 markers on all new additions
  - Preserved ALL existing functionality and APIs
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone

from src.agents.base_agent import BaseAgent

# ENHANCED: structured logger
_logger = logging.getLogger(__name__)


class DashboardReporterAgent(BaseAgent):
    """
    Dashboard Reporter Agent — ENHANCED v2.0

    Capabilities:
    - Real-time metrics aggregation
    - Visualization data formatting
    - WebSocket updates
    - Chart data generation
    - Historical trends
    - Alert formatting
    - Performance metrics

    ENHANCED v2.0 additions:
    - Timezone-aware timestamps (UTC)
    - UUID-based alert identifiers
    - Input validation and structured error handling
    - Defensive data access helpers
    - Configurable max_alerts parameter
    - Historical trend computation from metrics cache
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("dashboard_reporter", config)
        self.default_config = {
            "timeout": 60,
            "update_interval": 5,  # seconds
            "history_retention": 24,  # hours
            "enable_websocket": True,
            "chart_types": ["line", "bar", "pie", "gauge"],
            "max_alerts": 10,  # ENHANCED: configurable alert cap
        }
        self.config = {**self.default_config, **(config or {})}

        # Metrics cache
        self.metrics_cache: Dict[str, Dict] = {}
        self.history: List[Dict] = []

    # ── ENHANCED: defensive data accessor ────────────────────────────────────

    @staticmethod
    def _safe_get_data(result: Any) -> Dict:
        """ENHANCED: safely extract the 'data' dict from an agent result."""
        if not isinstance(result, dict):
            return {}
        data = result.get("data")
        if not isinstance(data, dict):
            return {}
        return data

    # ── Core execution ───────────────────────────────────────────────────────

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """Generate dashboard report"""

        # ENHANCED: input validation
        if not target or not isinstance(target, str):
            _logger.warning(json.dumps({
                "event": "dashboard_invalid_target",
                "target": str(target),
            }))
            return {"error": "target must be a non-empty string"}

        self.logger.progress("Generating dashboard report...")

        # Get all agent results from options
        agent_results = options.get("agent_results", {}) if options else {}

        # ENHANCED: guard each section so one failure doesn't abort the report
        try:
            overview = self._generate_overview(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "overview_generation_failed", "error": str(exc)}))
            overview = {"error": str(exc)}

        try:
            metrics = self._generate_metrics(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "metrics_generation_failed", "error": str(exc)}))
            metrics = {"error": str(exc)}

        try:
            charts = self._generate_charts(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "charts_generation_failed", "error": str(exc)}))
            charts = {"error": str(exc)}

        try:
            alerts = self._generate_alerts(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "alerts_generation_failed", "error": str(exc)}))
            alerts = []

        try:
            timeline = self._generate_timeline(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "timeline_generation_failed", "error": str(exc)}))
            timeline = []

        try:
            statistics = self._generate_statistics(agent_results)
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "statistics_generation_failed", "error": str(exc)}))
            statistics = {"error": str(exc)}

        try:
            trends = self._generate_trends()
        except (KeyError, TypeError, ValueError) as exc:
            _logger.error(json.dumps({"event": "trends_generation_failed", "error": str(exc)}))
            trends = {"error": str(exc)}

        # Generate dashboard data
        dashboard_data = {
            "metadata": {
                "target": target,
                # ENHANCED: timezone-aware UTC timestamp
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "update_interval": self.config["update_interval"]
            },
            "overview": overview,
            "metrics": metrics,
            "charts": charts,
            "alerts": alerts,
            "timeline": timeline,
            "statistics": statistics,
            "trends": trends,
        }

        # Cache metrics
        if isinstance(metrics, dict) and "error" not in metrics:
            self._cache_metrics(metrics)

        self.logger.success("Dashboard report generated")

        # ENHANCED: structured log
        _logger.info(json.dumps({
            "event": "dashboard_report_generated",
            "target": target,
            "sections": list(dashboard_data.keys()),
        }))

        return dashboard_data

    def _generate_overview(self, agent_results: Dict) -> Dict:
        """Generate overview section"""

        total_findings = 0
        critical_count = 0
        high_count = 0
        agents_executed = len(agent_results)

        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)

            # Count findings
            if "vulnerabilities" in data:
                total_findings += len(data["vulnerabilities"])
                critical_count += len([v for v in data["vulnerabilities"] if v.get("cvss_score", 0) >= 9.0])
                high_count += len([v for v in data["vulnerabilities"] if 7.0 <= v.get("cvss_score", 0) < 9.0])

            if "threats_detected" in data:
                total_findings += len(data["threats_detected"])
                critical_count += len([t for t in data["threats_detected"] if t.get("severity") == "critical"])

            if "findings" in data:
                total_findings += len(data["findings"])

        # Calculate risk score
        risk_score = min(100, (critical_count * 10 + high_count * 5))

        return {
            "total_findings": total_findings,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "agents_executed": agents_executed,
            "risk_score": risk_score,
            "risk_level": self._calculate_risk_level(risk_score),
            # ENHANCED: timezone-aware UTC timestamp
            "last_scan": datetime.now(timezone.utc).isoformat()
        }

    def _generate_metrics(self, agent_results: Dict) -> Dict:
        """Generate key metrics"""

        metrics: Dict[str, Any] = {
            "security_posture": {
                "score": 0,
                "trend": "stable",
                "change": 0
            },
            "vulnerability_count": {
                "total": 0,
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            },
            "threat_count": {
                "total": 0,
                "active": 0,
                "mitigated": 0
            },
            "compliance_score": {
                "percentage": 0,
                "frameworks": {}
            },
            "incident_count": {
                "total": 0,
                "open": 0,
                "resolved": 0
            }
        }

        # Calculate metrics from agent results
        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)

            # Vulnerabilities
            if "vulnerabilities" in data:
                vulns = data["vulnerabilities"]
                metrics["vulnerability_count"]["total"] = len(vulns)

                for vuln in vulns:
                    cvss = vuln.get("cvss_score", 0)
                    if cvss >= 9.0:
                        metrics["vulnerability_count"]["by_severity"]["critical"] += 1
                    elif cvss >= 7.0:
                        metrics["vulnerability_count"]["by_severity"]["high"] += 1
                    elif cvss >= 4.0:
                        metrics["vulnerability_count"]["by_severity"]["medium"] += 1
                    else:
                        metrics["vulnerability_count"]["by_severity"]["low"] += 1

            # Threats
            if "threats_detected" in data:
                metrics["threat_count"]["total"] = len(data["threats_detected"])
                metrics["threat_count"]["active"] = len(data["threats_detected"])

            # Compliance
            if "compliance_results" in data:
                for framework, result in data["compliance_results"].items():
                    metrics["compliance_score"]["frameworks"][framework] = result.get("compliance_percentage", 0)

                # Average compliance
                if metrics["compliance_score"]["frameworks"]:
                    metrics["compliance_score"]["percentage"] = sum(
                        metrics["compliance_score"]["frameworks"].values()
                    ) / len(metrics["compliance_score"]["frameworks"])

            # Incidents
            if "incidents" in data:
                metrics["incident_count"]["total"] = len(data["incidents"])
                metrics["incident_count"]["open"] = len([i for i in data["incidents"] if i.get("status") == "open"])

        # Calculate security posture score
        metrics["security_posture"]["score"] = self._calculate_security_posture(metrics)

        return metrics

    def _generate_charts(self, agent_results: Dict) -> Dict:
        """Generate chart data"""

        charts = {
            "vulnerability_distribution": self._chart_vuln_distribution(agent_results),
            "risk_timeline": self._chart_risk_timeline(),
            "compliance_radar": self._chart_compliance_radar(agent_results),
            "threat_heatmap": self._chart_threat_heatmap(agent_results),
            "agent_execution": self._chart_agent_execution(agent_results)
        }

        return charts

    def _chart_vuln_distribution(self, agent_results: Dict) -> Dict:
        """Vulnerability distribution pie chart"""

        distribution = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)
            if "vulnerabilities" in data:
                for vuln in data["vulnerabilities"]:
                    cvss = vuln.get("cvss_score", 0)
                    if cvss >= 9.0:
                        distribution["critical"] += 1
                    elif cvss >= 7.0:
                        distribution["high"] += 1
                    elif cvss >= 4.0:
                        distribution["medium"] += 1
                    else:
                        distribution["low"] += 1

        return {
            "type": "pie",
            "labels": ["Critical", "High", "Medium", "Low"],
            "data": [
                distribution["critical"],
                distribution["high"],
                distribution["medium"],
                distribution["low"]
            ],
            "colors": ["#d32f2f", "#f57c00", "#fbc02d", "#388e3c"]
        }

    def _chart_risk_timeline(self) -> Dict:
        """Risk score timeline"""

        # Generate last 24 hours of data points
        # ENHANCED: timezone-aware UTC timestamp
        now = datetime.now(timezone.utc)
        labels: List[str] = []
        data: List[int] = []

        for i in range(24, 0, -1):
            time_point = now - timedelta(hours=i)
            labels.append(time_point.strftime("%H:%M"))
            # Simulated data - in production, use actual historical data
            data.append(50 + (i % 10) * 5)

        return {
            "type": "line",
            "labels": labels,
            "datasets": [{
                "label": "Risk Score",
                "data": data,
                "borderColor": "#f57c00",
                "fill": False
            }]
        }

    def _chart_compliance_radar(self, agent_results: Dict) -> Dict:
        """Compliance radar chart"""

        compliance_scores: Dict[str, float] = {}

        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)
            if "compliance_results" in data:
                for framework, result in data["compliance_results"].items():
                    compliance_scores[framework] = result.get("compliance_percentage", 0)

        return {
            "type": "radar",
            "labels": list(compliance_scores.keys()),
            "datasets": [{
                "label": "Compliance Score",
                "data": list(compliance_scores.values()),
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgb(54, 162, 235)"
            }]
        }

    def _chart_threat_heatmap(self, agent_results: Dict) -> Dict:
        """Threat detection heatmap"""

        threat_counts: Dict[str, int] = {}

        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)
            if "threats_detected" in data:
                for threat in data["threats_detected"]:
                    threat_type = threat.get("type", "unknown")
                    threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

        return {
            "type": "bar",
            "labels": list(threat_counts.keys()),
            "datasets": [{
                "label": "Threat Count",
                "data": list(threat_counts.values()),
                "backgroundColor": "#f57c00"
            }]
        }

    def _chart_agent_execution(self, agent_results: Dict) -> Dict:
        """Agent execution status"""

        agents: List[str] = []
        statuses: List[int] = []
        colors: List[str] = []

        for agent_type, result in agent_results.items():
            agents.append(agent_type)
            status = result.get("status", "unknown")
            statuses.append(1 if status == "success" else 0)
            colors.append("#4caf50" if status == "success" else "#f44336")

        return {
            "type": "bar",
            "labels": agents,
            "datasets": [{
                "label": "Execution Status",
                "data": statuses,
                "backgroundColor": colors
            }]
        }

    def _generate_alerts(self, agent_results: Dict) -> List[Dict]:
        """Generate formatted alerts"""

        alerts: List[Dict] = []

        for agent_type, result in agent_results.items():
            data = self._safe_get_data(result)

            # Critical vulnerabilities
            if "vulnerabilities" in data:
                critical_vulns = [v for v in data["vulnerabilities"] if v.get("cvss_score", 0) >= 9.0]
                if critical_vulns:
                    alerts.append({
                        # ENHANCED: uuid4-based alert ID
                        "id": f"alert-vuln-{uuid.uuid4().hex[:12]}",
                        "type": "critical",
                        "title": f"{len(critical_vulns)} Critical Vulnerabilities",
                        "message": "Immediate patching required",
                        "source": agent_type,
                        # ENHANCED: timezone-aware UTC timestamp
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_required": True
                    })

            # Active threats
            if "threats_detected" in data:
                high_threats = [t for t in data["threats_detected"] if t.get("severity") == "high"]
                if high_threats:
                    alerts.append({
                        # ENHANCED: uuid4-based alert ID
                        "id": f"alert-threat-{uuid.uuid4().hex[:12]}",
                        "type": "warning",
                        "title": f"{len(high_threats)} Active Threats",
                        "message": "Investigation required",
                        "source": agent_type,
                        # ENHANCED: timezone-aware UTC timestamp
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "action_required": True
                    })

            # Compliance failures
            if "compliance_results" in data:
                for framework, result in data["compliance_results"].items():
                    if result.get("compliance_percentage", 100) < 70:
                        alerts.append({
                            # ENHANCED: uuid4-based alert ID
                            "id": f"alert-compliance-{uuid.uuid4().hex[:12]}",
                            "type": "info",
                            "title": f"{framework.upper()} Compliance Low",
                            "message": f"Only {result['compliance_percentage']:.1f}% compliant",
                            "source": agent_type,
                            # ENHANCED: timezone-aware UTC timestamp
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "action_required": False
                        })

        # ENHANCED: configurable max_alerts
        max_alerts = int(self.config.get("max_alerts", 10))
        return alerts[:max_alerts]

    def _generate_timeline(self, agent_results: Dict) -> List[Dict]:
        """Generate event timeline"""

        timeline: List[Dict] = []

        for agent_type, result in agent_results.items():
            timeline.append({
                # ENHANCED: timezone-aware UTC timestamp fallback
                "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "event": f"{agent_type} execution",
                "status": result.get("status", "unknown"),
                "duration": result.get("data", {}).get("duration", 0)
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)

        return timeline

    def _generate_statistics(self, agent_results: Dict) -> Dict:
        """Generate statistical summary"""

        return {
            "total_scans": len(agent_results),
            "successful_scans": len([r for r in agent_results.values() if r.get("status") == "success"]),
            "failed_scans": len([r for r in agent_results.values() if r.get("status") == "failed"]),
            "average_duration": self._calculate_average_duration(agent_results),
            "total_findings": self._count_total_findings(agent_results)
        }

    def _generate_trends(self) -> Dict:
        """Generate trend analysis.

        ENHANCED v2.0: computes directional trends from the metrics cache
        when sufficient history exists, otherwise returns defaults.
        """

        # ENHANCED: derive trends from cached history when available
        if len(self.metrics_cache) >= 2:
            try:
                sorted_keys = sorted(self.metrics_cache.keys())
                oldest = self.metrics_cache[sorted_keys[0]]
                newest = self.metrics_cache[sorted_keys[-1]]

                def _direction(old_val: float, new_val: float) -> str:
                    if new_val > old_val:
                        return "increasing"
                    elif new_val < old_val:
                        return "decreasing"
                    return "stable"

                vuln_old = oldest.get("vulnerability_count", {}).get("total", 0)
                vuln_new = newest.get("vulnerability_count", {}).get("total", 0)
                comp_old = oldest.get("compliance_score", {}).get("percentage", 0)
                comp_new = newest.get("compliance_score", {}).get("percentage", 0)
                threat_old = oldest.get("threat_count", {}).get("total", 0)
                threat_new = newest.get("threat_count", {}).get("total", 0)

                return {
                    "vulnerability_trend": _direction(vuln_old, vuln_new),
                    "compliance_trend": _direction(comp_old, comp_new),
                    "threat_trend": _direction(threat_old, threat_new),
                    "risk_trend": _direction(vuln_old + threat_old, vuln_new + threat_new),
                    "data_points": len(self.metrics_cache),  # ENHANCED: expose cache size
                }
            except (KeyError, TypeError, IndexError):
                pass  # fall through to defaults

        return {
            "vulnerability_trend": "increasing",
            "compliance_trend": "stable",
            "threat_trend": "decreasing",
            "risk_trend": "stable"
        }

    def _calculate_risk_level(self, risk_score: int) -> str:
        """Calculate risk level from score"""
        if risk_score >= 80:
            return "critical"
        elif risk_score >= 60:
            return "high"
        elif risk_score >= 40:
            return "medium"
        else:
            return "low"

    def _calculate_security_posture(self, metrics: Dict) -> int:
        """Calculate overall security posture score"""

        # Start with 100
        score = 100

        # Deduct for vulnerabilities
        vuln_count = metrics["vulnerability_count"]
        score -= vuln_count["by_severity"]["critical"] * 10
        score -= vuln_count["by_severity"]["high"] * 5
        score -= vuln_count["by_severity"]["medium"] * 2

        # Deduct for threats
        score -= metrics["threat_count"]["active"] * 5

        # Add for compliance
        score += metrics["compliance_score"]["percentage"] * 0.2

        return max(0, min(100, int(score)))

    def _calculate_average_duration(self, agent_results: Dict) -> float:
        """Calculate average execution duration"""
        durations: List[float] = []

        for result in agent_results.values():
            duration = result.get("data", {}).get("duration", 0)
            if duration:
                durations.append(duration)

        return sum(durations) / len(durations) if durations else 0

    def _count_total_findings(self, agent_results: Dict) -> int:
        """Count total findings across all agents"""
        total = 0

        for result in agent_results.values():
            data = self._safe_get_data(result)
            total += len(data.get("vulnerabilities", []))
            total += len(data.get("threats_detected", []))
            total += len(data.get("findings", []))

        return total

    def _cache_metrics(self, metrics: Dict) -> None:
        """Cache metrics for historical tracking"""
        # ENHANCED: timezone-aware UTC timestamp
        self.metrics_cache[datetime.now(timezone.utc).isoformat()] = metrics

        # Keep only last configured retention period
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.config["history_retention"])
        self.metrics_cache = {
            k: v for k, v in self.metrics_cache.items()
            if datetime.fromisoformat(k) > cutoff
        }
