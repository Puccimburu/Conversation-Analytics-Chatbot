from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pymongo
import json
import os
import re
from datetime import datetime, timedelta
import logging
import hashlib
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/analytics_db')

print("=" * 60)
print("🚀 CONVERSATIONAL ANALYTICS - ENHANCED WITH VALIDATION")
print("=" * 60)
print(f"📊 Database: analytics_db")
print(f"🔑 API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Initialize Gemini
model = None
gemini_available = False

if GOOGLE_API_KEY and GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        test_response = model.generate_content("Hello")
        gemini_available = True
        logger.info("✅ Gemini AI initialized successfully")
        print("✅ Gemini AI initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        print(f"❌ Gemini Error: {e}")
        gemini_available = False
else:
    print("⚠️  No Google API key provided. Set GOOGLE_API_KEY environment variable.")
    gemini_available = False

# MongoDB connection
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

# Enhanced schema information with proper field mappings
SCHEMA_INFO = """
Database Collections and Schema:

1. SALES Collection:
   - Fields: order_id, customer_id, product_id, product_name, category, quantity, unit_price, total_amount, discount, date, month, quarter, sales_rep, region
   - Date format: ISODate (e.g., 2024-06-15)
   - Categories: Laptops, Smartphones, Audio, Tablets, Accessories, Monitors
   - Regions: North America, Europe, Asia-Pacific
   - Available data: January 2024 - July 2024

2. MARKETING_CAMPAIGNS Collection:
   - Fields: campaign_id, name, type, start_date, end_date, budget, spent, impressions, clicks, conversions, revenue_generated, target_audience, ctr, conversion_rate
   - Types: Email, Google Ads, Social Media, Influencer, Display Ads

3. PRODUCTS Collection:
   - Fields: product_id, name, category, subcategory, brand, price, cost, stock, rating, reviews_count, launch_date
   - Use for inventory/stock queries
   
4. CUSTOMERS Collection:
   - Fields: customer_id, name, email, age, gender, country, state, city, customer_segment, signup_date, total_spent, order_count, last_purchase
   - Segments: Regular, Premium, VIP

5. INVENTORY_TRACKING Collection:
   - Fields: product_id, date, stock_level, reorder_point, supplier, last_restock, units_sold_month
"""

# =====================================================
# ANSWER VALIDATION AND FEEDBACK SYSTEM
# =====================================================

class AnswerValidator:
    """System to validate answer correctness and collect feedback"""
    
    def __init__(self, db):
        self.db = db
        self.feedback_collection = db.query_feedback
        self.validation_collection = db.answer_validation
        self.query_history = db.query_history
        
        # Create indexes for better performance
        try:
            self.feedback_collection.create_index("query_id")
            self.validation_collection.create_index("question_hash")
            self.query_history.create_index([("timestamp", -1)])
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")
    
    def generate_query_id(self, user_question, pipeline):
        """Generate unique ID for query-result pair"""
        query_string = f"{user_question}_{json.dumps(pipeline, sort_keys=True)}"
        return hashlib.md5(query_string.encode()).hexdigest()[:12]
    
    def log_query_execution(self, user_question, query_result, results, execution_time):
        """Log query execution for analysis"""
        try:
            query_id = self.generate_query_id(user_question, query_result.get('mongo_query', []))
            
            log_entry = {
                "query_id": query_id,
                "question": user_question,
                "timestamp": datetime.now(),
                "collection": query_result.get('collection'),
                "pipeline": query_result.get('mongo_query'),
                "chart_type": query_result.get('chart_type'),
                "results_count": len(results) if results else 0,
                "execution_time_ms": execution_time,
                "query_source": query_result.get('query_source', 'unknown'),
                "success": len(results) > 0 if results else False
            }
            
            self.query_history.insert_one(log_entry)
            return query_id
            
        except Exception as e:
            logger.error(f"Failed to log query: {e}")
            return None
    
    def validate_answer_logic(self, user_question, results, query_result):
        """Perform automated validation checks on the answer"""
        validation_results = {
            "overall_score": 0.0,
            "checks": [],
            "confidence": "low",
            "suggestions": []
        }
        
        try:
            # Check 1: Results exist and are reasonable
            if not results:
                validation_results["checks"].append({
                    "check": "results_exist",
                    "passed": False,
                    "message": "No results returned - query may be too restrictive"
                })
                validation_results["suggestions"].append("Try broadening your query criteria")
            else:
                validation_results["checks"].append({
                    "check": "results_exist", 
                    "passed": True,
                    "message": f"Query returned {len(results)} results"
                })
                validation_results["overall_score"] += 0.3
            
            # Check 2: Chart type appropriateness
            chart_type = query_result.get('chart_type', 'bar')
            question_lower = user_question.lower()
            
            appropriate_chart = self._validate_chart_type(question_lower, chart_type, len(results) if results else 0)
            validation_results["checks"].append(appropriate_chart)
            if appropriate_chart["passed"]:
                validation_results["overall_score"] += 0.2
            
            # Check 3: Data field consistency
            data_field = query_result.get('chart_mapping', {}).get('data_field', 'total')
            if results and data_field in results[0]:
                validation_results["checks"].append({
                    "check": "data_field_exists",
                    "passed": True,
                    "message": f"Data field '{data_field}' found in results"
                })
                validation_results["overall_score"] += 0.2
            elif results:
                validation_results["checks"].append({
                    "check": "data_field_exists",
                    "passed": False,
                    "message": f"Data field '{data_field}' not found in results"
                })
                validation_results["suggestions"].append("Check field mapping configuration")
            
            # Check 4: Question-collection alignment
            collection = query_result.get('collection', 'sales')
            alignment = self._validate_collection_choice(question_lower, collection)
            validation_results["checks"].append(alignment)
            if alignment["passed"]:
                validation_results["overall_score"] += 0.3
            
            # Determine confidence level
            if validation_results["overall_score"] >= 0.8:
                validation_results["confidence"] = "high"
            elif validation_results["overall_score"] >= 0.5:
                validation_results["confidence"] = "medium"
            else:
                validation_results["confidence"] = "low"
                validation_results["suggestions"].append("This answer may not be accurate - please verify manually")
        
        except Exception as e:
            logger.error(f"Answer validation failed: {e}")
            validation_results["checks"].append({
                "check": "validation_error",
                "passed": False,
                "message": f"Validation error: {str(e)}"
            })
        
        return validation_results
    
    def _validate_chart_type(self, question, chart_type, result_count):
        """Validate if chart type is appropriate for the question"""
        if 'trend' in question or 'over time' in question or 'monthly' in question:
            if chart_type == 'line':
                return {"check": "chart_type", "passed": True, "message": "Line chart appropriate for trend analysis"}
            else:
                return {"check": "chart_type", "passed": False, "message": "Line chart recommended for trend analysis"}
        
        elif 'compare' in question or 'vs' in question:
            if chart_type == 'bar':
                return {"check": "chart_type", "passed": True, "message": "Bar chart appropriate for comparisons"}
            else:
                return {"check": "chart_type", "passed": False, "message": "Bar chart recommended for comparisons"}
        
        elif 'distribution' in question or 'percentage' in question or 'share' in question:
            if chart_type in ['pie', 'doughnut']:
                return {"check": "chart_type", "passed": True, "message": "Pie chart appropriate for distributions"}
            else:
                return {"check": "chart_type", "passed": False, "message": "Pie chart recommended for distributions"}
        
        elif result_count > 10 and chart_type in ['pie', 'doughnut']:
            return {"check": "chart_type", "passed": False, "message": "Too many items for pie chart - consider bar chart"}
        
        return {"check": "chart_type", "passed": True, "message": f"{chart_type.title()} chart is acceptable"}
    
    def _validate_collection_choice(self, question, collection):
        """Validate if the right collection was chosen"""
        if any(word in question for word in ['sales', 'revenue', 'product', 'selling']):
            if collection == 'sales':
                return {"check": "collection_choice", "passed": True, "message": "Sales collection appropriate for sales queries"}
            else:
                return {"check": "collection_choice", "passed": False, "message": "Sales collection recommended for sales queries"}
        
        elif any(word in question for word in ['customer', 'segment', 'demographic']):
            if collection == 'customers':
                return {"check": "collection_choice", "passed": True, "message": "Customers collection appropriate for customer queries"}
            else:
                return {"check": "collection_choice", "passed": False, "message": "Customers collection recommended for customer queries"}
        
        elif any(word in question for word in ['marketing', 'campaign', 'conversion']):
            if collection == 'marketing_campaigns':
                return {"check": "collection_choice", "passed": True, "message": "Marketing collection appropriate for marketing queries"}
            else:
                return {"check": "collection_choice", "passed": False, "message": "Marketing collection recommended for marketing queries"}
        
        return {"check": "collection_choice", "passed": True, "message": f"{collection} collection choice is reasonable"}
    
    def store_validation_result(self, query_id, user_question, validation_result):
        """Store validation results for future reference"""
        try:
            validation_doc = {
                "query_id": query_id,
                "question": user_question,
                "question_hash": hashlib.md5(user_question.lower().encode()).hexdigest(),
                "timestamp": datetime.now(),
                "validation_score": validation_result["overall_score"],
                "confidence": validation_result["confidence"],
                "checks": validation_result["checks"],
                "suggestions": validation_result["suggestions"]
            }
            
            self.validation_collection.insert_one(validation_doc)
            
        except Exception as e:
            logger.error(f"Failed to store validation result: {e}")

# Initialize validator
validator = AnswerValidator(db) if mongodb_available else None

# =====================================================
# ENHANCED QUERY PROCESSING (keeping your existing logic)
# =====================================================

def create_enhanced_query_prompt(user_question):
    """Enhanced prompt with better examples for category comparisons"""
    prompt = f"""
You are a MongoDB aggregation pipeline expert. Convert this question to a VALID MongoDB aggregation pipeline.

CRITICAL RULES:
1. ONLY use aggregation pipeline - NEVER use find()
2. Return ONLY valid JSON - no explanations, no markdown
3. Use EXACT field names from schema
4. For sales analysis: use "sales" collection
5. For customer analysis: use "customers" collection  
6. For marketing: use "marketing_campaigns" collection

Question: "{user_question}"

Database Schema:
- sales: region, month, total_amount, customer_id, date, product_name, category, quantity, unit_price
- customers: customer_segment, total_spent, customer_id
- marketing_campaigns: name, conversion_rate, type, revenue_generated

SPECIFIC EXAMPLES:

For "Compare smartphone vs laptop sales":
{{
  "collection": "sales",
  "mongo_query": "[{{\\"$match\\": {{\\"category\\": {{\\"$in\\": [\\"Smartphones\\", \\"Laptops\\"]}}}}}}, {{\\"$group\\": {{\\"_id\\": \\"$category\\", \\"total_revenue\\": {{\\"$sum\\": \\"$total_amount\\"}}, \\"total_quantity\\": {{\\"$sum\\": \\"$quantity\\"}}, \\"order_count\\": {{\\"$sum\\": 1}}}}}}, {{\\"$sort\\": {{\\"total_revenue\\": -1}}}}]",
  "chart_type": "bar",
  "chart_mapping": {{
    "labels_field": "_id",
    "data_field": "total_revenue",
    "title": "Smartphones vs Laptops Sales Performance"
  }},
  "summary_hint": "Direct comparison of smartphones and laptops sales performance"
}}

Return ONLY this JSON format:
{{
  "collection": "collection_name",
  "mongo_query": "[aggregation_pipeline_as_string]",
  "chart_type": "bar|pie|line|doughnut",
  "chart_mapping": {{
    "labels_field": "field_for_labels",
    "data_field": "field_for_values",
    "title": "Chart Title"
  }},
  "summary_hint": "Brief description"
}}

JSON only, no other text:"""
    return prompt

def get_smart_fallback_query(user_question):
    """Enhanced fallback with specific handling for category comparisons"""
    question_lower = user_question.lower()
    logger.info(f"Using smart fallback for: {user_question}")
    
    # Category comparison queries (smartphones vs laptops, etc.)
    if ('compare' in question_lower or 'vs' in question_lower) and ('smartphone' in question_lower or 'laptop' in question_lower):
        # Extract categories to compare
        categories = []
        category_mapping = {
            'smartphone': 'Smartphones',
            'smartphones': 'Smartphones', 
            'phone': 'Smartphones',
            'phones': 'Smartphones',
            'mobile': 'Smartphones',
            'laptop': 'Laptops',
            'laptops': 'Laptops',
            'tablet': 'Tablets',
            'tablets': 'Tablets',
            'audio': 'Audio',
            'headphone': 'Audio',
            'headphones': 'Audio',
            'monitor': 'Monitors',
            'monitors': 'Monitors',
            'accessory': 'Accessories',
            'accessories': 'Accessories'
        }
        
        for key, value in category_mapping.items():
            if key in question_lower and value not in categories:
                categories.append(value)
        
        # If we found specific categories, create comparison query
        if len(categories) >= 2:
            return {
                "collection": "sales",
                "mongo_query": json.dumps([
                    {
                        "$match": {
                            "category": {"$in": categories}
                        }
                    },
                    {
                        "$group": {
                            "_id": "$category",
                            "total_revenue": {"$sum": "$total_amount"},
                            "total_quantity": {"$sum": "$quantity"},
                            "avg_unit_price": {"$avg": "$unit_price"},
                            "order_count": {"$sum": 1}
                        }
                    },
                    {
                        "$sort": {"total_revenue": -1}
                    }
                ]),
                "chart_type": "bar",
                "chart_mapping": {
                    "labels_field": "_id",
                    "data_field": "total_revenue",
                    "title": f"Sales Performance: {' vs '.join(categories)}"
                },
                "summary_hint": f"Comparison of sales performance between {' and '.join(categories)} categories"
            }
        
        # Fallback for general smartphone vs laptop comparison
        return {
            "collection": "sales",
            "mongo_query": json.dumps([
                {
                    "$match": {
                        "category": {"$in": ["Smartphones", "Laptops"]}
                    }
                },
                {
                    "$group": {
                        "_id": "$category",
                        "total_revenue": {"$sum": "$total_amount"},
                        "total_quantity": {"$sum": "$quantity"},
                        "avg_unit_price": {"$avg": "$unit_price"},
                        "order_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"total_revenue": -1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_revenue",
                "title": "Smartphones vs Laptops Sales Performance"
            },
            "summary_hint": "Direct comparison of smartphones and laptops sales performance"
        }
    
    # Category performance (general)
    elif any(word in question_lower for word in ['category', 'categories', 'product category']):
        return {
            "collection": "sales",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": "$category",
                        "total_revenue": {"$sum": "$total_amount"},
                        "total_quantity": {"$sum": "$quantity"},
                        "order_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"total_revenue": -1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_revenue",
                "title": "Sales Performance by Product Category"
            },
            "summary_hint": "Sales performance across all product categories"
        }
    
    # Revenue by region and month
    elif any(word in question_lower for word in ['revenue', 'region', 'month']) and 'region' in question_lower and 'month' in question_lower:
        return {
            "collection": "sales",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": {
                            "region": "$region",
                            "month": "$month"
                        },
                        "total_revenue": {"$sum": "$total_amount"}
                    }
                },
                {
                    "$sort": {"_id.region": 1, "_id.month": 1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_revenue",
                "title": "Revenue by Region and Month"
            },
            "summary_hint": "Revenue performance across different regions and months"
        }
    
    # Customer segment profit
    elif any(word in question_lower for word in ['customer', 'segment', 'profit']):
        return {
            "collection": "customers",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": "$customer_segment",
                        "total_profit": {"$sum": "$total_spent"},
                        "customer_count": {"$sum": 1},
                        "avg_spent": {"$avg": "$total_spent"}
                    }
                },
                {
                    "$sort": {"total_profit": -1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_profit",
                "title": "Total Profit by Customer Segment"
            },
            "summary_hint": "Customer segments ranked by total profit contribution"
        }
    
    # Marketing conversion rates
    elif any(word in question_lower for word in ['conversion', 'marketing', 'channel']):
        return {
            "collection": "marketing_campaigns",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": "$type",
                        "avg_conversion_rate": {"$avg": "$conversion_rate"},
                        "total_campaigns": {"$sum": 1},
                        "total_revenue": {"$sum": "$revenue_generated"}
                    }
                },
                {
                    "$sort": {"avg_conversion_rate": -1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "avg_conversion_rate",
                "title": "Average Conversion Rate by Marketing Channel"
            },
            "summary_hint": "Marketing channels ranked by average conversion performance"
        }
    
    # Revenue by region (simpler version)
    elif 'revenue' in question_lower and 'region' in question_lower:
        return {
            "collection": "sales",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": "$region",
                        "total_revenue": {"$sum": "$total_amount"},
                        "order_count": {"$sum": 1}
                    }
                },
                {
                    "$sort": {"total_revenue": -1}
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_revenue",
                "title": "Total Revenue by Region"
            },
            "summary_hint": "Revenue performance across regions"
        }
    
    # Default fallback - top products
    else:
        return {
            "collection": "sales",
            "mongo_query": json.dumps([
                {
                    "$group": {
                        "_id": "$product_name",
                        "total_quantity": {"$sum": "$quantity"},
                        "total_revenue": {"$sum": "$total_amount"}
                    }
                },
                {
                    "$sort": {"total_quantity": -1}
                },
                {
                    "$limit": 5
                }
            ]),
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total_quantity",
                "title": "Top Selling Products"
            },
            "summary_hint": "Top performing products by quantity sold"
        }

