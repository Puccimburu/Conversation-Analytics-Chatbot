from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pymongo
import json
import os
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/analytics_db')

print("=" * 60)
print("🚀 CONVERSATIONAL ANALYTICS BACKEND")
print("=" * 60)
print(f"📊 Database: analytics_db")
print(f"🔑 API Key Present: {'Yes' if GOOGLE_API_KEY else 'No'}")
print("=" * 60)

# Initialize Gemini with correct model name
model = None
gemini_available = False

if GOOGLE_API_KEY and GOOGLE_API_KEY != 'your-gemini-api-key-here':
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        # Use the correct model name for Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Test the model
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
    # Test connection
    client.admin.command('ping')
    mongodb_available = True
    logger.info("✅ MongoDB connected successfully")
    print("✅ MongoDB connected successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to MongoDB: {e}")
    print(f"❌ MongoDB Error: {e}")
    mongodb_available = False

# Database schema information
SCHEMA_INFO = """
Database Collections:
1. sales: order_id, customer_id, product_id, product_name, category, quantity, unit_price, total_amount, discount, date, month, quarter, sales_rep, region
2. products: product_id, name, category, brand, price, cost, stock, rating, reviews_count
3. customers: customer_id, name, email, age, gender, country, state, city, customer_segment, total_spent, order_count

Categories: Laptops, Smartphones, Audio, Tablets, Accessories, Monitors
Regions: North America, Europe, Asia-Pacific
Quarters: Q1, Q2
"""

def create_query_prompt(user_question):
    """Create a prompt for Gemini to generate MongoDB query"""
    prompt = f"""
Convert this business question into a MongoDB aggregation pipeline and chart specification.

Database Schema:
{SCHEMA_INFO}

User Question: "{user_question}"

Respond with JSON only:
{{
    "collection": "sales|products|customers",
    "mongo_query": "[MongoDB aggregation pipeline as string]",
    "chart_type": "bar|pie|line|doughnut",
    "chart_mapping": {{
        "labels_field": "_id",
        "data_field": "total",
        "title": "Chart Title"
    }}
}}

Rules:
- Use MongoDB aggregation syntax
- Include $group, $sort, $limit stages
- Limit to 10 results max
- Choose appropriate chart type

Example:
Question: "Top 5 selling products"
Response: {{"collection": "sales", "mongo_query": "[{{\\"$group\\": {{\\"_id\\": \\"$product_name\\", \\"total\\": {{\\"$sum\\": \\"$total_amount\\"}}}}}}, {{\\"$sort\\": {{\\"total\\": -1}}}}, {{\\"$limit\\": 5}}]", "chart_type": "bar", "chart_mapping": {{"labels_field": "_id", "data_field": "total", "title": "Top 5 Selling Products"}}}}
"""
    return prompt

def extract_json_from_response(text):
    """Extract JSON from Gemini response"""
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(text)
    except:
        return None

def format_chart_data(results, chart_mapping, chart_type):
    """Format data for Chart.js"""
    labels = []
    data = []
    
    for item in results:
        label = str(item.get(chart_mapping['labels_field'], 'Unknown'))
        value = item.get(chart_mapping['data_field'], 0)
        
        labels.append(label)
        data.append(float(value) if isinstance(value, (int, float)) else 0)
    
    colors = [
        'rgba(59, 130, 246, 0.8)',
        'rgba(16, 185, 129, 0.8)', 
        'rgba(245, 158, 11, 0.8)',
        'rgba(239, 68, 68, 0.8)',
        'rgba(147, 51, 234, 0.8)',
        'rgba(236, 72, 153, 0.8)',
        'rgba(14, 165, 233, 0.8)',
        'rgba(99, 102, 241, 0.8)',
        'rgba(168, 85, 247, 0.8)',
        'rgba(217, 70, 239, 0.8)'
    ]
    
    chart_config = {
        "type": chart_type,
        "data": {
            "labels": labels,
            "datasets": [{
                "label": chart_mapping.get('title', 'Data'),
                "data": data,
                "backgroundColor": colors[:len(data)] if chart_type in ['pie', 'doughnut'] else colors[0],
                "borderColor": colors[:len(data)] if chart_type in ['pie', 'doughnut'] else 'rgba(59, 130, 246, 1)',
                "borderWidth": 1
            }]
        },
        "options": {
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": chart_mapping.get('title', 'Analytics Chart')
                },
                "legend": {
                    "display": chart_type in ['pie', 'doughnut']
                }
            }
        }
    }
    
    if chart_type not in ['pie', 'doughnut']:
        chart_config["options"]["scales"] = {
            "y": {"beginAtZero": True},
            "x": {"display": True}
        }
    
    return chart_config

