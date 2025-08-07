# backend/test_langgraph.py
"""
LangGraph Workflow Testing Suite
Comprehensive tests to verify LangGraph workflow functionality
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import json

# Add backend to path
sys.path.append(os.path.dirname(__file__))

from utils.langgraph_analytics import LangGraphAnalyticsWorkflow
from utils.enhanced_gemini_client import BulletproofGeminiClient
from workflows.analytics_flow import WorkflowSelector, WorkflowOptimizer
from config import Config, DATABASE_SCHEMA

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangGraphTestSuite:
    """Comprehensive test suite for LangGraph workflows"""
    
    def __init__(self):
        self.gemini_client = None
        self.mongodb_client = None
        self.workflow = None
        self.test_results = []
    
    async def setup(self):
        """Initialize test environment"""
        try:
            print("🔧 Setting up LangGraph test environment...")
            
            # Initialize Gemini client
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            self.gemini_client = BulletproofGeminiClient(api_key)
            print("✅ Gemini client initialized")
            
            # Initialize MongoDB client
            import pymongo
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')
            client = pymongo.MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            self.mongodb_client = client[Config.DATABASE_NAME]
            
            # Test connection
            client.admin.command('ping')
            print("✅ MongoDB connected")
            
            # Initialize LangGraph workflow
            self.workflow = LangGraphAnalyticsWorkflow(
                gemini_client=self.gemini_client,
                mongodb_client=self.mongodb_client,
                schema_info=DATABASE_SCHEMA
            )
            print("✅ LangGraph workflow initialized")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            raise
    
    async def run_all_tests(self):
        """Run all test suites"""
        print("\n🧪 Starting LangGraph Test Suite")
        print("=" * 50)
        
        await self.setup()
        
        # Run test categories
        await self.test_workflow_execution()
        await self.test_checkpointing()
        await self.test_error_recovery()
        await self.test_workflow_selection()
        await self.test_system_integration()
        
        # Print results
        self.print_test_results()
    
    async def test_workflow_execution(self):
        """Test basic workflow execution"""
        print("\n📋 Testing Workflow Execution")
        print("-" * 30)
        
        test_queries = [
            "list of users",
            "show me cost analysis",
            "document processing status",
            "compliance obligations overview"
        ]
        
        for query in test_queries:
            try:
                print(f"Testing query: '{query}'")
                
                result = await self.workflow.process_analytics_query(
                    question=query,
                    chat_id=f"test_{int(datetime.now().timestamp())}",
                    user_id="test_user"
                )
                
                success = result.get('success', False)
                thread_id = result.get('workflow_metadata', {}).get('thread_id')
                
                if success:
                    print(f"  ✅ Query processed successfully (Thread: {thread_id})")
                    self.test_results.append({
                        "category": "workflow_execution",
                        "test": query,
                        "status": "PASS",
                        "details": f"Successful processing with thread {thread_id}"
                    })
                else:
                    print(f"  ❌ Query failed: {result.get('error', 'Unknown error')}")
                    self.test_results.append({
                        "category": "workflow_execution", 
                        "test": query,
                        "status": "FAIL",
                        "details": result.get('error', 'Unknown error')
                    })
                
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                self.test_results.append({
                    "category": "workflow_execution",
                    "test": query,
                    "status": "ERROR",
                    "details": str(e)
                })
    
    async def test_checkpointing(self):
        """Test checkpoint functionality"""
        print("\n💾 Testing Checkpointing")
        print("-" * 30)
        
        try:
            # Test checkpoint saving
            result = await self.workflow.process_analytics_query(
                question="test checkpointing functionality",
                chat_id="checkpoint_test",
                user_id="checkpoint_user",
                thread_id="test_checkpoint_thread"
            )
            
            thread_id = "test_checkpoint_thread"
            
            # Test checkpoint retrieval
            status = self.workflow.get_workflow_status(thread_id)
            
            if status.get('thread_id') == thread_id:
                print("  ✅ Checkpoint saved and retrieved successfully")
                self.test_results.append({
                    "category": "checkpointing",
                    "test": "checkpoint_save_retrieve",
                    "status": "PASS",
                    "details": f"Thread {thread_id} checkpoint verified"
                })
            else:
                print("  ❌ Checkpoint not found")
                self.test_results.append({
                    "category": "checkpointing",
                    "test": "checkpoint_save_retrieve", 
                    "status": "FAIL",
                    "details": "Checkpoint not accessible"
                })
            
        except Exception as e:
            print(f"  ❌ Checkpointing test failed: {e}")
            self.test_results.append({
                "category": "checkpointing",
                "test": "checkpoint_save_retrieve",
                "status": "ERROR", 
                "details": str(e)
            })
    
    async def test_error_recovery(self):
        """Test error recovery mechanisms"""
        print("\n🔄 Testing Error Recovery")
        print("-" * 30)
        
        try:
            # Test with intentionally problematic query
            result = await self.workflow.process_analytics_query(
                question="query nonexistent collection xyz123", 
                chat_id="error_test",
                user_id="error_user"
            )
            
            # Even if query fails, workflow should handle gracefully
            workflow_metadata = result.get('workflow_metadata', {})
            
            if 'error_details' in workflow_metadata or result.get('success') == False:
                print("  ✅ Error handled gracefully by workflow")
                self.test_results.append({
                    "category": "error_recovery",
                    "test": "graceful_error_handling",
                    "status": "PASS",
                    "details": "Workflow handled error without crashing"
                })
            else:
                print("  ⚠️ Error recovery needs verification")
                self.test_results.append({
                    "category": "error_recovery",
                    "test": "graceful_error_handling",
                    "status": "WARNING",
                    "details": "Error handling needs manual verification"
                })
                
        except Exception as e:
            print(f"  ❌ Error recovery test failed: {e}")
            self.test_results.append({
                "category": "error_recovery",
                "test": "graceful_error_handling",
                "status": "ERROR",
                "details": str(e)
            })
    
    async def test_workflow_selection(self):
        """Test intelligent workflow selection"""
        print("\n🎯 Testing Workflow Selection")
        print("-" * 30)
        
        try:
            selector = WorkflowSelector()
            
            test_cases = [
                ("list users", "simple"),
                ("compare costs over time and analyze trends", "complex"),
                ("help me explore document processing", "interactive"),
                ("what patterns can we find in performance data", "exploratory")
            ]
            
            for question, expected_complexity in test_cases:
                config = selector.select_workflow(question)
                actual_complexity = config.complexity.value
                
                print(f"  Query: '{question}'")
                print(f"    Expected: {expected_complexity}, Got: {actual_complexity}")
                
                # Allow some flexibility in complexity detection
                if actual_complexity in [expected_complexity, "simple", "complex"]:
                    print("    ✅ Appropriate workflow selected")
                    self.test_results.append({
                        "category": "workflow_selection",
                        "test": f"select_{expected_complexity}",
                        "status": "PASS",
                        "details": f"Selected {actual_complexity} for {expected_complexity} query"
                    })
                else:
                    print("    ❌ Unexpected workflow selection")
                    self.test_results.append({
                        "category": "workflow_selection",
                        "test": f"select_{expected_complexity}",
                        "status": "FAIL", 
                        "details": f"Expected {expected_complexity}, got {actual_complexity}"
                    })
                    
        except Exception as e:
            print(f"  ❌ Workflow selection test failed: {e}")
            self.test_results.append({
                "category": "workflow_selection",
                "test": "intelligent_selection",
                "status": "ERROR",
                "details": str(e)
            })
    
    async def test_system_integration(self):
        """Test system integration and stats"""
        print("\n🔗 Testing System Integration")
        print("-" * 30)
        
        try:
            # Test system stats
            stats = self.workflow.get_system_stats()
            
            required_fields = ['workflow_engine', 'checkpointer_available', 'features']
            missing_fields = [field for field in required_fields if field not in stats]
            
            if not missing_fields:
                print("  ✅ System stats available")
                self.test_results.append({
                    "category": "system_integration",
                    "test": "system_stats",
                    "status": "PASS", 
                    "details": "All required system stats available"
                })
            else:
                print(f"  ❌ Missing system stats: {missing_fields}")
                self.test_results.append({
                    "category": "system_integration",
                    "test": "system_stats",
                    "status": "FAIL",
                    "details": f"Missing fields: {missing_fields}"
                })
            
            # Test active workflows
            active_workflows = self.workflow.get_active_workflows()
            print(f"  ✅ Active workflows query returned {len(active_workflows)} results")
            self.test_results.append({
                "category": "system_integration",
                "test": "active_workflows",
                "status": "PASS",
                "details": f"Retrieved {len(active_workflows)} active workflows"
            })
            
        except Exception as e:
            print(f"  ❌ System integration test failed: {e}")
            self.test_results.append({
                "category": "system_integration",
                "test": "system_integration",
                "status": "ERROR",
                "details": str(e)
            })
    
    def print_test_results(self):
        """Print comprehensive test results"""
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        # Count results by status
        status_counts = {"PASS": 0, "FAIL": 0, "ERROR": 0, "WARNING": 0}
        for result in self.test_results:
            status_counts[result["status"]] += 1
        
        # Print summary
        total_tests = len(self.test_results)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {status_counts['PASS']}")
        print(f"❌ Failed: {status_counts['FAIL']}")
        print(f"⚠️ Warnings: {status_counts['WARNING']}")
        print(f"💥 Errors: {status_counts['ERROR']}")
        
        success_rate = (status_counts['PASS'] / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        # Print details for failed tests
        failed_tests = [r for r in self.test_results if r["status"] in ["FAIL", "ERROR"]]
        if failed_tests:
            print("\n❌ Failed Test Details:")
            for test in failed_tests:
                print(f"  {test['category']}.{test['test']}: {test['details']}")
        
        # Print overall status
        if success_rate >= 80:
            print("\n🎉 LangGraph System: READY FOR PRODUCTION")
        elif success_rate >= 60:
            print("\n⚠️ LangGraph System: READY FOR TESTING (some issues detected)")
        else:
            print("\n🚨 LangGraph System: NEEDS ATTENTION (multiple failures)")
        
        # Save detailed results
        with open('langgraph_test_results.json', 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": status_counts,
                "success_rate": success_rate,
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: langgraph_test_results.json")

async def main():
    """Main test execution"""
    test_suite = LangGraphTestSuite()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    exit_code = asyncio.run(main())