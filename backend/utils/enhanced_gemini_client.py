import google.generativeai as genai
import json
import time
import logging
import asyncio
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from config.config import DATABASE_SCHEMA  # Import the GenAI schema

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
        
        # Load GenAI schema dynamically
        self.genai_schema = DATABASE_SCHEMA.copy()
        self.genai_collections = list(self.genai_schema.get('collections', {}).keys())
        
        # Test connection
        try:
            test_response = self.model.generate_content("Test connection")
            self.available = True
            logger.info("✅ Enhanced Gemini client initialized and tested")
            logger.info(f"🎯 Configured for GenAI database with {len(self.genai_collections)} collections")
        except Exception as e:
            logger.error(f"❌ Gemini test failed: {e}")
            self.available = False
        
    async def generate_query_with_retry(self, user_question: str, schema_info: Dict = None, 
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
        
        # Use provided schema or default to GenAI schema
        schema = schema_info or self.genai_schema
        prompt = self._build_query_prompt(user_question, schema)
        
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
                
                logger.info(f"✅ Successfully generated query for collection: {query_data.get('collection')}")
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
                
                logger.info(f"✅ Successfully generated visualization: {viz_data.get('chart_type')}")
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
        # Get collection names from schema - prioritize key GenAI collections
        all_collections = list(schema_info.get('collections', {}).keys())
        
        # Prioritize key GenAI collections for better prompt focus
        priority_collections = [
            'costevalutionforllm', 'documentextractions', 'obligationextractions', 
            'agent_activity', 'files', 'batches', 'users', 'conversations',
            'prompts', 'compliances', 'documentmappings', 'llmpricing'
        ]
        
        # Use priority collections that exist in schema
        available_priority = [col for col in priority_collections if col in all_collections]
        other_collections = [col for col in all_collections if col not in priority_collections]
        
        # Combine for final list (priority first)
        featured_collections = available_priority[:8] + other_collections[:4]
        
        return f"""You are an expert MongoDB query architect specializing in AI operations and document intelligence systems.

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Use exact field names from schema
3. Create efficient aggregation pipelines with proper sorting and limits
4. Consider data relationships and business context for GenAI operations

DOMAIN: AI Operations & Document Intelligence
- Focus on AI costs, document processing, compliance tracking, agent performance
- Analyze operational efficiency, cost optimization, quality metrics

AVAILABLE COLLECTIONS: {', '.join(featured_collections)}

USER QUESTION: "{user_question}"

GENAI COLLECTION PURPOSES:
🤖 AI OPERATIONS & COSTS:
- costevalutionforllm: AI model costs, token usage, pricing analysis (totalCost, inputTokens, outputTokens, modelType)
- llmpricing: LLM model pricing tiers and rates (ratePerMillionInputTokens, ratePerMillionOutputTokens, modelVariant)
- agent_activity: AI agent performance and activity logs (Agent, Outcome, Timestamp)

📄 DOCUMENT PROCESSING:
- files: Document storage, metadata, processing status (filename, status, size, createdAt)
- documentextractions: Extracted content, confidence scores (Type, Confidence_Score, Extraction_Text)
- documenttypes: Document categorization and types
- documentmappings: Document-to-prompt relationships (mappingId, batchId, fileId)
- batches: Batch processing jobs and status (batchId, status, createdAt)

⚖️ COMPLIANCE & LEGAL:
- obligationextractions: Legal obligations extracted from documents (name, Text, Risk_Level)
- obligationmappings: Obligation-to-document relationships (mappingId, obligationIds)
- compliances: Compliance tracking and validation

👥 USER & SYSTEM:
- users: User accounts and profiles (firstName, lastName, email, role, createdAt)
- allowedusers: Access control and permissions
- conversations: Chat sessions and interactions (title, userId, createdAt, updatedAt)

🔄 WORKFLOW MANAGEMENT:
- prompts: AI prompts library and templates (promptName, promptType, promptText)
- langgraph_checkpoints: Workflow state management

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
    {{"$group": {{"_id": "$name", "count": {{"$sum": 1}}, "high_risk": {{"$sum": {{"$cond": [{{"$eq": ["$Risk_Level", "High"]}}, 1, 0]}}}}}}}},
    {{"$sort": {{"high_risk": -1, "count": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_hint": "pie",
  "query_intent": "Show distribution of compliance obligations with risk focus",
  "expected_fields": ["_id", "count", "high_risk"],
  "data_summary": "Count of each obligation type with high-risk indicators"
}}

For "How are our AI agents performing?":
{{
  "collection": "agent_activity",
  "pipeline": [
    {{"$group": {{"_id": "$Agent", "success_rate": {{"$avg": {{"$cond": [{{"$eq": ["$Outcome", "Success"]}}, 1, 0]}}}}, "total_activities": {{"$sum": 1}}}}}},
    {{"$sort": {{"success_rate": -1}}}},
    {{"$limit": 15}}
  ],
  "chart_hint": "bar",
  "query_intent": "Analyze agent performance by success rate",
  "expected_fields": ["_id", "success_rate", "total_activities"],
  "data_summary": "Success rates and activity counts for each agent"
}}

For "Show me user activity patterns":
{{
  "collection": "users",
  "pipeline": [
    {{"$group": {{"_id": "$role", "user_count": {{"$sum": 1}}, "avg_creation_date": {{"$avg": "$createdAt"}}}}}},
    {{"$sort": {{"user_count": -1}}}}
  ],
  "chart_hint": "pie",
  "query_intent": "Analyze user distribution by role",
  "expected_fields": ["_id", "user_count"],
  "data_summary": "Count of users by role for system usage analysis"
}}

CHART TYPE SELECTION:
- bar: comparisons, rankings, performance metrics, cost analysis
- pie/doughnut: distributions, percentages, breakdowns (≤8 categories)
- line: trends over time, sequential data, cost tracking

FIELD NAME ACCURACY:
- Use exact field names from your GenAI database
- Common fields: totalCost, inputTokens, outputTokens, Confidence_Score, Risk_Level, Outcome
- Always check field casing and use exact matches

JSON only - no other text:"""

    def _build_visualization_prompt(self, user_question: str, raw_data: List[Dict], 
                                  query_context: Dict) -> str:
        """
        Build enhanced prompt for Stage 2 - Visualization Generation
        Optimized for GenAI operations insights and business intelligence
        """
        # Sample the data for context (limit to 5 records for prompt efficiency)
        sample_data = raw_data[:5] if raw_data else []
        
        return f"""You are a data visualization expert specializing in AI operations and business intelligence.

DOMAIN: AI Operations & Document Intelligence
- Focus on actionable insights for cost optimization, performance improvement, compliance management
- Emphasize operational efficiency, quality metrics, and business value

USER QUESTION: "{user_question}"
QUERY CONTEXT: {json.dumps(query_context, indent=2)}
SAMPLE DATA: {json.dumps(sample_data, indent=2)}
TOTAL RECORDS: {len(raw_data)}

CRITICAL REQUIREMENTS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Choose optimal chart type for the data pattern and business context
3. Create meaningful summaries with specific insights and actionable recommendations
4. Include complete Chart.js configuration ready for rendering
5. Focus on business value and operational improvements for GenAI systems

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut",
  "chart_config": {{
    "type": "bar",
    "data": {{
      "labels": ["GPT-4", "GPT-3.5", "Gemini"],
      "datasets": [{{
        "label": "AI Costs ($)",
        "data": [1247.50, 892.30, 654.20],
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
  "summary": "Your AI costs total $2,793.00 across 3 models, with GPT-4 representing 45% of spending at $1,247.50 despite processing fewer requests than GPT-3.5.",
  "insights": [
    "GPT-4 generates 40% higher costs per token but delivers 95% confidence scores vs 87% for GPT-3.5",
    "Gemini processes 60% more documents but costs 48% less than GPT-4, indicating strong efficiency",
    "Cost per successful extraction: GPT-4 ($0.12), GPT-3.5 ($0.08), Gemini ($0.05)"
  ],
  "recommendations": [
    "Consider routing routine document processing to Gemini to reduce costs by 58%",
    "Reserve GPT-4 for high-value extractions requiring >90% confidence scores"
  ]
}}

GENAI DOMAIN CONTEXT & INSIGHTS:
- AI Cost Analysis: Focus on ROI, cost per token, model efficiency, operational optimization
- Document Processing: Emphasize accuracy, confidence, processing speed, quality metrics
- Compliance: Highlight risk levels, obligation priorities, coverage gaps, regulatory requirements
- Agent Performance: Show success rates, throughput, reliability metrics, operational health
- User Analytics: Track engagement, productivity, system utilization, workflow efficiency

BUSINESS-FOCUSED SUMMARIES:
- Include specific dollar amounts, percentages, and operational metrics
- Highlight cost savings opportunities and efficiency improvements
- Emphasize business impact and decision-making insights
- Use concrete numbers from the data for credibility

ACTIONABLE INSIGHTS:
- Connect data patterns to operational decisions
- Identify optimization opportunities and bottlenecks
- Suggest specific actions based on the analysis
- Focus on measurable improvements and ROI

CHART TYPE SELECTION GUIDE:
- Bar: Best for comparisons, rankings, performance metrics, cost analysis
- Line: Ideal for trends over time, cost tracking, performance monitoring
- Pie/Doughnut: Perfect for distributions, breakdowns, resource allocation (≤8 categories)

COLOR SCHEME: Use professional colors that convey business intelligence:
- Blues (#3B82F6, #1E40AF) for primary metrics and positive trends
- Greens (#10B981, #059669) for positive performance, success, efficiency
- Reds (#EF4444, #DC2626) for issues, high costs, failures, risks
- Oranges (#F59E0B, #D97706) for warnings, medium priority, attention needed
- Purples (#8B5CF6, #7C3AED) for special categories and advanced features

JSON only - no other text:"""

    def _validate_query_response(self, data: Dict) -> bool:
        """
        Validate Stage 1 response structure and content
        Enhanced for GenAI operations
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
            
            # Validate collection name - ensure it's a valid GenAI collection
            collection = data.get('collection', '')
            if not isinstance(collection, str) or not collection:
                logger.warning("Invalid collection name")
                return False
            
            # Check if collection exists in GenAI schema
            if collection not in self.genai_collections:
                logger.warning(f"Collection '{collection}' not found in GenAI schema")
                # Don't fail validation - might be a valid collection not in our schema
            
            # Validate chart hint
            valid_charts = ['bar', 'pie', 'line', 'doughnut']
            if data.get('chart_hint') not in valid_charts:
                logger.warning(f"Invalid chart hint: {data.get('chart_hint')}")
                return False
            
            logger.info(f"✅ Query validation passed for collection: {collection}")
            return True
            
        except Exception as e:
            logger.warning(f"Query validation error: {e}")
            return False
    
    def _validate_visualization_response(self, data: Dict) -> bool:
        """
        Validate Stage 2 response structure and content
        Enhanced for GenAI operations visualization
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
            
            # Validate datasets
            datasets = chart_data.get('datasets', [])
            if not isinstance(datasets, list) or len(datasets) == 0:
                logger.warning("Missing or invalid datasets")
                return False
            
            # Validate insights and recommendations
            insights = data.get('insights', [])
            if not isinstance(insights, list) or len(insights) == 0:
                logger.warning("Missing or invalid insights")
                return False
            
            # Summary should be substantial
            summary = data.get('summary', '')
            if not isinstance(summary, str) or len(summary) < 20:
                logger.warning("Summary too short or invalid")
                return False
            
            logger.info("✅ Visualization validation passed")
            return True
            
        except Exception as e:
            logger.warning(f"Visualization validation error: {e}")
            return False

    # Legacy compatibility methods for existing code
    async def generate_query(self, user_question: str, schema_info: Dict = None, 
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