"""
LLM Client
Integrates with local LLM (Ollama) for security insights
"""

import aiohttp
from typing import Dict, List, Optional
import json

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMClient:
    """
    Local LLM Integration Client (Ollama)
    
    Capabilities:
    - Connect to Ollama
    - Generate security insights
    - Analyze scan results
    - Explain vulnerabilities
    - Generate recommendations
    - Contextual threat intelligence
    """
    
    def __init__(
        self,
        provider: str = "ollama",
        model: str = "llama2",
        url: str = "http://localhost:11434",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.provider = provider
        self.model = model
        self.url = url.rstrip('/')
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # API endpoints
        self.generate_url = f"{self.url}/api/generate"
        self.chat_url = f"{self.url}/api/chat"
        
        logger.info(f"LLM client initialized: {provider}/{model}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            stream: Stream response
        
        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.generate_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "")
                    else:
                        error = await response.text()
                        logger.error(f"LLM generation failed: {error}")
                        return ""
        
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return ""
    
    async def analyze_scan_results(self, agent_type: str, results: Dict) -> Dict:
        """
        Analyze scan results and provide insights
        """
        logger.info(f"Analyzing {agent_type} results with LLM...")
        
        if agent_type == "recon":
            analysis = await self._analyze_recon(results)
        elif agent_type == "scanner":
            analysis = await self._analyze_scanner(results)
        elif agent_type == "vuln":
            analysis = await self._analyze_vulnerabilities(results)
        else:
            analysis = await self._generic_analysis(results)
        
        return {
            "agent_type": agent_type,
            "analysis": analysis,
            "llm_model": self.model
        }
    
    async def _analyze_recon(self, results: Dict) -> Dict:
        """Analyze reconnaissance results"""
        target = results.get("target", "unknown")
        dns_info = results.get("data", {}).get("dns_info", {})
        subdomains = results.get("data", {}).get("subdomains", [])
        open_ports = results.get("data", {}).get("open_ports", [])
        
        prompt = f"""
You are a cybersecurity expert analyzing reconnaissance results.

Target: {target}
DNS Records: {len(dns_info)} types found
Subdomains Discovered: {len(subdomains)}
Open Ports: {len(open_ports)}

Provide a brief security analysis covering:
1. Attack surface assessment
2. Potential security concerns
3. Recommended next steps

Keep the response concise and actionable (max 200 words).
"""
        
        system_prompt = "You are a cybersecurity analyst specializing in network reconnaissance and threat assessment."
        
        response = await self.generate(prompt, system_prompt)
        
        return {
            "summary": response,
            "attack_surface_score": self._calculate_attack_surface(results),
            "key_findings": self._extract_key_findings_recon(results)
        }
    
    async def _analyze_scanner(self, results: Dict) -> Dict:
        """Analyze port scan results"""
        target = results.get("target", "unknown")
        open_ports = results.get("data", {}).get("open_ports", [])
        services = results.get("data", {}).get("services", [])
        
        ports_list = [p.get("port") for p in open_ports]
        services_list = [s.get("service") for s in services]
        
        prompt = f"""
You are a cybersecurity expert analyzing port scan results.

Target: {target}
Open Ports: {ports_list}
Services Detected: {services_list}

Provide a brief analysis covering:
1. Service exposure risks
2. Unusual or concerning services
3. Hardening recommendations

Keep the response concise (max 200 words).
"""
        
        system_prompt = "You are a cybersecurity analyst specializing in network security and service hardening."
        
        response = await self.generate(prompt, system_prompt)
        
        return {
            "summary": response,
            "risk_services": self._identify_risky_services(services),
            "recommendations": self._generate_service_recommendations(services)
        }
    
    async def _analyze_vulnerabilities(self, results: Dict) -> Dict:
        """Analyze vulnerability scan results"""
        target = results.get("target", "unknown")
        vulns = results.get("data", {}).get("vulnerabilities", [])
        risk_score = results.get("data", {}).get("risk_score", 0)
        summary = results.get("data", {}).get("summary", {})
        
        critical = summary.get("critical", 0)
        high = summary.get("high", 0)
        
        prompt = f"""
You are a cybersecurity expert analyzing vulnerability scan results.

Target: {target}
Total Vulnerabilities: {len(vulns)}
Critical: {critical}, High: {high}
Overall Risk Score: {risk_score}/10

Top CVEs: {[v.get('cve_id') for v in vulns[:3]]}

Provide a brief analysis covering:
1. Severity assessment
2. Immediate actions required
3. Prioritization strategy

Keep the response concise and actionable (max 200 words).
"""
        
        system_prompt = "You are a cybersecurity analyst specializing in vulnerability management and risk assessment."
        
        response = await self.generate(prompt, system_prompt)
        
        return {
            "summary": response,
            "priority_vulns": self._prioritize_vulnerabilities(vulns),
            "remediation_timeline": self._suggest_timeline(summary)
        }
    
    async def _generic_analysis(self, results: Dict) -> Dict:
        """Generic analysis for unknown agent types"""
        prompt = f"""
Analyze these security scan results and provide key insights:

{json.dumps(results.get('data', {}), indent=2)[:1000]}

Provide a brief security analysis (max 150 words).
"""
        
        response = await self.generate(prompt)
        
        return {
            "summary": response,
            "insights": []
        }
    
    def _calculate_attack_surface(self, results: Dict) -> float:
        """Calculate attack surface score"""
        data = results.get("data", {})
        
        score = 0.0
        score += len(data.get("subdomains", [])) * 0.5
        score += len(data.get("open_ports", [])) * 1.0
        score += len(data.get("ip_addresses", [])) * 0.3
        
        return min(score, 10.0)
    
    def _extract_key_findings_recon(self, results: Dict) -> List[str]:
        """Extract key findings from recon"""
        findings = []
        data = results.get("data", {})
        
        subdomains = data.get("subdomains", [])
        if len(subdomains) > 10:
            findings.append(f"Large attack surface: {len(subdomains)} subdomains discovered")
        
        open_ports = data.get("open_ports", [])
        if len(open_ports) > 5:
            findings.append(f"Multiple open ports: {len(open_ports)} services exposed")
        
        return findings
    
    def _identify_risky_services(self, services: List[Dict]) -> List[str]:
        """Identify risky services"""
        risky = []
        risky_services = ["telnet", "ftp", "smb", "rdp", "vnc"]
        
        for service in services:
            service_name = service.get("service", "").lower()
            if any(risky_svc in service_name for risky_svc in risky_services):
                risky.append(f"{service_name} on port {service.get('port')}")
        
        return risky
    
    def _generate_service_recommendations(self, services: List[Dict]) -> List[str]:
        """Generate service-specific recommendations"""
        recommendations = []
        
        for service in services[:5]:
            port = service.get("port")
            service_name = service.get("service", "unknown")
            
            if port in [21, 23]:  # FTP, Telnet
                recommendations.append(f"Disable {service_name} (port {port}) - use secure alternatives")
            elif port == 22:  # SSH
                recommendations.append("Ensure SSH uses key-based authentication")
            elif port in [80, 8080]:  # HTTP
                recommendations.append("Migrate HTTP to HTTPS")
        
        return recommendations
    
    def _prioritize_vulnerabilities(self, vulns: List[Dict]) -> List[Dict]:
        """Prioritize vulnerabilities"""
        sorted_vulns = sorted(
            vulns,
            key=lambda v: v.get("cvss_score", 0),
            reverse=True
        )
        
        return sorted_vulns[:5]
    
    def _suggest_timeline(self, summary: Dict) -> Dict:
        """Suggest remediation timeline"""
        critical = summary.get("critical", 0)
        high = summary.get("high", 0)
        medium = summary.get("medium", 0)
        
        timeline = {}
        
        if critical > 0:
            timeline["immediate"] = f"Patch {critical} critical vulnerabilities within 24 hours"
        
        if high > 0:
            timeline["urgent"] = f"Address {high} high-severity issues within 7 days"
        
        if medium > 0:
            timeline["scheduled"] = f"Plan remediation for {medium} medium-severity issues within 30 days"
        
        return timeline
    
    async def explain_vulnerability(self, cve_id: str, context: Dict) -> str:
        """Explain a specific vulnerability in simple terms"""
        prompt = f"""
Explain this vulnerability in simple terms for a security team:

CVE ID: {cve_id}
CVSS Score: {context.get('cvss_score')}
Affected Service: {context.get('product')} {context.get('version')}

Provide:
1. What the vulnerability is
2. Why it's dangerous
3. How to fix it

Keep it concise (max 150 words).
"""
        
        return await self.generate(prompt)
    
    async def health_check(self) -> bool:
        """Check if LLM is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
