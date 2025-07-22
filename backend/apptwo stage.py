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
print("🚀 ENHANCED WORKING ANALYTICS - SIMPLE + GEMINI TWO-STAGE")
print("=" * 60)
print(f"📊 Database: {MONGODB_URI}")
print(f"🔑 API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Database Connection (Working Version)
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

# Enhanced Gemini Client
class EnhancedGeminiClient:
    """Simple but bulletproof Gemini client"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test the connection
        try:
            test_response = self.model.generate_content("Hello")
            self.available = True
            logger.info("✅ Gemini client initialized and tested")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
    
    async def generate_query(self, user_question: str, schema_info: Dict, max_retries: int = 3) -> Dict:
        """Generate MongoDB query with retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        prompt = self._build_query_prompt(user_question, schema_info)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Gemini Stage 1 - Query Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1000,
                        top_p=0.8
                    )
                )
                
                if response and response.text:
                    parsed_result = self._extract_json_from_response(response.text)
                    
                    if parsed_result and self._validate_query_response(parsed_result):
                        logger.info(f"✅ Gemini query generation successful on attempt {attempt + 1}")
                        return {"success": True, "data": parsed_result}
                    else:
                        logger.warning(f"Invalid response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # Progressive delay
        
        logger.error("❌ Gemini query generation failed after all retries")
        return {"success": False, "error": "Failed to generate query after retries"}
    
    async def generate_visualization(self, user_question: str, raw_data: List[Dict], query_context: Dict, max_retries: int = 3) -> Dict:
        """Generate visualization with retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        prompt = self._build_visualization_prompt(user_question, raw_data, query_context)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📊 Gemini Stage 2 - Visualization Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=1500,
                        top_p=0.9
                    )
                )
                
                if response and response.text:
                    parsed_result = self._extract_json_from_response(response.text)
                    
                    if parsed_result and self._validate_visualization_response(parsed_result):
                        logger.info(f"✅ Gemini visualization generation successful on attempt {attempt + 1}")
                        return {"success": True, "data": parsed_result}
                    else:
                        logger.warning(f"Invalid visualization response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Gemini visualization attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
        
        logger.error("❌ Gemini visualization generation failed after all retries")
        return {"success": False, "error": "Failed to generate visualization after retries"}
    
    def _build_query_prompt(self, user_question: str, schema_info: Dict) -> str:
        """Build enhanced prompt for query generation"""
        return f"""You are an expert MongoDB query generator. Convert natural language to MongoDB aggregation pipelines.

USER QUESTION: "{user_question}"

DATABASE SCHEMA:
{json.dumps(schema_info, indent=2)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations
2. Use exact field names from schema
3. Create efficient aggregation pipelines

RESPONSE FORMAT (JSON only):
{{
  "collection": "sales|products|customers|marketing_campaigns",
  "pipeline": [
    {{"$match": {{"field": "value"}}}},
    {{"$group": {{"_id": "$field", "metric": {{"$sum": "$value"}}}}}},
    {{"$sort": {{"metric": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar|pie|line|doughnut",
  "query_intent": "Brief description of what this query achieves"
}}

EXAMPLES:

For "Compare smartphone vs laptop sales":
{{
  "collection": "sales",
  "pipeline": [
    {{"$match": {{"category": {{"$in": ["Smartphones", "Laptops"]}}}}}},
    {{"$group": {{"_id": "$category", "total_revenue": {{"$sum": "$total_amount"}}, "total_quantity": {{"$sum": "$quantity"}}}}}},
    {{"$sort": {{"total_revenue": -1}}}}
  ],
  "chart_hint": "bar",
  "query_intent": "Compare revenue between smartphone and laptop categories"
}}

JSON only - no other text:"""

    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], query_context: Dict) -> str:
        """Build enhanced prompt for visualization generation"""
        sample_data = raw_data[:3] if raw_data else []
        
        return f"""You are a data visualization expert. Create Chart.js configurations and insights.

USER QUESTION: "{user_question}"
QUERY CONTEXT: {json.dumps(query_context, indent=2)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations
2. Create Chart.js configuration ready for rendering
3. Generate meaningful insights with specific numbers

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["label1", "label2"],
      "datasets": [{{
        "label": "Dataset Name",
        "data": [100, 200],
        "backgroundColor": ["color1", "color2"],
        "borderColor": ["border1", "border2"],
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "Chart Title"}},
        "legend": {{"display": true}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true}},
        "x": {{"display": true}}
      }}
    }}
  }},
  "summary": "Comprehensive 2-3 sentence summary with specific numbers and percentages",
  "insights": [
    "Key insight 1 with specific data points",
    "Key insight 2 with actionable information"
  ],
  "recommendations": [
    "Actionable recommendation based on data",
    "Strategic suggestion for improvement"
  ]
}}

