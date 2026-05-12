"""
Reconnaissance Agent
Performs network reconnaissance and information gathering
"""

import asyncio
import socket
import dns.resolver
from typing import Dict, List, Optional
import re
import functools

from src.agents.base_agent import BaseAgent


def _blocking_resolve(hostname: str) -> str:
    """Blocking DNS resolve — run via executor."""
    return socket.gethostbyname(hostname)


def _blocking_resolve_reverse(ip: str):
    """Blocking reverse DNS — run via executor."""
    return socket.gethostbyaddr(ip)


def _blocking_port_check(ip: str, port: int, timeout: float = 1.0) -> bool:
    """Blocking port check — run via executor."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((ip, port))
        return result == 0
    finally:
        sock.close()


class ReconAgent(BaseAgent):
    """
    Reconnaissance Agent
    
    Capabilities:
    - DNS enumeration
    - Subdomain discovery (concurrent)
    - WHOIS lookups
    - Port discovery (non-blocking)
    - Service fingerprinting
    - Technology stack detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("recon", config)
        self.default_config = {
            "timeout": 30,
            "max_subdomains": 50,
            "dns_servers": ["8.8.8.8", "1.1.1.1"],
            "common_ports": [80, 443, 22, 21, 25, 3306, 5432, 6379, 27017]
        }
        self.config = {**self.default_config, **(config or {})}
    
    async def execute(self, target: str, options: Optional[Dict] = None) -> Dict:
        """Execute reconnaissance on target"""
        
        # Validate target
        if not await self.validate_target(target):
            raise ValueError(f"Invalid target: {target}")
        
        self.logger.progress("Starting reconnaissance...")
        
        # Gather all information concurrently for speed
        dns_task = self.dns_enumeration(target)
        subdomain_task = self.subdomain_discovery(target)
        whois_task = self.whois_lookup(target)
        port_task = self.port_discovery(target)
        ip_task = self.resolve_ips(target)
        
        dns_info, subdomains, whois, open_ports, ip_addresses = await asyncio.gather(
            dns_task, subdomain_task, whois_task, port_task, ip_task,
            return_exceptions=True
        )
        
        # Convert exceptions to empty results
        results = {
            "target": target,
            "dns_info": dns_info if not isinstance(dns_info, Exception) else {"error": str(dns_info)},
            "subdomains": subdomains if not isinstance(subdomains, Exception) else [],
            "whois": whois if not isinstance(whois, Exception) else {"error": str(whois)},
            "open_ports": open_ports if not isinstance(open_ports, Exception) else [],
            "ip_addresses": ip_addresses if not isinstance(ip_addresses, Exception) else [],
        }
        
        # Reverse DNS (needs IP first)
        if results["ip_addresses"] and not isinstance(results["ip_addresses"], list):
            results["reverse_dns"] = {"error": "No IPs resolved"}
        else:
            results["reverse_dns"] = await self.reverse_dns_lookup(target)
        
        self.logger.success(f"Reconnaissance completed for {target}")
        return results
    
    async def dns_enumeration(self, target: str) -> Dict:
        """Enumerate DNS records"""
        self.logger.progress("Enumerating DNS records...")
        
        dns_records = {
            "A": [], "AAAA": [], "MX": [], "NS": [], "TXT": [], "CNAME": []
        }
        
        loop = asyncio.get_event_loop()
        
        for record_type in dns_records.keys():
            try:
                # dns.resolver.resolve is blocking — run in executor
                answers = await loop.run_in_executor(
                    None,
                    functools.partial(dns.resolver.resolve, target, record_type)
                )
                dns_records[record_type] = [str(rdata) for rdata in answers]
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
                pass
            except Exception as e:
                self.logger.warning(f"DNS {record_type} lookup failed: {e}")
        
        return dns_records
    
    async def subdomain_discovery(self, target: str) -> List[str]:
        """Discover subdomains — concurrent, non-blocking"""
        self.logger.progress("Discovering subdomains...")
        
        common_subdomains = [
            "www", "mail", "ftp", "admin", "api", "dev", "staging",
            "test", "blog", "shop", "portal", "vpn", "cdn", "app",
            "mobile", "m", "secure", "payment", "support", "help"
        ]
        
        loop = asyncio.get_event_loop()
        discovered = []
        
        async def _check_subdomain(subdomain: str):
            full_domain = f"{subdomain}.{target}"
            try:
                await loop.run_in_executor(None, _blocking_resolve, full_domain)
                discovered.append(full_domain)
                self.logger.progress(f"Found subdomain: {full_domain}")
            except socket.gaierror:
                pass
        
        # Run all lookups concurrently (bounded)
        sem = asyncio.Semaphore(10)  # max 10 concurrent DNS lookups
        
        async def _bounded_check(sub):
            async with sem:
                await _check_subdomain(sub)
        
        await asyncio.gather(
            *[_bounded_check(s) for s in common_subdomains[:self.config["max_subdomains"]]],
            return_exceptions=True
        )
        
        return discovered
    
    async def whois_lookup(self, target: str) -> Dict:
        """Perform WHOIS lookup"""
        self.logger.progress("Performing WHOIS lookup...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "whois", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config["timeout"]
            )
            
            if stdout:
                whois_data = stdout.decode('utf-8', errors='ignore')
                return {
                    "raw": whois_data,
                    "registrar": self._extract_whois_field(whois_data, "Registrar"),
                    "creation_date": self._extract_whois_field(whois_data, "Creation Date"),
                    "expiration_date": self._extract_whois_field(whois_data, "Expir"),
                    "name_servers": self._extract_whois_nameservers(whois_data)
                }
        except asyncio.TimeoutError:
            self.logger.warning("WHOIS lookup timed out")
        except FileNotFoundError:
            self.logger.warning("WHOIS command not found")
        except Exception as e:
            self.logger.warning(f"WHOIS lookup failed: {e}")
        
        return {"error": "WHOIS lookup failed"}
    
    def _extract_whois_field(self, whois_data: str, field: str) -> Optional[str]:
        """Extract field from WHOIS data"""
        pattern = rf"{field}:\s*(.+)"
        match = re.search(pattern, whois_data, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_whois_nameservers(self, whois_data: str) -> List[str]:
        """Extract nameservers from WHOIS data"""
        pattern = r"Name Server:\s*(.+)"
        matches = re.findall(pattern, whois_data, re.IGNORECASE)
        return [ns.strip() for ns in matches]
    
    async def port_discovery(self, target: str) -> List[Dict]:
        """Discover open ports — non-blocking via executor"""
        self.logger.progress("Discovering open ports...")
        
        loop = asyncio.get_event_loop()
        
        # Resolve target to IP (non-blocking)
        try:
            ip = await loop.run_in_executor(None, _blocking_resolve, target)
        except socket.gaierror:
            self.logger.warning(f"Could not resolve {target}")
            return []
        
        # Scan all ports concurrently via executor
        open_ports = []
        sem = asyncio.Semaphore(20)  # max 20 concurrent port checks
        
        async def _check_port(port: int):
            async with sem:
                is_open = await loop.run_in_executor(
                    None, _blocking_port_check, ip, port
                )
                if is_open:
                    service = self._get_service_name(port)
                    open_ports.append({
                        "port": port,
                        "service": service,
                        "state": "open"
                    })
                    self.logger.progress(f"Found open port: {port} ({service})")
        
        await asyncio.gather(
            *[_check_port(p) for p in self.config["common_ports"]],
            return_exceptions=True
        )
        
        return sorted(open_ports, key=lambda x: x["port"])
    
    def _get_service_name(self, port: int) -> str:
        """Get common service name for port"""
        services = {
            21: "FTP", 22: "SSH", 25: "SMTP", 80: "HTTP",
            443: "HTTPS", 3306: "MySQL", 5432: "PostgreSQL",
            6379: "Redis", 27017: "MongoDB", 8080: "HTTP-Proxy"
        }
        return services.get(port, "Unknown")
    
    async def resolve_ips(self, target: str) -> List[str]:
        """Resolve target to IP addresses (non-blocking)"""
        self.logger.progress("Resolving IP addresses...")
        
        loop = asyncio.get_event_loop()
        ips = []
        
        for rtype in ['A', 'AAAA']:
            try:
                answers = await loop.run_in_executor(
                    None,
                    functools.partial(dns.resolver.resolve, target, rtype)
                )
                ips.extend([str(rdata) for rdata in answers])
            except Exception:
                pass
        
        return ips
    
    async def reverse_dns_lookup(self, target: str) -> Dict:
        """Perform reverse DNS lookup (non-blocking)"""
        self.logger.progress("Performing reverse DNS lookup...")
        
        loop = asyncio.get_event_loop()
        
        try:
            ip = await loop.run_in_executor(None, _blocking_resolve, target)
            hostname = await loop.run_in_executor(None, _blocking_resolve_reverse, ip)
            return {
                "ip": ip,
                "hostname": hostname[0],
                "aliases": hostname[1]
            }
        except Exception as e:
            return {"error": str(e)}
