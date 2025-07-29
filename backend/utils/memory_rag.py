# backend/utils/memory_rag.py
"""
Advanced Memory RAG System for Conversational AI
Enhanced with Smart Suggestions Generation
"""

import logging
import json
import re
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import pymongo
from bson import ObjectId
import hashlib

logger = logging.getLogger(__name__)

# Helper function for timezone-aware datetime (compatible with all Python versions)
def utc_now():
    """Get current UTC time - compatible with all Python versions"""
    try:
        return datetime.now(timezone.utc)
    except AttributeError:
        # Fallback for older Python versions
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return datetime.utcnow()

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


class SmartSuggestionGenerator:
    """
    Generates intelligent follow-up questions using conversation context
    FIXED for BulletproofGeminiClient compatibility
    """
    
    def __init__(self, gemini_client, memory_manager=None):
        self.gemini_client = gemini_client
        self.memory_manager = memory_manager
        
        # Default fallback suggestions
        self.default_suggestions = [
            'Show this as a different chart type',
            'What are the monthly trends?',
            'How does this compare to last year?',
            'Show me the top 10 results',
            'Break this down by region',
            'Analyze the seasonal patterns'
        ]
        
        # Database schema awareness for generating answerable questions
        self.available_collections = ['sales', 'products', 'customers', 'user_engagement']
        self.available_fields = {
            'sales': ['order_id', 'customer_id', 'product_id', 'product_name', 'category', 
                     'quantity', 'unit_price', 'total_amount', 'discount', 'date', 'month', 
                     'quarter', 'sales_rep', 'region'],
            'products': ['product_id', 'name', 'category', 'brand', 'price', 'cost', 
                        'stock', 'rating', 'reviews_count'],
            'customers': ['customer_id', 'name', 'email', 'age', 'gender', 'country', 
                         'state', 'city', 'customer_segment', 'total_spent', 'order_count']
        }
    
    async def generate_smart_suggestions(self, chat_id: str, current_result: Dict, 
                                       user_question: str) -> List[str]:
        """
        Generate context-aware follow-up suggestions
        Returns default suggestions if AI generation fails (failsafe)
        """
        try:
            # Quick background generation - don't block main response
            suggestions = await asyncio.wait_for(
                self._generate_contextual_suggestions(chat_id, current_result, user_question),
                timeout=5.0  # 5 second timeout to not delay UI
            )
            
            # Validate suggestions are answerable by our system
            validated_suggestions = self._validate_suggestions(suggestions)
            
            if len(validated_suggestions) >= 3:
                logger.info(f"✅ Generated {len(validated_suggestions)} smart suggestions")
                return validated_suggestions[:6]  # Max 6 suggestions
            else:
                logger.info("🔄 Using default suggestions (validation failed)")
                return self.default_suggestions
                
        except asyncio.TimeoutError:
            logger.info("⏱️ Suggestion generation timeout - using defaults")
            return self.default_suggestions
        except Exception as e:
            logger.error(f"❌ Suggestion generation failed: {e}")
            return self.default_suggestions
    
    async def _generate_contextual_suggestions(self, chat_id: str, current_result: Dict, 
                                             user_question: str) -> List[str]:
        """Generate suggestions using BulletproofGeminiClient with correct interface"""
        
        # Check if the client is available
        if not hasattr(self.gemini_client, 'available') or not self.gemini_client.available:
            logger.warning("⚠️ Gemini client not available for suggestions")
            return []
        
        # Build context from memory if available
        memory_context = ""
        if self.memory_manager and chat_id:
            try:
                context = await self.memory_manager.build_conversation_context(chat_id, user_question)
                memory_context = f"""
CONVERSATION CONTEXT:
- Themes: {', '.join(context.conversation_themes[:3])}
- Recent entities: {', '.join(context.recent_entities[:5])}
- User preferences: {json.dumps(context.user_preferences) if context.user_preferences else 'None'}
"""
            except Exception as e:
                logger.warning(f"Failed to build memory context: {e}")
                memory_context = ""
        
        # Extract key info from current result
        chart_type = current_result.get('chart_data', {}).get('type', 'unknown')
        summary = current_result.get('summary', '')
        insights = current_result.get('insights', [])
        data_points = len(current_result.get('chart_data', {}).get('data', {}).get('labels', []))
        
        # Create intelligent prompt
        prompt = f"""
You are an analytics assistant. Based on the user's question and current results, generate 5 smart follow-up questions that naturally extend the analysis.

USER QUESTION: "{user_question}"

CURRENT ANALYSIS:
- Chart type: {chart_type}
- Summary: {summary}
- Key insights: {'; '.join(insights[:2]) if insights else 'None'}
- Data points shown: {data_points}

{memory_context}

AVAILABLE DATA STRUCTURE:
- Sales data: order_id, customer_id, product_name, category, quantity, unit_price, total_amount, date, month, quarter, region
- Product data: name, category, brand, price, cost, stock, rating
- Customer data: customer_segment, age, gender, country, state, city, total_spent

GENERATE 5 follow-up questions that:
1. Build naturally on the current analysis
2. Can be answered with the available data fields
3. Provide deeper business insights
4. Use conversational, business-friendly language
5. Focus on actionable analysis (trends, comparisons, segments)

Examples of good follow-ups:
- "What drove the January sales spike?"
- "Which product categories performed best?"
- "How do our top customers compare by region?"
- "What's the seasonal pattern in this data?"

Return ONLY a JSON array of 5 question strings, no other text:
["question 1", "question 2", "question 3", "question 4", "question 5"]
"""

        try:
            # 🚀 FIX: Use the correct method from BulletproofGeminiClient
            # Your client uses model.generate_content() directly
            response = self.gemini_client.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'max_output_tokens': 500,
                    'top_p': 0.8
                }
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Find JSON array in response
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                suggestions_json = json_match.group()
                suggestions = json.loads(suggestions_json)
                
                if isinstance(suggestions, list) and len(suggestions) > 0:
                    return [str(s).strip() for s in suggestions if s.strip()]
            
            logger.warning("⚠️ Failed to parse Gemini suggestions response")
            return []
            
        except Exception as e:
            logger.error(f"❌ Gemini suggestion generation failed: {e}")
            return []
    
    def _validate_suggestions(self, suggestions: List[str]) -> List[str]:
        """
        Validate that suggestions can likely be answered by our system
        Filter out questions that reference unavailable data
        """
        validated = []
        
        # Keywords that indicate answerable questions
        good_keywords = [
            'sales', 'revenue', 'customers', 'products', 'category', 'region', 
            'month', 'quarter', 'trends', 'compare', 'top', 'bottom', 'best', 
            'worst', 'segment', 'price', 'cost', 'rating', 'brand', 'age',
            'country', 'state', 'city', 'total', 'average', 'highest', 'lowest'
        ]
        
        # Keywords that indicate potentially problematic questions
        bad_keywords = [
            'external', 'api', 'real-time', 'live', 'current', 'today',
            'competitor', 'market share', 'social media', 'weather',
            'stock price', 'exchange rate', 'gdp', 'inflation'
        ]
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            # Check for bad keywords
            has_bad_keywords = any(bad_word in suggestion_lower for bad_word in bad_keywords)
            if has_bad_keywords:
                continue
            
            # Check for good keywords or general analytical patterns
            has_good_keywords = any(good_word in suggestion_lower for good_word in good_keywords)
            has_analytical_pattern = any(pattern in suggestion_lower for pattern in [
                'what', 'which', 'how', 'show', 'compare', 'analyze', 'breakdown'
            ])
            
            if has_good_keywords or has_analytical_pattern:
                validated.append(suggestion)
        
        return validated

    def get_default_suggestions(self) -> List[str]:
        """Get the default fallback suggestions"""
        return self.default_suggestions.copy()

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
            
            logger.info("✅ Memory collection indexes ensured")
            
        except Exception as e:
            logger.error(f"Failed to create memory indexes: {e}")
    
    def extract_keywords_and_entities(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract keywords and entities from text using simple NLP"""
        keywords = []
        entities = []
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'but', 'for', 'are', 'with', 'this', 'that', 'from', 'they', 'have', 'been', 'was', 'were', 'said', 'each', 'which', 'their', 'time', 'will', 'about', 'can', 'would', 'there', 'what', 'some', 'had', 'them', 'these', 'may', 'like', 'use', 'into', 'than', 'more', 'very', 'when', 'much', 'how', 'where', 'why', 'who'}
        keywords = [word for word in words if word not in stop_words][:10]
        
        # Extract dates, numbers, and monetary values
        entities.extend(re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', text))  # Dates
        entities.extend(re.findall(r'\$\d+\.?\d*', text))  # Money
        entities.extend(re.findall(r'\b\d+\.?\d*', text))
        
        # Capitalized words (potential names/places)
        entities.extend(re.findall(r'\b[A-Z][a-z]+\b', text))
        
        # Common business terms
        business_entities = re.findall(r'\b(revenue|sales|profit|customers?|products?|orders?|analytics?|dashboard|report|chart|graph)\b', text.lower())
        entities.extend(business_entities)
        
        return keywords[:10], list(set(entities))[:15]
    
    def calculate_enhanced_importance(self, content: str, content_type: str, context: Dict = None) -> float:
        """Enhanced importance scoring with multiple factors"""
        if context is None:
            context = {}
            
        # Base scores (keep your existing logic)
        base_scores = {
            'question': 0.7,
            'answer': 0.8,
            'preference': 0.9,
            'fact': 0.6,
            'context': 0.4
        }
        
        importance = base_scores.get(content_type, 0.5)
        
        # ENHANCEMENT: Pattern-based importance boosts
        try:
            content_lower = content.lower()
            
            # User preferences and needs (HIGH PRIORITY)
            if re.search(r'\b(prefer|like|want|need|always|never)\b', content_lower):
                importance += 0.2
            
            # Business metrics and KPIs
            if re.search(r'\b(revenue|profit|sales|growth|performance|trend|compare|versus)\b', content_lower):
                importance += 0.15
            
            # Temporal references (recent context)
            if re.search(r'\b(yesterday|today|this week|last month|recent|latest)\b', content_lower):
                importance += 0.1
            
            # Specific numbers and dates (concrete data)
            if re.search(r'\b(\d{4}|\$\d+|\d+%|\d+\.?\d*[KMB]?)\b', content_lower):
                importance += 0.05
                
        except Exception as e:
            # If pattern matching fails, use base score (SAFE)
            logger.warning(f"Pattern matching failed for importance scoring: {e}")
        
        # ENHANCEMENT: Recency factor
        try:
            if context.get('timestamp'):
                hours_old = (utc_now() - context['timestamp']).total_seconds() / 3600
                recency_factor = max(0, 1 - (hours_old / 168))  # Decay over a week
                importance *= (0.7 + 0.3 * recency_factor)
        except:
            # If recency calculation fails, skip it (SAFE)
            pass
        
        # ENHANCEMENT: Recent conversation turns bonus
        try:
            if context.get('turn') and context['turn'] <= 5:
                importance += 0.1  # Recent conversation turns are more important
        except:
            # If turn calculation fails, skip it (SAFE)
            pass
        
        # Cap at 1.0 and ensure minimum of 0.1
        return max(0.1, min(1.0, importance))
    
    async def store_memory(self, chat_id: str, content: str, content_type: str, 
                          related_to: List[str] = None, context: Dict = None) -> str:
        """Store a new memory fragment with enhanced importance scoring"""
        try:
            if context is None:
                context = {}
                
            # Extract keywords and entities
            keywords, entities = self.extract_keywords_and_entities(content)
            
            # Calculate enhanced importance score
            importance_score = self.calculate_enhanced_importance(content, content_type, context)
            
            # Generate unique fragment ID
            fragment_id = f"mem_{chat_id}_{utc_now().timestamp()}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
            
            memory_doc = {
                "fragment_id": fragment_id,
                "chat_id": chat_id,
                "content": content,
                "content_type": content_type,
                "timestamp": utc_now(),
                "importance_score": importance_score,
                "keywords": keywords,
                "entities": entities,
                "related_fragments": related_to or [],
                "access_count": 0,
                "context": context
            }
            
            # Store in database
            self.memory_collection.insert_one(memory_doc)
            
            logger.info(f"✅ Stored memory fragment: {fragment_id} (importance: {importance_score:.2f})")
            
            # Cleanup old memories if needed
            await self.cleanup_old_memories(chat_id)
            
            return fragment_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return None
    
    async def retrieve_relevant_memories(self, chat_id: str, query: str, limit: int = 6) -> List[MemoryFragment]:
        """Retrieve relevant memories for a given query"""
        try:
            # Build aggregation pipeline for smart memory retrieval
            pipeline = [
                # Match memories for this chat
                {"$match": {"chat_id": chat_id}},
                
                # Add relevance score based on text similarity and importance
                {
                    "$addFields": {
                        "relevance_score": {
                            "$add": [
                                "$importance_score",
                                {
                                    "$cond": {
                                        "if": {"$regexMatch": {"input": "$content", "regex": query, "options": "i"}},
                                        "then": 0.3,
                                        "else": 0
                                    }
                                }
                            ]
                        }
                    }
                },
                
                # Sort by relevance score and recency
                {"$sort": {"relevance_score": -1, "timestamp": -1}},
                
                # Limit results
                {"$limit": limit}
            ]
            
            results = list(self.memory_collection.aggregate(pipeline))
            
            # Convert to MemoryFragment objects
            memories = []
            for doc in results:
                # Update access statistics
                self.memory_collection.update_one(
                    {"fragment_id": doc["fragment_id"]},
                    {
                        "$inc": {"access_count": 1},
                        "$set": {"last_accessed": utc_now()}
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
        """Enhanced memory context formatter with better token management and timezone safety"""
        try:
            formatted_parts = []
            token_estimate = 0
            
            # Header (always include)
            header = f"=== CONVERSATION CONTEXT (Turn {context.current_turn}) ==="
            formatted_parts.append(header)
            token_estimate += len(header) // 4  # Rough token estimation
            
            # Add user preferences (high priority)
            if context.user_preferences:
                formatted_parts.append("\n👤 USER PREFERENCES:")
                for pref_type, pref_value in list(context.user_preferences.items())[:3]:  # Limit to 3
                    pref_line = f"   - {pref_type}: {pref_value}"
                    if token_estimate + len(pref_line) // 4 < max_tokens * 0.2:
                        formatted_parts.append(pref_line)
                        token_estimate += len(pref_line) // 4
            
            # Add conversation themes
            if context.conversation_themes:
                themes_line = f"\n🎯 CONVERSATION THEMES: {', '.join(context.conversation_themes[:5])}"
                if token_estimate + len(themes_line) // 4 < max_tokens * 0.15:
                    formatted_parts.append(themes_line)
                    token_estimate += len(themes_line) // 4
            
            # Add recent entities
            if context.recent_entities:
                entities_line = f"\n🏷️ RECENT ENTITIES: {', '.join(context.recent_entities[:6])}"
                if token_estimate + len(entities_line) // 4 < max_tokens * 0.15:
                    formatted_parts.append(entities_line)
                    token_estimate += len(entities_line) // 4
            
            # Add relevant memories (prioritized)
            if context.relevant_memories:
                formatted_parts.append("\n📚 RELEVANT MEMORY:")
                
                # Sort by recency AND importance (SAFE - won't break existing logic)
                try:
                    sorted_memories = sorted(
                        context.relevant_memories,
                        key=lambda m: (
                            getattr(m.timestamp, 'timestamp', lambda: 0)() if hasattr(m.timestamp, 'timestamp') else 0, 
                            getattr(m, 'importance_score', 0.5)
                        ),
                        reverse=True
                    )
                except Exception as sort_error:
                    # Fallback to original order if sorting fails
                    logger.warning(f"Memory sorting failed, using original order: {sort_error}")
                    sorted_memories = context.relevant_memories
                
                for memory in sorted_memories[:4]:  # Limit to top 4
                    try:
                        # TIMEZONE-SAFE age calculation
                        current_time = utc_now()
                        memory_time = memory.timestamp
                        
                        # Handle timezone mismatch (old vs new memories)
                        if memory_time.tzinfo is None:
                            # Old memory without timezone - make it UTC aware
                            memory_time = memory_time.replace(tzinfo=timezone.utc)
                        elif current_time.tzinfo is None:
                            # Current time without timezone - make it UTC aware  
                            current_time = current_time.replace(tzinfo=timezone.utc)
                        
                        # Calculate age safely
                        try:
                            age = current_time - memory_time
                            age_str = f"{age.days}d ago" if age.days > 0 else f"{age.seconds//3600}h ago"
                        except Exception as age_error:
                            # Ultimate fallback if age calculation still fails
                            logger.warning(f"Age calculation failed, using fallback: {age_error}")
                            age_str = "recent"
                        
                        # Smart truncation based on available space
                        max_content_len = 150 if token_estimate < max_tokens * 0.6 else 100
                        content = memory.content[:max_content_len] + "..." if len(memory.content) > max_content_len else memory.content
                        memory_line = f"   [{memory.content_type.upper()}, {age_str}] {content}"
                        
                        # Check token limit before adding
                        if token_estimate + len(memory_line) // 4 > max_tokens * 0.8:
                            break
                            
                        formatted_parts.append(memory_line)
                        token_estimate += len(memory_line) // 4
                        
                    except Exception as memory_error:
                        # Skip problematic memory, don't break the whole process
                        logger.warning(f"Skipping memory due to error: {memory_error}")
                        continue
            
            formatted_parts.append("\n=== END CONTEXT ===\n")
            
            return '\n'.join(formatted_parts)
            
        except Exception as e:
            logger.error(f"Failed to format memory context: {e}")
            # SAFE FALLBACK - return basic context if enhancement fails
            return f"=== CONVERSATION CONTEXT (Turn {context.current_turn}) ===\n[Context loading error: {str(e)}]\n=== END CONTEXT ===\n"
    
    async def cleanup_old_memories(self, chat_id: str):
        """Clean up old or low-importance memories"""
        try:
            # Count current memories
            memory_count = self.memory_collection.count_documents({"chat_id": chat_id})
            
            if memory_count > self.max_memory_fragments:
                # Remove oldest, least important memories
                old_memories = list(self.memory_collection.find(
                    {"chat_id": chat_id}
                ).sort([("importance_score", 1), ("timestamp", 1)]).limit(memory_count - self.max_memory_fragments))
                
                memory_ids = [mem["fragment_id"] for mem in old_memories]
                
                result = self.memory_collection.delete_many(
                    {"fragment_id": {"$in": memory_ids}}
                )
                
                logger.info(f"✅ Cleaned up {result.deleted_count} old memories for chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup memories: {e}")
    
    def get_memory_stats(self, chat_id: str) -> Dict[str, Any]:
        """Get statistics about stored memories for a chat"""
        try:
            # Aggregate memory statistics
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
    NOW WITH SMART SUGGESTIONS!
    """
    
    def __init__(self, base_processor, memory_manager: MemoryRAGManager, gemini_client=None):
        self.base_processor = base_processor
        self.memory_manager = memory_manager
        
        # Initialize smart suggestion generator if Gemini is available
        self.suggestion_generator = None
        if gemini_client:
            self.suggestion_generator = SmartSuggestionGenerator(gemini_client, memory_manager)
            logger.info("✅ Smart Suggestion Generator initialized")
    
    async def process_with_memory(self, question: str, chat_id: str) -> Dict[str, Any]:
        """Process question with full memory context AND smart suggestions"""
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
            
            # Process with base processor (YOUR EXISTING FLOW - UNCHANGED)
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
            
            # 🚀 NEW: Generate smart suggestions in background (non-blocking)
            if self.suggestion_generator and result.get('success'):
                try:
                    # Start suggestion generation task but don't wait for it
                    suggestion_task = asyncio.create_task(
                        self.suggestion_generator.generate_smart_suggestions(
                            chat_id, result, question
                        )
                    )
                    
                    # Try to get suggestions quickly, but don't block
                    try:
                        smart_suggestions = await asyncio.wait_for(suggestion_task, timeout=2.0)
                        result['suggested_questions'] = smart_suggestions
                        logger.info(f"✅ Smart suggestions generated: {len(smart_suggestions)}")
                    except asyncio.TimeoutError:
                        # Return default suggestions immediately, let background task continue
                        result['suggested_questions'] = self.suggestion_generator.get_default_suggestions()
                        logger.info("⏱️ Using default suggestions (background generation continuing)")
                        
                        # Schedule background completion (optional)
                        asyncio.create_task(self._complete_suggestion_background(suggestion_task, chat_id))
                        
                except Exception as e:
                    logger.error(f"❌ Suggestion generation error: {e}")
                    result['suggested_questions'] = self.suggestion_generator.get_default_suggestions()
            else:
                # Fallback to default suggestions if no generator available
                default_suggestions = [
                    'Show this as a different chart type',
                    'What are the monthly trends?',
                    'How does this compare to last year?',
                    'Show me the top 10 results',
                    'Break this down by region',
                    'Analyze the seasonal patterns'
                ]
                result['suggested_questions'] = default_suggestions
            
            return result
            
        except Exception as e:
            logger.error(f"Memory-enhanced processing failed: {e}")
            # Fallback to base processor
            result = await self.base_processor.process_question(question)
            
            # Add default suggestions even in fallback
            result['suggested_questions'] = [
                'Show this as a different chart type',
                'What are the monthly trends?',
                'How does this compare to last year?'
            ]
            
            return result
    
    async def _complete_suggestion_background(self, suggestion_task, chat_id):
        """Complete suggestion generation in background and optionally store"""
        try:
            smart_suggestions = await suggestion_task
            logger.info(f"🔥 Background suggestion generation completed for chat {chat_id}")
            # Could store these for future use or send via websocket if implemented
        except Exception as e:
            logger.error(f"Background suggestion completion failed: {e}")
    
    async def _extract_and_store_insights(self, chat_id: str, question: str, result: Dict):
        """Extract and store insights as memories"""
        try:
            # Store user preferences mentioned in questions
            preference_patterns = [
                r"i (prefer|like|want|need) (.+?)(?:\.|$)",
                r"(always|never) (.+?)(?:\.|$)",
                r"my favorite (.+?) is (.+?)(?:\.|$)"
            ]
            
            question_lower = question.lower()
            for pattern in preference_patterns:
                matches = re.findall(pattern, question_lower)
                for match in matches:
                    preference_content = f"User {match[0]}s {match[1]}"
                    await self.memory_manager.store_memory(
                        chat_id=chat_id,
                        content=preference_content,
                        content_type='preference'
                    )
            
            # Store important facts from results
            if result.get('insights'):
                for insight in result['insights']:
                    if len(insight.strip()) > 20:  # Only meaningful insights
                        await self.memory_manager.store_memory(
                            chat_id=chat_id,
                            content=f"Fact: {insight}",
                            content_type='fact'
                        )
                    
        except Exception as e:
            logger.error(f"Failed to extract insights: {e}")