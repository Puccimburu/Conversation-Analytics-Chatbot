#!/usr/bin/env python3
"""
GenAI Database Analysis Script
Analyzes your genai database collections and provides detailed statistics
"""

import pymongo
import json
from datetime import datetime
from collections import defaultdict

# Database connection (matches your .env)
MONGODB_URI = "mongodb://127.0.0.1:27017/genai"

def analyze_database():
    """Comprehensive analysis of the genai database"""
    
    try:
        # Connect to database
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.genai
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to genai database successfully!")
        print("=" * 60)
        
        # Get all collections
        collection_names = db.list_collection_names()
        print(f"📊 Found {len(collection_names)} collections:")
        print("-" * 60)
        
        total_documents = 0
        collection_stats = {}
        
        # Analyze each collection
        for collection_name in sorted(collection_names):
            try:
                collection = db[collection_name]
                
                # Get basic stats
                count = collection.count_documents({})
                total_documents += count
                
                # Get sample document for structure analysis
                sample = collection.find_one() if count > 0 else None
                
                # Categorize collection
                category = categorize_collection(collection_name)
                
                collection_stats[collection_name] = {
                    "document_count": count,
                    "category": category,
                    "sample_fields": list(sample.keys()) if sample else [],
                    "has_data": count > 0
                }
                
                # Display collection info
                status = "✅ HAS DATA" if count > 0 else "❌ EMPTY"
                print(f"{collection_name:25} | {count:6} docs | {category:15} | {status}")
                
                # Show sample fields for collections with data
                if sample and count > 0:
                    key_fields = list(sample.keys())[:5]  # First 5 fields
                    print(f"   └── Sample fields: {', '.join(key_fields)}")
                
            except Exception as e:
                print(f"{collection_name:25} | ERROR: {str(e)}")
        
        print("=" * 60)
        print(f"📈 SUMMARY:")
        print(f"   Total Collections: {len(collection_names)}")
        print(f"   Total Documents: {total_documents:,}")
        print(f"   Collections with Data: {len([c for c in collection_stats.values() if c['has_data']])}")
        
        # Category breakdown
        categories = defaultdict(list)
        for name, stats in collection_stats.items():
            categories[stats['category']].append(name)
        
        print(f"\n📂 COLLECTION CATEGORIES:")
        for category, collections in categories.items():
            collections_with_data = [c for c in collections if collection_stats[c]['has_data']]
            print(f"   {category}: {len(collections)} total ({len(collections_with_data)} with data)")
            
            # Show collections with data
            if collections_with_data:
                for collection in collections_with_data:
                    count = collection_stats[collection]['document_count']
                    print(f"     • {collection}: {count:,} documents")
        
        # Check for AI operations data specifically
        print(f"\n🤖 AI OPERATIONS DATA CHECK:")
        ai_collections = [
            'costevalutionforllm', 'documentextractions', 'obligationextractions',
            'agent_activity', 'batches', 'prompts'
        ]
        
        for collection_name in ai_collections:
            if collection_name in collection_stats:
                count = collection_stats[collection_name]['document_count']
                status = "✅ READY" if count > 0 else "⚠️ EMPTY"
                print(f"   {collection_name:25} | {count:6} docs | {status}")
            else:
                print(f"   {collection_name:25} | MISSING | ❌ NOT FOUND")
        
        # Export detailed stats
        with open('genai_database_analysis.json', 'w') as f:
            json.dump(collection_stats, f, indent=2, default=str)
        print(f"\n💾 Detailed analysis saved to: genai_database_analysis.json")
        
        return collection_stats
        
    except Exception as e:
        print(f"❌ Database analysis failed: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()

def categorize_collection(collection_name):
    """Categorize collections by their purpose"""
    
    if collection_name in ['costevalutionforllm', 'llmpricing']:
        return "AI_COSTS"
    elif collection_name in ['documentextractions', 'files', 'batches']:
        return "DOCUMENT_PROC"
    elif collection_name in ['obligationextractions', 'obligationmappings', 'compliances']:
        return "COMPLIANCE"
    elif collection_name in ['agent_activity']:
        return "AI_AGENTS"
    elif collection_name in ['users', 'allowedusers', 'conversations']:
        return "USER_MGMT"
    elif collection_name in ['prompts', 'promptmappings', 'documentmappings']:
        return "AI_PROMPTS"
    elif collection_name in ['chat_sessions', 'chat_memories']:
        return "CHAT_SYSTEM"
    elif collection_name in ['customers', 'products', 'sales', 'orders']:
        return "LEGACY_DATA"
    else:
        return "SYSTEM"

def check_specific_collection(collection_name, limit=5):
    """Deep dive into a specific collection"""
    
    try:
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        db = client.genai
        collection = db[collection_name]
        
        print(f"\n🔍 DEEP DIVE: {collection_name}")
        print("=" * 60)
        
        # Basic stats
        count = collection.count_documents({})
        print(f"Total Documents: {count:,}")
        
        if count == 0:
            print("❌ Collection is empty!")
            return
        
        # Sample documents
        print(f"\n📄 Sample Documents (showing {min(limit, count)}):")
        samples = list(collection.find().limit(limit))
        
        for i, doc in enumerate(samples, 1):
            print(f"\n--- Document {i} ---")
            for key, value in list(doc.items())[:10]:  # Show first 10 fields
                if len(str(value)) > 100:
                    value_str = str(value)[:97] + "..."
                else:
                    value_str = str(value)
                print(f"  {key}: {value_str}")
            
            if len(doc) > 10:
                print(f"  ... and {len(doc) - 10} more fields")
        
        # Field analysis
        print(f"\n📊 Field Analysis:")
        if samples:
            all_fields = set()
            for doc in samples:
                all_fields.update(doc.keys())
            
            print(f"Unique fields found: {len(all_fields)}")
            print(f"Fields: {', '.join(sorted(list(all_fields)))}")
        
    except Exception as e:
        print(f"❌ Error analyzing {collection_name}: {str(e)}")
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    print("🚀 GenAI Database Analysis Tool")
    print("=" * 60)
    
    # Run comprehensive analysis
    stats = analyze_database()
    
    if stats:
        print(f"\n🎯 MIGRATION READINESS:")
        
        # Check for critical collections
        critical_collections = ['batches', 'documentextractions', 'costevalutionforllm']
        ready_count = 0
        
        for collection in critical_collections:
            if collection in stats and stats[collection]['document_count'] > 0:
                ready_count += 1
                print(f"   ✅ {collection}: {stats[collection]['document_count']} documents")
            else:
                print(f"   ❌ {collection}: No data found")
        
        if ready_count >= 2:
            print(f"\n🎉 DATABASE READY FOR MIGRATION!")
            print(f"   You have {ready_count}/{len(critical_collections)} critical collections with data")
        else:
            print(f"\n⚠️ Database needs more data for full functionality")
    
    # Optional: Deep dive into specific collection
    print(f"\n" + "=" * 60)
    collection_name = input("Enter collection name for deep dive (or press Enter to skip): ").strip()
    if collection_name:
        check_specific_collection(collection_name)