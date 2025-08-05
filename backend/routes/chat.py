from flask import Blueprint, request, jsonify
import logging

# Create blueprint
chat_bp = Blueprint('chat', __name__)

logger = logging.getLogger(__name__)

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
            return jsonify({"chats": chats})
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
            return jsonify(chat)
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