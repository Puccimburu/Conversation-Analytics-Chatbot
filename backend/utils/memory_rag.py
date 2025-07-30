# backend/utils/memory_rag.py
"""
Advanced Memory RAG System for Conversational AI
Enhanced with Smart Suggestions Generation for GenAI Operations
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
from config.config import DATABASE_SCHEMA  # Import GenAI schema

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
    Enhanced for GenAI operations and document intelligence
    """
    
    def __init__(self, gemini_client, memory_manager=None):
        self.gemini_client = gemini_client
        self.memory_manager = memory_manager
        
        # GenAI-specific default suggestions
        self.default_suggestions = [
            'What are our AI operational costs this month?',
            'Show me document extraction confidence trends',
            'Which compliance obligations need attention?',
            'How are our AI agents performing?',
            'Compare processing efficiency across document types'
        ]
        
        # Enhanced domain context for GenAI operations
        self.domain_context = {
            "domain": "AI Operations & Document Intelligence",
            "primary_metrics": [
                "AI costs and spending", "document processing efficiency", 
                "extraction confidence scores", "compliance obligation tracking",
                "agent performance metrics", "batch processing success rates"
            ],
            "key_collections": list(DATABASE_SCHEMA["collections"].keys()),
            "analysis_types": [
                "cost_optimization", "quality_assurance", "compliance_management",
                "operational_efficiency", "user_productivity"
            ]
        }
    
    async def generate_smart_suggestions(self, question: str, result: Dict, 
                                       conversation_context: Optional[Dict] = None) -> List[str]:
        """
        Generate intelligent follow-up suggestions based on GenAI operations context
        """
        try:
            if not self.gemini_client:
                return self.get_default_suggestions()
            
            # Build comprehensive context for suggestion generation
            suggestion_context = {
                "original_question": question,
                "result_summary": self._extract_result_summary(result),
                "domain_context": self.domain_context,
                "conversation_history": conversation_context or {},
                "available_data": self._get_available_data_context()
            }
            
            # Generate suggestions using Gemini
            suggestions_prompt = self._build_suggestions_prompt(suggestion_context)
            
            try:
                # Use Gemini to generate contextual suggestions
                response = await self.gemini_client.generate_content_async(suggestions_prompt)
                
                if response and hasattr(response, 'text'):
                    suggestions = self._parse_suggestions_response(response.text)
                    validated_suggestions = self._validate_suggestions(suggestions)
                    
                    if validated_suggestions:
                        logger.info(f"✅ Generated {len(validated_suggestions)} smart suggestions")
                        return validated_suggestions[:5]  # Return top 5
                
            except Exception as e:
                logger.warning(f"Gemini suggestion generation failed: {e}")
            
            # Fallback to context-aware default suggestions
            return self._generate_contextual_fallback_suggestions(question, result)
            
        except Exception as e:
            logger.error(f"Smart suggestion generation error: {e}")
            return self.get_default_suggestions()
    
    def _extract_result_summary(self, result: Dict) -> str:
        """Extract key information from the analysis result"""
        summary_parts = []
        
        if result.get('success'):
            if result.get('query_data', {}).get('collection'):
                collection = result['query_data']['collection']
                summary_parts.append(f"Analyzed {collection} collection")
            
            if result.get('raw_results'):
                count = len(result['raw_results'])
                summary_parts.append(f"Found {count} records")
            
            if result.get('visualization', {}).get('chart_type'):
                chart_type = result['visualization']['chart_type']
                summary_parts.append(f"Displayed as {chart_type} chart")
            
            if result.get('insights'):
                insight_count = len(result['insights'])
                summary_parts.append(f"Generated {insight_count} insights")
        
        return "; ".join(summary_parts) if summary_parts else "Analysis completed"
    
    def _get_available_data_context(self) -> Dict:
        """Get context about available data for better suggestions"""
        return {
            "collections": list(DATABASE_SCHEMA["collections"].keys()),
            "ai_operations": [
                "costevalutionforllm", "llmpricing", "agent_activity"
            ],
            "document_processing": [
                "documentextractions", "obligationextractions", "batches", "files"
            ],
            "user_management": [
                "users", "allowedusers", "conversations"
            ],
            "compliance": [
                "obligationextractions", "obligationmappings", "compliances"
            ]
        }
    
    def _build_suggestions_prompt(self, context: Dict) -> str:
        """Build a comprehensive prompt for generating smart suggestions"""
        return f"""
You are an AI Operations Analytics expert generating intelligent follow-up questions.

CONTEXT:
- Domain: {context['domain_context']['domain']}
- Original Question: "{context['original_question']}"
- Analysis Result: {context['result_summary']}
- Available Collections: {', '.join(context['available_data']['collections'][:10])}

TASK: Generate 5 intelligent follow-up questions that would provide valuable insights for AI operations management.

FOCUS AREAS:
1. Cost optimization and efficiency
2. Document processing quality
3. Compliance and risk management
4. Operational performance
5. User productivity and system health

REQUIREMENTS:
- Questions should be specific and actionable
- Focus on operational insights and optimization
- Consider both immediate and strategic value
- Use natural, conversational language
- Avoid generic or vague questions

EXAMPLES OF GOOD FOLLOW-UPS:
- "Which AI models are driving our highest costs?"
- "Show me documents with confidence scores below 90%"
- "What's causing our batch processing delays?"
- "Which compliance obligations have the highest risk?"

Generate 5 smart follow-up questions (one per line, no numbering):
"""
    
    def _parse_suggestions_response(self, response_text: str) -> List[str]:
        """Parse suggestions from Gemini response"""
        lines = response_text.strip().split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            # Remove numbering, bullets, and clean up
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            line = re.sub(r'^[-•*]\s*', '', line)
            line = line.strip('"\'')
            
            if line and len(line) > 10 and '?' in line:
                suggestions.append(line)
        
        return suggestions[:8]  # Return up to 8 for validation
    
    def _validate_suggestions(self, suggestions: List[str]) -> List[str]:
        """Validate and filter suggestions for GenAI operations relevance"""
        if not suggestions:
            return []
        
        validated = []
        
        # GenAI operations keywords (good)
        good_keywords = [
            'cost', 'spending', 'efficiency', 'confidence', 'extraction', 'document',
            'compliance', 'obligation', 'agent', 'batch', 'processing', 'model',
            'token', 'performance', 'quality', 'risk', 'user', 'operational'
        ]
        
        # Generic or irrelevant keywords (bad)
        bad_keywords = [
            'weather', 'sports', 'entertainment', 'recipes', 'jokes', 'games',
            'personal', 'dating', 'shopping', 'travel', 'social media'
        ]
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            # Check for bad keywords
            has_bad_keywords = any(bad_word in suggestion_lower for bad_word in bad_keywords)
            if has_bad_keywords:
                continue
            
            # Check for good keywords or analytical patterns
            has_good_keywords = any(good_word in suggestion_lower for good_word in good_keywords)
            has_analytical_pattern = any(pattern in suggestion_lower for pattern in [
                'what', 'which', 'how', 'show', 'compare', 'analyze', 'track', 'find'
            ])
            
            if has_good_keywords or has_analytical_pattern:
                validated.append(suggestion)
        
        return validated
    
    def _generate_contextual_fallback_suggestions(self, question: str, result: Dict) -> List[str]:
        """Generate context-aware fallback suggestions for GenAI operations"""
        question_lower = question.lower()
        suggestions = []
        
        # Cost-related follow-ups
        if any(keyword in question_lower for keyword in ['cost', 'spending', 'price', 'expensive']):
            suggestions.extend([
                'Which AI models are most cost-effective?',
                'Show me cost trends over the last 3 months',
                'Compare costs between document types',
                'Which users generate the highest AI costs?'
            ])
        
        # Document processing follow-ups
        elif any(keyword in question_lower for keyword in ['document', 'extraction', 'confidence']):
            suggestions.extend([
                'Show me documents with low confidence scores',
                'Which document types have highest accuracy?',
                'What are our extraction success rates?',
                'Compare processing times by document size'
            ])
        
        # Compliance follow-ups
        elif any(keyword in question_lower for keyword in ['compliance', 'obligation', 'legal', 'risk']):
            suggestions.extend([
                'What are our highest risk compliance items?',
                'Show me recent compliance obligation changes',
                'Which contracts need compliance review?',
                'Track compliance resolution progress'
            ])
        
        # Agent/performance follow-ups
        elif any(keyword in question_lower for keyword in ['agent', 'performance', 'batch', 'processing']):
            suggestions.extend([
                'How can we improve agent performance?',
                'Show me batch processing failure patterns',
                'Which agents handle complex documents best?',
                'What causes processing delays?'
            ])
        
        # General operational follow-ups
        else:
            suggestions.extend([
                'What are our key operational metrics today?',
                'Show me system health overview',
                'Which areas need immediate attention?',
                'Compare this month vs last month performance'
            ])
        
        # Add result-specific suggestions
        if result.get('query_data', {}).get('collection'):
            collection = result['query_data']['collection']
            if collection == 'costevalutionforllm':
                suggestions.append('Break down costs by model and operation type')
            elif collection == 'documentextractions':
                suggestions.append('Show me extraction confidence distribution')
            elif collection == 'obligationextractions':
                suggestions.append('Which obligations require immediate action?')
        
        return suggestions[:5]  # Return top 5
    
    def get_default_suggestions(self) -> List[str]:
        """Get the default fallback suggestions for GenAI operations"""
        return self.default_suggestions.copy()


