# backend/appcondenselanggraph.py
"""
LangGraph-Enhanced Conversational Analytics Application
Advanced Flask app with sophisticated workflow orchestration using LangGraph
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
import uuid

# Import all modular components
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor
from utils.chat_manager import ensure_chat_indexes
from utils.enhanced_gemini_client import BulletproofGeminiClient
from utils.perfected_processor import PerfectedTwoStageProcessor

# LangGraph components (NEW)
#from utils.langgraph_analytics import LangGraphAnalyticsWorkflow
from utils.langgraph_analytics import EnhancedLangGraphAnalyticsWorkflow
from utils.mongodb_checkpointer import MongoDBCheckpointer
from workflows.analytics_flow import WorkflowSelector, WorkflowOptimizer

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
    """Convert ObjectId objects to strings and handle NaN values for JSON serialization"""
    import math
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, float) and math.isnan(obj):
        return None  # Convert NaN to null for JSON compatibility
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

class LangGraphProcessor:
    """
    LangGraph-enhanced processor that provides intelligent workflow orchestration
    while maintaining compatibility with existing interfaces
    """
    
    def __init__(self, langgraph_workflow: EnhancedLangGraphAnalyticsWorkflow):
        self.workflow = langgraph_workflow
        self.workflow_selector = WorkflowSelector()
        self.workflow_optimizer = WorkflowOptimizer(langgraph_workflow.db)
    
    async def process_with_memory(self, question: str, chat_id: str, user_id: str = "default") -> dict:
        """
        Compatibility method for existing routes
        Routes requests through LangGraph workflow system
        """
        return await self.process_with_workflow(question, chat_id, user_id)
    
    async def process_with_workflow(self, question: str, chat_id: str, user_id: str = "default", 
                                  thread_id: str = None, workflow_type: str = "auto") -> dict:
        """
        Enhanced processing with LangGraph workflow orchestration
        
        Args:
            question: User's analytics question
            chat_id: Chat session identifier
            user_id: User identifier for personalization
            thread_id: Optional thread ID for resuming workflows
            workflow_type: Workflow type selection ("auto", "simple", "complex", "interactive")
            
        Returns:
            Processed analytics result with workflow metadata
        """
        try:
            start_time = time.time()
            
            # Select appropriate workflow if auto mode
            if workflow_type == "auto":
                workflow_config = self.workflow_selector.select_workflow(question, {"user_id": user_id})
                logger.info(f"🎯 Auto-selected workflow: {workflow_config.name}")
            
            # Generate thread ID if not provided
            if not thread_id:
                thread_id = f"langgraph_{user_id}_{int(datetime.now().timestamp())}_{hash(question) % 10000}"
            
            logger.info(f"🧠 Processing with LangGraph: '{question}' (Thread: {thread_id})")
            
            # Execute workflow
            result = await self.workflow.execute_workflow(
                question=question,
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id
            )
            
            # Add processing metadata
            result['processing_time'] = time.time() - start_time
            result['processor_type'] = 'langgraph_enhanced'
            result['thread_id'] = thread_id
            result['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"✅ LangGraph processing completed in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ LangGraph processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processor_type": "langgraph_enhanced",
                "thread_id": thread_id,
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }
    
    async def resume_workflow(self, thread_id: str, user_input: str = None) -> dict:
        """Resume a paused workflow"""
        return await self.workflow.resume_workflow(thread_id, user_input)
    
    def get_workflow_status(self, thread_id: str) -> dict:
        """Get current workflow status"""
        return self.workflow.get_workflow_status(thread_id)
    
    def get_user_workflows(self, user_id: str) -> list:
        """Get user's workflow history"""
        return self.workflow.get_user_workflow_history(user_id)

# Flask App Setup
app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')

print("=" * 80)
print("🧠 LANGGRAPH-ENHANCED CONVERSATIONAL ANALYTICS")
print("=" * 80)
print(f"Database: {MONGODB_URI}")
print(f"API Key Present: {'✅ Yes' if GOOGLE_API_KEY else '❌ No'}")
print("=" * 80)

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
# INITIALIZE LANGGRAPH-ENHANCED COMPONENTS
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

