import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GeminiConfig:
    """Gemini AI and LLM configuration class"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Gemini Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 5))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Generation Config
    TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.05'))
    MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_MAX_OUTPUT_TOKENS', '3000'))
    TOP_P = float(os.getenv('GEMINI_TOP_P', '0.7'))
    TOP_K = int(os.getenv('GEMINI_TOP_K', '40'))
    
    # Visualization Config
    VIZ_TEMPERATURE = float(os.getenv('GEMINI_VIZ_TEMPERATURE', '0.05'))
    VIZ_MAX_OUTPUT_TOKENS = int(os.getenv('GEMINI_VIZ_MAX_OUTPUT_TOKENS', '2000'))
    VIZ_TOP_P = float(os.getenv('GEMINI_VIZ_TOP_P', '0.7'))
    VIZ_TOP_K = int(os.getenv('GEMINI_VIZ_TOP_K', '40'))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required Gemini configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        if cls.GOOGLE_API_KEY == 'your-gemini-api-key-here':
            raise ValueError("Please set a valid GOOGLE_API_KEY")
        
        return True
    
    @classmethod
    def get_generation_config(cls):
        """Get generation config for query generation"""
        return {
            'temperature': cls.TEMPERATURE,
            'max_output_tokens': cls.MAX_OUTPUT_TOKENS,
            'top_p': cls.TOP_P,
            'top_k': cls.TOP_K
        }
    
    @classmethod
    def get_viz_generation_config(cls):
        """Get generation config for visualization generation"""
        return {
            'temperature': cls.VIZ_TEMPERATURE,
            'max_output_tokens': cls.VIZ_MAX_OUTPUT_TOKENS,
            'top_p': cls.VIZ_TOP_P,
            'top_k': cls.VIZ_TOP_K
        }

# Prompt Templates
QUERY_PROMPT_TEMPLATE = """You are an expert MongoDB query generator. Convert natural language questions to perfect MongoDB aggregation pipelines.

USER QUESTION: "{user_question}"

DATABASE SCHEMA:
{schema_info}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Use exact field names from schema
3. Create efficient aggregation pipelines
4. Always include $sort and $limit for performance
5. Choose appropriate chart type based on question

RESPONSE FORMAT (JSON only):
{{
  "collection": "costevalutionforllm|documentextractions|obligationextractions|agent_activity",
  "pipeline": [
    {{"$match": {{"condition": "value"}}}},
    {{"$group": {{"_id": "$field", "metric": {{"$sum": "$value"}}}}}},
    {{"$sort": {{"metric": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar|pie|line|doughnut",
  "query_intent": "Description of what this query achieves"
}}

JSON only - no other text:"""

VISUALIZATION_PROMPT_TEMPLATE = """You are an expert data visualization specialist. Create perfect Chart.js configurations.

USER QUESTION: "{user_question}"
DATA SAMPLE: {sample_data}
TOTAL RECORDS: {total_records}
QUERY CONTEXT: {query_context}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Always include ALL required fields: chart_type, chart_config, summary, insights, recommendations
3. Make chart_config a complete, working Chart.js configuration
4. Ensure all JSON is properly formatted with correct quotes and brackets

REQUIRED JSON STRUCTURE:
{{
  "chart_type": "bar",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["Label1", "Label2"],
      "datasets": [{{
        "label": "Dataset Name", 
        "data": [100, 200],
        "backgroundColor": "rgba(59, 130, 246, 0.8)",
        "borderColor": "rgba(59, 130, 246, 1)",
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "maintainAspectRatio": false,
      "plugins": {{
        "title": {{"display": true, "text": "Chart Title"}},
        "legend": {{"display": false}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true}},
        "x": {{"display": true}}
      }}
    }}
  }},
  "summary": "Clear summary with specific numbers and insights",
  "insights": [
    "Specific insight with data",
    "Another meaningful insight"
  ],
  "recommendations": [
    "Actionable recommendation",
    "Strategic suggestion"
  ]
}}

JSON only:"""