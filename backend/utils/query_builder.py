import json
import re
import logging
from datetime import datetime, timedelta
from config import DATABASE_SCHEMA, CHART_TYPE_MAPPING

logger = logging.getLogger(__name__)

class QueryBuilder:
    """Utility class for building and validating MongoDB queries"""
    
    def __init__(self, db):
        self.db = db
        self.schema = DATABASE_SCHEMA['collections']
    
    def validate_pipeline(self, pipeline, collection_name):
        """Validate MongoDB aggregation pipeline"""
        try:
            if not isinstance(pipeline, list):
                raise ValueError("Pipeline must be a list")
            
            if collection_name not in self.schema:
                raise ValueError(f"Unknown collection: {collection_name}")
            
            # Basic validation - check for required fields
            valid_fields = self.schema[collection_name]['fields']
            
            # Additional validation can be added here
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid pipeline: {str(e)}")
    
    def optimize_pipeline(self, pipeline):
        """Optimize MongoDB aggregation pipeline for better performance"""
        optimized = []
        
        for stage in pipeline:
            # Move $match stages to the beginning when possible
            if '$match' in stage:
                optimized.insert(0, stage)
            else:
                optimized.append(stage)
        
        # Add default limit if not present
        has_limit = any('$limit' in stage for stage in optimized)
        if not has_limit:
            optimized.append({"$limit": 50})
        
        return optimized
    
    def add_date_filters(self, pipeline, date_range=None):
        """Add date filters to pipeline based on common patterns"""
        if not date_range:
            return pipeline
        
        # Add date matching stage
        date_match = {}
        if date_range == "last_month":
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            date_match = {
                "date": {
                    "$gte": last_month.replace(day=1),
                    "$lte": last_month
                }
            }
        elif date_range == "last_quarter":
            # Add logic for last quarter
            pass
        
        if date_match:
            pipeline.insert(0, {"$match": date_match})
        
        return pipeline
    
    def get_collection_info(self, collection_name):
        """Get metadata about a collection"""
        if collection_name not in self.schema:
            return None
        
        return {
            "name": collection_name,
            "fields": self.schema[collection_name]['fields'],
            "numeric_fields": self.schema[collection_name].get('numeric_fields', []),
            "date_fields": self.schema[collection_name].get('date_fields', []),
            "sample_count": self.db[collection_name].count_documents({})
        }

class ChartTypeSelector:
    """Utility class for selecting appropriate chart types"""
    
    @staticmethod
    def determine_chart_type(query_intent, data_structure):
        """Determine the best chart type based on query intent and data"""
        
        # Time-based queries
        if any(keyword in query_intent.lower() for keyword in ['trend', 'over time', 'monthly', 'quarterly', 'daily']):
            return 'line'
        
        # Distribution queries
        if any(keyword in query_intent.lower() for keyword in ['distribution', 'breakdown', 'split', 'percentage']):
            return 'pie'
        
        # Comparison queries
        if any(keyword in query_intent.lower() for keyword in ['compare', 'vs', 'versus', 'top', 'ranking']):
            return 'bar'
        
        # Default based on data structure
        if data_structure:
            if len(data_structure) <= 5:
                return 'pie'
            else:
                return 'bar'
        
        return 'bar'
    
    @staticmethod
    def get_chart_config(chart_type, title="Analytics Chart"):
        """Get Chart.js configuration for different chart types"""
        
        base_config = {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": title
                }
            }
        }
        
        if chart_type in ['pie', 'doughnut']:
            base_config["plugins"]["legend"] = {"display": True}
        else:
            base_config["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
            base_config["plugins"]["legend"] = {"display": False}
        
        return base_config

class PromptBuilder:
    """Utility class for building prompts for Gemini"""
    
    @staticmethod
    def build_query_prompt(user_question, schema_info):
        """Build a comprehensive prompt for query generation"""
        
        prompt = f"""
You are an expert MongoDB query generator and data analyst. Your task is to convert natural language questions into MongoDB aggregation pipelines and determine the best visualization approach.

AVAILABLE COLLECTIONS AND SCHEMA:
{json.dumps(schema_info, indent=2)}

USER QUESTION: "{user_question}"

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON - no markdown, no explanations, no extra text
2. Use this exact format:

{{
    "collection": "sales|products|customers",
    "mongo_query": "[MongoDB aggregation pipeline as JSON string]",
    "chart_type": "bar|pie|line|doughnut",
    "chart_mapping": {{
        "labels_field": "_id",
        "data_field": "total_sales",
        "title": "Chart Title"
    }},
    "query_intent": "brief description"
}}

MONGODB RULES:
- Use aggregation pipeline syntax: [{{"$group": {{}}}}, {{"$sort": {{}}}}, {{"$limit": 10}}]
- Always include $sort stage for better visualization
- Limit results to 10 items maximum
- Use meaningful field names in $group stage
- For sales analysis, typically group by product_name, category, or region

CHART TYPE SELECTION:
- bar: comparisons, rankings, top items
- pie/doughnut: distributions, percentages
- line: trends over time

EXAMPLE RESPONSE:
{{"collection": "sales", "mongo_query": "[{{\\"$group\\": {{\\"_id\\": \\"$product_name\\", \\"total_sales\\": {{\\"$sum\\": \\"$total_amount\\"}}}}}}, {{\\"$sort\\": {{\\"total_sales\\": -1}}}}, {{\\"$limit\\": 5}}]", "chart_type": "bar", "chart_mapping": {{"labels_field": "_id", "data_field": "total_sales", "title": "Top 5 Selling Products"}}, "query_intent": "Find top performing products"}}

Now respond with JSON only:"""
        
        return prompt
    
    @staticmethod
    def build_summary_prompt(user_question, query_results, query_intent):
        """Build prompt for generating text summaries"""
        
        prompt = f"""
Generate a concise, insightful summary based on the user's question and query results.

USER QUESTION: "{user_question}"
QUERY_INTENT: "{query_intent}"
RESULTS: {json.dumps(query_results[:5], default=str)}

REQUIREMENTS:
- 2-3 sentences maximum
- Include specific numbers/percentages
- Highlight key insights or trends
- Use professional but conversational tone
- Direct answer to the user's question
- Actionable insights when relevant

EXAMPLE:
"Based on your sales data, the MacBook Pro 14 is your top performer with $15,999 in revenue, followed by the iPhone 15 Pro at $8,999. This represents 45% of your total laptop sales, suggesting strong demand for premium Apple products."
"""
        return prompt

def validate_json_response(response_text):
    """Extract and validate JSON from Gemini response with improved error handling"""
    try:
        # Clean the response text
        cleaned_text = response_text.strip()
        logger.debug(f"Attempting to parse response: {cleaned_text[:200]}...")
        
        # Method 1: Try to parse as direct JSON
        try:
            result = json.loads(cleaned_text)
            logger.debug("Successfully parsed as direct JSON")
            return result
        except json.JSONDecodeError:
            pass
        
        # Method 2: Look for JSON code blocks (```json ... ```)
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
        if json_block_match:
            try:
                result = json.loads(json_block_match.group(1))
                logger.debug("Successfully extracted JSON from code block")
                return result
            except json.JSONDecodeError:
                pass
        
        # Method 3: Find JSON object with improved regex
        # Look for complete JSON objects from { to }
        json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_text)
        
        for match in json_matches:
            try:
                potential_json = match.group()
                result = json.loads(potential_json)
                logger.debug("Successfully extracted JSON using regex")
                return result
            except json.JSONDecodeError:
                continue
        
        # Method 4: Try to extract JSON with nested braces
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        potential_json = cleaned_text[start_idx:i+1]
                        result = json.loads(potential_json)
                        logger.debug("Successfully extracted JSON using brace counting")
                        return result
                    except json.JSONDecodeError:
                        continue
        
        # If all methods fail, log the actual response for debugging
        logger.error(f"Failed to extract JSON from response. Full response: {response_text}")
        raise ValueError(f"Could not extract valid JSON from Gemini response")
        
    except Exception as e:
        logger.error(f"JSON validation error: {str(e)}")
        raise ValueError(f"Invalid JSON in response: {str(e)}")

