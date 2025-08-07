# backend/utils/langgraph_analytics_enhanced.py
"""
Enhanced LangGraph Analytics Workflow System
Fixed version that addresses the execution failures and adds comprehensive debugging
"""

import logging
import asyncio
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig

# Local imports
from .workflow_nodes import EnhancedAnalyticsWorkflowNodes, AnalyticsState
from .mongodb_checkpointer import MongoDBCheckpointer

logger = logging.getLogger(__name__)

class AnalyticsWorkflowState(TypedDict):
    """Enhanced TypedDict definition for LangGraph state management"""
    # Use a reducer for all simple pass-through fields to be safe.
    # This takes the last value written to the key.
    original_question: Annotated[str, lambda x, y: y]
    user_id: Annotated[str, lambda x, y: y]
    chat_id: Annotated[str, lambda x, y: y]
    thread_id: Annotated[Optional[str], lambda x, y: y]
    start_time: Annotated[Optional[datetime], lambda x, y: y]
    
    # These are the fields that are *actually* updated by nodes.
    # We will add reducers to these as well for maximum safety.
    interpreted_intent: Annotated[Optional[Dict], lambda x, y: y]
    mongo_query: Annotated[Optional[Dict], lambda x, y: y]
    chart_config: Annotated[Optional[Dict], lambda x, y: y]
    raw_data: Annotated[Optional[List], lambda x, y: y]
    formatted_response: Annotated[Optional[Dict], lambda x, y: y]
    final_result: Annotated[Optional[Dict], lambda x, y: y]
    
    # Control fields also need reducers
    current_step: Annotated[str, lambda x, y: y]
    success: Annotated[bool, lambda x, y: y]
    
    # Special reducers for list concatenation and integer addition
    errors: Annotated[List[str], operator.add]
    retry_count: Annotated[int, operator.add]

