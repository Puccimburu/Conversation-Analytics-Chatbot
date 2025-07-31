# backend/utils/chat_manager.py

import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Get a logger for this module
logger = logging.getLogger(__name__)

# --- ID Generation ---

def generate_chat_id() -> str:
    """Generate a unique chat ID using the current timestamp."""
    return f"chat_{int(time.time() * 1000)}"

def generate_message_id() -> str:
    """Generate a unique message ID."""
    # Using a hash of the time makes it even less likely to have collisions
    return f"msg_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"

# --- Database Operations ---

def ensure_chat_indexes(db_client: Any) -> bool:
    """
    Creates necessary indexes on the chat_sessions collection for performance.
    
    Args:
        db_client: The database client instance (e.g., from pymongo).
    """
    if db_client is None:
        logger.warning("Database client is not available. Cannot ensure chat indexes.")
        return False
    
    try:
        chat_collection = db_client.chat_sessions
        
        # Create indexes for fast lookups and sorting
        chat_collection.create_index("chat_id", unique=True)
        chat_collection.create_index("created_at")
        chat_collection.create_index("updated_at")
        chat_collection.create_index("status")
        
        logger.info("✅ Chat collection indexes ensured successfully.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create chat indexes: {e}")
        return False

def create_new_chat_session(db_client: Any, title: Optional[str] = None, category: str = "conversational") -> Optional[str]:
    """
    Creates a new chat session document in MongoDB.
    
    Args:
        db_client: The database client instance.
        title: Optional title for the chat.
        category: The category of the chat.
        
    Returns:
        The chat_id of the newly created session, or None if it fails.
    """
    if db_client is None:
        logger.warning("Database client is not available. Cannot create chat session.")
        return None
    
    try:
        chat_id = generate_chat_id()
        now = datetime.now(timezone.utc)
        
        # Auto-generate a descriptive title if one isn't provided
        if not title:
            title = f"Chat Session {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
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
                'user_id': None,  # Can be populated later
                'tags': [],
                'is_favorite': False
            }
        }
        
        result = db_client.chat_sessions.insert_one(chat_doc)
        if result.inserted_id:
            logger.info(f"✅ Created new chat session in DB: {chat_id}")
            return chat_id
        else:
            logger.error("❌ Failed to insert new chat session document.")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to create chat session due to an exception: {e}")
        return None