def get_fallback_query_result(user_question):
    """Generate fallback results when Gemini is not available"""
    # Simple keyword-based routing
    question_lower = user_question.lower()
    
    if any(word in question_lower for word in ['top', 'best', 'selling', 'product']):
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$product_name", "total": {"$sum": "$total_amount"}}}, {"$sort": {"total": -1}}, {"$limit": 5}]',
            "chart_type": "bar",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total", 
                "title": "Top Selling Products"
            }
        }
    elif any(word in question_lower for word in ['region', 'location', 'geographic']):
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$region", "total": {"$sum": "$total_amount"}}}, {"$sort": {"total": -1}}]',
            "chart_type": "pie",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total",
                "title": "Sales by Region"
            }
        }
    elif any(word in question_lower for word in ['category', 'categories']):
        return {
            "collection": "sales", 
            "mongo_query": '[{"$group": {"_id": "$category", "total": {"$sum": "$total_amount"}}}, {"$sort": {"total": -1}}]',
            "chart_type": "doughnut",
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total",
                "title": "Sales by Category"
            }
        }
    else:
        # Default fallback
        return {
            "collection": "sales",
            "mongo_query": '[{"$group": {"_id": "$category", "total": {"$sum": "$total_amount"}}}, {"$sort": {"total": -1}}, {"$limit": 5}]',
            "chart_type": "bar", 
            "chart_mapping": {
                "labels_field": "_id",
                "data_field": "total",
                "title": "Sales Overview"
            }
        }

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language queries"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"Processing query: {user_question}")
        
        # Check if database is available
        if not mongodb_available:
            return jsonify({"error": "Database not available. Please check MongoDB connection."}), 500
        
        # Generate query - use Gemini if available, otherwise use fallback
        if gemini_available and model:
            try:
                prompt = create_query_prompt(user_question)
                response = model.generate_content(prompt)
                gemini_result = extract_json_from_response(response.text)
                
                if not gemini_result:
                    gemini_result = get_fallback_query_result(user_question)
            except Exception as e:
                logger.warning(f"Gemini query failed, using fallback: {e}")
                gemini_result = get_fallback_query_result(user_question)
        else:
            gemini_result = get_fallback_query_result(user_question)
        
        # Execute MongoDB query
        collection_name = gemini_result.get('collection', 'sales')
        pipeline_str = gemini_result.get('mongo_query', '[]')
        
        try:
            pipeline = json.loads(pipeline_str)
            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            if not results:
                return jsonify({
                    "summary": "No data found for your query. Please try a different question.",
                    "chart_data": None
                }), 200
            
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return jsonify({"error": f"Database query failed: {str(e)}"}), 500
        
        # Generate summary
        if gemini_available and model:
            try:
                summary_prompt = f"Summarize these results in 2-3 sentences: {json.dumps(results[:3], default=str)}"
                summary_response = model.generate_content(summary_prompt)
                summary = summary_response.text.strip()
            except:
                summary = f"Found {len(results)} results for your query about {user_question.lower()}."
        else:
            summary = f"Found {len(results)} results for your query. The data shows insights based on your question about {user_question.lower()}."
        
        # Format chart data
        chart_data = format_chart_data(
            results,
            gemini_result.get('chart_mapping', {}),
            gemini_result.get('chart_type', 'bar')
        )
        
        return jsonify({
            "summary": summary,
            "chart_data": chart_data,
            "results_count": len(results),
            "ai_powered": gemini_available
        })
        
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "gemini": "available" if gemini_available else "unavailable",
                "database": "available" if mongodb_available else "unavailable"
            }
        }
        
        if mongodb_available:
            # Test database
            db.sales.count_documents({})
        
        return jsonify(health)
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        if not mongodb_available:
            return jsonify({"error": "Database not available"}), 500
        
        # Get basic stats
        total_sales = db.sales.count_documents({})
        total_customers = db.customers.count_documents({})
        total_products = db.products.count_documents({})
        
        # Calculate total revenue
        revenue_result = list(db.sales.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]))
        total_revenue = revenue_result[0]["total"] if revenue_result else 0
        
        stats = {
            "overview": {
                "total_sales": total_sales,
                "total_customers": total_customers,
                "total_products": total_products,
                "total_revenue": round(total_revenue, 2)
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        "message": "Backend is working!",
        "timestamp": datetime.now().isoformat(),
        "gemini_available": gemini_available,
        "database_available": mongodb_available
    })

if __name__ == '__main__':
    print("\n🔗 Starting server...")
    if not gemini_available:
        print("⚠️  Warning: Gemini AI not available")
        print("   Set GOOGLE_API_KEY environment variable to enable full AI features")
        print("   The system will work with basic query patterns")
    
    if not mongodb_available:
        print("⚠️  Warning: Database not connected")
        print("   Make sure MongoDB is running and accessible")
    
    print(f"🌐 Server starting on http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)