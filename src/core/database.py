"""
MongoDB Database Client for PurpleOps Orchestrator
Handles all database operations
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class Database:
    """MongoDB database client"""
    
    def __init__(self, url: str, db_name: str):
        self.url = url
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_connected = False
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.url)
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self.is_connected = True
            logger.info(f"✅ Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("👋 Disconnected from MongoDB")
    
    # ==================== Agent Results ====================
    
    async def save_result(self, result: Dict) -> str:
        """Save agent execution result"""
        try:
            collection = self.db.agent_results
            
            # Add metadata
            result["created_at"] = datetime.now(timezone.utc)
            result["updated_at"] = datetime.now(timezone.utc)
            
            insert_result = await collection.insert_one(result)
            result_id = str(insert_result.inserted_id)
            
            logger.info(f"💾 Saved result: {result_id}")
            return result_id
        except Exception as e:
            logger.error(f"❌ Failed to save result: {e}")
            raise
    
    async def get_result(self, result_id: str) -> Optional[Dict]:
        """Get agent result by ID"""
        try:
            collection = self.db.agent_results
            result = await collection.find_one({"_id": ObjectId(result_id)})
            
            if result:
                result["id"] = str(result.pop("_id"))
            
            return result
        except Exception as e:
            logger.error(f"❌ Failed to get result: {e}")
            return None
    
    async def get_results_by_agent(
        self,
        agent_type: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict]:
        """Get results by agent type"""
        try:
            collection = self.db.agent_results
            cursor = collection.find(
                {"agent_type": agent_type}
            ).sort("created_at", -1).skip(skip).limit(limit)
            
            results = await cursor.to_list(length=limit)
            
            for result in results:
                result["id"] = str(result.pop("_id"))
            
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get results: {e}")
            return []
    
    async def get_results_by_target(self, target: str) -> List[Dict]:
        """Get all results for a specific target"""
        try:
            collection = self.db.agent_results
            cursor = collection.find({"target": target}).sort("created_at", -1)
            
            results = await cursor.to_list(length=None)
            
            for result in results:
                result["id"] = str(result.pop("_id"))
            
            return results
        except Exception as e:
            logger.error(f"❌ Failed to get results by target: {e}")
            return []
    
    # ==================== Agent Configuration ====================
    
    async def save_agent_config(self, agent_type: str, config: Dict) -> bool:
        """Save agent configuration"""
        try:
            collection = self.db.agent_configs
            
            config_doc = {
                "agent_type": agent_type,
                "config": config,
                "updated_at": datetime.now(timezone.utc)
            }
            
            await collection.update_one(
                {"agent_type": agent_type},
                {"$set": config_doc},
                upsert=True
            )
            
            logger.info(f"💾 Saved config for {agent_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
            return False
    
    async def get_agent_config(self, agent_type: str) -> Optional[Dict]:
        """Get agent configuration"""
        try:
            collection = self.db.agent_configs
            config_doc = await collection.find_one({"agent_type": agent_type})
            
            if config_doc:
                return config_doc.get("config")
            
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get config: {e}")
            return None
    
    # ==================== Workflow Mappings ====================
    
    async def save_workflow_mapping(
        self,
        agent_type: str,
        workflow_id: str,
        webhook_url: str
    ) -> bool:
        """Save n8n workflow mapping"""
        try:
            collection = self.db.workflow_mappings
            
            mapping = {
                "agent_type": agent_type,
                "workflow_id": workflow_id,
                "webhook_url": webhook_url,
                "updated_at": datetime.now(timezone.utc)
            }
            
            await collection.update_one(
                {"agent_type": agent_type},
                {"$set": mapping},
                upsert=True
            )
            
            logger.info(f"💾 Saved workflow mapping for {agent_type}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save workflow mapping: {e}")
            return False
    
    async def get_workflow_mapping(self, agent_type: str) -> Optional[Dict]:
        """Get workflow mapping for agent"""
        try:
            collection = self.db.workflow_mappings
            mapping = await collection.find_one({"agent_type": agent_type})
            
            if mapping:
                mapping["id"] = str(mapping.pop("_id"))
            
            return mapping
        except Exception as e:
            logger.error(f"❌ Failed to get workflow mapping: {e}")
            return None
    
    # ==================== Execution History ====================
    
    async def save_execution(self, execution: Dict) -> str:
        """Save agent execution record"""
        try:
            collection = self.db.executions
            
            execution["created_at"] = datetime.now(timezone.utc)
            
            result = await collection.insert_one(execution)
            execution_id = str(result.inserted_id)
            
            logger.info(f"💾 Saved execution: {execution_id}")
            return execution_id
        except Exception as e:
            logger.error(f"❌ Failed to save execution: {e}")
            raise
    
    async def update_execution(
        self,
        execution_id: str,
        updates: Dict
    ) -> bool:
        """Update execution record"""
        try:
            collection = self.db.executions
            
            updates["updated_at"] = datetime.now(timezone.utc)
            
            result = await collection.update_one(
                {"_id": ObjectId(execution_id)},
                {"$set": updates}
            )
            
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update execution: {e}")
            return False
    
    async def get_execution_history(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get execution history"""
        try:
            collection = self.db.executions
            
            query = {"agent_type": agent_type} if agent_type else {}
            cursor = collection.find(query).sort("created_at", -1).limit(limit)
            
            executions = await cursor.to_list(length=limit)
            
            for execution in executions:
                execution["id"] = str(execution.pop("_id"))
            
            return executions
        except Exception as e:
            logger.error(f"❌ Failed to get execution history: {e}")
            return []
    
    # ==================== Statistics ====================
    
    async def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            stats = {
                "total_results": await self.db.agent_results.count_documents({}),
                "total_executions": await self.db.executions.count_documents({}),
                "total_configs": await self.db.agent_configs.count_documents({}),
                "total_workflows": await self.db.workflow_mappings.count_documents({})
            }
            
            return stats
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}