JSON only - no other text:"""

    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON from Gemini response with multiple methods"""
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
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, cleaned_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Method 3: Find JSON object boundaries
            brace_count = 0
            start_idx = -1
            
            for i, char in enumerate(cleaned_text):
                if char == '{':
                    if start_idx == -1:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        try:
                            json_str = cleaned_text[start_idx:i+1]
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
            return None
    
    def _validate_query_response(self, data: Dict) -> bool:
        """Validate query response structure"""
        required_fields = ['collection', 'pipeline', 'chart_hint', 'query_intent']
        return all(field in data for field in required_fields)
    
    def _validate_visualization_response(self, data: Dict) -> bool:
        """Validate visualization response structure"""
        required_fields = ['chart_type', 'chart_config', 'summary']
        return all(field in data for field in required_fields)

# Simple Query Processor (Keep the working version)
class SimpleQueryProcessor:
    """Simple, working query processor for fallback"""
    
    def __init__(self, database):
        self.db = database
        
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process questions with direct MongoDB queries"""
        question_lower = user_question.lower()
        
        try:
            # Smartphone vs Laptop comparison
            if "smartphone" in question_lower and "laptop" in question_lower:
                return self._smartphone_laptop_comparison()
            
            # Top products
            elif any(word in question_lower for word in ["top", "best", "highest"]) and "product" in question_lower:
                return self._top_products()
            
            # Sales by region
            elif "region" in question_lower:
                return self._sales_by_region()
            
            # Customer segments
            elif "customer" in question_lower and "segment" in question_lower:
                return self._customer_segments()
            
            # Revenue by category
            elif "category" in question_lower and any(word in question_lower for word in ["revenue", "sales"]):
                return self._revenue_by_category()
            
            # Monthly trends
            elif "month" in question_lower or "trend" in question_lower:
                return self._monthly_trends()
            
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
        summary_parts = []
        total_revenue = sum(r['total_revenue'] for r in results)
        
        for result in results:
            category = result['_id']
            revenue = result['total_revenue']
            quantity = result['total_quantity']
            orders = result['order_count']
            avg_price = result['avg_price']
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            summary_parts.append(
                f"{category}: ${revenue:,.2f} ({percentage:.1f}%) from {quantity} units across {orders} orders (avg: ${avg_price:.2f})"
            )
        
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
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Revenue",
                    "data": [r['total_revenue'] for r in results],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Revenue by Category"}},
                "scales": {"y": {"beginAtZero": True}}
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
            "type": "doughnut",
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
            for collection_name in ["sales", "customers", "products"]:
                count = self.db[collection_name].count_documents({})
                collections_info.append(f"{collection_name}: {count} records")
            
            summary = f"Available data: {', '.join(collections_info)}. Try asking about: smartphone vs laptop sales, top products, sales by region, customer segments, revenue by category, or monthly trends."
            
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

# Enhanced Two-Stage Processor
class TwoStageProcessor:
    """Enhanced processor that combines Gemini AI with simple fallback"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor
        self.db = database
        self.schema_info = {
            "collections": {
                "sales": {
                    "fields": ["order_id", "customer_id", "product_id", "product_name", "category", "quantity", "unit_price", "total_amount", "discount", "date", "month", "quarter", "sales_rep", "region"],
                    "sample_values": {
                        "category": ["Smartphones", "Laptops", "Audio", "Tablets", "Accessories", "Monitors"],
                        "region": ["North America", "Europe", "Asia-Pacific"]
                    }
                },
                "customers": {
                    "fields": ["customer_id", "name", "email", "age", "gender", "country", "state", "city", "customer_segment", "total_spent", "order_count"],
                    "sample_values": {"customer_segment": ["Regular", "Premium", "VIP"]}
                },
                "products": {
                    "fields": ["product_id", "name", "category", "brand", "price", "cost", "stock", "rating", "reviews_count"]
                }
            }
        }
    
    async def process_question(self, user_question: str) -> Dict[str, Any]:
        """Enhanced two-stage processing with fallback"""
        start_time = datetime.now()
        
        # Stage 1: Try Gemini Query Generation
        stage_1_result = await self.gemini_client.generate_query(user_question, self.schema_info)
        
        if stage_1_result["success"]:
            # Execute the Gemini-generated query
            query_data = stage_1_result["data"]
            raw_results = await self._execute_database_query(query_data)
            
            if raw_results:
                # Stage 2: Try Gemini Visualization Generation
                stage_2_result = await self.gemini_client.generate_visualization(
                    user_question, raw_results, query_data
                )
                
                if stage_2_result["success"]:
                    # Success with both stages
                    viz_data = stage_2_result["data"]
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"✅ Two-stage Gemini processing successful: {len(raw_results)} results in {execution_time:.2f}s")
                    
                    return {
                        "success": True,
                        "summary": viz_data.get("summary", "Analysis completed successfully"),
                        "chart_data": viz_data.get("chart_config", {}),
                        "insights": viz_data.get("insights", []),
                        "recommendations": viz_data.get("recommendations", []),
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_two_stage",
                        "ai_powered": True
                    }
                else:
                    # Stage 2 failed, use simple visualization
                    logger.warning("Stage 2 failed, using simple visualization")
                    return self._create_simple_visualization(user_question, raw_results, query_data)
            else:
                # No results from Gemini query, try simple processor
                logger.warning("Gemini query returned no results, trying simple processor")
                return self.simple_processor.process_question(user_question)
        
        # Stage 1 failed, use simple processor
        logger.warning("Stage 1 failed, using simple processor")
        return self.simple_processor.process_question(user_question)
    
    async def _execute_database_query(self, query_data: Dict) -> List[Dict]:
        """Execute MongoDB query"""
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            if not collection_name or not pipeline:
                return []
            
            collection = self.db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            logger.info(f"Database query executed: {len(results)} results from {collection_name}")
            return results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return []
    
    def _create_simple_visualization(self, user_question: str, raw_results: List[Dict], query_data: Dict) -> Dict[str, Any]:
        """Create simple visualization when Gemini Stage 2 fails"""
        if not raw_results:
            return {"success": False, "error": "No data found"}
        
        # Basic chart configuration
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [str(item.get('_id', 'Unknown')) for item in raw_results[:10]],
                "datasets": [{
                    "label": "Values",
                    "data": [float(item.get('total_revenue', item.get('total', 0))) for item in raw_results[:10]],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Analysis Results"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        summary = f"Found {len(raw_results)} results for your query. Analysis completed using Gemini-generated query with fallback visualization."
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Data points: {len(raw_results)}", "Gemini query successful, simple visualization"],
            "recommendations": ["Enable full AI features for enhanced visualizations"],
            "results_count": len(raw_results),
            "execution_time": 0.2,
            "query_source": "gemini_query_simple_viz",
            "ai_powered": True
        }

# Initialize components
gemini_client = None
simple_processor = None
two_stage_processor = None
gemini_available = False

# Initialize Gemini
if GOOGLE_API_KEY and GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        gemini_client = EnhancedGeminiClient(GOOGLE_API_KEY)
        gemini_available = gemini_client.available
        if gemini_available:
            logger.info("✅ Enhanced Gemini client initialized")
            print("✅ Enhanced Gemini client initialized")
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
    simple_processor = SimpleQueryProcessor(db)
    
    if gemini_available and gemini_client:
        two_stage_processor = TwoStageProcessor(gemini_client, simple_processor, db)
        logger.info("✅ Two-stage processor initialized")
        print("✅ Two-stage processor initialized")
    else:
        logger.info("✅ Simple processor ready (Gemini not available)")
        print("✅ Simple processor ready (Gemini not available)")

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
        "version": "2.0.0-enhanced-working-with-gemini"
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Enhanced query processing with intelligent fallback"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"🔍 Processing question: '{user_question}'")
        
        # Try two-stage processor first, fallback to simple
        if two_stage_processor:
            # Use enhanced two-stage processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    two_stage_processor.process_question(user_question)
                )
            finally:
                loop.close()
            
            if result.get("success"):
                logger.info(f"✅ Enhanced query successful: {result.get('results_count', 0)} results")
                return jsonify(result)
            else:
                logger.warning("Enhanced processor failed, trying simple processor")
                # Fallback to simple processor
                if simple_processor:
                    simple_result = simple_processor.process_question(user_question)
                    if simple_result.get("success"):
                        simple_result["query_source"] = "simple_fallback"
                        logger.info(f"✅ Simple fallback successful: {simple_result.get('results_count', 0)} results")
                        return jsonify(simple_result)
                
                # Both failed
                return jsonify({
                    "success": False,
                    "error": result.get("error", "Query processing failed"),
                    "suggestions": [
                        "Try rephrasing your question",
                        "Use simpler terms",
                        "Try: 'Compare smartphone vs laptop sales'"
                    ]
                }), 400
        
        elif simple_processor:
            # Use simple processor only
            result = simple_processor.process_question(user_question)
            
            if result.get("success"):
                result["query_source"] = "simple_only"
                logger.info(f"✅ Simple query successful: {result.get('results_count', 0)} results")
                return jsonify(result)
            else:
                logger.error(f"❌ Simple query failed: {result.get('error')}")
                return jsonify(result), 400
        
        else:
            return jsonify({
                "error": "Query processor not available",
                "details": "Database not connected"
            }), 503
            
    except Exception as e:
        logger.error(f"❌ Critical error in query processing: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/api/query/advanced', methods=['POST'])
def process_advanced_query():
    """Force use of two-stage Gemini processor"""
    if not two_stage_processor:
        return jsonify({
            "error": "Advanced processing not available",
            "details": "Gemini AI not initialized"
        }), 503
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"🚀 Processing ADVANCED question: '{user_question}'")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                two_stage_processor.process_question(user_question)
            )
        finally:
            loop.close()
        
        if result.get("success"):
            logger.info(f"✅ Advanced query successful: {result.get('results_count', 0)} results")
            return jsonify(result)
        else:
            logger.error(f"❌ Advanced query failed: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Critical error in advanced query processing: {str(e)}")
        return jsonify({
            "error": "Advanced processing failed",
            "details": str(e)
        }), 500

