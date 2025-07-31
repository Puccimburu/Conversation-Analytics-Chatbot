#!/usr/bin/env python3
"""
Standalone debugging script - works independently
Run this to identify exactly where the problem is occurring
"""

import pymongo
import json
from datetime import datetime

print("🔍 DEBUGGING THE 'NO DATA FOUND' ISSUE")
print("=" * 60)

# Step 1: Direct MongoDB Test
print("\n1️⃣ TESTING MONGODB DIRECTLY")
print("-" * 40)

try:
    client = pymongo.MongoClient('mongodb://127.0.0.1:27017/analytics_db')
    db = client.analytics_db
    
    # Test basic connection
    client.admin.command('ping')
    print("✅ MongoDB connection: SUCCESS")
    
    # Check collections
    collections = db.list_collection_names()
    print(f"✅ Collections: {collections}")
    
    # Check total sales
    total_sales = db.sales.count_documents({})
    print(f"✅ Total sales records: {total_sales}")
    
    if total_sales == 0:
        print("❌ PROBLEM: No sales data at all!")
        print("   Solution: Run data insertion script first")
        exit()
    
    # Check June 2024 data specifically
    june_pipeline_test = {
        "date": {
            "$gte": datetime(2024, 6, 1),
            "$lt": datetime(2024, 7, 1)
        }
    }
    
    june_count = db.sales.count_documents(june_pipeline_test)
    print(f"✅ June 2024 sales: {june_count}")
    
    if june_count == 0:
        print("❌ PROBLEM FOUND: No June 2024 data!")
        
        # Check what dates you actually have
        print("\n📅 Checking actual dates in your database...")
        date_sample = list(db.sales.find({}, {"date": 1, "product_name": 1, "order_id": 1}).limit(10))
        print("Sample dates in your database:")
        for i, record in enumerate(date_sample, 1):
            date_val = record.get('date', 'No date')
            product = record.get('product_name', 'No product')
            order_id = record.get('order_id', 'No order ID')
            print(f"   {i}. {date_val} | {product} | {order_id}")
        
        # Find actual date range
        try:
            date_range = list(db.sales.aggregate([
                {"$group": {
                    "_id": None,
                    "min_date": {"$min": "$date"},
                    "max_date": {"$max": "$date"},
                    "count": {"$sum": 1}
                }}
            ]))
            
            if date_range:
                min_date = date_range[0]['min_date']
                max_date = date_range[0]['max_date']
                count = date_range[0]['count']
                print(f"\n📊 Your actual data range:")
                print(f"   From: {min_date}")
                print(f"   To: {max_date}")
                print(f"   Total records: {count}")
                
                # Check if dates are strings instead of datetime objects
                if isinstance(min_date, str):
                    print("⚠️  WARNING: Dates are stored as strings, not datetime objects!")
                    print("   This will cause date filtering to fail")
                    print("   Solution: Convert dates to proper datetime format")
            
        except Exception as e:
            print(f"❌ Error getting date range: {e}")
        
        print("\n🔧 SOLUTIONS:")
        print("1. If no June data: Re-run the data insertion script")
        print("2. If dates are strings: Convert them to datetime objects")
        print("3. Check if data was inserted in a different month/year")
        
    else:
        print("✅ June 2024 data exists! Testing aggregation...")
        
        # Test the exact aggregation that should work
        june_aggregation = [
            {
                "$match": {
                    "date": {
                        "$gte": datetime(2024, 6, 1),
                        "$lt": datetime(2024, 7, 1)
                    }
                }
            },
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
        ]
        
        print("\n🔄 Testing aggregation pipeline...")
        aggregation_results = list(db.sales.aggregate(june_aggregation))
        print(f"✅ Aggregation results: {len(aggregation_results)} products")
        
        if aggregation_results:
            print("✅ Top products from June 2024:")
            for i, product in enumerate(aggregation_results, 1):
                name = product.get('_id', 'Unknown')
                quantity = product.get('total_quantity', 0)
                revenue = product.get('total_revenue', 0)
                print(f"   {i}. {name}: {quantity} units, ${revenue:.2f}")
            
            print("\n🎉 SUCCESS: MongoDB aggregation works perfectly!")
            print("   The problem is likely in your backend code, not the data.")
            
        else:
            print("❌ Aggregation returned no results")
            print("   This means June data exists but aggregation fails")
            
            # Check field names
            sample_record = db.sales.find_one({"date": {"$gte": datetime(2024, 6, 1)}})
            if sample_record:
                print(f"\n📋 June record fields: {list(sample_record.keys())}")
                print(f"📋 Sample values:")
                print(f"   product_name: {sample_record.get('product_name', 'MISSING')}")
                print(f"   quantity: {sample_record.get('quantity', 'MISSING')}")
                print(f"   total_amount: {sample_record.get('total_amount', 'MISSING')}")
                
                # Check for field name mismatches
                if 'product_name' not in sample_record:
                    print("❌ PROBLEM: 'product_name' field is missing!")
                    print(f"   Available fields: {list(sample_record.keys())}")
                
                if 'quantity' not in sample_record:
                    print("❌ PROBLEM: 'quantity' field is missing!")
                
                if 'total_amount' not in sample_record:
                    print("❌ PROBLEM: 'total_amount' field is missing!")
            
