from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime, timedelta, timezone
import pymongo
import json
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple
import re
import time
from bson import ObjectId
from utils.analytics_processor import TwoStageAnalyticsProcessor
from utils.memory_rag import MemoryRAGManager, MemoryEnhancedProcessor

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
print("PERFECTED AI ANALYTICS - BULLETPROOF GEMINI TWO-STAGE + CHAT")
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

# ============================================================================
# NEW: CHAT SESSION MANAGEMENT FUNCTIONS
# ============================================================================

def generate_chat_id():
    """Generate unique chat ID with timestamp"""
    return f"chat_{int(time.time() * 1000)}"

def generate_message_id():
    """Generate unique message ID"""
    return f"msg_{int(time.time() * 1000)}_{hash(str(time.time())) % 10000}"

def ensure_chat_indexes():
    """Create indexes for chat collection for optimal performance"""
    if not mongodb_available or db is None:
        return False
    
    try:
        chat_collection = db.chat_sessions
        
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

def create_new_chat_session(title=None, category="conversational"):
    """Create a new chat session in MongoDB"""
    if not mongodb_available or db is None:
        return None
    
    try:
        chat_id = generate_chat_id()
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
        
        result = db.chat_sessions.insert_one(chat_doc)
        if result.inserted_id:
            logger.info(f"✅ Created new chat session: {chat_id}")
            return chat_id
        else:
            logger.error("Failed to insert chat session")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create chat session: {e}")
        return None

def save_message_to_chat(chat_id, message_data):
    """Save message to existing chat session"""
    if not mongodb_available or db is None:
        return False
    
    try:
        # Add message ID and timestamp if not present
        if 'message_id' not in message_data:
            message_data['message_id'] = generate_message_id()
        
        if 'timestamp' not in message_data:
            message_data['timestamp'] = datetime.now(timezone.utc)
        
        # Update the chat session
        result = db.chat_sessions.update_one(
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

def get_chat_session(chat_id):
    """Get a specific chat session by ID"""
    if not mongodb_available or db is None:
        return None
    
    try:
        chat = db.chat_sessions.find_one({'chat_id': chat_id})
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

def get_all_chat_sessions(limit=50, offset=0, status_filter=None):
    """Get all chat sessions with pagination"""
    if not mongodb_available or db is None:
        return []
    
    try:
        # Build query filter
        query_filter = {}
        if status_filter:
            query_filter['status'] = status_filter
        
        # Get chats sorted by last activity (most recent first)
        chats = list(db.chat_sessions.find(query_filter)
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

def update_chat_session(chat_id, updates):
    """Update chat session metadata"""
    if not mongodb_available or db is None:
        return False
    
    try:
        # Add updated timestamp
        updates['updated_at'] = datetime.now(timezone.utc)
        
        result = db.chat_sessions.update_one(
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

def delete_chat_session(chat_id, soft_delete=True):
    """Delete or archive a chat session"""
    if not mongodb_available or db is None:
        return False
    
    try:
        if soft_delete:
            # Soft delete - just change status to deleted
            result = db.chat_sessions.update_one(
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
            result = db.chat_sessions.delete_one({'chat_id': chat_id})
        
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

def auto_generate_chat_title(first_message):
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

# Initialize chat collection indexes on startup
if mongodb_available:
    ensure_chat_indexes()

# ============================================================================
# BULLETPROOF GEMINI CLIENT
# ============================================================================

class BulletproofGeminiClient:
    """Perfected Gemini client with enhanced reliability"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test the connection
        try:
            test_response = self.model.generate_content("Test")
            self.available = True
            logger.info("✅ Gemini client initialized and tested")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
    
    async def generate_query(self, user_question: str, schema_info: Dict, max_retries: int = 5) -> Dict:
        """Generate MongoDB query with enhanced retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        # Enhanced prompt with more examples and better instructions
        prompt = self._build_enhanced_query_prompt(user_question, schema_info)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Gemini Stage 1 - Query Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.05,  # Very low for consistency
                        max_output_tokens=3000,
                        top_p=0.7
                    )
                )
                
                if response and response.text:
                    parsed_result = self._extract_json_from_response(response.text)
                    
                    if parsed_result and self._validate_and_fix_query_response(parsed_result):
                        logger.info(f"✅ Gemini query generation successful on attempt {attempt + 1}")
                        return {"success": True, "data": parsed_result}
                    else:
                        logger.warning(f"Invalid response on attempt {attempt + 1}: {response.text[:200]}")
                
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 8)  # Exponential backoff, max 8 seconds
                    await asyncio.sleep(delay)
        
        logger.error("❌ Gemini query generation failed after all retries")
        return {"success": False, "error": "Failed to generate query after retries"}
    
    async def generate_visualization(self, user_question: str, raw_data: List[Dict], query_context: Dict, max_retries: int = 5) -> Dict:
        """Generate visualization with enhanced debugging and retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        # Enhanced prompt for better visualizations
        prompt = self._build_enhanced_visualization_prompt(user_question, raw_data, query_context)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📊 Gemini Stage 2 - Visualization Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.05,  # Even lower temperature for more consistent JSON
                        max_output_tokens=2000,
                        top_p=0.7,  # More focused responses
                        top_k=40
                    )
                )
                
                if response and response.text:
                    # Log the raw response for debugging
                    raw_response = response.text.strip()
                    logger.info(f"🔍 Gemini Stage 2 raw response (attempt {attempt + 1}): {raw_response[:300]}...")
                    
                    parsed_result = self._extract_json_from_response(raw_response)
                    
                    if parsed_result:
                        logger.info(f"✅ JSON extraction successful: {list(parsed_result.keys())}")
                        
                        if self._validate_and_fix_visualization_response(parsed_result, raw_data, user_question):
                            logger.info(f"✅ Gemini visualization generation successful on attempt {attempt + 1}")
                            return {"success": True, "data": parsed_result}
                        else:
                            logger.warning(f"❌ Validation failed on attempt {attempt + 1}, parsed keys: {list(parsed_result.keys())}")
                    else:
                        logger.warning(f"❌ JSON extraction failed on attempt {attempt + 1}")
                        logger.debug(f"Full response text: {raw_response}")
                else:
                    logger.warning(f"❌ Empty response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Gemini visualization attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < max_retries - 1:
                delay = min(2 ** attempt, 8)
                logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error("❌ Gemini visualization generation failed after all retries")
        return {"success": False, "error": "Failed to generate visualization after retries"}
    
    def _build_enhanced_query_prompt(self, user_question: str, schema_info: Dict) -> str:
        """Build comprehensive prompt with many examples"""
        return f"""You are a MongoDB aggregation expert specializing in AI Operations & Document Intelligence analytics.

USER QUESTION: "{user_question}"

AVAILABLE COLLECTIONS & KEY FIELDS:
- costevalutionforllm: _id, batchId, userId, modelType, operationType, inputTokens, outputTokens, totalCost, timestamp
- documentextractions: _id, Value, Type, Name, Confidence_Score, Status, batchId, fileId  
- obligationextractions: _id, name, description, obligationType, confidence, category, severity
- agent_activity: _id, Agent, Contract_Name, Outcome, Timestamp, duration
- batches: _id, batchId, batchType, status, totalItems, processedItems, failedItems
- users: _id, userId, emailId, name, role, createdAt
- conversations: _id, conversationId, userId, title, messages, createdAt

QUERY PATTERN EXAMPLES:
1. SIMPLE LISTS: "Show all prompts" → [{{"$limit": 50}}]
2. COUNTS: "Count total users" → [{{"$group": {{"_id": null, "count": {{"$sum": 1}}}}}}]
3. TOTALS: "Total cost" → [{{"$group": {{"_id": null, "total": {{"$sum": "$totalCost"}}}}}}]
4. GROUPING: "By Agent" → [{{"$group": {{"_id": "$Agent", "count": {{"$sum": 1}}}}}}, {{"$sort": {{"count": -1}}}}]
5. FILTERING: "Confidence > 0.8" → [{{"$match": {{"Confidence_Score": {{"$gt": 0.8}}}}}}, {{"$limit": 50}}]
6. TOP N: "Top 5 batches" → [{{"$sort": {{"totalItems": -1}}}}, {{"$limit": 5}}]
7. RANGE QUERIES: "Created after Jan 2025" → [{{"$match": {{"createdAt": {{"$gte": "2025-01-01T00:00:00Z"}}}}}}, {{"$limit": 50}}]
8. TIME SERIES: "Costs over time" → [{{"$group": {{"_id": {{"$dateToString": {{"format": "%Y-%m-%d", "date": "$timestamp"}}}}, "totalCost": {{"$sum": "$totalCost"}}}}}}, {{"$sort": {{"_id": 1}}}}]
9. MONTHLY TRENDS: "Monthly trends" → [{{"$group": {{"_id": {{"$dateToString": {{"format": "%Y-%m", "date": "$timestamp"}}}}, "count": {{"$sum": 1}}}}}}, {{"$sort": {{"_id": 1}}}}]
10. COMPLEX GROUP: "Cost by model type" → [{{"$group": {{"_id": "$modelType", "totalCost": {{"$sum": "$totalCost"}}, "count": {{"$sum": 1}}}}}}, {{"$sort": {{"totalCost": -1}}}}]

QUANTITY HANDLING:
- "Show 7 document extractions" = Use [{{"$limit": 7}}]  
- "Sample of 10 users" = Use [{{"$limit": 10}}]
- "First 5 batches" = Use [{{"$limit": 5}}]
- Always respect specific numbers in user requests

CRITICAL RULES:
- Return ONLY valid JSON, no markdown or explanations
- Use exact field names shown above (case-sensitive)
- When user specifies a number, use $limit with that exact number
- Always add {{"$limit": 100}} for lists, {{"$limit": 20}} for groups
- Sort by meaningful fields (cost DESC, count DESC, timestamp DESC)
- Choose collection based on question keywords:
  * "cost|spending|token" → costevalutionforllm
  * "document|extraction|confidence" → documentextractions  
  * "obligation|compliance|legal" → obligationextractions
  * "agent|activity|outcome" → agent_activity
  * "batch|processing" → batches
  * "user|account" → users
  * "conversation|chat" → conversations

RESPONSE FORMAT:
{{
  "collection": "exact_collection_name",
  "pipeline": [mongodb_aggregation_stages],
  "chart_hint": "bar|pie|line|doughnut|table",
  "query_intent": "brief_description"
}}

JSON only:"""

    def _build_enhanced_visualization_prompt(self, user_question: str, raw_data: List[Dict], query_context: Dict) -> str:
        """Improved visualization prompt with better instructions"""
        sample_data = raw_data[:3] if raw_data else []
        
        # Extract data structure info
        data_fields = []
        if raw_data:
            first_record = raw_data[0]
            data_fields = [k for k, v in first_record.items() if isinstance(v, (int, float))]
        
        return f"""You are an AI Operations visualization expert. Create Chart.js configs for business intelligence.

USER QUESTION: "{user_question}"
DATA RECORDS: {len(raw_data)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}

DATA ANALYSIS:
- Numeric fields available: {data_fields}
- Collection: {query_context.get('collection', 'unknown')}
- Query intent: {query_context.get('query_intent', 'unknown')}

CHART TYPE SELECTION RULES:
- Time series (dates/timestamps) → line chart
- Percentages/distributions/breakdowns → pie chart
- Parts of whole (with %), compositions → doughnut chart  
- Rankings/comparisons/counts → bar chart
- Raw data lists → table
- Single metrics → table with summary

CHART TYPE KEYWORDS:
- LINE: "over time", "trends", "daily", "monthly", "timeline", "history", "chronological", "time series"
- PIE: "percentage", "distribution", "breakdown", "composition", "what percent", "proportion", "share"  
- DOUGHNUT: "parts of", "share of", "portion of", "makeup", "constitution"
- BAR: "top", "compare", "rank", "most", "least", "count", "versus", "highest", "lowest"
- TABLE: "show all", "list", "display", "raw data", "details", "records", "entries"

🚨 CRITICAL CHART TYPE RULES - FOLLOW EXACTLY OR FAIL:
1. "show all", "list all", "display all", "get all" = chart_type MUST BE "table" 
2. "show me all", "list me all", "display me all" = chart_type MUST BE "table"
3. "table", "raw data", "details", "records", "entries" = chart_type MUST BE "table"
4. "in a table", "as a table", "table format" = chart_type MUST BE "table"
5. Time trends = "line", Percentages = "pie", Comparisons = "bar"
6. NEVER EVER use "bar" for listing/showing records - ALWAYS use "table"

⚠️ WARNING: If user wants to see records/data, chart_type = "table" ALWAYS

VISUALIZATION REQUIREMENTS:
1. Return ONLY valid JSON - no explanations or markdown
2. Extract labels from "_id" field, values from numeric fields
3. Use professional color scheme for business dashboards
4. Include actionable insights with specific numbers
5. Add recommendations for AI operations optimization

RESPONSE FORMAT:
{{
  "chart_type": "bar|pie|line|doughnut|table",
  "chart_config": {{
    "type": "chart_type_here",
    "data": {{
      "labels": [extract_from_data_id_field],
      "datasets": [{{
        "label": "meaningful_label",
        "data": [extract_numeric_values],
        "backgroundColor": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
        "borderWidth": 1
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "Descriptive Chart Title"}},
        "legend": {{"display": true, "position": "bottom"}}
      }}
    }},
    "tableData": [for_table_type_include_raw_records],
    "columns": [for_table_type_define_column_structure]
  }},
  "summary": "Found {len(raw_data)} records. Key metric: [specific number and insight]",
  
  FOR TABLE TYPE - INCLUDE THESE FIELDS:
  "tableData": [raw_data_records_with_cleaned_field_names],
  "columns": [
    {{"key": "userId", "label": "User ID", "type": "text", "width": "25%", "align": "left"}},
    {{"key": "emailId", "label": "Email", "type": "text", "width": "30%", "align": "left"}},
    {{"key": "role", "label": "Role", "type": "text", "width": "20%", "align": "left"}},
    {{"key": "createdAt", "label": "Created", "type": "date", "width": "25%", "align": "left"}}
  ],
  "insights": [
    "Data-driven insight with numbers",
    "Pattern or trend identified",
    "Performance comparison or ranking"
  ],
  "recommendations": [
    "Actionable AI operations improvement",
    "Cost optimization or efficiency suggestion"
  ]
}}

