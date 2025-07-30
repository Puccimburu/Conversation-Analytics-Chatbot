#!/usr/bin/env python3
"""
Find All MongoDB Databases Script
Discovers all databases and finds where your GenAI data actually lives
"""

import pymongo
import json
from datetime import datetime

# Try different connection possibilities
POSSIBLE_CONNECTIONS = [
    "mongodb://127.0.0.1:27017",  # Local MongoDB
    "mongodb://localhost:27017", 
    "mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics",  # Alternative local
    # Add your cloud connection if you have one
]

def find_all_databases():
    """Find all databases and analyze their contents"""
    
    for connection_uri in POSSIBLE_CONNECTIONS:
        try:
            print(f"\n🔍 Checking connection: {connection_uri}")
            print("-" * 60)
            
            # Connect to MongoDB server (not specific database)
            client = pymongo.MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            client.admin.command('ping')
            print("✅ Connection successful!")
            
            # List all databases
            db_names = client.list_database_names()
            print(f"📊 Found {len(db_names)} databases:")
            
            total_genai_collections = 0
            best_database = None
            best_score = 0
            
            for db_name in db_names:
                try:
                    db = client[db_name]
                    collections = db.list_collection_names()
                    
                    # Count GenAI-related collections
                    genai_collections = []
                    genai_keywords = [
                        'cost', 'document', 'obligation', 'agent', 'batch', 
                        'prompt', 'extraction', 'compliance', 'llm'
                    ]
                    
                    for collection in collections:
                        if any(keyword in collection.lower() for keyword in genai_keywords):
                            genai_collections.append(collection)
                    
                    # Calculate score
                    score = len(genai_collections)
                    if score > best_score:
                        best_score = score
                        best_database = db_name
                    
                    # Get total document count
                    total_docs = 0
                    for collection_name in collections:
                        try:
                            total_docs += db[collection_name].count_documents({})
                        except:
                            pass
                    
                    print(f"\n  📂 {db_name}:")
                    print(f"     Collections: {len(collections)}")
                    print(f"     Total Documents: {total_docs:,}")
                    print(f"     GenAI Collections: {len(genai_collections)}")
                    
                    if genai_collections:
                        print(f"     GenAI Collections Found:")
                        for gc in genai_collections[:10]:  # Show first 10
                            try:
                                count = db[gc].count_documents({})
                                print(f"       • {gc}: {count:,} docs")
                            except:
                                print(f"       • {gc}: (error reading)")
                    
                    # Special check for specific collections we need
                    critical_collections = [
                        'costevalutionforllm', 'documentextractions', 'obligationextractions',
                        'agent_activity', 'batches', 'prompts'
                    ]
                    
                    found_critical = []
                    for crit_col in critical_collections:
                        if crit_col in collections:
                            try:
                                count = db[crit_col].count_documents({})
                                if count > 0:
                                    found_critical.append(f"{crit_col}({count})")
                            except:
                                pass
                    
                    if found_critical:
                        print(f"     🎯 CRITICAL DATA: {', '.join(found_critical)}")
                        total_genai_collections += len(found_critical)
                
                except Exception as e:
                    print(f"  ❌ Error accessing {db_name}: {str(e)}")
            
            # Summary for this connection
            if best_database and best_score > 0:
                print(f"\n🎯 BEST DATABASE FOUND: {best_database}")
                print(f"   GenAI Collections: {best_score}")
                print(f"   Connection: {connection_uri}")
                print(f"   📝 Update your .env to:")
                print(f"   MONGODB_URI={connection_uri}/{best_database}")
                
                # Analyze the best database in detail
                analyze_best_database(client, best_database)
            else:
                print(f"\n❌ No GenAI collections found in {connection_uri}")
            
            client.close()
            
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")

def analyze_best_database(client, db_name):
    """Analyze the best database found"""
    
    try:
        print(f"\n🔍 DETAILED ANALYSIS: {db_name}")
        print("=" * 60)
        
        db = client[db_name]
        collections = db.list_collection_names()
        
        # Critical collections analysis
        critical_collections = [
            'costevalutionforllm', 'documentextractions', 'obligationextractions',
            'agent_activity', 'batches', 'prompts', 'users', 'conversations'
        ]
        
        print("🤖 AI OPERATIONS READINESS:")
        ready_collections = 0
        
        for collection_name in critical_collections:
            if collection_name in collections:
                try:
                    count = db[collection_name].count_documents({})
                    if count > 0:
                        print(f"   ✅ {collection_name}: {count:,} documents")
                        ready_collections += 1
                        
                        # Sample document structure
                        sample = db[collection_name].find_one()
                        if sample:
                            fields = list(sample.keys())[:5]
                            print(f"      └── Fields: {', '.join(fields)}")
                    else:
                        print(f"   ⚠️ {collection_name}: 0 documents (empty)")
                except Exception as e:
                    print(f"   ❌ {collection_name}: Error - {str(e)}")
            else:
                print(f"   ❌ {collection_name}: Collection not found")
        
        readiness_percent = (ready_collections / len(critical_collections)) * 100
        print(f"\n📊 MIGRATION READINESS: {readiness_percent:.0f}% ({ready_collections}/{len(critical_collections)} collections ready)")
        
        if readiness_percent >= 50:
            print(f"🎉 DATABASE IS READY FOR MIGRATION!")
        else:
            print(f"⚠️ Database needs more data for full functionality")
            
        # Show all collections for completeness
        print(f"\n📋 ALL COLLECTIONS ({len(collections)}):")
        for i, collection_name in enumerate(sorted(collections), 1):
            try:
                count = db[collection_name].count_documents({})
                print(f"   {i:2}. {collection_name}: {count:,} docs")
            except:
                print(f"   {i:2}. {collection_name}: (error)")
                
    except Exception as e:
        print(f"❌ Error analyzing {db_name}: {str(e)}")

def check_cloud_connection():
    """Check if there's a cloud MongoDB connection"""
    
    print(f"\n🌐 CLOUD CONNECTION CHECK:")
    print("-" * 40)
    
    # Check for common cloud connection environment variables
    import os
    
    cloud_vars = [
        'MONGODB_CLOUD_URI', 'MONGODB_ATLAS_URI', 'MONGO_URL', 
        'DATABASE_URL', 'MONGODB_CONNECTION_STRING'
    ]
    
    found_cloud = False
    for var in cloud_vars:
        value = os.getenv(var)
        if value:
            print(f"   Found {var}: {value[:50]}...")
            found_cloud = True
    
    if not found_cloud:
        print("   No cloud connection variables found")
        print("   💡 Check if you have a .env file with cloud MongoDB URI")

if __name__ == "__main__":
    print("🚀 MongoDB Database Discovery Tool")
    print("=" * 60)
    print("This script will find ALL databases and locate your GenAI data")
    
    find_all_databases()
    check_cloud_connection()
    
    print(f"\n" + "=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Update your .env file with the correct MONGODB_URI")
    print("2. Restart your application")
    print("3. Test with your GenAI operations queries")
    print("=" * 60)