@app.route('/api/batch_query', methods=['POST'])
def batch_process_queries():
    """Process multiple queries at once"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        
        if not questions or not isinstance(questions, list):
            return jsonify({"error": "Questions array is required"}), 400
        
        if len(questions) > 5:
            return jsonify({"error": "Maximum 5 questions per batch"}), 400
        
        logger.info(f"🔄 Processing batch of {len(questions)} questions")
        
        results = []
        processor = two_stage_processor if two_stage_processor else simple_processor
        
        if not processor:
            return jsonify({"error": "No query processor available"}), 503
        
        for i, question in enumerate(questions):
            try:
                if two_stage_processor:
                    # Use async two-stage processor
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
                        "results_count": result.get("results_count", 0),
                        "execution_time": result.get("execution_time", 0)
                    })
                else:
                    results.append({
                        "question": question,
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                logger.error(f"Batch question {i+1} failed: {e}")
                results.append({
                    "question": question,
                    "success": False,
                    "error": f"Processing failed: {str(e)}"
                })
        
        successful_count = sum(1 for r in results if r.get("success"))
        total_time = sum(r.get("execution_time", 0) for r in results)
        
        return jsonify({
            "batch_success": True,
            "results": results,
            "batch_summary": {
                "total_questions": len(questions),
                "successful": successful_count,
                "failed": len(questions) - successful_count,
                "total_execution_time": round(total_time, 2),
                "average_execution_time": round(total_time / len(questions), 2) if questions else 0
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Batch processing error: {str(e)}")
        return jsonify({"error": "Batch processing failed", "details": str(e)}), 500

@app.route('/api/query/test', methods=['POST'])
def test_query_types():
    """Test different types of queries for debugging"""
    try:
        data = request.get_json()
        query_type = data.get('type', 'simple')
        user_question = data.get('question', 'Compare smartphone vs laptop sales')
        
        logger.info(f"🧪 Testing query type: {query_type}")
        
        if query_type == 'simple' and simple_processor:
            result = simple_processor.process_question(user_question)
            result["test_type"] = "simple_processor"
            return jsonify(result)
        
        elif query_type == 'gemini_stage1' and gemini_client:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                schema_info = {
                    "collections": {
                        "sales": {
                            "fields": ["category", "total_amount", "quantity"],
                            "sample_values": {"category": ["Smartphones", "Laptops"]}
                        }
                    }
                }
                stage1_result = loop.run_until_complete(
                    gemini_client.generate_query(user_question, schema_info)
                )
            finally:
                loop.close()
            
            return jsonify({
                "test_type": "gemini_stage1",
                "stage1_result": stage1_result
            })
        
        elif query_type == 'two_stage' and two_stage_processor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    two_stage_processor.process_question(user_question)
                )
            finally:
                loop.close()
            
            result["test_type"] = "two_stage_processor"
            return jsonify(result)
        
        else:
            return jsonify({
                "error": f"Test type '{query_type}' not available",
                "available_types": ["simple", "gemini_stage1", "two_stage"],
                "available_processors": {
                    "simple": simple_processor is not None,
                    "gemini": gemini_client is not None,
                    "two_stage": two_stage_processor is not None
                }
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Test query error: {str(e)}")
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get detailed system status"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": {
                    "available": mongodb_available,
                    "collections": []
                },
                "gemini": {
                    "available": gemini_available,
                    "client_initialized": gemini_client is not None
                },
                "processors": {
                    "simple": simple_processor is not None,
                    "two_stage": two_stage_processor is not None
                }
            },
            "capabilities": {
                "basic_queries": simple_processor is not None,
                "ai_queries": two_stage_processor is not None,
                "batch_processing": True,
                "advanced_processing": two_stage_processor is not None
            }
        }
        
        # Get collection info if database is available
        if mongodb_available and db is not None:
            try:
                for collection_name in ["sales", "customers", "products", "marketing_campaigns"]:
                    count = db[collection_name].count_documents({})
                    status["components"]["database"]["collections"].append({
                        "name": collection_name,
                        "document_count": count,
                        "available": count > 0
                    })
            except Exception as e:
                status["components"]["database"]["error"] = str(e)
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": f"Status check failed: {str(e)}"}), 500

@app.route('/api/debug/collections', methods=['GET'])
def debug_collections():
    """Debug endpoint to check available collections and data"""
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
                
                collections_info[collection_name] = {
                    "document_count": count,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "sample_document": sample
                }
            except Exception as e:
                collections_info[collection_name] = {
                    "error": str(e),
                    "document_count": -1
                }
        
        return jsonify({
            "database_name": db.name,
            "total_collections": len(collections_info),
            "collection_names": collection_names,
            "collections": collections_info
        })
        
    except Exception as e:
        logger.error(f"Debug collections failed: {str(e)}")
        return jsonify({"error": f"Debug failed: {str(e)}"}), 500

@app.route('/api/examples', methods=['GET'])
def get_query_examples():
    """Get example questions that work well with the system"""
    examples = {
        "basic_comparisons": [
            "Compare smartphone vs laptop sales performance",
            "Show me revenue by category",
            "What are our customer segments?"
        ],
        "analysis_queries": [
            "What are our top selling products?",
            "Show me sales by region",
            "How do our customer segments compare?"
        ],
        "advanced_queries": [
            "Analyze the relationship between product categories and customer segments",
            "Compare Q1 vs Q2 performance across all regions",
            "What products have the highest profit margins?"
        ] if two_stage_processor else [],
        "supported_entities": {
            "product_categories": ["Smartphones", "Laptops", "Audio", "Tablets", "Monitors", "Accessories"],
            "regions": ["North America", "Europe", "Asia-Pacific"],
            "customer_segments": ["Regular", "Premium", "VIP"],
            "metrics": ["revenue", "sales", "quantity", "profit", "customers"]
        }
    }
    
    return jsonify(examples)

if __name__ == '__main__':
    print("\n🔗 Starting ENHANCED Working Analytics Server with Two-Stage Gemini...")
    print("🎯 Enhanced Features:")
    print("   - ✅ Two-stage Gemini processing (when available)")
    print("   - ✅ Intelligent fallback to simple processor")
    print("   - ✅ Multiple chart types (bar, pie, doughnut, line)")
    print("   - ✅ Batch query processing")
    print("   - ✅ Advanced query endpoint")
    print("   - ✅ System testing capabilities")
    print("   - ✅ Real-time status monitoring")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected and ready")
    else:
        print("   ❌ MongoDB: Connection failed")
    
    if gemini_available:
        print("   ✅ Gemini AI: Available for enhanced processing")
    else:
        print("   ⚠️ Gemini AI: Not available (using simple processor)")
    
    if two_stage_processor:
        print("   ✅ Two-Stage Processor: Ready for advanced queries")
    elif simple_processor:
        print("   ✅ Simple Processor: Ready for basic queries")
    else:
        print("   ❌ No processors available")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 Available endpoints:")
    print("   - POST /api/query (intelligent processing with fallback)")
    print("   - POST /api/query/advanced (force Gemini two-stage)")
    print("   - POST /api/batch_query (process multiple questions)")
    print("   - POST /api/query/test (test different processor types)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/system/status (detailed system status)")
    print("   - GET  /api/debug/collections (debug database)")
    print("   - GET  /api/examples (get example questions)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)