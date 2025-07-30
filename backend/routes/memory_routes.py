from flask import Blueprint, request, jsonify
import asyncio
import logging

logger = logging.getLogger(__name__)

# Create blueprint
memory_bp = Blueprint('memory', __name__, url_prefix='/api')

def init_memory_routes(memory_service):
    """Initialize memory routes with memory service"""
    
    @memory_bp.route('/memory/stats/<chat_id>', methods=['GET'])
    def get_memory_stats(chat_id):
        """Get memory statistics for a specific chat"""
        if not memory_service or not memory_service.is_available():
            return jsonify({"error": "Memory RAG not available"}), 503
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stats = loop.run_until_complete(memory_service.get_memory_stats(chat_id))
                
                if stats is not None:
                    return jsonify({
                        "success": True,
                        "chat_id": chat_id,
                        "memory_stats": stats
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to retrieve memory stats"
                    }), 500
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to get memory stats for {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @memory_bp.route('/memory/search/<chat_id>', methods=['POST'])
    def search_memories(chat_id):
        """Search memories in a specific chat"""
        if not memory_service or not memory_service.is_available():
            return jsonify({"error": "Memory RAG not available"}), 503
        
        try:
            data = request.get_json()
            search_query = data.get('query', '')
            limit = data.get('limit', 10)
            
            if not search_query:
                return jsonify({"error": "Search query required"}), 400
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                memory_data = loop.run_until_complete(
                    memory_service.search_memories(chat_id, search_query, limit)
                )
                
                if memory_data is not None:
                    return jsonify({
                        "success": True,
                        "search_query": search_query,
                        "results_count": len(memory_data),
                        "memories": memory_data
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to search memories"
                    }), 500
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Failed to search memories for {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    return memory_bp