def format_enhanced_chart_data(results, chart_mapping, chart_type):
    """Enhanced chart data formatting with proper label handling"""
    if not results:
        return {
            "type": chart_type,
            "data": {"labels": [], "datasets": []},
            "options": {"responsive": True}
        }
    
    labels = []
    data = []
    
    labels_field = chart_mapping.get('labels_field', '_id')
    data_field = chart_mapping.get('data_field', 'total')
    
    for item in results:
        # Handle complex _id structures (like region + month)
        if labels_field == '_id' and isinstance(item.get('_id'), dict):
            # For complex IDs like {"region": "North America", "month": "January"}
            id_obj = item['_id']
            if 'region' in id_obj and 'month' in id_obj:
                label = f"{id_obj['region']} - {id_obj['month']}"
            elif 'region' in id_obj:
                label = id_obj['region']
            elif 'month' in id_obj:
                label = id_obj['month']
            else:
                # Use first available key-value pair
                first_key = list(id_obj.keys())[0]
                label = str(id_obj[first_key])
        elif labels_field in item:
            label = str(item[labels_field])
        elif '_id' in item:
            label = str(item['_id'])
        else:
            label = 'Unknown'
        
        # Handle data values
        if data_field in item:
            value = item[data_field]
        elif 'total' in item:
            value = item['total']
        elif 'count' in item:
            value = item['count']
        else:
            value = 0
        
        # Convert to number and handle None values
        if isinstance(value, (int, float)) and value is not None:
            data_value = float(value)
        else:
            data_value = 0.0
        
        labels.append(label)
        data.append(round(data_value, 2))
    
    # Enhanced color scheme
    colors = [
        'rgba(59, 130, 246, 0.8)',   # Blue
        'rgba(16, 185, 129, 0.8)',   # Green
        'rgba(245, 158, 11, 0.8)',   # Yellow
        'rgba(239, 68, 68, 0.8)',    # Red
        'rgba(147, 51, 234, 0.8)',   # Purple
        'rgba(236, 72, 153, 0.8)',   # Pink
        'rgba(14, 165, 233, 0.8)',   # Light Blue
        'rgba(99, 102, 241, 0.8)',   # Indigo
        'rgba(168, 85, 247, 0.8)',   # Violet
        'rgba(217, 70, 239, 0.8)'    # Fuchsia
    ]
    
    # Color handling for different chart types
    if chart_type in ['pie', 'doughnut']:
        background_colors = colors[:len(data)]
        border_colors = [color.replace('0.8', '1') for color in background_colors]
    else:
        background_colors = colors[0]
        border_colors = colors[0].replace('0.8', '1')
    
    chart_config = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": [{
                "label": chart_mapping.get('title', 'Data'),
                "data": data,
                "backgroundColor": background_colors,
                "borderColor": border_colors,
                "borderWidth": 2,
                "fill": False if chart_type == 'line' else True
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {
                    "display": True,
                    "text": chart_mapping.get('title', 'Analytics Chart'),
                    "font": {"size": 16}
                },
                "legend": {
                    "display": chart_type in ['pie', 'doughnut'],
                    "position": "bottom"
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "display": chart_type not in ['pie', 'doughnut']
                },
                "x": {
                    "display": chart_type not in ['pie', 'doughnut'],
                    "ticks": {
                        "maxRotation": 45,
                        "minRotation": 0
                    }
                }
            } if chart_type not in ['pie', 'doughnut'] else {}
        }
    }
    
    return chart_config

