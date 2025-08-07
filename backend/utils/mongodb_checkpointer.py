# backend/utils/mongodb_checkpointer.py
"""
MongoDB Checkpointer for LangGraph Workflows
Provides persistent state management using your existing langgraph_checkpoints collection
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
from langchain_core.runnables import RunnableConfig

logger = logging.getLogger(__name__)

class MongoDBCheckpointer(BaseCheckpointSaver):
    """
    Custom LangGraph checkpointer using your existing MongoDB collection
    Integrates with langgraph_checkpoints collection from your config.py
    """
    
    def __init__(self, mongodb_client, collection_name: str = "langgraph_checkpoints"):
        """
        Initialize MongoDB checkpointer
        
        Args:
            mongodb_client: Your existing MongoDB database client
            collection_name: Collection name (matches your config.py schema)
        """
        super().__init__()
        self.db = mongodb_client
        self.collection = mongodb_client[collection_name] if mongodb_client is not None else None
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure proper indexes exist for efficient querying"""
        try:
            if self.collection is not None:
                # Create indexes matching your existing schema
                self.collection.create_index([("thread_id", 1), ("checkpoint_id", 1)])
                self.collection.create_index([("thread_id", 1), ("last_updated", -1)])
                self.collection.create_index("workflowType")
                logger.info("✅ MongoDB checkpointer indexes ensured")
        except Exception as e:
            logger.warning(f"Failed to create checkpointer indexes: {e}")
    
    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata
    ) -> RunnableConfig:
        """
        Save checkpoint to MongoDB collection
        
        Args:
            config: LangGraph configuration
            checkpoint: Current workflow state
            metadata: Checkpoint metadata
            
        Returns:
            Updated configuration
        """
        try:
            if self.collection is None:
                logger.warning("MongoDB collection not available for checkpointing")
                return config
            
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                logger.warning("No thread_id provided for checkpointing")
                return config
            
            # Create checkpoint document matching your schema
            checkpoint_doc = {
                "_id": f"{thread_id}_{checkpoint.get('id', datetime.now().timestamp())}",
                "thread_id": thread_id,
                "checkpointId": checkpoint.get("id"),
                "state": self._serialize_state(checkpoint),
                "metadata": self._serialize_metadata(metadata),
                "last_updated": datetime.now(timezone.utc),
                "workflowType": config.get("configurable", {}).get("workflow_type", "analytics"),
                
                # Additional fields for your analytics workflows
                "user_id": config.get("configurable", {}).get("user_id"),
                "chat_id": config.get("configurable", {}).get("chat_id"),
                "original_question": config.get("configurable", {}).get("original_question"),
                "current_step": checkpoint.get("channel_values", {}).get("current_step"),
                "success": checkpoint.get("channel_values", {}).get("success", False)
            }
            
            # Upsert checkpoint
            result = self.collection.replace_one(
                {"thread_id": thread_id, "checkpointId": checkpoint_doc["checkpointId"]},
                checkpoint_doc,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Saved checkpoint for thread {thread_id}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return config
    
    def get_tuple(self, config: RunnableConfig) -> Optional[tuple]:
        """
        Retrieve checkpoint from MongoDB
        
        Args:
            config: LangGraph configuration
            
        Returns:
            Tuple of (config, checkpoint, metadata) or None
        """
        try:
            if self.collection is None:
                return None
                
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return None
            
            # Find most recent checkpoint for thread
            doc = self.collection.find_one(
                {"thread_id": thread_id},
                sort=[("last_updated", -1)]
            )
            
            if not doc:
                return None
            
            # Deserialize checkpoint data
            checkpoint = self._deserialize_state(doc.get("state", {}))
            metadata = self._deserialize_metadata(doc.get("metadata", {}))
            
            logger.info(f"✅ Retrieved checkpoint for thread {thread_id}")
            return (config, checkpoint, metadata)
            
        except Exception as e:
            logger.error(f"Failed to retrieve checkpoint: {e}")
            return None
    
    def list(self, config: RunnableConfig, limit: int = 10) -> List[tuple]:
        """
        List recent checkpoints for a thread
        
        Args:
            config: LangGraph configuration
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of (config, checkpoint, metadata) tuples
        """
        try:
            if self.collection is None:
                return []
                
            thread_id = config.get("configurable", {}).get("thread_id")
            if not thread_id:
                return []
            
            # Get recent checkpoints
            docs = list(self.collection.find(
                {"thread_id": thread_id},
                sort=[("last_updated", -1)],
                limit=limit
            ))
            
            results = []
            for doc in docs:
                checkpoint = self._deserialize_state(doc.get("state", {}))
                metadata = self._deserialize_metadata(doc.get("metadata", {}))
                results.append((config, checkpoint, metadata))
            
            logger.info(f"Retrieved {len(results)} checkpoints for thread {thread_id}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to list checkpoints: {e}")
            return []
    
    def _serialize_state(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """Serialize checkpoint state for MongoDB storage"""
        try:
            # Extract channel values (the actual workflow state)
            state = checkpoint.get("channel_values", {})
            
            # Ensure JSON serializable
            return self._make_json_serializable(state)
            
        except Exception as e:
            logger.error(f"Failed to serialize checkpoint state: {e}")
            return {}
    
    def _deserialize_state(self, state_data: Dict[str, Any]) -> Checkpoint:
        """Deserialize checkpoint state from MongoDB"""
        try:
            return {
                "channel_values": state_data,
                "channel_versions": {},
                "versions_seen": {},
                "id": state_data.get("checkpoint_id", "unknown")
            }
        except Exception as e:
            logger.error(f"Failed to deserialize checkpoint state: {e}")
            return {"channel_values": {}, "channel_versions": {}, "versions_seen": {}}
    
    def _serialize_metadata(self, metadata: CheckpointMetadata) -> Dict[str, Any]:
        """Serialize metadata for storage"""
        try:
            return self._make_json_serializable(dict(metadata) if metadata else {})
        except Exception as e:
            logger.error(f"Failed to serialize metadata: {e}")
            return {}
    
    def _deserialize_metadata(self, metadata_data: Dict[str, Any]) -> CheckpointMetadata:
        """Deserialize metadata from storage"""
        try:
            return CheckpointMetadata(**metadata_data) if metadata_data else CheckpointMetadata()
        except Exception as e:
            logger.error(f"Failed to deserialize metadata: {e}")
            return CheckpointMetadata()
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Recursively make object JSON serializable"""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        else:
            # Convert other types to string representation
            try:
                return str(obj)
            except Exception:
                return None
    
    # Workflow-specific helper methods
    def get_workflow_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get workflow execution history for a user"""
        try:
            if self.collection is None:
                return []
            
            docs = list(self.collection.find(
                {"user_id": user_id},
                sort=[("last_updated", -1)],
                limit=limit
            ))
            
            history = []
            for doc in docs:
                history.append({
                    "thread_id": doc.get("thread_id"),
                    "workflow_type": doc.get("workflowType"),
                    "original_question": doc.get("original_question"),
                    "current_step": doc.get("current_step"),
                    "success": doc.get("success"),
                    "last_updated": doc.get("last_updated"),
                    "chat_id": doc.get("chat_id")
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get workflow history: {e}")
            return []
    
    def get_active_workflows(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get currently active (incomplete) workflows"""
        try:
            if self.collection is None:
                return []
            
            query = {"success": {"$ne": True}}
            if user_id:
                query["user_id"] = user_id
            
            docs = list(self.collection.find(
                query,
                sort=[("last_updated", -1)],
                limit=20
            ))
            
            active = []
            for doc in docs:
                active.append({
                    "thread_id": doc.get("thread_id"),
                    "workflow_type": doc.get("workflowType"),
                    "original_question": doc.get("original_question"),
                    "current_step": doc.get("current_step"),
                    "last_updated": doc.get("last_updated"),
                    "user_id": doc.get("user_id"),
                    "chat_id": doc.get("chat_id")
                })
            
            return active
            
        except Exception as e:
            logger.error(f"Failed to get active workflows: {e}")
            return []
    
    def cleanup_old_checkpoints(self, days_old: int = 30) -> int:
        """Clean up old completed checkpoints"""
        try:
            if self.collection is None:
                return 0
            
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            result = self.collection.delete_many({
                "success": True,
                "last_updated": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old checkpoints")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0