def create_fallback_response(user_question):
    """Create a fallback response when Gemini fails"""
    question_lower = user_question.lower()
    
    logger.info(f"Creating fallback response for: {user_question}")
    
    # Analyze the question to determine intent
    if any(word in question_lower for word in ['top', 'best', 'highest', 'most']):
        if any(word in question_lower for word in ['product', 'products', 'selling']):
            return {
                "collection": "sales",
                "mongo_query": '[{"$group": {"_id": "$product_name", "total_sales": {"$sum": "$total_amount"}}}, {"$sort": {"total_sales": -1}}, {"$limit": 10}]',
                "chart_type": "bar",
                "chart_mapping": {
                    "labels_field": "_id",
                    "data_field": "total_sales",
                    "title": "Top Selling Products"
                },
                "query_intent": "Find top performing products by sales revenue"
            }
        elif any(word in question_lower for word in ['customer', 'customers']):
            return {
                "collection": "customers",
                "mongo_query": '[{"$sort": {"total_spent": -1}}, {"$limit": 10}]',
                "chart_type": "bar",
                "chart_mapping": {
                    "labels_field": "name",
                    "data_field": "total_spent",
                    "title": "Top Customers by Spending"
                },
                "query_intent": "Find top customers by total spending"
            }
    
    elif any(word in question_lower for word in ['region', 'regions', 'location']):
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$region", "total_sales": {"$sum": "$total_amount"}}}, {"$sort": {"total_sales": -1}}]',
            "chart_type": "pie",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_sales",
                "title": "Sales by Region"
            },
            "query_intent": "Analyze sales distribution by region"
        }
    
    elif any(word in question_lower for word in ['category', 'categories']):
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$category", "total_sales": {"$sum": "$total_amount"}}}, {"$sort": {"total_sales": -1}}]',
            "chart_type": "doughnut",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_sales",
                "title": "Sales by Category"
            },
            "query_intent": "Analyze sales distribution by product category"
        }
    
    elif any(word in question_lower for word in ['quarter', 'quarterly', 'q1', 'q2', 'q3', 'q4']):
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$quarter", "total_sales": {"$sum": "$total_amount"}}}, {"$sort": {"_id": 1}}]',
            "chart_type": "line",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_sales",
                "title": "Quarterly Sales Trend"
            },
            "query_intent": "Analyze sales trends by quarter"
        }
    
    else:
        # Default fallback - overview of sales by category
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$category", "total_sales": {"$sum": "$total_amount"}}}, {"$sort": {"total_sales": -1}}, {"$limit": 8}]',
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_sales",
                "title": "Sales Overview by Category"
            },
            "query_intent": "General sales overview by product category"
        }

def safe_json_loads(json_string):
    """Safely load JSON string with better error messages"""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error at position {e.pos}: {e.msg}")
        logger.error(f"Problematic JSON string: {json_string}")
        raise ValueError(f"Invalid JSON format: {e.msg} at position {e.pos}")

def format_number(value):
    """Format numbers for display"""
    if isinstance(value, (int, float)):
        if value >= 1000000:
            return f"${value/1000000:.1f}M"
        elif value >= 1000:
            return f"${value/1000:.1f}K"
        else:
            return f"${value:.2f}"
    return str(value)