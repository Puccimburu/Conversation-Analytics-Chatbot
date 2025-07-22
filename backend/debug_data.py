#!/usr/bin/env python3
"""
Quick debug script to check your data and find the issue
"""
import pymongo
import os
from pprint import pprint

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/analytics_db')

def debug_data():
    print("🔍 Debugging Data Issues...")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.analytics_db
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check collections
        collections = db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
        # Check sales collection specifically
        if 'sales' in collections:
            sales = db.sales
            
            # Count total documents
            total_docs = sales.count_documents({})
            print(f"📈 Sales collection has {total_docs} documents")
            
            if total_docs > 0:
                # Get sample document
                sample = sales.find_one()
                print(f"\n📋 Sample sales document:")
                pprint(sample)
                
                # Check categories
                print(f"\n🏷️ Available categories:")
                categories = list(sales.aggregate([
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]))
                
                for cat in categories:
                    print(f"   - {cat['_id']}: {cat['count']} records")
                
                # Test the specific query that's failing
                print(f"\n🧪 Testing problematic query:")
                test_pipeline = [
                    {'$match': {'category': {'$in': ['Smartphones', 'Laptops']}}},
                    {'$group': {'_id': '$category', 'total_revenue': {'$sum': '$total_amount'}, 'total_units_sold': {'$sum': '$quantity'}}},
                    {'$sort': {'total_revenue': -1}}
                ]
                
                print(f"Pipeline: {test_pipeline}")
                
                test_results = list(sales.aggregate(test_pipeline))
                print(f"Results: {test_results}")
                
                if not test_results:
                    print("\n❌ The query returns no results!")
                    print("🔍 Let's check why...")
                    
                    # Check for exact category matches
                    smartphone_count = sales.count_documents({"category": "Smartphones"})
                    laptop_count = sales.count_documents({"category": "Laptops"})
                    
                    print(f"   Direct 'Smartphones' match: {smartphone_count}")
                    print(f"   Direct 'Laptops' match: {laptop_count}")
                    
                    if smartphone_count == 0 and laptop_count == 0:
                        print("\n💡 Categories might be named differently!")
                        print("Try these variations:")
                        
                        variations = ['smartphones', 'laptop', 'Smartphone', 'Laptop']
                        for var in variations:
                            count = sales.count_documents({"category": var})
                            if count > 0:
                                print(f"   Found '{var}': {count} records")
                else:
                    print("✅ Query works! Results found:")
                    pprint(test_results)
                    
            else:
                print("❌ Sales collection is empty!")
        else:
            print("❌ Sales collection doesn't exist!")
            print(f"Available collections: {collections}")
        
        # Check other required fields
        if 'sales' in collections and db.sales.count_documents({}) > 0:
            print(f"\n🔍 Checking required fields...")
            sample = db.sales.find_one()
            
            required_fields = ['category', 'total_amount', 'quantity', 'product_name']
            missing_fields = []
            
            for field in required_fields:
                if field not in sample:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                print(f"Available fields: {list(sample.keys())}")
            else:
                print("✅ All required fields present")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_data()