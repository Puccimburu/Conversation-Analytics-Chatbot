# backend/utils/memory_rag.py - COMPLETE FIXED VERSION
"""
Streamlined Memory RAG System for Conversational AI
Reduced from 800+ lines to ~200 lines while retaining core functionality
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
            
            response = self.gemini_client.model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                suggestions = self._parse_suggestions(response.text)
                logger.info(f"🎯 Generated {len(suggestions)} smart suggestions: {suggestions}")
                return suggestions[:3] if suggestions else self._get_contextual_suggestions(question)
            
        except Exception as e:
            logger.warning(f"Smart suggestion generation failed: {e}")
        
        return self._get_contextual_suggestions(question)
    
    def _extract_data_context(self, result: Dict) -> str:
        """Extract data context for better suggestion generation"""
        parts = []
        
        # Get collection/table info
        if result.get('query_data', {}).get('collection'):
            collection = result['query_data']['collection']
            parts.append(f"Collection: {collection}")
        
        # Get result count
        result_count = result.get('results_count', 0)
        if result_count:
            parts.append(f"Showing {result_count} records")
        
        # Get data fields if available (from chart data)
        if result.get('chart_data', {}).get('tableData'):
            table_data = result['chart_data']['tableData']
            if table_data and len(table_data) > 0:
                sample_fields = list(table_data[0].keys())
                parts.append(f"Fields: {', '.join(sample_fields[:5])}")
        
        return "; ".join(parts) if parts else "Data analysis completed"
    
    def _extract_result_summary(self, result: Dict) -> str:
        """Extract key info from result"""
        parts = []
        if result.get('query_data', {}).get('collection'):
            parts.append(f"Collection: {result['query_data']['collection']}")
        if result.get('raw_results'):
            parts.append(f"Records: {len(result['raw_results'])}")
        return "; ".join(parts) if parts else "Analysis completed"
    
    def _parse_suggestions(self, text: str) -> List[str]:
        """Parse suggestions from Gemini response"""
        lines = [line.strip() for line in text.strip().split('\n')]
        suggestions = []
        for line in lines:
            line = re.sub(r'^\d+[\.\)]\s*|^[-•*]\s*', '', line).strip('"\'')
            if line and len(line) > 10 and '?' in line:
                suggestions.append(line)
        return suggestions
    
    def _get_contextual_suggestions(self, question: str) -> List[str]:
        """Generate context-aware fallback suggestions"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['user', 'users', 'people', 'account']):
            return [
                'Which users are admins?',
                'Show me only active users',
                'Who are the most recently created users?'
            ]
        elif any(word in question_lower for word in ['admin', 'administrator', 'role']):
            return [
                'List all admin users',
                'Show users by role type',
                'Who has the most permissions?'
            ]
        elif any(word in question_lower for word in ['document', 'file', 'upload']):
            return [
                'Which documents were uploaded recently?',
                'Show documents by type',
                'Which users uploaded the most documents?'
            ]
        elif any(word in question_lower for word in ['activity', 'active', 'recent']):
            return [
                'Show recent user activity',
                'Which users are most active?',
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
    """Simplified Memory RAG system"""
    
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
        """Store a memory fragment with optional query context"""
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
            
            self.memory_collection.insert_one(memory)
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
            
            # Add current data context if available
            if recent_data_context and recent_data_context.get('query_context'):
                qc = recent_data_context['query_context']
                context_parts.append(f"CURRENT DATA: {qc.get('collection', 'unknown')} collection, {qc.get('result_count', 0)} records")
                if qc.get('fields'):
                    context_parts.append(f"AVAILABLE FIELDS: {', '.join(qc['fields'][:5])}")
            
            # Add recent conversation context
            if memories:
                context_parts.append("RECENT CONTEXT:")
                for memory in memories[:2]:
                    snippet = (memory['content'][:60] + "...") if len(memory['content']) > 60 else memory['content']
                    context_parts.append(f"- {snippet}")
            
            context_parts.append(f"USER QUESTION: {question}")
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return f"DOMAIN: AI Operations & Document Intelligence\nUSER QUESTION: {question}"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract GenAI operation keywords"""
        content_lower = content.lower()
        
        # GenAI-specific keywords
        keywords = [
            'cost', 'spending', 'token', 'model', 'document', 'extraction',
            'confidence', 'compliance', 'obligation', 'agent', 'batch',
            'processing', 'efficiency', 'performance', 'quality', 'risk'
        ]
        
        found = [kw for kw in keywords if kw in content_lower]
        
        # Add numbers and percentages
        numbers = re.findall(r'\$[\d,]+|\d+%|\d+\s*(?:tokens|documents|batches)', content_lower)
        found.extend(numbers)
        
        return list(set(found))[:8]
    
    def _calculate_importance(self, content: str, content_type: str) -> float:
        """Calculate importance score"""
        scores = {'question': 0.7, 'answer': 0.8, 'fact': 0.6}
        base_score = scores.get(content_type, 0.5)
        
        # Boost for high-value keywords
        high_value = ['critical', 'urgent', 'error', 'cost', 'risk', 'compliance']
        boost = sum(0.1 for word in high_value if word in content.lower())
        
        # Boost for numbers (specific metrics are valuable)
        if re.search(r'\d+(?:\.\d+)?[%$]?', content):
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

class MemoryEnhancedProcessor:
    """Simplified memory-enhanced processor"""
    
    def __init__(self, base_processor, memory_manager: MemoryRAGManager, gemini_client=None):
        self.base_processor = base_processor
        self.memory_manager = memory_manager
        self.suggestion_generator = SmartSuggestionGenerator(gemini_client) if gemini_client else None
    
    def _clean_memory_metadata_from_response(self, result: Dict[str, Any], original_question: str) -> Dict[str, Any]:
        """Clean memory metadata from response to avoid user-facing clutter"""
        if not isinstance(result, dict):
            return result
        
        # Clean chart title if it contains memory metadata
        chart_config = result.get('visualization', {}).get('chart_config', {})
        if chart_config:
            # Check multiple possible title locations
            title_paths = [
                ['options', 'plugins', 'title', 'text'],
                ['title'],
                ['options', 'title', 'text']
            ]
            
            for path in title_paths:
                current = chart_config
                for key in path[:-1]:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                
                if current and isinstance(current, dict) and path[-1] in current:
                    title = current[path[-1]]
                    if isinstance(title, str) and ('DOMAIN:' in title or 'USER QUESTION:' in title):
                        # Extract just the user question part
                        user_question_match = re.search(r'USER QUESTION:\s*(.+)$', title)
                        if user_question_match:
                            clean_title = user_question_match.group(1).strip()
                            current[path[-1]] = clean_title
                        else:
                            # Fallback to original question
                            current[path[-1]] = original_question.capitalize()
        
        # Clean summary if it contains metadata
        if result.get('summary') and ('DOMAIN:' in result['summary'] or 'RELEVANT CONTEXT:' in result['summary']):
            # Extract just the core summary without metadata
            lines = result['summary'].split('\n')
            clean_lines = []
            for line in lines:
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
            # Store user question
            await self.memory_manager.store_memory(chat_id, question, 'question')
            
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
                
                await self.memory_manager.store_memory(chat_id, response_content, 'answer', query_context)
            
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
                'chat_id': chat_id
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