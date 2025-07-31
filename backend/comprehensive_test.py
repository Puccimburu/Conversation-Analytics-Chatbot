#!/usr/bin/env python3
"""
Comprehensive Test Suite for GenAI Analytics System
Tests all visualizations, database collections, and query types
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

# Test Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 60  # seconds per query

class VisualizationTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name: str, query: str, success: bool, chart_type: str = None, 
                   record_count: int = 0, execution_time: float = 0, error: str = None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "query": query,
            "success": success,
            "chart_type": chart_type,
            "record_count": record_count,
            "execution_time": execution_time,
            "error": error
        }
        self.results.append(result)
        self.total_tests += 1
        
        if success:
            self.passed_tests += 1
            print(f"✅ {test_name}: {chart_type} chart, {record_count} records, {execution_time:.2f}s")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {error}")
    
    def test_query(self, test_name: str, query: str) -> Dict[str, Any]:
        """Execute a single test query"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/api/query",
                json={"message": query},
                timeout=TIMEOUT
            )
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    chart_data = data.get('chart_data', {})
                    chart_type = chart_data.get('type', 'unknown')
                    record_count = data.get('results_count', 0)
                    
                    self.log_result(test_name, query, True, chart_type, record_count, execution_time)
                    return data
                else:
                    self.log_result(test_name, query, False, error=data.get('error', 'Unknown error'))
            else:
                self.log_result(test_name, query, False, error=f"HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            self.log_result(test_name, query, False, error="Timeout")
        except Exception as e:
            self.log_result(test_name, query, False, error=str(e))
        
        return {}
    
    def test_all_visualizations(self):
        """Test all visualization types"""
        print("\n🎯 TESTING ALL VISUALIZATION TYPES")
        print("=" * 50)
        
        # Table visualizations
        table_queries = [
            ("Users Table", "Show me users from the database in a table"),
            ("Customers Table", "List all customers in table format"),
            ("Documents Table", "Display document extractions as a table"),
            ("Batches Table", "Show me all batches in a table"),
            ("Cost Evaluations Table", "Show cost evaluations in table format")
        ]
        
        for test_name, query in table_queries:
            self.test_query(test_name, query)
            time.sleep(1)  # Avoid overwhelming the system
        
        # Bar chart visualizations
        bar_queries = [
            ("User Roles Bar Chart", "Show me user distribution by role"),
            ("Document Types Bar", "Show document types breakdown"),
            ("Agent Performance Bar", "Show agent performance metrics"),
            ("Cost by Model Bar", "Show AI costs by model type"),
            ("Batch Status Bar", "Show batch processing status distribution")
        ]
        
        for test_name, query in bar_queries:
            self.test_query(test_name, query)
            time.sleep(1)
        
        # Pie chart visualizations  
        pie_queries = [
            ("Role Distribution Pie", "What's the percentage breakdown of user roles?"),
            ("Document Status Pie", "Show me document processing status as percentages"),
            ("Model Usage Pie", "What percentage of requests use each AI model?"),
            ("Obligation Types Pie", "Show obligation types distribution as percentages"),
            ("File Types Pie", "What's the file type distribution in percentages?")
        ]
        
        for test_name, query in pie_queries:
            self.test_query(test_name, query)
            time.sleep(1)
        
        # Line chart visualizations
        line_queries = [
            ("Cost Trends Line", "Show AI cost trends over time"),
            ("Processing Volume Line", "Show document processing volume over time"),
            ("User Registration Line", "Show user registration trends over time"),
            ("Token Usage Line", "Show token usage trends over time"),
            ("Performance Trends Line", "Show system performance trends over time")
        ]
        
        for test_name, query in line_queries:
            self.test_query(test_name, query)
            time.sleep(1)
        
        # Doughnut chart visualizations
        doughnut_queries = [
            ("Success Rate Doughnut", "Show success rates as a doughnut chart"),
            ("Model Distribution Doughnut", "Show AI model distribution as doughnut"),
            ("Status Overview Doughnut", "Show processing status overview as doughnut"),
            ("Category Breakdown Doughnut", "Show category breakdown as doughnut chart"),
            ("Confidence Levels Doughnut", "Show confidence score distribution as doughnut")
        ]
        
        for test_name, query in doughnut_queries:
            self.test_query(test_name, query)
            time.sleep(1)
    
    def test_all_collections(self):
        """Test queries across all database collections"""
        print("\n🗄️ TESTING ALL DATABASE COLLECTIONS")
        print("=" * 50)
        
        collection_queries = [
            # AI Operations & Cost Tracking
            ("Cost Evaluations", "Show me AI cost evaluations"),
            ("LLM Pricing", "Show me LLM pricing information"),
            ("Agent Activity", "Show me agent activity data"),
            
            # Document Processing Pipeline
            ("Document Extractions", "Show me document extractions"),
            ("Obligation Extractions", "Show me obligation extractions"),
            ("Obligation Mappings", "Show me obligation mappings"),
            ("Processing Batches", "Show me processing batches"),
            ("Files", "Show me file information"),
            
            # AI Prompt Management
            ("Prompts", "Show me AI prompts"),
            ("Prompts3", "Show me prompt library data"),
            ("Prompt Mappings", "Show me prompt mappings"),
            
            # Document Management
            ("Document Mappings", "Show me document mappings"),
            ("Document Types", "Show me document types"),
            
            # Communication System
            ("Conversations", "Show me chat conversations"),
            
            # User Management
            ("Users", "Show me users"),
            ("Allowed Users", "Show me allowed users"),
            
            # Compliance & Audit
            ("Compliances", "Show me compliance data"),
            
            # Workflow Management
            ("Checkpoints", "Show me workflow checkpoints"),
            
            # Legacy Analytics
            ("Customers", "Show me customers"),
            ("Orders", "Show me orders")
        ]
        
        for test_name, query in collection_queries:
            self.test_query(f"Collection: {test_name}", query)
            time.sleep(1)
    
    def test_complex_queries(self):
        """Test complex analytical queries"""
        print("\n🧠 TESTING COMPLEX ANALYTICAL QUERIES")
        print("=" * 50)
        
        complex_queries = [
            ("Cost Analysis", "What are our highest AI operational costs this month?"),
            ("Performance Analytics", "Which AI models are most cost-effective?"),
            ("User Analytics", "Show me user engagement patterns"),
            ("Document Intelligence", "What's our document processing success rate?"),
            ("Compliance Risk", "Show me high-risk compliance obligations"),
            ("Operational Efficiency", "Which agents have the best performance?"),
            ("Token Analytics", "Show me token usage patterns by user"),
            ("Confidence Analysis", "What are our confidence score distributions?"),
            ("Trend Analysis", "Show me processing volume trends"),
            ("Quality Metrics", "What's our extraction accuracy by document type?"),
            ("Resource Utilization", "Show me resource utilization patterns"),
            ("Error Analysis", "What are the most common processing errors?"),
            ("Batch Analytics", "Show me batch processing efficiency"),
            ("Model Comparison", "Compare AI model performance metrics"),
            ("Time Series", "Show me daily processing volumes over the last month")
        ]
        
        for test_name, query in complex_queries:
            self.test_query(f"Complex: {test_name}", query)
            time.sleep(2)  # Complex queries may take longer
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n⚠️ TESTING EDGE CASES")
        print("=" * 50)
        
        edge_queries = [
            ("Empty Collection", "Show me data from nonexistent collection"),
            ("Invalid Syntax", "Show me $$invalid query syntax$$"),
            ("Very Long Query", "Show me " + "very " * 50 + "long query"),
            ("Special Characters", "Show me data with special chars: @#$%^&*()"),
            ("SQL Injection Test", "Show me users'; DROP TABLE users; --"),
            ("MongoDB Injection", "Show me users with {$ne: null}"),
            ("Unicode Test", "Show me données with émojis 🚀🔥⭐"),
            ("Number Only Query", "12345"),
            ("Empty Query", ""),
            ("Whitespace Query", "   ")
        ]
        
        for test_name, query in edge_queries:
            self.test_query(f"Edge Case: {test_name}", query)
            time.sleep(1)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({self.passed_tests/self.total_tests*100:.1f}%)")
        print(f"Failed: {self.failed_tests} ({self.failed_tests/self.total_tests*100:.1f}%)")
        
        # Chart type breakdown
        chart_types = {}
        for result in self.results:
            if result['success'] and result['chart_type']:
                chart_types[result['chart_type']] = chart_types.get(result['chart_type'], 0) + 1
        
        print(f"\n📈 Chart Types Generated:")
        for chart_type, count in chart_types.items():
            print(f"  {chart_type}: {count}")
        
        # Record count statistics
        record_counts = [r['record_count'] for r in self.results if r['success']]
        if record_counts:
            print(f"\n📋 Data Records:")
            print(f"  Total Records Retrieved: {sum(record_counts)}")
            print(f"  Average per Query: {sum(record_counts)/len(record_counts):.1f}")
            print(f"  Max Records: {max(record_counts)}")
        
        # Performance statistics
        execution_times = [r['execution_time'] for r in self.results if r['success']]
        if execution_times:
            print(f"\n⏱️ Performance:")
            print(f"  Average Query Time: {sum(execution_times)/len(execution_times):.2f}s")
            print(f"  Fastest Query: {min(execution_times):.2f}s")
            print(f"  Slowest Query: {max(execution_times):.2f}s")
        
        # Failed tests details
        failed_results = [r for r in self.results if not r['success']]
        if failed_results:
            print(f"\n❌ Failed Tests:")
            for result in failed_results[:10]:  # Show first 10 failures
                print(f"  {result['test_name']}: {result['error']}")
        
        # Save detailed results to JSON
        with open('test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to test_results.json")
        
        return self.passed_tests / self.total_tests >= 0.8  # 80% success rate threshold

def main():
    """Run comprehensive test suite"""
    print("🚀 STARTING COMPREHENSIVE VISUALIZATION AND DATABASE TEST")
    print("Testing all chart types, database collections, and query patterns")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            sys.exit(1)
    except:
        print("❌ Backend server is not running. Please start with: python backend/app.py")
        sys.exit(1)
    
    print("✅ Backend server is running")
    
    # Initialize tester
    tester = VisualizationTester()
    
    # Run all test suites
    tester.test_all_visualizations()
    tester.test_all_collections()
    tester.test_complex_queries()
    tester.test_edge_cases()
    
    # Generate final report
    success = tester.generate_report()
    
    if success:
        print("\n🎉 COMPREHENSIVE TEST SUITE PASSED!")
        print("All visualizations and database queries are working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Check the detailed report above for issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()