except Exception as e:
    print(f"❌ MongoDB error: {e}")
    exit()

# Step 2: Test Backend if MongoDB works
print("\n2️⃣ TESTING BACKEND (if running)")
print("-" * 40)

try:
    import requests
    
    backend_url = "http://localhost:5000"
    
    # Test health
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("✅ Backend health check passed")
            print(f"   Gemini: {health['services']['gemini']}")
            print(f"   Database: {health['services']['database']}")
            
            # Test the actual query
            query_response = requests.post(
                f"{backend_url}/api/query",
                json={"question": "What were our top 5 selling products in June 2024?"},
                timeout=10
            )
            
            print(f"\n📊 Query test result: {query_response.status_code}")
            if query_response.status_code == 200:
                result = query_response.json()
                print(f"   Results count: {result.get('results_count', 0)}")
                print(f"   Summary: {result.get('summary', 'No summary')[:100]}...")
                
                if result.get('results_count', 0) == 0:
                    print("❌ Backend returns 0 results - this is the bug!")
                    print("   MongoDB works but backend processing fails")
                else:
                    print("✅ Backend works correctly!")
            else:
                print(f"❌ Query failed: {query_response.text}")
                
        else:
            print(f"❌ Health check failed: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - Flask app not running?")
    except Exception as e:
        print(f"❌ Backend test error: {e}")

except ImportError:
    print("⚠️  requests not installed - skipping backend test")
    print("   Install with: pip install requests")

# Step 3: Summary and Solutions
print("\n3️⃣ SUMMARY AND SOLUTIONS")
print("-" * 40)

print("Based on the tests above:")
print("\n✅ If MongoDB aggregation worked:")
print("   - Your data is correct")
print("   - Problem is in backend code")
print("   - Apply the enhanced app.py fixes")
print("   - Check date format conversion in backend")

print("\n❌ If no June 2024 data found:")
print("   - Re-run the data insertion script")
print("   - Make sure script includes June 2024 data")
print("   - Check the paste.txt script you have")

print("\n❌ If dates are strings:")
print("   - Convert date fields to datetime objects")
print("   - Use proper MongoDB date format")

print("\n❌ If field names don't match:")
print("   - Check 'product_name', 'quantity', 'total_amount' fields")
print("   - Update backend code to use correct field names")

print("\n🔧 IMMEDIATE NEXT STEPS:")
print("1. Check the MongoDB test results above")
print("2. If MongoDB works: Apply the complete enhanced app.py")
print("3. If no June data: Re-run data insertion script")
print("4. If dates are strings: Fix date format in database")

print("\n" + "=" * 60)
print("🎯 Run this script again after making changes to verify fixes!")