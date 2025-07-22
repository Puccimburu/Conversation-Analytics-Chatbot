from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import os
import logging
from datetime import datetime
import pymongo
import json
import google.generativeai as genai
from typing import Dict, Any, List, Optional
import re
import time

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
print("🚀 PERFECTED AI ANALYTICS - BULLETPROOF GEMINI TWO-STAGE")
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

# Bulletproof Gemini Client
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
                        max_output_tokens=1200,
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
        """Generate visualization with enhanced retry logic"""
        
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
                        temperature=0.1,  # Low for consistency
                        max_output_tokens=2000,
                        top_p=0.8
                    )
                )
                
                if response and response.text:
                    parsed_result = self._extract_json_from_response(response.text)
                    
                    if parsed_result and self._validate_and_fix_visualization_response(parsed_result, raw_data):
                        logger.info(f"✅ Gemini visualization generation successful on attempt {attempt + 1}")
                        return {"success": True, "data": parsed_result}
                    else:
                        logger.warning(f"Invalid visualization response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Gemini visualization attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 8)
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

CHART TYPE SELECTION RULES:
- "top", "best", "ranking", "comparison" → "bar"
- "distribution", "breakdown", "segments", "by category" → "pie" or "doughnut"  
- "trends", "over time", "monthly", "quarterly" → "line"
- "revenue by category", "sales by region" → "doughnut"

COMPREHENSIVE EXAMPLES:

For "What were our top 5 selling products in June 2024?":
{{
  "collection": "sales",
  "pipeline": [
    {{"$match": {{"month": "June"}}}},
    {{"$group": {{"_id": "$product_name", "total_revenue": {{"$sum": "$total_amount"}}, "total_quantity": {{"$sum": "$quantity"}}}}}},
    {{"$sort": {{"total_revenue": -1}}}},
    {{"$limit": 5}}
  ],
  "chart_hint": "bar",
  "query_intent": "Find top 5 products by revenue in June 2024"
}}

For "Show me customer distribution by segment":
{{
  "collection": "customers",
  "pipeline": [
    {{"$group": {{"_id": "$customer_segment", "customer_count": {{"$sum": 1}}, "total_spending": {{"$sum": "$total_spent"}}, "avg_spending": {{"$avg": "$total_spent"}}}}}},
    {{"$sort": {{"customer_count": -1}}}}
  ],
  "chart_hint": "pie",
  "query_intent": "Analyze customer distribution across segments"
}}

For "Show me sales revenue by category":
{{
  "collection": "sales",
  "pipeline": [
    {{"$group": {{"_id": "$category", "total_revenue": {{"$sum": "$total_amount"}}, "order_count": {{"$sum": 1}}}}}},
    {{"$sort": {{"total_revenue": -1}}}}
  ],
  "chart_hint": "doughnut",
  "query_intent": "Revenue breakdown by product category"
}}

For "Show me monthly sales trends for 2024":
{{
  "collection": "sales",
  "pipeline": [
    {{"$match": {{"date": {{"$gte": "2024-01-01T00:00:00.000Z"}}}}}},
    {{"$group": {{"_id": "$month", "total_revenue": {{"$sum": "$total_amount"}}, "order_count": {{"$sum": 1}}}}}},
    {{"$sort": {{"_id": 1}}}}
  ],
  "chart_hint": "line",
  "query_intent": "Monthly sales trend analysis for 2024"
}}

For "Top customers by order value":
{{
  "collection": "customers",
  "pipeline": [
    {{"$sort": {{"total_spent": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar",
  "query_intent": "Ranking customers by total spending"
}}

For "Marketing campaign performance":
{{
  "collection": "marketing_campaigns",
  "pipeline": [
    {{"$group": {{"_id": "$name", "total_revenue": {{"$sum": "$revenue_generated"}}, "conversion_rate": {{"$avg": "$conversion_rate"}}, "roi": {{"$avg": {{"$divide": ["$revenue_generated", "$spent"]}}}}}}}},
    {{"$sort": {{"total_revenue": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar",
  "query_intent": "Campaign performance analysis by revenue"
}}

For "Show me inventory levels for low-stock products":
{{
  "collection": "products",
  "pipeline": [
    {{"$match": {{"stock": {{"$lt": 50}}}}}},
    {{"$sort": {{"stock": 1}}}},
    {{"$limit": 15}}
  ],
  "chart_hint": "bar",
  "query_intent": "Products with low inventory levels"
}}

SPECIAL HANDLING:
- For "this quarter", "Q1", "Q2" etc: Use appropriate date filters
- For "this year", "2024": Match year in date field
- For "best", "top": Always sort descending and limit results
- For "low", "worst": Sort ascending
- For "trends": Group by time periods (month, quarter)

JSON only - no other text:"""

    def _build_enhanced_visualization_prompt(self, user_question: str, raw_data: List[Dict], query_context: Dict) -> str:
        """Build comprehensive visualization prompt"""
        sample_data = raw_data[:5] if raw_data else []
        
        return f"""You are an expert data visualization designer. Create perfect Chart.js configurations with insights.

USER QUESTION: "{user_question}"
QUERY CONTEXT: {json.dumps(query_context, indent=2)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations
2. Create production-ready Chart.js configuration
3. Generate specific insights with actual numbers
4. Choose colors that match the data story

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["Label1", "Label2"],
      "datasets": [{{
        "label": "Dataset Name",
        "data": [100, 200],
        "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
        "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "maintainAspectRatio": false,
      "plugins": {{
        "title": {{"display": true, "text": "Descriptive Chart Title", "font": {{"size": 16}}}},
        "legend": {{"display": true, "position": "bottom"}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true, "title": {{"display": true, "text": "Y-axis Label"}}}},
        "x": {{"title": {{"display": true, "text": "X-axis Label"}}}}
      }}
    }}
  }},
  "summary": "Comprehensive 2-3 sentence summary with specific numbers, percentages, and key insights",
  "insights": [
    "Specific insight with actual data point (e.g., 'Product X leads with $50,000 revenue')",
    "Comparative insight (e.g., 'Category A outperforms Category B by 45%')",
    "Trend or pattern insight (e.g., 'Premium segment shows 23% higher spending')"
  ],
  "recommendations": [
    "Actionable business recommendation based on the data",
    "Strategic suggestion for improvement or optimization"
  ]
}}

COLOR SCHEMES:
Bar Charts: Professional blues and greens
Pie/Doughnut: Diverse palette with good contrast
Line Charts: Single color with gradient fill

CHART TYPE MAPPING:
- Rankings/Comparisons → bar chart
- Distributions/Segments → pie chart  
- Revenue by category → doughnut chart
- Trends over time → line chart

EXAMPLES:

For bar chart data like revenue by product:
{{
  "chart_type": "bar",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["ProductA", "ProductB"],
      "datasets": [{{
        "label": "Revenue ($)",
        "data": [15000, 12000],
        "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
        "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "Top Product Revenue"}},
        "legend": {{"display": false}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true, "title": {{"display": true, "text": "Revenue ($)"}}}},
        "x": {{"title": {{"display": true, "text": "Products"}}}}
      }}
    }}
  }},
  "summary": "ProductA leads with $15,000 revenue, followed by ProductB at $12,000, showing a 25% performance difference.",
  "insights": [
    "ProductA generates 55.6% of total revenue from top products",
    "Revenue gap of $3,000 between top two products",
    "Both products show strong performance above $10,000 threshold"
  ],
  "recommendations": [
    "Focus marketing efforts on ProductA success factors",
    "Analyze what makes ProductA outperform to apply to ProductB"
  ]
}}

JSON only - no other text:"""

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Enhanced JSON extraction with multiple fallback methods"""
        try:
            cleaned_text = response_text.strip()
            
            # Method 1: Direct JSON parsing
            try:
                result = json.loads(cleaned_text)
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass
            
            # Method 2: Extract from code blocks
            json_patterns = [
                r'```(?:json)?\s*(\{.*?\})\s*```',
                r'```(\{.*?\})```',
                r'`(\{.*?\})`'
            ]
            
            for pattern in json_patterns:
                match = re.search(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        continue
            
            # Method 3: Find JSON object boundaries with better logic
            brace_count = 0
            start_idx = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(cleaned_text):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
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
                                if isinstance(result, dict) and len(result) > 2:  # Valid JSON object
                                    return result
                            except json.JSONDecodeError:
                                continue
                            finally:
                                start_idx = -1
                                brace_count = 0
            
            # Method 4: Try to fix common JSON issues
            fixed_text = cleaned_text
            # Remove trailing commas
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
            # Fix single quotes
            fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
            
            try:
                return json.loads(fixed_text)
            except json.JSONDecodeError:
                pass
            
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
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
            
            # Validate pipeline
            pipeline = data.get('pipeline', [])
            if not isinstance(pipeline, list) or len(pipeline) == 0:
                return False
            
            # Validate collection name
            valid_collections = ['sales', 'products', 'customers', 'marketing_campaigns']
            if data['collection'] not in valid_collections:
                data['collection'] = 'sales'  # Default to sales
            
            # Validate chart hint
            valid_charts = ['bar', 'pie', 'line', 'doughnut']
            if data['chart_hint'] not in valid_charts:
                data['chart_hint'] = 'bar'  # Default
            
            # Ensure pipeline has sort and limit for performance
            has_sort = any('$sort' in stage for stage in pipeline)
            has_limit = any('$limit' in stage for stage in pipeline)
            
            if not has_sort:
                # Add default sort
                if len(pipeline) > 0 and '$group' in str(pipeline):
                    pipeline.append({"$sort": {"_id": 1}})
            
            if not has_limit:
                # Add reasonable limit
                pipeline.append({"$limit": 50})
            
            return True
            
        except Exception as e:
            logger.error(f"Query validation error: {e}")
            return False
    
    def _validate_and_fix_visualization_response(self, data: Dict, raw_data: List[Dict]) -> bool:
        """Validate and fix visualization response"""
        try:
            # Check required fields
            required_fields = ['chart_type', 'chart_config', 'summary']
            
            if 'chart_type' not in data:
                data['chart_type'] = 'bar'
            
            if 'chart_config' not in data:
                # Create basic chart config
                data['chart_config'] = self._create_basic_chart_config(data['chart_type'], raw_data)
            
            if 'summary' not in data:
                data['summary'] = f"Analysis completed with {len(raw_data)} data points."
            
            if 'insights' not in data:
                data['insights'] = [f"Found {len(raw_data)} records", "Data analysis completed"]
            
            if 'recommendations' not in data:
                data['recommendations'] = ["Review the data patterns", "Consider strategic implications"]
            
            # Validate chart config structure
            chart_config = data['chart_config']
            if not isinstance(chart_config, dict):
                data['chart_config'] = self._create_basic_chart_config(data['chart_type'], raw_data)
                return True
            
            # Ensure required chart config fields
            if 'type' not in chart_config:
                chart_config['type'] = data['chart_type']
            
            if 'data' not in chart_config:
                chart_config['data'] = self._extract_chart_data(raw_data)
            
            if 'options' not in chart_config:
                chart_config['options'] = {
                    "responsive": True,
                    "plugins": {"title": {"display": True, "text": "Data Analysis"}}
                }
            
            return True
            
        except Exception as e:
            logger.error(f"Visualization validation error: {e}")
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

# Complete Simple Query Processor (Fixed)
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
            
            # Sales by region
            elif any(word in question_lower for word in ["region", "geographic", "territory"]):
                return self._sales_by_region()
            
            # Customer segments
            elif "customer" in question_lower and any(word in question_lower for word in ["segment", "distribution", "breakdown"]):
                return self._customer_segments()
            
            # Revenue by category
            elif any(word in question_lower for word in ["category", "categories"]) and any(word in question_lower for word in ["revenue", "sales"]):
                return self._revenue_by_category()
            
            # Monthly trends
            elif any(word in question_lower for word in ["month", "trend", "quarterly", "time"]):
                return self._monthly_trends()
            
            # Marketing campaigns
            elif any(word in question_lower for word in ["campaign", "marketing", "conversion"]):
                return self._marketing_campaigns()
            
            # Inventory/stock
            elif any(word in question_lower for word in ["inventory", "stock", "low-stock"]):
                return self._inventory_levels()
            
            # Customer analysis
            elif "customer" in question_lower and any(word in question_lower for word in ["total", "spending", "value"]):
                return self._customer_analysis()
            
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
                "order_count": {"$sum": 1},
                "avg_price": {"$avg": "$unit_price"}
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
    
    def _sales_by_region(self):
        """Sales breakdown by region"""
        pipeline = [
            {"$group": {
                "_id": "$region",
                "total_revenue": {"$sum": "$total_amount"},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        
        results = list(self.db.sales.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No regional data found"}
        
        total_revenue = sum(r['total_revenue'] for r in results)
        summary = "Regional sales: "
        for result in results:
            region = result['_id']
            revenue = result['total_revenue']
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            summary += f"{region} ${revenue:,.2f} ({percentage:.1f}%), "
        
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['total_revenue'] for r in results],
                    "backgroundColor": [
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(16, 185, 129, 0.8)", 
                        "rgba(245, 158, 11, 0.8)",
                        "rgba(239, 68, 68, 0.8)"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Sales by Region"}}
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total regions: {len(results)}", f"Leading region: {results[0]['_id']}"],
            "recommendations": ["Focus on underperforming regions", "Expand successful regional strategies"],
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
    
    def _monthly_trends(self):
        """Monthly sales trends"""
        pipeline = [
            {"$group": {
                "_id": "$month",
                "total_revenue": {"$sum": "$total_amount"},
                "order_count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        results = list(self.db.sales.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No monthly data found"}
        
        total_revenue = sum(r['total_revenue'] for r in results)
        avg_monthly = total_revenue / len(results) if results else 0
        
        summary = f"Monthly trends across {len(results)} months: Total ${total_revenue:,.2f}, Average per month: ${avg_monthly:,.2f}"
        
        chart_config = {
            "type": "line",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Monthly Revenue",
                    "data": [r['total_revenue'] for r in results],
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": True,
                    "tension": 0.1,
                    "borderWidth": 3,
                    "pointBackgroundColor": "rgba(59, 130, 246, 1)",
                    "pointRadius": 5
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Monthly Sales Trends"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total months: {len(results)}", f"Peak month: {max(results, key=lambda x: x['total_revenue'])['_id']}"],
            "recommendations": ["Identify seasonal patterns", "Plan for peak periods"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _marketing_campaigns(self):
        """Marketing campaign performance"""
        pipeline = [
            {"$group": {
                "_id": "$name",
                "total_revenue": {"$sum": "$revenue_generated"},
                "total_spent": {"$sum": "$spent"},
                "avg_conversion": {"$avg": "$conversion_rate"},
                "avg_ctr": {"$avg": "$ctr"}
            }},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.marketing_campaigns.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No marketing campaign data found"}
        
        summary = f"Marketing campaigns: Top {len(results)} by revenue. "
        for result in results[:3]:
            campaign = result['_id']
            revenue = result['total_revenue']
            conversion = result['avg_conversion']
            summary += f"{campaign}: ${revenue:,.2f} ({conversion:.1f}% conversion), "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Revenue Generated ($)",
                    "data": [r['total_revenue'] for r in results],
                    "backgroundColor": "rgba(16, 185, 129, 0.8)",
                    "borderColor": "rgba(16, 185, 129, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Marketing Campaign Performance"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total campaigns: {len(results)}", f"Top performer: {results[0]['_id']}"],
            "recommendations": ["Scale successful campaigns", "Optimize underperforming campaigns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _inventory_levels(self):
        """Inventory levels analysis"""
        pipeline = [
            {"$match": {"stock": {"$lt": 100}}},  # Low stock threshold
            {"$sort": {"stock": 1}},
            {"$limit": 15}
        ]
        
        results = list(self.db.products.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No low-stock products found"}
        
        summary = f"Low inventory alert: {len(results)} products below 100 units. "
        if results:
            lowest = results[0]
            summary += f"Lowest stock: {lowest['name']} ({lowest['stock']} units). "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['name'] for r in results],
                "datasets": [{
                    "label": "Stock Level",
                    "data": [r['stock'] for r in results],
                    "backgroundColor": "rgba(239, 68, 68, 0.8)",
                    "borderColor": "rgba(239, 68, 68, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Low Stock Products"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Products needing restock: {len(results)}", "Urgent attention required"],
            "recommendations": ["Reorder low-stock items", "Review inventory management"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _customer_analysis(self):
        """Customer spending analysis"""
        pipeline = [
            {"$sort": {"total_spent": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.customers.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No customer data found"}
        
        total_spending = sum(r['total_spent'] for r in results)
        summary = f"Top {len(results)} customers by spending: Total ${total_spending:,.2f}. "
        if results:
            top_customer = results[0]
            summary += f"Top spender: {top_customer['name']} (${top_customer['total_spent']:,.2f}). "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['name'] for r in results],
                "datasets": [{
                    "label": "Total Spent ($)",
                    "data": [r['total_spent'] for r in results],
                    "backgroundColor": "rgba(147, 51, 234, 0.8)",
                    "borderColor": "rgba(147, 51, 234, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Top Customers by Spending"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"High-value customers: {len(results)}", "Strong customer loyalty"],
            "recommendations": ["Reward top customers", "Develop VIP programs"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _show_available_data(self):
        """Show what data is available"""
        try:
            collections_info = []
            for collection_name in ["sales", "customers", "products", "marketing_campaigns"]:
                count = self.db[collection_name].count_documents({})
                collections_info.append(f"{collection_name}: {count} records")
            
            summary = f"Available data: {', '.join(collections_info)}. Try asking about: smartphone vs laptop sales, top products, sales by region, customer segments, revenue by category, monthly trends, marketing campaigns, or inventory levels."
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'Compare smartphone vs laptop sales'",
                    "Try: 'Show me customer segments'",
                    "Try: 'What's our revenue by category?'",
                    "Try: 'Show me monthly sales trends'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {"success": False, "error": f"Could not retrieve data info: {str(e)}"}

# Perfected Two-Stage Processor
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
                    "date_fields": ["date"],
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
                },
                "marketing_campaigns": {
                    "description": "Marketing campaign performance",
                    "fields": ["campaign_id", "name", "type", "start_date", "end_date", "budget", "spent", "impressions", "clicks", "conversions", "revenue_generated", "target_audience", "ctr", "conversion_rate"],
                    "sample_values": {"type": ["Email", "Google Ads", "Social Media", "Influencer", "Display Ads"]},
                    "numeric_fields": ["budget", "spent", "impressions", "clicks", "conversions", "revenue_generated", "ctr", "conversion_rate"]
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
                        "ai_powered": True,
                        "stage_details": {
                            "stage_1": "gemini_success",
                            "stage_2": "gemini_success"
                        }
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
                        "ai_powered": True,
                        "stage_details": {
                            "stage_1": "gemini_success",
                            "stage_2": "enhanced_fallback"
                        }
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
                            "Check if you're asking about available data",
                            "Try: 'Show me what data is available'"
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
            
            logger.info(f"Database query executed: {len(results)} results from {collection_name}")
            
            # Log sample results for debugging
            if results and len(results) > 0:
                logger.info(f"Sample result: {results[0]}")
            
            return results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            logger.error(f"Collection: {query_data.get('collection')}")
            logger.error(f"Pipeline: {query_data.get('pipeline')}")
            return None
    
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
            # Get label
            label = str(item.get('_id', 'Unknown'))
            if isinstance(item.get('_id'), dict):
                # Handle complex _id objects
                label = str(list(item['_id'].values())[0]) if item['_id'] else 'Unknown'
            labels.append(label)
            
            # Get value
            value = 0
            for field in ['total_revenue', 'total_spent', 'total_amount', 'customer_count', 'order_count', 'stock', 'count', 'revenue_generated']:
                if field in item and item[field] is not None:
                    value = float(item[field])
                    break
            values.append(value)
        
        # Color schemes based on chart type
        if chart_hint in ['pie', 'doughnut']:
            colors = [
                "rgba(59, 130, 246, 0.8)",   # Blue
                "rgba(16, 185, 129, 0.8)",   # Green
                "rgba(245, 158, 11, 0.8)",   # Yellow
                "rgba(239, 68, 68, 0.8)",    # Red
                "rgba(147, 51, 234, 0.8)",   # Purple
                "rgba(236, 72, 153, 0.8)"    # Pink
            ]
            backgroundColor = colors[:len(labels)]
        else:
            backgroundColor = "rgba(59, 130, 246, 0.8)"
        
        # Chart configuration
        chart_config = {
            "type": chart_hint,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Values",
                    "data": values,
                    "backgroundColor": backgroundColor,
                    "borderColor": "rgba(59, 130, 246, 1)" if chart_hint not in ['pie', 'doughnut'] else None,
                    "borderWidth": 2 if chart_hint not in ['pie', 'doughnut'] else None
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {"display": True, "text": "Enhanced Data Analysis"},
                    "legend": {"display": chart_hint in ['pie', 'doughnut'], "position": "bottom"}
                }
            }
        }
        
        # Add scales for non-pie charts
        if chart_hint not in ['pie', 'doughnut']:
            chart_config["options"]["scales"] = {
                "y": {"beginAtZero": True, "title": {"display": True, "text": "Values"}},
                "x": {"title": {"display": True, "text": "Categories"}}
            }
        
        # Generate smart summary
        total_value = sum(values) if values else 0
        avg_value = total_value / len(values) if values else 0
        max_item = max(raw_results, key=lambda x: x.get('total_revenue', x.get('total_spent', x.get('total_amount', 0)))) if raw_results else None
        
        summary = f"Enhanced analysis of {len(raw_results)} data points. "
        if max_item:
            max_label = str(max_item.get('_id', 'Unknown'))
            max_value = max(values) if values else 0
            summary += f"Top performer: {max_label} with {max_value:,.2f}. "
        summary += f"Total value: {total_value:,.2f}, Average: {avg_value:,.2f}."
        
        # Generate insights
        insights = [
            f"Analyzed {len(raw_results)} records successfully",
            f"Data range: {min(values):.2f} to {max(values):.2f}" if values else "No numeric data available",
            "Enhanced fallback visualization applied"
        ]
        
        # Generate recommendations
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
            "two_stage_processor": "available" if two_stage_processor else "unavailable"
        },
        "version": "3.0.0-perfected-ai-system"
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Perfected query processing with AI priority"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"🔍 Processing question with perfected system: '{user_question}'")
        
        # Prioritize two-stage processor (AI-first approach)
        if two_stage_processor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    two_stage_processor.process_question(user_question)
                )
            finally:
                loop.close()
            
            if result.get("success"):
                logger.info(f"✅ Perfected query successful: {result.get('results_count', 0)} results")
                return jsonify(result)
            else:
                logger.error(f"❌ Perfected query failed: {result.get('error')}")
                return jsonify(result), 400
        
        elif simple_processor:
            # Fallback to simple processor
            result = simple_processor.process_question(user_question)
            
            if result.get("success"):
                result["query_source"] = "simple_only"
                result["ai_powered"] = False
                logger.info(f"✅ Simple query successful: {result.get('results_count', 0)} results")
                return jsonify(result)
            else:
                logger.error(f"❌ Simple query failed: {result.get('error')}")
                return jsonify(result), 400
        
        else:
            return jsonify({
                "error": "No query processor available",
                "details": "System not properly initialized"
            }), 503
            
    except Exception as e:
        logger.error(f"❌ Critical error in perfected query processing: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/api/query/force-ai', methods=['POST'])
def force_ai_query():
    """Force use of AI processing only"""
    if not two_stage_processor or not gemini_available:
        return jsonify({
            "error": "AI processing not available",
            "details": "Gemini not initialized or unavailable"
        }), 503
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"🤖 FORCE AI Processing: '{user_question}'")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                two_stage_processor.process_question(user_question)
            )
        finally:
            loop.close()
        
        # Only return AI results, no fallback
        if result.get("success") and result.get("ai_powered", False):
            logger.info(f"✅ Force AI successful: {result.get('results_count', 0)} results")
            return jsonify(result)
        else:
            return jsonify({
                "error": "AI processing failed",
                "details": result.get("error", "Unknown AI error"),
                "suggestions": [
                    "Try rephrasing your question",
                    "Use simpler terms",
                    "Check if question relates to available data"
                ]
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Force AI error: {str(e)}")
        return jsonify({
            "error": "AI processing failed",
            "details": str(e)
        }), 500

@app.route('/api/batch_query', methods=['POST'])
def batch_process_queries():
    """Process multiple queries with perfected system"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        
        if not questions or not isinstance(questions, list):
            return jsonify({"error": "Questions array is required"}), 400
        
        if len(questions) > 8:
            return jsonify({"error": "Maximum 8 questions per batch"}), 400
        
        logger.info(f"🔄 Batch processing {len(questions)} questions with perfected system")
        
        results = []
        processor = two_stage_processor if two_stage_processor else simple_processor
        
        if not processor:
            return jsonify({"error": "No query processor available"}), 503
        
        for i, question in enumerate(questions):
            try:
                if two_stage_processor:
                    # Use perfected two-stage processor
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            two_stage_processor.process_question(question)
                        )
                    finally:
                        loop.close()
                else:
                    # Use simple processor
                    result = simple_processor.process_question(question)
                
                if result.get("success"):
                    results.append({
                        "question": question,
                        "success": True,
                        "summary": result.get("summary"),
                        "chart_data": result.get("chart_data"),
                        "insights": result.get("insights", []),
                        "recommendations": result.get("recommendations", []),
                        "results_count": result.get("results_count", 0),
                        "execution_time": result.get("execution_time", 0),
                        "ai_powered": result.get("ai_powered", False),
                        "query_source": result.get("query_source", "unknown")
                    })
                else:
                    results.append({
                        "question": question,
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "suggestions": result.get("suggestions", [])
                    })
                    
            except Exception as e:
                logger.error(f"Batch question {i+1} failed: {e}")
                results.append({
                    "question": question,
                    "success": False,
                    "error": f"Processing failed: {str(e)}"
                })
        
        successful_count = sum(1 for r in results if r.get("success"))
        ai_powered_count = sum(1 for r in results if r.get("success") and r.get("ai_powered"))
        total_time = sum(r.get("execution_time", 0) for r in results)
        
        return jsonify({
            "batch_success": True,
            "results": results,
            "batch_summary": {
                "total_questions": len(questions),
                "successful": successful_count,
                "failed": len(questions) - successful_count,
                "ai_powered": ai_powered_count,
                "simple_fallback": successful_count - ai_powered_count,
                "success_rate": f"{(successful_count / len(questions) * 100):.1f}%",
                "ai_success_rate": f"{(ai_powered_count / len(questions) * 100):.1f}%",
                "total_execution_time": round(total_time, 2),
                "average_execution_time": round(total_time / len(questions), 2) if questions else 0
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Batch processing error: {str(e)}")
        return jsonify({"error": "Batch processing failed", "details": str(e)}), 500

@app.route('/api/system/test', methods=['POST'])
def test_system_components():
    """Test all system components"""
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
                "Show me sales by region",
                "What are our top selling products?",
                "Show me monthly sales trends for 2024"
            ]
        },
        "ai_powered_advanced": {
            "description": "Advanced questions that work best with AI processing",
            "questions": [
                "What were our top 5 selling products in June 2024?",
                "Show me conversion rates by marketing campaign",
                "Which products have the lowest inventory levels?",
                "Analyze customer lifetime value by segment",
                "Compare Q1 vs Q2 performance across all regions",
                "What's the seasonal pattern in our sales data?",
                "Show me marketing campaign ROI analysis",
                "Which customer segments show the highest retention?"
            ]
        },
        "chart_type_examples": {
            "bar_charts": [
                "Top 10 products by revenue",
                "Sales performance by sales rep",
                "Best performing marketing campaigns",
                "Customer ranking by total spending"
            ],
            "pie_charts": [
                "Customer distribution by segment",
                "Product mix by brand",
                "Geographic customer distribution"
            ],
            "doughnut_charts": [
                "Revenue breakdown by category",
                "Sales distribution by region",
                "Marketing spend by campaign type"
            ],
            "line_charts": [
                "Monthly sales trends for 2024",
                "Quarterly revenue growth",
                "Customer acquisition trends over time"
            ]
        },
        "data_entities": {
            "product_categories": ["Smartphones", "Laptops", "Audio", "Tablets", "Monitors", "Accessories"],
            "regions": ["North America", "Europe", "Asia-Pacific"],
            "customer_segments": ["Regular", "Premium", "VIP"],
            "time_periods": ["January", "February", "March", "April", "May", "June", "July", "Q1", "Q2", "2024"],
            "metrics": ["revenue", "sales", "quantity", "customers", "conversion", "ROI"]
        },
        "system_capabilities": {
            "ai_features": [
                "Natural language understanding",
                "Intelligent chart type selection",
                "Context-aware insights generation",
                "Automated recommendations"
            ],
            "fallback_features": [
                "Pattern-based query processing",
                "Guaranteed response for common questions",
                "Fast processing times",
                "Reliable basic analytics"
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
                    "ai_compatible": collection_name in ["sales", "customers", "products", "marketing_campaigns"]
                }
            except Exception as e:
                collections_info[collection_name] = {
                    "error": str(e),
                    "document_count": -1,
                    "ai_compatible": False
                }
        
        return jsonify({
            "database_name": db.name,
            "total_collections": len(collections_info),
            "collection_names": collection_names,
            "collections": collections_info,
            "ai_system_status": {
                "gemini_available": gemini_available,
                "two_stage_processor": two_stage_processor is not None,
                "simple_processor": simple_processor is not None
            }
        })
        
    except Exception as e:
        logger.error(f"Debug collections failed: {str(e)}")
        return jsonify({"error": f"Debug failed: {str(e)}"}), 500

if __name__ == '__main__':
    print("\n🔗 Starting PERFECTED AI Analytics Server...")
    print("🎯 AI-First Features:")
    print("   - ✅ Bulletproof Gemini two-stage processing")
    print("   - ✅ Enhanced retry logic with exponential backoff")
    print("   - ✅ Intelligent JSON extraction and validation")
    print("   - ✅ Smart fallback visualizations")
    print("   - ✅ Complete simple processor backup")
    print("   - ✅ Advanced batch processing")
    print("   - ✅ Force AI mode for testing")
    print("   - ✅ Comprehensive system testing")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected and ready")
    else:
        print("   ❌ MongoDB: Connection failed")
    
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
    print("   - POST /api/query (AI-first intelligent processing)")
    print("   - POST /api/query/force-ai (AI-only processing)")
    print("   - POST /api/batch_query (batch processing with AI)")
    print("   - POST /api/system/test (comprehensive system testing)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/examples (enhanced example questions)")
    print("   - GET  /api/debug/collections (enhanced debug info)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)