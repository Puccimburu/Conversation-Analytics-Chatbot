"""
LangGraph Debug and Fix Script
Identifies and fixes critical LangGraph workflow execution issues
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import json
import traceback

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from utils.langgraph_analytics import LangGraphAnalyticsWorkflow
from utils.enhanced_gemini_client import BulletproofGeminiClient
from workflows.analytics_flow import WorkflowSelector
from config import Config, DATABASE_SCHEMA

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LangGraphDebugger:
    """Debug and fix LangGraph workflow issues"""
    
    def __init__(self):
        self.gemini_client = None
        self.mongodb_client = None
        self.workflow = None
        self.issues_found = []
        self.fixes_applied = []
    
    async def setup(self):
        """Initialize components for debugging"""
        try:
            print("🔧 Setting up LangGraph debug environment...")
            
            # Initialize Gemini client with debugging
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                self.issues_found.append("CRITICAL: GOOGLE_API_KEY not found")
                return False
            
            self.gemini_client = BulletproofGeminiClient(api_key)
            print("✅ Gemini client initialized")
            
            # Initialize MongoDB with detailed connection info
            import pymongo
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')
            client = pymongo.MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self.mongodb_client = client[Config.DATABASE_NAME]
            
            # Test connection with detailed error info
            try:
                client.admin.command('ping')
                print("✅ MongoDB connected")
                
                # Check if collections exist
                collections = self.mongodb_client.list_collection_names()
                print(f"📁 Available collections: {collections}")
                
                if not collections:
                    self.issues_found.append("WARNING: No collections found in database")
                
            except Exception as e:
                self.issues_found.append(f"CRITICAL: MongoDB connection failed: {e}")
                return False
            
            # Initialize LangGraph workflow with debugging
            try:
                self.workflow = LangGraphAnalyticsWorkflow(
                    gemini_client=self.gemini_client,
                    mongodb_client=self.mongodb_client,
                    schema_info=DATABASE_SCHEMA
                )
                print("✅ LangGraph workflow initialized")
                
            except Exception as e:
                self.issues_found.append(f"CRITICAL: LangGraph initialization failed: {e}")
                print(f"❌ LangGraph Error: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def debug_workflow_nodes(self):
        """Debug individual workflow nodes"""
        print("\n🔍 DEBUGGING WORKFLOW NODES")
        print("-" * 50)
        
        if not self.workflow:
            print("❌ Workflow not available for debugging")
            return
        
        # Test each node individually
        test_state = {
            "original_question": "list of users",
            "user_id": "debug_user",
            "chat_id": "debug_chat",
            "thread_id": "debug_thread",
            "start_time": datetime.now(),
            "current_step": "start",
            "retry_count": 0,
            "errors": [],
            "success": False,
            "final_result": None
        }
        
        nodes_to_test = [
            ("understand_intent", self.workflow.nodes.understand_intent),
            ("generate_query", self.workflow.nodes.generate_mongo_query),
            ("execute_query", self.workflow.nodes.execute_data_query),
            ("plan_visualization", self.workflow.nodes.plan_visualization),
            ("format_response", self.workflow.nodes.format_final_response)
        ]
        
        for node_name, node_func in nodes_to_test:
            try:
                print(f"\n🧪 Testing node: {node_name}")
                
                # Create a copy of state for each test
                node_state = test_state.copy()
                
                # Execute node
                result_state = await node_func(node_state)
                
                if result_state and isinstance(result_state, dict):
                    print(f"✅ {node_name}: Executed successfully")
                    print(f"   Current step: {result_state.get('current_step', 'N/A')}")
                    print(f"   Errors: {len(result_state.get('errors', []))}")
                    
                    # Update test_state for next node
                    test_state.update(result_state)
                    
                else:
                    print(f"❌ {node_name}: Invalid result state")
                    self.issues_found.append(f"Node {node_name} returns invalid state")
                    
            except Exception as e:
                print(f"❌ {node_name}: Failed with error: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
                self.issues_found.append(f"Node {node_name} execution failed: {e}")
    
    async def debug_gemini_integration(self):
        """Debug Gemini API integration within workflow context"""
        print("\n🤖 DEBUGGING GEMINI INTEGRATION")
        print("-" * 50)
        
        try:
            # Test direct Gemini call
            test_prompt = """
            Analyze this analytics question: "list of users"
            
            Available collections: users, documents, batches
            
            Respond with JSON containing:
            {
                "intent": "user_management",
                "collection": "users", 
                "analysis_type": "list_query"
            }
            """
            
            print("🧪 Testing direct Gemini call...")
            response = await self.gemini_client.generate_response(test_prompt)
            
            if response and response.get('success'):
                print("✅ Gemini direct call successful")
                print(f"   Response: {response.get('content', '')[:200]}...")
            else:
                print("❌ Gemini direct call failed")
                self.issues_found.append(f"Gemini API issue: {response}")
                
        except Exception as e:
            print(f"❌ Gemini integration test failed: {e}")
            self.issues_found.append(f"Gemini integration failed: {e}")
    
    async def debug_mongodb_operations(self):
        """Debug MongoDB operations within workflow context"""
        print("\n💾 DEBUGGING MONGODB OPERATIONS")
        print("-" * 50)
        
        try:
            # Test collection access
            collections = self.mongodb_client.list_collection_names()
            print(f"📁 Available collections: {collections}")
            
            # Test a simple query on each collection
            for collection_name in collections[:3]:  # Test first 3 collections
                try:
                    collection = self.mongodb_client[collection_name]
                    count = collection.count_documents({})
                    sample = collection.find_one()
                    
                    print(f"✅ {collection_name}: {count} documents")
                    if sample:
                        print(f"   Sample fields: {list(sample.keys())}")
                    
                except Exception as e:
                    print(f"❌ {collection_name}: Query failed - {e}")
                    self.issues_found.append(f"Collection {collection_name} access failed: {e}")
                    
        except Exception as e:
            print(f"❌ MongoDB operations test failed: {e}")
            self.issues_found.append(f"MongoDB operations failed: {e}")
    
    async def generate_fix_recommendations(self):
        """Generate specific fix recommendations based on identified issues"""
        print("\n🔧 GENERATING FIX RECOMMENDATIONS")
        print("-" * 50)
        
        recommendations = []
        
        # Analyze failure patterns
        if any("Workflow execution failed" in issue for issue in self.issues_found):
            recommendations.append({
                "priority": "HIGH",
                "issue": "Workflow execution failures",
                "fix": "Add detailed error logging in workflow node wrappers",
                "code_change": "Add try-catch blocks with full exception details in _understand_intent_wrapper and other node wrappers"
            })
        
        if any("Gemini" in issue for issue in self.issues_found):
            recommendations.append({
                "priority": "HIGH", 
                "issue": "Gemini API integration problems",
                "fix": "Verify Gemini client compatibility with async workflow execution",
                "code_change": "Update workflow nodes to properly handle async Gemini calls"
            })
        
        if any("MongoDB" in issue for issue in self.issues_found):
            recommendations.append({
                "priority": "MEDIUM",
                "issue": "Database operation issues",
                "fix": "Verify MongoDB queries work within workflow context",
                "code_change": "Add connection verification and query testing in workflow nodes"
            })
        
        # Always recommend enhanced error logging
        recommendations.append({
            "priority": "HIGH",
            "issue": "Insufficient error details",
            "fix": "Enhance error logging throughout workflow execution",
            "code_change": "Replace generic 'Workflow execution failed' with specific error details"
        })
        
        print("📋 Recommended Fixes:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['issue']}")
            print(f"   Fix: {rec['fix']}")
            print(f"   Code: {rec['code_change']}")
        
        return recommendations
    
    async def run_comprehensive_debug(self):
        """Run complete debugging suite"""
        print("🧪 COMPREHENSIVE LANGGRAPH DEBUG SESSION")
        print("=" * 60)
        
        # Setup
        setup_success = await self.setup()
        if not setup_success:
            print("❌ Setup failed - cannot continue debugging")
            return
        
        # Debug individual components
        await self.debug_gemini_integration()
        await self.debug_mongodb_operations() 
        await self.debug_workflow_nodes()
        
        # Generate recommendations
        recommendations = await self.generate_fix_recommendations()
        
        # Summary
        print("\n📊 DEBUG SUMMARY")
        print("=" * 40)
        print(f"Issues Found: {len(self.issues_found)}")
        print(f"Fixes Available: {len(recommendations)}")
        
        if self.issues_found:
            print("\n❌ Issues Found:")
            for issue in self.issues_found:
                print(f"   • {issue}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Apply the recommended fixes above")
        print("2. Add detailed error logging to workflow nodes")
        print("3. Verify Gemini-LangGraph async compatibility")
        print("4. Test individual nodes before full workflow execution")
        print("5. Re-run tests after applying fixes")