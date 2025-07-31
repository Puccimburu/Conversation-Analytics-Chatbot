#!/usr/bin/env python3
"""
Debug what query the application generates for a simple request
"""
import asyncio
import os
import pymongo
from utils.enhanced_gemini_client import BulletproofGeminiClient
from config import Config, DATABASE_SCHEMA

async def debug_query():
    # Initialize Gemini client
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ No GOOGLE_API_KEY found")
        return
    
    gemini_client = BulletproofGeminiClient(api_key)
    
    # Test query generation
    user_question = "list all users"
    print(f"User Question: {user_question}")
    print("=" * 50)
    
    # Generate query
    query_result = await gemini_client.generate_query(user_question, DATABASE_SCHEMA)
    
    print("GEMINI QUERY RESULT:")
    print(f"Success: {query_result.get('success')}")
    if query_result.get('success'):
        query_data = query_result.get('data')
        print(f"Collection: {query_data.get('collection')}")
        print(f"Pipeline: {query_data.get('pipeline')}")
        print(f"Chart Hint: {query_data.get('chart_hint')}")
        print()
        
        # Test the actual database query
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics')
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.genai
        
        collection_name = query_data.get('collection')
        pipeline = query_data.get('pipeline')
        
        print(f"EXECUTING QUERY ON {collection_name}:")
        print(f"Pipeline: {pipeline}")
        
        collection = db[collection_name]
        results = list(collection.aggregate(pipeline))
        
        print(f"Results: {len(results)} records")
        if results:
            print("First result:")
            print(results[0])
    else:
        print(f"Error: {query_result.get('error')}")

if __name__ == "__main__":
    asyncio.run(debug_query())