#!/usr/bin/env python3
"""
Intent Recognition and Visualization Adaptation Test
Tests if Gemini understands user intent and returns appropriate visualizations
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Categorized test queries with expected visualization types
TEST_QUERIES = {
    "LIST_QUERIES_SHOULD_BE_TABLES": [
        ("Show me all the prompts", "table"),
        ("List all available files", "table"), 
        ("Get all registered users", "table"),
        ("Display all batches", "table"),
        ("Show me all files uploaded after January 1st, 2025", "table"),
        ("Find all conversations updated in the last week", "table"),
        ("List orders placed in the month of June 2025", "table"),
    ],
    
    "COUNT_QUERIES_SHOULD_BE_METRICS": [
        ("How many files are in a 'completed' status?", ["bar", "pie", "metric"]),
        ("Count the total number of prompts", ["bar", "pie", "metric"]),
        ("How many conversations does user123 have?", ["bar", "pie", "metric"]),
        ("What is the total cost across all LLM cost evaluations?", ["bar", "pie", "metric"]),
        ("What's the average cost for LLM evaluations related to batch ABC?", ["bar", "pie", "metric"]),
        ("Calculate the sum of total price for all orders", ["bar", "pie", "metric"]),
    ],
    
    "GROUPING_QUERIES_SHOULD_BE_CHARTS": [
        ("Count how many times each promptType appears in the prompts collection", ["bar", "pie"]),
        ("Tell me the total number of unique batchIds in costevalutionforllm", ["bar", "pie"]),
        ("Group cost of evaluation by batch and show the total tokens used for each batch", ["bar", "pie"]),
        ("Show me the average ratePerMillionInputTokens for each modelVariant in llmpricing", ["bar", "pie"]),
        ("Group agent activities by Agent and count their Outcomes", ["bar", "pie"]),
    ],
    
    "COMPLEX_QUERIES_SHOULD_BE_TABLES": [
        ("Show me all orders and include the customer's name for each order", "table"),
        ("List all files and their associated batch names", "table"),
        ("For each batch, show me the names of the files it contains", "table"),
    ]
}

def test_query_intent(query, expected_types, category):
    """Test a single query and check if the visualization matches intent"""
    try:
        print(f"\n🔍 Testing: {query}")
        print(f"   Category: {category}")
        print(f"   Expected: {expected_types}")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"question": query},
            timeout=60
        )
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                chart_data = data.get('chart_data', {})
                actual_type = chart_data.get('type', 'unknown')
                record_count = data.get('results_count', 0)
                summary = data.get('summary', '')[:80]
                
                # Check if actual type matches expected
                if isinstance(expected_types, list):
                    intent_match = actual_type in expected_types
                else:
                    intent_match = actual_type == expected_types
                
                if intent_match:
                    print(f"   ✅ SUCCESS: Got {actual_type} ({record_count} records)")
                    print(f"   📊 Summary: {summary}...")
                    print(f"   ⏱️  Time: {execution_time:.2f}s")
                    return True, actual_type, record_count
                else:
                    print(f"   ❌ INTENT MISMATCH: Expected {expected_types}, got {actual_type}")
                    print(f"   📊 Records: {record_count}")
                    return False, actual_type, record_count
            else:
                print(f"   ❌ QUERY FAILED: {data.get('error', 'Unknown error')}")
                return False, "error", 0
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            return False, "http_error", 0
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {str(e)}")
        return False, "exception", 0

def run_intent_test():
    """Run comprehensive intent recognition test"""
    print("=" * 80)
    print("🧠 GEMINI INTENT RECOGNITION & VISUALIZATION ADAPTATION TEST")
    print("=" * 80)
    print("Testing if Gemini understands user intent and returns appropriate visualizations")
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server not responding")
            return False
    except:
        print("❌ Backend server not running")
        return False
    
    print("✅ Backend server is running")
    
    # Track results
    total_tests = 0
    passed_tests = 0
    intent_matches = 0
    results_by_category = {}
    
    # Run tests by category
    for category, queries in TEST_QUERIES.items():
        print(f"\n{'='*60}")
        print(f"📋 TESTING CATEGORY: {category}")
        print(f"{'='*60}")
        
        category_results = []
        
        for query, expected_types in queries:
            total_tests += 1
            success, actual_type, record_count = test_query_intent(query, expected_types, category)
            
            if success:
                passed_tests += 1
                intent_matches += 1
            elif actual_type not in ["error", "http_error", "exception"]:
                passed_tests += 1  # Query worked, just wrong visualization type
                
            category_results.append({
                "query": query,
                "expected": expected_types, 
                "actual": actual_type,
                "success": success,
                "records": record_count
            })
            
            time.sleep(2)  # Don't overwhelm the system
        
        results_by_category[category] = category_results
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE INTENT RECOGNITION REPORT")
    print(f"{'='*80}")
    
    print(f"📈 Overall Results:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful Queries: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   Intent Matches: {intent_matches} ({intent_matches/total_tests*100:.1f}%)")
    
    print(f"\n📋 Results by Category:")
    for category, results in results_by_category.items():
        total_cat = len(results)
        successful_cat = sum(1 for r in results if r['success'])
        print(f"   {category}: {successful_cat}/{total_cat} ({successful_cat/total_cat*100:.1f}%)")
    
    print(f"\n📊 Visualization Type Distribution:")
    type_counts = {}
    for results in results_by_category.values():
        for result in results:
            if result['actual'] not in ["error", "http_error", "exception"]:
                type_counts[result['actual']] = type_counts.get(result['actual'], 0) + 1
    
    for viz_type, count in sorted(type_counts.items()):
        print(f"   {viz_type}: {count}")
    
    # Identify problem areas
    print(f"\n⚠️  Intent Recognition Issues:")
    for category, results in results_by_category.items():
        failed_intents = [r for r in results if not r['success'] and r['actual'] not in ["error", "http_error", "exception"]]
        if failed_intents:
            print(f"   {category}:")
            for result in failed_intents:
                print(f"     - '{result['query'][:50]}...' → Expected {result['expected']}, got {result['actual']}")
    
    # Success criteria
    intent_success_rate = intent_matches / total_tests
    query_success_rate = passed_tests / total_tests
    
    print(f"\n🎯 ASSESSMENT:")
    if intent_success_rate >= 0.8:
        print("✅ EXCELLENT: Gemini shows strong intent recognition (≥80%)")
    elif intent_success_rate >= 0.6:
        print("⚠️  GOOD: Gemini shows decent intent recognition (≥60%)")
    else:
        print("❌ NEEDS IMPROVEMENT: Intent recognition below 60%")
    
    if query_success_rate >= 0.9:
        print("✅ EXCELLENT: Query processing is very reliable (≥90%)")
    elif query_success_rate >= 0.7:
        print("⚠️  GOOD: Query processing is reliable (≥70%)")
    else:
        print("❌ NEEDS IMPROVEMENT: Query processing below 70%")
    
    print(f"\n💡 CONCLUSION:")
    if intent_success_rate >= 0.75 and query_success_rate >= 0.8:
        print("🎉 SYSTEM IS READY: Gemini adapts well to different query intents!")
        print("   Users can expect appropriate visualizations for their requests.")
    else:
        print("🔧 SYSTEM NEEDS TUNING: Some intent recognition improvements needed.")
        print("   Consider enhancing Gemini prompts for better visualization selection.")
    
    return intent_success_rate >= 0.75 and query_success_rate >= 0.8

if __name__ == "__main__":
    success = run_intent_test()
    exit(0 if success else 1)