def generate_enhanced_summary(user_question, results, query_result):
    """Enhanced summary generation with better insights for category comparisons"""
    if not results:
        return "No data found for your query. This might be due to missing data in the specified date range or criteria. Please try a different question or check your parameters."
    
    summary_hint = query_result.get('summary_hint', '')
    chart_mapping = query_result.get('chart_mapping', {})
    data_field = chart_mapping.get('data_field', 'total')
    
    try:
        total_items = len(results)
        question_lower = user_question.lower()
        
        # Enhanced summaries for category comparisons
        if ('compare' in question_lower or 'vs' in question_lower) and ('smartphone' in question_lower or 'laptop' in question_lower):
            if len(results) >= 2:
                # Sort results by the data field to get top performer
                sorted_results = sorted(results, key=lambda x: x.get(data_field, 0), reverse=True)
                
                top_category = sorted_results[0]
                second_category = sorted_results[1] if len(sorted_results) > 1 else None
                
                top_name = top_category.get('_id', 'Unknown')
                top_revenue = top_category.get(data_field, 0)
                top_quantity = top_category.get('total_quantity', 0)
                top_orders = top_category.get('order_count', 0)
                
                if second_category:
                    second_name = second_category.get('_id', 'Unknown')
                    second_revenue = second_category.get(data_field, 0)
                    
                    # Calculate percentage difference
                    if second_revenue > 0:
                        percentage_diff = ((top_revenue - second_revenue) / second_revenue) * 100
                        return f"{top_name} significantly outperforms {second_name} with ${top_revenue:,.2f} vs ${second_revenue:,.2f} in total revenue ({percentage_diff:+.1f}% difference). {top_name} sold {top_quantity} units across {top_orders} orders, demonstrating stronger market performance."
                    else:
                        return f"{top_name} is the clear leader with ${top_revenue:,.2f} in total revenue and {top_quantity} units sold, while {second_name} shows minimal performance in comparison."
                else:
                    return f"{top_name} generated ${top_revenue:,.2f} in total revenue from {top_quantity} units sold across {top_orders} orders."
            
            elif len(results) == 1:
                single_result = results[0]
                category_name = single_result.get('_id', 'Unknown')
                revenue = single_result.get(data_field, 0)
                quantity = single_result.get('total_quantity', 0)
                return f"Only {category_name} data is available, showing ${revenue:,.2f} in total revenue from {quantity} units sold. The comparison category may not have any sales data in the current period."
        
        # Generic summary for other cases
        if results and data_field in results[0]:
            values = [item.get(data_field, 0) for item in results]
            total_value = sum(values)
            avg_value = total_value / len(values) if values else 0
            
            return f"Found {total_items} results for your query. Total {data_field.replace('_', ' ')}: {total_value:,.2f}, Average: {avg_value:,.2f}. {summary_hint if summary_hint else 'The analysis shows valuable insights based on your question.'}"
        
        return f"Found {total_items} results for your query. {summary_hint if summary_hint else 'The data shows insights related to your question.'}"
        
    except Exception as e:
        logger.error(f"Enhanced summary generation failed: {e}")
        return f"Found {len(results)} results for your query. The analysis provides insights based on your question about {user_question.lower()}."

