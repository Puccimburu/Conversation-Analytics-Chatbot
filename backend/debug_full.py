#!/usr/bin/env python3
"""
Debug the full two-stage process
"""
import asyncio
import os
import pymongo
from utils.enhanced_gemini_client import BulletproofGeminiClient
from config import Config, DATABASE_SCHEMA
import json

async def debug_full_process():
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
    
    # STAGE 1: Generate query
    query_result = await gemini_client.generate_query(user_question, DATABASE_SCHEMA)
    
    print("STAGE 1 - QUERY GENERATION:")
    print(f"Success: {query_result.get('success')}")
    if not query_result.get('success'):
        print(f"Error: {query_result.get('error')}")
        return
        
    query_data = query_result.get('data')
    print(f"Collection: {query_data.get('collection')}")
    print(f"Pipeline: {query_data.get('pipeline')}")
    print(f"Chart Hint: {query_data.get('chart_hint')}")
    print()
    
    # Execute database query
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics')
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.genai
    
    collection_name = query_data.get('collection')
    pipeline = query_data.get('pipeline')
    
    collection = db[collection_name]
    raw_results = list(collection.aggregate(pipeline))
    
    # Clean ObjectIds 
    cleaned_results = []
    for result in raw_results:
        cleaned = {}
        for key, value in result.items():
            if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                cleaned[key] = str(value)
            else:
                cleaned[key] = value
        cleaned_results.append(cleaned)
    
    print(f"DATABASE RESULTS: {len(cleaned_results)} records")
    if cleaned_results:
        print("First result:", cleaned_results[0])
    print()
    
    # STAGE 2: Generate visualization
    print("STAGE 2 - VISUALIZATION GENERATION:")
    viz_result = await gemini_client.generate_visualization(user_question, cleaned_results, query_data)
    
    print(f"Success: {viz_result.get('success')}")
    if viz_result.get('success'):
        viz_data = viz_result.get('data')
        print(f"Chart Type: {viz_data.get('chart_type')}")
        print(f"Summary: {viz_data.get('summary')}")
        
        chart_config = viz_data.get('chart_config', {})
        print(f"Chart Config Keys: {list(chart_config.keys())}")
        
        if 'tableData' in chart_config:
            print(f"Table Data Count: {len(chart_config.get('tableData', []))}")
            if chart_config.get('tableData'):
                print("First table row:", chart_config['tableData'][0])
        
        print("Full visualization data:")
        print(json.dumps(viz_data, indent=2, default=str))
    else:
        print(f"Error: {viz_result.get('error')}")

if __name__ == "__main__":
    asyncio.run(debug_full_process())