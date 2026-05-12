from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool
import boto3
from datetime import datetime
from src.config import Config

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=Config.AWS_REGION)
audit_table = dynamodb.Table(Config.DYNAMODB_TABLE_AUDIT)

@tool
def execute_sql_injection(target_url: str, payload: str) -> dict:
    """Execute SQL injection attack against target URL with safety checks"""
    # Safety check: reject production targets
    if "prod" in target_url.lower() or "production" in target_url.lower():
        return {
            "status": "rejected",
            "reason": "Production target detected - attack blocked",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Log attack attempt
    audit_table.put_item(Item={
        "session_id": "current_session",
        "event_timestamp": int(datetime.utcnow().timestamp()),
        "agent_type": "RED",
        "action": "sql_injection_attempt",
        "target": target_url,
        "payload": payload,
        "outcome": "simulated"
    })
    
    return {
        "status": "executed",
        "attack_type": "SQL Injection",
        "target": target_url,
        "payload": payload,
        "simulated_result": "Vulnerability detected - SQL error returned",
        "timestamp": datetime.utcnow().isoformat()
    }

@tool
def test_xss_vulnerability(target_url: str, payload: str) -> dict:
    """Test XSS vulnerability on target endpoint"""
    audit_table.put_item(Item={
        "session_id": "current_session",
        "event_timestamp": int(datetime.utcnow().timestamp()),
        "agent_type": "RED",
        "action": "xss_test",
        "target": target_url,
        "payload": payload,
        "outcome": "simulated"
    })
    
    return {
        "status": "executed",
        "attack_type": "XSS",
        "target": target_url,
        "payload": payload,
        "simulated_result": "XSS payload reflected in response",
        "timestamp": datetime.utcnow().isoformat()
    }

@tool
def test_privilege_escalation(iam_role: str) -> dict:
    """Test IAM privilege escalation vectors"""
    audit_table.put_item(Item={
        "session_id": "current_session",
        "event_timestamp": int(datetime.utcnow().timestamp()),
        "agent_type": "RED",
        "action": "privilege_escalation_test",
        "target": iam_role,
        "outcome": "simulated"
    })
    
    return {
        "status": "executed",
        "attack_type": "Privilege Escalation",
        "target_role": iam_role,
        "simulated_result": "Overly permissive IAM policy detected",
        "timestamp": datetime.utcnow().isoformat()
    }

class RedAgent:
    def __init__(self):
        self.llm = ChatBedrock(
            model_id=Config.BEDROCK_MODEL_ID,
            region_name=Config.AWS_REGION,
            model_kwargs={
                "temperature": Config.BEDROCK_TEMPERATURE,
                "max_tokens": Config.BEDROCK_MAX_TOKENS,
                "top_p": Config.BEDROCK_TOP_P
            }
        )
        
        self.tools = [execute_sql_injection, test_xss_vulnerability, test_privilege_escalation]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Red Team AI agent for Sentinel AI, an autonomous purple teaming platform.
            
Your mission: Identify and validate security vulnerabilities through controlled exploitation.

Rules:
1. NEVER target production systems or customer data
2. Always log your actions to the audit trail
3. Use the provided tools to execute attacks
4. Focus on: SQL injection, XSS, privilege escalation, API abuse
5. Provide detailed attack reports for the Blue Agent to learn from

You have access to these attack tools:
- execute_sql_injection: Test SQL injection vulnerabilities
- test_xss_vulnerability: Test cross-site scripting vulnerabilities  
- test_privilege_escalation: Test IAM privilege escalation

Analyze the target infrastructure and execute appropriate attacks."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
    
    def execute_campaign(self, target_info: dict) -> dict:
        """Execute offensive campaign against target infrastructure"""
        input_text = f"""
Target Infrastructure: {target_info.get('description', 'Unknown')}
Target URL: {target_info.get('url', 'http://test-target.example.com')}
Target IAM Role: {target_info.get('iam_role', 'test-role')}

Execute a comprehensive security validation campaign. Test for:
1. SQL injection vulnerabilities
2. XSS vulnerabilities
3. Privilege escalation opportunities

Report your findings."""
        
        result = self.executor.invoke({"input": input_text})
        return result