JSON only:"""

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Ultra-robust JSON extraction with extensive fallback methods"""
        try:
            cleaned_text = response_text.strip()
            logger.debug(f"Extracting JSON from: {cleaned_text[:200]}...")
            
            # Method 1: Direct JSON parsing
            try:
                result = json.loads(cleaned_text)
                if isinstance(result, dict) and len(result) > 0:
                    logger.debug("✅ Direct JSON parsing successful")
                    return result
            except json.JSONDecodeError as e:
                logger.debug(f"Direct parsing failed: {e}")
            
            # Method 2: Extract from various code block formats
            code_block_patterns = [
                r'```(?:json)?\s*(\{.*?\})\s*```',
                r'```(\{.*?\})```', 
                r'`(\{.*?\})`',
                r'JSON:\s*(\{.*?\})',
                r'Response:\s*(\{.*?\})',
                r'Result:\s*(\{.*?\})'
            ]
            
            for pattern in code_block_patterns:
                match = re.search(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        result = json.loads(match.group(1))
                        if isinstance(result, dict) and len(result) > 0:
                            logger.debug(f"✅ Code block extraction successful with pattern: {pattern}")
                            return result
                    except json.JSONDecodeError:
                        continue
            
            # Method 3: Find JSON object with proper brace matching
            brace_count = 0
            start_idx = -1
            in_string = False
            escape_next = False
            quote_char = None
            
            for i, char in enumerate(cleaned_text):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char in ['"', "'"] and not escape_next:
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                    continue
                
                if not in_string:
                    if char == '{':
                        if start_idx == -1:
                            start_idx = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            try:
                                json_str = cleaned_text[start_idx:i+1]
                                result = json.loads(json_str)
                                if isinstance(result, dict) and len(result) > 2:
                                    logger.debug("✅ Brace matching extraction successful")
                                    return result
                            except json.JSONDecodeError:
                                continue
                            finally:
                                start_idx = -1
                                brace_count = 0
            
            # Method 4: Fix common JSON issues and retry
            fixed_attempts = [
                # Remove trailing commas
                re.sub(r',(\s*[}\]])', r'\1', cleaned_text),
                # Fix single quotes
                re.sub(r"'([^']*)':", r'"\1":', cleaned_text),
                # Fix unescaped quotes in values
                re.sub(r':\s*"([^"]*)"([^",}\]])', r': "\1\2"', cleaned_text),
                # Remove extra text before/after JSON
                re.sub(r'^[^{]*(\{.*\})[^}]*$', r'\1', cleaned_text, flags=re.DOTALL)
            ]
            
            for i, fixed_text in enumerate(fixed_attempts):
                try:
                    result = json.loads(fixed_text)
                    if isinstance(result, dict) and len(result) > 0:
                        logger.debug(f"✅ JSON fixing method {i+1} successful")
                        return result
                except json.JSONDecodeError:
                    continue
            
            logger.warning("❌ All JSON extraction methods failed")
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction critical error: {e}")
            return None

    def _validate_and_fix_query_response(self, data: Dict) -> bool:
        """Validate and fix query response"""
        try:
            # Check required fields
            required_fields = ['collection', 'pipeline', 'chart_hint', 'query_intent']
            
            # Fix missing fields
            if 'collection' not in data:
                data['collection'] = 'costevalutionforllm'  # Default
            
            if 'pipeline' not in data:
                return False  # Can't fix missing pipeline
            
            if 'chart_hint' not in data:
                data['chart_hint'] = 'bar'  # Default
            
            if 'query_intent' not in data:
                data['query_intent'] = 'Data analysis query'
            
            return True
            
        except Exception as e:
            logger.error(f"Query validation error: {e}")
            return False
    
    def _validate_and_fix_visualization_response(self, data: Dict, raw_data: List[Dict], user_question: str = "") -> bool:
        """Enhanced validation with auto-fixing and logging"""
        try:
            logger.info(f"🔍 Validating visualization response: {list(data.keys())}")
            
            # Check if user explicitly requested table format
            table_keywords = ['table', 'raw data', 'in a table', 'as a table', 'table format', 'show all', 'list all', 'display all']
            force_table = any(keyword in user_question.lower() for keyword in table_keywords)
            
            if force_table:
                logger.info(f"🔄 User requested table format, ensuring full dataset table")
                data['chart_type'] = 'table'
                
                # Always create table data from full raw data when table is requested
                if raw_data:
                    table_data, columns = self._create_table_from_raw_data(raw_data)
                    if 'chart_config' not in data:
                        data['chart_config'] = {}
                    data['chart_config']['tableData'] = table_data
                    data['chart_config']['columns'] = columns
                    logger.info(f"✅ Created table with {len(table_data)} rows, {len(columns)} columns from full dataset")
                    # Update summary and insights to reflect actual data count
                    data = self._update_summary_for_full_dataset(data, table_data, user_question)
            
            # Check if Gemini generated a table but with limited data - replace with full dataset
            elif data.get('chart_type') == 'table' and raw_data:
                existing_table_data = data.get('chart_config', {}).get('tableData', [])
                if len(existing_table_data) < len(raw_data):
                    logger.info(f"🔄 Replacing limited table data ({len(existing_table_data)} rows) with full dataset ({len(raw_data)} rows)")
                    table_data, columns = self._create_table_from_raw_data(raw_data)
                    if 'chart_config' not in data:
                        data['chart_config'] = {}
                    data['chart_config']['tableData'] = table_data
                    data['chart_config']['columns'] = columns
                    logger.info(f"✅ Updated table with {len(table_data)} rows, {len(columns)} columns from full dataset")
                    # Update summary and insights to reflect actual data count
                    data = self._update_summary_for_full_dataset(data, table_data, user_question)
            
            # More flexible validation with auto-fixing
            required_fields = ['chart_type', 'chart_config', 'summary']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"Missing fields: {missing_fields}, attempting to fix...")
                
                # Auto-fix missing fields
                if 'chart_type' not in data:
                    data['chart_type'] = 'bar'  # Default
                    logger.info("✅ Fixed: Added default chart_type 'bar'")
                
                if 'summary' not in data:
                    record_count = len(raw_data) if raw_data else 0
                    data_type = self._determine_data_type_from_question(user_question)
                    data['summary'] = f"Found {record_count} records. Analysis of {record_count} {data_type} completed successfully with {data.get('chart_type', 'chart')} visualization."
                    logger.info("✅ Fixed: Added detailed summary")
                
                if 'chart_config' not in data:
                    data['chart_config'] = self._create_basic_chart_config(data['chart_type'], raw_data)
                    logger.info("✅ Fixed: Created basic chart config")
            
            # Add default insights and recommendations if missing
            if 'insights' not in data:
                data['insights'] = [
                    f"Successfully analyzed {len(raw_data)} data points",
                    "Data processing completed with AI assistance"
                ]
                logger.info("✅ Fixed: Added default insights")
            
            if 'recommendations' not in data:
                data['recommendations'] = [
                    "Review the data patterns for actionable insights",
                    "Consider strategic implications of the analysis"
                ]
                logger.info("✅ Fixed: Added default recommendations")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Visualization validation error: {e}")
            return False
    
    def _create_table_from_raw_data(self, raw_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Create structured table data and columns from raw MongoDB results"""
        if not raw_data:
            return [], []
            
        # Get field names from first record
        first_record = raw_data[0]
        field_names = list(first_record.keys())
        
        logger.info(f"🔍 Table creation debug - Raw field names: {field_names}")
        
        # Create column definitions with proper labels and types
        columns = []
        for field_name in field_names:
            if field_name == '_id':
                continue  # Skip MongoDB ObjectId
                
            # Determine column type and label
            label = self._format_field_name(field_name)
            field_type = self._determine_field_type(field_name, first_record.get(field_name))
            width = "25%" if len(field_names) <= 4 else "20%"
            
            columns.append({
                "key": field_name,
                "label": label,
                "type": field_type,
                "width": width,
                "align": "right" if field_type in ['number', 'currency'] else "left"
            })
        
        logger.info(f"🔍 Table creation debug - Created {len(columns)} columns: {[col['label'] for col in columns]}")
        
        # Clean and format table data
        table_data = []
        for record in raw_data[:50]:  # Limit to 50 rows for performance
            cleaned_record = {}
            for field_name in field_names:
                if field_name == '_id':
                    continue
                value = record.get(field_name)
                cleaned_record[field_name] = self._clean_table_value(value)
            table_data.append(cleaned_record)
        
        return table_data, columns
    
    def _update_summary_for_full_dataset(self, data: Dict, table_data: List[Dict], user_question: str = "") -> Dict:
        """Update summary and insights to reflect the actual full dataset"""
        record_count = len(table_data)
        
        # Determine data type from question or table data
        data_type = self._determine_data_type_from_question(user_question)
        
        # Generate accurate summary
        data['summary'] = f"Found {record_count} records. Complete dataset showing all {record_count} {data_type} from the database."
        
        # Generate detailed insights based on actual data
        insights = [f"Successfully retrieved and displayed all {record_count} {data_type} from the database"]
        
        # Add specific insights based on data analysis
        if table_data:
            # Analyze data for meaningful insights
            if "role" in table_data[0]:
                role_counts = {}
                for record in table_data:
                    role = record.get('role', 'unknown')
                    role_counts[role] = role_counts.get(role, 0) + 1
                if len(role_counts) > 1:
                    role_breakdown = ", ".join([f"{count} {role}" for role, count in role_counts.items()])
                    insights.append(f"Role distribution: {role_breakdown}")
            
            if "createdAt" in table_data[0]:
                # Analyze creation dates
                dates = [record.get('createdAt', '') for record in table_data if record.get('createdAt')]
                if dates:
                    recent_count = sum(1 for date in dates if '2025' in str(date))
                    if recent_count > 0:
                        insights.append(f"{recent_count} {data_type} were created in 2025")
            
            # Add data completeness insight
            if record_count > 10:
                insights.append(f"Large dataset with {record_count} records - all records are displayed in the table")
            elif record_count > 1:
                insights.append(f"Complete dataset with {record_count} records - all data is shown")
        
        data['insights'] = insights
        
        # Update recommendations
        recommendations = [
            f"Review all {record_count} {data_type} in the table above for complete analysis",
            "Use table sorting and filtering capabilities for detailed examination",
        ]
        
        if record_count > 5:
            recommendations.append("Consider exporting data for further analysis in external tools")
        
        data['recommendations'] = recommendations
        
        return data
    
    def _determine_data_type_from_question(self, user_question: str = "") -> str:
        """Determine data type from user question for accurate summaries"""
        question_lower = user_question.lower()
        if "user" in question_lower:
            return "users"
        elif "customer" in question_lower:
            return "customers"
        elif "document" in question_lower:
            return "documents"
        elif "batch" in question_lower:
            return "batches"
        elif "cost" in question_lower or "evaluation" in question_lower:
            return "cost evaluations"
        elif "extraction" in question_lower:
            return "extractions"
        elif "obligation" in question_lower:
            return "obligations"
        elif "file" in question_lower:
            return "files"
        elif "conversation" in question_lower or "chat" in question_lower:
            return "conversations"
        elif "prompt" in question_lower:
            return "prompts"
        else:
            return "records"
    
    def _format_field_name(self, field_name: str) -> str:
        """Convert field names to readable labels"""
        field_mappings = {
            'userId': 'User ID',
            'emailId': 'Email Address',
            'email': 'Email Address',
            'name': 'Name',
            'role': 'Role', 
            'createdAt': 'Created Date',
            'updatedAt': 'Updated Date',
            'lastLogin': 'Last Login',
            'batchId': 'Batch ID',
            'fileId': 'File ID',
            'totalCost': 'Total Cost',
            'inputTokens': 'Input Tokens',
            'outputTokens': 'Output Tokens',
            'modelType': 'Model Type',
            'operationType': 'Operation Type',
            'Confidence_Score': 'Confidence Score',
            'obligationType': 'Obligation Type',
            'Contract_Name': 'Contract Name',
            'Value': 'Extracted Value',
            'Type': 'Extraction Type',
            'Name': 'Field Name',
            'Status': 'Status',
            'batchId': 'Batch ID',
            'fileId': 'File ID',
            'extractionType': 'Extraction Type',
            'processingTime': 'Processing Time',
            'timestamp': 'Timestamp'
        }
        
        return field_mappings.get(field_name, field_name.replace('_', ' ').title())
    
    def _determine_field_type(self, field_name: str, sample_value) -> str:
        """Determine appropriate column type for formatting"""
        if field_name in ['totalCost', 'costPerToken']:
            return 'currency'
        elif field_name in ['createdAt', 'updatedAt', 'timestamp', 'Timestamp']:
            return 'date'
        elif field_name in ['inputTokens', 'outputTokens', 'duration', 'Confidence_Score']:
            return 'number'
        elif isinstance(sample_value, (int, float)):
            return 'number'
        else:
            return 'text'
    
    def _clean_table_value(self, value):
        """Clean values for table display"""
        if value is None:
            return ''
        elif hasattr(value, 'isoformat'):  # datetime
            return value.isoformat()
        elif hasattr(value, 'hex'):  # ObjectId
            return str(value)
        else:
            return value
    
    def _create_basic_chart_config(self, chart_type: str, raw_data: List[Dict]) -> Dict:
        """Create basic chart configuration as fallback"""
        chart_data = self._extract_chart_data(raw_data)
        
        base_config = {
            "type": chart_type,
            "data": chart_data,
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {"display": True, "text": "Data Analysis"},
                    "legend": {"display": chart_type in ['pie', 'doughnut']}
                }
            }
        }
        
        if chart_type not in ['pie', 'doughnut']:
            base_config["options"]["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
        
        return base_config
    
    def _extract_chart_data(self, raw_data: List[Dict]) -> Dict:
        """Extract chart data from raw MongoDB results"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        # Determine labels and data
        labels = []
        values = []
        
        for item in raw_data[:20]:  # Limit for readability
            # Get label (usually _id field)
            label = str(item.get('_id', 'Unknown'))
            labels.append(label)
            
            # Get value (try different fields)
            value = 0
            for field in ['total_revenue', 'total_spent', 'total_amount', 'customer_count', 'order_count', 'stock', 'count']:
                if field in item:
                    value = float(item[field]) if item[field] is not None else 0
                    break
            
            values.append(value)
        
        return {
            "labels": labels,
            "datasets": [{
                "label": "Values",
                "data": values,
                "backgroundColor": "rgba(59, 130, 246, 0.8)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 2
            }]
        }

# ============================================================================
# COMPLETE SIMPLE QUERY PROCESSOR
# ============================================================================

class CompleteSimpleQueryProcessor:
    """Complete simple processor with all methods"""
    
    def __init__(self, database):
        self.db = database
        
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process questions with pattern matching"""
        question_lower = user_question.lower()
        
        try:
            # AI cost analysis
            if any(word in question_lower for word in ["cost", "spending", "ai cost", "model cost"]) or ("compare" in question_lower and any(word in question_lower for word in ["ai", "model", "cost"])):
                return self._ai_cost_analysis()
            
            # Document confidence analysis
            elif any(word in question_lower for word in ["confidence", "document", "extraction"]) and any(word in question_lower for word in ["top", "best", "analysis"]):
                return self._document_confidence_analysis()
            
            # Compliance obligations
            elif any(word in question_lower for word in ["compliance", "obligation", "legal"]) and any(word in question_lower for word in ["category", "type", "analysis"]):
                return self._compliance_obligations()
            
            # Agent performance
            elif any(word in question_lower for word in ["agent", "performance", "activity"]):
                return self._agent_performance()
            
            # Default: show available data
            else:
                return self._show_available_data()
                
        except Exception as e:
            logger.error(f"Simple processor error: {e}")
            return {
                "success": False,
                "error": f"Query failed: {str(e)}",
                "suggestions": ["Try a different question", "Check your data"]
            }
    
    def _ai_cost_analysis(self):
        """Analyze AI operational costs by model type"""
        pipeline = [
            {"$group": {
                "_id": "$modelType",
                "total_cost": {"$sum": "$totalCost"},
                "total_tokens": {"$sum": {"$add": ["$inputTokens", "$outputTokens"]}},
                "request_count": {"$sum": 1}
            }},
            {"$sort": {"total_cost": -1}}
        ]
        
        results = list(self.db.costevalutionforllm.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No AI cost data found"}
        
        # Create summary
        total_cost = sum(r['total_cost'] for r in results)
        summary_parts = []
        
        for result in results:
            model_type = result['_id']
            cost = result['total_cost']
            tokens = result['total_tokens']
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            
            summary_parts.append(f"{model_type}: ${cost:,.2f} ({percentage:.1f}%) from {tokens:,} tokens")
        
        summary = "AI cost analysis: " + " | ".join(summary_parts)
        
        # Chart configuration
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "AI Cost ($)",
                    "data": [r['total_cost'] for r in results],
                    "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
                    "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "AI Model Cost Analysis"},
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Cost ($)"}},
                    "x": {"title": {"display": True, "text": "AI Model"}}
                }
            }
        }
        
        insights = []
        if len(results) >= 2:
            leader = results[0]
            runner_up = results[1]
            revenue_diff = leader['total_revenue'] - runner_up['total_revenue']
            insights.append(f"{leader['_id']} leads by ${revenue_diff:,.2f}")
            insights.append(f"Total combined revenue: ${total_revenue:,.2f}")
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": insights,
            "recommendations": ["Focus on the leading category", "Analyze pricing strategies"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _document_confidence_analysis(self):
        """Analyze document extraction confidence scores"""
        pipeline = [
            {"$group": {
                "_id": "$Type",
                "avg_confidence": {"$avg": "$Confidence_Score"},
                "total_extractions": {"$sum": 1},
                "low_confidence_count": {"$sum": {"$cond": [{"$lt": ["$Confidence_Score", 0.8]}, 1, 0]}}
            }},
            {"$sort": {"avg_confidence": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.documentextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No document extraction data found"}
        
        summary = f"Top {len(results)} document types by confidence: "
        top_3 = results[:3]
        for i, doc_type in enumerate(top_3, 1):
            summary += f"{i}. {doc_type['_id']} ({doc_type['avg_confidence']:.2f} confidence) "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Avg Confidence",
                    "data": [r['avg_confidence'] for r in results],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Top Selling Products by Revenue"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total document types: {len(results)}", f"Highest confidence: {results[0]['_id']}"],
            "recommendations": ["Focus on high-confidence extractions", "Analyze low-confidence patterns for improvement"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _compliance_obligations(self):
        """Compliance obligations breakdown by type"""
        pipeline = [
            {"$group": {
                "_id": "$obligationType",
                "total_obligations": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"}
            }},
            {"$sort": {"total_obligations": -1}}
        ]
        
        results = list(self.db.obligationextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No compliance obligation data found"}
        
        total_obligations = sum(r['total_obligations'] for r in results)
        summary = f"Compliance obligations across {len(results)} types: "
        for result in results[:3]:  # Top 3
            obligation_type = result['_id']
            count = result['total_obligations']
            percentage = (count / total_obligations * 100) if total_obligations > 0 else 0
            summary += f"{obligation_type} {count} obligations ({percentage:.1f}%), "
        
        colors = [
            "rgba(59, 130, 246, 0.8)",   # Blue
            "rgba(16, 185, 129, 0.8)",   # Green
            "rgba(245, 158, 11, 0.8)",   # Yellow
            "rgba(239, 68, 68, 0.8)",    # Red
            "rgba(147, 51, 234, 0.8)",   # Purple
            "rgba(236, 72, 153, 0.8)"    # Pink
        ]
        
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['total_obligations'] for r in results],
                    "backgroundColor": colors[:len(results)]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Compliance Obligations by Type"},
                    "legend": {"display": True, "position": "bottom"}
                }
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total categories: {len(results)}", f"Leading category: {results[0]['_id']}"],
            "recommendations": ["Invest in top categories", "Analyze underperforming categories"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _agent_performance(self):
        """Agent performance analysis"""
        pipeline = [
            {"$group": {
                "_id": "$Agent",
                "success_count": {"$sum": {"$cond": [{"$eq": ["$Outcome", "Success"]}, 1, 0]}},
                "total_activities": {"$sum": 1},
                "avg_duration": {"$avg": "$duration"}
            }},
            {"$sort": {"success_count": -1}}
        ]
        
        results = list(self.db.agent_activity.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No agent performance data found"}
        
        summary = "Agent performance: "
        for result in results:
            agent = result['_id']
            success = result['success_count']
            total = result['total_activities']
            success_rate = (success / total * 100) if total > 0 else 0
            summary += f"{agent}: {success}/{total} ({success_rate:.1f}% success), "
        
        chart_config = {
            "type": "pie",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['total_spent'] for r in results],
                    "backgroundColor": [
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(16, 185, 129, 0.8)",
                        "rgba(245, 158, 11, 0.8)"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Customer Spending by Segment"}}
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total segments: {len(results)}", f"Top segment: {results[0]['_id']}"],
            "recommendations": ["Focus on high-value segments", "Develop segment-specific strategies"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _show_available_data(self):
        """Show what data is available"""
        try:
            collections_info = []
            for collection_name in ["costevalutionforllm", "documentextractions", "obligationextractions", "agent_activity", "batches", "users", "conversations"]:
                try:
                    count = self.db[collection_name].count_documents({})
                    collections_info.append(f"{collection_name}: {count} records")
                except:
                    collections_info.append(f"{collection_name}: 0 records")
            
            summary = f"Available data: {', '.join(collections_info)}. Try asking about: AI operational costs, document processing confidence, compliance obligations, agent performance."
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'What are our AI operational costs this month?'",
                    "Try: 'Show me document extraction confidence trends'",
                    "Try: 'Which compliance obligations need attention?'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {"success": False, "error": f"Could not retrieve data info: {str(e)}"}

# ============================================================================
# PERFECTED TWO-STAGE PROCESSOR
# ============================================================================

class PerfectedTwoStageProcessor:
    """Perfected processor that prioritizes Gemini AI"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor
        self.db = database
        # Import GenAI schema from config
        from config import DATABASE_SCHEMA
        self.schema_info = DATABASE_SCHEMA.copy()
    
    
    async def process_question(self, user_question: str) -> Dict[str, Any]:
        """Enhanced two-stage processing with Gemini priority"""
        start_time = datetime.now()
        
        # STAGE 1: Query Generation with Gemini (Priority)
        logger.info(f"🚀 Starting perfected two-stage processing: '{user_question}'")
        
        stage_1_result = await self.gemini_client.generate_query(user_question, self.schema_info)
        
        if stage_1_result["success"]:
            # Execute the Gemini-generated query
            query_data = stage_1_result["data"]
            raw_results = await self._execute_database_query(query_data)
            
            if raw_results is not None and len(raw_results) > 0:
                # STAGE 2: Visualization Generation with Gemini
                stage_2_result = await self.gemini_client.generate_visualization(
                    user_question, raw_results, query_data
                )
                
                if stage_2_result["success"]:
                    # Complete success with both Gemini stages
                    viz_data = stage_2_result["data"]
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"✅ Perfected two-stage Gemini processing successful: {len(raw_results)} results in {execution_time:.2f}s")
                    
                    return {
                        "success": True,
                        "summary": viz_data.get("summary", "AI-powered analysis completed successfully"),
                        "chart_data": viz_data.get("chart_config", {}),
                        "insights": viz_data.get("insights", ["AI-generated insights"]),
                        "recommendations": viz_data.get("recommendations", ["AI-powered recommendations"]),
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_two_stage_perfect",
                        "ai_powered": True
                    }
                else:
                    # Stage 2 failed, create enhanced fallback visualization
                    logger.warning("Stage 2 failed, creating enhanced fallback visualization")
                    fallback_viz = self._create_enhanced_visualization(user_question, raw_results, query_data)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return {
                        "success": True,
                        "summary": fallback_viz["summary"],
                        "chart_data": fallback_viz["chart_config"],
                        "insights": fallback_viz["insights"],
                        "recommendations": fallback_viz["recommendations"],
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_query_enhanced_viz",
                        "ai_powered": True
                    }
            else:
                # Gemini query returned no results, try simple processor
                logger.warning("Gemini query returned no results, trying simple processor")
                simple_result = self.simple_processor.process_question(user_question)
                if simple_result.get("success"):
                    simple_result["query_source"] = "gemini_failed_simple_success"
                    simple_result["ai_powered"] = False
                    return simple_result
                else:
                    return {
                        "success": False,
                        "error": "No data found for your query",
                        "suggestions": [
                            "Try rephrasing your question",
                            "Check if you're asking about available data"
                        ]
                    }
        
        # Stage 1 failed completely, use simple processor as last resort
        logger.warning("Gemini Stage 1 failed, using simple processor as last resort")
        simple_result = self.simple_processor.process_question(user_question)
        
        if simple_result.get("success"):
            simple_result["query_source"] = "simple_last_resort"
            simple_result["ai_powered"] = False
            logger.info(f"✅ Simple processor success as fallback: {simple_result.get('results_count', 0)} results")
            return simple_result
        else:
            return {
                "success": False,
                "error": "Unable to process your question with available methods",
                "suggestions": [
                    "Try a simpler question",
                    "Ask about: 'What are our AI operational costs?'",
                    "Ask about: 'Show me document extraction confidence'",
                    "Ask about: 'Which compliance obligations need attention?'"
                ]
            }
    
    async def _execute_database_query(self, query_data: Dict) -> Optional[List[Dict]]:
        """Execute MongoDB query with enhanced error handling"""
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return None
            
            collection = self.db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            # Convert ObjectIds to strings for JSON serialization
            cleaned_results = []
            for result in results:
                cleaned_result = self._clean_mongodb_result(result)
                cleaned_results.append(cleaned_result)
            
            logger.info(f"Database query executed: {len(cleaned_results)} results from {collection_name}")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return None
    
    def _clean_mongodb_result(self, result: Dict) -> Dict:
        """Clean MongoDB result by converting ObjectIds to strings"""
        cleaned = {}
        
        for key, value in result.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_mongodb_result(value)
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _create_enhanced_visualization(self, user_question: str, raw_results: List[Dict], query_data: Dict) -> Dict[str, Any]:
        """Create enhanced visualization when Gemini Stage 2 fails"""
        if not raw_results:
            return {
                "summary": "No data found for visualization",
                "chart_config": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["No data available"],
                "recommendations": ["Try a different question"]
            }
        
        # Smart chart type selection based on data and query
        chart_hint = query_data.get("chart_hint", "bar")
        
        # Extract data intelligently
        labels = []
        values = []
        
        for item in raw_results[:15]:  # Limit for readability
            label = str(item.get('_id', 'Unknown'))
            labels.append(label)
            
            # Get value
            value = 0
            for field in ['total_revenue', 'total_spent', 'total_amount', 'customer_count', 'order_count', 'stock']:
                if field in item and item[field] is not None:
                    value = float(item[field])
                    break
            values.append(value)
        
        # Chart configuration
        chart_config = {
            "type": chart_hint,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Values",
                    "data": values,
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {"display": True, "text": "Enhanced Data Analysis"},
                    "legend": {"display": chart_hint in ['pie', 'doughnut']}
                }
            }
        }
        
        if chart_hint not in ['pie', 'doughnut']:
            chart_config["options"]["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
        
        # Generate smart summary
        total_value = sum(values) if values else 0
        summary = f"Enhanced analysis of {len(raw_results)} data points. Total value: {total_value:,.2f}"
        
        insights = [
            f"Analyzed {len(raw_results)} records successfully",
            "Enhanced fallback visualization applied"
        ]
        
        recommendations = [
            "Review data patterns for optimization opportunities",
            "Consider AI-powered analysis for deeper insights"
        ]
        
        return {
            "summary": summary,
            "chart_config": chart_config,
            "insights": insights,
            "recommendations": recommendations
        }

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

# Initialize components
gemini_client = None
simple_processor = None
two_stage_processor = None
gemini_available = False

# Initialize Gemini
if GOOGLE_API_KEY and GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        gemini_client = BulletproofGeminiClient(GOOGLE_API_KEY)
        gemini_available = gemini_client.available
        if gemini_available:
            logger.info("Bulletproof Gemini client initialized")
            print("Bulletproof Gemini client initialized")
        else:
            logger.warning("Gemini client created but not available")
            print("Gemini client created but not available")
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
    
    if gemini_available and gemini_client:
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("Perfected two-stage processor initialized")
        print("Perfected two-stage processor initialized")
    else:
        logger.info("Complete simple processor ready (Gemini not available)")
        print("Complete simple processor ready (Gemini not available)")

# ============================================================================
# INITIALIZE MEMORY RAG SYSTEM
# ============================================================================

# Initialize Memory RAG system
memory_manager = None
memory_enhanced_processor = None

if mongodb_available and db is not None:
    try:
        memory_manager = MemoryRAGManager(db, gemini_client)
        logger.info("Memory RAG Manager initialized")
        print("Memory RAG Manager initialized")
        
        # Create memory-enhanced processor WITH Gemini client for smart suggestions
        if two_stage_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                two_stage_processor, 
                memory_manager, 
                gemini_client  # 🚀 NEW: Pass Gemini client for smart suggestions
            )
            logger.info("✅ Memory-Enhanced Two-Stage Processor ready with Smart Suggestions")
            print("✅ Memory-Enhanced Two-Stage Processor ready with Smart Suggestions")
        elif simple_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(
                simple_processor, 
                memory_manager, 
                gemini_client  # 🚀 NEW: Pass Gemini client for smart suggestions
            )
            logger.info("✅ Memory-Enhanced Simple Processor ready with Smart Suggestions")
            print("✅ Memory-Enhanced Simple Processor ready with Smart Suggestions")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Memory RAG: {e}")
        print(f"❌ Memory RAG Error: {e}")
        memory_manager = None
        memory_enhanced_processor = None
