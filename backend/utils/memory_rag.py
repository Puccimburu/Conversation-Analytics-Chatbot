# backend/utils/memory_rag.py - STREAMLINED VERSION
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
            
            # Use Gemini for smart suggestions
            prompt = f"""
Generate 3 intelligent follow-up questions for GenAI operations based on:
Question: "{question}"
Result: {self._extract_result_summary(result)}

Focus on: costs, document processing, compliance, performance optimization.
Return only the questions, one per line.
"""
            
            response = self.gemini_client.model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                suggestions = self._parse_suggestions(response.text)
                return suggestions[:3] if suggestions else self.default_suggestions[:3]
            
        except Exception as e:
            logger.warning(f"Smart suggestion generation failed: {e}")
        
        return self._get_contextual_suggestions(question)
    
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
        
        if any(word in question_lower for word in ['cost', 'spending', 'expensive']):
            return [
                'Which AI models are most cost-effective?',
                'Show me cost trends over the last 3 months',
                'Compare costs between document types'
            ]
        elif any(word in question_lower for word in ['document', 'extraction', 'confidence']):
            return [
                'Show me documents with low confidence scores',
                'Which document types have highest accuracy?',
                'Compare processing times by document size'
            ]
        elif any(word in question_lower for word in ['compliance', 'obligation', 'risk']):
            return [
                'What are our highest risk compliance items?',
                'Show me recent compliance changes',
                'Track compliance resolution progress'
            ]
        
        return self.default_suggestions[:3]

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
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
    
    async def store_memory(self, chat_id: str, content: str, content_type: str) -> str:
        """Store a memory fragment"""
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
            
            self.memory_collection.insert_one(memory)
            await self._cleanup_old_memories(chat_id)
            return fragment_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return ""
    
    async def get_conversation_context(self, chat_id: str, question: str) -> str:
        """Get relevant conversation context"""
        try:
            question_keywords = self._extract_keywords(question)
            
            # Get relevant memories
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
            
            if not memories:
                return f"DOMAIN: AI Operations & Document Intelligence\nUSER QUESTION: {question}"
            
            # Format context
            context_parts = ["DOMAIN: AI Operations & Document Intelligence"]
            
            # Add recent topics from memories
            recent_keywords = []
            for memory in memories:
                recent_keywords.extend(memory.get('keywords', []))
            
            if recent_keywords:
                top_topics = list(set(recent_keywords))[:3]
                context_parts.append(f"RECENT TOPICS: {', '.join(top_topics)}")
            
            # Add relevant memory snippets
            if memories:
                context_parts.append("RELEVANT CONTEXT:")
                for memory in memories[:3]:
                    snippet = (memory['content'][:80] + "...") if len(memory['content']) > 80 else memory['content']
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
    
    async def process_with_memory(self, question: str, chat_id: str) -> Dict[str, Any]:
        """Process question with memory context"""
        try:
            # Store user question
            await self.memory_manager.store_memory(chat_id, question, 'question')
            
            # Get conversation context
            enhanced_question = await self.memory_manager.get_conversation_context(chat_id, question)
            
            # Process with base processor
            if hasattr(self.base_processor, 'process_question'):
                if asyncio.iscoroutinefunction(self.base_processor.process_question):
                    result = await self.base_processor.process_question(enhanced_question)
                else:
                    result = self.base_processor.process_question(enhanced_question)
            else:
                result = {"success": False, "error": "Processor interface not supported"}
            
            # Store AI response
            if result.get('success'):
                response_content = result.get('summary', 'Analysis completed')
                await self.memory_manager.store_memory(chat_id, response_content, 'answer')
            
            # Generate smart suggestions
            if self.suggestion_generator:
                try:
                    suggestions = await self.suggestion_generator.generate_smart_suggestions(question, result)
                    result['suggestions'] = suggestions
                except Exception as e:
                    logger.warning(f"Suggestion generation failed: {e}")
                    result['suggestions'] = self.suggestion_generator.default_suggestions[:3]
            
            # Add memory metadata
            result['memory_context'] = {
                'enhanced_with_memory': True,
                'chat_id': chat_id
            }
            
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
                    return result
                else:
                    return {"success": False, "error": f"Processing failed: {str(e)}"}
            except Exception:
                return {"success": False, "error": "Complete processing failure"}