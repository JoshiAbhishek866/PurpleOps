"""
Dual LLM Orchestrator for PurpleOps
Coordinates Offensive (Red Team) and Defensive (Blue Team) AI models
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from enum import Enum

class ThreatLevel(Enum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class DualLLMOrchestrator:
    def __init__(
        self,
        offensive_model: str = "codellama:7b",
        defensive_model: str = "llama3:8b",
        ollama_url: str = "http://localhost:11434"
    ):
        self.offensive_model = offensive_model
        self.defensive_model = defensive_model
        self.ollama_url = ollama_url
        self.attack_log = []
        self.defense_log = []
        self.threat_history = []
        
    def _generate_response(self, model: str, prompt: str, system_prompt: str = "") -> str:
        """
        Generate response from Ollama model
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    async def offensive_scan(self, target: Dict) -> Dict:
        """
        🔴 Offensive LLM: Scan for vulnerabilities
        
        Args:
            target: Dictionary containing:
                - type: 'code', 'api', 'network', 'config'
                - data: The actual content to scan
                - context: Optional additional context
        
        Returns:
            Dictionary with vulnerability findings
        """
        system_prompt = """You are an elite penetration testing AI (Red Team).
Your mission is to identify security vulnerabilities with precision.

Analyze the target and provide:
1. Vulnerability type (e.g., SQL Injection, XSS, CSRF, etc.)
2. Severity level (Critical/High/Medium/Low)
3. Attack vector description
4. Potential impact
5. OWASP category (if applicable)

Be thorough and technical. Think like an attacker."""

        prompt = f"""
Analyze this target for security vulnerabilities:

Target Type: {target.get('type', 'unknown')}
Target Data:
{target.get('data', '')}

Context: {target.get('context', 'No additional context')}

Provide detailed vulnerability analysis.
"""
        
        print(f"🔴 Offensive LLM: Scanning {target.get('type')}...")
        response = self._generate_response(
            self.offensive_model,
            prompt,
            system_prompt
        )
        
        findings = {
            'id': f"vuln_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'vulnerabilities': response,
            'model': 'offensive',
            'threat_level': self._extract_threat_level(response)
        }
        
        self.attack_log.append(findings)
        return findings
    
    async def defensive_patch(self, vulnerability: Dict) -> Dict:
        """
        🔵 Defensive LLM: Generate patches and mitigations
        
        Args:
            vulnerability: Output from offensive_scan()
        
        Returns:
            Dictionary with patch recommendations
        """
        system_prompt = """You are an expert security defense AI (Blue Team).
Your mission is to protect systems by providing immediate, actionable solutions.

For each vulnerability, provide:
1. Immediate mitigation steps
2. Code patch (if applicable)
3. Security controls to implement
4. Monitoring recommendations
5. Prevention strategies

Be practical and implementation-focused. Prioritize quick wins."""

        prompt = f"""
VULNERABILITY DETECTED:

{vulnerability.get('vulnerabilities', '')}

Target Information:
Type: {vulnerability.get('target', {}).get('type')}
Threat Level: {vulnerability.get('threat_level', 'UNKNOWN')}

Provide comprehensive defense measures and patches.
"""
        
        print(f"🔵 Defensive LLM: Generating patches...")
        response = self._generate_response(
            self.defensive_model,
            prompt,
            system_prompt
        )
        
        defense = {
            'id': f"patch_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'vulnerability_id': vulnerability.get('id'),
            'patch': response,
            'model': 'defensive',
            'actions': self._extract_actions(response)
        }
        
        self.defense_log.append(defense)
        return defense
    
    async def attack_defense_cycle(self, target: Dict) -> Dict:
        """
        Complete Red Team → Blue Team cycle
        
        Args:
            target: Target to analyze
        
        Returns:
            Complete analysis with vulnerabilities and patches
        """
        print("\n" + "="*60)
        print("🔄 Starting Attack-Defense Cycle")
        print("="*60)
        
        # Step 1: Offensive scan
        vulnerabilities = await self.offensive_scan(target)
        
        # Step 2: Defensive response
        patches = await self.defensive_patch(vulnerabilities)
        
        # Step 3: Log cycle
        cycle_result = {
            'cycle_id': f"cycle_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'vulnerabilities': vulnerabilities,
            'patches': patches,
            'status': 'completed',
            'threat_level': vulnerabilities.get('threat_level')
        }
        
        self.threat_history.append(cycle_result)
        
        print("✅ Cycle completed")
        print("="*60 + "\n")
        
        return cycle_result
    
    async def real_time_threat_detection(self, network_traffic: Dict) -> Dict:
        """
        Real-time threat detection and automated response
        
        Args:
            network_traffic: Dictionary containing:
                - source_ip
                - destination
                - protocol
                - payload
                - headers (optional)
        
        Returns:
            Threat analysis and response actions
        """
        # Offensive LLM analyzes for attack patterns
        attack_analysis = await self._analyze_traffic_offensive(network_traffic)
        
        if attack_analysis['threat_detected']:
            print(f"🚨 THREAT DETECTED: {attack_analysis['threat_level']}")
            
            # Defensive LLM responds
            response = await self._respond_to_threat(attack_analysis)
            
            # Execute defensive actions
            await self._execute_defense(response['actions'])
            
            return {
                'threat_detected': True,
                'analysis': attack_analysis,
                'response': response,
                'status': 'defended'
            }
        
        return {
            'threat_detected': False,
            'status': 'clean'
        }
    
    async def _analyze_traffic_offensive(self, traffic: Dict) -> Dict:
        """
        Offensive LLM analyzes network traffic
        """
        system_prompt = """You are a network security analyst AI specializing in threat detection.
Analyze network traffic for malicious patterns.

Detect:
- DDoS attacks
- SQL injection attempts
- XSS attacks
- Brute force attempts
- Port scanning
- Malware communication
- Data exfiltration

Classify threat level: NONE, LOW, MEDIUM, HIGH, or CRITICAL"""

        prompt = f"""
Analyze this network traffic:

Source IP: {traffic.get('source_ip', 'unknown')}
Destination: {traffic.get('destination', 'unknown')}
Protocol: {traffic.get('protocol', 'unknown')}
Payload: {traffic.get('payload', '')}
Headers: {traffic.get('headers', {})}

Is this malicious traffic? What attack patterns do you detect?
Provide threat level and reasoning.
"""
        
        response = self._generate_response(
            self.offensive_model,
            prompt,
            system_prompt
        )
        
        threat_level = self._extract_threat_level(response)
        threat_detected = threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
        
        return {
            'threat_detected': threat_detected,
            'threat_level': threat_level.name,
            'analysis': response,
            'traffic': traffic,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _respond_to_threat(self, threat: Dict) -> Dict:
        """
        Defensive LLM generates immediate response
        """
        system_prompt = """You are an incident response AI. Respond to threats IMMEDIATELY.

Provide:
1. BLOCK or ALLOW decision
2. Firewall rules (iptables format)
3. IDS/IPS signatures
4. Incident response steps
5. Alert priority

Be decisive and fast. Lives may depend on it."""

        prompt = f"""
URGENT THREAT DETECTED:

Threat Level: {threat['threat_level']}
Analysis: {threat['analysis']}

Traffic Details:
{json.dumps(threat['traffic'], indent=2)}

Provide IMMEDIATE response actions. Format your response clearly.
"""
        
        response = self._generate_response(
            self.defensive_model,
            prompt,
            system_prompt
        )
        
        return {
            'threat': threat,
            'response': response,
            'actions': self._extract_actions(response),
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_threat_level(self, text: str) -> ThreatLevel:
        """
        Extract threat level from LLM response
        """
        text_upper = text.upper()
        
        if 'CRITICAL' in text_upper:
            return ThreatLevel.CRITICAL
        elif 'HIGH' in text_upper:
            return ThreatLevel.HIGH
        elif 'MEDIUM' in text_upper:
            return ThreatLevel.MEDIUM
        elif 'LOW' in text_upper:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.NONE
    
    def _extract_actions(self, text: str) -> List[Dict]:
        """
        Extract actionable items from defensive response
        """
        actions = []
        text_upper = text.upper()
        
        if 'BLOCK' in text_upper:
            actions.append({
                'type': 'firewall',
                'action': 'block',
                'priority': 'immediate'
            })
        
        if 'ALERT' in text_upper or 'NOTIFY' in text_upper:
            actions.append({
                'type': 'notification',
                'priority': 'high',
                'action': 'alert_soc'
            })
        
        if 'PATCH' in text_upper:
            actions.append({
                'type': 'patch',
                'action': 'apply_fix',
                'priority': 'high'
            })
        
        if 'MONITOR' in text_upper:
            actions.append({
                'type': 'monitoring',
                'action': 'increase_logging',
                'priority': 'medium'
            })
        
        return actions
    
    async def _execute_defense(self, actions: List[Dict]):
        """
        Execute defensive actions
        (Integrate with your actual infrastructure)
        """
        for action in actions:
            print(f"🛡️  Executing: {action['type']} - {action['action']}")
            
            if action['type'] == 'firewall':
                # TODO: Integrate with firewall API
                print(f"   → Blocking IP via firewall")
            
            elif action['type'] == 'notification':
                # TODO: Send alert to SOC
                print(f"   → Sending alert to security team")
            
            elif action['type'] == 'patch':
                # TODO: Apply security patch
                print(f"   → Applying security patch")
            
            elif action['type'] == 'monitoring':
                # TODO: Increase monitoring
                print(f"   → Increasing monitoring level")
    
    def get_statistics(self) -> Dict:
        """
        Get orchestrator statistics
        """
        return {
            'total_scans': len(self.attack_log),
            'total_patches': len(self.defense_log),
            'total_cycles': len(self.threat_history),
            'critical_threats': sum(
                1 for t in self.threat_history 
                if t.get('threat_level') == ThreatLevel.CRITICAL.name
            ),
            'high_threats': sum(
                1 for t in self.threat_history 
                if t.get('threat_level') == ThreatLevel.HIGH.name
            )
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_code_scan():
    """
    Example: Scan vulnerable code
    """
    orchestrator = DualLLMOrchestrator()
    
    target = {
        'type': 'code',
        'data': '''
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    return cursor.fetchone()
        ''',
        'context': 'Python Flask login function'
    }
    
    result = await orchestrator.attack_defense_cycle(target)
    print(json.dumps(result, indent=2))


async def example_api_scan():
    """
    Example: Scan API endpoint
    """
    orchestrator = DualLLMOrchestrator()
    
    target = {
        'type': 'api',
        'data': '''
GET /api/users/{id}
No authentication required
Returns: {"id": 123, "email": "user@example.com", "ssn": "123-45-6789"}
        ''',
        'context': 'REST API endpoint'
    }
    
    result = await orchestrator.attack_defense_cycle(target)
    print(json.dumps(result, indent=2))


async def example_traffic_analysis():
    """
    Example: Real-time traffic analysis
    """
    orchestrator = DualLLMOrchestrator()
    
    # Suspicious traffic
    traffic = {
        'source_ip': '192.168.1.100',
        'destination': 'api.PurpleOps.com/login',
        'protocol': 'HTTP',
        'payload': "username=admin' OR '1'='1'--&password=anything",
        'headers': {
            'User-Agent': 'sqlmap/1.0'
        }
    }
    
    result = await orchestrator.real_time_threat_detection(traffic)
    print(json.dumps(result, indent=2))


async def main():
    """
    Run all examples
    """
    print("🚀 PurpleOps Dual LLM Orchestrator Demo\n")
    
    # Example 1: Code vulnerability scan
    print("\n📝 Example 1: Scanning vulnerable code...")
    await example_code_scan()
    
    # Example 2: API security scan
    print("\n🌐 Example 2: Scanning API endpoint...")
    await example_api_scan()
    
    # Example 3: Real-time threat detection
    print("\n🚨 Example 3: Analyzing suspicious traffic...")
    await example_traffic_analysis()


if __name__ == "__main__":
    asyncio.run(main())
