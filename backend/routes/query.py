from flask import Blueprint, request, jsonify
import asyncio
import time
import logging
from datetime import datetime, timezone

# Create blueprint
query_bp = Blueprint('query', __name__)

logger = logging.getLogger(__name__)

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

def init_query_routes(db, mongodb_available, gemini_available, memory_enhanced_processor, two_stage_processor):
    """Initialize query routes with dependencies"""
    
    @query_bp.route('/api/query', methods=['POST'])
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
                from utils.chat_manager import save_message_to_chat
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
                from utils.chat_manager import save_message_to_chat
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
            return jsonify(result)
            
        except Exception as e:
            error_msg = f"Query processing failed: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                "success": False,
                "error": error_msg,
                "processing_mode": "error"
            }), 500

    return query_bp