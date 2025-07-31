#!/usr/bin/env python3
"""
Debug script to check database collections and data
"""
import pymongo
import os
from datetime import datetime

# Database connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics')

def check_database():
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.genai
        
        print("=" * 60)
        print("DATABASE DEBUG ANALYSIS")
        print("=" * 60)
        print(f"Connected to: {MONGODB_URI}")
        print(f"Database: {db.name}")
        print()
        
        # Get all collection names
        collections = db.list_collection_names()
        print(f"Total Collections Found: {len(collections)}")
        print()
        
        # Check each collection
        collection_stats = []
        for collection_name in sorted(collections):
            try:
                collection = db[collection_name]
                count = collection.count_documents({})
                
                # Get sample document to understand structure
                sample = collection.find_one({})
                fields = list(sample.keys()) if sample else []
                
                collection_stats.append({
                    'name': collection_name,
                    'count': count,
                    'fields': fields[:10]  # First 10 fields
                })
                
                print(f"[DATA] {collection_name}")
                print(f"   Documents: {count:,}")
                if sample:
                    print(f"   Sample fields: {', '.join(fields[:5])}")
                    if len(fields) > 5:
                        print(f"   ... and {len(fields) - 5} more fields")
                else:
                    print("   No documents found")
                print()
                
            except Exception as e:
                print(f"[ERROR] Error checking {collection_name}: {e}")
                print()
        
        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        # Collections with data
        with_data = [c for c in collection_stats if c['count'] > 0]
        without_data = [c for c in collection_stats if c['count'] == 0]
        
        print(f"Collections with data: {len(with_data)}")
        for col in with_data:
            print(f"  [OK] {col['name']}: {col['count']:,} documents")
        
        print()
        print(f"Empty collections: {len(without_data)}")
        for col in without_data:
            print(f"  [EMPTY] {col['name']}: 0 documents")
        
        print()
        print("=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)
        
        if len(with_data) > 0:
            print("[OK] Use these collections for queries:")
            for col in with_data[:5]:  # Top 5
                print(f"   - {col['name']} ({col['count']:,} records)")
        
        if len(without_data) > 0:
            print("[WARNING] These collections are empty and will return zero data:")
            for col in without_data[:5]:  # First 5
                print(f"   - {col['name']}")
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")

if __name__ == "__main__":
    check_database()