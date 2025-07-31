import google.generativeai as genai
import json
import time
import logging
import asyncio
import re
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
    Optimized for GenAI operations and document intelligence domain
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
        
        # Test connection
        try:
            test_response = self.model.generate_content("Test connection")
            self.available = True
            logger.info("✅ Enhanced Gemini client initialized and tested")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
        
    async def generate_query_with_retry(self, user_question: str, schema_info: Dict, 
                                      max_retries: int = 5) -> GeminiResponse:
        """
        Stage 1: Generate MongoDB query with bulletproof retry logic
        Enhanced for GenAI operations domain
        """
        if not self.available:
            return GeminiResponse(
                success=False, 
                data={}, 
                error="Gemini client not available",
                stage=QueryStage.QUERY_GENERATION
            )
        
        prompt = self._build_query_prompt(user_question, schema_info)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Gemini Stage 1 - Query Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.query_config
                )
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Extract and validate JSON
                query_data = self._extract_json_from_response(response.text)
                
                if not query_data:
                    raise ValueError("Could not extract valid JSON from response")
                
                # Validate response structure
                if not self._validate_query_response(query_data):
                    raise ValueError("Response missing required fields")
                
                logger.info("✅ Successfully generated query")
                return GeminiResponse(
                    success=True,
                    data=query_data,
                    attempts=attempt + 1,
                    stage=QueryStage.QUERY_GENERATION
                )
                
            except Exception as e:
                logger.warning(f"Query generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:
                    logger.error("All query generation attempts failed")
                    return GeminiResponse(
                        success=False,
                        data={},
                        error=f"Query generation failed after {max_retries} attempts: {str(e)}",
                        attempts=max_retries,
                        stage=QueryStage.QUERY_GENERATION
                    )
                
                # Wait with exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    async def generate_visualization_with_retry(self, user_question: str, raw_data: List[Dict], 
                                              query_context: Dict, max_retries: int = 4) -> GeminiResponse:
        """
        Stage 2: Generate visualization with bulletproof retry logic
        Enhanced for GenAI operations insights
        """
        if not self.available:
            return GeminiResponse(
                success=False,
                data={},
                error="Gemini client not available",
                stage=QueryStage.VISUALIZATION
            )
        
        prompt = self._build_visualization_prompt(user_question, raw_data, query_context)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🧠 Gemini Stage 2 - Visualization Generation (attempt {attempt + 1})")
                
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.viz_config
                )
                
                if not response.text:
                    raise ValueError("Empty response from Gemini")
                
                # Extract and validate JSON
                viz_data = self._extract_json_from_response(response.text)
                
                if not viz_data:
                    raise ValueError("Could not extract valid JSON from response")
                
                # Validate response structure
                if not self._validate_visualization_response(viz_data):
                    raise ValueError("Response missing required fields")
                
                # CRITICAL: Override chart type if intent detection says table but Gemini returned something else
                force_table = self._detect_table_intent(user_question)
                if force_table and viz_data.get('chart_type') != 'table':
                    logger.warning(f"🚨 OVERRIDING: Gemini returned {viz_data.get('chart_type')} but table was required")
                    viz_data = self._force_table_format(viz_data, raw_data, user_question)
                
                logger.info("✅ Successfully generated visualization")
                return GeminiResponse(
                    success=True,
                    data=viz_data,
                    attempts=attempt + 1,
                    stage=QueryStage.VISUALIZATION
                )
                
            except Exception as e:
                logger.warning(f"Visualization generation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries - 1:
                    logger.error("All visualization generation attempts failed")
                    return GeminiResponse(
                        success=False,
                        data={},
                        error=f"Visualization generation failed after {max_retries} attempts: {str(e)}",
                        attempts=max_retries,
                        stage=QueryStage.VISUALIZATION
                    )
                
                # Wait with exponential backoff
                await asyncio.sleep(1.5 ** attempt)
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """
        Bulletproof JSON extraction with multiple fallback methods
        """
        if not response_text:
            return None
        
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Method 1: Try direct JSON parsing
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Remove markdown code blocks
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
            # Fix single quotes to double quotes for keys
            fixed_text = re.sub(r"'([^']*)':", r'"\1":', fixed_text)
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        logger.error(f"Failed to extract JSON from response: {cleaned_text[:200]}...")
        return None
    
    def _build_query_prompt(self, user_question: str, schema_info: Dict) -> str:
        """
        Build enhanced prompt for Stage 1 - Query Generation
        Optimized for GenAI operations and document intelligence domain
        """
        return f"""You are an expert MongoDB query architect specializing in AI operations and document intelligence systems.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Use exact field names from schema
3. Create efficient aggregation pipelines with proper sorting and limits
4. Consider data relationships and business context

DOMAIN: AI Operations & Document Intelligence
- Focus on AI costs, document processing, compliance tracking, agent performance

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

GENAI DOMAIN EXAMPLES:

For "What's our AI spending this month?":
{{
  "collection": "costevalutionforllm",
  "pipeline": [
    {{"$match": {{"timestamp": {{"$gte": "2025-07-01T00:00:00.000Z"}}}}}},
    {{"$group": {{"_id": "$modelType", "total_cost": {{"$sum": "$totalCost"}}, "total_tokens": {{"$sum": {{"$add": ["$inputTokens", "$outputTokens"]}}}}}}}},
    {{"$sort": {{"total_cost": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "bar",
  "query_intent": "Analyze AI spending by model type for current month",
  "expected_fields": ["_id", "total_cost", "total_tokens"],
  "data_summary": "Cost and token usage totals for each AI model"
}}

For "Show me document extraction confidence scores":
{{
  "collection": "documentextractions",
  "pipeline": [
    {{"$group": {{"_id": "$Type", "avg_confidence": {{"$avg": "$Confidence_Score"}}, "count": {{"$sum": 1}}}}}},
    {{"$sort": {{"avg_confidence": -1}}}},
    {{"$limit": 15}}
  ],
  "chart_hint": "bar",
  "query_intent": "Analyze extraction confidence by document type",
  "expected_fields": ["_id", "avg_confidence", "count"],
  "data_summary": "Average confidence scores and counts by extraction type"
}}

For "Which compliance obligations need attention?":
{{
  "collection": "obligationextractions",
  "pipeline": [
    {{"$group": {{"_id": "$name", "count": {{"$sum": 1}}}}}},
    {{"$sort": {{"count": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "pie",
  "query_intent": "Show distribution of compliance obligations",
  "expected_fields": ["_id", "count"],
  "data_summary": "Count of each obligation type for priority assessment"
}}

For "How are our AI agents performing?":
{{
  "collection": "agent_activity",
  "pipeline": [
    {{"$group": {{"_id": "$Agent", "success_rate": {{"$avg": {{"$cond": [{{"$eq": ["$Outcome", "Success"]}}, 1, 0]}}}}, "total_activities": {{"$sum": 1}}}}}},
    {{"$sort": {{"success_rate": -1}}}}
  ],
  "chart_hint": "bar",
  "query_intent": "Analyze agent performance by success rate",
  "expected_fields": ["_id", "success_rate", "total_activities"],
  "data_summary": "Success rates and activity counts for each agent"
}}

CHART TYPE SELECTION:
- table: "show all", "list all", raw data display, detailed records (MANDATORY for listing queries)
- bar: comparisons, rankings, performance metrics
- pie/doughnut: distributions, percentages, breakdowns (≤8 categories)  
- line: trends over time, sequential data, cost tracking

JSON only - no other text:"""

    def _detect_table_intent(self, user_question: str) -> bool:
        """
        Detect if user wants a table visualization based on keywords
        Critical for intent recognition accuracy
        """
        question_lower = user_question.lower().strip()
        
        # Definitive table keywords - highest priority
        table_keywords = [
            "show me all", "list all", "display all", "get all",
            "show all", "list me all", "display me all",
            "in a table", "as a table", "table format",
            "raw data", "details", "records", "entries"
        ]
        
        for keyword in table_keywords:
            if keyword in question_lower:
                logger.info(f"🎯 Table intent detected: '{keyword}' found in '{user_question}'")
                return True
        
        return False
    
    def _force_table_format(self, viz_data: Dict, raw_data: List[Dict], user_question: str) -> Dict:
        """
        Force conversion to table format when Gemini ignores intent
        This is the bulletproof fallback that ensures table queries get tables
        """
        logger.info("🔧 Converting to table format due to intent mismatch")
        
        # Create table data from raw_data
        if not raw_data:
            table_data = []
            columns = []
        else:
            # Use first few records for table
            table_data = raw_data[:50]  # Limit to 50 records for performance
            
            # Auto-generate columns from first record
            if table_data:
                first_record = table_data[0]
                columns = []
                for field, value in first_record.items():
                    # Determine field type
                    field_type = "string"
                    if isinstance(value, (int, float)):
                        field_type = "number"
                    elif isinstance(value, bool):
                        field_type = "boolean"
                    elif field.lower() in ['date', 'timestamp', 'createdat', 'updatedat']:
                        field_type = "date"
                    
                    # Clean field name for display
                    display_name = str(field).replace('_', ' ').title()
                    
                    columns.append({
                        "field": field,
                        "header": display_name,
                        "type": field_type
                    })
        
        # Create new table-format response
        forced_response = {
            "chart_type": "table",
            "chart_config": {
                "type": "table",
                "tableData": table_data,
                "columns": columns
            },
            "summary": f"Table showing {len(table_data)} records as requested by user query: '{user_question}'",
            "insights": viz_data.get('insights', [f"Displaying {len(table_data)} records in table format"]),
            "recommendations": viz_data.get('recommendations', ["Review individual records for detailed analysis"])
        }
        
        return forced_response
    
    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], 
                                  query_context: Dict) -> str:
        """
        Build enhanced prompt for Stage 2 - Visualization Generation
        Optimized for GenAI operations insights and business intelligence
        """
        # Sample the data for context (limit to 5 records for prompt efficiency)
        sample_data = raw_data[:5] if raw_data else []
        
        # Detect if user wants table format
        force_table = self._detect_table_intent(user_question)
        table_instruction = ""
        
        if force_table:
            table_instruction = """
🚨 CRITICAL OVERRIDE: USER WANTS TABLE FORMAT - SET chart_type = "table" MANDATORY
This query contains table-intent keywords. You MUST return chart_type as "table", not bar/pie/line.
"""
        
        return f"""You are a data visualization expert specializing in AI operations and business intelligence.
{table_instruction}

DOMAIN: AI Operations & Document Intelligence
- Focus on actionable insights for cost optimization, performance improvement, compliance management

USER QUESTION: "{user_question}"
QUERY CONTEXT: {json.dumps(query_context, indent=2)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Choose optimal chart type for the data pattern and business context
3. Create meaningful summaries with specific insights and actionable recommendations
4. Include complete Chart.js configuration ready for rendering
5. Focus on business value and operational improvements

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut|table",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["Model A", "Model B"],
      "datasets": [{{
        "label": "AI Costs ($)",
        "data": [1247.50, 892.30],
        "backgroundColor": ["#3B82F6", "#EF4444", "#10B981", "#F59E0B"],
        "borderColor": "#1E40AF",
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "AI Operations Analysis"}},
        "legend": {{"display": true}}
      }},
      "scales": {{
        "y": {{"beginAtZero": true, "title": {{"display": true, "text": "Cost ($)"}}}},
        "x": {{"title": {{"display": true, "text": "AI Models"}}}}
      }}
    }}
  }},
  "summary": "Comprehensive 2-3 sentence summary with specific numbers, percentages, and business impact",
  "insights": [
    "Key insight 1 with specific data points and operational significance",
    "Key insight 2 with actionable information for decision making",
    "Key insight 3 highlighting trends, anomalies, or optimization opportunities"
  ],
  "recommendations": [
    "Actionable recommendation for cost optimization or performance improvement", 
    "Strategic suggestion based on the data patterns observed"
  ]
}}

FOR TABLE FORMAT (when chart_type = "table"):
{{
  "chart_type": "table",
  "chart_config": {{
    "type": "table",
    "tableData": [
      {{"Name": "Prompt 1", "Type": "Document", "Created": "2025-07-15", "Usage": 42}},
      {{"Name": "Prompt 2", "Type": "Legal", "Created": "2025-07-14", "Usage": 28}}
    ],
    "columns": [
      {{"field": "Name", "header": "Prompt Name", "type": "string"}},
      {{"field": "Type", "header": "Type", "type": "string"}},
      {{"field": "Created", "header": "Created Date", "type": "date"}},
      {{"field": "Usage", "header": "Usage Count", "type": "number"}}
    ]
  }},
  "summary": "Table showing detailed records with all relevant fields",
  "insights": ["Data insights about the records shown"],
  "recommendations": ["Actions based on the detailed data"]
}}

GENAI DOMAIN CONTEXT:
- AI Cost Analysis: Focus on ROI, cost per token, model efficiency
- Document Processing: Emphasize accuracy, confidence, processing speed
- Compliance: Highlight risk levels, obligation priorities, coverage gaps
- Agent Performance: Show success rates, throughput, reliability metrics
- Operational: Identify bottlenecks, optimization opportunities, system health

CHART TYPE SELECTION GUIDE:
- Bar: Best for comparisons, rankings, performance metrics, cost analysis
- Line: Ideal for trends over time, cost tracking, performance monitoring
- Pie/Doughnut: Perfect for distributions, breakdowns, resource allocation (≤8 categories)

COLOR SCHEME: Use professional colors that convey business intelligence:
- Blues (#3B82F6, #1E40AF) for primary metrics
- Greens (#10B981, #059669) for positive performance/success
- Reds (#EF4444, #DC2626) for issues/high costs/failures
- Oranges (#F59E0B, #D97706) for warnings/medium priority
- Purples (#8B5CF6, #7C3AED) for special categories

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
            
            # Validate insights and recommendations
            insights = data.get('insights', [])
            recommendations = data.get('recommendations', [])
            
            if not isinstance(insights, list) or len(insights) == 0:
                logger.warning("Missing or invalid insights")
                return False
            
            if not isinstance(recommendations, list):
                logger.warning("Invalid recommendations format")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Visualization validation error: {e}")
            return False

    # Legacy compatibility methods for existing code
    async def generate_query(self, user_question: str, schema_info: Dict, 
                           context: Dict = None) -> Dict:
        """Legacy compatibility method for generate_query"""
        response = await self.generate_query_with_retry(user_question, schema_info)
        
        if response.success:
            return {
                "success": True,
                "query_data": response.data,
                "attempts": response.attempts
            }
        else:
            return {
                "success": False,
                "error": response.error,
                "attempts": response.attempts
            }
    
    async def generate_insights(self, user_question: str, query_data: Dict, 
                              raw_results: List[Dict], context: Dict = None) -> Dict:
        """Legacy compatibility method for generate_insights"""
        response = await self.generate_visualization_with_retry(
            user_question, raw_results, query_data
        )
        
        if response.success:
            return {
                "success": True,
                "visualization": response.data,
                "attempts": response.attempts
            }
        else:
            return {
                "success": False,
                "error": response.error,
                "attempts": response.attempts
            }

# Factory function for creating the client
def create_gemini_client(api_key: str) -> BulletproofGeminiClient:
    """Factory function to create a BulletproofGeminiClient instance"""
    return BulletproofGeminiClient(api_key)

# Utility function for testing the client
async def test_gemini_client(api_key: str) -> bool:
    """Test if the Gemini client can be initialized and is working"""
    try:
        client = BulletproofGeminiClient(api_key)
        return client.available
    except Exception as e:
        logger.error(f"Failed to test Gemini client: {e}")
        return False