# Complete backend/app.py with debugging and table fixes
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime, timezone
import pymongo
import time

# Import all modular components
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor
from utils.chat_manager import ensure_chat_indexes
from utils.enhanced_gemini_client import BulletproofGeminiClient
# from utils.simple_query_processor import CompleteSimpleQueryProcessor  # Removed - using Gemini-only architecture
from utils.perfected_processor import PerfectedTwoStageProcessor
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

app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')

print("=" * 60)
print("PERFECTED AI ANALYTICS - FULLY MODULAR ARCHITECTURE")
print("=" * 60)
print(f"Database: {MONGODB_URI}")
print(f"API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Database Connection
db = None
mongodb_available = False

try:
    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[Config.DATABASE_NAME]
    client.admin.command('ping')
    mongodb_available = True
    logger.info(f"MongoDB connected successfully to {Config.DATABASE_NAME} database")
    print(f"MongoDB connected successfully to {Config.DATABASE_NAME} database")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    print(f"MongoDB Error: {e}")
    mongodb_available = False

# Initialize chat collection indexes on startup
if mongodb_available:
    ensure_chat_indexes(db)

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

# Initialize components with error handling
gemini_client = None
gemini_available = False
if GOOGLE_API_KEY:
    try:
        gemini_client = BulletproofGeminiClient(GOOGLE_API_KEY)
        gemini_available = True
        logger.info("✅ Enhanced Gemini client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")

# Initialize processors (Gemini-only architecture)
two_stage_processor = None
memory_manager = None
memory_enhanced_processor = None

if mongodb_available and gemini_available:
    try:
        # Initialize two-stage processor (no simple fallback needed)
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, None, db)
        logger.info("✅ Perfected Two-Stage Processor initialized (Gemini-only)")
        
        # Initialize memory systems
        memory_manager = MemoryRAGManager(db, gemini_client)
        memory_enhanced_processor = MemoryEnhancedProcessor(two_stage_processor, memory_manager, gemini_client)
        logger.info("✅ Memory-Enhanced Processor initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize processors: {e}")
elif not gemini_available:
    logger.warning("⚠️ Gemini API not available - system requires Gemini for operation")

# ============================================================================
# REGISTER ROUTE BLUEPRINTS
# ============================================================================

# Initialize and register route blueprints
if mongodb_available and gemini_available:
    # Initialize route modules with dependencies
    query_blueprint = init_query_routes(db, mongodb_available, gemini_available, memory_enhanced_processor, two_stage_processor)
    system_blueprint = init_system_routes(db, mongodb_available, gemini_available, two_stage_processor, memory_enhanced_processor, MONGODB_URI)
    chat_blueprint = init_chat_routes(db, mongodb_available)
    
    # Register blueprints
    app.register_blueprint(query_blueprint)
    app.register_blueprint(system_blueprint)
    app.register_blueprint(chat_blueprint)
    
    logger.info("✅ All route blueprints registered successfully")
else:
    logger.warning("⚠️ Route blueprints not registered - missing dependencies")

# Routes are now modularized in the routes/ folder

if __name__ == '__main__':
    print("\nStarting GenAI Operations Analytics Server - FULLY MODULAR VERSION...")
    print("Modular Architecture Features:")
    print("   - Chat management: utils/chat_manager.py")
    print("   - Enhanced Gemini client: utils/enhanced_gemini_client.py")
    print("   - Simple query processor: utils/simple_query_processor.py")
    print("   - Perfected processor: utils/perfected_processor.py")
    print("   - Memory RAG system: utils/memory_rag.py")
    print("   - Analytics processor: utils/analytics_processor.py")
    
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
    else:
        print("   ❌ No processors available - Gemini AI required")
    
    if memory_manager:
        print("   ✅ Memory RAG: Advanced conversation memory system ready")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 GenAI Operations Endpoints:")
    print("   - POST /api/query (AI operations intelligent processing + chat)")
    print("   - GET /api/health (System health check)")
    print("   - GET /api/debug/collections (Database debugging)")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)