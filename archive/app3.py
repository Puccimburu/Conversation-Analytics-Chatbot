from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
import pymongo
from typing import Dict, Any

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
print("🚀 SIMPLE WORKING CONVERSATIONAL ANALYTICS")
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

# Simple Query Processor Class
class SimpleQueryProcessor:
    """Simple, working query processor for your data"""
    
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
            logger.error(f"Query processing error: {e}")
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
            return {
                "success": False,
                "error": "No smartphone or laptop data found"
            }
        
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
                "labels": [r['_id'] for r in results[:8]],  # Top 8 for readability
                "datasets": [{
                    "label": "Revenue",
                    "data": [r['total_revenue'] for r in results[:8]],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Top Selling Products"}},
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
            "type": "pie",
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
                    "tension": 0.1
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
                    "Try: 'Show me top products'",
                    "Try: 'What are sales by region?'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not retrieve data info: {str(e)}"
            }

# Initialize simple processor
simple_processor = SimpleQueryProcessor(db) if db is not None else None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "available" if mongodb_available else "unavailable",
            "simple_processor": "available" if simple_processor else "unavailable"
        },
        "version": "1.0.0-simple-working"
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Simple query processing that actually works"""
    if not simple_processor:
        return jsonify({
            "error": "Query processor not available",
            "details": "Database not connected"
        }), 503
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "Question is required"}), 400
        
        logger.info(f"🔍 Processing question: '{user_question}'")
        
        # Process the question
        result = simple_processor.process_question(user_question)
        
        if result.get("success"):
            logger.info(f"✅ Query successful: {result.get('results_count', 0)} results")
            return jsonify(result)
        else:
            logger.error(f"❌ Query failed: {result.get('error')}")
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ Critical error in query processing: {str(e)}")
        return jsonify({
            "error": "Internal server error", 
            "details": str(e)
        }), 500

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

if __name__ == '__main__':
    print("\n🔗 Starting SIMPLE Working Analytics Server...")
    print("🎯 Features:")
    print("   - ✅ Direct MongoDB queries (no complex AI processing)")
    print("   - ✅ Smartphone vs Laptop comparison")
    print("   - ✅ Top products analysis")
    print("   - ✅ Sales by region")
    print("   - ✅ Customer segment analysis")
    print("   - ✅ Revenue by category")
    print("   - ✅ Monthly trends")
    
    print("\n🔧 System Status:")
    if mongodb_available:
        print("   ✅ MongoDB: Connected and ready")
    else:
        print("   ❌ MongoDB: Connection failed")
        
    if simple_processor:
        print("   ✅ Simple Processor: Ready for queries")
    else:
        print("   ❌ Simple Processor: Not available")
    
    print(f"\n🌐 Server starting on http://localhost:5000")
    print("📊 Available endpoints:")
    print("   - POST /api/query (working query processor)")
    print("   - GET  /api/health (system health)")
    print("   - GET  /api/debug/collections (debug database)")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)