# backend/utils/conversational_handler.py
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import DATABASE_SCHEMA  # Import the new GenAI schema

logger = logging.getLogger(__name__)

class ConversationalHandler:
    """
    Handles conversational queries like greetings, system information, and general help.
    Enhanced for GenAI operations and document intelligence domain.
    """
    
    def __init__(self, database_manager, gemini_client):
        self.db_manager = database_manager
        self.gemini_client = gemini_client
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> Dict:
        """Get GenAI database schema information from config"""
        return {
            "collections": DATABASE_SCHEMA["collections"],
            "domain": "AI Operations & Document Intelligence",
            "primary_collections": [
                "costevalutionforllm", "documentextractions", "obligationextractions",
                "agent_activity", "batches", "users", "conversations"
            ],
            "sample_analysis_types": [
                "AI cost tracking", "document processing metrics", "compliance analysis",
                "agent performance", "user activity", "operational efficiency"
            ],
            "sample_data_points": {
                "ai_operations": ["AI spending", "token usage", "model performance"],
                "document_processing": ["extraction confidence", "processing times", "success rates"],
                "compliance": ["legal obligations", "risk assessment", "regulatory tracking"],
                "operational": ["batch efficiency", "user productivity", "system health"]
            }
        }
    
    def is_conversational_query(self, query: str) -> bool:
        """
        Determine if a query is conversational rather than analytical.
        """
        query_lower = query.lower().strip()
        
        # Greeting patterns
        greeting_patterns = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
            'greetings', 'howdy', 'what\'s up', 'how are you'
        ]
        
        # System information patterns
        system_patterns = [
            'what do you do', 'what can you do', 'how do you work', 'help me',
            'what is this', 'about you', 'your capabilities', 'how to use',
            'getting started', 'introduction', 'what data', 'available data',
            'what information', 'what can i ask', 'examples', 'sample questions'
        ]
        
        # Check for exact matches or patterns
        for pattern in greeting_patterns + system_patterns:
            if pattern in query_lower:
                return True
        
        # Check if query is very short and likely conversational
        if len(query_lower.split()) <= 3 and any(word in query_lower for word in ['hi', 'hello', 'help', 'what', 'how']):
            return True
        
        return False
    
    def get_query_type(self, query: str) -> str:
        """
        Classify the type of conversational query.
        """
        query_lower = query.lower().strip()
        
        if any(word in query_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']):
            return 'greeting'
        elif any(phrase in query_lower for phrase in ['what do you do', 'what can you do', 'your capabilities', 'about you']):
            return 'capabilities'
        elif any(phrase in query_lower for phrase in ['help', 'how to use', 'getting started', 'introduction']):
            return 'help'
        elif any(phrase in query_lower for phrase in ['what data', 'available data', 'what information', 'data types']):
            return 'data_info'
        elif any(phrase in query_lower for phrase in ['examples', 'sample questions', 'what can i ask']):
            return 'examples'
        else:
            return 'general'
    
    async def generate_dynamic_stats(self) -> Dict:
        """
        Generate dynamic statistics from the GenAI database for conversational responses.
        """
        stats = {}
        
        if not self.db_manager.is_connected():
            return stats
        
        try:
            # Get AI Operations statistics
            stats.update(await self._get_ai_operations_stats())
            
            # Get Document Processing statistics  
            stats.update(await self._get_document_processing_stats())
            
            # Get User Activity statistics
            stats.update(await self._get_user_activity_stats())
            
            # Get System Health statistics
            stats.update(await self._get_system_health_stats())
            
        except Exception as e:
            logger.warning(f"Could not generate dynamic stats: {str(e)}")
            stats = {"status": "limited_data"}
        
        return stats
    
    async def _get_ai_operations_stats(self) -> Dict:
        """Get AI operations and cost statistics"""
        stats = {}
        
        try:
            # Cost evaluation stats
            cost_collection = self.db_manager.get_collection("costevalutionforllm")
            if cost_collection:
                total_costs = await self._get_total_ai_costs(cost_collection)
                model_count = await self._get_model_count(cost_collection)
                avg_tokens = await self._get_average_tokens(cost_collection)
                
                stats.update({
                    "total_ai_costs": total_costs,
                    "models_used": model_count,
                    "avg_tokens_per_request": avg_tokens
                })
            
            # Agent activity stats
            agent_collection = self.db_manager.get_collection("agent_activity")
            if agent_collection:
                agent_stats = await self._get_agent_performance(agent_collection)
                stats.update(agent_stats)
                
        except Exception as e:
            logger.warning(f"Could not get AI operations stats: {str(e)}")
        
        return stats
    
    async def _get_document_processing_stats(self) -> Dict:
        """Get document processing statistics"""
        stats = {}
        
        try:
            # Document extractions
            doc_collection = self.db_manager.get_collection("documentextractions")
            if doc_collection:
                doc_count = doc_collection.count_documents({})
                avg_confidence = await self._get_average_confidence(doc_collection)
                extraction_types = await self._get_extraction_types(doc_collection)
                
                stats.update({
                    "total_documents_processed": doc_count,
                    "avg_extraction_confidence": avg_confidence,
                    "extraction_types": extraction_types[:5]  # Top 5
                })
            
            # Batch processing
            batch_collection = self.db_manager.get_collection("batches")
            if batch_collection:
                batch_stats = await self._get_batch_statistics(batch_collection)
                stats.update(batch_stats)
                
            # Compliance/obligations
            obligation_collection = self.db_manager.get_collection("obligationextractions")
            if obligation_collection:
                obligation_count = obligation_collection.count_documents({})
                stats["total_obligations"] = obligation_count
                
        except Exception as e:
            logger.warning(f"Could not get document processing stats: {str(e)}")
        
        return stats
    
    async def _get_user_activity_stats(self) -> Dict:
        """Get user activity statistics"""
        stats = {}
        
        try:
            users_collection = self.db_manager.get_collection("users")
            if users_collection:
                user_count = users_collection.count_documents({})
                stats["total_users"] = user_count
            
            conversations_collection = self.db_manager.get_collection("conversations")
            if conversations_collection:
                conversation_count = conversations_collection.count_documents({})
                stats["total_conversations"] = conversation_count
                
        except Exception as e:
            logger.warning(f"Could not get user activity stats: {str(e)}")
        
        return stats
    
    async def _get_system_health_stats(self) -> Dict:
        """Get system health statistics"""
        stats = {}
        
        try:
            # Get collection counts for system overview
            collections = self.db_manager.db.list_collection_names()
            stats["total_collections"] = len(collections)
            
            # Calculate recent activity (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            recent_activity = 0
            
            for collection_name in ["documentextractions", "batches", "conversations"]:
                try:
                    collection = self.db_manager.get_collection(collection_name)
                    if collection:
                        count = collection.count_documents({
                            "createdAt": {"$gte": recent_date}
                        })
                        recent_activity += count
                except:
                    continue
            
            stats["recent_activity_7d"] = recent_activity
            
        except Exception as e:
            logger.warning(f"Could not get system health stats: {str(e)}")
        
        return stats
    
    # Helper methods for statistics gathering
    async def _get_total_ai_costs(self, collection) -> float:
        """Get total AI costs"""
        try:
            pipeline = [{"$group": {"_id": None, "total": {"$sum": "$totalCost"}}}]
            result = list(collection.aggregate(pipeline))
            if result and result[0]["total"]:
                return round(result[0]["total"], 2)
        except:
            pass
        return 0.0
    
    async def _get_model_count(self, collection) -> int:
        """Get count of different models used"""
        try:
            pipeline = [{"$group": {"_id": "$modelType"}}]
            result = list(collection.aggregate(pipeline))
            return len(result)
        except:
            return 0
    
    async def _get_average_tokens(self, collection) -> int:
        """Get average tokens per request"""
        try:
            pipeline = [{"$group": {"_id": None, "avg": {"$avg": {"$add": ["$inputTokens", "$outputTokens"]}}}}]
            result = list(collection.aggregate(pipeline))
            if result and result[0]["avg"]:
                return int(result[0]["avg"])
        except:
            return 0
    
    async def _get_agent_performance(self, collection) -> Dict:
        """Get agent performance statistics"""
        try:
            total_activities = collection.count_documents({})
            success_activities = collection.count_documents({"Outcome": "Success"})
            
            success_rate = (success_activities / total_activities * 100) if total_activities > 0 else 0
            
            return {
                "total_agent_activities": total_activities,
                "agent_success_rate": round(success_rate, 1)
            }
        except:
            return {}
    
    async def _get_average_confidence(self, collection) -> float:
        """Get average extraction confidence score"""
        try:
            pipeline = [{"$group": {"_id": None, "avg": {"$avg": "$Confidence_Score"}}}]
            result = list(collection.aggregate(pipeline))
            if result and result[0]["avg"]:
                return round(result[0]["avg"], 1)
        except:
            return 0.0
    
    async def _get_extraction_types(self, collection) -> List[str]:
        """Get most common extraction types"""
        try:
            pipeline = [
                {"$group": {"_id": "$Type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            result = list(collection.aggregate(pipeline))
            return [item["_id"] for item in result if item["_id"]]
        except:
            return []
    
    async def _get_batch_statistics(self, collection) -> Dict:
        """Get batch processing statistics"""
        try:
            total_batches = collection.count_documents({})
            completed_batches = collection.count_documents({"status": "completed"})
            
            success_rate = (completed_batches / total_batches * 100) if total_batches > 0 else 0
            
            return {
                "total_batches": total_batches,
                "batch_success_rate": round(success_rate, 1)
            }
        except:
            return {}
    
    async def generate_conversational_response(self, query: str) -> Dict:
        """
        Generate a conversational response based on the query type and dynamic GenAI data.
        """
        query_type = self.get_query_type(query)
        stats = await self.generate_dynamic_stats()
        
        if query_type == 'greeting':
            return await self._generate_greeting_response(stats)
        elif query_type == 'capabilities':
            return await self._generate_capabilities_response(stats)
        elif query_type == 'help':
            return await self._generate_help_response(stats)
        elif query_type == 'data_info':
            return await self._generate_data_info_response(stats)
        elif query_type == 'examples':
            return await self._generate_examples_response(stats)
        else:
            return await self._generate_general_response(query, stats)
    
    async def _generate_greeting_response(self, stats: Dict) -> Dict:
        """Generate a greeting response with dynamic GenAI data context"""
        
        # Create dynamic greeting based on available AI operations data
        greeting_parts = [
            "Hello! I'm your AI Operations Analytics assistant.",
            "I specialize in analyzing AI costs, document processing, and operational intelligence."
        ]
        
        if stats:
            data_summary = []
            if stats.get('total_documents_processed'):
                data_summary.append(f"{stats['total_documents_processed']:,} processed documents")
            if stats.get('total_users'):
                data_summary.append(f"{stats['total_users']} active users")
            if stats.get('total_batches'):
                data_summary.append(f"{stats['total_batches']} processing batches")
            
            if data_summary:
                greeting_parts.append(f"I have access to {', '.join(data_summary)} in your AI operations database.")
            
            if stats.get('total_ai_costs'):
                greeting_parts.append(f"Your total AI operational costs are ${stats['total_ai_costs']:,.2f}.")
            
            if stats.get('avg_extraction_confidence'):
                greeting_parts.append(f"Your document extraction system maintains {stats['avg_extraction_confidence']}% average confidence.")
        
        greeting_parts.append("What would you like to know about your AI operations?")
        
        return {
            "summary": " ".join(greeting_parts),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_capabilities_response(self, stats: Dict) -> Dict:
        """Generate response about GenAI system capabilities"""
        
        capabilities = [
            "I'm an AI-powered conversational analytics assistant specialized in AI operations that can help you:",
            "• Analyze AI costs, token usage, and model performance",
            "• Track document processing metrics and extraction confidence", 
            "• Monitor compliance obligations and legal risk assessment",
            "• Review agent performance and operational efficiency",
            "• Explore user activity and system health metrics",
            "• Generate visualizations and insights for operational data"
        ]
        
        if stats:
            capabilities.append(f"\nI'm currently connected to your AI operations database with:")
            if stats.get('total_documents_processed'):
                capabilities.append(f"• {stats['total_documents_processed']:,} document processing records")
            if stats.get('total_ai_costs'):
                capabilities.append(f"• ${stats['total_ai_costs']:,.2f} in tracked AI operational costs")
            if stats.get('total_obligations'):
                capabilities.append(f"• {stats['total_obligations']} compliance obligations monitored")
            if stats.get('models_used'):
                capabilities.append(f"• {stats['models_used']} different AI models in use")
            
            if stats.get('extraction_types'):
                types = ', '.join(stats['extraction_types'][:3])
                capabilities.append(f"• Document types include: {types}")
        
        capabilities.append("\nJust ask me questions in natural language about your AI operations, and I'll provide insights with visualizations!")
        
        return {
            "summary": "\n".join(capabilities),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_help_response(self, stats: Dict) -> Dict:
        """Generate help response with GenAI-specific examples"""
        
        help_text = [
            "Here's how to use the AI Operations Analytics system:",
            "",
            "1. **Ask Natural Questions**: Simply type your question in plain English",
            "2. **Get AI Insights**: I'll analyze your operational data and provide summaries",
            "3. **View Visualizations**: Charts and graphs will help you understand patterns",
            "4. **Follow Suggestions**: Use the suggested follow-up questions for deeper analysis",
            "",
            "**AI Operations Examples:**",
            "• 'What's our AI spending this month?'",
            "• 'Show me document extraction confidence scores'",
            "• 'Which compliance obligations need attention?'",
            "• 'How are our AI agents performing?'",
            "• 'Compare processing costs between document types'",
            "",
            "**Advanced Analysis:**",
            "• 'Show me cost trends over the last 6 months'",
            "• 'Which users generate the highest AI costs?'",
            "• 'What's our batch processing success rate?'",
            "• 'Find documents with low confidence scores'"
        ]
        
        if stats:
            help_text.append(f"\n**Your Current Data Overview:**")
            if stats.get('total_documents_processed'):
                help_text.append(f"• {stats['total_documents_processed']:,} documents available for analysis")
            if stats.get('recent_activity_7d'):
                help_text.append(f"• {stats['recent_activity_7d']} recent activities in the last 7 days")
            if stats.get('total_collections'):
                help_text.append(f"• {stats['total_collections']} data collections for comprehensive analysis")
        
        return {
            "summary": "\n".join(help_text),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_data_info_response(self, stats: Dict) -> Dict:
        """Generate response about available GenAI data"""
        
        data_info = [
            "Your AI Operations database contains comprehensive operational intelligence data:",
            "",
            "**🤖 AI Operations Data:**",
            "• Cost tracking and token usage analytics",
            "• Model performance and efficiency metrics",
            "• Processing time and resource utilization",
            "",
            "**📄 Document Intelligence:**",
            "• Document extraction results and confidence scores",
            "• Content analysis and classification data",
            "• Processing batch information and success rates",
            "",
            "**⚖️ Compliance & Legal:**",
            "• Legal obligation extractions and risk assessment",
            "• Compliance tracking and regulatory monitoring",
            "• Contract analysis and obligation mapping",
            "",
            "**👥 User & System Data:**",
            "• User activity and engagement metrics",
            "• System health and performance indicators",
            "• Conversation history and interaction patterns"
        ]
        
        if stats:
            data_info.append(f"\n**Current Data Volume:**")
            if stats.get('total_documents_processed'):
                data_info.append(f"• {stats['total_documents_processed']:,} processed documents")
            if stats.get('total_ai_costs'):
                data_info.append(f"• ${stats['total_ai_costs']:,.2f} in tracked operational costs")
            if stats.get('total_users'):
                data_info.append(f"• {stats['total_users']} active users")
            if stats.get('total_batches'):
                data_info.append(f"• {stats['total_batches']} processing batches")
            if stats.get('total_obligations'):
                data_info.append(f"• {stats['total_obligations']} compliance obligations")
        
        return {
            "summary": "\n".join(data_info),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_examples_response(self, stats: Dict) -> Dict:
        """Generate response with GenAI-specific example questions"""
        
        examples = [
            "Here are some example questions you can ask about your AI operations:",
            "",
            "**💰 Cost & Performance Analysis:**",
            "• 'What's our AI spending this month?'",
            "• 'Which AI models are most cost-effective?'",
            "• 'Show me token usage patterns by user'",
            "• 'Compare processing costs between document types'",
            "",
            "**📊 Document Processing:**",
            "• 'How many documents did we process today?'",
            "• 'What's our extraction success rate?'",
            "• 'Show me documents with low confidence scores'",
            "• 'Which document types take longest to process?'",
            "",
            "**⚖️ Compliance & Risk:**",
            "• 'What are our most critical compliance obligations?'",
            "• 'Show me high-risk legal obligations'",
            "• 'Which contracts have data confidentiality requirements?'",
            "• 'Track compliance obligation trends over time'",
            "",
            "**🤖 Agent & System Performance:**",
            "• 'How are our AI agents performing?'",
            "• 'Show me batch processing success rates'",
            "• 'Which users are most active in the system?'",
            "• 'What's our overall system health status?'"
        ]
        
        if stats:
            examples.append(f"\n**Personalized Suggestions Based on Your Data:**")
            if stats.get('avg_extraction_confidence') and stats['avg_extraction_confidence'] < 85:
                examples.append(f"• 'Why is our extraction confidence at {stats['avg_extraction_confidence']}%?'")
            if stats.get('total_ai_costs') and stats['total_ai_costs'] > 1000:
                examples.append(f"• 'Break down our ${stats['total_ai_costs']:,.2f} in AI costs by category'")
            if stats.get('batch_success_rate') and stats['batch_success_rate'] < 95:
                examples.append(f"• 'What's causing our {stats['batch_success_rate']}% batch success rate?'")
        
        return {
            "summary": "\n".join(examples),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_general_response(self, query: str, stats: Dict) -> Dict:
        """Generate a general response for unclassified queries"""
        
        response = [
            f"I understand you're asking: '{query}'",
            "",
            "I specialize in AI operations analytics and can help you with:",
            "",
            "🤖 **AI Cost Analysis** - spending, efficiency, ROI",
            "📄 **Document Processing** - extraction results, confidence scores",
            "⚖️ **Compliance Tracking** - legal obligations, risk assessment", 
            "👥 **User Analytics** - activity patterns, system usage",
            "📊 **Operational Intelligence** - system health, performance metrics",
            "",
            "Try asking more specific questions about your AI operations data!"
        ]
        
        return {
            "summary": "\n".join(response),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    def _get_dynamic_suggestions(self, stats: Dict) -> List[str]:
        """Generate dynamic suggestions based on GenAI operational data"""
        suggestions = [
            "What's our AI spending this month?",
            "Show me document extraction confidence scores",
            "Which compliance obligations need attention?",
            "How are our AI agents performing?"
        ]
        
        # Add data-driven suggestions
        if stats:
            if stats.get('total_ai_costs', 0) > 500:
                suggestions.insert(0, "Break down our AI costs by model type")
            
            if stats.get('avg_extraction_confidence', 100) < 90:
                suggestions.insert(1, "Why are our confidence scores low?")
            
            if stats.get('recent_activity_7d', 0) > 100:
                suggestions.append("Show me this week's processing activity")
            
            if stats.get('total_obligations', 0) > 50:
                suggestions.append("What are our highest risk obligations?")
            
            if stats.get('agent_success_rate', 100) < 95:
                suggestions.insert(2, "What's affecting our agent performance?")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _get_genai_context_suggestions(self, stats: Dict) -> List[str]:
        """Get contextual suggestions based on GenAI data patterns"""
        suggestions = []
        
        if not stats:
            return [
                "Show me system overview",
                "What data do we have available?",
                "Help me get started with AI analytics"
            ]
        
        # Cost-based suggestions
        if stats.get('total_ai_costs', 0) > 0:
            suggestions.append("Compare AI costs by time period")
            if stats.get('models_used', 0) > 1:
                suggestions.append("Which AI model is most cost-effective?")
        
        # Document processing suggestions
        if stats.get('total_documents_processed', 0) > 0:
            suggestions.append("Show me document processing trends")
            if stats.get('avg_extraction_confidence', 100) < 95:
                suggestions.append("Improve document extraction confidence")
        
        # Compliance suggestions
        if stats.get('total_obligations', 0) > 0:
            suggestions.append("Review high-priority compliance items")
            suggestions.append("Track obligation resolution progress")
        
        # User activity suggestions
        if stats.get('total_users', 0) > 1:
            suggestions.append("Who are our most active users?")
        
        # System health suggestions
        if stats.get('batch_success_rate', 100) < 98:
            suggestions.append("Investigate batch processing issues")
        
        return suggestions[:6]  # Return top 6 contextual suggestions