# backend/app.py - Fully Modularized Flask Application

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
from utils.chat_manager import (
    ensure_chat_indexes, create_new_chat_session, save_message_to_chat,
    get_all_chats, get_chat_by_id, delete_chat_session
)
from utils.enhanced_gemini_client import BulletproofGeminiClient
from utils.simple_query_processor import CompleteSimpleQueryProcessor
from utils.perfected_processor import PerfectedTwoStageProcessor
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
        logger.info("Enhanced Gemini client initialized from utils/enhanced_gemini_client")
        print("Enhanced Gemini client initialized from utils/enhanced_gemini_client")
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
    logger.info("Simple query processor initialized from utils/simple_query_processor")
    print("Simple query processor initialized from utils/simple_query_processor")
    
    if gemini_available and gemini_client:
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("Perfected two-stage processor initialized from utils/perfected_processor")
        print("Perfected two-stage processor initialized from utils/perfected_processor")
    else:
        logger.info("Complete simple processor ready (Gemini not available)")
        print("Complete simple processor ready (Gemini not available)")

# Initialize Memory RAG system
if mongodb_available and db is not None:
    try:
        memory_manager = MemoryRAGManager(db, gemini_client)
        logger.info("Memory RAG Manager initialized from utils/memory_rag")
        print("Memory RAG Manager initialized from utils/memory_rag")
        
        # Create memory-enhanced processor
        if two_stage_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                two_stage_processor, 
                memory_manager, 
                gemini_client
            )
            logger.info("Memory-Enhanced Two-Stage Processor ready")
            print("Memory-Enhanced Two-Stage Processor ready")
        elif simple_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                simple_processor, 
                memory_manager, 
                gemini_client
            )
            logger.info("Memory-Enhanced Simple Processor ready")
            print("Memory-Enhanced Simple Processor ready")
            
    except Exception as e:
        logger.error(f"Failed to initialize Memory RAG: {e}")
        print(f"Memory RAG Error: {e}")
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
    """Enhanced query processing with Memory RAG integration - Fully Modular"""
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "mongodb_available": mongodb_available,
        "gemini_available": gemini_available,
        "processors": {
            "simple_processor": simple_processor is not None,
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

if __name__ == '__main__':
    print("\nStarting GenAI Operations Analytics Server - FULLY MODULAR VERSION...")
    print("Modular Architecture Features:")
    print("   - Chat management: utils/chat_manager.py")
    print("   - Enhanced Gemini client: utils/enhanced_gemini_client.py")
    print("   - Simple query processor: utils/simple_query_processor.py")
    print("   - Perfected two-stage processor: utils/perfected_processor.py")
    print("   - Memory RAG system: utils/memory_rag.py")
    print("   - Analytics processor: utils/analytics_processor.py")
    print("   - Configuration: config.py")
    
    print("\nSystem Status:")
    if mongodb_available:
        print("   [OK] MongoDB: Connected to GenAI operations database")
        print("   [OK] Chat System: Indexes created, ready for persistence")
    else:
        print("   [ERROR] MongoDB: Connection failed")
        print("   [ERROR] Chat System: Not available")
    
    if gemini_available:
        print("   [OK] Gemini AI: Enhanced client ready for AI operations")
    else:
        print("   [WARNING] Gemini AI: Not available")
    
    if two_stage_processor:
        print("   [OK] Perfected Two-Stage Processor: AI operations processing ready")
    elif simple_processor:
        print("   [OK] Complete Simple Processor: Fallback processing ready")
    else:
        print("   [ERROR] No processors available")
    
    if memory_manager:
        print("   [OK] Memory RAG: Advanced conversation memory system ready")
    
    print(f"\nServer starting on http://localhost:5000")
    print("GenAI Operations Endpoints:")
    print("   - POST /api/query (AI operations intelligent processing + chat)")
    print("   - GET  /api/health (system health check)")
    print("   - GET  /api/system/info (modular architecture information)")
    
    print("\nModular File Structure:")
    print("   app.py - Flask application with routing only")
    print("   config.py - Configuration and database schema")
    print("   utils/chat_manager.py - Chat session management")
    print("   utils/enhanced_gemini_client.py - Bulletproof Gemini client")
    print("   utils/simple_query_processor.py - Pattern matching processor")
    print("   utils/perfected_processor.py - Two-stage Gemini processor")
    print("   utils/memory_rag.py - Memory and RAG system")
    print("   utils/analytics_processor.py - Analytics processing")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)