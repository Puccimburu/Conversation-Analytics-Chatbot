#!/usr/bin/env python3
"""
Test the table intent detection fix
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.enhanced_gemini_client import BulletproofGeminiClient

def test_intent_detection():
    """Test the table intent detection"""
    # Create a mock client just to test the intent detection method
    client = BulletproofGeminiClient("dummy_key")
    
    test_queries = [
        ("Show me all the prompts", True),
        ("List all users", True), 
        ("Display all files", True),
        ("Show me all documents in table format", True),
        ("Get all batches", True),
        ("Show cost trends over time", False),
        ("What's the breakdown of user roles?", False),
        ("Compare model performance", False),
    ]
    
    print("Testing table intent detection...")
    print("=" * 50)
    
    correct = 0
    total = len(test_queries)
    
    for query, expected in test_queries:
        detected = client._detect_table_intent(query)
        status = "PASS" if detected == expected else "FAIL"
        print(f"{status}: '{query}' -> Expected: {expected}, Got: {detected}")
        if detected == expected:
            correct += 1
    
    print("=" * 50)
    print(f"Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
    
    if correct == total:
        print("SUCCESS: All intent detection tests passed!")
        return True
    else:
        print("FAILED: Some intent detection tests failed!")
        return False

if __name__ == "__main__":
    success = test_intent_detection()
    sys.exit(0 if success else 1)