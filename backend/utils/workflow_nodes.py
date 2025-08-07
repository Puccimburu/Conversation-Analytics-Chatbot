# backend/utils/workflow_nodes_enhanced.py
"""
Enhanced LangGraph Workflow Nodes with Comprehensive Error Handling
Fixed version that addresses the execution failures seen in test results
"""

import logging
import asyncio
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsState:
    """
    Enhanced state definition for analytics workflows with better validation
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

class EnhancedAnalyticsWorkflowNodes:
    """
    Enhanced workflow nodes with comprehensive error handling and detailed logging
    Fixes the execution failures identified in the test results
    """
    
    def __init__(self, gemini_client, mongodb_client, schema_info):
        """
        Initialize workflow nodes with enhanced error handling
        
        Args:
            gemini_client: Enhanced Gemini client
            mongodb_client: MongoDB database client
            schema_info: Database schema information
        """
        self.gemini_client = gemini_client
        self.db = mongodb_client
        self.schema_info = schema_info
        
        # Validate dependencies
        if not gemini_client:
            logger.warning("⚠️ Gemini client not provided - AI features will be limited")
        if mongodb_client is None:
            logger.warning("⚠️ MongoDB client not provided - data queries will fail")
        
        logger.info("✅ Enhanced workflow nodes initialized")
    
    async def understand_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced intent understanding with detailed error handling and fallbacks
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with interpreted_intent or detailed error info
        """
        try:
            state["current_step"] = "understanding_intent"
            original_question = state.get("original_question", "")
            
            logger.info(f"🧠 Starting intent analysis for: '{original_question}'")
            
            if not original_question:
                raise Exception("No question provided for intent analysis")
            
            # Get available collections with error handling
            try:
                available_collections = list(self.schema_info.get('collections', {}).keys())
                if not available_collections:
                    # Fallback: try to get from database
                    available_collections = self.db.list_collection_names() if self.db else ["users", "documents"]
                
                logger.debug(f"Available collections: {available_collections}")
                
            except Exception as e:
                logger.warning(f"Could not get collections list: {e}")
                available_collections = ["users", "documents", "batches"]  # Safe fallback
            
            # Enhanced prompt for intent understanding
            intent_prompt = f"""
            Analyze this analytics question and determine the user's intent.
            
            Question: "{original_question}"
            
            Available collections: {available_collections}
            
            Respond with ONLY a JSON object in this exact format:
            {{
                "primary_intent": "user_management",
                "target_collection": "users",
                "analysis_type": "list",
                "time_filter": "all",
                "visualization_needed": false,
                "confidence": 0.8,
                "reasoning": "User is asking for a simple list of users"
            }}
            
            Primary intent options: user_management, cost_analysis, document_processing, compliance_review, performance_analysis, general_query
            Analysis type options: list, aggregate, count, trend, comparison
            Time filter options: recent, all, specific_period
            """
            
            # Make Gemini API call with comprehensive error handling
            try:
                logger.debug("Making Gemini API call for intent analysis")
                
                if not self.gemini_client:
                    raise Exception("Gemini client not available")
                
                response = await self.gemini_client.generate_query(original_question, self.schema_info)
                
                if not response or not response.get('success'):
                    raise Exception(f"Gemini API call failed: {response.get('error', 'Unknown error')}")

                # FIX 1: Get data from the 'data' key, not 'content'
                intent_query_data = response.get('data')
                logger.debug(f"Raw Gemini response data: {intent_query_data}")

                if not intent_query_data:
                    raise Exception("Empty 'data' field from Gemini API response")

                # FIX 2: The data is already a dictionary. No need for json.loads.
                # **CRITICAL STEP**: Adapt the query output to the intent structure.
                adapted_intent = {
                    "primary_intent": intent_query_data.get("intent", "general_query"),
                    "target_collection": intent_query_data.get("collection"),
                    "analysis_type": "custom_query",  # Special flag for the next node
                    "custom_pipeline": intent_query_data.get("pipeline"),  # The generated query
                    "confidence": 0.95,
                    "reasoning": "Intent adapted from an AI-generated MongoDB query."
                }

                # Store the ADAPTED intent and mark step as completed
                state["interpreted_intent"] = adapted_intent
                state["current_step"] = "intent_completed"

                logger.info(f"✅ Intent understanding completed (adapted from query): {adapted_intent.get('primary_intent')}")
                return state
                
            except Exception as gemini_error:
                logger.error(f"Gemini API error: {gemini_error}")
                
                # Create intelligent fallback
                intent_data = self._create_fallback_intent(original_question, available_collections)
                state["interpreted_intent"] = intent_data
                state["errors"].append(f"Gemini API error (using fallback): {str(gemini_error)}")
                state["current_step"] = "intent_completed_fallback"
                
                logger.warning(f"Using fallback intent due to Gemini error: {intent_data}")
                return state
                
        except Exception as e:
            logger.error(f"❌ Intent understanding completely failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            state["errors"].append(f"Intent understanding failed: {str(e)}")
            state["current_step"] = "intent_failed"
            state["success"] = False
            
            return state
    
    def _create_fallback_intent(self, question: str, available_collections: List[str]) -> Dict[str, Any]:
        """Create intelligent fallback intent based on question keywords"""
        question_lower = question.lower()
        
        # Determine collection
        if 'user' in question_lower:
            collection = 'users' if 'users' in available_collections else available_collections[0]
            intent = 'user_management'
        elif 'cost' in question_lower or 'price' in question_lower or 'revenue' in question_lower:
            collection = 'documents' if 'documents' in available_collections else available_collections[0]
            intent = 'cost_analysis'
        elif 'document' in question_lower or 'file' in question_lower:
            collection = 'documents' if 'documents' in available_collections else available_collections[0]
            intent = 'document_processing'
        else:
            collection = available_collections[0] if available_collections else 'users'
            intent = 'general_query'
        
        # Determine analysis type
        if 'list' in question_lower or 'show' in question_lower:
            analysis_type = 'list'
        elif 'count' in question_lower or 'how many' in question_lower:
            analysis_type = 'count'
        elif 'compare' in question_lower or 'analysis' in question_lower:
            analysis_type = 'aggregate'
        else:
            analysis_type = 'list'
        
        return {
            "primary_intent": intent,
            "target_collection": collection,
            "analysis_type": analysis_type,
            "time_filter": "all",
            "visualization_needed": False,
            "confidence": 0.5,
            "reasoning": f"Fallback intent for question: {question}"
        }
    
    async def generate_mongo_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced MongoDB query generation with validation and fallbacks
        
        Args:
            state: Current workflow state with interpreted_intent
            
        Returns:
            Updated state with mongo_query configuration
        """
        try:
            state["current_step"] = "generating_query"
            intent = state.get("interpreted_intent", {})
            
            logger.info(f"🔍 Generating MongoDB query for intent: {intent.get('primary_intent', 'unknown')}")
            
            if not intent:
                raise Exception("No intent data available for query generation")
            
            collection = intent.get("target_collection", "users")
            analysis_type = intent.get("analysis_type", "list")
            
            # Validate collection exists
            try:
                if self.db is not None:
                    available_collections = self.db.list_collection_names()
                    if collection not in available_collections:
                        logger.warning(f"Collection '{collection}' not found in {available_collections}")
                        # Use first available collection as fallback
                        collection = available_collections[0] if available_collections else "users"
                        logger.info(f"Using fallback collection: {collection}")
                else:
                    logger.warning("Database not available - using default collection")
                    
            except Exception as e:
                logger.warning(f"Could not validate collection: {e}")
            
            # Generate appropriate MongoDB query based on analysis type
            if analysis_type == "list":
                mongo_query = {
                    "collection": collection,
                    "operation": "find",
                    "query": {},
                    "limit": 10,
                    "sort": {"_id": -1},
                    "projection": {}  # Get all fields
                }
                
            elif analysis_type == "count":
                mongo_query = {
                    "collection": collection,
                    "operation": "count_documents",
                    "query": {}
                }
                
            elif analysis_type == "aggregate":
                mongo_query = {
                    "collection": collection,
                    "operation": "aggregate",
                    "pipeline": [
                        {"$group": {"_id": None, "total_count": {"$sum": 1}}},
                        {"$limit": 1}
                    ]
                }
                
            elif analysis_type == "trend":
                mongo_query = {
                    "collection": collection,
                    "operation": "aggregate",
                    "pipeline": [
                        {"$sort": {"createdAt": -1}},
                        {"$limit": 20}
                    ]
                }
                
            else:
                # Default fallback
                mongo_query = {
                    "collection": collection,
                    "operation": "find",
                    "query": {},
                    "limit": 5
                }
            
            state["mongo_query"] = mongo_query
            state["current_step"] = "query_generated"
            
            logger.info(f"✅ MongoDB query generated successfully")
            logger.debug(f"Query details: {mongo_query}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Query generation failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            state["errors"].append(f"Query generation failed: {str(e)}")
            state["current_step"] = "query_generation_failed"
            
            return state
    
    async def execute_data_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced data query execution with comprehensive error handling
        
        Args:
            state: Current workflow state with mongo_query
            
        Returns:
            Updated state with raw_data results
        """
        try:
            state["current_step"] = "executing_query"
            query_config = state.get("mongo_query", {})
            
            logger.info(f"💾 Executing MongoDB query")
            logger.debug(f"Query config: {query_config}")
            
            if not query_config:
                raise Exception("No MongoDB query configuration available")
            
            if self.db is None:
                raise Exception("Database connection not available")
            
            collection_name = query_config.get("collection")
            operation = query_config.get("operation", "find")
            
            if not collection_name:
                raise Exception("No collection specified in query config")
            
            # Get collection with validation
            try:
                collection = self.db[collection_name]
                
                # Test collection access
                collection.find_one()
                logger.debug(f"Collection '{collection_name}' accessible")
                
            except Exception as e:
                raise Exception(f"Cannot access collection '{collection_name}': {e}")
            
            # Execute query based on operation type
            raw_data = []
            
            if operation == "find":
                query = query_config.get("query", {})
                limit = query_config.get("limit", 10)
                sort_config = query_config.get("sort", {})
                projection = query_config.get("projection", {})
                
                logger.debug(f"Executing find: query={query}, limit={limit}")
                
                cursor = collection.find(query, projection).limit(limit)
                if sort_config:
                    cursor = cursor.sort(list(sort_config.items()))
                
                raw_data = list(cursor)
                
            elif operation == "count_documents":
                query = query_config.get("query", {})
                count = collection.count_documents(query)
                raw_data = [{"count": count, "collection": collection_name}]
                
            elif operation == "aggregate":
                pipeline = query_config.get("pipeline", [])
                logger.debug(f"Executing aggregation: {pipeline}")
                raw_data = list(collection.aggregate(pipeline))
                
            else:
                raise Exception(f"Unsupported operation: {operation}")
            
            # Convert ObjectId and other MongoDB types to JSON-serializable format
            cleaned_data = self._clean_mongodb_data(raw_data)
            
            state["raw_data"] = cleaned_data
            state["current_step"] = "query_executed"
            
            logger.info(f"✅ Query executed successfully: {len(cleaned_data)} results from {collection_name}")
            
            if not cleaned_data:
                logger.warning("Query returned no results - this may be expected")
                state["errors"].append(f"Query returned no results from {collection_name}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            state["errors"].append(f"Query execution failed: {str(e)}")
            state["current_step"] = "execution_failed"
            
            return state
    
    def _clean_mongodb_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Clean MongoDB data for JSON serialization"""
        try:
            cleaned_data = []
            
            for item in raw_data:
                if isinstance(item, dict):
                    cleaned_item = {}
                    for key, value in item.items():
                        # Convert ObjectId to string
                        if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                            cleaned_item[key] = str(value)
                        elif isinstance(value, datetime):
                            cleaned_item[key] = value.isoformat()
                        elif isinstance(value, (int, float, str, bool)) or value is None:
                            cleaned_item[key] = value
                        else:
                            # Convert other types to string
                            cleaned_item[key] = str(value)
                    
                    cleaned_data.append(cleaned_item)
                else:
                    # Handle non-dict items
                    cleaned_data.append(str(item))
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            return raw_data  # Return as-is if cleaning fails
    
    async def plan_visualization(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced visualization planning with intelligent chart selection
        
        Args:
            state: Current workflow state with raw_data
            
        Returns:
            Updated state with chart_config
        """
        try:
            state["current_step"] = "planning_visualization"
            
            intent = state.get("interpreted_intent", {})
            raw_data = state.get("raw_data", [])
            
            logger.info(f"📊 Planning visualization for {len(raw_data)} data points")
            
            # Determine appropriate chart type
            analysis_type = intent.get("analysis_type", "list")
            data_count = len(raw_data)
            
            if data_count == 0:
                chart_config = {
                    "chart_type": "empty",
                    "message": "No data available for visualization",
                    "show_table": False
                }
                
            elif analysis_type == "count":
                chart_config = {
                    "chart_type": "metric",
                    "title": f"Total Count",
                    "value": raw_data[0].get("count", 0) if raw_data else 0,
                    "show_table": False
                }
                
            elif analysis_type == "list":
                chart_config = {
                    "chart_type": "table",
                    "title": f"Data from {intent.get('target_collection', 'database')}",
                    "columns": self._extract_table_columns(raw_data),
                    "show_table": True,
                    "pagination": data_count > 10
                }
                
            elif analysis_type in ["aggregate", "trend", "comparison"]:
                chart_config = {
                    "chart_type": "bar",
                    "title": f"Analysis Results",
                    "show_table": True,
                    "interactive": True
                }
                
            else:
                # Default table view
                chart_config = {
                    "chart_type": "table",
                    "title": "Query Results",
                    "columns": self._extract_table_columns(raw_data),
                    "show_table": True
                }
            
            state["chart_config"] = chart_config
            state["current_step"] = "visualization_planned"
            
            logger.info(f"✅ Visualization planned: {chart_config.get('chart_type')} chart")
            return state
            
        except Exception as e:
            logger.error(f"❌ Visualization planning failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Fallback visualization
            state["chart_config"] = {
                "chart_type": "table",
                "title": "Results",
                "show_table": True,
                "error": str(e)
            }
            
            state["errors"].append(f"Visualization planning failed: {str(e)}")
            state["current_step"] = "visualization_failed"
            
            return state
    
    def _extract_table_columns(self, data: List[Dict]) -> List[Dict]:
        """Extract table column configuration from data"""
        if not data or not isinstance(data[0], dict):
            return []
        
        sample_record = data[0]
        columns = []
        
        for field_name in sample_record.keys():
            if field_name.startswith('_'):
                continue  # Skip MongoDB internal fields
                
            column_config = {
                "key": field_name,
                "title": field_name.replace('_', ' ').title(),
                "type": self._determine_field_type(sample_record[field_name])
            }
            columns.append(column_config)
        
        return columns
    
    def _determine_field_type(self, value) -> str:
        """Determine field type for table formatting"""
        if isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, datetime):
            return "date"
        else:
            return "text"
    
    async def format_final_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced final response formatting with insights and recommendations
        
        Args:
            state: Current workflow state with all processing complete
            
        Returns:
            Updated state with final_result and success status
        """
        try:
            state["current_step"] = "formatting_response"
            
            chart_config = state.get("chart_config", {})
            raw_data = state.get("raw_data", [])
            intent = state.get("interpreted_intent", {})
            errors = state.get("errors", [])
            
            logger.info(f"📝 Formatting final response for {len(raw_data)} results")
            
            # Generate basic insights
            insights = self._generate_basic_insights(raw_data, intent)
            recommendations = self._generate_basic_recommendations(raw_data, intent)
            
            # Create comprehensive response
            final_response = {
                "success": len(errors) == 0,
                "summary": self._generate_summary(state),
                "chart_data": chart_config,
                "raw_data": raw_data,
                "insights": insights,
                "recommendations": recommendations,
                "results_count": len(raw_data),
                "query_source": "langgraph_workflow",
                "ai_powered": True,
                "workflow_enhanced": True,
                
                # Workflow metadata
                "workflow_metadata": {
                    "thread_id": state.get("thread_id"),
                    "steps_completed": state["current_step"],
                    "retry_count": state.get("retry_count", 0),
                    "errors": errors,
                    "intent_detected": intent.get("primary_intent"),
                    "target_collection": intent.get("target_collection"),
                    "processing_time": (datetime.now(timezone.utc) - state.get("start_time")).total_seconds() if state.get("start_time") else 0
                }
            }
            
            # Handle errors gracefully
            if errors:
                final_response["success"] = False
                final_response["summary"] = f"Query completed with {len(errors)} warnings"
                logger.warning(f"Response generated with {len(errors)} errors")
            
            state["final_result"] = final_response
            state["success"] = len(errors) == 0
            state["current_step"] = "completed"
            
            logger.info(f"✅ Response formatted successfully: {final_response['success']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Response formatting failed: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Create minimal error response
            error_response = {
                "success": False,
                "summary": f"Response formatting failed: {str(e)}",
                "error": str(e),
                "query_source": "langgraph_workflow_error",
                "workflow_metadata": {
                    "errors": state.get("errors", []) + [str(e)]
                }
            }
            
            state["final_result"] = error_response
            state["success"] = False
            state["errors"].append(f"Response formatting failed: {str(e)}")
            state["current_step"] = "formatting_failed"
            
            return state
    
    def _generate_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary based on workflow state"""
        intent = state.get("interpreted_intent", {})
        raw_data = state.get("raw_data", [])
        errors = state.get("errors", [])
        
        if errors:
            return f"Query processed with {len(errors)} issues. Found {len(raw_data)} results from {intent.get('target_collection', 'database')}."
        else:
            return f"Successfully analyzed {intent.get('primary_intent', 'query')}. Found {len(raw_data)} results from {intent.get('target_collection', 'database')}."
    
    def _generate_basic_insights(self, data: List[Dict], intent: Dict) -> List[str]:
        """Generate basic insights from data"""
        insights = []
        
        if not data:
            insights.append("No data found for the specified query")
            return insights
        
        data_count = len(data)
        insights.append(f"Retrieved {data_count} records from {intent.get('target_collection', 'database')}")
        
        if data_count > 0 and isinstance(data[0], dict):
            field_count = len(data[0].keys())
            insights.append(f"Each record contains {field_count} fields")
        
        return insights
    
    def _generate_basic_recommendations(self, data: List[Dict], intent: Dict) -> List[str]:
        """Generate basic recommendations"""
        recommendations = []
        
        if not data:
            recommendations.append("Consider checking if the collection contains data")
            recommendations.append("Verify the query criteria are correct")
        else:
            recommendations.append("Data retrieved successfully")
            if len(data) >= 10:
                recommendations.append("Consider adding filters to narrow down results")
        
        return recommendations
    
    async def handle_error_recovery(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced error recovery with intelligent retry logic
        
        Args:
            state: Current workflow state with errors
            
        Returns:
            Updated state with recovery actions
        """
        try:
            state["current_step"] = "handling_error"
            errors = state.get("errors", [])
            retry_count = state.get("retry_count", 0)
            
            logger.info(f"🔄 Handling error recovery: {len(errors)} errors, retry #{retry_count}")
            
            if retry_count >= 3:
                logger.warning("Maximum retries reached - ending workflow")
                state["success"] = False
                state["current_step"] = "max_retries_reached"
                return state
            
            # Increment retry count
            state["retry_count"] = retry_count + 1
            
            # Analyze error types for intelligent recovery
            has_gemini_error = any("Gemini" in error for error in errors)
            has_db_error = any("MongoDB" in error or "collection" in error.lower() for error in errors)
            has_intent_error = any("intent" in error.lower() for error in errors)
            
            # Determine recovery strategy
            if has_intent_error or has_gemini_error:
                logger.info("🔄 Retrying from intent understanding")
                state["current_step"] = "retry_intent"
                # Clear intent to force regeneration
                state["interpreted_intent"] = None
                
            elif has_db_error:
                logger.info("🔄 Retrying query execution")
                state["current_step"] = "retry_execute"
                
            else:
                logger.info("🔄 Generic retry - starting from query generation")
                state["current_step"] = "retry_query"
            
            # Clear previous errors for retry
            state["errors"] = [f"Retry #{retry_count + 1} initiated"]
            
            logger.info(f"✅ Error recovery strategy determined: {state['current_step']}")
            return state
            
        except Exception as e:
            logger.error(f"❌ Error recovery failed: {e}")
            state["errors"].append(f"Error recovery failed: {str(e)}")
            state["success"] = False
            state["current_step"] = "recovery_failed"
            return state