# Initialize processors with LangGraph enhancement
langgraph_workflow = None
langgraph_processor = None
fallback_processor = None

if mongodb_available and gemini_available:
    try:
        # Initialize LangGraph workflow system
        langgraph_workflow = EnhancedLangGraphAnalyticsWorkflow(
            gemini_client=gemini_client,
            mongodb_client=db,
            schema_info=DATABASE_SCHEMA
        )
        
        # Initialize LangGraph processor
        langgraph_processor = LangGraphProcessor(langgraph_workflow)
        
        # Keep fallback processors for compatibility and comparison
        base_processor = PerfectedTwoStageProcessor(gemini_client, None, db)
        fallback_memory_manager = MemoryRAGManager(db, gemini_client)
        fallback_processor = MemoryEnhancedProcessor(
            base_processor, 
            fallback_memory_manager, 
            gemini_client
        )
        
        logger.info("🧠✅ LangGraph Workflow System - FULLY OPERATIONAL")
        print("🧠✅ LangGraph Workflow System - FULLY OPERATIONAL")
        print("       • Multi-step reasoning and branching logic")
        print("       • Error recovery and workflow resumption")  
        print("       • State persistence across sessions")
        print("       • Intelligent workflow selection")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize LangGraph system: {e}")
        print(f"❌ LangGraph initialization error: {e}")

elif not gemini_available:
    logger.warning("⚠️ Gemini API required for LangGraph operation")
    print("⚠️ Gemini API required for LangGraph operation")

# ============================================================================
# LANGGRAPH-SPECIFIC ROUTES
# ============================================================================

