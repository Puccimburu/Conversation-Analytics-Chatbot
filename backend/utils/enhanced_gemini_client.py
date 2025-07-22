import google.generativeai as genai
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryStage(Enum):
    QUERY_GENERATION = "query_generation"
    VISUALIZATION = "visualization"

@dataclass
class GeminiResponse:
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    attempts: int = 1
    stage: Optional[QueryStage] = None

class BulletproofGeminiClient:
    """
    Enhanced Gemini client with bulletproof reliability and two-stage processing
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        if not api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Enhanced configuration for better reliability
        self.query_config = genai.types.GenerationConfig(
            temperature=0.1,  # Very low for consistent query generation
            max_output_tokens=1500,
            top_p=0.8,
            top_k=40
        )
        
        self.viz_config = genai.types.GenerationConfig(
            temperature=0.2,  # Slightly higher for creative visualizations
            max_output_tokens=2000,
            top_p=0.9,
            top_k=50
        )
        
        # Validation patterns for each stage
        self.required_query_fields = ['collection', 'pipeline', 'chart_hint', 'query_intent']
        self.required_viz_fields = ['chart_type', 'chart_config', 'summary', 'insights']
        
    async def generate_query_with_retry(self, user_question: str, schema_info: Dict, 
                                      max_retries: int = 5) -> GeminiResponse:
        """
        Stage 1: Generate MongoDB query with bulletproof retry logic
        """
        logger.info(f"🔍 Stage 1 - Query Generation: {user_question}")
        
        prompt = self._build_query_prompt(user_question, schema_info)
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"   Attempt {attempt}/{max_retries}")
                
                response = await self._make_gemini_call(
                    prompt, 
                    self.query_config,
                    stage=QueryStage.QUERY_GENERATION
                )
                
                if response.success:
                    # Enhanced validation for query response
                    if self._validate_query_response(response.data):
                        logger.info(f"✅ Query generation successful on attempt {attempt}")
                        response.attempts = attempt
                        return response
                    else:
                        logger.warning(f"   Query validation failed on attempt {attempt}")
                        
            except Exception as e:
                logger.warning(f"   Attempt {attempt} failed: {str(e)}")
                
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + (attempt * 0.5)
                    logger.info(f"   Retrying in {delay:.1f} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Query generation failed after {max_retries} attempts")
                    return GeminiResponse(
                        success=False, 
                        data={}, 
                        error=f"Failed after {max_retries} attempts: {str(e)}",
                        attempts=attempt,
                        stage=QueryStage.QUERY_GENERATION
                    )
        
        # Fallback response if all retries failed
        return self._create_fallback_query_response(user_question)
    
    async def generate_visualization_with_retry(self, user_question: str, raw_data: List[Dict], 
                                              query_context: Dict, max_retries: int = 5) -> GeminiResponse:
        """
        Stage 2: Generate visualization config with bulletproof retry logic
        """
        logger.info(f"📊 Stage 2 - Visualization Generation for {len(raw_data)} results")
        
        prompt = self._build_visualization_prompt(user_question, raw_data, query_context)
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"   Attempt {attempt}/{max_retries}")
                
                response = await self._make_gemini_call(
                    prompt, 
                    self.viz_config,
                    stage=QueryStage.VISUALIZATION
                )
                
                if response.success:
                    if self._validate_visualization_response(response.data):
                        logger.info(f"✅ Visualization generation successful on attempt {attempt}")
                        response.attempts = attempt
                        return response
                    else:
                        logger.warning(f"   Visualization validation failed on attempt {attempt}")
                        
            except Exception as e:
                logger.warning(f"   Attempt {attempt} failed: {str(e)}")
                
                if attempt < max_retries:
                    delay = (2 ** attempt) + (attempt * 0.3)
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Visualization generation failed after {max_retries} attempts")
                    return GeminiResponse(
                        success=False, 
                        data={}, 
                        error=f"Failed after {max_retries} attempts: {str(e)}",
                        attempts=attempt,
                        stage=QueryStage.VISUALIZATION
                    )
        
        # Fallback visualization if all retries failed
        return self._create_fallback_visualization_response(user_question, raw_data)
    
    async def _make_gemini_call(self, prompt: str, config: genai.types.GenerationConfig, 
                              stage: QueryStage) -> GeminiResponse:
        """
        Make a single Gemini API call with enhanced error handling
        """
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            # Extract and parse JSON from response
            parsed_data = self._extract_json_from_response(response.text, stage)
            
            if not parsed_data:
                raise ValueError("Could not extract valid JSON from response")
            
            return GeminiResponse(success=True, data=parsed_data, stage=stage)
            
        except Exception as e:
            logger.warning(f"Gemini call failed: {str(e)}")
            raise e
    
    def _extract_json_from_response(self, response_text: str, stage: QueryStage) -> Optional[Dict]:
        """
        Enhanced JSON extraction with multiple fallback methods
        """
        import re
        
        cleaned_text = response_text.strip()
        
        # Method 1: Direct JSON parsing
        try:
            result = json.loads(cleaned_text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract from code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, cleaned_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Method 3: Find JSON object boundaries
        brace_count = 0
        start_idx = -1
        
        for i, char in enumerate(cleaned_text):
            if char == '{':
                if start_idx == -1:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        json_str = cleaned_text[start_idx:i+1]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
        
        # Method 4: Attempt to fix common JSON issues
        try:
            # Remove trailing commas
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
            # Fix single quotes to double quotes
            fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        logger.error(f"Failed to extract JSON from response: {cleaned_text[:200]}...")
        return None
    
    def _build_query_prompt(self, user_question: str, schema_info: Dict) -> str:
        """
        Build enhanced prompt for Stage 1 - Query Generation
        """
        return f"""You are an expert MongoDB query architect. Convert natural language questions to MongoDB aggregation pipelines.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations
