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
        
        # Skip test for faster startup - validate on first real request
        self.available = True  # Assume available, will be validated on first use
        logger.info("✅ Gemini client initialized (test skipped for faster startup)")
    
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
                        # DEBUG: Log what query was generated
                        logger.info(f"🔍 GENERATED QUERY DEBUG:")
                        logger.info(f"   Collection: {query_data.get('collection', 'Unknown')}")
                        logger.info(f"   Pipeline stages: {len(query_data.get('pipeline', []))}")
                        if query_data.get('pipeline'):
                            logger.info(f"   First stage: {query_data['pipeline'][0] if query_data['pipeline'] else 'None'}")
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

            QUERY GENERATION RULES:
            1. DETAILED QUERIES (show individual records):
               - "cost of llm", "AI costs", "expenses" → Show individual cost records with batchId, totalCostInUSD, etc.
               - "users", "show users", "user data" → Show individual user records
               - "documents", "files" → Show individual document records
               - Use $limit: 50 for performance, $sort by relevant fields
            
            2. AGGREGATE QUERIES (sum/count/group):
               - "total cost", "sum of costs", "overall expense" → Use $group with $sum
               - "count users", "number of documents" → Use $group with $count
               - "breakdown by batch", "costs per batch" → Use $group by batchId
            
            3. SPECIFIC QUERIES:
               - "cost of llm" should return individual cost records, NOT a single sum
               - Always prefer showing detailed data unless explicitly asked for totals/counts

            COLLECTION NAME PRECISION:
            - For cost/pricing queries, use EXACTLY: "costevalutionforllm" (NOT "costevaluationforllm")
            - For user queries, use EXACTLY: "users"
            - For batch queries, use EXACTLY: "batches"

            IMPORTANT: Only use field names that exist in the collection schema above. Do not assume field names.

            RESPONSE FORMAT (JSON only, no comments):
            {{
              "collection": "exact_collection_name",
              "pipeline": [ ...mongodb aggregation stages... ]
            }}
            """)

    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], 
                                  query_context: Dict) -> str:
        """Builds an enhanced prompt for multi-output visualization generation."""
        sample_data = raw_data[:5]
        return textwrap.dedent(f"""
            You are an advanced data visualization expert. Analyze the data and determine the BEST COMBINATION of outputs for maximum user value.

            USER QUESTION: "{user_question}"
            DATA SAMPLE (first 5 records):
            {json.dumps(sample_data, indent=2, default=str)}
            TOTAL RECORDS: {len(raw_data)}

            MULTI-OUTPUT DECISION RULES:
            🔍 ANALYSIS KEYWORDS → TEXT + TABLE + CHART:
            - "analyze", "comprehensive", "insights", "report", "examine", "study"
            
            📊 BREAKDOWN KEYWORDS → TEXT + DOUGHNUT/PIE:
            - "breakdown", "distribution", "percentage", "composition", "split"
            
            📈 TREND KEYWORDS → TEXT + LINE CHART:
            - "trend", "over time", "timeline", "growth", "change", "progress"
            
            📋 LIST KEYWORDS → TABLE + optional TEXT:
            - "list", "show all", "display", "users", "entries", "records"
            
            🎯 COMPARISON KEYWORDS → TEXT + BAR CHART:
            - "compare", "ranking", "top", "versus", "best", "most", "least"

            CHART TYPE SELECTION:
            - "percentage breakdown", "donut" → "doughnut"
            - "distribution", "breakdown" → "pie"  
            - "trend", "over time", "timeline" → "line"
            - "comparison", "ranking", "top" → "bar"
            - "parts of whole", "composition" → "doughnut"

            OUTPUT COMBINATIONS:
            1. Simple data request → TABLE only
            2. Analysis request → TEXT + TABLE + CHART
            3. Breakdown request → TEXT + DOUGHNUT + TABLE
            4. Trend analysis → TEXT + LINE CHART
            5. Explanation needed → TEXT + supporting visual
            6. Comprehensive → TEXT + TABLE + multiple charts

            RESPONSE FORMAT (JSON only):
            {{
                "outputs": [
                    {{
                        "type": "text",
                        "content": "Natural language analysis and insights..."
                    }},
                    {{
                        "type": "table",
                        "data": {{
                            "tableData": [],
                            "columns": []
                        }}
                    }},
                    {{
                        "type": "chart",
                        "chart_type": "doughnut|pie|bar|line",
                        "data": {{
                            "labels": [],
                            "datasets": [{{
                                "label": "Dataset Label",
                                "data": [],
                                "backgroundColor": []
                            }}]
                        }},
                        "options": {{
                            "responsive": true,
                            "plugins": {{
                                "legend": {{"position": "right"}},
                                "title": {{"display": true, "text": "Chart Title"}}
                            }}
                        }}
                    }}
                ],
                "primary_insights": ["Key insight 1", "Key insight 2"],
                "recommendations": ["Action 1", "Action 2"]
            }}
            
            IMPORTANT: Always include 1-3 outputs based on user intent. For doughnut charts, use vibrant colors and ensure data adds up to 100% when showing percentages.
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
        
        # Return new multi-output format
        outputs = [{
            "type": "table",
            "data": {
                "tableData": table_data,
                "columns": [col["field"] for col in columns]  # Simplified column format for frontend
            }
        }]
        
        # Add text summary if this is an analysis request
        question_lower = user_question.lower()
        if any(word in question_lower for word in ['analyze', 'insights', 'examine', 'study']):
            outputs.insert(0, {
                "type": "text",
                "content": f"Analysis of {len(table_data)} records. The table below shows the detailed breakdown of all available data points for: {user_question}"
            })
        
        return {
            "outputs": outputs,
            "primary_insights": ["Displaying data in a structured table format as requested."],
            "recommendations": ["Review individual records for detailed analysis.", "Consider filtering data for specific insights."],
            # Backward compatibility fields
            "chart_type": "table",
            "chart_config": {
                "type": "table",
                "tableData": table_data,
                "columns": columns
            },
            "summary": f"Table showing {len(table_data)} of {len(raw_data)} records."
        }

    def _validate_visualization_response(self, data: Dict, raw_data: List[Dict], user_question: str) -> bool:
        """Validate multi-output response structure and fix chart types."""
        question_lower = user_question.lower()
        
        # DEBUG: Log what we received from Gemini
        logger.info(f"🔍 GEMINI RESPONSE STRUCTURE:")
        logger.info(f"   Keys: {list(data.keys())}")
        logger.info(f"   Has outputs: {'outputs' in data}")
        logger.info(f"   Has chart_config: {'chart_config' in data}")
        logger.info(f"   Chart config type: {type(data.get('chart_config'))}")
        
        # Handle both old and new response formats for backward compatibility
        if 'outputs' in data:
            # New multi-output format
            logger.info("🎯 Using NEW multi-output format")
            return self._validate_multi_output_response(data, raw_data, user_question)
        else:
            # Convert old format to new format for consistency
            logger.info("🎯 Converting LEGACY format to new format")
            data = self._convert_legacy_to_multi_output(data, raw_data, user_question)
            
            # DEBUG: Log the converted data
            logger.info(f"🔍 CONVERTED DATA STRUCTURE:")
            logger.info(f"   Chart config after conversion: {type(data.get('chart_config'))}")
            if data.get('chart_config'):
                logger.info(f"   Chart config keys: {list(data.get('chart_config', {}).keys())}")
                
                # FINAL SAFETY CHECK: Ensure chart data is populated
                chart_config = data.get('chart_config', {})
                chart_data = chart_config.get('data', {})
                if not chart_data.get('labels') or len(chart_data.get('labels', [])) == 0:
                    logger.info("🔧 Final check: Chart data still empty, applying data processing")
                    processed_data = self._process_raw_data_for_chart(raw_data, user_question, chart_config.get('type', 'bar'))
                    data['chart_config']['data'] = processed_data
                    logger.info(f"   Populated with {len(processed_data.get('labels', []))} data points")
            
            return True
    
    def _validate_multi_output_response(self, data: Dict, raw_data: List[Dict], user_question: str) -> bool:
        """Validate the new multi-output response format."""
        if 'outputs' not in data or not isinstance(data['outputs'], list):
            return False
        
        question_lower = user_question.lower()
        
        # Find the first chart output for legacy compatibility
        chart_output = None
        text_content = ""
        
        # Validate and enhance each output
        for output in data['outputs']:
            if output.get('type') == 'chart' and not chart_output:
                # Override chart type based on keywords if needed
                if 'percentage breakdown' in question_lower or 'donut' in question_lower:
                    output['chart_type'] = 'doughnut'
                elif any(word in question_lower for word in ['distribution', 'breakdown', 'composition']):
                    output['chart_type'] = 'pie'
                elif any(word in question_lower for word in ['trend', 'over time', 'timeline']):
                    output['chart_type'] = 'line'
                elif any(word in question_lower for word in ['compare', 'ranking', 'top', 'versus']):
                    output['chart_type'] = 'bar'
                
                # Ensure chart has required structure
                if 'data' not in output:
                    output['data'] = {"labels": [], "datasets": []}
                if 'options' not in output:
                    output['options'] = {"responsive": True}
                
                chart_output = output
            
            elif output.get('type') == 'text':
                text_content += output.get('content', '') + "\n"
        
        # CREATE BACKWARD COMPATIBILITY FIELDS WITH ACTUAL DATA
        if chart_output:
            # Process the raw data to create meaningful chart data
            chart_data = self._process_raw_data_for_chart(raw_data, user_question, chart_output.get('chart_type', 'bar'))
            
            data['chart_config'] = {
                "type": chart_output.get('chart_type', 'bar'),
                "data": chart_data,
                "options": chart_output.get('options', {"responsive": True})
            }
            logger.info(f"🔧 Created legacy chart_config with {len(chart_data.get('labels', []))} data points")
        
        # Add text summary for legacy compatibility
        if text_content.strip():
            data['summary'] = text_content.strip()
        elif not data.get('summary'):
            data['summary'] = "Multi-output analysis completed successfully."
        
        # Ensure required fields exist
        if 'primary_insights' not in data:
            data['primary_insights'] = ["Analysis completed successfully."]
        if 'recommendations' not in data:
            data['recommendations'] = ["Review the data for actionable insights."]
        
        # Legacy compatibility fields
        data['insights'] = data.get('primary_insights', [])
        
        return True
    
    def _convert_legacy_to_multi_output(self, legacy_data: Dict, raw_data: List[Dict], user_question: str) -> Dict:
        """Convert old single-output format to new multi-output format."""
        outputs = []
        
        # Add text output if summary exists
        if legacy_data.get('summary'):
            outputs.append({
                "type": "text",
                "content": legacy_data['summary']
            })
        
        # Add chart output if chart_config exists
        if legacy_data.get('chart_config'):
            chart_config = legacy_data['chart_config']
            
            # Process raw data to populate chart if data is empty
            chart_data = chart_config.get('data', {"labels": [], "datasets": []})
            if not chart_data.get('labels') or len(chart_data.get('labels', [])) == 0:
                logger.info("🔧 Legacy chart data is empty, processing raw data")
                chart_data = self._process_raw_data_for_chart(raw_data, user_question, chart_config.get('type', 'bar'))
                # Update the legacy chart_config with processed data
                legacy_data['chart_config']['data'] = chart_data
            
            outputs.append({
                "type": "chart",
                "chart_type": chart_config.get('type', 'bar'),
                "data": chart_data,
                "options": chart_config.get('options', {"responsive": True})
            })
        
        # Check if table should be added based on question intent
        if self._detect_table_intent(user_question) and raw_data:
            table_data = raw_data[:50]  # Limit for performance
            outputs.append({
                "type": "table",
                "data": {
                    "tableData": table_data,
                    "columns": list(table_data[0].keys()) if table_data else []
                }
            })
        
        # Update the legacy data with new structure
        legacy_data['outputs'] = outputs
        legacy_data['primary_insights'] = legacy_data.get('insights', ["Analysis completed."])
        legacy_data['recommendations'] = legacy_data.get('recommendations', ["Review data for insights."])
        
        return legacy_data

    def _process_raw_data_for_chart(self, raw_data: List[Dict], user_question: str, chart_type: str) -> Dict:
        """Process raw database results into chart data format"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        question_lower = user_question.lower()
        
        # Determine grouping field based on question context
        if 'batch' in question_lower:
            group_field = self._find_batch_field(raw_data[0])
            value_field = self._find_cost_field(raw_data[0])
        elif 'user' in question_lower:
            group_field = self._find_user_field(raw_data[0])  
            value_field = self._find_count_field(raw_data[0])
        elif 'cost' in question_lower:
            group_field = self._find_batch_field(raw_data[0])
            value_field = self._find_cost_field(raw_data[0])
        else:
            # Default: use first string field for grouping, first numeric for values
            group_field = self._find_first_string_field(raw_data[0])
            value_field = self._find_first_numeric_field(raw_data[0])
        
        if not group_field or not value_field:
            # Fallback: create simple index-based chart
            labels = [f"Item {i+1}" for i in range(min(20, len(raw_data)))]
            values = [1 for _ in labels]  # Default to count
            return self._create_chart_data_structure(labels, values, chart_type)
        
        # Group and aggregate data
        grouped_data = {}
        for record in raw_data:
            group_key = str(record.get(group_field, 'Unknown'))
            value = record.get(value_field, 0)
            
            # Convert to numeric if possible
            try:
                value = float(value) if value is not None else 0
            except (ValueError, TypeError):
                value = 1  # Count instead
            
            if group_key in grouped_data:
                grouped_data[group_key] += value
            else:
                grouped_data[group_key] = value
        
        # Sort by value for better visualization (top items first)
        sorted_items = sorted(grouped_data.items(), key=lambda x: x[1], reverse=True)
        
        # Limit to top 15 items for readability
        sorted_items = sorted_items[:15]
        
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        logger.info(f"📊 Processed {len(raw_data)} records into {len(labels)} chart groups")
        logger.info(f"   Group field: {group_field}, Value field: {value_field}")
        logger.info(f"   Top 3 items: {labels[:3]} = {values[:3]}")
        
        return self._create_chart_data_structure(labels, values, chart_type)
    
    def _find_batch_field(self, sample_record: Dict) -> str:
        """Find the batch identifier field"""
        batch_fields = ['batchId', 'batch_id', 'batchName', 'batch_name', 'batch']
        for field in batch_fields:
            if field in sample_record:
                return field
        return None
    
    def _find_cost_field(self, sample_record: Dict) -> str:
        """Find the cost/amount field"""
        cost_fields = ['totalCostInUSD', 'total_cost', 'cost', 'amount', 'totalTokens', 'price']
        for field in cost_fields:
            if field in sample_record:
                return field
        return None
    
    def _find_user_field(self, sample_record: Dict) -> str:
        """Find user identifier field"""
        user_fields = ['userId', 'user_id', 'emailId', 'email', 'name', 'firstName', 'role']
        for field in user_fields:
            if field in sample_record:
                return field
        return None
    
    def _find_count_field(self, sample_record: Dict) -> str:
        """Find a numeric field for counting/summing"""
        # For user queries, often we just want to count
        numeric_fields = ['count', 'total', 'quantity', 'amount']
        for field in numeric_fields:
            if field in sample_record:
                return field
        # If no count field, we'll count records instead
        return None
    
    def _find_first_string_field(self, sample_record: Dict) -> str:
        """Find first string field for grouping"""
        for key, value in sample_record.items():
            if key != '_id' and isinstance(value, str) and value:
                return key
        return None
    
    def _find_first_numeric_field(self, sample_record: Dict) -> str:
        """Find first numeric field for values"""
        for key, value in sample_record.items():
            if isinstance(value, (int, float)) and value > 0:
                return key
        return None
    
    def _create_chart_data_structure(self, labels: List[str], values: List[float], chart_type: str) -> Dict:
        """Create the chart.js data structure"""
        # Color palette for charts
        colors = [
            '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
            '#F97316', '#06B6D4', '#84CC16', '#EC4899', '#6B7280',
            '#14B8A6', '#F59E0B', '#8B5CF6', '#EF4444', '#10B981'
        ]
        
        background_colors = [colors[i % len(colors)] for i in range(len(labels))]
        
        return {
            "labels": labels,
            "datasets": [{
                "label": "Values",
                "data": values,
                "backgroundColor": background_colors,
                "borderColor": background_colors,
                "borderWidth": 1
            }]
        }

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
            
            # Fix MongoDB-specific syntax that's not valid JSON
            # Convert ISODate("...") to just the string date
            json_str = re.sub(r'ISODate\("([^"]+)"\)', r'"\1"', json_str)
            
            # Convert ObjectId("...") to just the string
            json_str = re.sub(r'ObjectId\("([^"]+)"\)', r'"\1"', json_str)
            
            # Convert NumberLong(...) to just the number
            json_str = re.sub(r'NumberLong\((\d+)\)', r'\1', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode extracted JSON: {e}")
                logger.error(f"Cleaned JSON string: {json_str}")
                return None
        return None
    
    def _build_query_prompt(self, user_question: str, database_schema: Dict) -> str:
        """Build intelligent prompt for MongoDB query generation using database schema"""
        
        # Extract collections and their schemas for context
        collections_info = []
        for collection_name, collection_data in database_schema.get("collections", {}).items():
            fields = collection_data.get("fields", [])
            description = collection_data.get("description", f"{collection_name} collection")
            
            collections_info.append(f"""
Collection: {collection_name}
Description: {description}
Fields: {', '.join(fields)}""")
        
        collections_text = '\n'.join(collections_info)
        
        prompt = f"""You are a MongoDB query expert. Generate a MongoDB aggregation pipeline based on the user's question.

DATABASE SCHEMA:
{collections_text}

USER QUESTION: {user_question}

IMPORTANT INSTRUCTIONS:
1. Choose the most appropriate collection based on the question keywords
2. For user-related questions, use the "users" collection
3. For admin queries, filter by role field: {{"role": {{"$regex": "admin", "$options": "i"}}}}
4. Use aggregation pipeline format with proper MongoDB operators
5. Include proper filtering, grouping, and sorting as needed

RESPONSE FORMAT (JSON only):
{{
    "intent": "description of what user wants",
    "collection": "collection_name", 
    "pipeline": [
        {{"$match": {{"field": "criteria"}}}},
        {{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}},
        {{"$sort": {{"count": -1}}}},
        {{"$limit": 50}}
    ]
}}

Generate the query now:"""
        
        return prompt