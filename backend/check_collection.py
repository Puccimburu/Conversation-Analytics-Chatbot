#!/usr/bin/env python3
"""
Check specific collection structure
"""
import pymongo
import os
import json

# Database connection
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics')

def check_collection(collection_name, limit=3):
    try:
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.genai
        collection = db[collection_name]
        
        print(f"=== {collection_name.upper()} COLLECTION ANALYSIS ===")
        print(f"Total documents: {collection.count_documents({}):,}")
        print()
        
        # Get sample documents
        samples = list(collection.find({}).limit(limit))
        
        for i, doc in enumerate(samples, 1):
            print(f"SAMPLE DOCUMENT {i}:")
            print(json.dumps(doc, indent=2, default=str))
            print()
            
        print("=" * 50)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Check key collections with data
    collections_to_check = [
        "costevalutionforllm",
        "users", 
        "documentextractions",
        "agent_activity"
    ]
    
    for col in collections_to_check:
        check_collection(col, 2)