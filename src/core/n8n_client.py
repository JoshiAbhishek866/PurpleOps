"""
n8n Client
Integrates with n8n workflow automation platform
"""

import aiohttp
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class N8NClient:
    """
    n8n Workflow Integration Client
    
    Capabilities:
    - Connect to n8n instance
    - Trigger workflows via webhooks
    - Execute workflows via API
    - Retrieve workflow results
    - Manage workflow configurations
    """
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.webhook_url = f"{self.url}/webhook"
        self.api_url = f"{self.url}/api/v1"
        
        # Headers for API requests
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            self.headers["X-N8N-API-KEY"] = self.api_key
        
        logger.info(f"n8n client initialized: {self.url}")
    
    async def trigger_webhook(
        self,
        webhook_path: str,
        data: Dict,
        method: str = "POST"
    ) -> Dict:
        """Trigger n8n workflow via webhook"""
        url = f"{self.webhook_url}{webhook_path}"
        
        logger.info(f"Triggering n8n webhook: {webhook_path}")
        
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "POST":
                    json_data = json.dumps(data, default=json_serial)
                    async with session.post(
                        url,
                        data=json_data,
                        headers={"Content-Type": "application/json"},
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        result = await self._handle_response(response)
                        logger.info(f"Webhook triggered successfully: {webhook_path}")
                        return result
                
                elif method.upper() == "GET":
                    async with session.get(
                        url,
                        params=data,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        result = await self._handle_response(response)
                        logger.info(f"Webhook triggered successfully: {webhook_path}")
                        return result
        
        except aiohttp.ClientError as e:
            logger.error(f"Webhook trigger failed: {e}")
            return {"error": str(e), "status": "failed"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """Execute workflow via n8n API"""
        url = f"{self.api_url}/workflows/{workflow_id}/execute"
        
        logger.info(f"Executing workflow: {workflow_id}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={"data": data or {}},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    result = await self._handle_response(response)
                    logger.info(f"✅ Workflow executed: {workflow_id}")
                    return result
        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow details"""
        url = f"{self.api_url}/workflows/{workflow_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get workflow: {response.status}")
                        return None
        
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            return None
    
    async def list_workflows(self) -> List[Dict]:
        """List all workflows"""
        url = f"{self.api_url}/workflows"
        
        logger.info("Fetching workflow list...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        workflows = data.get("data", [])
                        logger.info(f"Found {len(workflows)} workflows")
                        return workflows
                    else:
                        logger.warning(f"Failed to list workflows: {response.status}")
                        return []
        
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []
    
    async def get_execution(self, execution_id: str) -> Optional[Dict]:
        """Get execution details"""
        url = f"{self.api_url}/executions/{execution_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
        
        except Exception as e:
            logger.error(f"Error getting execution: {e}")
            return None
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """Handle HTTP response"""
        if response.status in [200, 201]:
            try:
                return await response.json()
            except json.JSONDecodeError:
                text = await response.text()
                return {"result": text, "status": "success"}
        else:
            error_text = await response.text()
            logger.error(f"HTTP {response.status}: {error_text}")
            return {
                "error": error_text,
                "status_code": response.status,
                "status": "failed"
            }
    
    async def trigger_agent_workflow(
        self,
        agent_type: str,
        target: str,
        results: Dict
    ) -> Dict:
        """Trigger agent-specific workflow"""
        webhook_path = f"/{agent_type}"
        
        payload = {
            "agent_type": agent_type,
            "target": target,
            "results": results,
            "timestamp": results.get("timestamp")
        }
        
        return await self.trigger_webhook(webhook_path, payload)
    
    async def enrich_results(
        self,
        agent_type: str,
        results: Dict
    ) -> Dict:
        """Send results to n8n for enrichment"""
        webhook_path = f"/enrich/{agent_type}"
        
        logger.info(f"Enriching {agent_type} results via n8n...")
        
        enriched = await self.trigger_webhook(webhook_path, results)
        
        if enriched.get("status") != "failed":
            logger.info(f"✅ Results enriched successfully")
            return enriched
        else:
            logger.warning("⚠️ Enrichment failed, returning original results")
            return results
    
    async def health_check(self) -> bool:
        """Check if n8n is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/healthz",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
