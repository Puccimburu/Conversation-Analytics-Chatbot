from flask import Flask
from flask_cors import CORS
import logging
import pymongo
from datetime import datetime, timezone

# Import configurations
from config.config import Config, DATABASE_SCHEMA
from config.gemini_config import GeminiConfig

# Import services
from services.gemini_service import BulletproofGeminiClient
from services.chat_service import ChatService
from services.analytics_service import CompleteSimpleQueryProcessor, PerfectedTwoStageProcessor
from services.memory_service import MemoryService

# Import route blueprints
from routes.conversation_management import init_conversation_routes
from routes.analytics_routes import init_analytics_routes
from routes.memory_routes import init_memory_routes
from routes.system_routes import init_system_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app, origins=Config.CORS_ORIGINS)

print("=" * 60)
print("PERFECTED AI ANALYTICS - BULLETPROOF GEMINI TWO-STAGE + CHAT (MODULAR)")
print("=" * 60)
print(f"Database: {Config.MONGODB_URI}")
print(f"API Key Present: {'Yes' if GeminiConfig.GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

db = None
mongodb_available = False

try:
    client = pymongo.MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[Config.DATABASE_NAME]
    client.admin.command('ping')
    mongodb_available = True
    logger.info("MongoDB connected successfully to GenAI database")
    print("MongoDB connected successfully to GenAI database")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    print(f"MongoDB Error: {e}")
    mongodb_available = False

# ============================================================================
# SERVICE INITIALIZATION
# ============================================================================

# Initialize Gemini Client
gemini_client = None
gemini_available = False

if GeminiConfig.GOOGLE_API_KEY and GeminiConfig.GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        gemini_client = BulletproofGeminiClient.create_client()
        gemini_available = gemini_client and gemini_client.available
        if gemini_available:
            logger.info("✅ Bulletproof Gemini client initialized")
            print("✅ Bulletproof Gemini client initialized")
        else:
            logger.warning("⚠️ Gemini client created but not available")
            print("⚠️ Gemini client created but not available")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        print(f"❌ Gemini Error: {e}")
        gemini_available = False
else:
    logger.warning("⚠️ No Google API key provided")
    print("⚠️ No Google API key provided")
    gemini_available = False

# Initialize Chat Service
chat_service = None
if mongodb_available:
    chat_service = ChatService(db)
    logger.info("✅ Chat service initialized")
    print("✅ Chat service initialized")

# Initialize Analytics Services
simple_processor = None
two_stage_processor = None

if db is not None:
    simple_processor = CompleteSimpleQueryProcessor(db)
    logger.info("✅ Simple processor initialized")
    
    if gemini_available and gemini_client:
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("✅ Perfected two-stage processor initialized")
        print("✅ Perfected two-stage processor initialized")
    else:
        logger.info("✅ Complete simple processor ready (Gemini not available)")
        print("✅ Complete simple processor ready (Gemini not available)")

# Determine which processor to use as main analytics service
analytics_service = two_stage_processor if two_stage_processor else simple_processor

# Initialize Memory Service
memory_service = None
if mongodb_available and db is not None:
    try:
        memory_service = MemoryService(db, gemini_client)
        
        # Create memory-enhanced processor if we have a base processor
        if analytics_service:
            memory_enhanced_processor = memory_service.create_memory_enhanced_processor(analytics_service)
            if memory_enhanced_processor:
                # Use memory-enhanced processor as main analytics service if available
                analytics_service = memory_enhanced_processor
                logger.info("✅ Memory-Enhanced Processor ready with Smart Suggestions")
                print("✅ Memory-Enhanced Processor ready with Smart Suggestions")
        
        logger.info("✅ Memory service initialized")
        print("✅ Memory service initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Memory service: {e}")
        print(f"❌ Memory Service Error: {e}")
        memory_service = None
else:
    logger.warning("⚠️ MongoDB not available - Memory service disabled")
    print("⚠️ MongoDB not available - Memory service disabled")

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Initialize and register blueprints
if chat_service:
    conversation_bp = init_conversation_routes(chat_service)
    app.register_blueprint(conversation_bp)
    logger.info("✅ Conversation routes registered")

if analytics_service:
    analytics_bp = init_analytics_routes(analytics_service, memory_service, chat_service, db)
    app.register_blueprint(analytics_bp)
    logger.info("✅ Analytics routes registered")

if memory_service:
    memory_bp = init_memory_routes(memory_service)
    app.register_blueprint(memory_bp)
    logger.info("✅ Memory routes registered")

# System routes (always available)
system_bp = init_system_routes(analytics_service, memory_service, chat_service, db)
app.register_blueprint(system_bp)
logger.info("✅ System routes registered")

# ============================================================================
# HEALTH CHECK ENDPOINT (Direct registration for backward compatibility)
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return {
        "message": "GenAI Operations Analytics Server (Modular)",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0-modular",
        "endpoints": {
            "health": "/api/health",
            "query": "/api/query",
            "chats": "/api/chats",
            "examples": "/api/examples",
            "debug": "/api/debug/collections",
            "system_test": "/api/system/test"
        }
    }

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return {
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist",
        "available_endpoints": [
            "/api/health",
            "/api/query", 
            "/api/chats",
            "/api/examples",
            "/api/debug/collections",
            "/api/system/test"
        ]
    }, 404

@app.errorhandler(500)
def internal_error(error):
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, 500

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("\n🔗 Starting GenAI Operations Analytics Server (Modular) with Chat...")
    print("🎯 AI Operations Features:")
    print("   - ✅ Bulletproof Gemini two-stage processing for AI operations")
    print("   - ✅ Enhanced retry logic with exponential backoff")
    print("   - ✅ Intelligent JSON extraction and validation")
    print("   - ✅ Smart fallback visualizations for operational data")
    print("   - ✅ Complete simple processor backup")
    print("   - ✅ Complete chat session management")
    print("   - ✅ Real-time message persistence")
    print("   - ✅ Chat history and search")
    print("   - ✅ Smart context-aware follow-up suggestions")
    print("   - ✅ Memory RAG system for operational intelligence")
    print("   - ✅ MODULAR ARCHITECTURE with Flask Blueprints")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected to GenAI operations database")
        print("   ✅ Chat System: Indexes created, ready for persistence")
    else:
        print("   ❌ MongoDB: Connection failed")
        print("   ❌ Chat System: Not available")
    
    if gemini_available:
        print("   ✅ Gemini AI: Bulletproof client ready for AI operations")
    else:
        print("   ⚠️ Gemini AI: Not available")
    
    if two_stage_processor:
        print("   ✅ Perfected Two-Stage Processor: AI operations processing ready")
    elif simple_processor:
        print("   ✅ Complete Simple Processor: Fallback processing ready")
    else:
        print("   ❌ No processors available")
    
    if memory_service and memory_service.is_available():
        print("   ✅ Memory RAG: Advanced conversation memory system ready")
    
    print(f"\n🌐 Server starting on http://localhost:{Config.PORT}")
    print("📊 GenAI Operations Endpoints:")
    print("   - POST /api/query (AI operations intelligent processing + chat)")
    print("   - POST /api/system/test (comprehensive system testing)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/examples (GenAI operations example questions)")
    print("   - GET  /api/debug/collections (GenAI collections debug info)")
    print("\n💬 Chat Management Endpoints:")
    print("   - GET  /api/chats (list all chat sessions)")
    print("   - POST /api/chats (create new chat session)")
    print("   - GET  /api/chats/{id} (get specific chat)")
    print("   - PUT  /api/chats/{id} (update chat metadata)")
    print("   - DELETE /api/chats/{id} (delete chat session)")
    print("   - POST /api/chats/{id}/messages (add message to chat)")
    print("   - GET  /api/chats/stats (chat system statistics)")
    print("\n🧠 Memory RAG Endpoints:")
    print("   - GET  /api/memory/stats/{chat_id} (memory statistics)")
    print("   - POST /api/memory/search/{chat_id} (search memories)")
    print("\n🤖 AI Operations Domain:")
    print("   - Cost analysis and optimization")
    print("   - Document processing intelligence")
    print("   - Compliance risk assessment")
    print("   - Agent performance monitoring")
    print("   - Operational efficiency analytics")
    print("=" * 80)
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)