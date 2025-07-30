from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Create blueprint
conversation_bp = Blueprint('conversation_management', __name__, url_prefix='/api')

def init_conversation_routes(chat_service):
    """Initialize conversation routes with chat service"""
    
    @conversation_bp.route('/chats', methods=['GET'])
    def get_chat_sessions_endpoint():
        """Get all chat sessions with optional filtering"""
        try:
            # Get query parameters
            limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
            offset = int(request.args.get('offset', 0))
            status_filter = request.args.get('status')  # active, archived, deleted
            
            chats = chat_service.get_all_chat_sessions(limit=limit, offset=offset, status_filter=status_filter)
            
            # Calculate summary stats
            total_chats = len(chats)
            active_chats = len([c for c in chats if c.get('status') == 'active'])
            
            return jsonify({
                "success": True,
                "chats": chats,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "returned": len(chats)
                },
                "summary": {
                    "total_returned": total_chats,
                    "active_chats": active_chats,
                    "filter_applied": status_filter
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get chat sessions: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to retrieve chat sessions",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats', methods=['POST'])
    def create_chat_session_endpoint():
        """Create a new chat session"""
        try:
            data = request.get_json() or {}
            
            title = data.get('title')
            category = data.get('category', 'conversational')
            first_message = data.get('first_message')
            
            # Auto-generate title from first message if not provided
            if not title and first_message:
                title = chat_service.auto_generate_chat_title(first_message)
            
            chat_id = chat_service.create_new_chat_session(title=title, category=category)
            
            if chat_id:
                # If there's a first message, save it
                if first_message:
                    message_data = {
                        'type': 'user',
                        'content': first_message,
                        'timestamp': datetime.now(timezone.utc)
                    }
                    chat_service.save_message_to_chat(chat_id, message_data)
                
                # Return the created chat
                chat = chat_service.get_chat_session(chat_id)
                
                return jsonify({
                    "success": True,
                    "chat_id": chat_id,
                    "chat": chat,
                    "message": "Chat session created successfully"
                }), 201
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to create chat session"
                }), 500
                
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to create chat session",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats/<chat_id>', methods=['GET'])
    def get_chat_session_endpoint(chat_id):
        """Get a specific chat session by ID"""
        try:
            chat = chat_service.get_chat_session(chat_id)
            
            if chat:
                return jsonify({
                    "success": True,
                    "chat": chat
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Chat session not found"
                }), 404
                
        except Exception as e:
            logger.error(f"Failed to get chat session {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to retrieve chat session",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats/<chat_id>/messages', methods=['POST'])
    def add_message_to_chat_endpoint(chat_id):
        """Add a new message to an existing chat session"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "error": "Message data is required"
                }), 400
            
            message_type = data.get('type', 'user')  # user, assistant, system
            content = data.get('content', '')
            
            if not content:
                return jsonify({
                    "success": False,
                    "error": "Message content is required"
                }), 400
            
            # Build message data
            message_data = {
                'type': message_type,
                'content': content,
                'timestamp': datetime.now(timezone.utc)
            }
            
            # Add optional fields if provided
            if 'chart_data' in data:
                message_data['chart_data'] = data['chart_data']
            
            if 'validation' in data:
                message_data['validation'] = data['validation']
            
            if 'insights' in data:
                message_data['insights'] = data['insights']
            
            if 'recommendations' in data:
                message_data['recommendations'] = data['recommendations']
            
            if 'query_response' in data:
                message_data['query_response'] = data['query_response']
            
            # Save the message
            success = chat_service.save_message_to_chat(chat_id, message_data)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Message added successfully",
                    "message_id": message_data.get('message_id')
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to add message to chat"
                }), 400
                
        except Exception as e:
            logger.error(f"Failed to add message to chat {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to add message",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats/<chat_id>', methods=['PUT'])
    def update_chat_session_endpoint(chat_id):
        """Update chat session metadata (title, status, etc.)"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "success": False,
                    "error": "Update data is required"
                }), 400
            
            # Only allow certain fields to be updated
            allowed_updates = ['title', 'status', 'category']
            updates = {}
            
            for field in allowed_updates:
                if field in data:
                    updates[field] = data[field]
            
            if not updates:
                return jsonify({
                    "success": False,
                    "error": "No valid fields to update"
                }), 400
            
            success = chat_service.update_chat_session(chat_id, updates)
            
            if success:
                # Return updated chat
                updated_chat = chat_service.get_chat_session(chat_id)
                return jsonify({
                    "success": True,
                    "message": "Chat session updated successfully",
                    "chat": updated_chat
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Chat session not found or update failed"
                }), 404
                
        except Exception as e:
            logger.error(f"Failed to update chat session {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to update chat session",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats/<chat_id>', methods=['DELETE'])
    def delete_chat_session_endpoint(chat_id):
        """Delete a chat session (soft delete by default)"""
        try:
            # Check if it should be a hard delete
            hard_delete = request.args.get('hard', 'false').lower() == 'true'
            
            success = chat_service.delete_chat_session(chat_id, soft_delete=not hard_delete)
            
            if success:
                delete_type = "permanently deleted" if hard_delete else "archived"
                return jsonify({
                    "success": True,
                    "message": f"Chat session {delete_type} successfully"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Chat session not found"
                }), 404
                
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to delete chat session",
                "details": str(e)
            }), 500

    @conversation_bp.route('/chats/stats', methods=['GET'])
    def get_chat_statistics():
        """Get chat system statistics"""
        try:
            stats = chat_service.get_chat_statistics()
            
            if stats:
                return jsonify({
                    "success": True,
                    "statistics": stats
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to retrieve chat statistics"
                }), 500
                
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to retrieve chat statistics",
                "details": str(e)
            }), 500

    return conversation_bp