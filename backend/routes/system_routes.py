from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import asyncio
import logging

logger = logging.getLogger(__name__)

# Create blueprint
system_bp = Blueprint('system', __name__, url_prefix='/api')

def init_system_routes(analytics_service, memory_service, chat_service, database):
    """Initialize system routes with services"""
    
    @system_bp.route('/system/test', methods=['POST'])
    def test_system_components():
        """Test all system components including chat"""
        try:
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "tests": {}
            }
            
            # Test database
            if database is not None:
                try:
                    count = database.costevalutionforllm.count_documents({})
                    test_results["tests"]["database"] = {
                        "status": "pass",
                        "details": f"AI cost collection has {count} documents"
                    }
                except Exception as e:
                    test_results["tests"]["database"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            else:
                test_results["tests"]["database"] = {
                    "status": "fail",
                    "details": "Database not available"
                }
            
            # Test chat system
            if database is not None and chat_service:
                try:
                    # Test creating a chat session
                    test_chat_id = chat_service.create_new_chat_session("Test Chat Session")
                    if test_chat_id:
                        # Test saving a message
                        test_message = {
                            'type': 'user',
                            'content': 'Test message for system validation',
                            'timestamp': datetime.now(timezone.utc)
                        }
                        message_saved = chat_service.save_message_to_chat(test_chat_id, test_message)
                        
                        # Test retrieving the chat
                        retrieved_chat = chat_service.get_chat_session(test_chat_id)
                        
                        if message_saved and retrieved_chat:
                            test_results["tests"]["chat_system"] = {
                                "status": "pass",
                                "details": f"Chat system functional - created chat {test_chat_id}"
                            }
                            # Clean up test chat
                            chat_service.delete_chat_session(test_chat_id, soft_delete=False)
                        else:
                            test_results["tests"]["chat_system"] = {
                                "status": "fail",
                                "details": "Chat message handling failed"
                            }
                    else:
                        test_results["tests"]["chat_system"] = {
                            "status": "fail",
                            "details": "Failed to create test chat session"
                        }
                except Exception as e:
                    test_results["tests"]["chat_system"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            else:
                test_results["tests"]["chat_system"] = {
                    "status": "fail",
                    "details": "Database or chat service not available"
                }
            
            # Test simple processor
            if hasattr(analytics_service, 'simple_processor') and analytics_service.simple_processor:
                try:
                    result = analytics_service.simple_processor.process_question("Show me what data is available")
                    test_results["tests"]["simple_processor"] = {
                        "status": "pass" if result.get("success") else "fail",
                        "details": result.get("summary", result.get("error"))
                    }
                except Exception as e:
                    test_results["tests"]["simple_processor"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            elif hasattr(analytics_service, 'process_question'):
                try:
                    result = analytics_service.process_question("Show me what data is available")
                    test_results["tests"]["simple_processor"] = {
                        "status": "pass" if result.get("success") else "fail",
                        "details": result.get("summary", result.get("error"))
                    }
                except Exception as e:
                    test_results["tests"]["simple_processor"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            else:
                test_results["tests"]["simple_processor"] = {
                    "status": "fail",
                    "details": "Simple processor not available"
                }
            
            # Test Gemini AI
            if hasattr(analytics_service, 'gemini_client') and analytics_service.gemini_client:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        # Test basic query generation
                        result = loop.run_until_complete(
                            analytics_service.gemini_client.generate_query(
                                "Test query", 
                                {"collections": {"costevalutionforllm": {"fields": ["modelType", "totalCost"]}}}
                            )
                        )
                        test_results["tests"]["gemini_ai"] = {
                            "status": "pass" if result.get("success") else "fail",
                            "details": "Query generation test completed"
                        }
                    finally:
                        loop.close()
                        
                except Exception as e:
                    test_results["tests"]["gemini_ai"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            else:
                test_results["tests"]["gemini_ai"] = {
                    "status": "fail",
                    "details": "Gemini AI not available"
                }
            
            # Test two-stage processor
            if hasattr(analytics_service, 'process_question') and asyncio.iscoroutinefunction(analytics_service.process_question):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            analytics_service.process_question("What are our AI operational costs this month?")
                        )
                        test_results["tests"]["two_stage_processor"] = {
                            "status": "pass" if result.get("success") else "fail",
                            "details": f"Test query processed with {result.get('query_source', 'unknown')} source"
                        }
                    finally:
                        loop.close()
                        
                except Exception as e:
                    test_results["tests"]["two_stage_processor"] = {
                        "status": "fail",
                        "details": str(e)
                    }
            else:
                test_results["tests"]["two_stage_processor"] = {
                    "status": "fail",
                    "details": "Two-stage processor not available"
                }
            
            # Calculate overall status
            passed_tests = sum(1 for test in test_results["tests"].values() if test["status"] == "pass")
            total_tests = len(test_results["tests"])
            
            test_results["overall"] = {
                "status": "healthy" if passed_tests == total_tests else "degraded" if passed_tests > 0 else "unhealthy",
                "passed": passed_tests,
                "total": total_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%"
            }
            
            return jsonify(test_results)
            
        except Exception as e:
            return jsonify({
                "error": "System test failed",
                "details": str(e)
            }), 500

    return system_bp