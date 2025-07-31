#!/usr/bin/env python3
"""
Test direct MongoDB queries
"""
import pymongo
import os
from pprint import pprint

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://puccimburu:lrcJzcn6tKcz6X2O@conversational-analytic.ugl1wyj.mongodb.net/?retryWrites=true&w=majority&appName=conversational-analytics')
client = pymongo.MongoClient(MONGODB_URI)
db = client.genai

# Test a simple query on users collection
print('=== TESTING USERS QUERY ===')
pipeline = [
    {"$group": {
        "_id": "$role", 
        "count": {"$sum": 1}
    }},
    {"$sort": {"count": -1}}
]

print('Pipeline:', pipeline)
results = list(db.users.aggregate(pipeline))
print('Results:', results)
print()

# Test cost query
print('=== TESTING COST QUERY ===')
pipeline2 = [
    {"$group": {
        "_id": "$batchId", 
        "total_cost": {"$sum": "$totalCostInUSD"},
        "total_tokens": {"$sum": "$totalTokens"}
    }},
    {"$sort": {"total_cost": -1}},
    {"$limit": 10}
]

print('Pipeline:', pipeline2)
results2 = list(db.costevalutionforllm.aggregate(pipeline2))
print('Results count:', len(results2))
if results2:
    pprint(results2[0])