class MemoryRAGManager:
    """
    Advanced Memory RAG system for chat-based conversational AI
    Enhanced for GenAI operations and document intelligence
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
        
        # GenAI domain context
        self.domain_context = {
            "domain": "AI Operations & Document Intelligence",
            "key_entities": [
                "AI models", "document types", "compliance obligations", 
                "processing batches", "extraction confidence", "users", "agents"
            ],
            "important_metrics": [
                "costs", "token usage", "confidence scores", "processing times",
                "success rates", "compliance status"
            ]
        }
        
    def ensure_memory_indexes(self):
        """Create optimized indexes for memory retrieval"""
        try:
            # Core indexes for fast retrieval
            self.memory_collection.create_index([
                ("chat_id", 1),
                ("timestamp", -1)
            ])
            
            self.memory_collection.create_index([
                ("chat_id", 1),
                ("content_type", 1),
                ("importance_score", -1)
            ])
            
            self.memory_collection.create_index([
                ("keywords", 1),
                ("importance_score", -1)
            ])
            
            self.memory_collection.create_index([
                ("entities", 1),
                ("timestamp", -1)
            ])
            
            logger.info("✅ Memory indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Could not create memory indexes: {e}")
    
    async def store_memory(self, chat_id: str, content: str, content_type: str, 
                          context: Dict = None, importance_score: float = None) -> str:
        """
        Store a memory fragment with enhanced context extraction for GenAI operations
        """
        try:
            # Generate unique fragment ID
            fragment_id = self._generate_fragment_id(chat_id, content)
            
            # Extract keywords and entities with GenAI focus
            keywords = self._extract_keywords(content)
            entities = self._extract_entities(content)
            
            # Calculate importance score
            if importance_score is None:
                importance_score = self._calculate_importance_score(content, content_type, context)
            
            # Create memory fragment
            memory_fragment = {
                "fragment_id": fragment_id,
                "chat_id": chat_id,
                "content": content,
                "content_type": content_type,
                "timestamp": utc_now(),
                "importance_score": importance_score,
                "keywords": keywords,
                "entities": entities,
                "related_fragments": [],
                "access_count": 0,
                "last_accessed": None,
                "context": context or {},
                "domain": self.domain_context["domain"]
            }
            
            # Store in database
            self.memory_collection.insert_one(memory_fragment)
            
            # Cleanup old memories if needed
            await self._cleanup_old_memories(chat_id)
            
            logger.debug(f"📝 Stored memory fragment: {fragment_id}")
            return fragment_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return ""
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords with focus on GenAI operations"""
        content_lower = content.lower()
        
        # GenAI-specific keywords
        genai_keywords = [
            'cost', 'spending', 'token', 'model', 'document', 'extraction',
            'confidence', 'compliance', 'obligation', 'agent', 'batch',
            'processing', 'efficiency', 'performance', 'quality', 'risk'
        ]
        
        # Technical terms
        technical_terms = [
            'llm', 'ai', 'machine learning', 'nlp', 'api', 'database',
            'pipeline', 'workflow', 'automation', 'optimization'
        ]
        
        # Business metrics
        business_metrics = [
            'revenue', 'profit', 'roi', 'efficiency', 'productivity',
            'success rate', 'failure rate', 'accuracy', 'precision'
        ]
        
        all_keywords = genai_keywords + technical_terms + business_metrics
        found_keywords = [kw for kw in all_keywords if kw in content_lower]
        
        # Add important phrases
        important_phrases = re.findall(r'\b(?:high|low|increase|decrease|improve|optimize)\s+\w+', content_lower)
        found_keywords.extend(important_phrases)
        
        return list(set(found_keywords))[:10]  # Limit to top 10
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract entities relevant to GenAI operations"""
        entities = []
        
        # Model names (common AI models)
        model_patterns = [
            r'\b(gpt-\d+|claude|gemini|llama|bert|t5)\w*\b',
            r'\b(openai|anthropic|google|meta|huggingface)\w*\b'
        ]
        
        # Document types
        doc_patterns = [
            r'\b(contract|agreement|policy|report|invoice|receipt)\w*\b',
            r'\b(pdf|docx|txt|json|xml|csv)\b'
        ]
        
        # Business entities
        business_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # Currency amounts
            r'\b\d+%\b',  # Percentages
            r'\b\d+\s*(?:tokens|documents|batches|users)\b'  # Quantities
        ]
        
        all_patterns = model_patterns + doc_patterns + business_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))[:8]  # Limit to top 8
    
    def _calculate_importance_score(self, content: str, content_type: str, context: Dict = None) -> float:
        """Calculate importance score with GenAI operations focus"""
        score = 0.5  # Base score
        
        # Content type weights
        type_weights = {
            'question': 0.7,
            'answer': 0.8,
            'insight': 0.9,
            'preference': 0.6,
            'fact': 0.7,
            'error': 0.4
        }
        score = type_weights.get(content_type, 0.5)
        
        # High-value keywords boost
        high_value_keywords = [
            'cost', 'expensive', 'efficient', 'optimize', 'improve',
            'critical', 'urgent', 'important', 'risk', 'compliance',
            'failure', 'error', 'success', 'performance'
        ]
        
        content_lower = content.lower()
        keyword_boost = sum(0.1 for keyword in high_value_keywords if keyword in content_lower)
        score += min(keyword_boost, 0.3)  # Cap at 0.3 boost
        
        # Numerical data boost (specific metrics are valuable)
        if re.search(r'\d+(?:\.\d+)?[%$]?', content):
            score += 0.1
        
        # Question marks indicate queries (valuable for context)
        if '?' in content:
            score += 0.1
        
        # Context-based adjustments
        if context:
            if context.get('user_initiated'):
                score += 0.1
            if context.get('complex_query'):
                score += 0.15
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _generate_fragment_id(self, chat_id: str, content: str) -> str:
        """Generate unique fragment ID"""
        timestamp = str(int(utc_now().timestamp()))
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{chat_id}_{timestamp}_{content_hash}"
    
    async def build_conversation_context(self, chat_id: str, current_question: str) -> ConversationContext:
        """
        Build rich conversation context for GenAI operations
        """
        try:
            # Get relevant memories
            relevant_memories = await self._get_relevant_memories(chat_id, current_question)
            
            # Extract conversation themes
            themes = self._extract_conversation_themes(relevant_memories)
            
            # Get user preferences
            preferences = await self._get_user_preferences(chat_id)
            
            # Extract recent entities
            recent_entities = self._get_recent_entities(relevant_memories)
            
            # Build session context
            session_context = await self._build_session_context(chat_id, relevant_memories)
            
            # Get current turn number
            current_turn = await self._get_conversation_turn(chat_id)
            
            context = ConversationContext(
                chat_id=chat_id,
                current_turn=current_turn,
                relevant_memories=relevant_memories,
                user_preferences=preferences,
                conversation_themes=themes,
                recent_entities=recent_entities,
                session_context=session_context
            )
            
            logger.debug(f"📋 Built conversation context: {len(relevant_memories)} memories, {len(themes)} themes")
            return context
            
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
    
    async def _get_relevant_memories(self, chat_id: str, question: str, limit: int = 10) -> List[MemoryFragment]:
        """Get relevant memories for the current question"""
        try:
            # Extract keywords from current question
            question_keywords = self._extract_keywords(question)
            
            # Build query for relevant memories
            query = {
                "chat_id": chat_id,
                "$or": [
                    {"keywords": {"$in": question_keywords}},
                    {"content": {"$regex": re.escape(question[:50]), "$options": "i"}},
                    {"importance_score": {"$gte": 0.7}}
                ]
            }
            
            # Get memories sorted by relevance and recency
            cursor = self.memory_collection.find(query).sort([
                ("importance_score", -1),
                ("timestamp", -1)
            ]).limit(limit)
            
            memories = []
            for doc in cursor:
                memory = MemoryFragment(
                    fragment_id=doc["fragment_id"],
                    chat_id=doc["chat_id"],
                    content=doc["content"],
                    content_type=doc["content_type"],
                    timestamp=doc["timestamp"],
                    importance_score=doc["importance_score"],
                    keywords=doc.get("keywords", []),
                    entities=doc.get("entities", []),
                    related_fragments=doc.get("related_fragments", []),
                    access_count=doc.get("access_count", 0),
                    last_accessed=doc.get("last_accessed")
                )
                memories.append(memory)
            
            # Update access counts
            if memories:
                fragment_ids = [m.fragment_id for m in memories]
                self.memory_collection.update_many(
                    {"fragment_id": {"$in": fragment_ids}},
                    {
                        "$inc": {"access_count": 1},
                        "$set": {"last_accessed": utc_now()}
                    }
                )
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return []
    
    def _extract_conversation_themes(self, memories: List[MemoryFragment]) -> List[str]:
        """Extract conversation themes from memories"""
        all_keywords = []
        for memory in memories:
            all_keywords.extend(memory.keywords)
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Get top themes
        themes = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [theme[0] for theme in themes[:5]]
    
    async def _get_user_preferences(self, chat_id: str) -> Dict[str, Any]:
        """Get user preferences from stored memories"""
        try:
            cursor = self.memory_collection.find({
                "chat_id": chat_id,
                "content_type": "preference"
            }).sort("timestamp", -1).limit(5)
            
            preferences = {}
            for doc in cursor:
                content = doc["content"].lower()
                # Extract preference patterns
                if "prefer" in content:
                    pref_match = re.search(r"prefer (\w+)", content)
                    if pref_match:
                        preferences["preferred_analysis"] = pref_match.group(1)
                
                if "chart" in content:
                    chart_match = re.search(r"(bar|line|pie|chart)", content)
                    if chart_match:
                        preferences["preferred_chart_type"] = chart_match.group(1)
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    def _get_recent_entities(self, memories: List[MemoryFragment]) -> List[str]:
        """Get recently mentioned entities"""
        all_entities = []
        for memory in memories[-5:]:  # Last 5 memories
            all_entities.extend(memory.entities)
        
        # Remove duplicates while preserving order
        seen = set()
        recent_entities = []
        for entity in all_entities:
            if entity not in seen:
                seen.add(entity)
                recent_entities.append(entity)
        
        return recent_entities[:8]
    
    async def _build_session_context(self, chat_id: str, memories: List[MemoryFragment]) -> Dict[str, Any]:
        """Build session-specific context"""
        context = {
            "session_start": utc_now().isoformat(),
            "memory_count": len(memories),
            "domain": self.domain_context["domain"]
        }
        
        # Add recent analysis types
        recent_analyses = []
        for memory in memories[-3:]:
            if "analysis" in memory.content.lower():
                recent_analyses.append(memory.content[:50])
        
        context["recent_analyses"] = recent_analyses
        return context
    
    async def _get_conversation_turn(self, chat_id: str) -> int:
        """Get current conversation turn number"""
        try:
            count = self.memory_collection.count_documents({
                "chat_id": chat_id,
                "content_type": "question"
            })
            return count + 1
        except:
            return 1
    
    async def _cleanup_old_memories(self, chat_id: str):
        """Cleanup old memories to maintain performance"""
        try:
            # Remove memories older than decay period
            cutoff_date = utc_now() - timedelta(days=self.memory_decay_days)
            
            self.memory_collection.delete_many({
                "chat_id": chat_id,
                "timestamp": {"$lt": cutoff_date},
                "importance_score": {"$lt": 0.7}  # Keep important memories longer
            })
            
            # Limit total memories per chat
            total_count = self.memory_collection.count_documents({"chat_id": chat_id})
            
            if total_count > self.max_memory_fragments:
                # Remove oldest, least important memories
                excess_count = total_count - self.max_memory_fragments
                
                oldest_memories = self.memory_collection.find({
                    "chat_id": chat_id
                }).sort([
                    ("importance_score", 1),
                    ("timestamp", 1)
                ]).limit(excess_count)
                
                fragment_ids = [doc["fragment_id"] for doc in oldest_memories]
                
                self.memory_collection.delete_many({
                    "fragment_id": {"$in": fragment_ids}
                })
                
                logger.debug(f"🧹 Cleaned up {excess_count} old memories for chat {chat_id}")
                
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {e}")
    
    def format_memory_context_for_ai(self, context: ConversationContext) -> str:
        """
        Format conversation context for AI processing
        """
        context_parts = []
        
        # Add domain context
        context_parts.append(f"DOMAIN: {self.domain_context['domain']}")
        
        # Add conversation themes
        if context.conversation_themes:
            themes = ", ".join(context.conversation_themes[:3])
            context_parts.append(f"RECENT TOPICS: {themes}")
        
        # Add recent entities
        if context.recent_entities:
            entities = ", ".join(context.recent_entities[:5])
            context_parts.append(f"RECENT ENTITIES: {entities}")
        
        # Add relevant memories
        if context.relevant_memories:
            memory_snippets = []
            for memory in context.relevant_memories[:3]:  # Top 3 most relevant
                snippet = memory.content[:100] + "..." if len(memory.content) > 100 else memory.content
                memory_snippets.append(f"- {snippet}")
            
            context_parts.append("RELEVANT CONTEXT:")
            context_parts.extend(memory_snippets)
        
        # Add user preferences
        if context.user_preferences:
            prefs = []
            for key, value in context.user_preferences.items():
                prefs.append(f"{key}: {value}")
            context_parts.append(f"USER PREFERENCES: {', '.join(prefs)}")
        
        return "\n".join(context_parts)


class MemoryEnhancedProcessor:
    """
    Enhanced processor that combines base analytics with memory and smart suggestions
    Optimized for GenAI operations and document intelligence
    """
    
    def __init__(self, base_processor, memory_manager: MemoryRAGManager, gemini_client=None):
        self.base_processor = base_processor
        self.memory_manager = memory_manager
        
        # Initialize smart suggestion generator if Gemini is available
        self.suggestion_generator = None
        if gemini_client:
            self.suggestion_generator = SmartSuggestionGenerator(gemini_client, memory_manager)
            logger.info("✅ Smart Suggestion Generator initialized for GenAI operations")
    
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
                context={'turn': context.current_turn, 'user_initiated': True}
            )
            
            # Format memory context for AI
            memory_context = self.memory_manager.format_memory_context_for_ai(context)
            
            # Enhanced question with memory context
            enhanced_question = f"{memory_context}\nUSER QUESTION: {question}"
            
            # Process with base processor (YOUR EXISTING FLOW - UNCHANGED)
            if hasattr(self.base_processor, 'process_question'):
                # For analytics processor with async support
                if asyncio.iscoroutinefunction(self.base_processor.process_question):
                    result = await self.base_processor.process_question(enhanced_question)
                else:
                    result = self.base_processor.process_question(enhanced_question)
            else:
                # Fallback for different processor interfaces
                result = {"success": False, "error": "Processor interface not supported"}
            
            # Store the AI response as memory
            if result.get('success'):
                response_content = result.get('summary', 'Analysis completed successfully')
                await self.memory_manager.store_memory(
                    chat_id=chat_id,
                    content=response_content,
                    content_type='answer',
                    context={'turn': context.current_turn, 'success': True}
                )
                
                # Store insights as facts
                if result.get('insights'):
                    for insight in result['insights']:
                        await self.memory_manager.store_memory(
                            chat_id=chat_id,
                            content=f"Insight: {insight}",
                            content_type='fact',
                            context={'turn': context.current_turn}
                        )
            
            # Generate smart suggestions (async in background if possible)
            if self.suggestion_generator:
                try:
                    # Try to generate smart suggestions
                    smart_suggestions = await self.suggestion_generator.generate_smart_suggestions(
                        question, result, context.session_context
                    )
                    
                    # Add smart suggestions to result
                    result['smart_suggestions'] = smart_suggestions
                    result['suggestions'] = smart_suggestions  # Backward compatibility
                    
                except Exception as e:
                    logger.warning(f"Smart suggestion generation failed: {e}")
                    # Fallback to default suggestions
                    result['suggestions'] = self.suggestion_generator.get_default_suggestions()
            else:
                # Use memory-based suggestions if no Gemini
                result['suggestions'] = self._generate_memory_based_suggestions(context, question)
            
            # Add memory context info to result
            result['memory_context'] = {
                'relevant_memories_count': len(context.relevant_memories),
                'conversation_themes': context.conversation_themes,
                'turn_number': context.current_turn,
                'has_preferences': bool(context.user_preferences)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Memory-enhanced processing failed: {e}")
            
            # Fallback to base processor without memory
            try:
                if hasattr(self.base_processor, 'process_question'):
                    if asyncio.iscoroutinefunction(self.base_processor.process_question):
                        result = await self.base_processor.process_question(question)
                    else:
                        result = self.base_processor.process_question(question)
                    
                    # Add basic suggestions
                    if self.suggestion_generator:
                        result['suggestions'] = self.suggestion_generator.get_default_suggestions()
                    
                    return result
                else:
                    return {"success": False, "error": f"Processing failed: {str(e)}"}
                    
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {fallback_error}")
                return {"success": False, "error": "Complete processing failure"}
    
    def _generate_memory_based_suggestions(self, context: ConversationContext, question: str) -> List[str]:
        """Generate suggestions based on memory context when Gemini is not available"""
        suggestions = []
        
        # Theme-based suggestions
        for theme in context.conversation_themes[:2]:
            if theme in ['cost', 'spending']:
                suggestions.append(f"Show me more details about {theme} optimization")
            elif theme in ['document', 'extraction']:
                suggestions.append(f"Analyze {theme} processing trends")
            elif theme in ['compliance', 'obligation']:
                suggestions.append(f"Review {theme} risk assessment")
        
        # Entity-based suggestions
        for entity in context.recent_entities[:2]:
            if '$' in entity:  # Currency amount
                suggestions.append(f"Compare costs with {entity} as baseline")
            elif '%' in entity:  # Percentage
                suggestions.append(f"Show breakdown of the {entity} metric")
        
        # Default GenAI suggestions if none generated
        if not suggestions:
            suggestions = [
                "What are our current AI operational costs?",
                "Show me document processing efficiency",
                "Which compliance items need attention?",
                "How are our systems performing today?"
            ]
        
        return suggestions[:5]
    
    async def get_conversation_summary(self, chat_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation summary with memory insights"""
        try:
            context = await self.memory_manager.build_conversation_context(chat_id, "")
            
            # Get memory statistics
            memory_stats = await self._get_memory_statistics(chat_id)
            
            # Build comprehensive summary
            summary = {
                "chat_id": chat_id,
                "total_turns": context.current_turn,
                "conversation_themes": context.conversation_themes,
                "recent_entities": context.recent_entities,
                "user_preferences": context.user_preferences,
                "memory_stats": memory_stats,
                "domain": "AI Operations & Document Intelligence",
                "last_active": utc_now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return {"chat_id": chat_id, "error": str(e)}
    
    async def _get_memory_statistics(self, chat_id: str) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        try:
            total_memories = self.memory_manager.memory_collection.count_documents({
                "chat_id": chat_id
            })
            
            # Get memory types breakdown
            pipeline = [
                {"$match": {"chat_id": chat_id}},
                {"$group": {
                    "_id": "$content_type",
                    "count": {"$sum": 1},
                    "avg_importance": {"$avg": "$importance_score"}
                }}
            ]
            
            type_stats = {}
            for doc in self.memory_manager.memory_collection.aggregate(pipeline):
                type_stats[doc["_id"]] = {
                    "count": doc["count"],
                    "avg_importance": round(doc["avg_importance"], 2)
                }
            
            return {
                "total_memories": total_memories,
                "memory_types": type_stats,
                "retention_days": self.memory_manager.memory_decay_days
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory statistics: {e}")
            return {"total_memories": 0}
    
    async def reset_conversation_memory(self, chat_id: str) -> bool:
        """Reset all memory for a conversation"""
        try:
            result = self.memory_manager.memory_collection.delete_many({
                "chat_id": chat_id
            })
            
            logger.info(f"🔄 Reset {result.deleted_count} memories for chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset conversation memory: {e}")
            return False
    
    async def export_conversation_memory(self, chat_id: str) -> Dict[str, Any]:
        """Export conversation memory for analysis or backup"""
        try:
            memories = []
            cursor = self.memory_manager.memory_collection.find({
                "chat_id": chat_id
            }).sort("timestamp", 1)
            
            for doc in cursor:
                # Clean up document for export
                memory = {
                    "fragment_id": doc["fragment_id"],
                    "content": doc["content"],
                    "content_type": doc["content_type"],
                    "timestamp": doc["timestamp"].isoformat(),
                    "importance_score": doc["importance_score"],
                    "keywords": doc.get("keywords", []),
                    "entities": doc.get("entities", []),
                    "access_count": doc.get("access_count", 0)
                }
                memories.append(memory)
            
            return {
                "chat_id": chat_id,
                "export_timestamp": utc_now().isoformat(),
                "total_memories": len(memories),
                "memories": memories
            }
            
        except Exception as e:
            logger.error(f"Failed to export conversation memory: {e}")
            return {"chat_id": chat_id, "error": str(e)}


# Utility functions for memory management
def clean_memory_content(content: str) -> str:
    """Clean and normalize memory content"""
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content.strip())
    
    # Remove special characters that might cause issues
    content = re.sub(r'[^\w\s\.\?\!\,\:\;\-\$\%\(\)]', '', content)
    
    # Limit length
    if len(content) > 1000:
        content = content[:997] + "..."
    
    return content

def extract_numerical_insights(content: str) -> List[str]:
    """Extract numerical insights from content"""
    insights = []
    
    # Currency amounts
    currency_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
    for match in currency_matches:
        insights.append(f"Amount mentioned: {match}")
    
    # Percentages
    percentage_matches = re.findall(r'\d+(?:\.\d+)?%', content)
    for match in percentage_matches:
        insights.append(f"Percentage mentioned: {match}")
    
    # Counts
    count_matches = re.findall(r'\b\d+\s*(?:documents|batches|users|items|records)\b', content, re.IGNORECASE)
    for match in count_matches:
        insights.append(f"Count mentioned: {match}")
    
    return insights

def calculate_content_similarity(content1: str, content2: str) -> float:
    """Calculate similarity between two pieces of content"""
    # Simple keyword-based similarity
    words1 = set(content1.lower().split())
    words2 = set(content2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0