2. Use exact field names from schema
3. Create efficient aggregation pipelines
4. Consider data relationships and constraints

SCHEMA INFORMATION:
{json.dumps(schema_info, indent=2)}

USER QUESTION: "{user_question}"

RESPONSE FORMAT (JSON only):
{{
  "collection": "collection_name",
  "pipeline": [
    {{"$match": {{"field": "value"}}}},
    {{"$group": {{"_id": "$field", "metric": {{"$sum": "$value"}}}}}},
    {{"$sort": {{"metric": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar|pie|line|doughnut",
  "query_intent": "Brief description of what this query achieves",
  "expected_fields": ["field1", "field2"],
  "data_summary": "What the results should contain"
}}

EXAMPLES:

For "Compare smartphone vs laptop sales":
{{
  "collection": "sales",
  "pipeline": [
    {{"$match": {{"category": {{"$in": ["Smartphones", "Laptops"]}}}}}},
    {{"$group": {{"_id": "$category", "total_revenue": {{"$sum": "$total_amount"}}, "total_quantity": {{"$sum": "$quantity"}}}}}},
    {{"$sort": {{"total_revenue": -1}}}}
  ],
  "chart_hint": "bar",
  "query_intent": "Compare revenue and quantity between smartphone and laptop categories",
  "expected_fields": ["_id", "total_revenue", "total_quantity"],
  "data_summary": "Revenue and quantity totals for each category"
}}

JSON only - no other text:"""

    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], 
                                  query_context: Dict) -> str:
        """
        Build enhanced prompt for Stage 2 - Visualization Generation
        """
        # Sample the data for context (limit to 5 records for prompt efficiency)
        sample_data = raw_data[:5] if raw_data else []
        
        return f"""You are a data visualization expert. Create Chart.js configurations and insights based on query results.

USER QUESTION: "{user_question}"
QUERY CONTEXT: {json.dumps(query_context, indent=2)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations
2. Choose optimal chart type for the data pattern
3. Create meaningful summaries with specific insights
4. Include Chart.js configuration ready for rendering

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["label1", "label2"],
      "datasets": [{{
        "label": "Dataset Name",
        "data": [100, 200],
        "backgroundColor": ["color1", "color2"],
        "borderColor": ["border1", "border2"],
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "Chart Title"}},
        "legend": {{"display": true}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true}},
        "x": {{"display": true}}
      }}
    }}
  }},
  "summary": "Comprehensive 2-3 sentence summary with specific numbers and percentages",
  "insights": [
    "Key insight 1 with specific data points",
    "Key insight 2 with actionable information",
    "Key insight 3 highlighting trends or anomalies"
  ],
  "recommendations": [
    "Actionable recommendation based on the data",
    "Strategic suggestion for improvement"
  ]
}}

CHART TYPE SELECTION GUIDE:
- Bar: Comparisons, rankings, categorical data
- Line: Trends over time, sequential data
- Pie/Doughnut: Parts of whole, distributions (≤8 categories)

