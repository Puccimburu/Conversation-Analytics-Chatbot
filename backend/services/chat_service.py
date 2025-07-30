import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId

logger = logging.getLogger(__name__)

class ChatService:
    """Service for managing chat sessions and messages"""
    
    def __init__(self, database):
        self.db = database
        self.mongodb_available = database is not None
        
        # Initialize indexes if database is available
        if self.mongodb_available:
            self._ensure_chat_indexes()
    
    def _ensure_chat_indexes(self):
        """Create indexes for chat collection for optimal performance"""
        try:
            chat_collection = self.db.chat_sessions
            
            # Create indexes for performance
            chat_collection.create_index("chat_id", unique=True)
            chat_collection.create_index("created_at")
            chat_collection.create_index("updated_at")
            chat_collection.create_index("status")
            
            logger.info("✅ Chat collection indexes ensured")
            return True
        except Exception as e:
            logger.error(f"Failed to create chat indexes: {e}")
            return False
    
    def generate_chat_id(self):
        """Generate unique chat ID with timestamp"""
        return f"chat_{int(time.time() * 1000)}"
    
    def generate_message_id(self):
        """Generate unique message ID"""
        return f"msg_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"
    
    def create_new_chat_session(self, title=None, category="conversational"):
        """Create a new chat session in MongoDB"""
        if not self.mongodb_available:
            return None
        
        try:
            chat_id = self.generate_chat_id()
            now = datetime.now(timezone.utc)
            
            # Auto-generate title if not provided
            if not title:
                title = f"Chat Session {now.strftime('%m/%d %H:%M')}"
            
            chat_doc = {
                'chat_id': chat_id,
                'title': title,
                'category': category,
                'created_at': now,
                'updated_at': now,
                'status': 'active',
                'messages': [],
                'metadata': {
                    'total_messages': 0,
                    'last_activity': now,
                    'user_id': None,  # For future user authentication
                    'tags': [],
                    'is_favorite': False
                }
            }
            
            result = self.db.chat_sessions.insert_one(chat_doc)
            if result.inserted_id:
                logger.info(f"✅ Created new chat session: {chat_id}")
                return chat_id
            else:
                logger.error("Failed to insert chat session")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return None
    
    def save_message_to_chat(self, chat_id, message_data):
        """Save message to existing chat session"""
        if not self.mongodb_available:
            return False
        
        try:
            # Add message ID and timestamp if not present
            if 'message_id' not in message_data:
                message_data['message_id'] = self.generate_message_id()
            
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.now(timezone.utc)
            
            # Update the chat session
            result = self.db.chat_sessions.update_one(
                {'chat_id': chat_id},
                {
                    '$push': {'messages': message_data},
                    '$set': {
                        'updated_at': datetime.now(timezone.utc),
                        'metadata.last_activity': datetime.now(timezone.utc)
                    },
                    '$inc': {'metadata.total_messages': 1}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Saved message to chat {chat_id}")
                return True
            else:
                logger.warning(f"Chat {chat_id} not found for message save")
                return False
                
        except Exception as e:
            logger.error(f"Failed to save message to chat {chat_id}: {e}")
            return False
    
    def get_chat_session(self, chat_id):
        """Get a specific chat session by ID"""
        if not self.mongodb_available:
            return None
        
        try:
            chat = self.db.chat_sessions.find_one({'chat_id': chat_id})
            if chat:
                # Convert ObjectId to string for JSON serialization
                chat['_id'] = str(chat['_id'])
                logger.info(f"✅ Retrieved chat session: {chat_id}")
                return chat
            else:
                logger.warning(f"Chat session not found: {chat_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get chat session {chat_id}: {e}")
            return None
    
    def get_all_chat_sessions(self, limit=50, offset=0, status_filter=None):
        """Get all chat sessions with pagination"""
        if not self.mongodb_available:
            return []
        
        try:
            # Build query filter
            query_filter = {}
            if status_filter:
                query_filter['status'] = status_filter
            
            # Get chats sorted by last activity (most recent first)
            chats = list(self.db.chat_sessions.find(query_filter)
                        .sort('updated_at', -1)
                        .skip(offset)
                        .limit(limit))
            
            # Convert ObjectIds to strings
            for chat in chats:
                chat['_id'] = str(chat['_id'])
            
            logger.info(f"✅ Retrieved {len(chats)} chat sessions")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chat sessions: {e}")
            return []
    
    def update_chat_session(self, chat_id, updates):
        """Update chat session metadata"""
        if not self.mongodb_available:
            return False
        
        try:
            # Add updated timestamp
            updates['updated_at'] = datetime.now(timezone.utc)
            
            result = self.db.chat_sessions.update_one(
                {'chat_id': chat_id},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated chat session: {chat_id}")
                return True
            else:
                logger.warning(f"Chat session not found for update: {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update chat session {chat_id}: {e}")
            return False
    
    def delete_chat_session(self, chat_id, soft_delete=True):
        """Delete or archive a chat session"""
        if not self.mongodb_available:
            return False
        
        try:
            if soft_delete:
                # Soft delete - just change status to deleted
                result = self.db.chat_sessions.update_one(
                    {'chat_id': chat_id},
                    {
                        '$set': {
                            'status': 'deleted',
                            'updated_at': datetime.now(timezone.utc)
                        }
                    }
                )
            else:
                # Hard delete - remove from database
                result = self.db.chat_sessions.delete_one({'chat_id': chat_id})
            
            if result.modified_count > 0 or result.deleted_count > 0:
                delete_type = "soft deleted" if soft_delete else "permanently deleted"
                logger.info(f"✅ Chat session {delete_type}: {chat_id}")
                return True
            else:
                logger.warning(f"Chat session not found for deletion: {chat_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete chat session {chat_id}: {e}")
            return False
    
    def auto_generate_chat_title(self, first_message):
        """Auto-generate a meaningful chat title from the first message"""
        if not first_message:
            return f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
        
        # Clean and truncate the message
        title = first_message.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['show me', 'what is', 'what are', 'how do', 'can you', 'please']
        title_lower = title.lower()
        
        for prefix in prefixes_to_remove:
            if title_lower.startswith(prefix):
                title = title[len(prefix):].strip()
                break
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        # Truncate if too long
        if len(title) > 50:
            title = title[:47] + "..."
        
        return title if title else f"Chat {datetime.now().strftime('%m/%d %H:%M')}"
    
    def get_chat_statistics(self):
        """Get comprehensive chat system statistics"""
        if not self.mongodb_available:
            return None
        
        try:
            # Get basic stats
            total_chats = self.db.chat_sessions.count_documents({})
            active_chats = self.db.chat_sessions.count_documents({"status": "active"})
            archived_chats = self.db.chat_sessions.count_documents({"status": "deleted"})
            
            # Get recent activity
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            recent_chats = self.db.chat_sessions.count_documents({
                "updated_at": {"$gte": one_day_ago}
            })
            
            # Get message statistics
            pipeline = [
                {"$match": {"status": {"$ne": "deleted"}}},
                {"$project": {
                    "message_count": {"$size": "$messages"},
                    "created_at": 1,
                    "updated_at": 1
                }},
                {"$group": {
                    "_id": None,
                    "total_messages": {"$sum": "$message_count"},
                    "avg_messages_per_chat": {"$avg": "$message_count"},
                    "max_messages": {"$max": "$message_count"}
                }}
            ]
            
            message_stats = list(self.db.chat_sessions.aggregate(pipeline))
            message_data = message_stats[0] if message_stats else {
                "total_messages": 0,
                "avg_messages_per_chat": 0,
                "max_messages": 0
            }
            
            return {
                "total_chats": total_chats,
                "active_chats": active_chats,
                "archived_chats": archived_chats,
                "recent_activity_24h": recent_chats,
                "message_statistics": {
                    "total_messages": message_data["total_messages"],
                    "average_messages_per_chat": round(message_data["avg_messages_per_chat"], 2),
                    "max_messages_in_chat": message_data["max_messages"]
                },
                "system_health": {
                    "database_available": True,
                    "chat_indexes_ready": True,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return None