def extract_json_from_response(response_text):
    """Enhanced JSON extraction with better error handling"""
    try:
        logger.info(f"Extracting JSON from response: {response_text[:200]}...")
        
        # Clean the response text
        text = response_text.strip()
        
        # Method 1: Try direct JSON parsing
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict) and 'collection' in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
        
        # Method 2: Remove markdown formatting
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = re.sub(r'^\s*Here.*?:\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Method 3: Extract JSON using regex
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and 'collection' in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        
        logger.error("All JSON extraction methods failed")
        return None
        
    except Exception as e:
        logger.error(f"JSON extraction error: {e}")
        return None

# =====================================================
# FEEDBACK ENDPOINTS
# =====================================================

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Collect user feedback on answer quality"""
    try:
        data = request.get_json()
        query_id = data.get('query_id')
        rating = data.get('rating')  # 1-5 scale
        feedback_type = data.get('type', 'general')  # 'accuracy', 'completeness', 'clarity', 'general'
        comment = data.get('comment', '')
        user_correction = data.get('correction', '')  # User's suggested correct answer
        
        if not query_id or rating is None:
            return jsonify({"error": "query_id and rating are required"}), 400
        
        if not (1 <= rating <= 5):
            return jsonify({"error": "Rating must be between 1 and 5"}), 400
        
        if not validator:
            return jsonify({"error": "Feedback system not available"}), 500
        
        feedback_doc = {
            "query_id": query_id,
            "rating": rating,
            "feedback_type": feedback_type,
            "comment": comment,
            "user_correction": user_correction,
            "timestamp": datetime.now(),
            "helpful": rating >= 4,  # Consider 4+ as helpful
            "needs_improvement": rating <= 2  # Consider 2 and below as needing improvement
        }
        
        validator.feedback_collection.insert_one(feedback_doc)
        
        # Update query history with feedback
        validator.query_history.update_one(
            {"query_id": query_id},
            {
                "$set": {
                    "user_rating": rating,
                    "user_feedback": comment,
                    "feedback_timestamp": datetime.now()
                }
            }
        )
        
        return jsonify({
            "message": "Feedback submitted successfully",
            "query_id": query_id,
            "rating": rating
        })
        
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        return jsonify({"error": "Failed to submit feedback"}), 500

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Get feedback statistics and insights"""
    try:
        if not validator:
            return jsonify({"error": "Feedback system not available"}), 500
        
        # Overall feedback stats
        total_feedback = validator.feedback_collection.count_documents({})
        
        if total_feedback == 0:
            return jsonify({
                "total_feedback": 0,
                "message": "No feedback collected yet"
            })
        
        # Rating distribution
        rating_pipeline = [
            {"$group": {
                "_id": "$rating",
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        rating_dist = list(validator.feedback_collection.aggregate(rating_pipeline))
        
        # Average rating
        avg_rating_pipeline = [
            {"$group": {
                "_id": None,
                "avg_rating": {"$avg": "$rating"},
                "helpful_count": {"$sum": {"$cond": ["$helpful", 1, 0]}},
                "needs_improvement_count": {"$sum": {"$cond": ["$needs_improvement", 1, 0]}}
            }}
        ]
        avg_stats = list(validator.feedback_collection.aggregate(avg_rating_pipeline))
        
        # Feedback by type
        type_pipeline = [
            {"$group": {
                "_id": "$feedback_type",
                "count": {"$sum": 1},
                "avg_rating": {"$avg": "$rating"}
            }},
            {"$sort": {"count": -1}}
        ]
        type_stats = list(validator.feedback_collection.aggregate(type_pipeline))
        
        # Recent feedback trends (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_feedback = validator.feedback_collection.count_documents({
            "timestamp": {"$gte": week_ago}
        })
        
        stats = {
            "total_feedback": total_feedback,
            "rating_distribution": rating_dist,
            "average_rating": avg_stats[0]["avg_rating"] if avg_stats else 0,
            "helpful_answers": avg_stats[0]["helpful_count"] if avg_stats else 0,
            "needs_improvement": avg_stats[0]["needs_improvement_count"] if avg_stats else 0,
            "feedback_by_type": type_stats,
            "recent_feedback_count": recent_feedback,
            "satisfaction_rate": (avg_stats[0]["helpful_count"] / total_feedback * 100) if avg_stats and total_feedback > 0 else 0
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        return jsonify({"error": "Failed to retrieve feedback statistics"}), 500

@app.route('/api/validation/insights', methods=['GET'])
def get_validation_insights():
    """Get insights from automated validation checks"""
    try:
        if not validator:
            return jsonify({"error": "Validation system not available"}), 500
        
        # Common validation issues
        common_issues_pipeline = [
            {"$unwind": "$checks"},
            {"$match": {"checks.passed": False}},
            {"$group": {
                "_id": "$checks.check",
                "count": {"$sum": 1},
                "messages": {"$addToSet": "$checks.message"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        common_issues = list(validator.validation_collection.aggregate(common_issues_pipeline))
        
        # Confidence distribution
        confidence_pipeline = [
            {"$group": {
                "_id": "$confidence",
                "count": {"$sum": 1},
                "avg_score": {"$avg": "$validation_score"}
            }},
            {"$sort": {"count": -1}}
        ]
        
        confidence_dist = list(validator.validation_collection.aggregate(confidence_pipeline))
        
        # Validation score trends
        score_ranges = [
            {"range": "High (0.8-1.0)", "count": validator.validation_collection.count_documents({"validation_score": {"$gte": 0.8}})},
            {"range": "Medium (0.5-0.8)", "count": validator.validation_collection.count_documents({"validation_score": {"$gte": 0.5, "$lt": 0.8}})},
            {"range": "Low (0.0-0.5)", "count": validator.validation_collection.count_documents({"validation_score": {"$lt": 0.5}})}
        ]
        
        insights = {
            "common_validation_issues": common_issues,
            "confidence_distribution": confidence_dist,
            "score_distribution": score_ranges,
            "total_validations": validator.validation_collection.count_documents({})
        }
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Failed to get validation insights: {e}")
        return jsonify({"error": "Failed to retrieve validation insights"}), 500

# =====================================================
# ENHANCED QUERY PROCESSING WITH VALIDATION
# =====================================================

@app.route('/api/query', methods=['POST'])
def process_query():
    """Enhanced query processing with answer validation"""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"Processing query with validation: {user_question}")
        
        if not mongodb_available:
            return jsonify({"error": "Database not available. Please check MongoDB connection."}), 500
        
        query_result = None
        query_source = "fallback"
        
        # Try Gemini first with enhanced error handling
        if gemini_available and model:
            try:
                logger.info("Attempting Gemini query processing")
                prompt = create_enhanced_query_prompt(user_question)
                
                response = model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.1,
                        'max_output_tokens': 1000,
                        'top_p': 0.8
                    }
                )
                
                extracted_result = extract_json_from_response(response.text)
                
                if extracted_result and all(key in extracted_result for key in ['collection', 'mongo_query', 'chart_type']):
                    query_result = extracted_result
                    query_source = "gemini"
                    logger.info("Successfully processed Gemini response")
                else:
                    logger.warning("Gemini response validation failed, using fallback")
                    
            except Exception as e:
                logger.warning(f"Gemini processing failed: {str(e)}")
        
        # Use enhanced fallback if Gemini failed
        if not query_result:
            logger.info("Using enhanced fallback query system")
            query_result = get_smart_fallback_query(user_question)
            query_source = "fallback"
        
        query_result['query_source'] = query_source
        
        # Extract and validate query components
        collection_name = query_result.get('collection', 'sales')
        chart_mapping = query_result.get('chart_mapping', {})
        chart_type = query_result.get('chart_type', 'bar')
        mongo_query = query_result.get('mongo_query', '[]')
        
        # Parse the MongoDB pipeline
        try:
            if isinstance(mongo_query, list):
                pipeline = mongo_query
            elif isinstance(mongo_query, str):
                pipeline = json.loads(mongo_query)
            else:
                raise ValueError(f"Invalid mongo_query type: {type(mongo_query)}")
        except json.JSONDecodeError as e:
            logger.error(f"Pipeline parsing failed: {e}")
            return jsonify({
                "error": "Query format error. Please try rephrasing your question.",
                "debug_info": f"Pipeline parsing failed: {str(e)}" if app.debug else None
            }), 400
        
        # Execute the query
        logger.info(f"Executing query on collection: {collection_name}")
        logger.info(f"Pipeline: {pipeline}")
        
        try:
            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            logger.info(f"Query returned {len(results)} results")
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Generate query ID and log execution
            query_id = None
            validation_result = None
            
            if validator:
                query_id = validator.log_query_execution(user_question, query_result, results, execution_time)
                
                # Perform automated validation
                validation_result = validator.validate_answer_logic(user_question, results, query_result)
                
                # Store validation results
                if query_id:
                    validator.store_validation_result(query_id, user_question, validation_result)
            
            if not results:
                return jsonify({
                    "summary": "No data found for your query. This might be due to missing data or incorrect criteria. Please try a different question or check your parameters.",
                    "chart_data": {
                        "type": "bar",
                        "data": {"labels": [], "datasets": []},
                        "options": {"responsive": True}
                    },
                    "results_count": 0,
                    "ai_powered": gemini_available,
                    "query_source": query_source,
                    "query_id": query_id,
                    "validation": validation_result,
                    "feedback_enabled": validator is not None
                })
            
            # Generate enhanced summary and chart data
            summary = generate_enhanced_summary(user_question, results, query_result)
            chart_data = format_enhanced_chart_data(results, chart_mapping, chart_type)
            
            response = {
                "summary": summary,
                "chart_data": chart_data,
                "results_count": len(results),
                "execution_time_ms": execution_time,
                "ai_powered": gemini_available,
                "query_source": query_source,
                "query_id": query_id,
                "validation": validation_result,
                "feedback_enabled": validator is not None,
                "debug_info": {
                    "collection": collection_name,
                    "chart_type": chart_type,
                    "pipeline": pipeline
                } if app.debug else None
            }
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return jsonify({
                "error": f"Failed to execute query: {str(e)}",
                "suggestion": "Please try rephrasing your question or use simpler terms.",
                "debug_info": str(e) if app.debug else None
            }), 500
        
    except Exception as e:
        logger.error(f"Request processing error: {e}")
        return jsonify({
            "error": f"Request failed: {str(e)}",
            "debug_info": str(e) if app.debug else None
        }), 500

# =====================================================
# EXISTING ENDPOINTS (keeping your original ones)
# =====================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "gemini": "available" if gemini_available else "unavailable",
                "database": "available" if mongodb_available else "unavailable",
                "validation": "available" if validator else "unavailable"
            },
            "features": {
                "answer_validation": validator is not None,
                "user_feedback": validator is not None,
                "performance_monitoring": validator is not None
            }
        }
        
        if mongodb_available:
            db.sales.count_documents({})
        
        return jsonify(health)
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        "message": "Enhanced backend with answer validation and feedback system is working!",
        "timestamp": datetime.now().isoformat(),
        "gemini_available": gemini_available,
        "database_available": mongodb_available,
        "validation_available": validator is not None,
        "version": "6.0.0-enhanced-validation-system",
        "features": {
            "category_comparison_fix": True,
            "answer_validation": True,
            "user_feedback": True,
            "performance_monitoring": True,
            "confidence_scoring": True
        }
    })