JSON only - no other text:"""

    def _validate_query_response(self, data: Dict) -> bool:
        """
        Validate Stage 1 response structure and content
        """
        try:
            # Check required fields
            for field in self.required_query_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate pipeline structure
            pipeline = data.get('pipeline', [])
            if not isinstance(pipeline, list) or len(pipeline) == 0:
                logger.warning("Invalid pipeline structure")
                return False
            
            # Validate collection name
            collection = data.get('collection', '')
            if not isinstance(collection, str) or not collection:
                logger.warning("Invalid collection name")
                return False
            
            # Validate chart hint
            valid_charts = ['bar', 'pie', 'line', 'doughnut']
            if data.get('chart_hint') not in valid_charts:
                logger.warning(f"Invalid chart hint: {data.get('chart_hint')}")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Query validation error: {e}")
            return False
    
    def _validate_visualization_response(self, data: Dict) -> bool:
        """
        Validate Stage 2 response structure and content
        """
        try:
            # Check required fields
            for field in self.required_viz_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate chart config structure
            chart_config = data.get('chart_config', {})
            required_config_fields = ['type', 'data', 'options']
            
            for field in required_config_fields:
                if field not in chart_config:
                    logger.warning(f"Missing chart config field: {field}")
                    return False
            
            # Validate data structure
            chart_data = chart_config.get('data', {})
            if 'labels' not in chart_data or 'datasets' not in chart_data:
                logger.warning("Invalid chart data structure")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Visualization validation error: {e}")
            return False
    
    def _create_fallback_query_response(self, user_question: str) -> GeminiResponse:
        """
        Create intelligent fallback for Stage 1 when Gemini fails
        """
        logger.info("🔄 Creating fallback query response")
        
        question_lower = user_question.lower()
        
        # Intelligent pattern matching for fallback
        if any(word in question_lower for word in ['top', 'best', 'highest']):
            fallback_data = {
                "collection": "sales",
                "pipeline": [
                    {"$group": {"_id": "$product_name", "total_revenue": {"$sum": "$total_amount"}}},
                    {"$sort": {"total_revenue": -1}},
                    {"$limit": 10}
                ],
                "chart_hint": "bar",
                "query_intent": "Find top performing items by revenue",
                "expected_fields": ["_id", "total_revenue"],
                "data_summary": "Top performing products by revenue"
            }
        elif 'compare' in question_lower and any(word in question_lower for word in ['smartphone', 'laptop']):
            fallback_data = {
                "collection": "sales",
                "pipeline": [
                    {"$match": {"category": {"$in": ["Smartphones", "Laptops"]}}},
                    {"$group": {"_id": "$category", "total_revenue": {"$sum": "$total_amount"}}},
                    {"$sort": {"total_revenue": -1}}
                ],
                "chart_hint": "bar",
                "query_intent": "Compare smartphone and laptop sales performance",
                "expected_fields": ["_id", "total_revenue"],
                "data_summary": "Revenue comparison between categories"
            }
        else:
            # Generic fallback
            fallback_data = {
                "collection": "sales",
                "pipeline": [
                    {"$group": {"_id": "$category", "total_revenue": {"$sum": "$total_amount"}}},
                    {"$sort": {"total_revenue": -1}},
                    {"$limit": 10}
                ],
                "chart_hint": "bar",
                "query_intent": "General sales analysis by category",
                "expected_fields": ["_id", "total_revenue"],
                "data_summary": "Sales performance by category"
            }
        
        return GeminiResponse(
            success=True,
            data=fallback_data,
            error="Used intelligent fallback - Gemini unavailable",
            stage=QueryStage.QUERY_GENERATION
        )
    
    def _create_fallback_visualization_response(self, user_question: str, 
                                              raw_data: List[Dict]) -> GeminiResponse:
        """
        Create intelligent fallback for Stage 2 when Gemini fails
        """
        logger.info("🔄 Creating fallback visualization response")
        
        if not raw_data:
            fallback_data = {
                "chart_type": "bar",
                "chart_config": {
                    "type": "bar",
                    "data": {"labels": [], "datasets": []},
                    "options": {"responsive": True}
                },
                "summary": "No data found for your query.",
                "insights": ["No data available to analyze"],
                "recommendations": ["Try a different question or check data availability"]
            }
        else:
            # Create basic visualization from data
            labels = [str(item.get('_id', 'Unknown')) for item in raw_data[:10]]
            values = [float(item.get('total_revenue', item.get('total', 0))) for item in raw_data[:10]]
            
            fallback_data = {
                "chart_type": "bar",
                "chart_config": {
                    "type": "bar",
                    "data": {
                        "labels": labels,
                        "datasets": [{
                            "label": "Values",
                            "data": values,
                            "backgroundColor": "rgba(59, 130, 246, 0.8)",
                            "borderColor": "rgba(59, 130, 246, 1)",
                            "borderWidth": 2
                        }]
                    },
                    "options": {
                        "responsive": True,
                        "plugins": {
                            "title": {"display": True, "text": "Analysis Results"},
                            "legend": {"display": False}
                        },
                        "scales": {
                            "y": {"beginAtZero": True},
                            "x": {"display": True}
                        }
                    }
                },
                "summary": f"Found {len(raw_data)} results for your query. Analysis shows data across {len(labels)} categories with values ranging from {min(values):.2f} to {max(values):.2f}.",
                "insights": [
                    f"Total of {len(raw_data)} records analyzed",
                    f"Highest value: {max(values):.2f}" if values else "No numeric data available",
                    "Fallback visualization generated due to AI unavailability"
                ],
                "recommendations": ["Enable full AI features for enhanced analysis"]
            }
        
        return GeminiResponse(
            success=True,
            data=fallback_data,
            error="Used intelligent fallback - Gemini unavailable",
            stage=QueryStage.VISUALIZATION
        )