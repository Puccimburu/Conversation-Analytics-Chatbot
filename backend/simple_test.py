#!/usr/bin/env python3
"""
Simple Test Suite for GenAI Analytics System
Tests key visualizations and database collections
"""

import requests
import json
import time
import sys

# Test Configuration
BASE_URL = "http://localhost:5000"
TIMEOUT = 45  # seconds per query

def test_query(test_name, query):
    """Execute a single test query"""
    try:
        print(f"\nTesting: {test_name}")
        print(f"Query: {query}")
        
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
                summary = data.get('summary', 'No summary')
                
                print(f"SUCCESS: {chart_type} chart, {record_count} records, {execution_time:.2f}s")
                print(f"Summary: {summary[:100]}...")
                
                # Check for table data
                if chart_type == 'table':
                    table_data = chart_data.get('tableData', [])
                    columns = chart_data.get('columns', [])
                    print(f"Table: {len(table_data)} rows, {len(columns)} columns")
                
                return True
            else:
                print(f"FAILED: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"FAILED: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("FAILED: Timeout")
        return False
    except Exception as e:
        print(f"FAILED: {str(e)}")
        return False

def main():
    """Run key tests"""
    print("COMPREHENSIVE VISUALIZATION AND DATABASE TEST")
    print("=" * 50)
    
    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("Backend server is not responding properly")
            sys.exit(1)
    except:
        print("Backend server is not running. Please start with: python backend/app.py")
        sys.exit(1)
    
    print("Backend server is running")
    
    # Test results tracking
    total_tests = 0
    passed_tests = 0
    
    # Test all visualization types
    test_cases = [
        # Table visualizations
        ("Users Table", "Show me users from the database in a table"),
        ("Customers Table", "List all customers in table format"), 
        ("Documents Table", "Display document extractions as a table"),
        
        # Bar charts
        ("User Roles Bar", "Show me user distribution by role"),
        ("Document Types Bar", "Show document types breakdown"),
        ("Agent Performance Bar", "Show agent performance metrics"),
        
        # Pie charts
        ("Role Distribution Pie", "What's the percentage breakdown of user roles?"),
        ("Document Status Pie", "Show me document processing status as percentages"),
        ("Model Usage Pie", "What percentage of requests use each AI model?"),
        
        # Line charts
        ("Cost Trends Line", "Show AI cost trends over time"),
        ("Processing Volume Line", "Show document processing volume over time"),
        ("User Registration Line", "Show user registration trends over time"),
        
        # Doughnut charts
        ("Success Rate Doughnut", "Show success rates as a doughnut chart"),
        ("Model Distribution Doughnut", "Show AI model distribution as doughnut"),
        
        # Database collections
        ("Cost Evaluations", "Show me AI cost evaluations"),
        ("Agent Activity", "Show me agent activity data"),
        ("Obligation Extractions", "Show me obligation extractions"),
        ("Processing Batches", "Show me processing batches"),
        ("Files", "Show me file information"),
        ("Prompts", "Show me AI prompts"),
        ("Conversations", "Show me chat conversations"),
        ("Compliances", "Show me compliance data"),
        
        # Complex queries
        ("Cost Analysis", "What are our highest AI operational costs this month?"),
        ("Performance Analytics", "Which AI models are most cost-effective?"),
        ("Document Intelligence", "What's our document processing success rate?"),
        ("Compliance Risk", "Show me high-risk compliance obligations"),
        ("Token Usage", "Show me token usage patterns by user"),
        ("Confidence Analysis", "What are our confidence score distributions?")
    ]
    
    # Run all tests
    for test_name, query in test_cases:
        total_tests += 1
        if test_query(test_name, query):
            passed_tests += 1
        time.sleep(2)  # Avoid overwhelming the system
    
    # Final report
    print("\n" + "=" * 50)
    print("TEST REPORT")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed: {total_tests - passed_tests} ({(total_tests-passed_tests)/total_tests*100:.1f}%)")
    
    if passed_tests / total_tests >= 0.8:
        print("\nTEST SUITE PASSED!")
        print("Most visualizations and database queries are working correctly.")
        return True
    else:
        print("\nSOME TESTS FAILED")
        print("Check the output above for specific issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)