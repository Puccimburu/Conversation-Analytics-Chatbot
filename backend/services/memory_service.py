import asyncio
import logging
from typing import Dict, Any, Optional
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing memory RAG functionality"""
    
    def __init__(self, database, gemini_client):
        self.db = database
        self.gemini_client = gemini_client
        self.memory_manager = None
        self.memory_enhanced_processor = None
        
        # Initialize if database is available
        if database is not None:
            self._initialize_memory_system()
    
    def _initialize_memory_system(self):
        """Initialize the memory RAG system"""
        try:
            self.memory_manager = MemoryRAGManager(self.db, self.gemini_client)
            logger.info("✅ Memory RAG Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Memory RAG: {e}")
            self.memory_manager = None
    
    def create_memory_enhanced_processor(self, base_processor):
        """Create memory-enhanced processor with base processor"""
        if not self.memory_manager:
            return None
        
        try:
            self.memory_enhanced_processor = MemoryEnhancedProcessor(
                base_processor, 
                self.memory_manager, 
                self.gemini_client
            )
            logger.info("✅ Memory-Enhanced Processor ready with Smart Suggestions")
            return self.memory_enhanced_processor
            
        except Exception as e:
            logger.error(f"❌ Failed to create memory-enhanced processor: {e}")
            return None
    
    async def get_memory_stats(self, chat_id):
        """Get memory statistics for a specific chat"""
        if not self.memory_manager:
            return None
        
        try:
            stats = await self.memory_manager.get_chat_memory_stats(chat_id)
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory stats for {chat_id}: {e}")
            return None
    
    async def search_memories(self, chat_id, search_query, limit=10):
        """Search memories in a specific chat"""
        if not self.memory_manager:
            return None
        
        try:
            memories = await self.memory_manager.retrieve_relevant_memories(chat_id, search_query, limit)
            
            # Convert to JSON-serializable format
            memory_data = [
                {
                    "fragment_id": mem.fragment_id,
                    "content": mem.content,
                    "content_type": mem.content_type,
                    "importance_score": mem.importance_score,
                    "keywords": mem.keywords,
                    "entities": mem.entities,
                    "timestamp": mem.timestamp.isoformat(),
                    "access_count": mem.access_count,
                    "last_accessed": mem.last_accessed.isoformat() if mem.last_accessed else None
                } for mem in memories
            ]
            
            return memory_data
            
        except Exception as e:
            logger.error(f"Failed to search memories for {chat_id}: {e}")
            return None
    
    async def process_with_memory(self, user_question, chat_id):
        """Process question with memory enhancement"""
        if not self.memory_enhanced_processor:
            return {"success": False, "error": "Memory-enhanced processor not available"}
        
        try:
            result = await self.memory_enhanced_processor.process_with_memory(user_question, chat_id)
            return result
        except Exception as e:
            logger.error(f"Memory-enhanced processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def is_available(self):
        """Check if memory system is available"""
        return self.memory_manager is not None