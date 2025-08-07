from flask import Blueprint, request, jsonify
import logging
import math
from bson import ObjectId

# Create blueprint
chat_bp = Blueprint('chat', __name__)

logger = logging.getLogger(__name__)

def convert_objectid_to_str(obj):
    """Convert ObjectId objects to strings and handle NaN values for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, float) and math.isnan(obj):
        return None  # Convert NaN to null for JSON compatibility
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    return obj

def init_chat_routes(db, mongodb_available):
    """Initialize chat routes with dependencies"""
    
    @chat_bp.route('/api/chats', methods=['GET'])
    def get_chats():
        """Get all chat sessions"""
        if not mongodb_available:
            return jsonify({"error": "Database not available"}), 503
        
        from utils.chat_manager import get_all_chats
        chats = get_all_chats(db)
        if chats is not None:
            cleaned_chats = convert_objectid_to_str({"chats": chats})
            return jsonify(cleaned_chats)
        else:
            return jsonify({"error": "Failed to retrieve chats"}), 500

    @chat_bp.route('/api/chats', methods=['POST'])
    def create_chat():
        """Create a new chat session"""
        if not mongodb_available:
            return jsonify({"error": "Database not available"}), 503
        
        try:
            data = request.get_json() or {}
            title = data.get('title')
            category = data.get('category', 'conversational')
            
            from utils.chat_manager import create_new_chat_session
            chat_id = create_new_chat_session(db, title, category)
            
            if chat_id:
                return jsonify({"chat_id": chat_id, "success": True})
            else:
                return jsonify({"error": "Failed to create chat"}), 500
                
        except Exception as e:
            logger.error(f"Failed to create chat: {e}")
            return jsonify({"error": "Failed to create chat"}), 500

    @chat_bp.route('/api/chats/<chat_id>', methods=['GET'])
    def get_chat(chat_id):
        """Get specific chat session with messages"""
        if not mongodb_available:
            return jsonify({"error": "Database not available"}), 503
        
        from utils.chat_manager import get_chat_by_id
        chat = get_chat_by_id(db, chat_id)
        if chat is not None:
            cleaned_chat = convert_objectid_to_str(chat)
            return jsonify(cleaned_chat)
        else:
            return jsonify({"error": "Chat not found"}), 404

    @chat_bp.route('/api/chats/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id):
        """Delete a chat session"""
        if not mongodb_available:
            return jsonify({"error": "Database not available"}), 503
        
        from utils.chat_manager import delete_chat_session
        if delete_chat_session(db, chat_id):
            return jsonify({"success": True, "message": "Chat deleted"})
        else:
            return jsonify({"error": "Chat not found"}), 404

    return chat_bp