def run_async(coro):
    """Helper to run async functions in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.route('/api/langgraph-query', methods=['POST'])
def langgraph_enhanced_query():
    """LangGraph-enhanced query endpoint with workflow orchestration"""
    return run_async(process_langgraph_query_async())

async def process_langgraph_query_async():
    """Process query with LangGraph workflow orchestration"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400
        
        user_question = (data.get('question') or data.get('query') or '').strip()
        chat_id = data.get('chat_id', f"langgraph_{int(time.time())}")
        user_id = data.get('user_id', 'default_user')
        thread_id = data.get('thread_id')  # Optional for resuming workflows
        workflow_type = data.get('workflow_type', 'auto')  # auto, simple, complex, interactive
        
        if not user_question:
            return jsonify({"success": False, "error": "No question provided"}), 400
        
        logger.info(f"🧠 LangGraph Query: '{user_question}' (User: {user_id}, Chat: {chat_id})")
        
        # Use LangGraph enhanced processor
        if langgraph_processor:
            result = await langgraph_processor.process_with_workflow(
                question=user_question,
                chat_id=chat_id,
                user_id=user_id,
                thread_id=thread_id,
                workflow_type=workflow_type
            )
        else:
            return jsonify({
                "success": False, 
                "error": "LangGraph processor not available"
            }), 503
        
        # Add processing metadata
        result['processing_time'] = time.time() - start_time
        result['endpoint_used'] = 'langgraph_enhanced'
        result['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"🧠✅ LangGraph query processed in {result['processing_time']:.2f}s")
        
        # Clean ObjectIds and NaN values before JSON serialization
        cleaned_result = convert_objectid_to_str(result)
        return jsonify(cleaned_result)
        
    except Exception as e:
        logger.error(f"❌ LangGraph query processing failed: {e}")
        return jsonify({
            "success": False, 
            "error": str(e),
            "processing_time": time.time() - start_time,
            "endpoint_used": 'langgraph_enhanced'
        }), 500

@app.route('/api/workflow/status/<thread_id>', methods=['GET'])
def get_workflow_status(thread_id):
    """Get current workflow status for a thread"""
    try:
        if not langgraph_processor:
            return jsonify({"error": "LangGraph not available"}), 503
        
        status = langgraph_processor.get_workflow_status(thread_id)
        cleaned_status = convert_objectid_to_str(status)
        return jsonify(cleaned_status)
        
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/resume/<thread_id>', methods=['POST'])
def resume_workflow(thread_id):
    """Resume a paused or failed workflow"""
    return run_async(resume_workflow_async(thread_id))

async def resume_workflow_async(thread_id):
    try:
        if not langgraph_processor:
            return jsonify({"error": "LangGraph not available"}), 503
        
        data = request.get_json() or {}
        user_input = data.get('user_input')
        
        result = await langgraph_processor.resume_workflow(thread_id, user_input)
        cleaned_result = convert_objectid_to_str(result)
        return jsonify(cleaned_result)
        
    except Exception as e:
        logger.error(f"Failed to resume workflow: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/history/<user_id>', methods=['GET'])
def get_workflow_history(user_id):
    """Get workflow execution history for a user"""
    try:
        if not langgraph_processor:
            return jsonify({"error": "LangGraph not available"}), 503
        
        limit = request.args.get('limit', 20, type=int)
        history = langgraph_processor.get_user_workflows(user_id)
        
        history_data = {
            "user_id": user_id,
            "workflow_history": history[:limit]
        }
        cleaned_history = convert_objectid_to_str(history_data)
        return jsonify(cleaned_history)
        
    except Exception as e:
        logger.error(f"Failed to get workflow history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/active', methods=['GET'])
def get_active_workflows():
    """Get currently active workflows"""
    try:
        if not langgraph_workflow:
            return jsonify({"error": "LangGraph not available"}), 503
        
        user_id = request.args.get('user_id')
        active_workflows = langgraph_workflow.get_active_workflows(user_id)
        
        active_data = {
            "active_workflows": active_workflows,
            "count": len(active_workflows)
        }
        cleaned_active = convert_objectid_to_str(active_data)
        return jsonify(cleaned_active)
        
    except Exception as e:
        logger.error(f"Failed to get active workflows: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/workflow/available', methods=['GET'])
def get_available_workflows():
    """Get list of available workflow configurations"""
    try:
        if not langgraph_processor:
            return jsonify({"error": "LangGraph not available"}), 503
        
        selector = WorkflowSelector()
        workflows = selector.get_available_workflows()
        
        workflows_data = {
            "available_workflows": workflows,
            "count": len(workflows)
        }
        cleaned_workflows = convert_objectid_to_str(workflows_data)
        return jsonify(cleaned_workflows)
        
    except Exception as e:
        logger.error(f"Failed to get available workflows: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/langgraph-status', methods=['GET'])
def langgraph_system_status():
    """Get LangGraph system status and capabilities"""
    try:
        if langgraph_workflow:
            status = langgraph_workflow.get_system_stats()
            status['processor_available'] = langgraph_processor is not None
            status['fallback_available'] = fallback_processor is not None
        else:
            status = {
                'workflow_engine': 'LangGraph',
                'available': False,
                'error': 'LangGraph not initialized',
                'processor_available': False,
                'fallback_available': fallback_processor is not None
            }
        
        status['database_connected'] = mongodb_available
        status['gemini_available'] = gemini_available
        status['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        cleaned_status = convert_objectid_to_str(status)
        return jsonify(cleaned_status)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# REGISTER STANDARD ROUTE BLUEPRINTS WITH LANGGRAPH COMPATIBILITY
# ============================================================================

if mongodb_available and gemini_available:
    try:
        # Use LangGraph processor as primary, fallback as secondary
        primary_processor = langgraph_processor if langgraph_processor else fallback_processor
        secondary_processor = fallback_processor
        
        # Initialize route blueprints with LangGraph-enhanced processors
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
        
        logger.info("✅ All route blueprints registered with LangGraph enhancement")
        print("✅ All routes registered with LangGraph enhancement")
        
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
    """Enhanced health check with LangGraph status"""
    try:
        langgraph_status = langgraph_workflow.get_system_stats() if langgraph_workflow else {"available": False}
        
        status = {
            "status": "healthy" if mongodb_available and gemini_available else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected" if mongodb_available else "disconnected",
            "gemini_ai": "available" if gemini_available else "unavailable",
            "langgraph_system": langgraph_status,
            "processors": {
                "langgraph_enhanced": langgraph_processor is not None,
                "fallback_memory": fallback_processor is not None,
            },
            "version": "langgraph_enhanced_v1.0",
            "capabilities": {
                "workflow_orchestration": langgraph_workflow is not None,
                "error_recovery": langgraph_workflow is not None,
                "state_persistence": langgraph_workflow is not None and langgraph_workflow.checkpointer is not None,
                "workflow_resume": langgraph_workflow is not None and langgraph_workflow.checkpointer is not None,
                "multi_step_reasoning": langgraph_workflow is not None
            }
        }
        
        cleaned_status = convert_objectid_to_str(status)
        return jsonify(cleaned_status)
        
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
    print("🧠 STARTING LANGGRAPH-ENHANCED CONVERSATIONAL ANALYTICS")
    print("="*80)
    
    print("\n🔧 Advanced System Architecture:")
    print("   🧠 Workflow Engine: LangGraph with MongoDB checkpointing")
    print("   🤖 AI Engine: Google Gemini Pro with enhanced processing")
    print("   🔄 Processing: Multi-step workflows with error recovery")
    print("   💾 Data Storage: MongoDB with persistent workflow state")
    print("   🎯 Intelligence: Automatic workflow selection and optimization")
    
    print(f"\n📊 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected to analytics database")
        print("   ✅ Chat System: Persistent conversation storage ready")
        print("   ✅ Checkpointing: LangGraph state persistence enabled")
    else:
        print("   ❌ MongoDB: Connection failed")
    
    if gemini_available:
        print("   ✅ Gemini AI: Enhanced client operational")
    else:
        print("   ❌ Gemini AI: Not available")
    
    if langgraph_processor:
        print("   🧠✅ LangGraph Workflow System: FULLY OPERATIONAL")
        print("       • Multi-step reasoning with conditional branching")
        print("       • Error recovery and automatic retry logic")
        print("       • Workflow state persistence across sessions")
        print("       • Intelligent workflow selection and optimization")
        print("       • Interactive and exploratory analysis workflows")
    else:
        print("   ❌ LangGraph System: Not initialized")
    
    if fallback_processor:
        print("   ✅ Fallback System: Available for comparison and reliability")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("🧠 LangGraph-Enhanced Endpoints:")
    print("   - POST /api/langgraph-query (Advanced workflow processing)")
    print("   - GET /api/workflow/status/<thread_id> (Workflow status)")
    print("   - POST /api/workflow/resume/<thread_id> (Resume workflows)")
    print("   - GET /api/workflow/history/<user_id> (User workflow history)")
    print("   - GET /api/workflow/active (Active workflows)")
    print("   - GET /api/workflow/available (Available workflow types)")
    print("   - GET /api/langgraph-status (LangGraph system status)")
    print("   - POST /api/query (Standard processing with LangGraph)")
    print("   - GET /api/health (Enhanced system health check)")
    
    print("\n💡 Advanced Features:")
    print("   • Complex query handling with multi-step reasoning")
    print("   • Automatic error recovery and workflow resumption")
    print("   • State persistence - resume interrupted analysis")
    print("   • Intelligent workflow selection based on query complexity")
    print("   • Interactive workflows for guided data exploration")
    print("   • Performance optimization and user adaptation")
    
    print("\n🔄 Workflow Types Available:")
    print("   • Simple: Direct processing for straightforward queries")
    print("   • Complex: Multi-step analysis with validation")
    print("   • Interactive: User-guided exploration with feedback")
    print("   • Exploratory: Open-ended discovery with iterations")
    
    print("="*80)
    
    # Start the Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)