import json
import re
from datetime import datetime, timedelta
from config import DATABASE_SCHEMA, CHART_TYPE_MAPPING

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

REQUIREMENTS:
1. Generate a valid MongoDB aggregation pipeline as a JSON array
2. Choose the most appropriate collection to query
3. Select the best chart type for visualization
4. Define field mappings for chart creation

RESPONSE FORMAT (JSON only):
{{
    "collection": "collection_name",
    "mongo_query": "[{{\\"$match\\": {{}}}}, {{\\"$group\\": {{}}}}]",
    "chart_type": "bar|pie|line|doughnut",
    "chart_mapping": {{
        "labels_field": "_id",
        "data_field": "total",
        "title": "Descriptive Chart Title"
    }},
    "query_intent": "brief description of what the query does"
}}

RULES:
- Use proper MongoDB aggregation syntax
- Include $sort and $limit stages for better presentation
- For time-based queries, use line charts
- For categorical comparisons, use bar charts
- For distributions/percentages, use pie/doughnut charts
- Limit results to 15 items for readability
- Use meaningful field names in grouping
- Include proper date filtering when temporal keywords are used

EXAMPLES:
Question: "Top 5 selling products"
Response: {{"collection": "sales", "mongo_query": "[{{\\"$group\\": {{\\"_id\\": \\"$product_name\\", \\"total_sales\\": {{\\"$sum\\": \\"$total_amount\\"}}}}}}, {{\\"$sort\\": {{\\"total_sales\\": -1}}}}, {{\\"$limit\\": 5}}]", "chart_type": "bar", "chart_mapping": {{"labels_field": "_id", "data_field": "total_sales", "title": "Top 5 Selling Products"}}, "query_intent": "Find top performing products by sales revenue"}}
"""
        return prompt
    
    @staticmethod
    def build_summary_prompt(user_question, query_results, query_intent):
        """Build prompt for generating text summaries"""
        
        prompt = f"""
Generate a concise, insightful summary based on the user's question and query results.

USER QUESTION: "{user_question}"
QUERY INTENT: "{query_intent}"
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
    """Extract and validate JSON from Gemini response"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            # Try to parse the entire response as JSON
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in response: {str(e)}")

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