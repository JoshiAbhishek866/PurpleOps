"""
Credential Testing Agent — ENHANCED v2.0
Ethical brute force simulation and credential testing

ENHANCED v2.0:
- Structured JSON-compatible logging via _log()
- Timezone-aware datetimes (datetime.now(timezone.utc))
- UUID4-based scan tracking
- Input validation on public methods
- try/except with specific exception types
- Configurable parameters with sensible defaults
- Detailed docstrings on every method
"""

import asyncio
from typing import Dict, List, Optional, Any
import hashlib
import time
import uuid
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent


class CredentialTestingAgent(BaseAgent):
    """
    Credential Testing Agent — ENHANCED v2.0

    Capabilities:
    - Brute force simulation (ethical)
    - Password spraying
    - Default credential checking
    - Common password testing
    - Rate limiting
    - Lockout detection
    - Ethical testing controls

    ENHANCED v2.0 additions:
    - Structured logging with JSON context
    - Input validation on service and username lists
    - Specific exception handling (no bare except)
    - Timezone-aware timestamps throughout
    - UUID4-based scan tracking
    - Configurable max_services_tested limit
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("credential_testing", config)
        self.default_config = {
            "timeout": 300,
            "max_attempts": 100,
            "rate_limit": 1.0,  # seconds between attempts
            "test_mode": "safe",  # safe, moderate, aggressive
            "check_defaults": True,
            "password_spray": True,
            "lockout_threshold": 5,
            "ethical_mode": True,  # Always respect rate limits and stop on lockout
            # ENHANCED: configurable service limit
            "max_services_tested": 5,
        }
        self.config = {**self.default_config, **(config or {})}

        # Common credentials database
        self.default_credentials = self._load_default_credentials()
        self.common_passwords = self._load_common_passwords()

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Execute credential testing against a target.

        Args:
            target: Hostname or IP to test credentials against.
            options: Dict with 'services' and optional 'usernames' lists.

        Returns:
            Dict with test results, weak credentials, defaults found,
            spray results, and recommendations.

        Raises:
            ValueError: If ethical_mode is disabled.
        """

        if not self.config["ethical_mode"]:
            raise ValueError("Ethical mode must be enabled for credential testing")

        # ENHANCED: structured log with scan ID and timestamp
        scan_id = uuid.uuid4().hex[:12]
        self._log("info", "Credential testing started", target=target, scan_id=scan_id,
                  test_mode=self.config["test_mode"])
        self.logger.progress("Starting ethical credential testing...")

        # Get services from options
        services = options.get("services", []) if options else []
        usernames = options.get("usernames", ["admin", "root", "user"]) if options else ["admin"]

        # ENHANCED: validate usernames input
        if not isinstance(usernames, list) or not usernames:
            self._log("warning", "Invalid usernames list, using defaults", target=target)
            usernames = ["admin", "root", "user"]

        results: Dict[str, Any] = {
            "target": target,
            # ENHANCED: timezone-aware timestamp and scan tracking
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan_id": scan_id,
            "test_mode": self.config["test_mode"],
            "mode": "simulation",  # Clearly indicates results are simulated
            "services_tested": [],
            "weak_credentials": [],
            "default_credentials": [],
            "password_spray_results": [],
            "lockout_detected": False,
            "recommendations": []
        }

        # Test default credentials
        if self.config["check_defaults"]:
            try:
                default_results = await self.test_default_credentials(target, services)
                results["default_credentials"] = default_results
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # ENHANCED: specific error handling
                self._log("warning", "Default credential test failed",
                          target=target, error=str(e))
                results["default_credentials"] = []

        # Password spraying
        if self.config["password_spray"]:
            try:
                spray_results = await self.password_spray(target, usernames)
                results["password_spray_results"] = spray_results
            except asyncio.CancelledError:
                raise
            except Exception as e:
                # ENHANCED: specific error handling
                self._log("warning", "Password spray failed",
                          target=target, error=str(e))
                results["password_spray_results"] = []

        # Common password testing
        try:
            common_results = await self.test_common_passwords(target, usernames[:3])
            results["weak_credentials"] = common_results
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # ENHANCED: specific error handling
            self._log("warning", "Common password test failed",
                      target=target, error=str(e))
            results["weak_credentials"] = []

        # Generate recommendations
        results["recommendations"] = self._generate_recommendations(results)

        # Summary
        results["summary"] = {
            "services_tested": len(results["services_tested"]),
            "weak_found": len(results["weak_credentials"]),
            "defaults_found": len(results["default_credentials"]),
            "lockout_detected": results["lockout_detected"]
        }

        self._log("info", "Credential testing completed", target=target,
                  scan_id=scan_id,
                  weak_found=results["summary"]["weak_found"],
                  defaults_found=results["summary"]["defaults_found"])
        self.logger.success(
            f"Credential testing completed: {results['summary']['weak_found']} weak credentials found"
        )

        return results

    async def test_default_credentials(
        self,
        target: str,
        services: List[Dict]
    ) -> List[Dict]:
        """
        Test for default credentials on discovered services.

        Args:
            target: Hostname or IP.
            services: List of service dicts with 'service' and 'port' keys.

        Returns:
            List of dicts describing found default credentials.
        """
        self.logger.progress("Testing default credentials...")

        found_defaults: List[Dict] = []
        # ENHANCED: use configurable service limit
        max_services = self.config.get("max_services_tested", 5)

        for service in services[:max_services]:
            service_name = service.get("service", "").lower()
            port = service.get("port")

            # ENHANCED: validate service dict
            if not service_name:
                self._log("warning", "Skipping service with empty name", port=port)
                continue

            # Get default credentials for this service
            defaults = self.default_credentials.get(service_name, [])

            for cred in defaults:
                username = cred["username"]
                password = cred["password"]

                try:
                    # Simulate credential test (ethical - not actual login)
                    result = await self._simulate_credential_test(
                        target,
                        port,
                        username,
                        password
                    )

                    if result["success"]:
                        found_defaults.append({
                            "service": service_name,
                            "port": port,
                            "username": username,
                            "password": password,
                            "severity": "critical",
                            "description": f"Default credentials found for {service_name}"
                        })
                        self.logger.warning(f"Default credentials found: {service_name}")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # ENHANCED: per-credential error handling
                    self._log("warning", "Default cred test error",
                              service=service_name, username=username, error=str(e))

                # Rate limiting
                await asyncio.sleep(self.config["rate_limit"])

        return found_defaults

    async def password_spray(
        self,
        target: str,
        usernames: List[str]
    ) -> List[Dict]:
        """
        Password spraying attack simulation.

        Tests a small set of common passwords across multiple usernames,
        respecting lockout thresholds and rate limits.

        Args:
            target: Hostname or IP.
            usernames: List of usernames to test.

        Returns:
            List of dicts for weak credentials found via spraying.
        """
        self.logger.progress("Simulating password spray attack...")

        spray_results: List[Dict] = []
        common_passwords = self.common_passwords[:10]  # Top 10 most common

        attempt_count = 0

        for password in common_passwords:
            for username in usernames:
                # Check lockout threshold
                if attempt_count >= self.config["lockout_threshold"]:
                    self.logger.warning("Lockout threshold reached, stopping")
                    self._log("info", "Lockout threshold reached",
                              target=target, attempt_count=attempt_count)
                    return spray_results

                try:
                    # Simulate test
                    result = await self._simulate_credential_test(
                        target,
                        None,
                        username,
                        password
                    )

                    if result["success"]:
                        spray_results.append({
                            "username": username,
                            "password": password,
                            "method": "password_spray",
                            "severity": "high",
                            "description": f"Weak password found via spray attack"
                        })
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # ENHANCED: per-attempt error handling
                    self._log("warning", "Spray attempt error",
                              username=username, error=str(e))

                attempt_count += 1

                # Rate limiting
                await asyncio.sleep(self.config["rate_limit"])

        return spray_results

    async def test_common_passwords(
        self,
        target: str,
        usernames: List[str]
    ) -> List[Dict]:
        """
        Test common weak passwords against provided usernames.

        Args:
            target: Hostname or IP.
            usernames: List of usernames to test (max 3 recommended).

        Returns:
            List of dicts for weak credentials found.
        """
        self.logger.progress("Testing common weak passwords...")

        weak_found: List[Dict] = []
        passwords_to_test = self.common_passwords[:20]  # Top 20

        for username in usernames:
            for password in passwords_to_test:
                try:
                    # Simulate test
                    result = await self._simulate_credential_test(
                        target,
                        None,
                        username,
                        password
                    )

                    if result["success"]:
                        weak_found.append({
                            "username": username,
                            "password": password,
                            "method": "common_password",
                            "severity": "high",
                            "description": f"Common weak password in use"
                        })
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # ENHANCED: per-attempt error handling
                    self._log("warning", "Common password test error",
                              username=username, error=str(e))

                # Rate limiting
                await asyncio.sleep(self.config["rate_limit"])

        return weak_found

    async def _simulate_credential_test(
        self,
        target: str,
        port: Optional[int],
        username: str,
        password: str
    ) -> Dict:
        """
        Simulate credential testing (ethical mode).

        In production, this would attempt actual authentication.
        For safety, this is a simulation that flags known-weak passwords.

        Args:
            target: Hostname or IP.
            port: Service port (may be None for non-service-specific tests).
            username: Username to test.
            password: Password to test.

        Returns:
            Dict with success (bool), simulated flag, and credential details.
        """
        # Simulate network delay
        await asyncio.sleep(0.1)

        # Simulate success for demonstration
        # In real implementation, this would use actual authentication
        # For common weak passwords, simulate finding them
        weak_passwords = ["password", "123456", "admin", "default"]

        success = password.lower() in weak_passwords

        return {
            "success": success,
            "simulated": True,
            "username": username,
            "password": password,
            "target": target,
            "port": port
        }

    def _load_default_credentials(self) -> Dict[str, List[Dict]]:
        """Load database of default credentials"""
        return {
            "ssh": [
                {"username": "root", "password": "root"},
                {"username": "admin", "password": "admin"},
            ],
            "ftp": [
                {"username": "ftp", "password": "ftp"},
                {"username": "anonymous", "password": "anonymous"},
            ],
            "mysql": [
                {"username": "root", "password": ""},
                {"username": "root", "password": "root"},
            ],
            "postgresql": [
                {"username": "postgres", "password": "postgres"},
            ],
            "mongodb": [
                {"username": "admin", "password": "admin"},
            ],
            "redis": [
                {"username": "", "password": ""},
            ],
            "http": [
                {"username": "admin", "password": "admin"},
                {"username": "admin", "password": "password"},
            ],
            "telnet": [
                {"username": "admin", "password": "admin"},
            ]
        }

    def _load_common_passwords(self) -> List[str]:
        """Load list of common weak passwords"""
        return [
            "password", "123456", "12345678", "qwerty", "abc123",
            "monkey", "1234567", "letmein", "trustno1", "dragon",
            "baseball", "111111", "iloveyou", "master", "sunshine",
            "ashley", "bailey", "passw0rd", "shadow", "123123",
            "654321", "superman", "qazwsx", "michael", "football",
            "welcome", "admin", "default", "root", "toor"
        ]

    def _generate_recommendations(self, results: Dict) -> List[str]:
        """
        Generate security recommendations based on credential test results.

        Args:
            results: Full results dict from execute().

        Returns:
            Prioritized list of recommendation strings (max 10).
        """
        recommendations: List[str] = []

        if results["default_credentials"]:
            recommendations.append(
                "⚠️ CRITICAL: Change all default credentials immediately"
            )

        if results["weak_credentials"]:
            recommendations.append(
                "⚠️ HIGH: Implement strong password policy (min 12 chars, complexity)"
            )

        if results["password_spray_results"]:
            recommendations.append(
                "⚠️ HIGH: Enable account lockout after failed login attempts"
            )

        recommendations.extend([
            "Enable multi-factor authentication (MFA) for all accounts",
            "Implement password complexity requirements",
            "Use password manager for secure password generation",
            "Regular password rotation policy",
            "Monitor for brute force attempts",
            "Implement CAPTCHA for login forms",
            "Use rate limiting on authentication endpoints",
            "Enable security logging for failed login attempts"
        ])

        return recommendations[:10]
