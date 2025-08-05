from flask import Blueprint, jsonify
from datetime import datetime, timezone
import logging

# Create blueprint
system_bp = Blueprint('system', __name__)

logger = logging.getLogger(__name__)

def init_system_routes(db, mongodb_available, gemini_available, two_stage_processor, memory_enhanced_processor, MONGODB_URI):
    """Initialize system routes with dependencies"""
    
    @system_bp.route('/api/health', methods=['GET'])
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

    @system_bp.route('/api/system/info', methods=['GET'])
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

    @system_bp.route('/api/debug/collections', methods=['GET'])
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

    return system_bp