class EnhancedLangGraphAnalyticsWorkflow:
    """
    Enhanced workflow orchestration with comprehensive error handling and debugging
    
    Fixes the execution failures identified in test results by:
    - Adding detailed error logging throughout
    - Improving async operation handling
    - Adding fallback mechanisms
    - Enhancing state management
    """
    
    def __init__(self, gemini_client, mongodb_client, schema_info):
        """
        Initialize the enhanced LangGraph workflow system
        
        Args:
            gemini_client: Enhanced Gemini client for AI operations
            mongodb_client: MongoDB database client
            schema_info: Database schema configuration
        """
        self.gemini_client = gemini_client
        self.db = mongodb_client
        self.schema_info = schema_info
        
        # Initialize enhanced workflow nodes
        self.nodes = EnhancedAnalyticsWorkflowNodes(
            gemini_client=gemini_client,
            mongodb_client=mongodb_client,
            schema_info=schema_info
        )
        
        # Initialize checkpointer with enhanced error handling
        try:
            self.checkpointer = MongoDBCheckpointer(mongodb_client) if mongodb_client is not None else None
            if self.checkpointer:
                logger.info("✅ MongoDB checkpointer initialized")
            else:
                logger.warning("⚠️ Checkpointer not available - workflows won't persist")
        except Exception as e:
            logger.error(f"Failed to initialize checkpointer: {e}")
            self.checkpointer = None
        
        # Build and compile the workflow with error handling
        try:
            self.workflow = self._build_enhanced_workflow()
            self.compiled_workflow = self.workflow.compile(checkpointer=self.checkpointer)
            logger.info("✅ Enhanced LangGraph Analytics Workflow initialized")
        except Exception as e:
            logger.error(f"Failed to build workflow: {e}")
            raise
    
    def _build_enhanced_workflow(self) -> StateGraph:
        """
        Build the enhanced workflow with comprehensive error handling and debugging
        
        Returns:
            StateGraph with enhanced error handling and recovery
        """
        try:
            # Create state graph
            workflow = StateGraph(AnalyticsWorkflowState)
            
            # Add workflow nodes with enhanced wrappers
            workflow.add_node("understand_intent", self._enhanced_understand_intent_wrapper)
            workflow.add_node("generate_query", self._enhanced_generate_query_wrapper)
            workflow.add_node("execute_query", self._enhanced_execute_query_wrapper)
            workflow.add_node("plan_visualization", self._enhanced_plan_visualization_wrapper)
            workflow.add_node("format_response", self._enhanced_format_response_wrapper)
            workflow.add_node("handle_error", self._enhanced_handle_error_wrapper)
            
            # Set entry point
            workflow.set_entry_point("understand_intent")
            
            # Add edges for normal flow
            workflow.add_edge("understand_intent", "generate_query")
            workflow.add_edge("generate_query", "execute_query")
            workflow.add_edge("execute_query", "plan_visualization")
            workflow.add_edge("plan_visualization", "format_response")
            workflow.add_edge("format_response", END)
            
            # Add conditional edges for error handling
            workflow.add_conditional_edges(
                "understand_intent",
                self._should_retry_or_continue,
                {
                    "retry": "handle_error",
                    "continue": "generate_query",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "generate_query",
                self._should_retry_or_continue,
                {
                    "retry": "handle_error",
                    "continue": "execute_query",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "execute_query",
                self._should_retry_or_continue,
                {
                    "retry": "handle_error",
                    "continue": "plan_visualization",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "plan_visualization",
                self._should_retry_or_continue,
                {
                    "retry": "handle_error",
                    "continue": "format_response",
                    "end": END
                }
            )
            
            workflow.add_conditional_edges(
                "handle_error",
                self._should_retry_or_end,
                {
                    "retry_intent": "understand_intent",
                    "retry_query": "generate_query",
                    "retry_execute": "execute_query",
                    "retry_visualization": "plan_visualization",
                    "end": END
                }
            )
            
            logger.info("✅ Enhanced workflow graph built successfully")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to build workflow: {e}")
            raise
    
    # Enhanced node wrapper functions with comprehensive error handling
    async def _enhanced_understand_intent_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for understand_intent node with detailed error handling"""
        try:
            logger.debug(f"🧠 Intent wrapper called for: '{state.get('original_question', 'N/A')}'")
            logger.debug(f"State keys available: {list(state.keys())}")
            
            # Convert to dict for node processing
            state_dict = dict(state)
            
            # Call the enhanced node
            result_dict = await self.nodes.understand_intent(state_dict)
            
            if not result_dict:
                raise Exception("Node returned None result")
            
            if not isinstance(result_dict, dict):
                raise Exception(f"Node returned invalid type: {type(result_dict)}")
            
            logger.debug(f"Intent node result keys: {list(result_dict.keys())}")
            
            # Convert back to workflow state format
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            
            logger.info(f"✅ Intent understanding wrapper completed successfully")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Intent wrapper failed: {e}")
            logger.error(f"Detailed traceback: {traceback.format_exc()}")
            
            # Create error state
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Intent wrapper error: {str(e)}"]
            error_state["current_step"] = "intent_wrapper_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    async def _enhanced_generate_query_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for generate_mongo_query node"""
        try:
            logger.debug("🔍 Query generation wrapper called")
            
            state_dict = dict(state)
            result_dict = await self.nodes.generate_mongo_query(state_dict)
            
            if not result_dict or not isinstance(result_dict, dict):
                raise Exception(f"Query node returned invalid result: {type(result_dict)}")
            
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            logger.info("✅ Query generation wrapper completed")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Query wrapper failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Query wrapper error: {str(e)}"]
            error_state["current_step"] = "query_wrapper_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    async def _enhanced_execute_query_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for execute_data_query node"""
        try:
            logger.debug("💾 Query execution wrapper called")
            
            state_dict = dict(state)
            result_dict = await self.nodes.execute_data_query(state_dict)
            
            if not result_dict or not isinstance(result_dict, dict):
                raise Exception(f"Execution node returned invalid result: {type(result_dict)}")
            
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            logger.info("✅ Query execution wrapper completed")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Execution wrapper failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Execution wrapper error: {str(e)}"]
            error_state["current_step"] = "execution_wrapper_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    async def _enhanced_plan_visualization_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for plan_visualization node"""
        try:
            logger.debug("📊 Visualization planning wrapper called")
            
            state_dict = dict(state)
            result_dict = await self.nodes.plan_visualization(state_dict)
            
            if not result_dict or not isinstance(result_dict, dict):
                raise Exception(f"Visualization node returned invalid result: {type(result_dict)}")
            
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            logger.info("✅ Visualization planning wrapper completed")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Visualization wrapper failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Visualization wrapper error: {str(e)}"]
            error_state["current_step"] = "visualization_wrapper_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    async def _enhanced_format_response_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for format_final_response node"""
        try:
            logger.debug("📝 Response formatting wrapper called")
            
            state_dict = dict(state)
            result_dict = await self.nodes.format_final_response(state_dict)
            
            if not result_dict or not isinstance(result_dict, dict):
                raise Exception(f"Format node returned invalid result: {type(result_dict)}")
            
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            logger.info("✅ Response formatting wrapper completed")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Format wrapper failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Format wrapper error: {str(e)}"]
            error_state["current_step"] = "format_wrapper_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    async def _enhanced_handle_error_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Enhanced wrapper for handle_error_recovery node"""
        try:
            logger.debug("🔄 Error handling wrapper called")
            
            state_dict = dict(state)
            result_dict = await self.nodes.handle_error_recovery(state_dict)
            
            if not result_dict or not isinstance(result_dict, dict):
                raise Exception(f"Error handling node returned invalid result: {type(result_dict)}")
            
            enhanced_state = self._convert_dict_to_workflow_state(result_dict)
            logger.info("✅ Error handling wrapper completed")
            return enhanced_state
            
        except Exception as e:
            logger.error(f"❌ Error handling wrapper failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Final fallback - just mark as failed
            error_state = dict(state)
            error_state["errors"] = error_state.get("errors", []) + [f"Error handling failed: {str(e)}"]
            error_state["current_step"] = "error_handling_failed"
            error_state["success"] = False
            
            return self._convert_dict_to_workflow_state(error_state)
    
    def _convert_dict_to_workflow_state(self, state_dict: Dict[str, Any]) -> AnalyticsWorkflowState:
        """
        Convert dictionary state to TypedDict format with validation
        
        Args:
            state_dict: Dictionary containing state data
            
        Returns:
            Properly formatted AnalyticsWorkflowState
        """
        try:
            # Ensure all required fields exist with proper defaults
            workflow_state = AnalyticsWorkflowState(
                # Required input fields
                original_question=state_dict.get("original_question", ""),
                user_id=state_dict.get("user_id", "default_user"),
                chat_id=state_dict.get("chat_id", ""),
                
                # Optional fields with proper defaults
                thread_id=state_dict.get("thread_id"),
                start_time=state_dict.get("start_time"),
                interpreted_intent=state_dict.get("interpreted_intent"),
                mongo_query=state_dict.get("mongo_query"),
                chart_config=state_dict.get("chart_config"),
                raw_data=state_dict.get("raw_data"),
                formatted_response=state_dict.get("formatted_response"),
                
                # Control fields
                current_step=state_dict.get("current_step", "start"),
                retry_count=state_dict.get("retry_count", 0),
                errors=state_dict.get("errors", []),
                
                # Output fields
                success=state_dict.get("success", False),
                final_result=state_dict.get("final_result")
            )
            
            return workflow_state
            
        except Exception as e:
            logger.error(f"State conversion failed: {e}")
            # Return minimal valid state
            return AnalyticsWorkflowState(
                original_question=state_dict.get("original_question", ""),
                user_id=state_dict.get("user_id", "default_user"),
                chat_id=state_dict.get("chat_id", ""),
                thread_id=None,
                start_time=None,
                interpreted_intent=None,
                mongo_query=None,
                chart_config=None,
                raw_data=None,
                formatted_response=None,
                current_step="conversion_failed",
                retry_count=0,
                errors=[f"State conversion error: {str(e)}"],
                success=False,
                final_result=None
            )
    
    def _should_retry_or_continue(self, state: AnalyticsWorkflowState) -> str:
        """
        Enhanced decision logic for retry vs continue vs end
        
        Args:
            state: Current workflow state
            
        Returns:
            Decision string: "retry", "continue", or "end"
        """
        try:
            current_step = state.get("current_step", "")
            errors = state.get("errors", [])
            retry_count = state.get("retry_count", 0)
            
            logger.debug(f"Decision point: step={current_step}, errors={len(errors)}, retries={retry_count}")
            
            # End conditions
            if retry_count >= 3:
                logger.info("🛑 Maximum retries reached - ending workflow")
                return "end"
            
            if current_step in ["completed", "max_retries_reached"]:
                return "end"
            
            # Retry conditions
            if current_step.endswith("_failed") or current_step.endswith("_wrapper_failed"):
                if retry_count < 3:
                    logger.info(f"🔄 Retry needed for step: {current_step}")
                    return "retry"
                else:
                    return "end"
            
            # Continue conditions
            if current_step.endswith("_completed") or current_step in ["intent_completed", "query_generated", "query_executed", "visualization_planned"]:
                logger.debug(f"✅ Continuing from successful step: {current_step}")
                return "continue"
            
            # Default: continue if no explicit failure
            if not errors or len(errors) == 0:
                return "continue"
            
            # Has errors but under retry limit
            if retry_count < 2:
                return "retry"
            
            return "end"
            
        except Exception as e:
            logger.error(f"Decision logic failed: {e}")
            return "end"
    
    def _should_retry_or_end(self, state: AnalyticsWorkflowState) -> str:
        """
        Enhanced decision logic for error recovery
        
        Args:
            state: Current workflow state in error handling
            
        Returns:
            Recovery strategy: "retry_intent", "retry_query", "retry_execute", "retry_visualization", or "end"
        """
        try:
            current_step = state.get("current_step", "")
            retry_count = state.get("retry_count", 0)
            errors = state.get("errors", [])
            
            logger.debug(f"Error recovery decision: step={current_step}, retries={retry_count}")
            
            if retry_count >= 3:
                logger.warning("Maximum retries reached in error recovery")
                return "end"
            
            # Analyze error types for targeted recovery
            has_intent_error = any("intent" in error.lower() for error in errors)
            has_query_error = any("query" in error.lower() for error in errors)
            has_execution_error = any("execution" in error.lower() or "mongodb" in error.lower() for error in errors)
            has_visualization_error = any("visualization" in error.lower() for error in errors)
            
            # Determine recovery strategy
            if has_intent_error or current_step == "retry_intent":
                logger.info("🔄 Retrying from intent understanding")
                return "retry_intent"
            elif has_query_error or current_step == "retry_query":
                logger.info("🔄 Retrying from query generation")
                return "retry_query"
            elif has_execution_error or current_step == "retry_execute":
                logger.info("🔄 Retrying from query execution")
                return "retry_execute"
            elif has_visualization_error or current_step == "retry_visualization":
                logger.info("🔄 Retrying from visualization planning")
                return "retry_visualization"
            
            # Default retry strategy
            if retry_count == 0:
                return "retry_query"  # Most common failure point
            elif retry_count == 1:
                return "retry_intent"  # Try fresh intent analysis
            else:
                return "end"
                
        except Exception as e:
            logger.error(f"Error recovery decision failed: {e}")
            return "end"
    
    async def execute_workflow(
        self,
        question: str,
        user_id: str = "default_user",
        chat_id: str = None,
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Execute workflow with comprehensive error handling and debugging
        
        Args:
            question: User's analytics question
            user_id: User identifier
            chat_id: Chat session identifier
            thread_id: Workflow thread identifier (auto-generated if None)
            
        Returns:
            Complete workflow result with detailed metadata
        """
        if not thread_id:
            thread_id = f"analytics_{user_id}_{int(datetime.now().timestamp())}"
        
        if not chat_id:
            chat_id = f"chat_{int(datetime.now().timestamp())}"
        
        try:
            logger.info(f"🚀 Starting enhanced LangGraph workflow for: '{question}' (Thread: {thread_id})")
            
            # Initialize enhanced state with validation
            initial_state = AnalyticsWorkflowState(
                original_question=question,
                user_id=user_id,
                chat_id=chat_id,
                thread_id=thread_id,
                start_time=datetime.now(timezone.utc),
                interpreted_intent=None,
                mongo_query=None,
                chart_config=None,
                raw_data=None,
                formatted_response=None,
                current_step="start",
                retry_count=0,
                errors=[],
                success=False,
                final_result=None
            )
            
            # Create runnable configuration
            config = RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "user_id": user_id,
                    "chat_id": chat_id,
                    "workflow_type": "enhanced_analytics",
                    "original_question": question
                }
            )
            
            # Execute workflow with comprehensive error handling
            start_execution = datetime.now()
            
            try:
                logger.info(f"⚡ Executing compiled workflow...")
                final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)
                
            except Exception as workflow_error:
                logger.error(f"❌ Workflow execution failed: {workflow_error}")
                logger.error(f"Workflow traceback: {traceback.format_exc()}")
                
                # Create fallback result
                return {
                    "success": False,
                    "error": f"Workflow execution failed: {str(workflow_error)}",
                    "summary": f"Failed to process: {question}",
                    "query_source": "langgraph_enhanced_fallback",
                    "workflow_metadata": {
                        "thread_id": thread_id,
                        "execution_failed": True,
                        "error_details": str(workflow_error),
                        "fallback_used": True
                    }
                }
            
            execution_time = (datetime.now() - start_execution).total_seconds()
            
            # Extract and validate final result
            final_result = final_state.get("final_result", {})
            
            if not final_result:
                logger.warning("Workflow completed but no final_result found")
                
                # Create result from available state
                final_result = {
                    "success": final_state.get("success", False),
                    "summary": f"Workflow processed: {question}",
                    "chart_data": final_state.get("chart_config", {}),
                    "raw_data": final_state.get("raw_data", []),
                    "results_count": len(final_state.get("raw_data", [])),
                    "insights": [f"Processed query: {question}"],
                    "recommendations": ["Review results for accuracy"],
                    "query_source": "langgraph_enhanced_recovered"
                }
            
            # Add enhanced workflow metadata
            if isinstance(final_result, dict):
                final_result["workflow_metadata"] = {
                    "thread_id": thread_id,
                    "execution_time": execution_time,
                    "steps_completed": final_state.get("current_step", "unknown"),
                    "retry_count": final_state.get("retry_count", 0),
                    "success": final_state.get("success", False),
                    "workflow_type": "langgraph_enhanced",
                    "checkpoint_available": self.checkpointer is not None,
                    "errors": final_state.get("errors", []),
                    "enhanced_features": True,
                    "intent_detected": final_state.get("interpreted_intent", {}).get("primary_intent", "unknown")
                }
                
                # Enhanced logging
                if final_state.get("success"):
                    logger.info(f"✅ Enhanced LangGraph workflow completed successfully in {execution_time:.2f}s")
                else:
                    logger.warning(f"⚠️ Enhanced LangGraph workflow completed with issues in {execution_time:.2f}s")
                    logger.warning(f"Errors encountered: {final_state.get('errors', [])}")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Enhanced workflow execution completely failed: {e}")
            logger.error(f"Complete traceback: {traceback.format_exc()}")
            
            return {
                "success": False,
                "error": f"Enhanced workflow execution failed: {str(e)}",
                "summary": f"Critical failure processing: {question}",
                "query_source": "langgraph_enhanced_critical_error",
                "workflow_metadata": {
                    "thread_id": thread_id,
                    "critical_failure": True,
                    "error_details": str(e),
                    "traceback": traceback.format_exc()
                }
            }
    
    async def resume_workflow(self, thread_id: str) -> Dict[str, Any]:
        """
        Resume an interrupted workflow with enhanced error handling
        
        Args:
            thread_id: Thread identifier for the workflow to resume
            
        Returns:
            Workflow result or error information
        """
        try:
            if not self.checkpointer:
                return {
                    "success": False,
                    "error": "Cannot resume workflow - checkpointing not available"
                }
            
            logger.info(f"🔄 Attempting to resume workflow: {thread_id}")
            
            # Get checkpoint configuration
            config = RunnableConfig(configurable={"thread_id": thread_id})
            
            # Resume execution
            start_time = datetime.now()
            final_state = await self.compiled_workflow.ainvoke(None, config=config)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Extract result
            final_result = final_state.get("final_result", {})
            
            if isinstance(final_result, dict):
                final_result["workflow_metadata"] = final_result.get("workflow_metadata", {})
                final_result["workflow_metadata"]["resumed"] = True
                final_result["workflow_metadata"]["resume_execution_time"] = execution_time
            
            logger.info(f"✅ Workflow resumed successfully in {execution_time:.2f}s")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Failed to resume workflow {thread_id}: {e}")
            return {
                "success": False,
                "error": f"Failed to resume workflow: {str(e)}",
                "thread_id": thread_id
            }
    
    def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """
        Get enhanced status information for a workflow thread
        
        Args:
            thread_id: Thread identifier to check
            
        Returns:
            Detailed workflow status information
        """
        try:
            if not self.checkpointer:
                return {
                    "thread_id": thread_id,
                    "status": "checkpointing_unavailable",
                    "message": "Cannot check status - checkpointing not available"
                }
            
            config = RunnableConfig(configurable={"thread_id": thread_id})
            checkpoint_data = self.checkpointer.get_tuple(config)
            
            if not checkpoint_data:
                return {
                    "thread_id": thread_id,
                    "status": "not_found",
                    "message": "No workflow found for this thread"
                }
            
            _, checkpoint, metadata = checkpoint_data
            state = checkpoint.get("channel_values", {})
            
            return {
                "thread_id": thread_id,
                "status": "active" if not state.get("success") else "completed",
                "current_step": state.get("current_step", "unknown"),
                "success": state.get("success", False),
                "retry_count": state.get("retry_count", 0),
                "errors": state.get("errors", []),
                "original_question": state.get("original_question"),
                "user_id": state.get("user_id"),
                "chat_id": state.get("chat_id"),
                "has_results": len(state.get("raw_data", [])) > 0,
                "intent_detected": state.get("interpreted_intent", {}).get("primary_intent", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get enhanced system statistics and capabilities
        
        Returns:
            Comprehensive system status information
        """
        try:
            stats = {
                "langgraph_version": "enhanced_v2.0",
                "available": True,
                "capabilities": {
                    "workflow_orchestration": True,
                    "error_recovery": True,
                    "state_persistence": self.checkpointer is not None,
                    "workflow_resume": self.checkpointer is not None,
                    "multi_step_reasoning": True,
                    "enhanced_debugging": True,
                    "fallback_mechanisms": True
                },
                "components": {
                    "gemini_client": self.gemini_client is not None,
                    "mongodb_client": self.db is not None,
                    "checkpointer": self.checkpointer is not None,
                    "workflow_nodes": True,
                    "enhanced_error_handling": True
                },
                "workflow_nodes": [
                    "understand_intent",
                    "generate_query", 
                    "execute_query",
                    "plan_visualization",
                    "format_response",
                    "handle_error"
                ],
                "supported_intents": [
                    "user_management",
                    "cost_analysis", 
                    "document_processing",
                    "compliance_review",
                    "performance_analysis",
                    "general_query"
                ]
            }
            
            # Add active workflow count if possible
            try:
                if self.checkpointer and hasattr(self.checkpointer, 'get_active_workflows'):
                    active_workflows = self.checkpointer.get_active_workflows()
                    stats["active_workflows"] = len(active_workflows) if active_workflows else 0
                else:
                    stats["active_workflows"] = "unknown"
            except:
                stats["active_workflows"] = "unavailable"
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def test_workflow_components(self) -> Dict[str, Any]:
        """
        Test individual workflow components for debugging
        
        Returns:
            Test results for each component
        """
        test_results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component_tests": {}
        }
        
        # Test Gemini client
        try:
            if self.gemini_client:
                test_prompt = "Test prompt for component validation"
                response = await self.gemini_client.generate_response(test_prompt)
                test_results["component_tests"]["gemini_client"] = {
                    "status": "pass" if response and response.get('success') else "fail",
                    "details": "Gemini client responds correctly" if response and response.get('success') else f"Error: {response}"
                }
            else:
                test_results["component_tests"]["gemini_client"] = {
                    "status": "fail",
                    "details": "Gemini client not available"
                }
        except Exception as e:
            test_results["component_tests"]["gemini_client"] = {
                "status": "error",
                "details": str(e)
            }
        
        # Test MongoDB connection
        try:
            if self.db:
                collections = self.db.list_collection_names()
                test_results["component_tests"]["mongodb"] = {
                    "status": "pass",
                    "details": f"Connected with {len(collections)} collections"
                }
            else:
                test_results["component_tests"]["mongodb"] = {
                    "status": "fail",
                    "details": "MongoDB client not available"
                }
        except Exception as e:
            test_results["component_tests"]["mongodb"] = {
                "status": "error",
                "details": str(e)
            }
        
        # Test checkpointer
        try:
            if self.checkpointer:
                test_results["component_tests"]["checkpointer"] = {
                    "status": "pass",
                    "details": "MongoDB checkpointer available"
                }
            else:
                test_results["component_tests"]["checkpointer"] = {
                    "status": "fail",
                    "details": "Checkpointer not available"
                }
        except Exception as e:
            test_results["component_tests"]["checkpointer"] = {
                "status": "error",
                "details": str(e)
            }
        
        # Test workflow compilation
        try:
            if self.compiled_workflow:
                test_results["component_tests"]["workflow_compilation"] = {
                    "status": "pass",
                    "details": "Workflow compiled successfully"
                }
            else:
                test_results["component_tests"]["workflow_compilation"] = {
                    "status": "fail",
                    "details": "Workflow not compiled"
                }
        except Exception as e:
            test_results["component_tests"]["workflow_compilation"] = {
                "status": "error",
                "details": str(e)
            }
        
        # Calculate overall status
        passed_tests = sum(1 for test in test_results["component_tests"].values() if test["status"] == "pass")
        total_tests = len(test_results["component_tests"])
        
        test_results["summary"] = {
            "passed": passed_tests,
            "total": total_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "overall_status": "healthy" if passed_tests == total_tests else "degraded" if passed_tests > 0 else "critical"
        }
        
        logger.info(f"Component test results: {passed_tests}/{total_tests} passed")
        return test_results
    
    def get_user_workflow_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get enhanced workflow execution history for a specific user
        
        Args:
            user_id: User identifier
            limit: Maximum number of workflows to return
            
        Returns:
            List of workflow execution records with enhanced metadata
        """
        try:
            if not self.checkpointer:
                return []
            
            if hasattr(self.checkpointer, 'get_workflow_history'):
                history = self.checkpointer.get_workflow_history(user_id, limit)
                return history
            else:
                logger.warning("Checkpointer does not support workflow history")
                return []
            
        except Exception as e:
            logger.error(f"Failed to get user workflow history: {e}")
            return []
    
    def get_active_workflows(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get currently active (incomplete) workflows with enhanced filtering
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of active workflow information
        """
        try:
            if not self.checkpointer:
                return []
            
            if hasattr(self.checkpointer, 'get_active_workflows'):
                active_workflows = self.checkpointer.get_active_workflows(user_id)
                return active_workflows
            else:
                logger.warning("Checkpointer does not support active workflows query")
                return []
            
        except Exception as e:
            logger.error(f"Failed to get active workflows: {e}")
            return []