else:
    logger.warning("MongoDB not available - Memory RAG disabled")
    print("MongoDB not available - Memory RAG disabled")

# ============================================================================
# CHAT API ENDPOINTS
# ============================================================================

@app.route('/api/chats', methods=['GET'])
def get_chat_sessions_endpoint():
    """Get all chat sessions with optional filtering"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        offset = int(request.args.get('offset', 0))
        status_filter = request.args.get('status')  # active, archived, deleted
        
        chats = get_all_chat_sessions(limit=limit, offset=offset, status_filter=status_filter)
        
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

@app.route('/api/chats', methods=['POST'])
def create_chat_session_endpoint():
    """Create a new chat session"""
    try:
        data = request.get_json() or {}
        
        title = data.get('title')
        category = data.get('category', 'conversational')
        first_message = data.get('first_message')
        
        # Auto-generate title from first message if not provided
        if not title and first_message:
            title = auto_generate_chat_title(first_message)
        
        chat_id = create_new_chat_session(title=title, category=category)
        
        if chat_id:
            # If there's a first message, save it
            if first_message:
                message_data = {
                    'type': 'user',
                    'content': first_message,
                    'timestamp': datetime.now(timezone.utc)
                }
                save_message_to_chat(chat_id, message_data)
            
            # Return the created chat
            chat = get_chat_session(chat_id)
            
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

@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat_session_endpoint(chat_id):
    """Get a specific chat session by ID"""
    try:
        chat = get_chat_session(chat_id)
        
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

@app.route('/api/chats/<chat_id>/messages', methods=['POST'])
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
        success = save_message_to_chat(chat_id, message_data)
        
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

@app.route('/api/chats/<chat_id>', methods=['PUT'])
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
        
        success = update_chat_session(chat_id, updates)
        
        if success:
            # Return updated chat
            updated_chat = get_chat_session(chat_id)
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

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat_session_endpoint(chat_id):
    """Delete a chat session (soft delete by default)"""
    try:
        # Check if it should be a hard delete
        hard_delete = request.args.get('hard', 'false').lower() == 'true'
        
        success = delete_chat_session(chat_id, soft_delete=not hard_delete)
        
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

# ============================================================================
# MAIN QUERY ENDPOINTS WITH CHAT INTEGRATION
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check for GenAI operations"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "ai_system": "unavailable",
            "collections": {},
            "domain": "AI Operations & Document Intelligence"
        }
        
        # Database health check
        if mongodb_available and db is not None:
            health_status["database"] = "connected"
            
            # Check GenAI collections instead of old ones
            genai_collections = [
                "costevalutionforllm", "documentextractions", "obligationextractions",
                "agent_activity", "batches", "users", "conversations"
            ]
            
            collection_status = {}
            total_documents = 0
            
            for collection_name in genai_collections:
                try:
                    collection = db[collection_name]
                    count = collection.count_documents({})
                    collection_status[collection_name] = {
                        "status": "available",
                        "document_count": count
                    }
                    total_documents += count
                except Exception as e:
                    collection_status[collection_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            health_status["collections"] = collection_status
            health_status["total_documents"] = total_documents
        
        # AI system health check
        if gemini_available:
            health_status["ai_system"] = "available"
            health_status["processors"] = {
                "two_stage": two_stage_processor is not None,
                "simple": simple_processor is not None,
                "memory_enhanced": memory_enhanced_processor is not None
            }
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Enhanced query processing with Memory RAG integration"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        chat_id = data.get('chat_id')
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        # Determine if we should use memory enhancement
        use_memory = chat_id and memory_enhanced_processor and memory_manager
        
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
            save_message_to_chat(chat_id, user_message)
        
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
            save_message_to_chat(chat_id, ai_message)
        
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

@app.route('/api/system/test', methods=['POST'])
def test_system_components():
    """Test all system components including chat"""
    try:
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test database
        if mongodb_available and db is not None:
            try:
                count = db.costevalutionforllm.count_documents({})
                test_results["tests"]["database"] = {
                    "status": "pass",
                    "details": f"AI cost collection has {count} documents"
                }
            except Exception as e:
                test_results["tests"]["database"] = {
                    "status": "fail",
                    "details": str(e)
                }
        else:
            test_results["tests"]["database"] = {
                "status": "fail",
                "details": "Database not available"
            }
        
        # Test chat system
        if mongodb_available and db is not None:
            try:
                # Test creating a chat session
                test_chat_id = create_new_chat_session("Test Chat Session")
                if test_chat_id:
                    # Test saving a message
                    test_message = {
                        'type': 'user',
                        'content': 'Test message for system validation',
                        'timestamp': datetime.now(timezone.utc)
                    }
                    message_saved = save_message_to_chat(test_chat_id, test_message)
                    
                    # Test retrieving the chat
                    retrieved_chat = get_chat_session(test_chat_id)
                    
                    if message_saved and retrieved_chat:
                        test_results["tests"]["chat_system"] = {
                            "status": "pass",
                            "details": f"Chat system functional - created chat {test_chat_id}"
                        }
                        # Clean up test chat
                        delete_chat_session(test_chat_id, soft_delete=False)
                    else:
                        test_results["tests"]["chat_system"] = {
                            "status": "fail",
                            "details": "Chat message handling failed"
                        }
                else:
                    test_results["tests"]["chat_system"] = {
                        "status": "fail",
                        "details": "Failed to create test chat session"
                    }
            except Exception as e:
                test_results["tests"]["chat_system"] = {
                    "status": "fail",
                    "details": str(e)
                }
        else:
            test_results["tests"]["chat_system"] = {
                "status": "fail",
                "details": "Database not available for chat system"
            }
        
        # Test simple processor
        if simple_processor:
            try:
                result = simple_processor.process_question("Show me what data is available")
                test_results["tests"]["simple_processor"] = {
                    "status": "pass" if result.get("success") else "fail",
                    "details": result.get("summary", result.get("error"))
                }
            except Exception as e:
                test_results["tests"]["simple_processor"] = {
                    "status": "fail",
                    "details": str(e)
                }
        else:
            test_results["tests"]["simple_processor"] = {
                "status": "fail",
                "details": "Simple processor not available"
            }
        
        # Test Gemini AI
        if gemini_client and gemini_available:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    # Test basic query generation
                    result = loop.run_until_complete(
                        gemini_client.generate_query(
                            "Test query", 
                            {"collections": {"costevalutionforllm": {"fields": ["modelType", "totalCost"]}}}
                        )
                    )
                    test_results["tests"]["gemini_ai"] = {
                        "status": "pass" if result.get("success") else "fail",
                        "details": "Query generation test completed"
                    }
                finally:
                    loop.close()
                    
            except Exception as e:
                test_results["tests"]["gemini_ai"] = {
                    "status": "fail",
                    "details": str(e)
                }
        else:
            test_results["tests"]["gemini_ai"] = {
                "status": "fail",
                "details": "Gemini AI not available"
            }
        
        # Test two-stage processor
        if two_stage_processor:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    result = loop.run_until_complete(
                        two_stage_processor.process_question("What are our AI operational costs this month?")
                    )
                    test_results["tests"]["two_stage_processor"] = {
                        "status": "pass" if result.get("success") else "fail",
                        "details": f"Test query processed with {result.get('query_source', 'unknown')} source"
                    }
                finally:
                    loop.close()
                    
            except Exception as e:
                test_results["tests"]["two_stage_processor"] = {
                    "status": "fail",
                    "details": str(e)
                }
        else:
            test_results["tests"]["two_stage_processor"] = {
                "status": "fail",
                "details": "Two-stage processor not available"
            }
        
        # Calculate overall status
        passed_tests = sum(1 for test in test_results["tests"].values() if test["status"] == "pass")
        total_tests = len(test_results["tests"])
        
        test_results["overall"] = {
            "status": "healthy" if passed_tests == total_tests else "degraded" if passed_tests > 0 else "unhealthy",
            "passed": passed_tests,
            "total": total_tests,
            "success_rate": f"{(passed_tests / total_tests * 100):.1f}%"
        }
        
        return jsonify(test_results)
        
    except Exception as e:
        return jsonify({
            "error": "System test failed",
            "details": str(e)
        }), 500

@app.route('/api/examples', methods=['GET'])
def get_example_questions():
    """Get example questions for GenAI operations analytics"""
    
    examples = {
        "ai_operations": {
            "description": "AI cost analysis and performance optimization",
            "examples": [
                "What's our AI spending this month?",
                "Which AI models are most cost-effective?",
                "Show me token usage patterns by user",
                "Compare processing costs between document types",
                "What's our average cost per document extraction?"
            ]
        },
        "document_processing": {
            "description": "Document extraction and processing analytics",
            "examples": [
                "How many documents did we process today?",
                "What's our extraction success rate?",
                "Show me documents with low confidence scores",
                "Which document types take longest to process?",
                "What are our confidence score distributions?"
            ]
        },
        "compliance_analytics": {
            "description": "Legal compliance and risk assessment",
            "examples": [
                "What are our most critical compliance obligations?",
                "Show me high-risk compliance items",
                "Which contracts have data confidentiality requirements?",
                "Track compliance obligation trends over time",
                "List all insurance-related obligations"
            ]
        },
        "operational_intelligence": {
            "description": "System performance and user analytics",
            "examples": [
                "How are our AI agents performing?",
                "Show me batch processing success rates",
                "Which users are most active in the system?",
                "What's our overall system health status?",
                "Compare agent performance across document types"
            ]
        },
        "advanced_analytics": {
            "description": "Cross-collection complex analysis",
            "examples": [
                "Show AI costs for documents that failed compliance",
                "Which prompts are most effective for legal documents?",
                "Compare extraction confidence vs processing costs",
                "Track document processing pipeline success rates",
                "Show ROI analysis for different AI models"
            ]
        },
        "chat_integration_examples": {
            "description": "Examples showing how to use chat functionality",
            "create_new_chat": "POST /api/chats with {\"title\": \"AI Cost Analysis\", \"category\": \"operations\"}",
            "query_with_chat": "POST /api/query with {\"question\": \"Show AI spending trends\", \"chat_id\": \"chat_123\"}",
            "get_chat_history": "GET /api/chats/chat_123",
            "list_all_chats": "GET /api/chats?limit=20&status=active"
        },
        "system_capabilities": {
            "ai_features": [
                "Natural language understanding for AI operations",
                "Intelligent chart type selection for operational data",
                "Context-aware insights generation for cost optimization",
                "Automated recommendations for system improvements",
                "Chat session persistence with operational context",
                "Memory-enhanced conversations for better follow-ups"
            ],
            "fallback_features": [
                "Pattern-based query processing for GenAI collections",
                "Guaranteed response for common operational questions",
                "Fast processing times for system health queries",
                "Reliable basic analytics for cost and performance data",
                "Chat session management for operational discussions",
                "Real-time message saving for audit trails"
            ]
        }
    }
    
    return jsonify(examples)

# Replace the debug_collections endpoint in your app.py (around line 1100)

@app.route('/api/debug/collections', methods=['GET'])
def debug_collections():
    """Debug endpoint with enhanced information for GenAI collections"""
    if not mongodb_available or db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        collections_info = {}
        collection_names = db.list_collection_names()
        
        for collection_name in collection_names:
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                sample = collection.find_one() if count > 0 else None
                
                # Convert ObjectId to string for JSON serialization - FIXED
                if sample and '_id' in sample:
                    sample['_id'] = str(sample['_id'])
                
                # Clean all fields for JSON serialization - NEW FIX
                if sample:
                    cleaned_sample = {}
                    for key, value in sample.items():
                        if hasattr(value, 'isoformat'):  # datetime
                            cleaned_sample[key] = value.isoformat()
                        elif hasattr(value, '__str__') and hasattr(value, 'hex'):  # ObjectId
                            cleaned_sample[key] = str(value)
                        elif isinstance(value, dict):
                            # Recursively clean nested objects
                            cleaned_value = {}
                            for k, v in value.items():
                                if hasattr(v, 'isoformat'):
                                    cleaned_value[k] = v.isoformat()
                                elif hasattr(v, '__str__') and hasattr(v, 'hex'):
                                    cleaned_value[k] = str(v)
                                else:
                                    cleaned_value[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                            cleaned_sample[key] = cleaned_value
                        elif isinstance(value, list):
                            # Clean list items
                            cleaned_list = []
                            for item in value[:3]:  # Limit to first 3 items
                                if hasattr(item, 'isoformat'):
                                    cleaned_list.append(item.isoformat())
                                elif hasattr(item, '__str__') and hasattr(item, 'hex'):
                                    cleaned_list.append(str(item))
                                else:
                                    cleaned_list.append(str(item) if not isinstance(item, (str, int, float, bool, type(None))) else item)
                            cleaned_sample[key] = cleaned_list
                        else:
                            # Convert everything else to string if it's not a basic type
                            if isinstance(value, (str, int, float, bool, type(None))):
                                cleaned_sample[key] = value
                            else:
                                cleaned_sample[key] = str(value)
                    
                    sample = cleaned_sample
                
                # Get field statistics
                field_stats = {}
                if sample:
                    for field, value in sample.items():
                        field_stats[field] = {
                            "type": type(value).__name__,
                            "sample_value": str(value)[:100]  # Truncate long values
                        }
                
                # Determine if collection is AI operations compatible
                ai_compatible = collection_name in [
                    "costevalutionforllm", "documentextractions", "obligationextractions",
                    "agent_activity", "batches", "users", "conversations", "prompts",
                    "files", "compliances", "obligationmappings", "documentmappings"
                ]
                
                collections_info[collection_name] = {
                    "document_count": count,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "field_statistics": field_stats,
                    "sample_document": sample,
                    "ai_compatible": ai_compatible,
                    "is_chat_collection": collection_name in ["conversations", "chat_sessions"],
                    "domain_relevance": "high" if ai_compatible else "low"
                }
            except Exception as e:
                collections_info[collection_name] = {
                    "error": str(e),
                    "document_count": -1,
                    "ai_compatible": False,
                    "is_chat_collection": False
                }
        
        return jsonify({
            "database_name": db.name,
            "domain": "AI Operations & Document Intelligence",
            "total_collections": len(collections_info),
            "collection_names": collection_names,
            "collections": collections_info,
            "ai_system_status": {
                "gemini_available": gemini_available,
                "two_stage_processor": two_stage_processor is not None,
                "simple_processor": simple_processor is not None,
                "chat_system": mongodb_available,
                "memory_rag": memory_manager is not None
            }
        })
        
    except Exception as e:
        logger.error(f"Debug collections failed: {str(e)}")
        return jsonify({"error": f"Debug failed: {str(e)}"}), 500

@app.route('/api/chats/stats', methods=['GET'])
def get_chat_statistics():
    """Get chat system statistics"""
    if not mongodb_available or db is None:
        return jsonify({"error": "Database not available"}), 503
    
    try:
        # Get basic stats
        total_chats = db.chat_sessions.count_documents({})
        active_chats = db.chat_sessions.count_documents({"status": "active"})
        archived_chats = db.chat_sessions.count_documents({"status": "deleted"})
        
        # Get recent activity
        one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        recent_chats = db.chat_sessions.count_documents({
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
        
        message_stats = list(db.chat_sessions.aggregate(pipeline))
        message_data = message_stats[0] if message_stats else {
            "total_messages": 0,
            "avg_messages_per_chat": 0,
            "max_messages": 0
        }
        
        return jsonify({
            "success": True,
            "statistics": {
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
        })
        
    except Exception as e:
        logger.error(f"Failed to get chat statistics: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve chat statistics",
            "details": str(e)
        }), 500

# ============================================================================
# MEMORY RAG ENDPOINTS
# ============================================================================

@app.route('/api/memory/stats/<chat_id>', methods=['GET'])
def get_memory_stats(chat_id):
    """Get memory statistics for a specific chat"""
    if not memory_manager:
        return jsonify({"error": "Memory RAG not available"}), 503
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            stats = loop.run_until_complete(memory_manager.get_chat_memory_stats(chat_id))
            return jsonify({
                "success": True,
                "chat_id": chat_id,
                "memory_stats": stats
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to get memory stats for {chat_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/memory/search/<chat_id>', methods=['POST'])
def search_memories(chat_id):
    """Search memories in a specific chat"""
    if not memory_manager:
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
            memories = loop.run_until_complete(
                memory_manager.retrieve_relevant_memories(chat_id, search_query, limit)
            )
            
            # Convert to JSON-serializable format
            memory_data = [
                {
                    "fragment_id": mem.fragment_id,
                    "content": mem.content,
                    "content_type": mem.content_type,
                    "importance_score": mem.importance_score,
                    "keywords": mem.keywords,
                    "entities": mem.entities,
                    "timestamp": mem.timestamp.isoformat(),
                    "access_count": mem.access_count,
                    "last_accessed": mem.last_accessed.isoformat() if mem.last_accessed else None
                } for mem in memories
            ]
            
            return jsonify({
                "success": True,
                "search_query": search_query,
                "results_count": len(memory_data),
                "memories": memory_data
            })
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to search memories for {chat_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500 


if __name__ == '__main__':
    print("\n🔗 Starting GenAI Operations Analytics Server with Chat...")
    print("🎯 AI Operations Features:")
    print("   - ✅ Bulletproof Gemini two-stage processing for AI operations")
    print("   - ✅ Enhanced retry logic with exponential backoff")
    print("   - ✅ Intelligent JSON extraction and validation")
    print("   - ✅ Smart fallback visualizations for operational data")
    print("   - ✅ Complete simple processor backup")
    print("   - ✅ Complete chat session management")
    print("   - ✅ Real-time message persistence")
    print("   - ✅ Chat history and search")
    print("   - ✅ Smart context-aware follow-up suggestions")
    print("   - ✅ Memory RAG system for operational intelligence")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected to GenAI operations database")
        print("   ✅ Chat System: Indexes created, ready for persistence")
    else:
        print("   ❌ MongoDB: Connection failed")
        print("   ❌ Chat System: Not available")
    
    if gemini_available:
        print("   ✅ Gemini AI: Bulletproof client ready for AI operations")
    else:
        print("   ⚠️ Gemini AI: Not available")
    
    if two_stage_processor:
        print("   ✅ Perfected Two-Stage Processor: AI operations processing ready")
    elif simple_processor:
        print("   ✅ Complete Simple Processor: Fallback processing ready")
    else:
        print("   ❌ No processors available")
    
    if memory_manager:
        print("   ✅ Memory RAG: Advanced conversation memory system ready")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 GenAI Operations Endpoints:")
    print("   - POST /api/query (AI operations intelligent processing + chat)")
    print("   - POST /api/system/test (comprehensive system testing)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/examples (GenAI operations example questions)")
    print("   - GET  /api/debug/collections (GenAI collections debug info)")
    print("\n💬 Chat Management Endpoints:")
    print("   - GET  /api/chats (list all chat sessions)")
    print("   - POST /api/chats (create new chat session)")
    print("   - GET  /api/chats/{id} (get specific chat)")
    print("   - PUT  /api/chats/{id} (update chat metadata)")
    print("   - DELETE /api/chats/{id} (delete chat session)")
    print("   - POST /api/chats/{id}/messages (add message to chat)")
    print("   - GET  /api/chats/stats (chat system statistics)")
    print("\n🤖 AI Operations Domain:")
    print("   - Cost analysis and optimization")
    print("   - Document processing intelligence")
    print("   - Compliance risk assessment")
    print("   - Agent performance monitoring")
    print("   - Operational efficiency analytics")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)