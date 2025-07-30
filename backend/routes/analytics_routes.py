from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api')

def init_analytics_routes(analytics_service, memory_service, chat_service, database):
    """Initialize analytics routes with services"""
    
    @analytics_bp.route('/query', methods=['POST'])
    def process_query():
        """Enhanced query processing with Memory RAG integration"""
        try:
            data = request.get_json()
            user_question = data.get('question', '').strip()
            chat_id = data.get('chat_id')
            
            if not user_question:
                return jsonify({"error": "Question is required"}), 400
            
            # Determine if we should use memory enhancement
            use_memory = chat_id and memory_service and memory_service.is_available()
            
            logger.info(f"🔍 Processing question: '{user_question}'" + 
                       (f" (chat: {chat_id}, memory: {use_memory})" if chat_id else " (no chat)"))
            
            start_time = time.time()
            result = None
            
            # Save user message to chat if chat_id provided
            if chat_id and chat_service:
                user_message = {
                    'type': 'user',
                    'content': user_question,
                    'timestamp': datetime.now(timezone.utc)
                }
                chat_service.save_message_to_chat(chat_id, user_message)
            
            # Process with Memory RAG if available and chat_id provided
            if use_memory:
                logger.info("🧠 Using Memory-Enhanced Processing")
                
                # Use asyncio to run the async memory processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        memory_service.process_with_memory(user_question, chat_id)
                    )
                    result['processing_mode'] = 'memory_enhanced'
                finally:
                    loop.close()
                    
            else:
                # Fallback to regular processing
                logger.info("🔄 Using Standard Processing")
                
                # Check if we have a two-stage processor
                if hasattr(analytics_service, 'process_question') and asyncio.iscoroutinefunction(analytics_service.process_question):
                    # Async two-stage processor
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(analytics_service.process_question(user_question))
                        result['processing_mode'] = 'two_stage'
                    finally:
                        loop.close()
                elif hasattr(analytics_service, 'process_question'):
                    # Sync simple processor
                    result = analytics_service.process_question(user_question)
                    result['processing_mode'] = 'simple'
                else:
                    return jsonify({"error": "No processors available"}), 503
            
            execution_time = time.time() - start_time
            result['execution_time'] = round(execution_time, 3)
            
            # Save AI response to chat
            if chat_id and chat_service and result.get('success'):
                ai_message = {
                    'type': 'assistant',
                    'content': result.get('summary', 'Analysis completed'),
                    'chart_data': result.get('chart_data'),
                    'insights': result.get('insights'),
                    'recommendations': result.get('recommendations'),
                    'memory_context': result.get('memory_context'),
                    'processing_mode': result.get('processing_mode'),
                    'timestamp': datetime.now(timezone.utc)
                }
                chat_service.save_message_to_chat(chat_id, ai_message)
            
            logger.info(f"✅ Query processed successfully in {execution_time:.3f}s")
            return jsonify(result)
            
        except Exception as e:
            error_msg = f"Query processing failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "success": False,
                "error": error_msg,
                "processing_mode": "error"
            }), 500

    @analytics_bp.route('/health', methods=['GET'])
    def health_check():
        """Enhanced health check for GenAI operations"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "disconnected",
                "ai_system": "unavailable",
                "collections": {},
                "domain": "AI Operations & Document Intelligence"
            }
            
            # Database health check
            if database is not None:
                health_status["database"] = "connected"
                
                # Check GenAI collections instead of old ones
                genai_collections = [
                    "costevalutionforllm", "documentextractions", "obligationextractions",
                    "agent_activity", "batches", "users", "conversations"
                ]
                
                collection_status = {}
                total_documents = 0
                
                for collection_name in genai_collections:
                    try:
                        collection = database[collection_name]
                        count = collection.count_documents({})
                        collection_status[collection_name] = {
                            "status": "available",
                            "document_count": count
                        }
                        total_documents += count
                    except Exception as e:
                        collection_status[collection_name] = {
                            "status": "error",
                            "error": str(e)
                        }
                
                health_status["collections"] = collection_status
                health_status["total_documents"] = total_documents
            
            # AI system health check
            if hasattr(analytics_service, 'gemini_client') and analytics_service.gemini_client:
                health_status["ai_system"] = "available"
                health_status["processors"] = {
                    "two_stage": hasattr(analytics_service, 'process_question'),
                    "simple": hasattr(analytics_service, 'simple_processor'),
                    "memory_enhanced": memory_service and memory_service.is_available()
                }
            
            return jsonify(health_status)
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @analytics_bp.route('/examples', methods=['GET'])
    def get_example_questions():
        """Get example questions for GenAI operations analytics"""
        
        examples = {
            "ai_operations": {
                "description": "AI cost analysis and performance optimization",
                "examples": [
                    "What's our AI spending this month?",
                    "Which AI models are most cost-effective?",
                    "Show me token usage patterns by user",
                    "Compare processing costs between document types",
                    "What's our average cost per document extraction?"
                ]
            },
            "document_processing": {
                "description": "Document extraction and processing analytics",
                "examples": [
                    "How many documents did we process today?",
                    "What's our extraction success rate?",
                    "Show me documents with low confidence scores",
                    "Which document types take longest to process?",
                    "What are our confidence score distributions?"
                ]
            },
            "compliance_analytics": {
                "description": "Legal compliance and risk assessment",
                "examples": [
                    "What are our most critical compliance obligations?",
                    "Show me high-risk compliance items",
                    "Which contracts have data confidentiality requirements?",
                    "Track compliance obligation trends over time",
                    "List all insurance-related obligations"
                ]
            },
            "operational_intelligence": {
                "description": "System performance and user analytics",
                "examples": [
                    "How are our AI agents performing?",
                    "Show me batch processing success rates",
                    "Which users are most active in the system?",
                    "What's our overall system health status?",
                    "Compare agent performance across document types"
                ]
            },
            "advanced_analytics": {
                "description": "Cross-collection complex analysis",
                "examples": [
                    "Show AI costs for documents that failed compliance",
                    "Which prompts are most effective for legal documents?",
                    "Compare extraction confidence vs processing costs",
                    "Track document processing pipeline success rates",
                    "Show ROI analysis for different AI models"
                ]
            },
            "chat_integration_examples": {
                "description": "Examples showing how to use chat functionality",
                "create_new_chat": "POST /api/chats with {\"title\": \"AI Cost Analysis\", \"category\": \"operations\"}",
                "query_with_chat": "POST /api/query with {\"question\": \"Show AI spending trends\", \"chat_id\": \"chat_123\"}",
                "get_chat_history": "GET /api/chats/chat_123",
                "list_all_chats": "GET /api/chats?limit=20&status=active"
            },
            "system_capabilities": {
                "ai_features": [
                    "Natural language understanding for AI operations",
                    "Intelligent chart type selection for operational data",
                    "Context-aware insights generation for cost optimization",
                    "Automated recommendations for system improvements",
                    "Chat session persistence with operational context",
                    "Memory-enhanced conversations for better follow-ups"
                ],
                "fallback_features": [
                    "Pattern-based query processing for GenAI collections",
                    "Guaranteed response for common operational questions",
                    "Fast processing times for system health queries",
                    "Reliable basic analytics for cost and performance data",
                    "Chat session management for operational discussions",
                    "Real-time message saving for audit trails"
                ]
            }
        }
        
        return jsonify(examples)

    @analytics_bp.route('/debug/collections', methods=['GET'])
    def debug_collections():
        """Debug endpoint with enhanced information for GenAI collections"""
        if database is None:
            return jsonify({"error": "Database not available"}), 503
        
        try:
            collections_info = {}
            collection_names = database.list_collection_names()
            
            for collection_name in collection_names:
                try:
                    collection = database[collection_name]
                    count = collection.count_documents({})
                    sample = collection.find_one() if count > 0 else None
                    
                    # Convert ObjectId to string for JSON serialization - FIXED
                    if sample and '_id' in sample:
                        sample['_id'] = str(sample['_id'])
                    
                    # Clean all fields for JSON serialization - NEW FIX
                    if sample:
                        cleaned_sample = {}
                        for key, value in sample.items():
                            if hasattr(value, 'isoformat'):  # datetime
                                cleaned_sample[key] = value.isoformat()
                            elif hasattr(value, '__str__') and hasattr(value, 'hex'):  # ObjectId
                                cleaned_sample[key] = str(value)
                            elif isinstance(value, dict):
                                # Recursively clean nested objects
                                cleaned_value = {}
                                for k, v in value.items():
                                    if hasattr(v, 'isoformat'):
                                        cleaned_value[k] = v.isoformat()
                                    elif hasattr(v, '__str__') and hasattr(v, 'hex'):
                                        cleaned_value[k] = str(v)
                                    else:
                                        cleaned_value[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                                cleaned_sample[key] = cleaned_value
                            elif isinstance(value, list):
                                # Clean list items
                                cleaned_list = []
                                for item in value[:3]:  # Limit to first 3 items
                                    if hasattr(item, 'isoformat'):
                                        cleaned_list.append(item.isoformat())
                                    elif hasattr(item, '__str__') and hasattr(item, 'hex'):
                                        cleaned_list.append(str(item))
                                    else:
                                        cleaned_list.append(str(item) if not isinstance(item, (str, int, float, bool, type(None))) else item)
                                cleaned_sample[key] = cleaned_list
                            else:
                                # Convert everything else to string if it's not a basic type
                                if isinstance(value, (str, int, float, bool, type(None))):
                                    cleaned_sample[key] = value
                                else:
                                    cleaned_sample[key] = str(value)
                        
                        sample = cleaned_sample
                    
                    # Get field statistics
                    field_stats = {}
                    if sample:
                        for field, value in sample.items():
                            field_stats[field] = {
                                "type": type(value).__name__,
                                "sample_value": str(value)[:100]  # Truncate long values
                            }
                    
                    # Determine if collection is AI operations compatible
                    ai_compatible = collection_name in [
                        "costevalutionforllm", "documentextractions", "obligationextractions",
                        "agent_activity", "batches", "users", "conversations", "prompts",
                        "files", "compliances", "obligationmappings", "documentmappings"
                    ]
                    
                    collections_info[collection_name] = {
                        "document_count": count,
                        "sample_fields": list(sample.keys()) if sample else [],
                        "field_statistics": field_stats,
                        "sample_document": sample,
                        "ai_compatible": ai_compatible,
                        "is_chat_collection": collection_name in ["conversations", "chat_sessions"],
                        "domain_relevance": "high" if ai_compatible else "low"
                    }
                except Exception as e:
                    collections_info[collection_name] = {
                        "error": str(e),
                        "document_count": -1,
                        "ai_compatible": False,
                        "is_chat_collection": False
                    }
            
            return jsonify({
                "database_name": database.name,
                "domain": "AI Operations & Document Intelligence",
                "total_collections": len(collections_info),
                "collection_names": collection_names,
                "collections": collections_info,
                "ai_system_status": {
                    "gemini_available": hasattr(analytics_service, 'gemini_client') and analytics_service.gemini_client,
                    "two_stage_processor": hasattr(analytics_service, 'process_question'),
                    "simple_processor": hasattr(analytics_service, 'simple_processor'),
                    "chat_system": database is not None,
                    "memory_rag": memory_service and memory_service.is_available()
                }
            })
            
        except Exception as e:
            logger.error(f"Debug collections failed: {str(e)}")
            return jsonify({"error": f"Debug failed: {str(e)}"}), 500

    return analytics_bp