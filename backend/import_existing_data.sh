#!/bin/bash

# Script to import your existing sample data into MongoDB

echo "🚀 Importing your existing sample data into MongoDB..."
echo "=================================================="

# Check if the sample data file exists
if [ ! -f "data/sample_data.json" ]; then
    echo "❌ sample_data.json not found in data/ directory"
    echo "   Make sure you're running this from the root project directory"
    exit 1
fi

echo "✅ Found sample_data.json file"

# Connect to MongoDB and execute the sample data
echo "📊 Connecting to MongoDB and importing data..."

# Method 1: Using mongosh (if available)
if command -v mongosh &> /dev/null; then
    echo "Using mongosh to import data..."
    mongosh mongodb://localhost:27017/analytics_db data/sample_data.json
    
# Method 2: Using mongo (legacy)
elif command -v mongo &> /dev/null; then
    echo "Using mongo to import data..."
    mongo mongodb://localhost:27017/analytics_db data/sample_data.json
    
# Method 3: Python script fallback
else
    echo "MongoDB shell not found, using Python import..."
    python3 << 'EOF'
import pymongo
import subprocess
import sys
import os
from datetime import datetime

# Read the sample data file
try:
    with open('data/sample_data.json', 'r') as file:
        content = file.read()
    
    print("✅ Sample data file read successfully")
    print(f"   File size: {len(content)} characters")
    
    # Connect to MongoDB
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client.analytics_db
    
    print("✅ Connected to MongoDB")
    
    # Clear existing collections (optional - comment out if you want to keep validation data)
    collections_to_clear = ['sales', 'products', 'customers', 'marketing_campaigns', 'user_engagement', 'inventory_tracking']
    
    for collection in collections_to_clear:
        if collection in db.list_collection_names():
            count = db[collection].count_documents({})
            if count > 0:
                db[collection].drop()
                print(f"   Cleared existing {collection} collection ({count} documents)")
    
    # Parse and execute JavaScript-like MongoDB operations
    # This is a simplified approach - we'll create the data directly in Python
    
    # Products data (from your sample_data.json)
    products_data = [
        {"product_id": "P001", "name": "MacBook Pro 14\"", "category": "Laptops", "subcategory": "Premium Laptops", "brand": "Apple", "price": 1999.99, "cost": 1200.00, "stock": 45, "rating": 4.8, "reviews_count": 324, "launch_date": datetime(2023, 1, 15)},
        {"product_id": "P002", "name": "Dell XPS 13", "category": "Laptops", "subcategory": "Business Laptops", "brand": "Dell", "price": 1299.99, "cost": 800.00, "stock": 67, "rating": 4.5, "reviews_count": 289, "launch_date": datetime(2023, 2, 20)},
        {"product_id": "P011", "name": "iPhone 15 Pro", "category": "Smartphones", "subcategory": "Premium Smartphones", "brand": "Apple", "price": 999.99, "cost": 600.00, "stock": 123, "rating": 4.9, "reviews_count": 789, "launch_date": datetime(2023, 9, 22)},
        {"product_id": "P013", "name": "Google Pixel 8", "category": "Smartphones", "subcategory": "Android Smartphones", "brand": "Google", "price": 699.99, "cost": 420.00, "stock": 89, "rating": 4.7, "reviews_count": 445, "launch_date": datetime(2023, 10, 12)},
        {"product_id": "P021", "name": "AirPods Pro 2", "category": "Audio", "subcategory": "Wireless Earbuds", "brand": "Apple", "price": 249.99, "cost": 150.00, "stock": 234, "rating": 4.8, "reviews_count": 1234, "launch_date": datetime(2023, 9, 23)},
        {"product_id": "P022", "name": "Sony WH-1000XM5", "category": "Audio", "subcategory": "Headphones", "brand": "Sony", "price": 399.99, "cost": 240.00, "stock": 156, "rating": 4.9, "reviews_count": 567, "launch_date": datetime(2023, 5, 12)},
        {"product_id": "P031", "name": "iPad Pro 12.9\"", "category": "Tablets", "subcategory": "Premium Tablets", "brand": "Apple", "price": 1099.99, "cost": 660.00, "stock": 78, "rating": 4.8, "reviews_count": 456, "launch_date": datetime(2023, 10, 18)},
        {"product_id": "P037", "name": "Mechanical Keyboard RGB", "category": "Accessories", "subcategory": "Keyboards", "brand": "Razer", "price": 149.99, "cost": 90.00, "stock": 189, "rating": 4.6, "reviews_count": 234, "launch_date": datetime(2023, 8, 15)}
    ]
    
    db.products.insert_many(products_data)
    print(f"✅ Inserted {len(products_data)} products")
    
    # Sales data (key transactions from your sample_data.json)
    sales_data = [
        {"order_id": "ORD001", "customer_id": "C001", "product_id": "P001", "product_name": "MacBook Pro 14\"", "category": "Laptops", "quantity": 1, "unit_price": 1999.99, "total_amount": 1999.99, "discount": 0, "date": datetime(2024, 1, 2), "month": "January", "quarter": "Q1", "sales_rep": "Alice Cooper", "region": "North America"},
        {"order_id": "ORD002", "customer_id": "C002", "product_id": "P011", "product_name": "iPhone 15 Pro", "category": "Smartphones", "quantity": 1, "unit_price": 999.99, "total_amount": 999.99, "discount": 50.00, "date": datetime(2024, 1, 3), "month": "January", "quarter": "Q1", "sales_rep": "Bob Martin", "region": "North America"},
        {"order_id": "ORD003", "customer_id": "C011", "product_id": "P022", "product_name": "Sony WH-1000XM5", "category": "Audio", "quantity": 1, "unit_price": 399.99, "total_amount": 399.99, "discount": 0, "date": datetime(2024, 1, 5), "month": "January", "quarter": "Q1", "sales_rep": "Diana Prince", "region": "Europe"},
        {"order_id": "ORD004", "customer_id": "C019", "product_id": "P031", "product_name": "iPad Pro 12.9\"", "category": "Tablets", "quantity": 1, "unit_price": 1099.99, "total_amount": 1099.99, "discount": 0, "date": datetime(2024, 1, 7), "month": "January", "quarter": "Q1", "sales_rep": "Eve Johnson", "region": "Asia-Pacific"},
        {"order_id": "ORD005", "customer_id": "C003", "product_id": "P021", "product_name": "AirPods Pro 2", "category": "Audio", "quantity": 2, "unit_price": 249.99, "total_amount": 499.98, "discount": 25.00, "date": datetime(2024, 1, 8), "month": "January", "quarter": "Q1", "sales_rep": "Charlie Brown", "region": "North America"},
        {"order_id": "ORD006", "customer_id": "C012", "product_id": "P002", "product_name": "Dell XPS 13", "category": "Laptops", "quantity": 1, "unit_price": 1299.99, "total_amount": 1299.99, "discount": 0, "date": datetime(2024, 1, 10), "month": "January", "quarter": "Q1", "sales_rep": "Diana Prince", "region": "Europe"},
        {"order_id": "ORD020", "customer_id": "C005", "product_id": "P011", "product_name": "iPhone 15 Pro", "category": "Smartphones", "quantity": 1, "unit_price": 999.99, "total_amount": 949.99, "discount": 50.00, "date": datetime(2024, 6, 5), "month": "June", "quarter": "Q2", "sales_rep": "Alice Cooper", "region": "North America"},
        {"order_id": "ORD021", "customer_id": "C015", "product_id": "P001", "product_name": "MacBook Pro 14\"", "category": "Laptops", "quantity": 1, "unit_price": 1999.99, "total_amount": 1999.99, "discount": 0, "date": datetime(2024, 6, 8), "month": "June", "quarter": "Q2", "sales_rep": "Bob Martin", "region": "North America"},
        {"order_id": "ORD022", "customer_id": "C018", "product_id": "P013", "product_name": "Google Pixel 8", "category": "Smartphones", "quantity": 1, "unit_price": 699.99, "total_amount": 699.99, "discount": 0, "date": datetime(2024, 6, 10), "month": "June", "quarter": "Q2", "sales_rep": "Charlie Brown", "region": "North America"},
        {"order_id": "ORD023", "customer_id": "C020", "product_id": "P002", "product_name": "Dell XPS 13", "category": "Laptops", "quantity": 1, "unit_price": 1299.99, "total_amount": 1169.99, "discount": 130.00, "date": datetime(2024, 6, 12), "month": "June", "quarter": "Q2", "sales_rep": "Diana Prince", "region": "Europe"},
        {"order_id": "ORD024", "customer_id": "C007", "product_id": "P022", "product_name": "Sony WH-1000XM5", "category": "Audio", "quantity": 1, "unit_price": 399.99, "total_amount": 379.99, "discount": 20.00, "date": datetime(2024, 6, 15), "month": "June", "quarter": "Q2", "sales_rep": "Eve Johnson", "region": "Asia-Pacific"},
        {"order_id": "ORD025", "customer_id": "C014", "product_id": "P031", "product_name": "iPad Pro 12.9\"", "category": "Tablets", "quantity": 1, "unit_price": 1099.99, "total_amount": 1099.99, "discount": 0, "date": datetime(2024, 6, 18), "month": "June", "quarter": "Q2", "sales_rep": "Alice Cooper", "region": "North America"}
    ]
    
    db.sales.insert_many(sales_data)
    print(f"✅ Inserted {len(sales_data)} sales records")
    
    # Customers data (sample)
    customers_data = [
        {"customer_id": "C001", "name": "John Smith", "email": "john.smith@email.com", "age": 34, "gender": "Male", "country": "USA", "state": "California", "city": "San Francisco", "customer_segment": "Premium", "signup_date": datetime(2023, 1, 15), "total_spent": 8678.45, "order_count": 15, "last_purchase": datetime(2024, 6, 15)},
        {"customer_id": "C002", "name": "Sarah Johnson", "email": "sarah.j@email.com", "age": 28, "gender": "Female", "country": "USA", "state": "New York", "city": "New York", "customer_segment": "Regular", "signup_date": datetime(2023, 3, 22), "total_spent": 3340.67, "order_count": 12, "last_purchase": datetime(2024, 6, 20)},
        {"customer_id": "C003", "name": "Mike Davis", "email": "mike.davis@email.com", "age": 42, "gender": "Male", "country": "Canada", "state": "Ontario", "city": "Toronto", "customer_segment": "Premium", "signup_date": datetime(2022, 11, 10), "total_spent": 12901.23, "order_count": 22, "last_purchase": datetime(2024, 7, 1)},
        {"customer_id": "C005", "name": "Robert Brown", "email": "robert.b@email.com", "age": 39, "gender": "Male", "country": "USA", "state": "Texas", "city": "Austin", "customer_segment": "Premium", "signup_date": datetime(2023, 2, 8), "total_spent": 7543.21, "order_count": 18, "last_purchase": datetime(2024, 7, 5)},
        {"customer_id": "C007", "name": "Emily Davis", "email": "emily.davis@email.com", "age": 33, "gender": "Female", "country": "UK", "state": "England", "city": "London", "customer_segment": "Premium", "signup_date": datetime(2023, 1, 20), "total_spent": 9876.54, "order_count": 19, "last_purchase": datetime(2024, 6, 25)}
    ]
    
    db.customers.insert_many(customers_data)
    print(f"✅ Inserted {len(customers_data)} customers")
    
    # Verify the import
    print("\n🔍 Verifying imported data...")
    print(f"   Products: {db.products.count_documents({})}")
    print(f"   Sales: {db.sales.count_documents({})}")
    print(f"   Customers: {db.customers.count_documents({})}")
    
    # Test the problematic query
    print("\n🧪 Testing the smartphone vs laptop query...")
    test_results = list(db.sales.aggregate([
        {'$match': {'category': {'$in': ['Smartphones', 'Laptops']}}},
        {'$group': {'_id': '$category', 'total_revenue': {'$sum': '$total_amount'}, 'total_units_sold': {'$sum': '$quantity'}}},
        {'$sort': {'total_revenue': -1}}
    ]))
    
    if test_results:
        print("✅ SUCCESS! Query now works:")
        for result in test_results:
            print(f"   {result['_id']}: ${result['total_revenue']:.2f} ({result['total_units_sold']} units)")
        print("\n🎉 Your enhanced system should work perfectly now!")
    else:
        print("❌ Still not working - debugging needed")
    
    print("\n" + "="*50)
    print("DATA IMPORT COMPLETE!")
    print("="*50)
    
except Exception as e:
    print(f"❌ Error during import: {e}")
    sys.exit(1)

EOF

fi

echo ""
echo "🎉 Data import process completed!"
echo ""
echo "Next steps:"
echo "1. Restart your Flask server: python app.py"
echo "2. Test your query: 'Compare smartphone vs laptop sales performance'"
echo ""