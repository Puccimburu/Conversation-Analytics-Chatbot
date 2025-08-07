# backend/utils/workflow_nodes.py
"""
LangGraph Workflow Nodes for Analytics Processing
Individual processing nodes that can be composed into complex workflows
"""

import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsState:
    """
    State definition for analytics workflows
    Matches the TypedDict structure but as a dataclass for easier handling
    """
    # Input
    original_question: str
    user_id: str = "default_user"
    chat_id: str = ""
    
    # Processing pipeline
    interpreted_intent: Optional[Dict] = None
    mongo_query: Optional[Dict] = None
    chart_config: Optional[Dict] = None
    raw_data: Optional[List] = None
    formatted_response: Optional[Dict] = None
    
    # Workflow control
    current_step: str = "start"
    retry_count: int = 0
    errors: List[str] = None
    
    # Output
    success: bool = False
    final_result: Optional[Dict] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class AnalyticsWorkflowNodes:
    """
    Collection of workflow nodes for analytics processing
    Each node is a standalone function that can be composed into workflows
    """
    
    def __init__(self, gemini_client, mongodb_client, schema_info):
        """
        Initialize workflow nodes with necessary clients
        
        Args:
            gemini_client: Your existing enhanced Gemini client
            mongodb_client: MongoDB database client
            schema_info: Database schema information from config.py
        """
        self.gemini_client = gemini_client
        self.db = mongodb_client
        self.schema_info = schema_info
    
    async def understand_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 1: Analyze user question to understand intent and data requirements
        
        This node determines:
        - What type of analysis is requested (cost, document, compliance, etc.)
        - What data collections are needed
        - What time periods or filters might be required
        - What visualization might be appropriate
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with interpreted_intent
        """
        try:
            state["current_step"] = "understanding_intent"
            logger.info(f"🧠 Understanding intent for: '{state['original_question']}'")
            
            # Enhanced prompt for intent understanding
            intent_prompt = f"""
            Analyze this analytics question and determine the user's intent:
            
            Question: "{state['original_question']}"
            
            Available collections: {list(self.schema_info.get('collections', {}).keys())}
            
            Determine:
            1. Primary intent (cost_analysis, document_processing, compliance_review, user_management, performance_analysis)
            2. Required collections (which MongoDB collections are needed)
            3. Time sensitivity (does this need recent data, historical trends, or specific time periods)
            4. Complexity level (simple_query, multi_step_analysis, comparative_analysis)
            5. Expected output (single_metric, trend_analysis, comparative_chart, detailed_breakdown)
            
            Respond with JSON:
            {{
                "primary_intent": "string",
                "required_collections": ["collection1", "collection2"],
                "time_sensitivity": "string",
                "complexity_level": "string",
                "expected_output": "string",
                "key_entities": ["entity1", "entity2"],
                "suggested_chart_type": "bar|line|pie|table"
            }}
            """
            
            # Use your existing Gemini client
            if hasattr(self.gemini_client, 'generate_content_async'):
                response = await self.gemini_client.generate_content_async(intent_prompt)
            else:
                response = self.gemini_client.generate_content(intent_prompt)
            
            # Parse the response
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Extract JSON from response
            try:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    intent_data = json.loads(json_match.group())
                else:
                    # Fallback: create intent based on keywords
                    intent_data = self._fallback_intent_analysis(state['original_question'])
            except json.JSONDecodeError:
                intent_data = self._fallback_intent_analysis(state['original_question'])
            
            state["interpreted_intent"] = intent_data
            state["current_step"] = "intent_understood"
            
            logger.info(f"✅ Intent understood: {intent_data.get('primary_intent')}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Intent understanding failed: {e}")
            state["errors"].append(f"Intent understanding failed: {str(e)}")
            state["current_step"] = "intent_failed"
            return state
    
    def _fallback_intent_analysis(self, question: str) -> Dict[str, Any]:
        """Fallback intent analysis using keyword matching"""
        question_lower = question.lower()
        
        # Determine primary intent
        if any(word in question_lower for word in ['cost', 'spending', 'expense', 'price']):
            primary_intent = "cost_analysis"
            required_collections = ["costevalutionforllm", "llmpricing"]
        elif any(word in question_lower for word in ['document', 'extraction', 'processing']):
            primary_intent = "document_processing"
            required_collections = ["documentextractions", "files", "batches"]
        elif any(word in question_lower for word in ['compliance', 'obligation', 'requirement']):
            primary_intent = "compliance_review"
            required_collections = ["obligationextractions", "obligationmappings", "compliances"]
        elif any(word in question_lower for word in ['user', 'role', 'access']):
            primary_intent = "user_management"
            required_collections = ["users", "allowedusers"]
        else:
            primary_intent = "performance_analysis"
            required_collections = ["agent_activity"]
        
        return {
            "primary_intent": primary_intent,
            "required_collections": required_collections,
            "time_sensitivity": "recent",
            "complexity_level": "simple_query",
            "expected_output": "trend_analysis",
            "key_entities": [],
            "suggested_chart_type": "bar"
        }
    
    async def generate_mongo_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 2: Generate MongoDB aggregation pipeline based on intent
        
        Uses the interpreted intent to create an optimized MongoDB query
        that will retrieve the necessary data for analysis.
        
        Args:
            state: Current workflow state with interpreted_intent
            
        Returns:
            Updated state with mongo_query
        """
        try:
            state["current_step"] = "generating_query"
            intent = state.get("interpreted_intent", {})
            
            logger.info(f"🔍 Generating MongoDB query for {intent.get('primary_intent')}")
            
            # Use your existing enhanced Gemini client for query generation
            query_prompt = f"""
            Generate MongoDB aggregation pipeline for this analytics request:
            
            Original Question: "{state['original_question']}"
            Intent: {intent.get('primary_intent')}
            Required Collections: {intent.get('required_collections', [])}
            Expected Output: {intent.get('expected_output')}
            
            Available Collections Schema:
            {json.dumps(self.schema_info.get('collections', {}), indent=2)}
            
            Generate an optimized MongoDB aggregation pipeline that:
            1. Uses the most appropriate collection from: {intent.get('required_collections', [])}
            2. Includes proper filtering and grouping
            3. Limits results to avoid overwhelming responses
            4. Includes relevant sorting
            
            Respond with JSON:
            {{
                "collection": "collection_name",
                "pipeline": [
                    {{"$match": {{}}}},
                    {{"$group": {{}}}},
                    {{"$sort": {{}}}},
                    {{"$limit": 50}}
                ]
            }}
            """
            
            # Generate query using existing client
            if hasattr(self.gemini_client, 'generate_content_async'):
                response = await self.gemini_client.generate_content_async(query_prompt)
            else:
                response = self.gemini_client.generate_content(query_prompt)
            
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Parse MongoDB query from response
            try:
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    query_data = json.loads(json_match.group())
                else:
                    # Fallback query generation
                    query_data = self._fallback_query_generation(intent)
            except json.JSONDecodeError:
                query_data = self._fallback_query_generation(intent)
            
            state["mongo_query"] = query_data
            state["current_step"] = "query_generated"
            
            logger.info(f"✅ Query generated for collection: {query_data.get('collection')}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Query generation failed: {e}")
            state["errors"].append(f"Query generation failed: {str(e)}")
            state["retry_count"] += 1
            state["current_step"] = "query_failed"
            return state
    
    def _fallback_query_generation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback MongoDB query based on intent"""
        collections = intent.get('required_collections', ['users'])
        primary_collection = collections[0] if collections else 'users'
        
        # Simple fallback queries for different intents
        if intent.get('primary_intent') == 'cost_analysis':
            return {
                "collection": "costevalutionforllm",
                "pipeline": [
                    {"$limit": 50},
                    {"$sort": {"totalCostInUSD": -1}}
                ]
            }
        elif intent.get('primary_intent') == 'user_management':
            return {
                "collection": "users",
                "pipeline": [
                    {"$limit": 50},
                    {"$sort": {"createdAt": -1}}
                ]
            }
        else:
            return {
                "collection": primary_collection,
                "pipeline": [
                    {"$limit": 50}
                ]
            }
    
    async def execute_data_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 3: Execute the MongoDB query and retrieve data
        
        Executes the generated query against your MongoDB collections
        and handles any database-level errors or optimizations.
        
        Args:
            state: Current workflow state with mongo_query
            
        Returns:
            Updated state with raw_data
        """
        try:
            state["current_step"] = "executing_query"
            query_data = state.get("mongo_query", {})
            
            if not query_data:
                raise ValueError("No MongoDB query available for execution")
            
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            logger.info(f"💾 Executing query on collection: {collection_name}")
            
            if self.db is None:
                raise ValueError("Database connection not available")
            
            # Execute the aggregation pipeline
            collection = self.db[collection_name]
            
            # Convert any string dates to datetime objects if needed
            processed_pipeline = self._process_pipeline_dates(pipeline)
            
            # Execute query
            cursor = collection.aggregate(processed_pipeline)
            raw_results = list(cursor)
            
            # Clean results for JSON serialization
            cleaned_results = []
            for result in raw_results:
                cleaned_result = self._clean_mongodb_result(result)
                cleaned_results.append(cleaned_result)
            
            state["raw_data"] = cleaned_results
            state["current_step"] = "data_retrieved"
            
            logger.info(f"✅ Retrieved {len(cleaned_results)} records from {collection_name}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Data query execution failed: {e}")
            state["errors"].append(f"Database query failed: {str(e)}")
            state["retry_count"] += 1
            state["current_step"] = "query_execution_failed"
            return state
    
    def _process_pipeline_dates(self, pipeline: List[Dict]) -> List[Dict]:
        """Process pipeline to handle date conversions"""
        # Reuse your existing date processing logic from perfected_processor.py
        from datetime import datetime
        import re
        
        def convert_dates_recursive(obj):
            if isinstance(obj, dict):
                return {key: convert_dates_recursive(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_dates_recursive(item) for item in obj]
            elif isinstance(obj, str):
                if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', obj):
                    try:
                        return datetime.fromisoformat(obj.replace('Z', '+00:00'))
                    except ValueError:
                        return obj
                return obj
            else:
                return obj
        
        return convert_dates_recursive(pipeline)
    
    def _clean_mongodb_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean MongoDB result for JSON serialization"""
        from bson import ObjectId
        import math
        
        cleaned = {}
        for key, value in result.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_mongodb_result(value)
            elif isinstance(value, float) and math.isnan(value):
                cleaned[key] = None
            else:
                cleaned[key] = value
        
        return cleaned
    
    async def plan_visualization(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 4: Determine best chart type and formatting for the data
        
        Analyzes the retrieved data and the original intent to determine
        the most appropriate visualization approach.
        
        Args:
            state: Current workflow state with raw_data
            
        Returns:
            Updated state with chart_config
        """
        try:
            state["current_step"] = "planning_visualization"
            raw_data = state.get("raw_data", [])
            intent = state.get("interpreted_intent", {})
            
            if not raw_data:
                logger.warning("No data available for visualization planning")
                state["chart_config"] = {"type": "table", "message": "No data found"}
                state["current_step"] = "visualization_planned"
                return state
            
            logger.info(f"📊 Planning visualization for {len(raw_data)} records")
            
            # Analyze data structure
            sample_record = raw_data[0] if raw_data else {}
            data_fields = list(sample_record.keys())
            
            # Determine best chart type based on intent and data structure
            suggested_chart = intent.get('suggested_chart_type', 'bar')
            
            # Smart chart type selection based on data
            if len(data_fields) == 2:
                # Two fields - good for bar charts or pie charts
                chart_type = "bar" if any(field in ['count', 'total', 'sum'] for field in data_fields) else "pie"
            elif any(field in ['date', 'time', 'createdAt', 'updatedAt'] for field in data_fields):
                # Time-based data - line chart
                chart_type = "line"
            elif len(raw_data) > 20:
                # Large datasets - table view
                chart_type = "table"
            else:
                # Default to suggested type
                chart_type = suggested_chart
            
            # Create chart configuration
            chart_config = {
                "type": chart_type,
                "data": raw_data,
                "labels": self._extract_labels(raw_data),
                "values": self._extract_values(raw_data),
                "title": f"Analytics: {state['original_question'][:50]}...",
                "fields": data_fields,
                "total_records": len(raw_data)
            }
            
            state["chart_config"] = chart_config
            state["current_step"] = "visualization_planned"
            
            logger.info(f"✅ Planned {chart_type} visualization with {len(raw_data)} data points")
            return state
            
        except Exception as e:
            logger.error(f"❌ Visualization planning failed: {e}")
            state["errors"].append(f"Visualization planning failed: {str(e)}")
            state["current_step"] = "visualization_failed"
            return state
    
    def _extract_labels(self, data: List[Dict]) -> List[str]:
        """Extract labels for chart visualization"""
        if not data:
            return []
        
        # Find the most likely label field
        sample = data[0]
        label_candidates = ['name', 'label', '_id', 'id', 'type', 'category']
        
        for candidate in label_candidates:
            if candidate in sample:
                return [str(record.get(candidate, 'Unknown')) for record in data]
        
        # Fallback to first field
        first_field = list(sample.keys())[0] if sample else 'unknown'
        return [str(record.get(first_field, 'Unknown')) for record in data]
    
    def _extract_values(self, data: List[Dict]) -> List[Any]:
        """Extract values for chart visualization"""
        if not data:
            return []
        
        # Find the most likely value field
        sample = data[0]
        value_candidates = ['value', 'count', 'total', 'amount', 'sum', 'avg', 'score']
        
        for candidate in value_candidates:
            if candidate in sample and isinstance(sample[candidate], (int, float)):
                return [record.get(candidate, 0) for record in data]
        
        # Fallback to first numeric field
        for field, value in sample.items():
            if isinstance(value, (int, float)):
                return [record.get(field, 0) for record in data]
        
        # Final fallback - count occurrences
        return [1] * len(data)
    
    async def format_final_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Node 5: Format the final response for the frontend
        
        Combines all processed data into a response format that matches
        your existing API expectations.
        
        Args:
            state: Current workflow state with all processing complete
            
        Returns:
            Updated state with final_result and success=True
        """
        try:
            state["current_step"] = "formatting_response"
            
            chart_config = state.get("chart_config", {})
            raw_data = state.get("raw_data", [])
            intent = state.get("interpreted_intent", {})
            
            # Generate insights and recommendations
            insights = self._generate_insights(raw_data, intent)
            recommendations = self._generate_recommendations(raw_data, intent)
            
            # Format final response matching your existing API structure
            final_response = {
                "success": True,
                "summary": f"Analytics completed for: {state['original_question']}",
                "chart_data": chart_config,
                "insights": insights,
                "recommendations": recommendations,
                "results_count": len(raw_data),
                "query_source": "langgraph_workflow",
                "ai_powered": True,
                "workflow_enhanced": True,
                
                # LangGraph-specific metadata
                "workflow_metadata": {
                    "thread_id": state.get("thread_id"),
                    "steps_completed": state["current_step"],
                    "retry_count": state.get("retry_count", 0),
                    "processing_time": (datetime.now() - state.get("start_time", datetime.now())).total_seconds() if state.get("start_time") else 0,
                    "intent_detected": intent.get("primary_intent"),
                    "collections_used": [state.get("mongo_query", {}).get("collection")]
                }
            }
            
            state["final_result"] = final_response
            state["success"] = True
            state["current_step"] = "completed"
            
            logger.info(f"✅ Response formatted successfully for {state['original_question']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Response formatting failed: {e}")
            state["errors"].append(f"Response formatting failed: {str(e)}")
            state["current_step"] = "formatting_failed"
            return state
    
    def _generate_insights(self, data: List[Dict], intent: Dict) -> List[str]:
        """Generate insights based on the data and intent"""
        if not data:
            return ["No data available for analysis"]
        
        insights = []
        data_count = len(data)
        
        # Generic insights
        insights.append(f"Found {data_count} records matching your query")
        
        # Intent-specific insights
        primary_intent = intent.get("primary_intent", "")
        
        if primary_intent == "cost_analysis":
            # Analyze costs
            cost_fields = ['totalCostInUSD', 'cost', 'amount']
            for field in cost_fields:
                if field in (data[0] if data else {}):
                    total_cost = sum(float(record.get(field, 0)) for record in data)
                    avg_cost = total_cost / data_count if data_count > 0 else 0
                    insights.append(f"Total cost: ${total_cost:.2f}, Average: ${avg_cost:.2f}")
                    break
        
        elif primary_intent == "user_management":
            # Analyze users
            roles = set(record.get('role', 'Unknown') for record in data)
            insights.append(f"Found users with roles: {', '.join(roles)}")
        
        elif primary_intent == "document_processing":
            # Analyze document processing
            if 'status' in (data[0] if data else {}):
                statuses = {}
                for record in data:
                    status = record.get('status', 'Unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                insights.append(f"Document statuses: {dict(statuses)}")
        
        # Add more insights based on data patterns
        if data_count > 10:
            insights.append("Large dataset detected - consider filtering for better performance")
        
        return insights[:5]  # Limit to 5 insights
    
    def _generate_recommendations(self, data: List[Dict], intent: Dict) -> List[str]:
        """Generate recommendations based on the analysis"""
        if not data:
            return ["Try a different query or check data availability"]
        
        recommendations = []
        primary_intent = intent.get("primary_intent", "")
        
        if primary_intent == "cost_analysis":
            recommendations.extend([
                "Monitor high-cost operations for optimization opportunities",
                "Consider setting up cost alerts for budget management",
                "Analyze cost trends over time to identify patterns"
            ])
        
        elif primary_intent == "user_management":
            recommendations.extend([
                "Review user access permissions regularly",
                "Consider role-based access control optimization",
                "Monitor user activity for security purposes"
            ])
        
        elif primary_intent == "document_processing":
            recommendations.extend([
                "Focus on improving low-confidence extractions",
                "Consider batch processing for efficiency",
                "Monitor processing success rates regularly"
            ])
        
        # Generic recommendations
        recommendations.append("Use filters to narrow down results for specific insights")
        recommendations.append("Consider exporting data for detailed offline analysis")
        
        return recommendations[:5]  # Limit to 5 recommendations

    async def handle_error_recovery(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Error recovery node that attempts to fix common issues
        
        Args:
            state: Current workflow state with errors
            
        Returns:
            Updated state with recovery attempt
        """
        try:
            state["current_step"] = "recovering_from_error"
            errors = state.get("errors", [])
            retry_count = state.get("retry_count", 0)
            
            logger.info(f"🔄 Attempting error recovery (attempt {retry_count + 1})")
            
            if retry_count >= 3:
                # Max retries reached, format error response
                state["final_result"] = {
                    "success": False,
                    "error": "Maximum retries exceeded",
                    "errors": errors,
                    "summary": f"Unable to process query: {state['original_question']}",
                    "suggestions": [
                        "Try simplifying your question",
                        "Check if the requested data exists",
                        "Use more specific terms in your query"
                    ]
                }
                state["success"] = False
                state["current_step"] = "error_final"
                return state
            
            # Attempt to recover based on error type
            last_error = errors[-1] if errors else ""
            
            if "query generation" in last_error.lower():
                # Reset to intent understanding with modified approach
                state["current_step"] = "recovery_intent"
                state["interpreted_intent"] = None
                
            elif "database query" in last_error.lower():
                # Try with a simpler query
                if state.get("mongo_query"):
                    query = state["mongo_query"]
                    query["pipeline"] = [{"$limit": 10}]  # Simplify to basic query
                state["current_step"] = "recovery_query"
                
            else:
                # Generic recovery - restart from intent
                state["current_step"] = "recovery_restart"
                state["interpreted_intent"] = None
                state["mongo_query"] = None
            
            logger.info(f"🔄 Recovery strategy: {state['current_step']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Error recovery failed: {e}")
            state["errors"].append(f"Recovery failed: {str(e)}")
            state["current_step"] = "recovery_failed"
            return state