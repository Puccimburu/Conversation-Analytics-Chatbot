# Complete backend/app.py with debugging and table fixes
from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime, timezone
import pymongo
import time
from bson import ObjectId
import json

# Import all modular components
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor
from utils.chat_manager import (
    ensure_chat_indexes, create_new_chat_session, save_message_to_chat,
    get_all_chats, get_chat_by_id, delete_chat_session
)
from utils.enhanced_gemini_client import BulletproofGeminiClient
# from utils.simple_query_processor import CompleteSimpleQueryProcessor  # Removed - using Gemini-only architecture
from utils.perfected_processor import PerfectedTwoStageProcessor
from config import Config, DATABASE_SCHEMA

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
# MAIN QUERY PROCESSING ENDPOINT WITH ENHANCED DEBUGGING
# ============================================================================

@app.route('/api/query', methods=['POST'])
def process_query_wrapper():
    """Wrapper to handle async processing in Flask"""
    return run_async(process_query_async())

async def process_query_async():
    """
    Main query processing endpoint with comprehensive debugging for table issues
    """
    start_time = time.time()
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        user_question = data.get('question', '').strip()
        chat_id = data.get('chat_id')
        
        if not user_question:
            return jsonify({"success": False, "error": "No question provided"}), 400
        
        logger.info(f"🔍 Processing question: '{user_question}' (chat: {chat_id}, memory: {memory_enhanced_processor})")
        
        # Save user message to chat if chat_id provided
        if chat_id and mongodb_available:
            user_message = {
                'role': 'user',
                'content': user_question,
                'timestamp': datetime.now(timezone.utc)
            }
            save_message_to_chat(db, chat_id, user_message)
        
        # Process with best available processor
        result = None
        processing_mode = "unknown"
        
        if memory_enhanced_processor and gemini_available:
            logger.info("🧠 Using Memory-Enhanced Processing")
            processing_mode = "memory_enhanced"
            result = await memory_enhanced_processor.process_with_memory(user_question, chat_id)
            
        elif two_stage_processor and gemini_available:
            logger.info("🚀 Using Perfected Two-Stage Processing")
            processing_mode = "two_stage_perfected"
            result = await two_stage_processor.process_question(user_question)
            
        else:
            return jsonify({
                "success": False,
                "error": "Gemini AI service required but not available",
                "processing_mode": "gemini_required"
            }), 503
        
        # Enhanced debugging for table responses
        if result and result.get('success') and result.get('visualization'):
            viz = result['visualization']
            if viz.get('chart_type') == 'table':
                chart_config = viz.get('chart_config', {})
                table_data = chart_config.get('tableData', [])
                columns = chart_config.get('columns', [])
                
                logger.info(f"🔍 TABLE RESPONSE DEBUG:")
                logger.info(f"   - Chart type: {viz.get('chart_type')}")
                logger.info(f"   - Table data rows: {len(table_data)}")
                logger.info(f"   - Columns count: {len(columns)}")
                
                if table_data:
                    sample_row = table_data[0]
                    logger.info(f"   - Sample data keys: {list(sample_row.keys())}")
                    logger.info(f"   - Sample data values: {dict(list(sample_row.items())[:3])}")
                
                if columns:
                    column_keys = [col.get('key', col.get('field', 'unknown')) for col in columns]
                    column_labels = [col.get('label', col.get('header', 'unknown')) for col in columns]
                    logger.info(f"   - Column keys: {column_keys}")
                    logger.info(f"   - Column labels: {column_labels}")
                
                # Verify data-column alignment
                if table_data and columns:
                    sample_row = table_data[0]
                    for col in columns:
                        col_key = col.get('key', col.get('field'))
                        if col_key in sample_row:
                            logger.info(f"   ✅ Column '{col_key}' matches data field")
                        else:
                            logger.warning(f"   ❌ Column '{col_key}' NOT found in data fields: {list(sample_row.keys())}")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Add processing metadata
        if result and result.get('success'):
            result['processing_mode'] = processing_mode
            result['execution_time'] = execution_time
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Save AI response to chat if successful
        if chat_id and mongodb_available and result and result.get('success'):
            ai_message = {
                'role': 'assistant',
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
        # Convert ObjectId fields to strings before JSON serialization
        result = convert_objectid_to_str(result)
        return jsonify(result)
        
    except Exception as e:
        error_msg = f"Query processing failed: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            "success": False,
            "error": error_msg,
            "processing_mode": "error"
        }), 500

# ============================================================================
# HEALTH AND SYSTEM ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with detailed status"""
    return jsonify({
        "status": "healthy",
        "mongodb_available": mongodb_available,
        "gemini_available": gemini_available,
        "processors": {
            "two_stage_processor": two_stage_processor is not None,
            "memory_enhanced_processor": memory_enhanced_processor is not None
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """System information endpoint"""
    return jsonify({
        "architecture": "fully_modular",
        "components": {
            "chat_manager": "utils.chat_manager",
            "enhanced_gemini_client": "utils.enhanced_gemini_client", 
            "simple_query_processor": "utils.simple_query_processor",
            "perfected_processor": "utils.perfected_processor",
            "memory_rag": "utils.memory_rag",
            "analytics_processor": "utils.analytics_processor"
        },
        "database": {
            "uri": MONGODB_URI,
            "available": mongodb_available,
            "schema": "GenAI Operations & Document Intelligence"
        },
        "ai_services": {
            "gemini_available": gemini_available,
            "model": "gemini-1.5-flash" if gemini_available else None
        }
    })

@app.route('/api/debug/collections', methods=['GET'])
def debug_collections():
    """Debug endpoint to check database collections"""
    if not mongodb_available:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        collections = db.list_collection_names()
        collection_stats = {}
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                sample = collection.find_one({}) if count > 0 else None
                
                collection_stats[collection_name] = {
                    "count": count,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "has_data": count > 0
                }
            except Exception as e:
                collection_stats[collection_name] = {"error": str(e)}
        
        return jsonify({
            "total_collections": len(collections),
            "collections": collection_stats
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to get collection info: {str(e)}"}), 500

# ============================================================================
# CHAT MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all chat sessions"""
    if not mongodb_available:
        return jsonify({"error": "Database not available"}), 503
    
    chats = get_all_chats(db)
    if chats is not None:
        return jsonify({"chats": chats})
    else:
        return jsonify({"error": "Failed to retrieve chats"}), 500

@app.route('/api/chats', methods=['POST'])
def create_chat():
    """Create a new chat session"""
    if not mongodb_available:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        data = request.get_json() or {}
        title = data.get('title')
        category = data.get('category', 'conversational')
        
        chat_id = create_new_chat_session(db, title, category)
        
        if chat_id:
            return jsonify({"chat_id": chat_id, "success": True})
        else:
            return jsonify({"error": "Failed to create chat"}), 500
            
    except Exception as e:
        logger.error(f"Failed to create chat: {e}")
        return jsonify({"error": "Failed to create chat"}), 500

@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get specific chat session with messages"""
    if not mongodb_available:
        return jsonify({"error": "Database not available"}), 503
    
    chat = get_chat_by_id(db, chat_id)
    if chat is not None:
        return jsonify(chat)
    else:
        return jsonify({"error": "Chat not found"}), 404

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session"""
    if not mongodb_available:
        return jsonify({"error": "Database not available"}), 503
    
    if delete_chat_session(db, chat_id):
        return jsonify({"success": True, "message": "Chat deleted"})
    else:
        return jsonify({"error": "Chat not found"}), 404

# ============================================================================
# ASYNC WRAPPER FOR FLASK
# ============================================================================

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Remove duplicate route definitions - use only the main process_query function

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