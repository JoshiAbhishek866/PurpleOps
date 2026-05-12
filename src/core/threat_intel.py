"""
Free Threat Intelligence Feed Fetcher for Sentinel AI

Fetches and caches data from free threat intel sources:
- CISA Known Exploited Vulnerabilities (KEV)
- NVD (National Vulnerability Database) recent CVEs
- Abuse.ch Feodo Tracker (C2 IPs)

All data is cached locally to minimize API calls and respect rate limits.
Fail-graceful: returns empty results if feeds are unavailable.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path("./data/threat_intel_cache")


class ThreatIntelFetcher:
    """
    Fetches and caches threat intelligence from free sources.

    Usage:
        fetcher = ThreatIntelFetcher()
        cisa_vulns = await fetcher.get_cisa_kev()
        nvd_cves = await fetcher.search_nvd("SQL injection")
    """

    def __init__(self, cache_ttl_hours: int = 24):
        self.cache_ttl = cache_ttl_hours * 3600  # Convert to seconds
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache(self, cache_key: str) -> Optional[Dict]:
        """Read from local cache if not expired."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                if time.time() - data.get("cached_at", 0) < self.cache_ttl:
                    return data.get("payload")
            except Exception:
                pass
        return None

    def _set_cache(self, cache_key: str, payload: any):
        """Write to local cache."""
        cache_file = CACHE_DIR / f"{cache_key}.json"
        try:
            cache_file.write_text(json.dumps({
                "cached_at": time.time(),
                "payload": payload,
            }, default=str))
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    # ==================== CISA KEV ====================

    async def get_cisa_kev(self, limit: int = 50) -> List[Dict]:
        """
        Fetch CISA Known Exploited Vulnerabilities catalog.
        Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
        Free, no API key needed, updated daily.
        """
        cached = self._get_cache("cisa_kev")
        if cached:
            return cached[:limit]

        try:
            import aiohttp
            url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        vulns = data.get("vulnerabilities", [])
                        # Extract relevant fields
                        clean = [{
                            "cve_id": v.get("cveID"),
                            "vendor": v.get("vendorProject"),
                            "product": v.get("product"),
                            "name": v.get("vulnerabilityName"),
                            "description": v.get("shortDescription"),
                            "date_added": v.get("dateAdded"),
                            "due_date": v.get("dueDate"),
                            "known_ransomware": v.get("knownRansomwareCampaignUse", "Unknown"),
                        } for v in vulns]
                        self._set_cache("cisa_kev", clean)
                        logger.info(f"Fetched {len(clean)} CISA KEV entries")
                        return clean[:limit]
        except Exception as e:
            logger.warning(f"CISA KEV fetch failed: {e}")
        return []

    # ==================== NVD ====================

    async def search_nvd(self, keyword: str, limit: int = 20) -> List[Dict]:
        """
        Search NVD for CVEs matching a keyword.
        Source: https://services.nvd.nist.gov/rest/json/cves/2.0
        Free, rate-limited to 5 requests per 30 seconds (no API key).
        """
        cache_key = f"nvd_{keyword.replace(' ', '_')[:30]}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached[:limit]

        try:
            import aiohttp
            url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
            params = {"keywordSearch": keyword, "resultsPerPage": limit}
            headers = {}

            # Use API key if available (higher rate limit)
            nvd_key = os.getenv("NVD_API_KEY")
            if nvd_key:
                headers["apiKey"] = nvd_key

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers,
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        cves = []
                        for item in data.get("vulnerabilities", []):
                            cve = item.get("cve", {})
                            descriptions = cve.get("descriptions", [])
                            desc = next(
                                (d["value"] for d in descriptions if d.get("lang") == "en"),
                                ""
                            )
                            # Get CVSS score if available
                            metrics = cve.get("metrics", {})
                            cvss_data = metrics.get("cvssMetricV31", [{}])
                            score = cvss_data[0].get("cvssData", {}).get("baseScore") if cvss_data else None

                            cves.append({
                                "cve_id": cve.get("id"),
                                "description": desc[:300],
                                "published": cve.get("published"),
                                "cvss_score": score,
                                "severity": self._score_to_severity(score),
                            })
                        self._set_cache(cache_key, cves)
                        return cves[:limit]
                    elif resp.status == 403:
                        logger.warning("NVD rate limited — using cache or returning empty")
        except Exception as e:
            logger.warning(f"NVD search failed: {e}")
        return []

    # ==================== Abuse.ch ====================

    async def get_feodo_c2_ips(self, limit: int = 50) -> List[Dict]:
        """
        Fetch active C2 (Command and Control) server IPs from Abuse.ch Feodo Tracker.
        Source: https://feodotracker.abuse.ch/
        Free, no API key needed.
        """
        cached = self._get_cache("feodo_c2")
        if cached:
            return cached[:limit]

        try:
            import aiohttp
            url = "https://feodotracker.abuse.ch/downloads/ipblocklist_recommended.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        entries = [{
                            "ip": entry.get("ip_address"),
                            "port": entry.get("port"),
                            "status": entry.get("status"),
                            "malware": entry.get("malware"),
                            "first_seen": entry.get("first_seen"),
                            "last_online": entry.get("last_online"),
                        } for entry in data[:limit]]
                        self._set_cache("feodo_c2", entries)
                        logger.info(f"Fetched {len(entries)} C2 IPs from Abuse.ch")
                        return entries
        except Exception as e:
            logger.warning(f"Abuse.ch fetch failed: {e}")
        return []

    # ==================== Aggregate ====================

    async def get_intel_summary(self) -> Dict:
        """Get a summary of all available threat intel."""
        cisa = await self.get_cisa_kev(limit=10)
        c2 = await self.get_feodo_c2_ips(limit=10)
        return {
            "cisa_kev": {
                "count": len(cisa),
                "latest": cisa[0] if cisa else None,
            },
            "feodo_c2": {
                "count": len(c2),
                "active_malware": list(set(e.get("malware", "") for e in c2))[:5],
            },
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def enrich_finding_with_intel(self, finding: Dict) -> Dict:
        """
        Enrich an agent finding with relevant threat intel.
        Matches CVE IDs found in the finding against CISA KEV.
        """
        finding_text = json.dumps(finding, default=str).upper()

        # Check if any CISA KEV CVEs match
        kev_data = await self.get_cisa_kev(limit=500)
        matched_kevs = [
            kev for kev in kev_data
            if kev.get("cve_id") and kev["cve_id"] in finding_text
        ]

        if matched_kevs:
            finding["threat_intel"] = {
                "cisa_kev_matches": matched_kevs,
                "risk_level": "CRITICAL — actively exploited in the wild",
                "enriched_at": datetime.utcnow().isoformat(),
            }
        else:
            finding["threat_intel"] = {
                "cisa_kev_matches": [],
                "risk_level": "standard",
                "enriched_at": datetime.utcnow().isoformat(),
            }

        return finding

    @staticmethod
    def _score_to_severity(score: Optional[float]) -> str:
        """Convert CVSS score to severity label."""
        if score is None:
            return "UNKNOWN"
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        return "LOW"
