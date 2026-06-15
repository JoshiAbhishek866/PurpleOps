"""
Threat Detection Agent — ENHANCED v2.0
Real-time threat monitoring and detection

Enhancements:
- Timezone-aware datetimes (datetime.now(timezone.utc))
- Structured JSON-compatible logging
- Input validation on all public methods
- try/except guards around regex and external calls
- uuid4-based correlation IDs
- Exponential backoff on continuous_monitoring failures
- Opt-in config for new features with sensible defaults
"""

import asyncio
import uuid
import re
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, timezone

from src.agents.base_agent import BaseAgent

# ENHANCED: module-level structured logger
_logger = logging.getLogger(__name__)


class ThreatDetectionAgent(BaseAgent):
    """
    Threat Detection Agent — ENHANCED v2.0

    Capabilities:
    - Log analysis
    - Anomaly detection
    - Pattern matching
    - Threat intelligence correlation
    - IOC (Indicators of Compromise) detection
    - Behavioral analysis
    - Alert generation

    ENHANCED v2.0 additions:
    - Timezone-aware timestamps throughout
    - Structured logging with JSON metadata
    - Input validation & type checking
    - Graceful error handling on all detection paths
    - Correlation IDs for tracing
    - Exponential backoff in continuous monitoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__("threat_detection", config)
        self.default_config = {
            "monitoring_interval": 60,  # seconds
            "alert_threshold": "medium",
            "log_sources": ["system", "application", "security"],
            "ioc_sources": ["known_malicious_ips", "malware_hashes"],
            "anomaly_sensitivity": 0.7,
            "max_alerts": 100,
            # ENHANCED: new opt-in config knobs
            "enable_structured_logging": True,
            "max_backoff_seconds": 300,
            "correlation_id_enabled": True,
        }
        self.config = {**self.default_config, **(config or {})}

        # Threat patterns
        self.threat_patterns = self._load_threat_patterns()

        # Known IOCs
        self.known_malicious_ips: set = set()
        self.known_malware_hashes: set = set()

        # Baseline for anomaly detection
        self.baseline: Dict[str, int] = {}

    # ENHANCED: helper for structured log entries
    def _structured_log(self, level: str, message: str, **kwargs: Any) -> None:
        """Emit a structured JSON-compatible log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "threat_detection",
            "level": level,
            "message": message,
            **kwargs,
        }
        if self.config.get("enable_structured_logging"):
            _logger.log(getattr(logging, level.upper(), logging.INFO), json.dumps(entry))

    async def execute(self, target: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute threat detection"""

        # ENHANCED: input validation
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty string")

        self.logger.progress("Starting threat detection...")

        # ENHANCED: correlation ID for this run
        correlation_id = str(uuid.uuid4()) if self.config.get("correlation_id_enabled") else None
        self._structured_log("info", "Threat detection started", target=target, correlation_id=correlation_id)

        # Get monitoring data from options
        logs = options.get("logs", []) if options else []
        network_traffic = options.get("network_traffic", []) if options else []
        system_events = options.get("system_events", []) if options else []

        # Perform threat detection
        results: Dict[str, Any] = {
            "target": target,
            "monitoring_period": self.config["monitoring_interval"],
            "threats_detected": [],
            "anomalies": [],
            "ioc_matches": [],
            "alerts": [],
            "risk_level": "low",
            # ENHANCED: correlation id in results
            "correlation_id": correlation_id,
        }

        # Analyze logs
        if logs:
            try:
                log_threats = await self.analyze_logs(logs)
                results["threats_detected"].extend(log_threats)
            except (re.error, TypeError, ValueError) as exc:
                self._structured_log("error", "Log analysis failed", error=str(exc))

        # Detect anomalies
        if system_events:
            try:
                anomalies = await self.detect_anomalies(system_events)
                results["anomalies"].extend(anomalies)
            except (TypeError, ValueError, KeyError) as exc:
                self._structured_log("error", "Anomaly detection failed", error=str(exc))

        # Check for IOCs
        if network_traffic:
            try:
                iocs = await self.check_iocs(network_traffic)
                results["ioc_matches"].extend(iocs)
            except (TypeError, KeyError) as exc:
                self._structured_log("error", "IOC check failed", error=str(exc))

        # Pattern matching
        try:
            all_data = logs + system_events
            pattern_matches = await self.pattern_matching(all_data)
            results["threats_detected"].extend(pattern_matches)
        except (re.error, TypeError, ValueError) as exc:
            self._structured_log("error", "Pattern matching failed", error=str(exc))

        # Generate alerts
        results["alerts"] = self._generate_alerts(results)

        # Calculate risk level
        results["risk_level"] = self._calculate_risk_level(results)

        # Summary
        results["summary"] = {
            "total_threats": len(results["threats_detected"]),
            "total_anomalies": len(results["anomalies"]),
            "total_iocs": len(results["ioc_matches"]),
            "total_alerts": len(results["alerts"]),
            "risk_level": results["risk_level"]
        }

        self.logger.success(
            f"Threat detection completed: {results['summary']['total_threats']} threats found"
        )
        self._structured_log("info", "Threat detection completed", summary=results["summary"], correlation_id=correlation_id)

        return results

    async def analyze_logs(self, logs: List[str]) -> List[Dict[str, Any]]:
        """Analyze logs for threats"""
        # ENHANCED: input validation
        if not isinstance(logs, list):
            raise TypeError("logs must be a list of strings")

        self.logger.progress("Analyzing logs...")

        threats: List[Dict[str, Any]] = []

        for log_entry in logs:
            # Check for suspicious patterns
            for pattern_name, pattern in self.threat_patterns.items():
                try:
                    if re.search(pattern, log_entry, re.IGNORECASE):
                        threats.append({
                            "type": "log_pattern",
                            "pattern": pattern_name,
                            "log_entry": log_entry[:200],  # Truncate
                            "severity": self._get_pattern_severity(pattern_name),
                            # ENHANCED: timezone-aware timestamp
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                except re.error as exc:
                    self._structured_log("warning", "Regex error in log analysis", pattern=pattern_name, error=str(exc))

        return threats

    async def detect_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in system events"""
        # ENHANCED: input validation
        if not isinstance(events, list):
            raise TypeError("events must be a list of dicts")

        self.logger.progress("Detecting anomalies...")

        anomalies: List[Dict[str, Any]] = []

        # Analyze event frequency
        event_counts: Dict[str, int] = {}
        for event in events:
            event_type = event.get("type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Check against baseline
        for event_type, count in event_counts.items():
            baseline_count = self.baseline.get(event_type, count)

            # Detect significant deviation
            if baseline_count > 0 and count > baseline_count * (1 + self.config["anomaly_sensitivity"]):
                anomalies.append({
                    "type": "frequency_anomaly",
                    "event_type": event_type,
                    "current_count": count,
                    "baseline_count": baseline_count,
                    "deviation": f"{((count - baseline_count) / baseline_count * 100):.1f}%",
                    "severity": "medium",
                    # ENHANCED: timezone-aware timestamp
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Update baseline
        self.baseline.update(event_counts)

        # Check for unusual time patterns
        time_anomalies = self._detect_time_anomalies(events)
        anomalies.extend(time_anomalies)

        return anomalies

    def _detect_time_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect unusual time-based patterns"""
        anomalies: List[Dict[str, Any]] = []

        # Group events by hour
        hour_counts: Dict[int, int] = {}
        for event in events:
            timestamp = event.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except (ValueError, TypeError):
                    pass

        # Detect activity during unusual hours (e.g., 2-5 AM)
        unusual_hours = [2, 3, 4, 5]
        for hour in unusual_hours:
            if hour_counts.get(hour, 0) > 10:  # Threshold
                anomalies.append({
                    "type": "time_anomaly",
                    "description": f"Unusual activity during hour {hour}:00",
                    "event_count": hour_counts[hour],
                    "severity": "medium",
                    # ENHANCED: timezone-aware timestamp
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        return anomalies

    async def check_iocs(self, network_traffic: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for Indicators of Compromise"""
        # ENHANCED: input validation
        if not isinstance(network_traffic, list):
            raise TypeError("network_traffic must be a list of dicts")

        self.logger.progress("Checking for IOCs...")

        ioc_matches: List[Dict[str, Any]] = []

        for traffic in network_traffic:
            # Check IP addresses
            src_ip = traffic.get("src_ip")
            dst_ip = traffic.get("dst_ip")

            if src_ip in self.known_malicious_ips:
                ioc_matches.append({
                    "type": "malicious_ip",
                    "ip": src_ip,
                    "direction": "source",
                    "severity": "high",
                    # ENHANCED: timezone-aware timestamp
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            if dst_ip in self.known_malicious_ips:
                ioc_matches.append({
                    "type": "malicious_ip",
                    "ip": dst_ip,
                    "direction": "destination",
                    "severity": "high",
                    # ENHANCED: timezone-aware timestamp
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            # Check for suspicious ports
            dst_port = traffic.get("dst_port")
            if dst_port in [4444, 5555, 6666, 31337]:  # Common backdoor ports
                ioc_matches.append({
                    "type": "suspicious_port",
                    "port": dst_port,
                    "dst_ip": dst_ip,
                    "severity": "medium",
                    # ENHANCED: timezone-aware timestamp
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        return ioc_matches

    async def pattern_matching(self, data: List[Any]) -> List[Dict[str, Any]]:
        """Match against known threat patterns"""
        self.logger.progress("Pattern matching...")

        matches: List[Dict[str, Any]] = []

        for entry in data:
            entry_str = str(entry)

            # ENHANCED: wrap each regex in try/except
            try:
                # SQL Injection patterns
                if re.search(r"(union.*select|select.*from|insert.*into|drop.*table)", entry_str, re.IGNORECASE):
                    matches.append({
                        "type": "sql_injection_attempt",
                        "data": entry_str[:200],
                        "severity": "high",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except re.error as exc:
                self._structured_log("warning", "Regex error in SQL injection check", error=str(exc))

            try:
                # XSS patterns
                if re.search(r"(<script|javascript:|onerror=|onload=)", entry_str, re.IGNORECASE):
                    matches.append({
                        "type": "xss_attempt",
                        "data": entry_str[:200],
                        "severity": "high",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except re.error as exc:
                self._structured_log("warning", "Regex error in XSS check", error=str(exc))

            try:
                # Command injection
                if re.search(r"(;.*rm\s|;.*cat\s|&&.*ls|`.*`|\$\(.*\))", entry_str):
                    matches.append({
                        "type": "command_injection_attempt",
                        "data": entry_str[:200],
                        "severity": "critical",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except re.error as exc:
                self._structured_log("warning", "Regex error in command injection check", error=str(exc))

            try:
                # Path traversal
                if re.search(r"(\.\./|\.\.\\|%2e%2e)", entry_str, re.IGNORECASE):
                    matches.append({
                        "type": "path_traversal_attempt",
                        "data": entry_str[:200],
                        "severity": "high",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except re.error as exc:
                self._structured_log("warning", "Regex error in path traversal check", error=str(exc))

        return matches

    def _load_threat_patterns(self) -> Dict[str, str]:
        """Load threat detection patterns"""
        return {
            "failed_login": r"(failed.*login|authentication.*failed|invalid.*credentials)",
            "brute_force": r"(multiple.*failed.*attempts|too many.*login)",
            "privilege_escalation": r"(sudo|su\s|privilege.*escalat)",
            "malware": r"(trojan|virus|malware|ransomware|backdoor)",
            "data_exfiltration": r"(large.*transfer|unusual.*download|data.*leak)",
            "port_scan": r"(port.*scan|nmap|masscan)",
            "ddos": r"(denial.*service|ddos|flood.*attack)",
            "unauthorized_access": r"(unauthorized.*access|access.*denied|permission.*denied)"
        }

    def _get_pattern_severity(self, pattern_name: str) -> str:
        """Get severity for pattern"""
        high_severity = ["malware", "privilege_escalation", "data_exfiltration", "ddos"]
        medium_severity = ["brute_force", "port_scan", "unauthorized_access"]

        if pattern_name in high_severity:
            return "high"
        elif pattern_name in medium_severity:
            return "medium"
        else:
            return "low"

    def _generate_alerts(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate security alerts"""
        alerts: List[Dict[str, Any]] = []

        # Critical threats
        critical_threats = [
            t for t in results["threats_detected"]
            if t.get("severity") == "critical"
        ]

        if critical_threats:
            alerts.append({
                "level": "critical",
                "title": f"{len(critical_threats)} Critical Threats Detected",
                "description": "Immediate action required",
                "threats": critical_threats[:5],  # Top 5
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # High severity
        high_threats = [
            t for t in results["threats_detected"]
            if t.get("severity") == "high"
        ]

        if len(high_threats) > 3:
            alerts.append({
                "level": "high",
                "title": f"{len(high_threats)} High-Severity Threats",
                "description": "Urgent investigation needed",
                "threats": high_threats[:5],
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # IOC matches
        if results["ioc_matches"]:
            alerts.append({
                "level": "high",
                "title": "Indicators of Compromise Detected",
                "description": f"{len(results['ioc_matches'])} IOCs found",
                "iocs": results["ioc_matches"][:5],
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        # Anomalies
        if len(results["anomalies"]) > 5:
            alerts.append({
                "level": "medium",
                "title": "Multiple Anomalies Detected",
                "description": f"{len(results['anomalies'])} anomalous patterns",
                "anomalies": results["anomalies"][:5],
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return alerts[:self.config["max_alerts"]]

    def _calculate_risk_level(self, results: Dict[str, Any]) -> str:
        """Calculate overall risk level"""
        score = 0

        # Count by severity
        for threat in results["threats_detected"]:
            severity = threat.get("severity", "low")
            if severity == "critical":
                score += 10
            elif severity == "high":
                score += 5
            elif severity == "medium":
                score += 2
            else:
                score += 1

        # IOCs are always high risk
        score += len(results["ioc_matches"]) * 5

        # Anomalies
        score += len(results["anomalies"]) * 2

        # Determine risk level
        if score >= 50:
            return "critical"
        elif score >= 20:
            return "high"
        elif score >= 10:
            return "medium"
        else:
            return "low"

    async def continuous_monitoring(
        self,
        target: str,
        duration: int = 3600,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Continuous threat monitoring

        Args:
            target: Target to monitor
            duration: Monitoring duration in seconds
            callback: Callback function for alerts

        ENHANCED v2.0: exponential backoff on errors, timezone-aware times
        """
        # ENHANCED: input validation
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty string")
        if duration <= 0:
            raise ValueError("duration must be a positive integer")

        self.logger.progress(f"Starting continuous monitoring for {duration}s...")

        # ENHANCED: timezone-aware start time
        start_time = datetime.now(timezone.utc)
        interval = self.config["monitoring_interval"]
        max_backoff = self.config.get("max_backoff_seconds", 300)
        consecutive_failures = 0

        while (datetime.now(timezone.utc) - start_time).total_seconds() < duration:
            try:
                # Perform detection
                result = await self.run(target)

                # Trigger callback if threats found
                if callback and result.get("data", {}).get("alerts"):
                    await callback(result)

                # ENHANCED: reset backoff on success
                consecutive_failures = 0

                # Wait for next interval
                await asyncio.sleep(interval)
            except (ConnectionError, TimeoutError, OSError) as exc:
                # ENHANCED: exponential backoff on transient errors
                consecutive_failures += 1
                backoff = min(interval * (2 ** consecutive_failures), max_backoff)
                self._structured_log(
                    "warning",
                    "Monitoring cycle failed, backing off",
                    error=str(exc),
                    backoff_seconds=backoff,
                    consecutive_failures=consecutive_failures,
                )
                await asyncio.sleep(backoff)

        self.logger.success("Continuous monitoring completed")
