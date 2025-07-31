#!/usr/bin/env python3
"""
Quick test of core functionality
"""
import requests
import json

# Test without chat_id to avoid memory enhancement
def test_basic_query():
    try:
        print("Testing basic query processing...")
        
        response = requests.post(
            "http://localhost:5000/api/query",
            json={"question": "What data do we have available?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get('success'):
                print(f"Processing Mode: {data.get('processing_mode')}")
                print(f"Records: {data.get('results_count', 0)}")
                print(f"Summary: {data.get('summary', 'No summary')[:100]}")
                return True
            else:
                print(f"Error: {data.get('error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_simple_collections():
    """Test simple collection queries"""
    queries = [
        "Show me users",
        "Show me agent activity", 
        "Show me documents",
        "Show me batches"
    ]
    
    results = []
    for query in queries:
        print(f"\nTesting: {query}")
        try:
            response = requests.post(
                "http://localhost:5000/api/query",
                json={"question": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                results.append(success)
                
                if success:
                    print(f"✓ Success: {data.get('results_count', 0)} records")
                    print(f"  Processing: {data.get('processing_mode', 'unknown')}")
                else:
                    print(f"✗ Failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"✗ HTTP {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"✗ Exception: {e}")
            results.append(False)
    
    return results

if __name__ == "__main__":
    print("=== QUICK FUNCTIONALITY TEST ===")
    
    # Test basic processing
    basic_success = test_basic_query()
    
    print("\n=== COLLECTION TESTS ===")
    collection_results = test_simple_collections()
    
    # Summary
    total_tests = 1 + len(collection_results)
    passed_tests = (1 if basic_success else 0) + sum(collection_results)
    
    print(f"\n=== RESULTS ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests > total_tests * 0.5:
        print("✓ Core functionality is working")
    else:
        print("✗ Core functionality has issues")