"""
Agent Benchmark Framework for PurpleOps

Runs agents against known-vulnerable applications and scores results.
Provides measurable metrics: detection rate, false positive rate,
defense effectiveness, and time-to-detect.

Cost-optimized: uses local Docker containers for vulnerable apps.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== Benchmark Targets ====================
# Known vulnerable applications that can be run locally in Docker

BENCHMARK_TARGETS = {
    "dvwa": {
        "name": "Damn Vulnerable Web Application",
        "docker_image": "vulnerables/web-dvwa",
        "port": 80,
        "known_vulns": [
            {"type": "SQL Injection", "location": "/vulnerabilities/sqli/", "severity": "HIGH"},
            {"type": "XSS (Reflected)", "location": "/vulnerabilities/xss_r/", "severity": "HIGH"},
            {"type": "XSS (Stored)", "location": "/vulnerabilities/xss_s/", "severity": "HIGH"},
            {"type": "Command Injection", "location": "/vulnerabilities/exec/", "severity": "CRITICAL"},
            {"type": "File Upload", "location": "/vulnerabilities/upload/", "severity": "HIGH"},
            {"type": "CSRF", "location": "/vulnerabilities/csrf/", "severity": "MEDIUM"},
            {"type": "File Inclusion", "location": "/vulnerabilities/fi/", "severity": "HIGH"},
            {"type": "Brute Force", "location": "/vulnerabilities/brute/", "severity": "MEDIUM"},
        ],
        "url_template": "http://localhost:{port}",
    },
    "juice_shop": {
        "name": "OWASP Juice Shop",
        "docker_image": "bkimminich/juice-shop",
        "port": 3000,
        "known_vulns": [
            {"type": "SQL Injection", "location": "/rest/products/search", "severity": "HIGH"},
            {"type": "XSS (DOM)", "location": "/#/search", "severity": "HIGH"},
            {"type": "Broken Authentication", "location": "/rest/user/login", "severity": "CRITICAL"},
            {"type": "Sensitive Data Exposure", "location": "/ftp/", "severity": "HIGH"},
            {"type": "Security Misconfiguration", "location": "/api-docs/", "severity": "MEDIUM"},
        ],
        "url_template": "http://localhost:{port}",
    },
    "webgoat": {
        "name": "OWASP WebGoat",
        "docker_image": "webgoat/webgoat",
        "port": 8080,
        "known_vulns": [
            {"type": "SQL Injection", "location": "/SqlInjection/", "severity": "HIGH"},
            {"type": "XSS", "location": "/CrossSiteScripting/", "severity": "HIGH"},
            {"type": "Insecure Deserialization", "location": "/InsecureDeserialization/", "severity": "CRITICAL"},
            {"type": "XXE", "location": "/XXE/", "severity": "HIGH"},
            {"type": "Broken Access Control", "location": "/MissingFunctionAC/", "severity": "HIGH"},
        ],
        "url_template": "http://localhost:{port}/WebGoat",
    },
}


class BenchmarkResult:
    """Stores the result of a single benchmark run."""

    def __init__(self, target_name: str, known_vulns: List[Dict]):
        self.target_name = target_name
        self.known_vulns = known_vulns
        self.found_vulns: List[Dict] = []
        self.false_positives: List[Dict] = []
        self.defenses_applied: List[Dict] = []
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None

    def add_finding(self, vuln_type: str, location: str, is_true_positive: bool = True):
        """Record a vulnerability finding."""
        entry = {"type": vuln_type, "location": location, "timestamp": datetime.utcnow().isoformat()}
        if is_true_positive:
            self.found_vulns.append(entry)
        else:
            self.false_positives.append(entry)

    def add_defense(self, action: str, target_vuln: str, effective: bool):
        """Record a defensive action."""
        self.defenses_applied.append({
            "action": action,
            "target_vuln": target_vuln,
            "effective": effective,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def finalize(self):
        """Mark the benchmark as complete and compute metrics."""
        self.end_time = time.time()

    @property
    def metrics(self) -> Dict:
        """Compute benchmark metrics."""
        total_known = len(self.known_vulns)
        total_found = len(self.found_vulns)
        total_fp = len(self.false_positives)
        total_defenses = len(self.defenses_applied)
        effective_defenses = sum(1 for d in self.defenses_applied if d["effective"])

        detection_rate = total_found / total_known if total_known > 0 else 0
        fp_rate = total_fp / (total_found + total_fp) if (total_found + total_fp) > 0 else 0
        defense_rate = effective_defenses / total_defenses if total_defenses > 0 else 0
        elapsed = (self.end_time or time.time()) - self.start_time

        return {
            "target": self.target_name,
            "detection_rate": round(detection_rate, 3),
            "false_positive_rate": round(fp_rate, 3),
            "defense_effectiveness": round(defense_rate, 3),
            "vulns_known": total_known,
            "vulns_found": total_found,
            "false_positives": total_fp,
            "defenses_applied": total_defenses,
            "defenses_effective": effective_defenses,
            "time_seconds": round(elapsed, 2),
            "timestamp": datetime.utcnow().isoformat(),
        }


class AgentBenchmark:
    """
    Benchmark framework for evaluating PurpleOps agents.

    Usage:
        bench = AgentBenchmark()
        result = await bench.run_benchmark("dvwa", red_agent, blue_agent)
        print(result.metrics)
    """

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    async def run_benchmark(
        self,
        target_name: str,
        red_agent=None,
        blue_agent=None,
        orchestrator=None,
    ) -> BenchmarkResult:
        """
        Run a full benchmark against a known-vulnerable target.

        This simulates a campaign: Red attacks, Blue defends, metrics are scored.
        If actual agents aren't available, scores against the known vuln list.
        """
        target = BENCHMARK_TARGETS.get(target_name)
        if not target:
            raise ValueError(f"Unknown target: {target_name}. Available: {list(BENCHMARK_TARGETS.keys())}")

        result = BenchmarkResult(target_name, target["known_vulns"])

        # Run Red Agent against the target
        if red_agent:
            await self._run_red_benchmark(red_agent, target, result)
        else:
            # Score based on a simulated run
            self._simulate_red_benchmark(target, result)

        # Run Blue Agent against Red's findings
        if blue_agent and result.found_vulns:
            await self._run_blue_benchmark(blue_agent, result)
        else:
            self._simulate_blue_benchmark(result)

        result.finalize()
        self.results.append(result)
        logger.info(f"Benchmark '{target_name}' complete: {result.metrics}")
        return result

    async def _run_red_benchmark(self, red_agent, target: Dict, result: BenchmarkResult):
        """Run actual Red Agent against benchmark target."""
        target_url = target["url_template"].format(port=target["port"])
        try:
            target_info = {
                "url": target_url,
                "description": f"Benchmark: {target['name']}",
                "iam_role": "benchmark-role",
            }
            red_result = red_agent.execute_campaign(target_info)

            # Match findings against known vulns
            red_str = str(red_result).lower()
            for vuln in target["known_vulns"]:
                vuln_type = vuln["type"].lower()
                if vuln_type.split()[0] in red_str:  # Basic matching
                    result.add_finding(vuln["type"], vuln["location"], is_true_positive=True)
        except Exception as e:
            logger.error(f"Red benchmark failed: {e}")

    def _simulate_red_benchmark(self, target: Dict, result: BenchmarkResult):
        """Simulate Red Agent findings for benchmarking without a live agent."""
        # Assume agent finds common vuln types
        detectable_types = {"SQL Injection", "XSS", "XSS (Reflected)", "XSS (Stored)", "XSS (DOM)"}
        for vuln in target["known_vulns"]:
            if vuln["type"] in detectable_types or "injection" in vuln["type"].lower():
                result.add_finding(vuln["type"], vuln["location"], is_true_positive=True)

    async def _run_blue_benchmark(self, blue_agent, result: BenchmarkResult):
        """Run actual Blue Agent against Red's findings."""
        for finding in result.found_vulns:
            try:
                threat_info = {
                    "attack_type": finding["type"],
                    "target": finding["location"],
                    "details": f"Benchmark finding: {finding['type']}",
                }
                blue_result = blue_agent.respond_to_threat(threat_info)
                if blue_result and "status" in str(blue_result):
                    result.add_defense(
                        action=f"Responded to {finding['type']}",
                        target_vuln=finding["type"],
                        effective=True,
                    )
            except Exception as e:
                logger.error(f"Blue benchmark failed: {e}")
                result.add_defense(
                    action=f"Failed on {finding['type']}",
                    target_vuln=finding["type"],
                    effective=False,
                )

    def _simulate_blue_benchmark(self, result: BenchmarkResult):
        """Simulate Blue Agent defenses for benchmarking."""
        for finding in result.found_vulns:
            # Assume Blue can defend against SQL injection and XSS
            effective = any(t in finding["type"].lower() for t in ["sql", "xss", "injection"])
            result.add_defense(
                action=f"WAF rule for {finding['type']}",
                target_vuln=finding["type"],
                effective=effective,
            )

    # ==================== Run All ====================

    async def run_all_benchmarks(self, red_agent=None, blue_agent=None) -> Dict:
        """Run benchmarks against all known targets."""
        all_metrics = {}
        for target_name in BENCHMARK_TARGETS:
            result = await self.run_benchmark(target_name, red_agent, blue_agent)
            all_metrics[target_name] = result.metrics

        # Aggregate
        if all_metrics:
            avg_detection = sum(m["detection_rate"] for m in all_metrics.values()) / len(all_metrics)
            avg_fp = sum(m["false_positive_rate"] for m in all_metrics.values()) / len(all_metrics)
            avg_defense = sum(m["defense_effectiveness"] for m in all_metrics.values()) / len(all_metrics)
            all_metrics["aggregate"] = {
                "avg_detection_rate": round(avg_detection, 3),
                "avg_false_positive_rate": round(avg_fp, 3),
                "avg_defense_effectiveness": round(avg_defense, 3),
                "targets_tested": len(all_metrics),  # Aggregate key not yet added
            }

        return all_metrics

    # ==================== History ====================

    def get_history(self) -> List[Dict]:
        """Get all benchmark results as metrics."""
        return [r.metrics for r in self.results]

    def get_improvement_over_time(self) -> Dict:
        """Compare latest results with oldest results."""
        if len(self.results) < 2:
            return {"trend": "insufficient_data", "runs": len(self.results)}

        first = self.results[0].metrics
        latest = self.results[-1].metrics
        return {
            "first_detection_rate": first["detection_rate"],
            "latest_detection_rate": latest["detection_rate"],
            "detection_improvement": round(latest["detection_rate"] - first["detection_rate"], 3),
            "first_defense_rate": first["defense_effectiveness"],
            "latest_defense_rate": latest["defense_effectiveness"],
            "defense_improvement": round(latest["defense_effectiveness"] - first["defense_effectiveness"], 3),
            "total_runs": len(self.results),
        }
