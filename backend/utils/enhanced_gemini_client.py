# backend/utils/enhanced_gemini_client.py

import asyncio
import json
import logging
import re
import textwrap
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class BulletproofGeminiClient:
    """
    Enhanced Gemini client with robust error handling, clean prompts, and native async calls.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.max_retries = 3
        
        # Test the connection and set availability
        try:
            test_response = self.model.generate_content("Test")
            self.available = True
            logger.info("✅ Gemini client initialized and tested")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
    
    async def generate_query(self, user_question: str, database_schema: Dict) -> Dict:
        """
        Stage 1: Generate MongoDB query from user question - FIXED SYNC VERSION
        """
        logger.info("🔍 Gemini Stage 1 - Query Generation (attempt 1)")
        prompt = self._build_query_prompt(user_question, database_schema)
        
        for attempt in range(self.max_retries):
            try:
                # FIXED: Use synchronous generate_content (no async version exists)
                response = self.model.generate_content(prompt)
                if response and response.text:
                    query_data = self._extract_json_from_response(response.text)
                    if query_data:
                        logger.info("✅ Successfully generated query")
                        return {"success": True, "data": query_data}
                logger.warning(f"Query generation attempt {attempt + 1} failed, retrying...")
            except Exception as e:
                logger.error(f"Query generation attempt {attempt + 1} failed: {str(e)}")
                
            # FIXED: Use synchronous sleep in Flask/async context
            if attempt < self.max_retries - 1:
                import time
                time.sleep(1)
        
        return {"success": False, "error": "Failed to generate query after retries"}
    
    async def generate_visualization(self, user_question: str, raw_data: List[Dict], 
                                   query_context: Dict) -> Dict:
        """
        Stage 2: Generate visualization from raw data with enhanced table support - FIXED SYNC VERSION
        """
        logger.info("🧠 Gemini Stage 2 - Visualization Generation (attempt 1)")
        
        # Check if we should skip visualization entirely
        if self._should_skip_visualization(user_question, raw_data):
            logger.info("📝 Skipping visualization - returning text-only response")
            return {
                "success": True, 
                "data": {
                    "summary": "The provided data contains insufficient information to create a meaningful visualization.",
                    "insights": ["No meaningful data available for analysis."],
                    "recommendations": ["Try a more specific query or check if data exists for this request."],
                    "text_only": True
                }
            }
        
        force_table = self._detect_table_intent(user_question)
        
        if force_table:
            logger.info("🎯 Table intent detected, forcing table format")
            return {"success": True, "data": self._force_table_format({}, raw_data, user_question)}
        
        prompt = self._build_visualization_prompt(user_question, raw_data, query_context)
        
        for attempt in range(self.max_retries):
            try:
                # FIXED: Use synchronous generate_content (no async version exists)
                response = self.model.generate_content(prompt)
                if response and response.text:
                    viz_data = self._extract_json_from_response(response.text)
                    if viz_data:
                        if self._validate_visualization_response(viz_data, raw_data, user_question):
                            logger.info("✅ Successfully generated visualization")
                            return {"success": True, "data": viz_data}
                logger.warning(f"Visualization attempt {attempt + 1} failed, retrying...")
            except Exception as e:
                logger.error(f"Visualization attempt {attempt + 1} failed: {str(e)}")
                
            # FIXED: Use synchronous sleep in Flask/async context  
            if attempt < self.max_retries - 1:
                import time
                time.sleep(1)
        
        logger.info("🔧 Falling back to forced table format")
        return {"success": True, "data": self._force_table_format({}, raw_data, user_question)}

    def _build_query_prompt(self, user_question: str, database_schema: Dict) -> str:
        """Builds a clean, readable prompt for query generation."""
        collections_info = "\n".join([
            f"- {name}: {schema.get('description', '')} (fields: {', '.join(schema.get('fields', [])[:8])})" 
            for name, schema in database_schema.get("collections", {}).items()
        ])
        
        return textwrap.dedent(f"""
            You are a MongoDB query expert. Your task is to convert a user's question into a valid MongoDB aggregation pipeline.

            DATABASE COLLECTIONS WITH FIELDS:
            {collections_info}

            USER QUESTION: "{user_question}"

            IMPORTANT: Only use field names that exist in the collection schema above. Do not assume field names.

            RESPONSE FORMAT (JSON only, no comments):
            {{
              "collection": "exact_collection_name",
              "pipeline": [ ...mongodb aggregation stages... ]
            }}
            """)

    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], 
                                  query_context: Dict) -> str:
        """Builds a clean, readable prompt for visualization generation."""
        sample_data = raw_data[:5]
        return textwrap.dedent(f"""
            You are a data visualization expert. Analyze the provided data and generate a summary, insights, and a chart configuration.

            USER QUESTION: "{user_question}"
            DATA SAMPLE (first 5 records):
            {json.dumps(sample_data, indent=2, default=str)}
            TOTAL RECORDS: {len(raw_data)}

            CHART TYPE SELECTION (MANDATORY):
            - If user asks about "distribution", "breakdown", "percentage" → ALWAYS use "pie"
            - If user asks about "trend", "over time", "timeline" → ALWAYS use "line"  
            - If user asks about "comparison", "ranking", "top", "by" → use "bar"
            - If user asks about "percentage breakdown" specifically → use "doughnut"
            - DEFAULT: use "bar" only if none of the above keywords match

            RESPONSE FORMAT (JSON only, no comments):
            {{
                "summary": "A natural language summary of the findings.",
                "insights": ["Insight 1.", "Insight 2."],
                "recommendations": ["Recommendation 1.", "Recommendation 2."],
                "chart_config": {{
                    "type": "bar",
                    "data": {{"labels": [], "datasets": []}},
                    "options": {{}}
                }}
            }}
            """)

    def _detect_table_intent(self, user_question: str) -> bool:
        """Detects if user wants a table based on keywords."""
        question_lower = user_question.lower()
        table_keywords = ["show all", "list all", "display all", "in a table", "raw data", "list of", "show users"]
        return any(keyword in question_lower for keyword in table_keywords)
    
    def _should_skip_visualization(self, user_question: str, raw_data: List[Dict]) -> bool:
        """Detects if the response should be text-only without charts."""
        question_lower = user_question.lower()
        
        # Skip visualization for informational queries
        text_only_keywords = [
            "what is", "how do", "how to", "explain", "define", "meaning of",
            "help", "guide", "tutorial", "documentation", "why", "when"
        ]
        
        if any(keyword in question_lower for keyword in text_only_keywords):
            return True
        
        # Skip if no meaningful data (empty, null, or insufficient data)
        if not raw_data or len(raw_data) == 0:
            return True
            
        # Skip if all data is null/empty
        meaningful_data = [item for item in raw_data if item and any(v for v in item.values() if v is not None)]
        if len(meaningful_data) == 0:
            return True
            
        # Skip if only one data point with null values (like your document types case)
        if len(raw_data) == 1:
            first_item = raw_data[0]
            if not first_item or all(v is None for k, v in first_item.items() if k != '_id'):
                return True
        
        return False

    def _force_table_format(self, viz_data: Dict, raw_data: List[Dict], user_question: str) -> Dict:
        """Force conversion to table format, trusting that raw_data is already clean."""
        logger.info("🔧 Converting to table format (using pre-cleaned data)")

        table_data = raw_data[:100]  # Limit for performance
        columns = []
        if table_data:
            first_record = table_data[0]
            for field in first_record.keys():
                if field == '_id' and len(first_record) > 1: continue
                columns.append({
                    "key": field, "field": field, "label": field.replace('_', ' ').title(),
                    "type": "string", "align": "left"
                })
        
        return {
            "chart_type": "table",
            "chart_config": {
                "type": "table",
                "tableData": table_data,
                "columns": columns,
                "data": {"labels": [], "datasets": []},
                "options": {"responsive": True, "plugins": {"title": {"display": True, "text": f"Table: {user_question}"}}}
            },
            "summary": f"Table showing {len(table_data)} of {len(raw_data)} records.",
            "insights": ["Displaying data in a table format as requested."],
            "recommendations": ["Review individual records for detailed analysis."]
        }

    def _validate_visualization_response(self, data: Dict, raw_data: List[Dict], user_question: str) -> bool:
        """Validate and fix chart type based on question keywords."""
        if 'chart_config' not in data:
            data['chart_config'] = {}
        if 'summary' not in data:
            data['summary'] = "Analysis complete."
        
        # Override chart type if Gemini chose incorrectly
        chart_config = data['chart_config']
        question_lower = user_question.lower()
        
        # Force chart type based on keywords
        if any(word in question_lower for word in ['distribution', 'breakdown']):
            chart_config['type'] = 'pie'
            logger.info(f"🔧 Overriding chart type to 'pie' for distribution question")
        elif 'percentage breakdown' in question_lower:
            chart_config['type'] = 'doughnut'
            logger.info(f"🔧 Overriding chart type to 'doughnut' for percentage breakdown")
        elif any(word in question_lower for word in ['trend', 'over time', 'timeline']):
            chart_config['type'] = 'line'
            logger.info(f"🔧 Overriding chart type to 'line' for trend question")
        
        return True

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extracts JSON from a string, stripping markdown and comments."""
        # First strip markdown code fences
        cleaned_text = re.sub(r'```(?:json)?\n?', '', response_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\n?```', '', cleaned_text)
        
        # Extract JSON object
        match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            
            # Remove JavaScript-style comments that break JSON parsing
            json_str = re.sub(r'//.*?(?=\n|$)', '', json_str, flags=re.MULTILINE)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            # Clean up extra whitespace and trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode extracted JSON: {e}")
                logger.error(f"Cleaned JSON string: {json_str}")
                return None
        return None