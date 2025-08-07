# backend/appcondensemem0.py
"""
Mem0-Enhanced Analytics Application
Complete backend with Mem0 integration for intelligent conversational analytics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
import time
from datetime import datetime, timezone
import pymongo
from bson import ObjectId
import json

# Import all modular components
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor
from utils.chat_manager import ensure_chat_indexes
from utils.enhanced_gemini_client import BulletproofGeminiClient
from utils.perfected_processor import PerfectedTwoStageProcessor
from utils.mem0 import Mem0EnhancedMemoryManager  # New Mem0 integration
from config import Config, DATABASE_SCHEMA

# Import route blueprints
from routes.query import init_query_routes
from routes.system import init_system_routes
from routes.chat import init_chat_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def convert_objectid_to_str(obj):
    """Convert ObjectId objects to strings for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

class Mem0EnhancedProcessor:
    """Enhanced processor that integrates Mem0 for intelligent memory management"""
    
    def __init__(self, base_processor, mem0_manager: Mem0EnhancedMemoryManager, gemini_client):
        self.base_processor = base_processor
        self.mem0_manager = mem0_manager
        self.gemini_client = gemini_client
    
    async def process_with_memory(self, question: str, chat_id: str, user_id: str = "default") -> dict:
        """Compatibility method for existing routes"""
        return await self.process_with_intelligent_memory(question, chat_id, user_id)
    
    async def process_with_intelligent_memory(self, question: str, chat_id: str, user_id: str = "default") -> dict:
        """Process query with Mem0 intelligent memory enhancement"""
        try:
            start_time = time.time()
            
            # Store the user question
            await self.mem0_manager.store_conversation_memory(
                user_id=user_id,
                chat_id=chat_id,
                content=question,
                memory_type='question'
            )
            
            # Get intelligent context from Mem0
            enhanced_context = await self.mem0_manager.get_relevant_context(
                user_id=user_id,
                question=question,
                limit=5
            )
            
            logger.info(f"📚 Mem0 Context Retrieved: {len(enhanced_context)} chars")
            
            # Process with enhanced context
            if hasattr(self.base_processor, 'process_question'):
                if asyncio.iscoroutinefunction(self.base_processor.process_question):
                    result = await self.base_processor.process_question(enhanced_context)
                else:
                    result = self.base_processor.process_question(enhanced_context)
            else:
                result = {"success": False, "error": "Base processor not compatible"}
            
            # Store successful results and learn from them
            if result.get('success'):
                # Store the answer
                answer_content = result.get('summary', 'Analysis completed successfully')
                await self.mem0_manager.store_conversation_memory(
                    user_id=user_id,
                    chat_id=chat_id,
                    content=answer_content,
                    memory_type='answer'
                )
                
                # Learn user preferences from successful interactions
                await self._learn_from_success(user_id, chat_id, question, result)
                
                # Generate intelligent suggestions
                smart_suggestions = await self.mem0_manager.get_smart_suggestions(
                    user_id=user_id,
                    current_context=enhanced_context
                )
                result['suggestions'] = smart_suggestions
            
            # Add Mem0 metadata to response
            result['mem0_enhanced'] = {
                'memory_system_used': self.mem0_manager.get_system_status(),
                'processing_time': time.time() - start_time,
                'context_length': len(enhanced_context),
                'user_id': user_id,
                'chat_id': chat_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Mem0 enhanced processing failed: {e}")
            
            # Fallback to base processor
            try:
                if hasattr(self.base_processor, 'process_question'):
                    if asyncio.iscoroutinefunction(self.base_processor.process_question):
                        return await self.base_processor.process_question(question)
                    else:
                        return self.base_processor.process_question(question)
                else:
                    return {"success": False, "error": f"Processing failed: {str(e)}"}
            except Exception as fallback_error:
                logger.error(f"Fallback processing also failed: {fallback_error}")
                return {"success": False, "error": "Complete processing failure"}
    
    async def _learn_from_success(self, user_id: str, chat_id: str, question: str, result: dict):
        """Learn user preferences from successful interactions"""
        try:
            # Learn chart preferences
            chart_type = result.get('chart_data', {}).get('type')
            if chart_type:
                await self.mem0_manager.learn_user_preference(
                    user_id=user_id,
                    preference_data={
                        'chat_id': chat_id,
                        'category': 'chart_type',
                        'details': f"{chart_type} charts for queries like '{question[:50]}...'",
                        'context': self._extract_query_domain(question),
                        'confidence': 0.8
                    }
                )
            
            # Learn query patterns
            query_domain = self._extract_query_domain(question)
            if query_domain:
                await self.mem0_manager.learn_user_preference(
                    user_id=user_id,
                    preference_data={
                        'chat_id': chat_id,
                        'category': 'query_style',
                        'details': f"User asks about {query_domain} using pattern: {question[:100]}",
                        'confidence': 0.7
                    }
                )
                
        except Exception as e:
            logger.warning(f"Learning from success failed: {e}")
    
    def _extract_query_domain(self, question: str) -> str:
        """Extract the domain/category of the query"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['cost', 'spending', 'expense', 'price']):
            return 'cost_analysis'
        elif any(word in question_lower for word in ['document', 'extraction', 'processing']):
            return 'document_processing'
        elif any(word in question_lower for word in ['compliance', 'obligation', 'requirement']):
            return 'compliance_monitoring'
        elif any(word in question_lower for word in ['agent', 'performance', 'efficiency']):
            return 'agent_performance'
        elif any(word in question_lower for word in ['user', 'role', 'access']):
            return 'user_management'
        else:
            return 'general_analytics'

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')

print("=" * 70)
print("🧠 MEM0-ENHANCED CONVERSATIONAL ANALYTICS")
print("=" * 70)
print(f"Database: {MONGODB_URI}")
print(f"API Key Present: {'✅ Yes' if GOOGLE_API_KEY else '❌ No'}")
print("=" * 70)

# Database Connection
db = None
mongodb_available = False

try:
    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[Config.DATABASE_NAME]
    client.admin.command('ping')
    mongodb_available = True
    logger.info(f"✅ MongoDB connected to {Config.DATABASE_NAME}")
    print(f"✅ MongoDB connected to {Config.DATABASE_NAME}")
except Exception as e:
    logger.error(f"❌ MongoDB connection failed: {e}")
    print(f"❌ MongoDB Error: {e}")
    mongodb_available = False

# Initialize chat indexes
if mongodb_available:
    ensure_chat_indexes(db)

# ============================================================================
# INITIALIZE MEM0-ENHANCED COMPONENTS
# ============================================================================

# Initialize Gemini client
gemini_client = None
gemini_available = False
if GOOGLE_API_KEY:
    try:
        gemini_client = BulletproofGeminiClient(GOOGLE_API_KEY)
        gemini_available = True
        logger.info("✅ Enhanced Gemini client initialized")
        print("✅ Gemini AI client ready")
    except Exception as e:
        logger.error(f"❌ Gemini initialization failed: {e}")
        print(f"❌ Gemini Error: {e}")

# Initialize processors with Mem0 enhancement
two_stage_processor = None
mem0_manager = None
mem0_enhanced_processor = None
fallback_memory_processor = None

if mongodb_available and gemini_available:
    try:
        # Initialize base two-stage processor
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, None, db)
        logger.info("✅ Base processor initialized")
        
        # Initialize Mem0 Enhanced Memory Manager
        mem0_config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "conversational_analytics",
                    "path": "./mem0_analytics_storage",
                    "persist": True,
                    "embedding_function": "all-MiniLM-L6-v2"
                }
            },
            "memory": {
                "relevance_threshold": 0.7,
                "max_memories_per_user": 1000,
                "decay_rate": 0.005,  # Very slow decay for analytics
                "update_threshold": 0.8
            }
        }
        
        mem0_manager = Mem0EnhancedMemoryManager(
            mongodb_client=db,
            config=mem0_config
        )
        
        # Initialize Mem0 Enhanced Processor
        mem0_enhanced_processor = Mem0EnhancedProcessor(
            base_processor=two_stage_processor,
            mem0_manager=mem0_manager,
            gemini_client=gemini_client
        )
        
        # Keep fallback memory processor for compatibility
        fallback_memory_manager = MemoryRAGManager(db, gemini_client)
        fallback_memory_processor = MemoryEnhancedProcessor(
            two_stage_processor, 
            fallback_memory_manager, 
            gemini_client
        )
        
        # Log system status
        mem0_status = mem0_manager.get_system_status()
        if mem0_status['mem0_available']:
            logger.info("🧠✅ Mem0 Enhanced Memory System - FULLY OPERATIONAL")
            print("🧠✅ Mem0 Enhanced Memory System - FULLY OPERATIONAL")
        else:
            logger.info("⚠️ Mem0 not available - using MongoDB fallback")
            print("⚠️ Mem0 not available - using MongoDB fallback")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Mem0 processors: {e}")
        print(f"❌ Processor initialization error: {e}")

elif not gemini_available:
    logger.warning("⚠️ Gemini API required for operation")
    print("⚠️ Gemini API required for operation")

# ============================================================================
# CUSTOM MEM0-ENHANCED ROUTES
# ============================================================================

def run_async(coro):
    """Helper to run async functions in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/api/mem0-query', methods=['POST'])
def mem0_enhanced_query():
    """Mem0-enhanced query endpoint with intelligent memory"""
    return run_async(process_mem0_query_async())

async def process_mem0_query_async():
    """Process query with Mem0 intelligent memory enhancement"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        user_question = data.get('question', '').strip()
        chat_id = data.get('chat_id', f"chat_{int(time.time())}")
        user_id = data.get('user_id', 'default_user')
        
        if not user_question:
            return jsonify({"success": False, "error": "No question provided"}), 400
        
        logger.info(f"🧠 Mem0 Query: '{user_question}' (User: {user_id}, Chat: {chat_id})")
        
        # Use Mem0 enhanced processor if available
        if mem0_enhanced_processor:
            result = await mem0_enhanced_processor.process_with_intelligent_memory(
                question=user_question,
                chat_id=chat_id,
                user_id=user_id
            )
        elif fallback_memory_processor:
            # Fallback to regular memory processor
            result = await fallback_memory_processor.process_with_memory(
                question=user_question,
                chat_id=chat_id,
                user_id=user_id
            )
        else:
            return jsonify({
                "success": False, 
                "error": "No memory processors available"
            }), 503
        
        # Add processing metadata
        result['processing_time'] = time.time() - start_time
        result['endpoint_used'] = 'mem0_enhanced'
        result['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"🧠✅ Mem0 Query processed in {result['processing_time']:.2f}s")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Mem0 query processing failed: {e}")
        return jsonify({
            "success": False, 
            "error": str(e),
            "processing_time": time.time() - start_time,
            "endpoint_used": 'mem0_enhanced'
        }), 500

@app.route('/api/mem0-status', methods=['GET'])
def mem0_system_status():
    """Get Mem0 system status and capabilities"""
    try:
        if mem0_manager:
            status = mem0_manager.get_system_status()
            status['processor_available'] = mem0_enhanced_processor is not None
            status['fallback_available'] = fallback_memory_processor is not None
        else:
            status = {
                'mem0_available': False,
                'mem0_initialized': False,
                'mongodb_fallback': mongodb_available,
                'system_type': 'No Memory System',
                'processor_available': False,
                'fallback_available': fallback_memory_processor is not None
            }
        
        status['database_connected'] = mongodb_available
        status['gemini_available'] = gemini_available
        status['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/mem0-learn', methods=['POST'])
def learn_user_preference():
    """Endpoint for explicit user preference learning"""
    return run_async(learn_preference_async())

async def learn_preference_async():
    """Learn user preferences explicitly"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id', 'default_user')
        preference_data = data.get('preference_data', {})
        
        if not preference_data:
            return jsonify({"success": False, "error": "No preference data provided"}), 400
        
        if mem0_manager:
            success = await mem0_manager.learn_user_preference(user_id, preference_data)
            
            if success:
                logger.info(f"✅ Learned preference for user {user_id}: {preference_data}")
                return jsonify({
                    "success": True,
                    "message": "Preference learned successfully",
                    "user_id": user_id
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to learn preference"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": "Mem0 manager not available"
            }), 503
            
    except Exception as e:
        logger.error(f"Preference learning failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# REGISTER STANDARD ROUTE BLUEPRINTS WITH MEM0 COMPATIBILITY
# ============================================================================

if mongodb_available and gemini_available:
    try:
        # Use Mem0 enhanced processor as primary, fallback as secondary
        primary_processor = mem0_enhanced_processor if mem0_enhanced_processor else fallback_memory_processor
        secondary_processor = two_stage_processor
        
        # Initialize route blueprints with Mem0-enhanced processors
        query_blueprint = init_query_routes(
            db, mongodb_available, gemini_available, 
            primary_processor, secondary_processor
        )
        system_blueprint = init_system_routes(
            db, mongodb_available, gemini_available, 
            secondary_processor, primary_processor, MONGODB_URI
        )
        chat_blueprint = init_chat_routes(db, mongodb_available)
        
        # Register blueprints
        app.register_blueprint(query_blueprint)
        app.register_blueprint(system_blueprint)
        app.register_blueprint(chat_blueprint)
        
        logger.info("✅ All route blueprints registered with Mem0 enhancement")
        print("✅ All routes registered with Mem0 enhancement")
        
    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        print(f"❌ Route Error: {e}")
else:
    logger.warning("⚠️ Routes not registered - missing dependencies")
    print("⚠️ Routes not registered - missing dependencies")

# ============================================================================
# HEALTH CHECK AND DEBUG ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check with Mem0 status"""
    try:
        status = {
            "status": "healthy" if mongodb_available and gemini_available else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected" if mongodb_available else "disconnected",
            "gemini_ai": "available" if gemini_available else "unavailable",
            "mem0_system": mem0_manager.get_system_status() if mem0_manager else {"available": False},
            "processors": {
                "mem0_enhanced": mem0_enhanced_processor is not None,
                "fallback_memory": fallback_memory_processor is not None,
                "base_two_stage": two_stage_processor is not None
            },
            "version": "mem0_enhanced_v1.0"
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🧠 STARTING MEM0-ENHANCED CONVERSATIONAL ANALYTICS SERVER")
    print("="*80)
    
    print("\n🔧 System Architecture:")
    print("   📚 Memory System: Mem0 with MongoDB fallback")
    print("   🤖 AI Engine: Google Gemini Pro")
    print("   🔍 Query Processing: Two-stage intelligent processing")
    print("   💾 Data Storage: MongoDB with vector embeddings")
    
    print(f"\n📊 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected to analytics database")
        print("   ✅ Chat System: Persistent conversation storage ready")
    else:
        print("   ❌ MongoDB: Connection failed")
    
    if gemini_available:
        print("   ✅ Gemini AI: Enhanced client operational")
    else:
        print("   ❌ Gemini AI: Not available")
    
    if mem0_enhanced_processor:
        mem0_status = mem0_manager.get_system_status()
        if mem0_status['mem0_available']:
            print("   🧠✅ Mem0 Enhanced Memory: FULLY OPERATIONAL")
            print("       • Intelligent context retrieval")
            print("       • Cross-session user learning")
            print("       • Smart suggestion generation")
            print("       • 90% token cost reduction")
        else:
            print("   ⚠️ Mem0: Not available - using MongoDB fallback")
    else:
        print("   ❌ Memory System: Not initialized")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("🧠 Mem0-Enhanced Endpoints:")
    print("   - POST /api/mem0-query (Intelligent memory-enhanced processing)")
    print("   - GET /api/mem0-status (Memory system status)")
    print("   - POST /api/mem0-learn (User preference learning)")
    print("   - POST /api/query (Standard processing with memory)")
    print("   - GET /api/health (Enhanced system health check)")
    print("   - GET /api/debug/collections (Database debugging)")
    
    print("\n💡 Usage Tips:")
    print("   • Use /api/mem0-query for best intelligent memory experience")
    print("   • Include user_id parameter for personalized learning")
    print("   • System learns from successful interactions automatically")
    print("   • Check /api/mem0-status for memory system capabilities")
    
    print("="*80)
    
    # Start the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)