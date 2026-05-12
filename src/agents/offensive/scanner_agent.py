"""
Scanner Agent
Performs comprehensive port scanning and service detection
"""

import asyncio
import socket
from typing import Dict, List, Optional
import re
import functools

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
    Scanner Agent
    
    Capabilities:
    - TCP/UDP port scanning (non-blocking)
    - Service version detection
    - OS fingerprinting
    - Banner grabbing
    - Network mapping
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
            "max_concurrent_ports": 50
        }
        self.config = {**self.default_config, **(config or {})}
    
    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """Execute port scan on target"""
        
        # Validate target
        if not await self.validate_target(target):
            raise ValueError(f"Invalid target: {target}")
        
        self.logger.progress("Starting port scan...")
        
        # Perform scans
        results = {
            "target": target,
            "scan_type": self.config["scan_type"],
            "port_range": self.config["port_range"],
            "open_ports": await self.port_scan(target),
            "services": [],
            "os_info": {},
            "banners": {}
        }
        
        # Service detection
        if self.config["service_detection"] and results["open_ports"]:
            results["services"] = await self.service_detection(
                target, results["open_ports"]
            )
        
        # OS detection
        if self.config["os_detection"]:
            results["os_info"] = await self.os_detection(target)
        
        # Banner grabbing
        if self.config["banner_grab"] and results["open_ports"]:
            results["banners"] = await self.banner_grabbing(
                target, results["open_ports"]
            )
        
        self.logger.success(f"Scan completed for {target}")
        return results
    
    async def port_scan(self, target: str) -> List[Dict]:
        """Perform port scan — tries nmap, falls back to async socket scan"""
        self.logger.progress(f"Scanning ports {self.config['port_range']}...")
        
        try:
            return await self.nmap_scan(target)
        except FileNotFoundError:
            self.logger.warning("Nmap not found, using async socket scan")
            return await self.socket_scan(target)
    
    async def nmap_scan(self, target: str) -> List[Dict]:
        """Perform nmap scan"""
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
        except Exception as e:
            self.logger.warning(f"Nmap scan failed: {e}")
        
        return []
    
    def _parse_nmap_output(self, xml_output: str) -> List[Dict]:
        """Parse nmap XML output"""
        ports = []
        
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
        """Async socket-based port scan with concurrency control"""
        self.logger.progress("Using async socket scan...")
        
        loop = asyncio.get_event_loop()
        
        # Parse port range
        start_port, end_port = map(int, self.config["port_range"].split("-"))
        # Cap at 1000 ports to avoid overwhelming
        end_port = min(end_port, start_port + 999)
        
        # Resolve target (non-blocking)
        try:
            ip = await loop.run_in_executor(None, _blocking_resolve, target)
        except socket.gaierror:
            self.logger.error(f"Could not resolve {target}")
            return []
        
        # Scan ports concurrently with semaphore
        open_ports = []
        sem = asyncio.Semaphore(self.config["max_concurrent_ports"])
        
        async def _check_port(port: int):
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
        """Detect services and versions"""
        self.logger.progress("Detecting services...")
        
        services = []
        
        for port_info in ports[:10]:  # Limit to first 10 ports
            port = port_info["port"]
            
            try:
                banner = await self._grab_banner(target, port)
                
                service_info = {
                    "port": port,
                    "service": port_info.get("service", "unknown"),
                    "version": self._extract_version(banner) if banner else None,
                    "banner": banner[:200] if banner else None  # Truncate
                }
                
                services.append(service_info)
            
            except Exception as e:
                self.logger.warning(f"Service detection failed for port {port}: {e}")
        
        return services
    
    async def _grab_banner(self, target: str, port: int, timeout: int = 3) -> Optional[str]:
        """Grab service banner (uses async I/O)"""
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
        """Detect operating system"""
        self.logger.progress("Detecting OS...")
        
        os_info = {
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
        
        except Exception as e:
            self.logger.warning(f"OS detection failed: {e}")
        
        return os_info
    
    async def _get_ttl(self, target: str) -> Optional[int]:
        """Get TTL from ping"""
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
        
        except Exception:
            pass
        
        return None
    
    async def banner_grabbing(self, target: str, ports: List[Dict]) -> Dict:
        """Grab banners from all open ports"""
        self.logger.progress("Grabbing banners...")
        
        banners = {}
        
        for port_info in ports[:10]:  # Limit to first 10
            port = port_info["port"]
            banner = await self._grab_banner(target, port)
            
            if banner:
                banners[str(port)] = banner[:500]  # Truncate
        
        return banners
