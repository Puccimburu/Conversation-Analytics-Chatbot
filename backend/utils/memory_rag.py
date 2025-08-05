# backend/utils/memory_rag.py - FIXED VERSION WITH COMPLETE LOGGING
"""
Memory RAG System with Complete Chat History Logging
Fixed to properly log ALL memory storage operations
"""

import logging
import re
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)

def utc_now():
    """Get current UTC time"""
    return datetime.now(timezone.utc)

@dataclass
class MemoryFragment:
    """Simplified memory fragment"""
    fragment_id: str
    chat_id: str
    content: str
    content_type: str  # 'question', 'answer', 'fact'
    timestamp: datetime
    importance_score: float
    keywords: List[str]

class SmartSuggestionGenerator:
    """Generates intelligent follow-up questions"""
    
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client
        self.default_suggestions = [
            'What are our AI operational costs this month?',
            'Show me document extraction confidence trends',
            'Which compliance obligations need attention?',
            'How are our AI agents performing?',
            'Compare processing efficiency across document types'
        ]
    
    async def generate_smart_suggestions(self, question: str, result: Dict) -> List[str]:
        """Generate contextual follow-up suggestions"""
        try:
            if not self.gemini_client:
                return self._get_contextual_suggestions(question)
            
            # Extract data context for better suggestions
            data_context = self._extract_data_context(result)
            
            # Use Gemini for smart suggestions
            prompt = f"""
Generate 3 practical follow-up questions based on the user's query and data results.

Original Question: "{question}"
Data Context: {data_context}

Generate questions that would naturally follow from seeing this data:
- If showing users/people, ask about roles, status, specific groups, filtering
- If showing data over time, ask about trends, comparisons, specific periods  
- If showing categories/groups, ask about breakdowns, specific items, comparisons
- If showing numbers/metrics, ask about what drives them, comparisons, details

Make questions practical and directly related to what the user just saw.
Return only the questions, one per line, no numbering.
"""
            
            # Generate suggestions using Gemini
            response = self.gemini_client.model.generate_content(prompt)
            if response and response.strip():
                suggestions = [s.strip() for s in response.strip().split('\n') if s.strip()]
                suggestions = suggestions[:3]  # Take first 3
                logger.info(f"🎯 Generated {len(suggestions)} smart suggestions: {suggestions}")
                return suggestions
            
        except Exception as e:
            logger.warning(f"Gemini suggestion generation failed: {e}")
        
        # Fallback to contextual suggestions
        return self._get_contextual_suggestions(question)
    
    def _extract_data_context(self, result: Dict) -> str:
        """Extract relevant data context for suggestion generation"""
        context_parts = []
        
        if result.get('results_count'):
            context_parts.append(f"Showing {result['results_count']} results")
        
        if result.get('chart_data', {}).get('tableData'):
            table_data = result['chart_data']['tableData']
            if table_data and len(table_data) > 0:
                fields = list(table_data[0].keys())
                context_parts.append(f"Fields: {', '.join(fields[:5])}")
        
        if result.get('insights'):
            context_parts.append(f"Key insight: {result['insights'][0][:100]}")
        
        return "; ".join(context_parts) if context_parts else "General query results"
    
    def _get_contextual_suggestions(self, question: str) -> List[str]:
        """Generate context-aware suggestions based on question keywords"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['user', 'users', 'people', 'person']):
            return [
                'Can I filter this list by creation date?',
                'What roles are associated with these users?',
                'How can I export this user list to a CSV file?'
            ]
        elif any(word in question_lower for word in ['document', 'documents', 'file', 'files']):
            return [
                'What is the confidence level distribution?',
                'Show me documents processed in the last week',
                'Group these documents by extraction status'
            ]
        elif any(word in question_lower for word in ['trend', 'over time', 'daily', 'monthly']):
            return [
                'Compare this with the previous period',
                'Break this down by week instead of month',
                'What happened in the last 30 days?'
            ]
        elif any(word in question_lower for word in ['data', 'records', 'entries']):
            return [
                'Filter this data by specific criteria',
                'Show me the most recent entries',
                'Group this data by category'
            ]
        
        return [
            'Filter this data by specific criteria',
            'Show me more details about these results', 
            'What are the most recent entries?'
        ]

class MemoryRAGManager:
    """Simplified Memory RAG system with complete logging"""
    
    def __init__(self, database, gemini_client=None):
        self.db = database
        self.memory_collection = self.db.chat_memories
        self._ensure_indexes()
        
        # Simple configuration
        self.max_memories = 500  # Per chat
        self.retention_days = 30
    
    def _ensure_indexes(self):
        """Create essential indexes"""
        try:
            self.memory_collection.create_index([("chat_id", 1), ("timestamp", -1)])
            self.memory_collection.create_index([("keywords", 1), ("importance_score", -1)])
            self.memory_collection.create_index([("chat_id", 1), ("content_type", 1), ("timestamp", -1)])
            logger.info("✅ Memory indexes created successfully")
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    async def store_memory(self, chat_id: str, content: str, content_type: str, query_context: dict = None) -> str:
        """Store a memory fragment with optional query context - NOW WITH COMPLETE LOGGING"""
        try:
            fragment_id = self._generate_id(chat_id, content)
            keywords = self._extract_keywords(content)
            importance = self._calculate_importance(content, content_type)
            
            memory = {
                "fragment_id": fragment_id,
                "chat_id": chat_id,
                "content": content,
                "content_type": content_type,
                "timestamp": utc_now(),
                "importance_score": importance,
                "keywords": keywords
            }
            
            # Store query context for answers to help with follow-up queries
            if query_context and content_type == 'answer':
                memory["query_context"] = {
                    "collection": query_context.get("collection"),
                    "result_count": query_context.get("result_count"),
                    "fields": query_context.get("fields", [])
                }
            
            # INSERT INTO DATABASE
            self.memory_collection.insert_one(memory)
            
            # 🔥 FIXED: LOG ALL MEMORY STORAGE OPERATIONS 🔥
            content_preview = content[:100] + "..." if len(content) > 100 else content
            logger.info(f"📝 Stored {content_type} memory: {fragment_id} for chat {chat_id}")
            logger.info(f"🧠 Stored {content_type.upper()} in memory: {fragment_id} - Content: {content_preview}")
            
            # Cleanup old memories
            await self._cleanup_old_memories(chat_id)
            return fragment_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return ""
    
    async def get_conversation_context(self, chat_id: str, question: str) -> str:
        """Get relevant conversation context with data context"""
        try:
            question_keywords = self._extract_keywords(question)
            
            # Get the most recent memory with query context (last data shown)
            recent_data_context = self.memory_collection.find_one({
                "chat_id": chat_id,
                "content_type": "answer",
                "query_context": {"$exists": True}
            }, sort=[("timestamp", -1)])
            
            # Get relevant memories for general context
            query = {
                "chat_id": chat_id,
                "$or": [
                    {"keywords": {"$in": question_keywords}},
                    {"importance_score": {"$gte": 0.7}}
                ]
            }
            
            memories = list(self.memory_collection.find(query)
                          .sort([("importance_score", -1), ("timestamp", -1)])
                          .limit(5))
            
            # Format context
            context_parts = ["DOMAIN: AI Operations & Document Intelligence"]
            
            # Add data context if available
            if recent_data_context and recent_data_context.get('query_context'):
                ctx = recent_data_context['query_context']
                context_parts.append(f"RECENT CONTEXT: User recently viewed {ctx.get('collection', 'data')} ({ctx.get('result_count', 0)} items)")
            
            # Add relevant memories
            if memories:
                context_parts.append("RELEVANT CONTEXT:")
                for memory in memories:
                    content_preview = memory['content'][:150]
                    context_parts.append(f"- {memory['content_type'].title()}: {content_preview}")
            
            # Add the current question
            context_parts.append(f"USER QUESTION: {question}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            return question
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract meaningful keywords from content"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'cannot', 'this', 'that', 'these', 'those'}
        
        # Extract words (alphanumeric + basic punctuation)
        words = re.findall(r'\b[a-zA-Z0-9_]+\b', content.lower())
        
        # Filter meaningful keywords
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        return list(set(keywords))[:10]  # Unique keywords, max 10
    
    def _calculate_importance(self, content: str, content_type: str) -> float:
        """Calculate importance score for memory prioritization"""
        # Base scores by type
        base_scores = {
            'question': 0.6,
            'answer': 0.7,
            'fact': 0.8
        }
        
        base_score = base_scores.get(content_type, 0.5)
        
        # Boost for specific patterns
        boost = 0.0
        if any(word in content.lower() for word in ['error', 'issue', 'problem', 'fail']):
            boost += 0.2
        if any(word in content.lower() for word in ['important', 'critical', 'urgent']):
            boost += 0.2
        if len(content) > 200:  # Detailed content
            boost += 0.1
        if re.search(r'\d+', content):  # Contains numbers
            boost += 0.1
        
        return min(base_score + boost, 1.0)
    
    def _generate_id(self, chat_id: str, content: str) -> str:
        """Generate unique fragment ID"""
        timestamp = str(int(utc_now().timestamp()))
        content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
        return f"{chat_id}_{timestamp}_{content_hash}"
    
    async def _cleanup_old_memories(self, chat_id: str):
        """Remove old memories to maintain performance"""
        try:
            # Remove old memories
            cutoff = utc_now() - timedelta(days=self.retention_days)
            self.memory_collection.delete_many({
                "chat_id": chat_id,
                "timestamp": {"$lt": cutoff},
                "importance_score": {"$lt": 0.7}
            })
            
            # Limit total memories
            total = self.memory_collection.count_documents({"chat_id": chat_id})
            if total > self.max_memories:
                excess = total - self.max_memories
                oldest = self.memory_collection.find({"chat_id": chat_id}) \
                    .sort([("importance_score", 1), ("timestamp", 1)]) \
                    .limit(excess)
                
                ids = [doc["fragment_id"] for doc in oldest]
                self.memory_collection.delete_many({"fragment_id": {"$in": ids}})
                
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    async def get_chat_history(self, chat_id: str, limit: int = 10) -> List[Dict]:
        """Get recent chat history for debugging"""
        try:
            memories = list(self.memory_collection.find({"chat_id": chat_id})
                          .sort([("timestamp", -1)])
                          .limit(limit))
            return memories
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []

    async def get_memory_stats(self, chat_id: str) -> Dict[str, int]:
        """Get memory statistics for debugging"""
        try:
            pipeline = [
                {"$match": {"chat_id": chat_id}},
                {"$group": {
                    "_id": "$content_type",
                    "count": {"$sum": 1}
                }}
            ]
            stats = {}
            for result in self.memory_collection.aggregate(pipeline):
                stats[result["_id"]] = result["count"]
            return stats
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}

class MemoryEnhancedProcessor:
    """Simplified memory-enhanced processor"""
    
    def __init__(self, base_processor, memory_manager: MemoryRAGManager, gemini_client=None):
        self.base_processor = base_processor
        self.memory_manager = memory_manager
        self.suggestion_generator = SmartSuggestionGenerator(gemini_client) if gemini_client else None
    
    def _clean_memory_metadata_from_response(self, result: Dict[str, Any], original_question: str) -> Dict[str, Any]:
        """Clean memory metadata from user-facing response"""
        if result.get('summary'):
            clean_lines = []
            for line in result['summary'].split('\n'):
                # Remove lines that contain memory context metadata
                if not any(prefix in line for prefix in ['DOMAIN:', 'RELEVANT CONTEXT:', 'RECENT TOPICS:', 'USER QUESTION:']):
                    clean_lines.append(line)
            
            if clean_lines:
                result['summary'] = '\n'.join(clean_lines).strip()
            else:
                # Fallback summary
                result['summary'] = f"Analysis completed for: {original_question}"
        
        return result
    
    def _extract_collection_from_result(self, result: Dict) -> str:
        """Extract collection name from query result"""
        # Try multiple ways to get collection name
        if result.get('query_data', {}).get('collection'):
            return result['query_data']['collection']
        elif result.get('query_source') and 'users' in str(result).lower():
            return 'users'
        elif result.get('query_source') and 'batches' in str(result).lower():
            return 'batches'
        elif result.get('query_source') and 'documents' in str(result).lower():
            return 'documents'
        return 'unknown'
    
    async def process_with_memory(self, question: str, chat_id: str) -> Dict[str, Any]:
        """Process question with memory context"""
        try:
            # 🔥 CRITICAL FIX: Store user question with logging
            question_fragment_id = await self.memory_manager.store_memory(chat_id, question, 'question')
            logger.info(f"💬 USER QUESTION stored: {question_fragment_id} - '{question[:50]}...'")
            
            # Get conversation context (for AI processing only)
            enhanced_question = await self.memory_manager.get_conversation_context(chat_id, question)
            
            # Process with base processor
            if hasattr(self.base_processor, 'process_question'):
                if asyncio.iscoroutinefunction(self.base_processor.process_question):
                    result = await self.base_processor.process_question(enhanced_question)
                else:
                    result = self.base_processor.process_question(enhanced_question)
            else:
                result = {"success": False, "error": "Processor interface not supported"}
            
            # Clean up memory metadata from user-facing content
            if result.get('success'):
                result = self._clean_memory_metadata_from_response(result, question)
            
            # Store AI response (use cleaned summary) with query context
            if result.get('success'):
                response_content = result.get('summary', 'Analysis completed')
                
                # Extract query context from result for better follow-up context
                query_context = None
                if result.get('chart_data', {}).get('tableData'):
                    table_data = result['chart_data']['tableData']
                    if table_data:
                        sample_fields = list(table_data[0].keys()) if len(table_data) > 0 else []
                        query_context = {
                            "collection": self._extract_collection_from_result(result),
                            "result_count": result.get('results_count', len(table_data)),
                            "fields": sample_fields[:10]  # Store field names for context
                        }
                
                answer_fragment_id = await self.memory_manager.store_memory(chat_id, response_content, 'answer', query_context)
                logger.info(f"🤖 AI ANSWER stored: {answer_fragment_id} - Summary: {response_content[:50]}...")
                
                # Store insights as separate facts
                if result.get('insights'):
                    for insight in result['insights']:
                        insight_fragment_id = await self.memory_manager.store_memory(
                            chat_id, 
                            f"Insight: {insight}", 
                            'fact'
                        )
                        logger.info(f"💡 INSIGHT stored: {insight_fragment_id} - {insight[:50]}...")
            
            # Generate smart suggestions (use original question, not enhanced)
            if self.suggestion_generator:
                try:
                    suggestions = await self.suggestion_generator.generate_smart_suggestions(question, result)
                    result['suggestions'] = suggestions
                    logger.info(f"🎯 Added {len(suggestions)} suggestions to result: {suggestions}")
                except Exception as e:
                    logger.warning(f"Suggestion generation failed: {e}")
                    result['suggestions'] = self.suggestion_generator.default_suggestions[:3]
            
            # Add memory metadata (for internal use)
            result['memory_context'] = {
                'enhanced_with_memory': True,
                'chat_id': chat_id,
                'question_fragment_id': question_fragment_id,
                'answer_fragment_id': result.get('answer_fragment_id')
            }
            
            # Debug: Log final result structure
            logger.info(f"🔍 FINAL RESULT: keys={list(result.keys())}, suggestions_count={len(result.get('suggestions', []))}")
            
            return result
            
        except Exception as e:
            logger.error(f"Memory processing failed: {e}")
            
            # Fallback to base processor
            try:
                if hasattr(self.base_processor, 'process_question'):
                    if asyncio.iscoroutinefunction(self.base_processor.process_question):
                        result = await self.base_processor.process_question(question)
                    else:
                        result = self.base_processor.process_question(question)
                    
                    # Even in fallback, try to generate suggestions
                    if self.suggestion_generator:
                        try:
                            fallback_suggestions = self.suggestion_generator._get_contextual_suggestions(question)
                            result['suggestions'] = fallback_suggestions
                            logger.info(f"🔄 Added fallback suggestions: {fallback_suggestions}")
                        except Exception as e2:
                            logger.warning(f"Even fallback suggestions failed: {e2}")
                            result['suggestions'] = []
                    
                    return result
                else:
                    return {"success": False, "error": f"Processing failed: {str(e)}"}
            except Exception as fallback_error:
                logger.error(f"Complete processing failure: {fallback_error}")
                return {"success": False, "error": "Complete processing failure"}