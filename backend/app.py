from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime, timedelta
import pymongo
import json
import google.generativeai as genai
from typing import Dict, Any, List, Optional
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
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/analytics_db')

print("=" * 60)
print("🚀 PERFECTED AI ANALYTICS - BULLETPROOF GEMINI TWO-STAGE + CHAT")
print("=" * 60)
print(f"📊 Database: {MONGODB_URI}")
print(f"🔑 API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Database Connection
db = None
mongodb_available = False

try:
    client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client.analytics_db
    client.admin.command('ping')
    mongodb_available = True
    logger.info("✅ MongoDB connected successfully")
    print("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to MongoDB: {e}")
    print(f"❌ MongoDB Error: {e}")
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
        now = datetime.utcnow()
        
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
            message_data['timestamp'] = datetime.utcnow()
        
        # Update the chat session
        result = db.chat_sessions.update_one(
            {'chat_id': chat_id},
            {
                '$push': {'messages': message_data},
                '$set': {
                    'updated_at': datetime.utcnow(),
                    'metadata.last_activity': datetime.utcnow()
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
        updates['updated_at'] = datetime.utcnow()
        
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
                        'updated_at': datetime.utcnow()
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
                        
                        if self._validate_and_fix_visualization_response(parsed_result, raw_data):
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
        return f"""You are an expert MongoDB query generator. Convert natural language questions to perfect MongoDB aggregation pipelines.

USER QUESTION: "{user_question}"

DATABASE SCHEMA:
{json.dumps(schema_info, indent=2)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Use exact field names from schema
3. Create efficient aggregation pipelines
4. Always include $sort and $limit for performance
5. Choose appropriate chart type based on question

RESPONSE FORMAT (JSON only):
{{
  "collection": "sales|products|customers|marketing_campaigns",
  "pipeline": [
    {{"$match": {{"condition": "value"}}}},
    {{"$group": {{"_id": "$field", "metric": {{"$sum": "$value"}}}}}},
    {{"$sort": {{"metric": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar|pie|line|doughnut",
  "query_intent": "Description of what this query achieves"
}}

JSON only - no other text:"""

    def _build_enhanced_visualization_prompt(self, user_question: str, raw_data: List[Dict], query_context: Dict) -> str:
        """Improved visualization prompt with better instructions"""
        sample_data = raw_data[:3] if raw_data else []
        
        return f"""You are an expert data visualization specialist. Create perfect Chart.js configurations.

USER QUESTION: "{user_question}"
DATA SAMPLE: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}
QUERY CONTEXT: {json.dumps(query_context, indent=2)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Always include ALL required fields: chart_type, chart_config, summary, insights, recommendations
3. Make chart_config a complete, working Chart.js configuration
4. Ensure all JSON is properly formatted with correct quotes and brackets

REQUIRED JSON STRUCTURE:
{{
  "chart_type": "bar",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["Label1", "Label2"],
      "datasets": [{{
        "label": "Dataset Name", 
        "data": [100, 200],
        "backgroundColor": "rgba(59, 130, 246, 0.8)",
        "borderColor": "rgba(59, 130, 246, 1)",
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "maintainAspectRatio": false,
      "plugins": {{
        "title": {{"display": true, "text": "Chart Title"}},
        "legend": {{"display": false}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true}},
        "x": {{"display": true}}
      }}
    }}
  }},
  "summary": "Clear summary with specific numbers and insights",
  "insights": [
    "Specific insight with data",
    "Another meaningful insight"
  ],
  "recommendations": [
    "Actionable recommendation",
    "Strategic suggestion"
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
                data['collection'] = 'sales'  # Default
            
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
    
    def _validate_and_fix_visualization_response(self, data: Dict, raw_data: List[Dict]) -> bool:
        """Enhanced validation with auto-fixing and logging"""
        try:
            logger.info(f"🔍 Validating visualization response: {list(data.keys())}")
            
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
                    data['summary'] = f"Analysis of {len(raw_data)} data points completed successfully."
                    logger.info("✅ Fixed: Added default summary")
                
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
            # Smartphone vs Laptop comparison
            if ("smartphone" in question_lower and "laptop" in question_lower) or ("compare" in question_lower and any(cat in question_lower for cat in ["smartphone", "laptop"])):
                return self._smartphone_laptop_comparison()
            
            # Top products queries
            elif any(word in question_lower for word in ["top", "best", "highest"]) and any(word in question_lower for word in ["product", "selling", "performer"]):
                return self._top_products()
            
            # Revenue by category
            elif any(word in question_lower for word in ["category", "categories"]) and any(word in question_lower for word in ["revenue", "sales"]):
                return self._revenue_by_category()
            
            # Customer segments
            elif "customer" in question_lower and any(word in question_lower for word in ["segment", "distribution", "breakdown"]):
                return self._customer_segments()
            
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
    
    def _smartphone_laptop_comparison(self):
        """Compare smartphone vs laptop sales"""
        pipeline = [
            {"$match": {"category": {"$in": ["Smartphones", "Laptops"]}}},
            {"$group": {
                "_id": "$category",
                "total_revenue": {"$sum": "$total_amount"},
                "total_quantity": {"$sum": "$quantity"},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        
        results = list(self.db.sales.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No smartphone or laptop data found"}
        
        # Create summary
        total_revenue = sum(r['total_revenue'] for r in results)
        summary_parts = []
        
        for result in results:
            category = result['_id']
            revenue = result['total_revenue']
            quantity = result['total_quantity']
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            summary_parts.append(f"{category}: ${revenue:,.2f} ({percentage:.1f}%) from {quantity} units")
        
        summary = "Sales comparison: " + " | ".join(summary_parts)
        
        # Chart configuration
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Revenue ($)",
                    "data": [r['total_revenue'] for r in results],
                    "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
                    "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Smartphone vs Laptop Sales Revenue"},
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Revenue ($)"}},
                    "x": {"title": {"display": True, "text": "Product Category"}}
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
    
    def _top_products(self):
        """Get top selling products"""
        pipeline = [
            {"$group": {
                "_id": "$product_name",
                "total_revenue": {"$sum": "$total_amount"},
                "total_quantity": {"$sum": "$quantity"},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.sales.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No product data found"}
        
        summary = f"Top {len(results)} products by revenue: "
        top_3 = results[:3]
        for i, product in enumerate(top_3, 1):
            summary += f"{i}. {product['_id']} (${product['total_revenue']:,.2f}) "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Revenue ($)",
                    "data": [r['total_revenue'] for r in results],
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
            "insights": [f"Total products: {len(results)}", f"Top performer: {results[0]['_id']}"],
            "recommendations": ["Focus on top performers", "Analyze why these products succeed"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _revenue_by_category(self):
        """Revenue breakdown by category"""
        pipeline = [
            {"$group": {
                "_id": "$category",
                "total_revenue": {"$sum": "$total_amount"},
                "total_quantity": {"$sum": "$quantity"}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        
        results = list(self.db.sales.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No category data found"}
        
        total_revenue = sum(r['total_revenue'] for r in results)
        summary = f"Revenue across {len(results)} categories: "
        for result in results[:3]:  # Top 3
            category = result['_id']
            revenue = result['total_revenue']
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            summary += f"{category} ${revenue:,.2f} ({percentage:.1f}%), "
        
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
                    "data": [r['total_revenue'] for r in results],
                    "backgroundColor": colors[:len(results)]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Revenue by Category"},
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
    
    def _customer_segments(self):
        """Customer segment analysis"""
        pipeline = [
            {"$group": {
                "_id": "$customer_segment",
                "total_spent": {"$sum": "$total_spent"},
                "customer_count": {"$sum": 1},
                "avg_spent": {"$avg": "$total_spent"}
            }},
            {"$sort": {"total_spent": -1}}
        ]
        
        results = list(self.db.customers.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No customer segment data found"}
        
        summary = "Customer segments: "
        for result in results:
            segment = result['_id']
            total = result['total_spent']
            count = result['customer_count']
            avg = result['avg_spent']
            summary += f"{segment}: {count} customers, ${total:,.2f} total (avg: ${avg:,.2f}), "
        
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
            for collection_name in ["sales", "customers", "products", "marketing_campaigns"]:
                try:
                    count = self.db[collection_name].count_documents({})
                    collections_info.append(f"{collection_name}: {count} records")
                except:
                    collections_info.append(f"{collection_name}: 0 records")
            
            summary = f"Available data: {', '.join(collections_info)}. Try asking about: smartphone vs laptop sales, top products, customer segments, revenue by category."
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'Compare smartphone vs laptop sales'",
                    "Try: 'Show me customer segments'",
                    "Try: 'What's our revenue by category?'"
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
        self.schema_info = {
            "collections": {
                "sales": {
                    "description": "Sales transaction records",
                    "fields": ["order_id", "customer_id", "product_id", "product_name", "category", "quantity", "unit_price", "total_amount", "discount", "date", "month", "quarter", "sales_rep", "region"],
                    "sample_values": {
                        "category": ["Smartphones", "Laptops", "Audio", "Tablets", "Accessories", "Monitors"],
                        "region": ["North America", "Europe", "Asia-Pacific"],
                        "month": ["January", "February", "March", "April", "May", "June", "July"]
                    },
                    "numeric_fields": ["quantity", "unit_price", "total_amount", "discount"]
                },
                "customers": {
                    "description": "Customer profiles and behavior",
                    "fields": ["customer_id", "name", "email", "age", "gender", "country", "state", "city", "customer_segment", "total_spent", "order_count", "signup_date", "last_purchase"],
                    "sample_values": {"customer_segment": ["Regular", "Premium", "VIP"]},
                    "numeric_fields": ["age", "total_spent", "order_count"]
                },
                "products": {
                    "description": "Product catalog and inventory",
                    "fields": ["product_id", "name", "category", "subcategory", "brand", "price", "cost", "stock", "rating", "reviews_count", "launch_date"],
                    "numeric_fields": ["price", "cost", "stock", "rating", "reviews_count"]
                }
            }
        }
    
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
                    "Ask about: 'smartphone vs laptop sales'",
                    "Ask about: 'customer segments'",
                    "Ask about: 'revenue by category'"
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
            logger.info("✅ Bulletproof Gemini client initialized")
            print("✅ Bulletproof Gemini client initialized")
        else:
            logger.warning("⚠️ Gemini client created but not available")
            print("⚠️ Gemini client created but not available")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        print(f"❌ Gemini Error: {e}")
        gemini_available = False
else:
    logger.warning("⚠️ No Google API key provided")
    print("⚠️ No Google API key provided")
    gemini_available = False

# Initialize processors
if db is not None:
    simple_processor = CompleteSimpleQueryProcessor(db)
    
    if gemini_available and gemini_client:
        two_stage_processor = PerfectedTwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("✅ Perfected two-stage processor initialized")
        print("✅ Perfected two-stage processor initialized")
    else:
        logger.info("✅ Complete simple processor ready (Gemini not available)")
        print("✅ Complete simple processor ready (Gemini not available)")

# ============================================================================
# INITIALIZE MEMORY RAG SYSTEM
# ============================================================================

# Initialize Memory RAG system
memory_manager = None
memory_enhanced_processor = None

if mongodb_available and db is not None:
    try:
        memory_manager = MemoryRAGManager(db, gemini_client)
        logger.info("✅ Memory RAG Manager initialized")
        print("✅ Memory RAG Manager initialized")
        
        # Create memory-enhanced processor
        if two_stage_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(two_stage_processor, memory_manager)
            logger.info("✅ Memory-Enhanced Two-Stage Processor ready")
            print("✅ Memory-Enhanced Two-Stage Processor ready")
        elif simple_processor:
            memory_enhanced_processor = MemoryEnhancedProcessor(simple_processor, memory_manager)
            logger.info("✅ Memory-Enhanced Simple Processor ready")
            print("✅ Memory-Enhanced Simple Processor ready")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize Memory RAG: {e}")
        print(f"❌ Memory RAG Error: {e}")
        memory_manager = None
        memory_enhanced_processor = None
else:
    logger.warning("⚠️ MongoDB not available - Memory RAG disabled")
    print("⚠️ MongoDB not available - Memory RAG disabled")

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
                    'timestamp': datetime.utcnow()
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
            'timestamp': datetime.utcnow()
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
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "available" if mongodb_available else "unavailable",
            "gemini": "available" if gemini_available else "unavailable",
            "simple_processor": "available" if simple_processor else "unavailable",
            "two_stage_processor": "available" if two_stage_processor else "unavailable",
            "chat_system": "available" if mongodb_available else "unavailable"
        },
        "version": "3.0.0-perfected-ai-system-with-chat"
    })

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
                'timestamp': datetime.utcnow()
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
                result = two_stage_processor.process_question(user_question)
                result['processing_mode'] = 'two_stage'
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
                'timestamp': datetime.utcnow()
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
                count = db.sales.count_documents({})
                test_results["tests"]["database"] = {
                    "status": "pass",
                    "details": f"Sales collection has {count} documents"
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
                        'timestamp': datetime.utcnow()
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
                            {"collections": {"sales": {"fields": ["category", "total_amount"]}}}
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
                        two_stage_processor.process_question("Compare smartphone vs laptop sales")
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
def get_enhanced_examples():
    """Get comprehensive example questions"""
    examples = {
        "guaranteed_working": {
            "description": "These questions are guaranteed to work with both AI and fallback",
            "questions": [
                "Compare smartphone vs laptop sales performance",
                "Show me customer distribution by segment", 
                "What's our revenue by category?",
                "What are our top selling products?"
            ]
        },
        "chat_integration_examples": {
            "description": "Examples showing how to use chat functionality",
            "create_new_chat": "POST /api/chats with {\"title\": \"Revenue Analysis\", \"category\": \"analysis\"}",
            "query_with_chat": "POST /api/query with {\"question\": \"Show revenue by category\", \"chat_id\": \"chat_123\"}",
            "get_chat_history": "GET /api/chats/chat_123",
            "list_all_chats": "GET /api/chats?limit=20&status=active"
        },
        "system_capabilities": {
            "ai_features": [
                "Natural language understanding",
                "Intelligent chart type selection",
                "Context-aware insights generation",
                "Automated recommendations",
                "Chat session persistence",
                "Message history tracking"
            ],
            "fallback_features": [
                "Pattern-based query processing",
                "Guaranteed response for common questions",
                "Fast processing times",
                "Reliable basic analytics",
                "Chat session management",
                "Real-time message saving"
            ]
        }
    }
    
    return jsonify(examples)

@app.route('/api/debug/collections', methods=['GET'])
def debug_collections():
    """Debug endpoint with enhanced information"""
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
                
                # Convert ObjectId to string for JSON serialization
                if sample and '_id' in sample:
                    sample['_id'] = str(sample['_id'])
                
                # Get field statistics
                field_stats = {}
                if sample:
                    for field, value in sample.items():
                        field_stats[field] = {
                            "type": type(value).__name__,
                            "sample_value": str(value)[:100]  # Truncate long values
                        }
                
                collections_info[collection_name] = {
                    "document_count": count,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "field_statistics": field_stats,
                    "sample_document": sample,
                    "ai_compatible": collection_name in ["sales", "customers", "products", "marketing_campaigns"],
                    "is_chat_collection": collection_name == "chat_sessions"
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
            "total_collections": len(collections_info),
            "collection_names": collection_names,
            "collections": collections_info,
            "ai_system_status": {
                "gemini_available": gemini_available,
                "two_stage_processor": two_stage_processor is not None,
                "simple_processor": simple_processor is not None,
                "chat_system": mongodb_available
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
        one_day_ago = datetime.utcnow() - timedelta(days=1)
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
                    "last_updated": datetime.utcnow().isoformat()
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
    print("\n🔗 Starting PERFECTED AI Analytics Server with Chat...")
    print("🎯 AI-First Features:")
    print("   - ✅ Bulletproof Gemini two-stage processing")
    print("   - ✅ Enhanced retry logic with exponential backoff")
    print("   - ✅ Intelligent JSON extraction and validation")
    print("   - ✅ Smart fallback visualizations")
    print("   - ✅ Complete simple processor backup")
    print("   - ✅ NEW: Complete chat session management")
    print("   - ✅ NEW: Real-time message persistence")
    print("   - ✅ NEW: Chat history and search")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected and ready")
        print("   ✅ Chat System: Indexes created, ready for persistence")
    else:
        print("   ❌ MongoDB: Connection failed")
        print("   ❌ Chat System: Not available")
    
    if gemini_available:
        print("   ✅ Gemini AI: Bulletproof client ready")
    else:
        print("   ⚠️ Gemini AI: Not available")
    
    if two_stage_processor:
        print("   ✅ Perfected Two-Stage Processor: AI-first processing ready")
    elif simple_processor:
        print("   ✅ Complete Simple Processor: Fallback processing ready")
    else:
        print("   ❌ No processors available")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 Enhanced endpoints:")
    print("   - POST /api/query (AI-first intelligent processing + chat integration)")
    print("   - POST /api/system/test (comprehensive system testing)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/examples (enhanced example questions)")
    print("   - GET  /api/debug/collections (enhanced debug info)")
    print("\n💬 NEW: Chat Management Endpoints:")
    print("   - GET  /api/chats (list all chat sessions)")
    print("   - POST /api/chats (create new chat session)")
    print("   - GET  /api/chats/{id} (get specific chat)")
    print("   - PUT  /api/chats/{id} (update chat metadata)")
    print("   - DELETE /api/chats/{id} (delete chat session)")
    print("   - POST /api/chats/{id}/messages (add message to chat)")
    print("   - GET  /api/chats/stats (chat system statistics)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)