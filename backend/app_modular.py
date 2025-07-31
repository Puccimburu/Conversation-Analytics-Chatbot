# backend/app_modular.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime, timezone
import pymongo
import time

# Import modular components
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor
from utils.chat_manager import ensure_chat_indexes, create_new_chat_session, save_message_to_chat
from utils.enhanced_gemini_client import BulletproofGeminiClient
from config import Config, DATABASE_SCHEMA

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genai')

print("=" * 60)
print("PERFECTED AI ANALYTICS - MODULAR ARCHITECTURE")
print("=" * 60)
print(f"Database: {MONGODB_URI}")
print(f"API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Database Connection
db = None
mongodb_available = False

try:
    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client.genai
    client.admin.command('ping')
    mongodb_available = True
    logger.info("MongoDB connected successfully to GenAI database")
    print("MongoDB connected successfully to GenAI database")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    print(f"MongoDB Error: {e}")
    mongodb_available = False

# Initialize chat collection indexes on startup
if mongodb_available:
    ensure_chat_indexes(db)

# ============================================================================
# SIMPLE QUERY PROCESSOR (Extracted from original app.py)
# ============================================================================

class CompleteSimpleQueryProcessor:
    """Complete simple processor with all methods"""
    
    def __init__(self, database):
        self.db = database
        
    def process_question(self, user_question: str) -> dict:
        """Process questions with pattern matching"""
        question_lower = user_question.lower()
        
        try:
            # AI cost analysis
            if any(word in question_lower for word in ["cost", "spending", "ai cost", "model cost"]) or ("compare" in question_lower and any(word in question_lower for word in ["ai", "model", "cost"])):
                return self._ai_cost_analysis()
            
            # Document confidence analysis
            elif any(word in question_lower for word in ["confidence", "document", "extraction"]) and any(word in question_lower for word in ["top", "best", "analysis"]):
                return self._document_confidence_analysis()
            
            # Compliance obligations
            elif any(word in question_lower for word in ["compliance", "obligation", "legal"]) and any(word in question_lower for word in ["category", "type", "analysis"]):
                return self._compliance_obligations()
            
            # Agent performance
            elif any(word in question_lower for word in ["agent", "performance", "activity"]):
                return self._agent_performance()
            
            # Default: show available data
            else:
                return self._show_available_data()
                
        except Exception as e:
            logger.error(f"Simple processor error: {e}")
            return {
                "success": False,
                "error": f"Query failed: {str(e)}",
                "suggestions": ["Try a different question", "Check your data"]
            }
    
    def _ai_cost_analysis(self):
        """Analyze AI operational costs by model type"""
        pipeline = [
            {"$group": {
                "_id": "$modelType",
                "total_cost": {"$sum": "$totalCost"},
                "total_tokens": {"$sum": {"$add": ["$inputTokens", "$outputTokens"]}},
                "request_count": {"$sum": 1}
            }},
            {"$sort": {"total_cost": -1}}
        ]
        
        results = list(self.db.costevalutionforllm.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No AI cost data found"}
        
        # Create summary
        total_cost = sum(r['total_cost'] for r in results)
        summary_parts = []
        
        for result in results:
            model_type = result['_id']
            cost = result['total_cost']
            tokens = result['total_tokens']
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            
            summary_parts.append(f"{model_type}: ${cost:,.2f} ({percentage:.1f}%) from {tokens:,} tokens")
        
        summary = "AI cost analysis: " + " | ".join(summary_parts)
        
        # Chart configuration
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "AI Cost ($)",
                    "data": [r['total_cost'] for r in results],
                    "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
                    "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "AI Model Cost Analysis"},
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Cost ($)"}},
                    "x": {"title": {"display": True, "text": "AI Model"}}
                }
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total models analyzed: {len(results)}", f"Total cost: ${total_cost:,.2f}"],
            "recommendations": ["Focus on cost optimization", "Analyze token efficiency"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _document_confidence_analysis(self):
        """Analyze document extraction confidence scores"""
        pipeline = [
            {"$group": {
                "_id": "$Type",
                "avg_confidence": {"$avg": "$Confidence_Score"},
                "total_extractions": {"$sum": 1}
            }},
            {"$sort": {"avg_confidence": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.documentextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No document extraction data found"}
        
        summary = f"Top {len(results)} document types by confidence"
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Avg Confidence",
                    "data": [r['avg_confidence'] for r in results],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Document Extraction Confidence"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total document types: {len(results)}", f"Highest confidence: {results[0]['_id']}"],
            "recommendations": ["Focus on high-confidence extractions", "Improve low-confidence patterns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _compliance_obligations(self):
        """Compliance obligations breakdown by type"""
        pipeline = [
            {"$group": {
                "_id": "$obligationType",
                "total_obligations": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"}
            }},
            {"$sort": {"total_obligations": -1}}
        ]
        
        results = list(self.db.obligationextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No compliance obligation data found"}
        
        total_obligations = sum(r['total_obligations'] for r in results)
        summary = f"Compliance obligations across {len(results)} types"
        
        colors = [
            "rgba(59, 130, 246, 0.8)",   # Blue
            "rgba(16, 185, 129, 0.8)",   # Green
            "rgba(245, 158, 11, 0.8)",   # Yellow
            "rgba(239, 68, 68, 0.8)",    # Red
            "rgba(147, 51, 234, 0.8)",   # Purple
            "rgba(236, 72, 153, 0.8)"    # Pink
        ]
        
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['total_obligations'] for r in results],
                    "backgroundColor": colors[:len(results)]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Compliance Obligations by Type"},
                    "legend": {"display": True, "position": "bottom"}
                }
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total categories: {len(results)}", f"Leading category: {results[0]['_id']}"],
            "recommendations": ["Review compliance requirements", "Address high-risk categories"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _agent_performance(self):
        """Agent performance analysis"""
        pipeline = [
            {"$group": {
                "_id": "$Agent",
                "success_count": {"$sum": {"$cond": [{"$eq": ["$Outcome", "Success"]}, 1, 0]}},
                "total_activities": {"$sum": 1},
                "avg_duration": {"$avg": "$duration"}
            }},
            {"$sort": {"success_count": -1}}
        ]
        
        results = list(self.db.agent_activity.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No agent performance data found"}
        
        summary = "Agent performance analysis"
        
        chart_config = {
            "type": "pie",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['success_count'] for r in results],
                    "backgroundColor": [
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(16, 185, 129, 0.8)",
                        "rgba(245, 158, 11, 0.8)"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Agent Success Distribution"}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total agents: {len(results)}", f"Top agent: {results[0]['_id']}"],
            "recommendations": ["Optimize agent performance", "Focus on successful patterns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _show_available_data(self):
        """Show what data is available"""
        try:
            collections_info = []
            for collection_name in ["costevalutionforllm", "documentextractions", "obligationextractions", "agent_activity", "batches", "users", "conversations"]:
                try:
                    count = self.db[collection_name].count_documents({})
                    collections_info.append(f"{collection_name}: {count} records")
                except:
                    collections_info.append(f"{collection_name}: 0 records")
            
            summary = f"Available data: {', '.join(collections_info)}"
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'What are our AI operational costs?'",
                    "Try: 'Show me document extraction confidence'",
                    "Try: 'Which compliance obligations need attention?'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {"success": False, "error": f"Could not retrieve data info: {str(e)}"}

# ============================================================================
# PERFECTED TWO-STAGE PROCESSOR (Extracted from original app.py)
# ============================================================================

class PerfectedTwoStageProcessor:
    """Perfected processor that prioritizes Gemini AI"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor
        self.db = database
        # Import GenAI schema from config
        self.schema_info = DATABASE_SCHEMA.copy()
    
    async def process_question(self, user_question: str) -> dict:
        """Enhanced two-stage processing with Gemini priority"""
        start_time = datetime.now()
        
        # STAGE 1: Query Generation with Gemini (Priority)
        logger.info(f"🚀 Starting perfected two-stage processing: '{user_question}'")
        
        stage_1_result = await self.gemini_client.generate_query(user_question, self.schema_info)
        
        if stage_1_result.success:
            # Execute the Gemini-generated query
            query_data = stage_1_result.data
            raw_results = await self._execute_database_query(query_data)
            
            if raw_results is not None and len(raw_results) > 0:
                # STAGE 2: Visualization Generation with Gemini
                stage_2_result = await self.gemini_client.generate_visualization(
                    user_question, raw_results, query_data
                )
                
                if stage_2_result.success:
                    # Complete success with both Gemini stages
                    viz_data = stage_2_result.data
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"✅ Perfected two-stage Gemini processing successful: {len(raw_results)} results in {execution_time:.2f}s")
                    
                    return {
                        "success": True,
                        "summary": viz_data.get("summary", "AI-powered analysis completed successfully"),
                        "chart_data": viz_data.get("chart_config", {}),
                        "insights": viz_data.get("insights", ["AI-generated insights"]),
                        "recommendations": viz_data.get("recommendations", ["AI-powered recommendations"]),
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_two_stage_perfect",
                        "ai_powered": True
                    }
                else:
                    # Stage 2 failed, use simple processor fallback
                    logger.warning("Stage 2 failed, falling back to simple processor")
                    fallback_result = self.simple_processor.process_question(user_question)
                    if fallback_result.get("success"):
                        fallback_result["query_source"] = "gemini_stage1_simple_fallback"
                        return fallback_result
            else:
                # Gemini query returned no results, try simple processor
                logger.warning("Gemini query returned no results, trying simple processor")
                simple_result = self.simple_processor.process_question(user_question)
                if simple_result.get("success"):
                    simple_result["query_source"] = "gemini_failed_simple_success"
                    simple_result["ai_powered"] = False
                    return simple_result
        
        # Complete fallback to simple processor
        logger.warning("Using simple processor as last resort")
        simple_result = self.simple_processor.process_question(user_question)
        
        if simple_result.get("success"):
            simple_result["query_source"] = "simple_last_resort"
            simple_result["ai_powered"] = False
            return simple_result
        else:
            return {
                "success": False,
                "error": "Unable to process your question",
                "suggestions": [
                    "Try a simpler question",
                    "Ask about AI costs, document confidence, or compliance obligations"
                ]
            }
    
    async def _execute_database_query(self, query_data: dict):
        """Execute MongoDB query with enhanced error handling"""
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return None
            
            collection = self.db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            # Convert ObjectIds to strings for JSON serialization
            cleaned_results = []
            for result in results:
                cleaned_result = self._clean_mongodb_result(result)
                cleaned_results.append(cleaned_result)
            
            logger.info(f"Database query executed: {len(cleaned_results)} results from {collection_name}")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return None
    
    def _clean_mongodb_result(self, result: dict) -> dict:
        """Clean MongoDB result by converting ObjectIds to strings"""
        from bson import ObjectId
        cleaned = {}
        
        for key, value in result.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_mongodb_result(value)
            else:
                cleaned[key] = value
        
        return cleaned

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

# Initialize components
gemini_client = None
simple_processor = None
two_stage_processor = None
memory_manager = None
memory_enhanced_processor = None
gemini_available = False

# Initialize Gemini
if GOOGLE_API_KEY and GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        gemini_client = BulletproofGeminiClient(GOOGLE_API_KEY)
        gemini_available = True  # Assuming the imported class handles availability check
        logger.info("Bulletproof Gemini client initialized")
        print("Bulletproof Gemini client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        print(f"Gemini Error: {e}")
        gemini_available = False
else:
    logger.warning("No Google API key provided")
    print("No Google API key provided")
    gemini_available = False

# Initialize processors
if db is not None:
    simple_processor = CompleteSimpleQueryProcessor(db)
    
    if gemini_available and gemini_client:
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("Perfected two-stage processor initialized")
        print("Perfected two-stage processor initialized")
    else:
        logger.info("Complete simple processor ready (Gemini not available)")
        print("Complete simple processor ready (Gemini not available)")

# Initialize Memory RAG system
if mongodb_available and db is not None:
    try:
        memory_manager = MemoryRAGManager(db, gemini_client)
        logger.info("Memory RAG Manager initialized")
        print("Memory RAG Manager initialized")
        
        # Create memory-enhanced processor
        if two_stage_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                two_stage_processor, 
                memory_manager, 
                gemini_client
            )
            logger.info("✅ Memory-Enhanced Two-Stage Processor ready")
            print("✅ Memory-Enhanced Two-Stage Processor ready")
        elif simple_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                simple_processor, 
                memory_manager, 
                gemini_client
            )
            logger.info("✅ Memory-Enhanced Simple Processor ready")
            print("✅ Memory-Enhanced Simple Processor ready")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Memory RAG: {e}")
        print(f"❌ Memory RAG Error: {e}")
        memory_manager = None
        memory_enhanced_processor = None
else:
    logger.warning("MongoDB not available - Memory RAG disabled")
    print("MongoDB not available - Memory RAG disabled")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/api/query', methods=['POST'])
def process_query():
    """Enhanced query processing with Memory RAG integration"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        chat_id = data.get('chat_id')
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        # Determine if we should use memory enhancement
        use_memory = chat_id and memory_enhanced_processor
        
        logger.info(f"🔍 Processing question: '{user_question}'" + 
                   (f" (chat: {chat_id}, memory: {use_memory})" if chat_id else " (no chat)"))
        
        start_time = time.time()
        result = None
        
        # Save user message to chat if chat_id provided
        if chat_id and mongodb_available:
            user_message = {
                'type': 'user',
                'content': user_question,
                'timestamp': datetime.now(timezone.utc)
            }
            save_message_to_chat(db, chat_id, user_message)
        
        # Process with Memory RAG if available and chat_id provided
        if use_memory:
            logger.info("🧠 Using Memory-Enhanced Processing")
            
            # Use asyncio to run the async memory processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    memory_enhanced_processor.process_with_memory(user_question, chat_id)
                )
                result['processing_mode'] = 'memory_enhanced'
            finally:
                loop.close()
                
        else:
            # Fallback to regular processing
            logger.info("🔄 Using Standard Processing")
            
            if two_stage_processor:
                # Use asyncio to run the async two-stage processor
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        two_stage_processor.process_question(user_question)
                    )
                    result['processing_mode'] = 'two_stage'
                finally:
                    loop.close()
            elif simple_processor:
                result = simple_processor.process_question(user_question)
                result['processing_mode'] = 'simple'
            else:
                return jsonify({"error": "No processors available"}), 503
        
        execution_time = time.time() - start_time
        result['execution_time'] = round(execution_time, 3)
        
        # Save AI response to chat
        if chat_id and mongodb_available and result.get('success'):
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
            save_message_to_chat(db, chat_id, ai_message)
        
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

if __name__ == '__main__':
    print("\n🔗 Starting GenAI Operations Analytics Server - MODULAR VERSION...")
    print("🎯 AI Operations Features:")
    print("   - ✅ Modular architecture with separated concerns")
    print("   - ✅ Enhanced Gemini client from utils/enhanced_gemini_client")
    print("   - ✅ Chat management from utils/chat_manager")
    print("   - ✅ Memory RAG system integration")
    print("   - ✅ Two-stage and simple query processing")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected to GenAI operations database")
        print("   ✅ Chat System: Indexes created, ready for persistence")
    else:
        print("   ❌ MongoDB: Connection failed")
        print("   ❌ Chat System: Not available")
    
    if gemini_available:
        print("   ✅ Gemini AI: Enhanced client ready for AI operations")
    else:
        print("   ⚠️ Gemini AI: Not available")
    
    if two_stage_processor:
        print("   ✅ Perfected Two-Stage Processor: AI operations processing ready")
    elif simple_processor:
        print("   ✅ Complete Simple Processor: Fallback processing ready")
    else:
        print("   ❌ No processors available")
    
    if memory_manager:
        print("   ✅ Memory RAG: Advanced conversation memory system ready")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 GenAI Operations Endpoints:")
    print("   - POST /api/query (AI operations intelligent processing + chat)")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)