if __name__ == '__main__':
    print("\n🔗 Starting ENHANCED backend server with validation...")
    print("🔧 New Features Added:")
    print("   - ✅ Answer validation with confidence scoring")
    print("   - ✅ User feedback collection system")
    print("   - ✅ Query execution logging and monitoring")
    print("   - ✅ Validation insights and analytics")
    print("   - ✅ Performance monitoring dashboard")
    print("   - ✅ Automated quality checks")
    print("\n🔧 Existing Features:")
    print("   - ✅ Fixed smartphone vs laptop comparison queries")
    print("   - ✅ Enhanced category-specific fallback handling")
    print("   - ✅ Better category detection and mapping")
    print("   - ✅ Improved comparison summaries with percentages")
    print("   - ✅ Support for multiple category comparisons")
    print("   - ✅ Enhanced chart data formatting for categories")
    print("=" * 60)
    
    if not gemini_available:
        print("⚠️  Warning: Gemini AI not available")
        print("   Set GOOGLE_API_KEY environment variable to enable full AI features")
        print("   The system will work with enhanced fallback patterns")
    
    if not mongodb_available:
        print("⚠️  Warning: Database not connected")
        print("   Make sure MongoDB is running and accessible")
        print("   Validation and feedback features require database connection")
    
    if validator:
        print("✅ Answer validation and feedback system ready")
    else:
        print("⚠️  Validation system disabled (database required)")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 New endpoints available:")
    print("   - POST /api/feedback (submit user feedback)")
    print("   - GET  /api/feedback/stats (feedback statistics)")
    print("   - GET  /api/validation/insights (validation insights)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)