"""
Scanner Agent — ENHANCED v2.0
Performs comprehensive port scanning and service detection

ENHANCED v2.0:
- Structured JSON-compatible logging via _log()
- Timezone-aware datetimes (datetime.now(timezone.utc))
- UUID4-based scan tracking
- Input validation on public methods
- try/except with specific exception types (no bare except where avoidable)
- Configurable concurrency and timeout overrides
- Detailed docstrings on every method
"""

import asyncio
import socket
from typing import Dict, List, Optional, Any
import re
import functools
import uuid
from datetime import datetime, timezone

from src.agents.base_agent import BaseAgent


def _blocking_resolve(hostname: str) -> str:
    """Blocking DNS resolve — run via executor."""
    return socket.gethostbyname(hostname)


def _blocking_port_check(ip: str, port: int, timeout: float = 1.0) -> bool:
    """Blocking port check — run via executor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return result == 0
    finally:
        sock.close()


class ScannerAgent(BaseAgent):
    """
    Scanner Agent — ENHANCED v2.0

    Capabilities:
    - TCP/UDP port scanning (non-blocking)
    - Service version detection
    - OS fingerprinting
    - Banner grabbing
    - Network mapping

    ENHANCED v2.0 additions:
    - Structured logging with JSON context
    - Input validation on public entry points
    - Specific exception handling throughout
    - Timezone-aware timestamps
    - UUID4-based scan tracking
    - Configurable banner_timeout
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__("scanner", config)
        self.default_config = {
            "timeout": 60,
            "scan_type": "tcp",  # tcp, udp, syn
            "port_range": "1-1000",
            "aggressive": False,
            "os_detection": True,
            "service_detection": True,
            "banner_grab": True,
            "max_concurrent_ports": 50,
            # ENHANCED: configurable banner grab timeout
            "banner_timeout": 3,
        }
        self.config = {**self.default_config, **(config or {})}

    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """
        Execute port scan on target.

        Args:
            target: Hostname or IP to scan.
            options: Optional dict of overrides.

        Returns:
            Dict with open_ports, services, os_info, and banners.

        Raises:
            ValueError: If target fails validation.
        """

        # Validate target
        if not await self.validate_target(target):
            raise ValueError(f"Invalid target: {target}")

        # ENHANCED: structured log with scan ID and timestamp
        scan_id = uuid.uuid4().hex[:12]
        self._log("info", "Port scan started", target=target, scan_id=scan_id,
                  scan_type=self.config["scan_type"])
        self.logger.progress("Starting port scan...")

        # Perform scans
        results: Dict[str, Any] = {
            "target": target,
            # ENHANCED: timezone-aware timestamp and scan tracking
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scan_id": scan_id,
            "scan_type": self.config["scan_type"],
            "port_range": self.config["port_range"],
            "open_ports": await self.port_scan(target),
            "services": [],
            "os_info": {},
            "banners": {}
        }

        # Service detection
        if self.config["service_detection"] and results["open_ports"]:
            try:
                results["services"] = await self.service_detection(
                    target, results["open_ports"]
                )
            except (OSError, asyncio.TimeoutError) as e:
                # ENHANCED: specific exception handling
                self._log("warning", "Service detection failed", target=target, error=str(e))
                results["services"] = []

        # OS detection
        if self.config["os_detection"]:
            try:
                results["os_info"] = await self.os_detection(target)
            except (OSError, asyncio.TimeoutError) as e:
                # ENHANCED: specific exception handling
                self._log("warning", "OS detection failed", target=target, error=str(e))
                results["os_info"] = {"detected": False, "os_family": "unknown", "details": []}

        # Banner grabbing
        if self.config["banner_grab"] and results["open_ports"]:
            try:
                results["banners"] = await self.banner_grabbing(
                    target, results["open_ports"]
                )
            except (OSError, asyncio.TimeoutError) as e:
                # ENHANCED: specific exception handling
                self._log("warning", "Banner grabbing failed", target=target, error=str(e))
                results["banners"] = {}

        self._log("info", "Port scan completed", target=target, scan_id=scan_id,
                  ports_found=len(results["open_ports"]))
        self.logger.success(f"Scan completed for {target}")
        return results

    async def port_scan(self, target: str) -> List[Dict]:
        """
        Perform port scan — tries nmap, falls back to async socket scan.

        Args:
            target: Hostname or IP to scan.

        Returns:
            List of dicts with port, state, and service keys.
        """
        self.logger.progress(f"Scanning ports {self.config['port_range']}...")

        try:
            return await self.nmap_scan(target)
        except FileNotFoundError:
            self.logger.warning("Nmap not found, using async socket scan")
            return await self.socket_scan(target)

    async def nmap_scan(self, target: str) -> List[Dict]:
        """
        Perform nmap scan via subprocess.

        Args:
            target: Hostname or IP to scan.

        Returns:
            Parsed list of port dicts from nmap XML output.

        Raises:
            FileNotFoundError: When nmap is not installed.
        """
        self.logger.progress("Using Nmap for scanning...")

        # Build nmap command — target is appended as a separate arg (no shell injection)
        nmap_args = [
            "nmap",
            "-p", self.config["port_range"],
            "-oX", "-",  # XML output to stdout
        ]

        if self.config["service_detection"]:
            nmap_args.append("-sV")

        if self.config["os_detection"]:
            nmap_args.append("-O")

        if self.config["aggressive"]:
            nmap_args.append("-A")

        nmap_args.append(target)

        try:
            process = await asyncio.create_subprocess_exec(
                *nmap_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config["timeout"]
            )

            if stdout:
                return self._parse_nmap_output(stdout.decode())

        except asyncio.TimeoutError:
            self.logger.warning("Nmap scan timed out")
            self._log("warning", "Nmap scan timed out", target=target)
        except FileNotFoundError:
            raise  # Propagate so port_scan can fall back
        except OSError as e:
            # ENHANCED: specific OS-level error
            self._log("warning", "Nmap OS error", target=target, error=str(e))
        except Exception as e:
            self.logger.warning(f"Nmap scan failed: {e}")

        return []

    def _parse_nmap_output(self, xml_output: str) -> List[Dict]:
        """Parse nmap XML output"""
        ports: List[Dict] = []

        port_pattern = r'portid="(\d+)".*?state="(\w+)".*?service name="([^"]*)"'
        matches = re.findall(port_pattern, xml_output)

        for port, state, service in matches:
            ports.append({
                "port": int(port),
                "state": state,
                "service": service or "unknown"
            })

        return ports

    async def socket_scan(self, target: str) -> List[Dict]:
        """
        Async socket-based port scan with concurrency control.

        Args:
            target: Hostname or IP to scan.

        Returns:
            Sorted list of dicts for open ports.
        """
        self.logger.progress("Using async socket scan...")

        loop = asyncio.get_event_loop()

        # Parse port range
        try:
            start_port, end_port = map(int, self.config["port_range"].split("-"))
        except (ValueError, AttributeError) as e:
            # ENHANCED: validate port range format
            self._log("error", "Invalid port range format", port_range=self.config["port_range"],
                      error=str(e))
            return []

        # Cap at 1000 ports to avoid overwhelming
        end_port = min(end_port, start_port + 999)

        # Resolve target (non-blocking)
        try:
            ip = await loop.run_in_executor(None, _blocking_resolve, target)
        except socket.gaierror:
            self.logger.error(f"Could not resolve {target}")
            return []

        # Scan ports concurrently with semaphore
        open_ports: List[Dict] = []
        sem = asyncio.Semaphore(self.config["max_concurrent_ports"])

        async def _check_port(port: int) -> None:
            async with sem:
                try:
                    is_open = await loop.run_in_executor(
                        None, _blocking_port_check, ip, port
                    )
                    if is_open:
                        open_ports.append({
                            "port": port,
                            "state": "open",
                            "service": self._guess_service(port)
                        })
                        self.logger.progress(f"Found open port: {port}")
                except (socket.error, OSError) as e:
                    # ENHANCED: specific socket/OS errors
                    self._log("warning", f"Error scanning port {port}", error=str(e))
                except Exception as e:
                    self.logger.warning(f"Error scanning port {port}: {e}")

        await asyncio.gather(
            *[_check_port(p) for p in range(start_port, end_port + 1)],
            return_exceptions=True
        )

        return sorted(open_ports, key=lambda x: x["port"])

    def _guess_service(self, port: int) -> str:
        """Guess service based on port number"""
        common_services = {
            20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",
            25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",
            143: "IMAP", 443: "HTTPS", 445: "SMB", 3306: "MySQL",
            3389: "RDP", 5432: "PostgreSQL", 6379: "Redis",
            8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB"
        }
        return common_services.get(port, "unknown")

    async def service_detection(self, target: str, ports: List[Dict]) -> List[Dict]:
        """
        Detect services and versions on open ports.

        Args:
            target: Hostname or IP.
            ports: List of port dicts from port_scan.

        Returns:
            List of dicts with port, service, version, and banner.
        """
        self.logger.progress("Detecting services...")

        services: List[Dict] = []

        for port_info in ports[:10]:  # Limit to first 10 ports
            port = port_info["port"]

            try:
                banner = await self._grab_banner(target, port)

                service_info: Dict[str, Any] = {
                    "port": port,
                    "service": port_info.get("service", "unknown"),
                    "version": self._extract_version(banner) if banner else None,
                    "banner": banner[:200] if banner else None  # Truncate
                }

                services.append(service_info)

            except (ConnectionRefusedError, ConnectionResetError) as e:
                # ENHANCED: specific connection errors
                self._log("warning", "Service detection connection error",
                          port=port, error=str(e))
            except Exception as e:
                self.logger.warning(f"Service detection failed for port {port}: {e}")

        return services

    async def _grab_banner(self, target: str, port: int,
                           timeout: Optional[int] = None) -> Optional[str]:
        """
        Grab service banner (uses async I/O).

        Args:
            target: Hostname or IP.
            port: Port number.
            timeout: Connection/read timeout in seconds.

        Returns:
            Banner string or None on failure.
        """
        # ENHANCED: use configurable banner_timeout
        if timeout is None:
            timeout = self.config.get("banner_timeout", 3)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target, port),
                timeout=timeout
            )

            # Send HTTP request for web services
            if port in [80, 8080, 8000]:
                writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
                await writer.drain()

            # Read response
            data = await asyncio.wait_for(
                reader.read(1024),
                timeout=timeout
            )

            writer.close()
            await writer.wait_closed()

            return data.decode('utf-8', errors='ignore')

        except asyncio.TimeoutError:
            # ENHANCED: silent timeout is expected for many ports
            return None
        except (ConnectionRefusedError, ConnectionResetError, OSError):
            # ENHANCED: specific connection errors
            return None
        except Exception:
            return None

    def _extract_version(self, banner: str) -> Optional[str]:
        """Extract version from banner"""
        patterns = [
            r'Server:\s*([^\r\n]+)',
            r'(\w+/[\d.]+)',
            r'Version:\s*([^\r\n]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, banner, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    async def os_detection(self, target: str) -> Dict:
        """
        Detect operating system via TTL analysis.

        Args:
            target: Hostname or IP to ping.

        Returns:
            Dict with detected (bool), os_family, and details.
        """
        self.logger.progress("Detecting OS...")

        os_info: Dict[str, Any] = {
            "detected": False,
            "os_family": "unknown",
            "details": []
        }

        try:
            ttl = await self._get_ttl(target)

            if ttl:
                if ttl <= 64:
                    os_info["os_family"] = "Linux/Unix"
                elif ttl <= 128:
                    os_info["os_family"] = "Windows"
                elif ttl <= 255:
                    os_info["os_family"] = "Cisco/Network Device"

                os_info["detected"] = True
                os_info["details"].append(f"TTL: {ttl}")

        except (OSError, asyncio.TimeoutError) as e:
            # ENHANCED: specific exceptions
            self._log("warning", "OS detection failed", target=target, error=str(e))
        except Exception as e:
            self.logger.warning(f"OS detection failed: {e}")

        return os_info

    async def _get_ttl(self, target: str) -> Optional[int]:
        """
        Get TTL from ping response.

        Args:
            target: Hostname or IP to ping.

        Returns:
            TTL integer or None.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "ping", "-n", "1", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )

            match = re.search(r'TTL=(\d+)', stdout.decode())
            if match:
                return int(match.group(1))

        except asyncio.TimeoutError:
            # ENHANCED: specific timeout
            self._log("warning", "Ping timed out", target=target)
        except FileNotFoundError:
            # ENHANCED: ping command not found
            self._log("warning", "Ping command not found")
        except OSError as e:
            self._log("warning", "Ping OS error", error=str(e))
        except Exception:
            pass

        return None

    async def banner_grabbing(self, target: str, ports: List[Dict]) -> Dict:
        """
        Grab banners from all open ports.

        Args:
            target: Hostname or IP.
            ports: List of port dicts.

        Returns:
            Dict mapping port number (str) to banner string.
        """
        self.logger.progress("Grabbing banners...")

        banners: Dict[str, str] = {}

        for port_info in ports[:10]:  # Limit to first 10
            port = port_info["port"]
            try:
                banner = await self._grab_banner(target, port)
                if banner:
                    banners[str(port)] = banner[:500]  # Truncate
            except Exception as e:
                # ENHANCED: log per-port banner errors
                self._log("warning", "Banner grab error", port=port, error=str(e))

        return banners
