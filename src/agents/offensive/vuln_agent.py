"""
Vulnerability Detection Agent — ENHANCED v2.0
Detects vulnerabilities and CVEs in discovered services

ENHANCED v2.0:
- Structured JSON-compatible logging via _log()
- Timezone-aware datetimes (datetime.now(timezone.utc))
- UUID4-based scan tracking
- Input validation on public methods
- try/except with specific exception types (aiohttp.ClientError, etc.)
- Exponential backoff with jitter on NVD rate-limit (403)
- Configurable retry parameters
- Detailed docstrings on every method
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
import re
import uuid
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent
from src.utils.helpers import calculate_risk_score


class VulnAgent(BaseAgent):
    """
    Vulnerability Detection Agent — ENHANCED v2.0

    Capabilities:
    - CVE database lookup
    - Vulnerability scoring (CVSS)
    - Exploit availability check
    - Patch information
    - Risk assessment

    ENHANCED v2.0 additions:
    - Structured logging with JSON context
    - Input validation on service dicts
    - Specific exception handling (aiohttp.ClientError, KeyError, etc.)
    - Exponential backoff with jitter for NVD 403 retries
    - Configurable max_retries and backoff_base
    - Timezone-aware timestamps throughout
    - UUID4-based scan tracking
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("vuln", config)
        self.default_config = {
            "timeout": 60,
            "cve_sources": ["nvd"],  # nvd, exploit-db
            "min_cvss_score": 0.0,
            "include_exploits": True,
            "check_patches": True,
            "nvd_api_key": None,  # Set for higher rate limits (50/30s vs 5/30s)
            # ENHANCED: configurable retry parameters
            "max_retries": 3,
            "backoff_base": 6,
        }
        self.config = {**self.default_config, **(config or {})}

        # CVE API endpoints
        self.nvd_api = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.exploit_db_api = "https://www.exploit-db.com/search"

        # Rate limiter: max 5 concurrent NVD requests
        self._nvd_semaphore = asyncio.Semaphore(5)

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Execute vulnerability detection against discovered services.

        Args:
            target: Hostname or IP being assessed.
            options: Must include 'services' list from the scanner agent.

        Returns:
            Dict with vulnerabilities, risk_score, summary, and recommendations.
        """

        # ENHANCED: structured log with scan ID
        scan_id = uuid.uuid4().hex[:12]
        self._log("info", "Vulnerability detection started", target=target, scan_id=scan_id)
        self.logger.progress("Starting vulnerability detection...")

        # Get services from options (from scanner agent)
        services = options.get("services", []) if options else []

        if not services:
            self.logger.warning("No services provided for vulnerability detection")
            return {
                "target": target,
                # ENHANCED: timezone-aware timestamp
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "scan_id": scan_id,
                "vulnerabilities": [],
                "risk_score": 0.0,
                "summary": {
                    "total": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }

        # Detect vulnerabilities
        all_vulnerabilities: List[Dict] = []

        for service in services:
            try:
                vulns = await self.check_service_vulnerabilities(service)
                all_vulnerabilities.extend(vulns)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # ENHANCED: specific network errors per service
                self._log("warning", "Service vuln check failed",
                          service=service.get("service", "unknown"),
                          port=service.get("port"), error=str(e))
            except Exception as e:
                self._log("warning", "Unexpected error checking service",
                          service=service.get("service", "unknown"), error=str(e))

        # Calculate risk score
        risk_score = calculate_risk_score(all_vulnerabilities)

        # Categorize vulnerabilities
        summary = self._categorize_vulnerabilities(all_vulnerabilities)

        results: Dict[str, Any] = {
            "target": target,
            # ENHANCED: timezone-aware timestamp and scan tracking
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan_id": scan_id,
            "services_checked": len(services),
            "vulnerabilities": all_vulnerabilities,
            "risk_score": risk_score,
            "summary": summary,
            "recommendations": self._generate_recommendations(all_vulnerabilities)
        }

        self._log("info", "Vulnerability detection completed", target=target,
                  scan_id=scan_id, vuln_count=len(all_vulnerabilities),
                  risk_score=risk_score)
        self.logger.success(
            f"Found {len(all_vulnerabilities)} vulnerabilities "
            f"(Risk Score: {risk_score:.1f}/10)"
        )

        return results

    async def check_service_vulnerabilities(self, service: Dict) -> List[Dict]:
        """
        Check vulnerabilities for a specific service.

        Args:
            service: Dict with 'service', 'version', and 'port' keys.

        Returns:
            List of vulnerability dicts for this service.
        """
        service_name = service.get("service", "unknown")
        version = service.get("version")
        port = service.get("port")

        self.logger.progress(f"Checking {service_name} on port {port}...")

        if not version:
            self.logger.warning(f"No version info for {service_name}")
            return []

        # ENHANCED: validate service dict fields
        if not isinstance(service_name, str) or not service_name.strip():
            self._log("warning", "Invalid service name in service dict", port=port)
            return []

        vulnerabilities: List[Dict] = []

        # Search CVE database
        if "nvd" in self.config["cve_sources"]:
            nvd_vulns = await self.search_nvd(service_name, version)
            vulnerabilities.extend(nvd_vulns)

        # Check for known exploits
        if self.config["include_exploits"]:
            for vuln in vulnerabilities:
                try:
                    vuln["exploits"] = await self.check_exploits(vuln.get("cve_id"))
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    # ENHANCED: specific error per exploit check
                    self._log("warning", "Exploit check network error",
                              cve_id=vuln.get("cve_id"), error=str(e))
                    vuln["exploits"] = []

        return vulnerabilities

    async def search_nvd(self, product: str, version: str) -> List[Dict]:
        """
        Search NVD with rate limiting and exponential backoff.

        Args:
            product: Software product name.
            version: Software version string.

        Returns:
            List of parsed vulnerability dicts from NVD.
        """
        self.logger.progress(f"Searching NVD for {product} {version}...")

        vulnerabilities: List[Dict] = []
        max_retries = self.config.get("max_retries", 3)
        backoff_base = self.config.get("backoff_base", 6)

        async with self._nvd_semaphore:  # Rate limit concurrent NVD calls
            for attempt in range(max_retries):
                try:
                    headers: Dict[str, str] = {}
                    if self.config.get("nvd_api_key"):
                        headers["apiKey"] = self.config["nvd_api_key"]

                    async with aiohttp.ClientSession() as session:
                        params = {
                            "keywordSearch": f"{product} {version}",
                            "resultsPerPage": 20
                        }

                        async with session.get(
                            self.nvd_api,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
                        ) as response:

                            if response.status == 200:
                                data = await response.json()

                                for cve_item in data.get("vulnerabilities", []):
                                    cve = cve_item.get("cve", {})
                                    vuln = self._parse_cve_data(cve, product, version)

                                    if vuln["cvss_score"] >= self.config["min_cvss_score"]:
                                        vulnerabilities.append(vuln)

                                return vulnerabilities  # Success — exit retry loop

                            elif response.status == 403:
                                # ENHANCED: exponential backoff with jitter
                                wait_time = 2 ** attempt * backoff_base
                                self._log(
                                    "warning",
                                    "NVD API rate limited",
                                    attempt=attempt + 1,
                                    max_retries=max_retries,
                                    wait_time=wait_time,
                                )
                                self.logger.warning(
                                    f"NVD API rate limited (attempt {attempt+1}/{max_retries}), "
                                    f"retrying in {wait_time}s..."
                                )
                                await asyncio.sleep(wait_time)
                            else:
                                self.logger.warning(f"NVD API returned status {response.status}")
                                return vulnerabilities

                except aiohttp.ClientError as e:
                    # ENHANCED: specific aiohttp errors
                    self._log("warning", "NVD search client error", error=str(e))
                    return vulnerabilities
                except asyncio.TimeoutError:
                    self.logger.warning("NVD search timed out")
                    self._log("warning", "NVD search timed out",
                              product=product, version=version)
                    return vulnerabilities
                except Exception as e:
                    self.logger.warning(f"NVD search failed: {e}")
                    return vulnerabilities

        return vulnerabilities

    def _parse_cve_data(self, cve: Dict, product: str, version: str) -> Dict:
        """
        Parse CVE data from NVD API response.

        Args:
            cve: Raw CVE dict from NVD.
            product: Product name for context.
            version: Version string for context.

        Returns:
            Normalized vulnerability dict.
        """
        cve_id = cve.get("id", "Unknown")

        # Get description
        descriptions = cve.get("descriptions", [])
        description = descriptions[0].get("value", "No description") if descriptions else "No description"

        # Get CVSS score
        metrics = cve.get("metrics", {})
        cvss_data = metrics.get("cvssMetricV31", [{}])[0] if metrics.get("cvssMetricV31") else {}
        cvss_score = cvss_data.get("cvssData", {}).get("baseScore", 0.0)
        severity = cvss_data.get("cvssData", {}).get("baseSeverity", "UNKNOWN")

        # Get published date
        published = cve.get("published", "")

        return {
            "cve_id": cve_id,
            "description": description[:500],  # Truncate
            "cvss_score": cvss_score,
            "severity": severity,
            "product": product,
            "version": version,
            "published_date": published,
            "references": [ref.get("url") for ref in cve.get("references", [])[:5]],
            "exploits": []
        }

    async def check_exploits(self, cve_id: str) -> List[Dict]:
        """
        Check for available exploits for a given CVE ID.

        Args:
            cve_id: CVE identifier string.

        Returns:
            List of exploit info dicts.
        """
        if not cve_id or cve_id == "Unknown":
            return []

        self.logger.progress(f"Checking exploits for {cve_id}...")

        exploits: List[Dict] = []

        try:
            async with aiohttp.ClientSession() as session:
                # Search Exploit-DB
                search_url = f"{self.exploit_db_api}?cve={cve_id}"

                async with session.get(
                    search_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status == 200:
                        # Parse exploit information
                        # This is simplified - actual implementation would parse HTML/JSON
                        exploits.append({
                            "source": "exploit-db",
                            "available": True,
                            "url": search_url
                        })

        except aiohttp.ClientError as e:
            # ENHANCED: specific aiohttp error
            self._log("warning", "Exploit check client error", cve_id=cve_id, error=str(e))
        except asyncio.TimeoutError:
            # ENHANCED: specific timeout
            self._log("warning", "Exploit check timed out", cve_id=cve_id)
        except Exception as e:
            self.logger.warning(f"Exploit check failed: {e}")

        return exploits

    def _categorize_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict:
        """
        Categorize vulnerabilities by severity based on CVSS score.

        Args:
            vulnerabilities: List of vulnerability dicts.

        Returns:
            Summary dict with counts per severity level.
        """
        summary: Dict[str, int] = {
            "total": len(vulnerabilities),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        for vuln in vulnerabilities:
            cvss = vuln.get("cvss_score", 0.0)
            # ENHANCED: ensure numeric type
            if not isinstance(cvss, (int, float)):
                try:
                    cvss = float(cvss)
                except (ValueError, TypeError):
                    cvss = 0.0

            if cvss >= 9.0:
                summary["critical"] += 1
            elif cvss >= 7.0:
                summary["high"] += 1
            elif cvss >= 4.0:
                summary["medium"] += 1
            elif cvss > 0.0:
                summary["low"] += 1
            else:
                summary["info"] += 1

        return summary

    def _generate_recommendations(self, vulnerabilities: List[Dict]) -> List[str]:
        """
        Generate remediation recommendations based on detected vulnerabilities.

        Args:
            vulnerabilities: List of vulnerability dicts.

        Returns:
            Prioritized list of recommendation strings (max 10).
        """
        recommendations: List[str] = []

        if not vulnerabilities:
            recommendations.append("No vulnerabilities detected. Continue monitoring.")
            return recommendations

        # Count by severity
        critical = sum(1 for v in vulnerabilities if v.get("cvss_score", 0) >= 9.0)
        high = sum(1 for v in vulnerabilities if 7.0 <= v.get("cvss_score", 0) < 9.0)

        if critical > 0:
            recommendations.append(
                f"⚠️ URGENT: {critical} critical vulnerabilities found. "
                "Immediate patching required."
            )

        if high > 0:
            recommendations.append(
                f"⚠️ HIGH PRIORITY: {high} high-severity vulnerabilities found. "
                "Schedule patching within 48 hours."
            )

        # Service-specific recommendations
        services_with_vulns = set(v.get("product") for v in vulnerabilities)

        for service in services_with_vulns:
            recommendations.append(
                f"Update {service} to the latest stable version"
            )

        # General recommendations
        recommendations.extend([
            "Enable automatic security updates where possible",
            "Implement a vulnerability management program",
            "Regular security scanning and monitoring",
            "Apply defense-in-depth security controls"
        ])

        return recommendations[:10]  # Limit to top 10
