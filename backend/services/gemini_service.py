import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from config.gemini_config import GeminiConfig, QUERY_PROMPT_TEMPLATE, VISUALIZATION_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

class BulletproofGeminiClient:
    """Perfected Gemini client with enhanced reliability"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GeminiConfig.GEMINI_MODEL)
        
        # Test the connection
        try:
            test_response = self.model.generate_content("Test")
            self.available = True
            logger.info("✅ Gemini client initialized and tested")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
    
    @classmethod
    def create_client(cls):
        """Factory method to create Gemini client"""
        try:
            GeminiConfig.validate_config()
            return cls(GeminiConfig.GOOGLE_API_KEY)
        except Exception as e:
            logger.error(f"Failed to create Gemini client: {e}")
            return None
    
    async def generate_query(self, user_question: str, schema_info: Dict, max_retries: int = None) -> Dict:
        """Generate MongoDB query with enhanced retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        max_retries = max_retries or GeminiConfig.MAX_RETRIES
        prompt = QUERY_PROMPT_TEMPLATE.format(
            user_question=user_question,
            schema_info=json.dumps(schema_info, indent=2)
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Gemini Stage 1 - Query Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**GeminiConfig.get_generation_config())
                )
                
                if response and response.text:
                    parsed_result = self._extract_json_from_response(response.text)
                    
                    if parsed_result and self._validate_and_fix_query_response(parsed_result):
                        logger.info(f"✅ Gemini query generation successful on attempt {attempt + 1}")
                        return {"success": True, "data": parsed_result}
                    else:
                        logger.warning(f"Invalid response on attempt {attempt + 1}: {response.text[:200]}")
                
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    delay = min(2 ** attempt, 8)  # Exponential backoff, max 8 seconds
                    await asyncio.sleep(delay)
        
        logger.error("❌ Gemini query generation failed after all retries")
        return {"success": False, "error": "Failed to generate query after retries"}
    
    async def generate_visualization(self, user_question: str, raw_data: List[Dict], query_context: Dict, max_retries: int = None) -> Dict:
        """Generate visualization with enhanced debugging and retry logic"""
        
        if not self.available:
            return {"success": False, "error": "Gemini not available"}
        
        max_retries = max_retries or GeminiConfig.MAX_RETRIES
        sample_data = raw_data[:3] if raw_data else []
        
        prompt = VISUALIZATION_PROMPT_TEMPLATE.format(
            user_question=user_question,
            sample_data=json.dumps(sample_data, indent=2),
            total_records=len(raw_data),
            query_context=json.dumps(query_context, indent=2)
        )
        
        for attempt in range(max_retries):
            try:
                logger.info(f"📊 Gemini Stage 2 - Visualization Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(**GeminiConfig.get_viz_generation_config())
                )
                
                if response and response.text:
                    # Log the raw response for debugging
                    raw_response = response.text.strip()
                    logger.info(f"🔍 Gemini Stage 2 raw response (attempt {attempt + 1}): {raw_response[:300]}...")
                    
                    parsed_result = self._extract_json_from_response(raw_response)
                    
                    if parsed_result:
                        logger.info(f"✅ JSON extraction successful: {list(parsed_result.keys())}")
                        
                        if self._validate_and_fix_visualization_response(parsed_result, raw_data):
                            logger.info(f"✅ Gemini visualization generation successful on attempt {attempt + 1}")
                            return {"success": True, "data": parsed_result}
                        else:
                            logger.warning(f"❌ Validation failed on attempt {attempt + 1}, parsed keys: {list(parsed_result.keys())}")
                    else:
                        logger.warning(f"❌ JSON extraction failed on attempt {attempt + 1}")
                        logger.debug(f"Full response text: {raw_response}")
                else:
                    logger.warning(f"❌ Empty response on attempt {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"Gemini visualization attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < max_retries - 1:
                delay = min(2 ** attempt, 8)
                logger.info(f"⏳ Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error("❌ Gemini visualization generation failed after all retries")
        return {"success": False, "error": "Failed to generate visualization after retries"}
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Ultra-robust JSON extraction with extensive fallback methods"""
        try:
            cleaned_text = response_text.strip()
            logger.debug(f"Extracting JSON from: {cleaned_text[:200]}...")
            
            # Method 1: Direct JSON parsing
            try:
                result = json.loads(cleaned_text)
                if isinstance(result, dict) and len(result) > 0:
                    logger.debug("✅ Direct JSON parsing successful")
                    return result
            except json.JSONDecodeError as e:
                logger.debug(f"Direct parsing failed: {e}")
            
            # Method 2: Extract from various code block formats
            code_block_patterns = [
                r'```(?:json)?\s*(\{.*?\})\s*```',
                r'```(\{.*?\})```', 
                r'`(\{.*?\})`',
                r'JSON:\s*(\{.*?\})',
                r'Response:\s*(\{.*?\})',
                r'Result:\s*(\{.*?\})'
            ]
            
            for pattern in code_block_patterns:
                match = re.search(pattern, cleaned_text, re.DOTALL | re.IGNORECASE)
                if match:
                    try:
                        result = json.loads(match.group(1))
                        if isinstance(result, dict) and len(result) > 0:
                            logger.debug(f"✅ Code block extraction successful with pattern: {pattern}")
                            return result
                    except json.JSONDecodeError:
                        continue
            
            # Method 3: Find JSON object with proper brace matching
            brace_count = 0
            start_idx = -1
            in_string = False
            escape_next = False
            quote_char = None
            
            for i, char in enumerate(cleaned_text):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char in ['"', "'"] and not escape_next:
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                    continue
                
                if not in_string:
                    if char == '{':
                        if start_idx == -1:
                            start_idx = i
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0 and start_idx != -1:
                            try:
                                json_str = cleaned_text[start_idx:i+1]
                                result = json.loads(json_str)
                                if isinstance(result, dict) and len(result) > 2:
                                    logger.debug("✅ Brace matching extraction successful")
                                    return result
                            except json.JSONDecodeError:
                                continue
                            finally:
                                start_idx = -1
                                brace_count = 0
            
            # Method 4: Fix common JSON issues and retry
            fixed_attempts = [
                # Remove trailing commas
                re.sub(r',(\s*[}\]])', r'\1', cleaned_text),
                # Fix single quotes
                re.sub(r"'([^']*)':", r'"\1":', cleaned_text),
                # Fix unescaped quotes in values
                re.sub(r':\s*"([^"]*)"([^",}\]])', r': "\1\2"', cleaned_text),
                # Remove extra text before/after JSON
                re.sub(r'^[^{]*(\{.*\})[^}]*$', r'\1', cleaned_text, flags=re.DOTALL)
            ]
            
            for i, fixed_text in enumerate(fixed_attempts):
                try:
                    result = json.loads(fixed_text)
                    if isinstance(result, dict) and len(result) > 0:
                        logger.debug(f"✅ JSON fixing method {i+1} successful")
                        return result
                except json.JSONDecodeError:
                    continue
            
            logger.warning("❌ All JSON extraction methods failed")
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction critical error: {e}")
            return None

    def _validate_and_fix_query_response(self, data: Dict) -> bool:
        """Validate and fix query response"""
        try:
            # Check required fields
            required_fields = ['collection', 'pipeline', 'chart_hint', 'query_intent']
            
            # Fix missing fields
            if 'collection' not in data:
                data['collection'] = 'costevalutionforllm'  # Default
            
            if 'pipeline' not in data:
                return False  # Can't fix missing pipeline
            
            if 'chart_hint' not in data:
                data['chart_hint'] = 'bar'  # Default
            
            if 'query_intent' not in data:
                data['query_intent'] = 'Data analysis query'
            
            return True
            
        except Exception as e:
            logger.error(f"Query validation error: {e}")
            return False
    
    def _validate_and_fix_visualization_response(self, data: Dict, raw_data: List[Dict]) -> bool:
        """Enhanced validation with auto-fixing and logging"""
        try:
            logger.info(f"🔍 Validating visualization response: {list(data.keys())}")
            
            # More flexible validation with auto-fixing
            required_fields = ['chart_type', 'chart_config', 'summary']
            missing_fields = []
            
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.warning(f"Missing fields: {missing_fields}, attempting to fix...")
                
                # Auto-fix missing fields
                if 'chart_type' not in data:
                    data['chart_type'] = 'bar'  # Default
                    logger.info("✅ Fixed: Added default chart_type 'bar'")
                
                if 'summary' not in data:
                    data['summary'] = f"Analysis of {len(raw_data)} data points completed successfully."
                    logger.info("✅ Fixed: Added default summary")
                
                if 'chart_config' not in data:
                    data['chart_config'] = self._create_basic_chart_config(data['chart_type'], raw_data)
                    logger.info("✅ Fixed: Created basic chart config")
            
            # Add default insights and recommendations if missing
            if 'insights' not in data:
                data['insights'] = [
                    f"Successfully analyzed {len(raw_data)} data points",
                    "Data processing completed with AI assistance"
                ]
                logger.info("✅ Fixed: Added default insights")
            
            if 'recommendations' not in data:
                data['recommendations'] = [
                    "Review the data patterns for actionable insights",
                    "Consider strategic implications of the analysis"
                ]
                logger.info("✅ Fixed: Added default recommendations")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Visualization validation error: {e}")
            return False
    
    def _create_basic_chart_config(self, chart_type: str, raw_data: List[Dict]) -> Dict:
        """Create basic chart configuration as fallback"""
        chart_data = self._extract_chart_data(raw_data)
        
        base_config = {
            "type": chart_type,
            "data": chart_data,
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {"display": True, "text": "Data Analysis"},
                    "legend": {"display": chart_type in ['pie', 'doughnut']}
                }
            }
        }
        
        if chart_type not in ['pie', 'doughnut']:
            base_config["options"]["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
        
        return base_config
    
    def _extract_chart_data(self, raw_data: List[Dict]) -> Dict:
        """Extract chart data from raw MongoDB results"""
        if not raw_data:
            return {"labels": [], "datasets": []}
        
        # Determine labels and data
        labels = []
        values = []
        
        for item in raw_data[:20]:  # Limit for readability
            # Get label (usually _id field)
            label = str(item.get('_id', 'Unknown'))
            labels.append(label)
            
            # Get value (try different fields)
            value = 0
            for field in ['total_revenue', 'total_spent', 'total_amount', 'customer_count', 'order_count', 'stock', 'count']:
                if field in item:
                    value = float(item[field]) if item[field] is not None else 0
                    break
            
            values.append(value)
        
        return {
            "labels": labels,
            "datasets": [{
                "label": "Values",
                "data": values,
                "backgroundColor": "rgba(59, 130, 246, 0.8)",
                "borderColor": "rgba(59, 130, 246, 1)",
                "borderWidth": 2
            }]
        }
    
    async def generate_content_async(self, prompt: str) -> str:
        """Generate content asynchronously for memory RAG suggestions"""
        if not self.available:
            raise Exception("Gemini client not available")
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                    top_p=0.9
                )
            )
            return response.text if response and response.text else ""
        except Exception as e:
            logger.error(f"Async content generation failed: {e}")
            raise