def save_message_to_chat(db_client: Any, chat_id: str, message_data: Dict[str, Any]) -> bool:
    """
    Saves a message to an existing chat session by its chat_id.
    
    Args:
        db_client: The database client instance.
        chat_id: The ID of the chat to update.
        message_data: A dictionary containing the message details.
        
    Returns:
        True if the message was saved successfully, False otherwise.
    """
    if db_client is None:
        logger.warning(f"Database client not available. Cannot save message to chat {chat_id}.")
        return False
    
    try:
        # Automatically add a message_id and timestamp if they don't exist
        if 'message_id' not in message_data:
            message_data['message_id'] = generate_message_id()
        
        if 'timestamp' not in message_data:
            message_data['timestamp'] = datetime.now(timezone.utc)
        
        # The update operation to perform on the document
        update_operation = {
            '$push': {'messages': message_data},
            '$set': {
                'updated_at': datetime.now(timezone.utc),
                'metadata.last_activity': datetime.now(timezone.utc)
            },
            '$inc': {'metadata.total_messages': 1}
        }
        
        result = db_client.chat_sessions.update_one(
            {'chat_id': chat_id},
            update_operation
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Saved message to chat {chat_id}")
            return True
        else:
            logger.warning(f"⚠️ Chat {chat_id} not found. Could not save message.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to save message to chat {chat_id}: {e}")
        return False

def get_all_chats(db_client: Any, limit: int = 50) -> Optional[List[Dict]]:
    """
    Retrieves all chat sessions with basic metadata.
    
    Args:
        db_client: The database client instance.
        limit: Maximum number of chats to retrieve.
        
    Returns:
        List of chat documents or None if failed.
    """
    if db_client is None:
        logger.warning("Database client not available. Cannot get chats.")
        return None
    
    try:
        # Get recent chat sessions
        chats = list(db_client.chat_sessions.find({}, {
            'chat_id': 1, 
            'title': 1, 
            'created_at': 1, 
            'updated_at': 1,
            'metadata.total_messages': 1,
            'status': 1
        }).sort('updated_at', -1).limit(limit))
        
        # Convert ObjectIds and datetimes to strings
        for chat in chats:
            chat['_id'] = str(chat['_id'])
            if isinstance(chat.get('created_at'), datetime):
                chat['created_at'] = chat['created_at'].isoformat()
            if isinstance(chat.get('updated_at'), datetime):
                chat['updated_at'] = chat['updated_at'].isoformat()
        
        logger.info(f"✅ Retrieved {len(chats)} chat sessions")
        return chats
        
    except Exception as e:
        logger.error(f"❌ Failed to get chats: {e}")
        return None

def get_chat_by_id(db_client: Any, chat_id: str) -> Optional[Dict]:
    """
    Retrieves a specific chat session with all messages.
    
    Args:
        db_client: The database client instance.
        chat_id: The ID of the chat to retrieve.
        
    Returns:
        Chat document with messages or None if not found.
    """
    if db_client is None:
        logger.warning("Database client not available. Cannot get chat.")
        return None
    
    try:
        chat = db_client.chat_sessions.find_one({'chat_id': chat_id})
        
        if not chat:
            logger.warning(f"⚠️ Chat {chat_id} not found")
            return None
        
        # Convert ObjectId and datetime objects
        chat['_id'] = str(chat['_id'])
        if isinstance(chat.get('created_at'), datetime):
            chat['created_at'] = chat['created_at'].isoformat()
        if isinstance(chat.get('updated_at'), datetime):
            chat['updated_at'] = chat['updated_at'].isoformat()
            
        # Convert message timestamps
        for message in chat.get('messages', []):
            if isinstance(message.get('timestamp'), datetime):
                message['timestamp'] = message['timestamp'].isoformat()
        
        logger.info(f"✅ Retrieved chat {chat_id} with {len(chat.get('messages', []))} messages")
        return chat
        
    except Exception as e:
        logger.error(f"❌ Failed to get chat {chat_id}: {e}")
        return None

def delete_chat_session(db_client: Any, chat_id: str) -> bool:
    """
    Deletes a chat session and all its messages.
    
    Args:
        db_client: The database client instance.
        chat_id: The ID of the chat to delete.
        
    Returns:
        True if deleted successfully, False otherwise.
    """
    if db_client is None:
        logger.warning("Database client not available. Cannot delete chat.")
        return False
    
    try:
        result = db_client.chat_sessions.delete_one({'chat_id': chat_id})
        
        if result.deleted_count > 0:
            logger.info(f"✅ Deleted chat session {chat_id}")
            return True
        else:
            logger.warning(f"⚠️ Chat {chat_id} not found for deletion")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to delete chat {chat_id}: {e}")
        return False

def get_chat_history(db_client: Any, chat_id: str) -> Optional[List[Dict]]:
    """
    Retrieves all messages for a given chat session.
    
    Args:
        db_client: The database client instance.
        chat_id: The ID of the chat.
        
    Returns:
        List of messages or None if failed.
    """
    chat = get_chat_by_id(db_client, chat_id)
    if chat:
        return chat.get('messages', [])
    return None

def update_chat_metadata(db_client: Any, chat_id: str, updates: Dict[str, Any]) -> bool:
    """
    Updates the metadata of a chat session (e.g., title, tags).
    
    Args:
        db_client: The database client instance.
        chat_id: The ID of the chat to update.
        updates: Dictionary of fields to update.
        
    Returns:
        True if updated successfully, False otherwise.
    """
    if db_client is None:
        logger.warning("Database client not available. Cannot update chat metadata.")
        return False
    
    try:
        # Prepare update operation
        update_op = {
            '$set': {
                'updated_at': datetime.now(timezone.utc)
            }
        }
        
        # Add user-specified updates
        for key, value in updates.items():
            if key in ['title', 'category', 'status']:
                update_op['$set'][key] = value
            elif key.startswith('metadata.'):
                update_op['$set'][key] = value
        
        result = db_client.chat_sessions.update_one(
            {'chat_id': chat_id},
            update_op
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ Updated metadata for chat {chat_id}")
            return True
        else:
            logger.warning(f"⚠️ Chat {chat_id} not found for metadata update")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to update chat metadata {chat_id}: {e}")
        return False