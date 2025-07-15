import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/analytics_db')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'analytics_db')
    
    # Flask Configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Gemini Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Query Limits
    MAX_RESULTS_LIMIT = int(os.getenv('MAX_RESULTS_LIMIT', 100))
    DEFAULT_RESULTS_LIMIT = int(os.getenv('DEFAULT_RESULTS_LIMIT', 15))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is required")
        
        return True

# Database Schema Configuration
DATABASE_SCHEMA = {
    "collections": {
        "sales": {
            "fields": [
                "order_id", "customer_id", "product_id", "product_name", 
                "category", "quantity", "unit_price", "total_amount", 
                "discount", "date", "month", "quarter", "sales_rep", "region"
            ],
            "date_fields": ["date"],
            "numeric_fields": ["quantity", "unit_price", "total_amount", "discount"]
        },
        "products": {
            "fields": [
                "product_id", "name", "category", "brand", "price", 
                "cost", "stock", "rating", "reviews_count"
            ],
            "numeric_fields": ["price", "cost", "stock", "rating", "reviews_count"]
        },
        "customers": {
            "fields": [
                "customer_id", "name", "email", "age", "gender", 
                "country", "state", "city", "customer_segment", 
                "total_spent", "order_count"
            ],
            "numeric_fields": ["age", "total_spent", "order_count"]
        },
        "user_engagement": {
            "fields": [
                "customer_id", "session_date", "page_views", 
                "time_spent_minutes", "actions_taken", "device", 
                "source", "bounce_rate"
            ],
            "date_fields": ["session_date"],
            "numeric_fields": ["page_views", "time_spent_minutes", "actions_taken"],
            "boolean_fields": ["bounce_rate"]
        },
        "marketing_campaigns": {
            "fields": [
                "campaign_id", "name", "type", "start_date", "end_date", 
                "budget", "spent", "impressions", "clicks", "conversions", 
                "revenue_generated", "target_audience", "ctr", "conversion_rate"
            ],
            "date_fields": ["start_date", "end_date"],
            "numeric_fields": [
                "budget", "spent", "impressions", "clicks", "conversions", 
                "revenue_generated", "ctr", "conversion_rate"
            ]
        },
        "inventory_tracking": {
            "fields": [
                "product_id", "date", "stock_level", "reorder_point", 
                "supplier", "last_restock", "units_sold_month"
            ],
            "date_fields": ["date", "last_restock"],
            "numeric_fields": ["stock_level", "reorder_point", "units_sold_month"]
        }
    }
}

# Chart Type Mapping
CHART_TYPE_MAPPING = {
    "time_series": "line",
    "categorical_comparison": "bar",
    "distribution": "pie",
    "percentage": "doughnut",
    "trend": "line",
    "ranking": "bar"
}

# Sample Query Templates
SAMPLE_QUERIES = [
    "What were our top 5 selling products this quarter?",
    "Show me revenue by region and month",
    "Which customer segment generates the most profit?",
    "Compare smartphone vs laptop sales performance",
    "What's our conversion rate by marketing channel?",
    "Show me inventory levels for low-stock products",
    "Which sales reps are performing best by region?",
    "What's the customer lifetime value by country?",
    "How does user engagement correlate with purchase behavior?",
    "Which products have the highest profit margins?"
]