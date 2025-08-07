# backend/utils/mem0.py
"""
Mem0 Enhanced Memory System for Conversational Analytics
Provides intelligent memory management with cross-session continuity and user preference learning
"""

import logging
import asyncio
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Conditional Mem0 import with graceful fallback
try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logging.warning("Mem0 not available - install with: pip install mem0ai")

logger = logging.getLogger(__name__)

def utc_now():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

@dataclass
class ConversationMemory:
    """Structure for conversation memories"""
    memory_id: str
    user_id: str
    chat_id: str
    content: str
    memory_type: str  # 'preference', 'query_pattern', 'insight', 'feedback'
    importance_score: float
    timestamp: datetime
    metadata: Dict[str, Any]

class Mem0EnhancedMemoryManager:
    """Enhanced Memory Manager using Mem0 for intelligent context and user learning"""
    
    def __init__(self, mongodb_client=None, config=None):
        """
        Initialize Mem0 Enhanced Memory Manager
        
        Args:
            mongodb_client: MongoDB client for backup storage
            config: Optional Mem0 configuration
        """
        self.db = mongodb_client
        self.memory_collection = mongodb_client.chat_memories if mongodb_client is not None else None
        self.mem0 = None
        self.mem0_available = MEM0_AVAILABLE
        
        # Initialize Mem0 with optimized configuration
        if self.mem0_available:
            try:
                # Initialize Mem0 with real OpenAI API key for full functionality
                import os
                
                # Get OpenAI API key from environment
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    os.environ['OPENAI_API_KEY'] = openai_key
                
                # Initialize with default config (now with full LLM capabilities)
                self.mem0 = Memory()
                logger.info("✅ Mem0 Enhanced Memory System initialized successfully")
                
                # Test Mem0 functionality
                self._test_mem0_connection()
                
            except Exception as e:
                logger.error(f"Failed to initialize Mem0: {e}")
                self.mem0_available = False
                self.mem0 = None
        
        # Fallback indexes for MongoDB
        if self.memory_collection is not None and not self.mem0_available:
            self._ensure_mongodb_indexes()
    
    def _test_mem0_connection(self):
        """Test Mem0 connectivity and functionality"""
        try:
            test_memory = "System test - analytics preferences initialized"
            self.mem0.add(test_memory, user_id="system_test")
            logger.info("✅ Mem0 connectivity test passed")
        except Exception as e:
            logger.warning(f"Mem0 connectivity test failed: {e}")
    
    def _ensure_mongodb_indexes(self):
        """Ensure MongoDB indexes exist for fallback mode"""
        try:
            if self.memory_collection is not None:
                self.memory_collection.create_index([("user_id", 1), ("timestamp", -1)])
                self.memory_collection.create_index("importance_score")
                self.memory_collection.create_index("memory_type")
                logger.info("✅ MongoDB memory indexes created")
        except Exception as e:
            logger.warning(f"Failed to create MongoDB indexes: {e}")
    
    async def store_conversation_memory(self, user_id: str, chat_id: str, content: str, 
                                      memory_type: str, metadata: Dict = None) -> bool:
        """
        Store conversation memory with intelligent processing
        
        Args:
            user_id: User identifier
            chat_id: Chat session identifier  
            content: Memory content to store
            memory_type: Type of memory ('question', 'answer', 'preference', 'insight')
            metadata: Additional metadata
            
        Returns:
            bool: Success status
        """
        try:
            metadata = metadata or {}
            metadata.update({
                "chat_id": chat_id,
                "memory_type": memory_type,
                "timestamp": utc_now().isoformat(),
                "domain": "conversational_analytics"
            })
            
            if self.mem0_available and self.mem0:
                # Store in Mem0 for intelligent retrieval
                formatted_content = self._format_memory_content(content, memory_type)
                
                # Use executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.mem0.add(formatted_content, user_id=user_id, metadata=metadata)
                )
                
                logger.debug(f"Stored memory in Mem0: {memory_type} for user {user_id}")
                return True
            
            elif self.memory_collection is not None:
                # Fallback to MongoDB storage
                return await self._store_in_mongodb(user_id, chat_id, content, memory_type, metadata)
            
            else:
                logger.warning("No memory storage available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store conversation memory: {e}")
            return False
    
    def _format_memory_content(self, content: str, memory_type: str) -> str:
        """Format memory content for optimal Mem0 storage"""
        if memory_type == 'question':
            return f"User asked about analytics: {content}"
        elif memory_type == 'answer':
            return f"System provided analysis: {content}"
        elif memory_type == 'preference':
            return f"User preference learned: {content}"
        elif memory_type == 'insight':
            return f"Key insight discovered: {content}"
        elif memory_type == 'feedback':
            return f"User feedback received: {content}"
        else:
            return content
    
    async def _store_in_mongodb(self, user_id: str, chat_id: str, content: str, 
                              memory_type: str, metadata: Dict) -> bool:
        """Fallback MongoDB storage"""
        try:
            memory_doc = {
                "memory_id": self._generate_memory_id(user_id, content),
                "user_id": user_id,
                "chat_id": chat_id,
                "content": content,
                "memory_type": memory_type,
                "importance_score": self._calculate_importance(content, memory_type),
                "timestamp": utc_now(),
                "metadata": metadata
            }
            
            self.memory_collection.insert_one(memory_doc)
            return True
            
        except Exception as e:
            logger.error(f"MongoDB memory storage failed: {e}")
            return False
    
    async def get_relevant_context(self, user_id: str, question: str, limit: int = 5) -> str:
        """
        Get relevant context for the current question using intelligent retrieval
        
        Args:
            user_id: User identifier
            question: Current question
            limit: Maximum number of relevant memories
            
        Returns:
            str: Formatted context string
        """
        try:
            if self.mem0_available and self.mem0:
                return await self._get_mem0_context(user_id, question, limit)
            elif self.memory_collection is not None:
                return await self._get_mongodb_context(user_id, question, limit)
            else:
                return f"DOMAIN: Conversational Analytics\nCURRENT QUESTION: {question}"
                
        except Exception as e:
            logger.error(f"Failed to get relevant context: {e}")
            return f"CURRENT QUESTION: {question}"
    
    async def _get_mem0_context(self, user_id: str, question: str, limit: int) -> str:
        """Get intelligent context from Mem0"""
        try:
            loop = asyncio.get_event_loop()
            
            # Search for relevant memories
            relevant_memories = await loop.run_in_executor(
                None,
                lambda: self.mem0.search(question, user_id=user_id, limit=limit)
            )
            
            if not relevant_memories:
                return f"DOMAIN: Conversational Analytics\nCURRENT QUESTION: {question}"
            
            context_parts = [
                "DOMAIN: Conversational Analytics",
                f"USER CONTEXT (Mem0 Enhanced):"
            ]
            
            # Process relevant memories
            preferences = []
            insights = []
            patterns = []
            
            for memory in relevant_memories:
                memory_text = memory.get('memory', '')
                score = memory.get('score', 0)
                
                if score > 0.7:  # High relevance only
                    if 'preference' in memory_text.lower():
                        preferences.append(f"  • {memory_text}")
                    elif 'insight' in memory_text.lower():
                        insights.append(f"  • {memory_text}")
                    else:
                        patterns.append(f"  • {memory_text}")
            
            # Add structured context
            if preferences:
                context_parts.append("USER PREFERENCES:")
                context_parts.extend(preferences[:2])
            
            if patterns:
                context_parts.append("QUERY PATTERNS:")
                context_parts.extend(patterns[:2])
            
            if insights:
                context_parts.append("RELEVANT INSIGHTS:")
                context_parts.extend(insights[:2])
            
            context_parts.append(f"\nCURRENT QUESTION: {question}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Mem0 context retrieval failed: {e}")
            return f"CURRENT QUESTION: {question}"
    
    async def _get_mongodb_context(self, user_id: str, question: str, limit: int) -> str:
        """Fallback MongoDB context retrieval"""
        try:
            # Extract keywords from question
            keywords = self._extract_analytics_keywords(question)
            
            # Build query
            query = {
                "user_id": user_id,
                "$or": [
                    {"content": {"$regex": "|".join(keywords), "$options": "i"}},
                    {"importance_score": {"$gte": 0.7}}
                ]
            }
            
            memories = list(self.memory_collection.find(query)
                          .sort([("importance_score", -1), ("timestamp", -1)])
                          .limit(limit))
            
            context_parts = ["DOMAIN: Conversational Analytics"]
            
            if memories:
                context_parts.append("RECENT CONTEXT:")
                for memory in memories:
                    content = memory['content']
                    snippet = content[:100] + "..." if len(content) > 100 else content
                    context_parts.append(f"  • {snippet}")
            
            context_parts.append(f"\nCURRENT QUESTION: {question}")
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"MongoDB context retrieval failed: {e}")
            return f"CURRENT QUESTION: {question}"
    
    async def learn_user_preference(self, user_id: str, preference_data: Dict[str, Any]) -> bool:
        """
        Learn and store user preferences for future queries
        
        Args:
            user_id: User identifier
            preference_data: Dictionary containing preference information
            
        Returns:
            bool: Success status
        """
        try:
            # Format preference for storage
            preference_content = self._format_preference(preference_data)
            
            metadata = {
                "type": "user_preference",
                "category": preference_data.get('category', 'general'),
                "confidence": preference_data.get('confidence', 0.8),
                "timestamp": utc_now().isoformat()
            }
            
            return await self.store_conversation_memory(
                user_id=user_id,
                chat_id=preference_data.get('chat_id', 'preference_learning'),
                content=preference_content,
                memory_type='preference',
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to learn user preference: {e}")
            return False
    
    def _format_preference(self, preference_data: Dict[str, Any]) -> str:
        """Format preference data for storage"""
        category = preference_data.get('category', '')
        details = preference_data.get('details', '')
        
        if category == 'chart_type':
            return f"User prefers {details} charts for {preference_data.get('context', 'data visualization')}"
        elif category == 'data_breakdown':
            return f"User typically wants data broken down by {details}"
        elif category == 'query_style':
            return f"User query pattern: {details}"
        else:
            return f"User preference in {category}: {details}"
    
    async def get_smart_suggestions(self, user_id: str, current_context: str) -> List[str]:
        """
        Generate smart suggestions based on user history and preferences
        
        Args:
            user_id: User identifier
            current_context: Current conversation context
            
        Returns:
            List[str]: Smart suggestions
        """
        try:
            if self.mem0_available and self.mem0:
                return await self._get_mem0_suggestions(user_id, current_context)
            else:
                return await self._get_fallback_suggestions(current_context)
                
        except Exception as e:
            logger.error(f"Failed to get smart suggestions: {e}")
            return self._get_default_suggestions()
    
    async def _get_mem0_suggestions(self, user_id: str, context: str) -> List[str]:
        """Get intelligent suggestions from Mem0"""
        try:
            loop = asyncio.get_event_loop()
            
            # Search for user patterns and preferences
            user_patterns = await loop.run_in_executor(
                None,
                lambda: self.mem0.search("user query patterns preferences", user_id=user_id, limit=5)
            )
            
            suggestions = []
            
            # Analyze patterns to generate suggestions
            if user_patterns:
                for pattern in user_patterns:
                    memory_text = pattern.get('memory', '').lower()
                    
                    # Extract suggestion patterns
                    if 'cost' in memory_text and 'cost' not in context.lower():
                        suggestions.append("What are our AI operational costs this month?")
                    elif 'document' in memory_text and 'document' not in context.lower():
                        suggestions.append("Show document processing efficiency trends")
                    elif 'compliance' in memory_text and 'compliance' not in context.lower():
                        suggestions.append("Display compliance obligation status")
                    elif 'performance' in memory_text and 'performance' not in context.lower():
                        suggestions.append("Analyze AI agent performance metrics")
            
            # Ensure we have at least 3 suggestions
            if len(suggestions) < 3:
                default_suggestions = [
                    "Compare processing costs by document type",
                    "Show extraction confidence trends over time", 
                    "Which compliance obligations need attention?"
                ]
                suggestions.extend(default_suggestions[:3-len(suggestions)])
            
            return suggestions[:3]
            
        except Exception as e:
            logger.error(f"Mem0 suggestions failed: {e}")
            return self._get_default_suggestions()
    
    async def _get_fallback_suggestions(self, context: str) -> List[str]:
        """Generate contextual suggestions without Mem0"""
        context_lower = context.lower()
        
        if 'cost' in context_lower:
            return [
                "Show cost breakdown by time period",
                "Compare costs across different operations",
                "What's driving our highest costs?"
            ]
        elif 'document' in context_lower:
            return [
                "Display document processing success rates",
                "Show confidence scores by document type",
                "Which documents need reprocessing?"
            ]
        elif 'compliance' in context_lower:
            return [
                "Show compliance status overview",
                "Which obligations are overdue?",
                "Display compliance trends over time"
            ]
        else:
            return self._get_default_suggestions()
    
    def _get_default_suggestions(self) -> List[str]:
        """Default analytics suggestions"""
        return [
            "Show AI operational costs overview",
            "Display document processing efficiency",
            "Analyze compliance obligation status"
        ]
    
    def _extract_analytics_keywords(self, content: str) -> List[str]:
        """Extract relevant analytics keywords from content"""
        analytics_keywords = [
            'cost', 'spending', 'expense', 'token', 'model', 'pricing',
            'document', 'extraction', 'processing', 'confidence', 'accuracy',
            'compliance', 'obligation', 'requirement', 'audit',
            'agent', 'performance', 'efficiency', 'success', 'failure',
            'batch', 'file', 'data', 'analysis', 'trend', 'metric'
        ]
        
        content_lower = content.lower()
        found_keywords = [kw for kw in analytics_keywords if kw in content_lower]
        
        # Add numeric patterns
        numbers = re.findall(r'\d+(?:\.\d+)?[%$]?', content)
        found_keywords.extend(numbers)
        
        return list(set(found_keywords))[:10]
    
    def _calculate_importance(self, content: str, memory_type: str) -> float:
        """Calculate importance score for memory"""
        type_scores = {
            'question': 0.7,
            'answer': 0.8,
            'preference': 0.9,  # High importance for user preferences
            'insight': 0.85,
            'feedback': 0.75
        }
        
        base_score = type_scores.get(memory_type, 0.6)
        
        # Boost score for important keywords
        important_terms = ['error', 'critical', 'urgent', 'cost', 'risk', 'compliance', 'failure']
        boost = sum(0.1 for term in important_terms if term in content.lower())
        
        # Boost for numeric data
        if re.search(r'\d+(?:\.\d+)?[%$]?', content):
            boost += 0.1
        
        return min(base_score + boost, 1.0)
    
    def _generate_memory_id(self, user_id: str, content: str) -> str:
        """Generate unique memory ID"""
        timestamp = str(int(utc_now().timestamp()))
        content_hash = hashlib.md5(f"{user_id}{content}".encode()).hexdigest()[:8]
        return f"mem_{timestamp}_{content_hash}"
    
    async def cleanup_old_memories(self, days_to_keep: int = 30):
        """Clean up old memories to maintain performance"""
        try:
            if self.mem0_available and self.mem0:
                # Mem0 handles decay automatically
                logger.info("Mem0 handles memory decay automatically")
                return
                
            if self.memory_collection is not None:
                cutoff_date = utc_now() - timedelta(days=days_to_keep)
                
                # Remove low-importance old memories
                result = self.memory_collection.delete_many({
                    "timestamp": {"$lt": cutoff_date},
                    "importance_score": {"$lt": 0.6}
                })
                
                if result.deleted_count > 0:
                    logger.info(f"Cleaned up {result.deleted_count} old memories")
                    
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get memory system status"""
        return {
            "mem0_available": self.mem0_available,
            "mem0_initialized": self.mem0 is not None,
            "mongodb_fallback": self.memory_collection is not None,
            "system_type": "Mem0 Enhanced" if self.mem0_available else "MongoDB Fallback"
        }