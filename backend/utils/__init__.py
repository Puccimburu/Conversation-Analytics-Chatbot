"""
Utility modules for the Conversational Analytics backend.

This package contains:
- database.py: Database connection and operations
- gemini_client.py: Google Gemini API integration
- query_builder.py: MongoDB query building and chart type selection
"""

__version__ = "1.0.0"
__author__ = "Conversational Analytics Team"

# Import main classes for easy access

__all__ = [
    'DatabaseManager',
    'get_db',
    'get_db_manager',
    'GeminiClient',
    'get_gemini_client',
    'validate_api_key',
    'QueryBuilder',
    'ChartTypeSelector',
    'PromptBuilder'
]