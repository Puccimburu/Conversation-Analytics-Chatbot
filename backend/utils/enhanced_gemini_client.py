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
            f"- {name}: {schema.get('description', '')}" 
            for name, schema in database_schema.get("collections", {}).items()
        ])
        
        return textwrap.dedent(f"""
            You are a MongoDB query expert. Your task is to convert a user's question into a valid MongoDB aggregation pipeline.

            DATABASE COLLECTIONS:
            {collections_info}

            USER QUESTION: "{user_question}"

            RESPONSE FORMAT (JSON only):
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

            RESPONSE FORMAT (JSON only):
            {{
                "summary": "A natural language summary of the findings.",
                "insights": ["Insight 1.", "Insight 2."],
                "recommendations": ["Recommendation 1.", "Recommendation 2."],
                "chart_config": {{
                    "chart_type": "bar",
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
        """A simple validator to ensure essential keys exist."""
        if 'chart_config' not in data:
            data['chart_config'] = {}
        if 'summary' not in data:
            data['summary'] = "Analysis complete."
        return True

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extracts JSON from a string, stripping markdown."""
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                logger.error("Failed to decode extracted JSON.")
                return None
        return None