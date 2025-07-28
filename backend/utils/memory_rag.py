# backend/utils/memory_rag.py
"""
Advanced Memory RAG System for Conversational AI
Implements ChatGPT-like memory within chat sessions
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pymongo
from bson import ObjectId
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class MemoryFragment:
    """Individual memory fragment with metadata"""
    fragment_id: str
    chat_id: str
    content: str
    content_type: str  # 'question', 'answer', 'context', 'preference', 'fact'
    timestamp: datetime
    importance_score: float
    keywords: List[str]
    entities: List[str]
    related_fragments: List[str]
    access_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class ConversationContext:
    """Rich conversation context for memory-aware responses"""
    chat_id: str
    current_turn: int
    relevant_memories: List[MemoryFragment]
    user_preferences: Dict[str, Any]
    conversation_themes: List[str]
    recent_entities: List[str]
    session_context: Dict[str, Any]

class MemoryRAGManager:
    """
    Advanced Memory RAG system for chat-based conversational AI
    Implements sophisticated memory management similar to ChatGPT
    """
    
    def __init__(self, database, gemini_client=None):
        self.db = database
        self.gemini_client = gemini_client
        self.memory_collection = self.db.chat_memories
        self.ensure_memory_indexes()
        
        # Memory configuration
        self.max_memory_fragments = 1000  # Per chat session
        self.memory_decay_days = 30
        self.relevance_threshold = 0.3
        self.max_context_tokens = 4000
        
    def ensure_memory_indexes(self):
        """Create optimized indexes for memory retrieval"""
        try:
            # Core indexes for fast retrieval
            self.memory_collection.create_index("chat_id")
            self.memory_collection.create_index("fragment_id", unique=True)
            self.memory_collection.create_index([("chat_id", 1), ("timestamp", -1)])
            self.memory_collection.create_index([("chat_id", 1), ("importance_score", -1)])
            
            # Text search indexes
            self.memory_collection.create_index([("content", "text"), ("keywords", "text")])
            self.memory_collection.create_index([("chat_id", 1), ("content_type", 1)])
            self.memory_collection.create_index([("chat_id", 1), ("entities", 1)])
            
            logger.info("✅ Memory RAG indexes created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create memory indexes: {e}")
            return False
    
    def generate_fragment_id(self, chat_id: str, content: str) -> str:
        """Generate unique fragment ID"""
        timestamp = str(datetime.utcnow().timestamp())
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"mem_{chat_id}_{timestamp}_{content_hash}"
    
    def extract_keywords_and_entities(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract keywords and entities from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = list(set([w for w in words if len(w) > 3]))[:10]
        
        # Simple entity extraction (numbers, capitalized words, common patterns)
        entities = []
        
        # Numbers and monetary values
        entities.extend(re.findall(r'\$?[\d,]+\.?\d*', text))
        
        # Capitalized words (potential names/places)
        entities.extend(re.findall(r'\b[A-Z][a-z]+\b', text))
        
        # Common business terms
        business_entities = re.findall(r'\b(revenue|sales|profit|customers?|products?|orders?|analytics?|dashboard|report|chart|graph)\b', text.lower())
        entities.extend(business_entities)
        
        return keywords[:10], list(set(entities))[:15]
    
    def calculate_importance_score(self, content: str, content_type: str, context: Dict = None) -> float:
        """Calculate importance score for memory fragment"""
        base_score = 0.5
        
        # Content type weights
        type_weights = {
            'preference': 0.9,    # User preferences are very important
            'fact': 0.8,          # Important facts
            'question': 0.6,      # User questions
            'answer': 0.7,        # AI responses
            'context': 0.4        # Background context
        }
        
        score = type_weights.get(content_type, 0.5)
        
        # Length bonus (longer content often more important)
        if len(content) > 100:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        
        # Keyword importance boost
        important_keywords = ['prefer', 'like', 'want', 'need', 'always', 'never', 'important', 'remember']
        for keyword in important_keywords:
            if keyword in content.lower():
                score += 0.15
        
        # Numbers and data boost
        if re.search(r'\d+', content):
            score += 0.1
        
        return min(1.0, score)
    
    async def store_memory(self, chat_id: str, content: str, content_type: str, 
                          related_to: List[str] = None, context: Dict = None) -> str:
        """Store a new memory fragment"""
        try:
            # Extract keywords and entities
            keywords, entities = self.extract_keywords_and_entities(content)
            
            # Calculate importance
            importance = self.calculate_importance_score(content, content_type, context)
            
            # Create memory fragment
            fragment = MemoryFragment(
                fragment_id=self.generate_fragment_id(chat_id, content),
                chat_id=chat_id,
                content=content,
                content_type=content_type,
                timestamp=datetime.utcnow(),
                importance_score=importance,
                keywords=keywords,
                entities=entities,
                related_fragments=related_to or []
            )
            
            # Store in MongoDB
            result = self.memory_collection.insert_one(asdict(fragment))
            
            if result.inserted_id:
                logger.info(f"✅ Stored memory fragment: {fragment.fragment_id}")
                
                # Cleanup old memories if needed
                await self.cleanup_old_memories(chat_id)
                
                return fragment.fragment_id
            else:
                logger.error("Failed to store memory fragment")
                return None
                
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return None
    
    async def retrieve_relevant_memories(self, chat_id: str, current_input: str, 
                                       limit: int = 10) -> List[MemoryFragment]:
        """Retrieve memories relevant to current input"""
        try:
            # Extract keywords from current input
            keywords, entities = self.extract_keywords_and_entities(current_input)
            
            # Build MongoDB aggregation pipeline for relevance scoring
            pipeline = [
                {"$match": {"chat_id": chat_id}},
                {
                    "$addFields": {
                        "relevance_score": {
                            "$add": [
                                # Base importance score
                                "$importance_score",
                                
                                # Keyword overlap bonus
                                {
                                    "$multiply": [
                                        0.3,
                                        {"$size": {"$setIntersection": ["$keywords", keywords]}}
                                    ]
                                },
                                
                                # Entity overlap bonus
                                {
                                    "$multiply": [
                                        0.4,
                                        {"$size": {"$setIntersection": ["$entities", entities]}}
                                    ]
                                },
                                
                                # Recent access bonus
                                {
                                    "$cond": [
                                        {"$gt": ["$access_count", 0]},
                                        {"$multiply": [0.1, {"$ln": {"$add": [1, "$access_count"]}}]},
                                        0
                                    ]
                                },
                                
                                # Recency bonus (more recent = higher score)
                                {
                                    "$multiply": [
                                        0.2,
                                        {
                                            "$divide": [
                                                {"$subtract": [datetime.utcnow(), "$timestamp"]},
                                                86400000  # milliseconds in a day
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                {"$match": {"relevance_score": {"$gte": self.relevance_threshold}}},
                {"$sort": {"relevance_score": -1}},
                {"$limit": limit}
            ]
            
            # Execute aggregation
            results = list(self.memory_collection.aggregate(pipeline))
            
            # Convert to MemoryFragment objects
            memories = []
            for doc in results:
                # Update access statistics
                self.memory_collection.update_one(
                    {"fragment_id": doc["fragment_id"]},
                    {
                        "$inc": {"access_count": 1},
                        "$set": {"last_accessed": datetime.utcnow()}
                    }
                )
                
                # Create MemoryFragment object
                memories.append(MemoryFragment(
                    fragment_id=doc["fragment_id"],
                    chat_id=doc["chat_id"],
                    content=doc["content"],
                    content_type=doc["content_type"],
                    timestamp=doc["timestamp"],
                    importance_score=doc["importance_score"],
                    keywords=doc["keywords"],
                    entities=doc["entities"],
                    related_fragments=doc["related_fragments"],
                    access_count=doc.get("access_count", 0),
                    last_accessed=doc.get("last_accessed")
                ))
            
            logger.info(f"✅ Retrieved {len(memories)} relevant memories for chat {chat_id}")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def build_conversation_context(self, chat_id: str, current_input: str) -> ConversationContext:
        """Build rich conversation context with memory"""
        try:
            # Get relevant memories
            relevant_memories = await self.retrieve_relevant_memories(chat_id, current_input)
            
            # Extract user preferences
            preferences = {}
            for memory in relevant_memories:
                if memory.content_type == 'preference':
                    # Parse preference from content
                    pref_match = re.search(r'(prefer|like|want|need)\s+([^.]+)', memory.content.lower())
                    if pref_match:
                        preferences[pref_match.group(1)] = pref_match.group(2)
            
            # Identify conversation themes
            all_keywords = []
            for memory in relevant_memories:
                all_keywords.extend(memory.keywords)
            
            # Count keyword frequency to identify themes
            keyword_counts = {}
            for keyword in all_keywords:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            themes = [k for k, v in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            # Get recent entities
            recent_entities = []
            for memory in relevant_memories[:5]:  # Most recent/relevant
                recent_entities.extend(memory.entities)
            recent_entities = list(set(recent_entities))[:10]
            
            # Get current conversation turn count
            turn_count = self.memory_collection.count_documents({
                "chat_id": chat_id,
                "content_type": {"$in": ["question", "answer"]}
            })
            
            return ConversationContext(
                chat_id=chat_id,
                current_turn=turn_count + 1,
                relevant_memories=relevant_memories,
                user_preferences=preferences,
                conversation_themes=themes,
                recent_entities=recent_entities,
                session_context={}
            )
            
        except Exception as e:
            logger.error(f"Failed to build conversation context: {e}")
            return ConversationContext(
                chat_id=chat_id,
                current_turn=1,
                relevant_memories=[],
                user_preferences={},
                conversation_themes=[],
                recent_entities=[],
                session_context={}
            )
    
    def format_memory_context_for_ai(self, context: ConversationContext, max_tokens: int = 4000) -> str:
        """Format memory context for AI prompt"""
        try:
            formatted_context = []
            
            # Add conversation metadata
            formatted_context.append(f"=== CONVERSATION CONTEXT (Turn {context.current_turn}) ===")
            
            # Add user preferences
            if context.user_preferences:
                formatted_context.append("\n👤 USER PREFERENCES:")
                for pref_type, pref_value in context.user_preferences.items():
                    formatted_context.append(f"   - {pref_type}: {pref_value}")
            
            # Add conversation themes
            if context.conversation_themes:
                formatted_context.append(f"\n🎯 CONVERSATION THEMES: {', '.join(context.conversation_themes)}")
            
            # Add recent entities
            if context.recent_entities:
                formatted_context.append(f"\n🏷️ RECENT ENTITIES: {', '.join(context.recent_entities[:8])}")
            
            # Add relevant memories
            if context.relevant_memories:
                formatted_context.append("\n📚 RELEVANT MEMORY:")
                
                for i, memory in enumerate(context.relevant_memories[:6]):
                    age = datetime.utcnow() - memory.timestamp
                    age_str = f"{age.days}d ago" if age.days > 0 else f"{age.seconds//3600}h ago"
                    
                    formatted_context.append(f"   [{memory.content_type.upper()}, {age_str}] {memory.content[:200]}...")
                    
                    if len('\n'.join(formatted_context)) > max_tokens:
                        break
            
            formatted_context.append("\n=== END CONTEXT ===\n")
            
            return '\n'.join(formatted_context)
            
        except Exception as e:
            logger.error(f"Failed to format memory context: {e}")
            return "=== CONVERSATION CONTEXT ===\n[Error loading context]\n=== END CONTEXT ===\n"
    
    async def cleanup_old_memories(self, chat_id: str):
        """Clean up old or low-importance memories"""
        try:
            # Count current memories
            memory_count = self.memory_collection.count_documents({"chat_id": chat_id})
            
            if memory_count > self.max_memory_fragments:
                # Remove oldest, least important memories
                memories_to_remove = memory_count - self.max_memory_fragments
                
                pipeline = [
                    {"$match": {"chat_id": chat_id}},
                    {"$sort": {"importance_score": 1, "timestamp": 1}},
                    {"$limit": memories_to_remove}
                ]
                
                old_memories = list(self.memory_collection.aggregate(pipeline))
                fragment_ids = [mem["fragment_id"] for mem in old_memories]
                
                result = self.memory_collection.delete_many({
                    "fragment_id": {"$in": fragment_ids}
                })
                
                logger.info(f"🧹 Cleaned up {result.deleted_count} old memories for chat {chat_id}")
            
            # Remove very old memories
            cutoff_date = datetime.utcnow() - timedelta(days=self.memory_decay_days)
            old_result = self.memory_collection.delete_many({
                "chat_id": chat_id,
                "timestamp": {"$lt": cutoff_date},
                "importance_score": {"$lt": 0.7}  # Keep important memories longer
            })
            
            if old_result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {old_result.deleted_count} expired memories for chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup memories: {e}")
    
    async def get_chat_memory_stats(self, chat_id: str) -> Dict:
        """Get memory statistics for a chat"""
        try:
            pipeline = [
                {"$match": {"chat_id": chat_id}},
                {
                    "$group": {
                        "_id": "$content_type",
                        "count": {"$sum": 1},
                        "avg_importance": {"$avg": "$importance_score"},
                        "total_access": {"$sum": "$access_count"}
                    }
                }
            ]
            
            stats_by_type = list(self.memory_collection.aggregate(pipeline))
            
            total_memories = self.memory_collection.count_documents({"chat_id": chat_id})
            
            # Get most accessed memories
            top_memories = list(self.memory_collection.find(
                {"chat_id": chat_id},
                {"content": 1, "access_count": 1, "importance_score": 1}
            ).sort("access_count", -1).limit(5))
            
            return {
                "total_memories": total_memories,
                "stats_by_type": {stat["_id"]: stat for stat in stats_by_type},
                "top_accessed_memories": top_memories,
                "memory_health": "good" if total_memories < self.max_memory_fragments else "needs_cleanup"
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}


class MemoryEnhancedProcessor:
    """
    Enhanced processor that integrates Memory RAG with existing analytics
    """
    
    def __init__(self, base_processor, memory_manager: MemoryRAGManager):
        self.base_processor = base_processor
        self.memory_manager = memory_manager
    
    async def process_with_memory(self, question: str, chat_id: str) -> Dict[str, Any]:
        """Process question with full memory context"""
        try:
            # Build conversation context
            context = await self.memory_manager.build_conversation_context(chat_id, question)
            
            # Store the user question as memory
            await self.memory_manager.store_memory(
                chat_id=chat_id,
                content=question,
                content_type='question',
                context={'turn': context.current_turn}
            )
            
            # Format memory context for AI
            memory_context = self.memory_manager.format_memory_context_for_ai(context)
            
            # Enhanced question with memory context
            enhanced_question = f"{memory_context}\nUSER QUESTION: {question}"
            
            # Process with base processor
            result = await self.base_processor.process_question(enhanced_question)
            
            # Store the AI response as memory
            if result.get('success'):
                response_content = f"Answer: {result.get('summary', '')}"
                if result.get('insights'):
                    response_content += f" Insights: {'; '.join(result['insights'])}"
                
                await self.memory_manager.store_memory(
                    chat_id=chat_id,
                    content=response_content,
                    content_type='answer',
                    context={'turn': context.current_turn}
                )
                
                # Store any discovered facts or preferences
                await self._extract_and_store_insights(chat_id, question, result)
            
            # Add memory context to result
            result['memory_context'] = {
                'memories_used': len(context.relevant_memories),
                'conversation_turn': context.current_turn,
                'themes': context.conversation_themes,
                'preferences': context.user_preferences
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Memory-enhanced processing failed: {e}")
            # Fallback to base processor
            return await self.base_processor.process_question(question)
    
    async def _extract_and_store_insights(self, chat_id: str, question: str, result: Dict):
        """Extract and store insights as memories"""
        try:
            # Store user preferences mentioned in questions
            preference_patterns = [
                r"i (prefer|like|want|need) (.+?)(?:\.|$)",
                r"(always|never) (.+?)(?:\.|$)",
                r"my favorite (.+?) is (.+?)(?:\.|$)"
            ]
            
            for pattern in preference_patterns:
                matches = re.finditer(pattern, question.lower())
                for match in matches:
                    preference_text = f"User {match.group(1)} {match.group(2)}"
                    await self.memory_manager.store_memory(
                        chat_id=chat_id,
                        content=preference_text,
                        content_type='preference'
                    )
            
            # Store important facts from results
            if result.get('insights'):
                for insight in result['insights']:
                    if any(keyword in insight.lower() for keyword in ['increase', 'decrease', 'highest', 'lowest', 'trend']):
                        await self.memory_manager.store_memory(
                            chat_id=chat_id,
                            content=f"Fact: {insight}",
                            content_type='fact'
                        )
                        
        except Exception as e:
            logger.error(f"Failed to extract insights: {e}")