import google.generativeai as genai
import json
import time
import logging
from config.config import Config
from .query_builder import PromptBuilder, validate_json_response

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self):
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.prompt_builder = PromptBuilder()
    
    def generate_query(self, user_question, schema_info, max_retries=3):
        """Generate MongoDB query from natural language"""
        
        prompt = self.prompt_builder.build_query_prompt(user_question, schema_info)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating query for: {user_question} (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,  # Low temperature for more consistent results
                        max_output_tokens=1000,
                        top_p=0.8
                    )
                )
                
                # Parse and validate response
                result = validate_json_response(response.text)
                
                # Validate required fields
                required_fields = ['collection', 'mongo_query', 'chart_type', 'chart_mapping']
                if not all(field in result for field in required_fields):
                    raise ValueError(f"Missing required fields in response: {required_fields}")
                
                # Validate chart_type
                valid_chart_types = ['bar', 'pie', 'line', 'doughnut']
                if result['chart_type'] not in valid_chart_types:
                    result['chart_type'] = 'bar'  # Default fallback
                
                # Validate chart_mapping
                if not isinstance(result['chart_mapping'], dict):
                    raise ValueError("chart_mapping must be a dictionary")
                
                logger.info(f"Successfully generated query for collection: {result['collection']}")
                return result
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate query after {max_retries} attempts: {str(e)}")
                time.sleep(1)  # Brief delay before retry
    
    def generate_summary(self, user_question, query_results, query_intent, max_retries=2):
        """Generate text summary from query results"""
        
        prompt = self.prompt_builder.build_summary_prompt(user_question, query_results, query_intent)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating summary (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,  # Slightly higher for more natural language
                        max_output_tokens=200,
                        top_p=0.9
                    )
                )
                
                summary = response.text.strip()
                
                # Basic validation
                if len(summary) < 10:
                    raise ValueError("Summary too short")
                
                if len(summary) > 500:
                    summary = summary[:500] + "..."
                
                logger.info("Successfully generated summary")
                return summary
                
            except Exception as e:
                logger.warning(f"Summary attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    # Fallback summary
                    return f"Analysis complete. Found {len(query_results)} results for your query about {user_question.lower()}."
    
    def analyze_query_intent(self, user_question):
        """Analyze the intent behind a user's question"""
        
        intent_prompt = f"""
Analyze this business analytics question and categorize the intent:

Question: "{user_question}"

Classify into one of these categories:
- sales_analysis: Questions about sales performance, revenue, top products
- customer_insights: Questions about customer behavior, demographics, segments
- product_analysis: Questions about product performance, inventory, ratings
- time_trend: Questions about trends over time, growth, seasonal patterns
- comparison: Questions comparing different categories, regions, periods
- operational: Questions about inventory, supply chain, operations

Respond with only the category name.
"""
        
        try:
            response = self.model.generate_content(intent_prompt)
            intent = response.text.strip().lower()
            
            valid_intents = [
                'sales_analysis', 'customer_insights', 'product_analysis',
                'time_trend', 'comparison', 'operational'
            ]
            
            if intent in valid_intents:
                return intent
            else:
                return 'sales_analysis'  # Default fallback
                
        except Exception as e:
            logger.warning(f"Intent analysis failed: {str(e)}")
            return 'sales_analysis'  # Default fallback

# Global Gemini client instance
gemini_client = None

def get_gemini_client():
    """Get or create Gemini client instance"""
    global gemini_client
    if gemini_client is None:
        gemini_client = GeminiClient()
    return gemini_client

def validate_api_key():
    """Validate that the API key is working"""
    try:
        client = get_gemini_client()
        test_response = client.model.generate_content("Hello")
        return True
    except Exception as e:
        logger.error(f"API key validation failed: {str(e)}")
        return False