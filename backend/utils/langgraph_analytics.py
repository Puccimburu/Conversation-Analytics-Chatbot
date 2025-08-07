# backend/utils/langgraph_analytics.py
"""
LangGraph Analytics Workflow System
Main orchestration system that replaces linear processing with sophisticated workflows
"""

import logging
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import asdict

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig

# Local imports
from .workflow_nodes import AnalyticsWorkflowNodes, AnalyticsState
from .mongodb_checkpointer import MongoDBCheckpointer

logger = logging.getLogger(__name__)

class AnalyticsWorkflowState(TypedDict):
    """TypedDict definition for LangGraph state management"""
    # Input
    original_question: str
    user_id: str
    chat_id: str
    thread_id: Optional[str]
    start_time: Optional[datetime]
    
    # Processing pipeline
    interpreted_intent: Optional[Dict]
    mongo_query: Optional[Dict]
    chart_config: Optional[Dict]
    raw_data: Optional[List]
    formatted_response: Optional[Dict]
    
    # Workflow control
    current_step: str
    retry_count: int
    errors: List[str]
    
    # Output
    success: bool
    final_result: Optional[Dict]

class LangGraphAnalyticsWorkflow:
    """
    Advanced workflow orchestration for conversational analytics
    
    Replaces linear processing with sophisticated multi-step workflows that can:
    - Handle complex multi-step reasoning
    - Recover from errors at specific steps
    - Maintain state across sessions
    - Branch based on query complexity
    - Resume interrupted workflows
    """
    
    def __init__(self, gemini_client, mongodb_client, schema_info):
        """
        Initialize the LangGraph workflow system
        
        Args:
            gemini_client: Your existing enhanced Gemini client
            mongodb_client: MongoDB database client  
            schema_info: Database schema from config.py
        """
        self.gemini_client = gemini_client
        self.db = mongodb_client
        self.schema_info = schema_info
        
        # Initialize workflow nodes
        self.nodes = AnalyticsWorkflowNodes(
            gemini_client=gemini_client,
            mongodb_client=mongodb_client, 
            schema_info=schema_info
        )
        
        # Initialize checkpointer using your existing collection
        self.checkpointer = MongoDBCheckpointer(mongodb_client) if mongodb_client is not None else None
        
        # Build and compile the workflow
        self.workflow = self._build_workflow()
        self.compiled_workflow = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("✅ LangGraph Analytics Workflow initialized")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the complete LangGraph workflow with all nodes and edges
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create state graph
        workflow = StateGraph(AnalyticsWorkflowState)
        
        # Add workflow nodes
        workflow.add_node("understand_intent", self._understand_intent_wrapper)
        workflow.add_node("generate_query", self._generate_query_wrapper) 
        workflow.add_node("execute_query", self._execute_query_wrapper)
        workflow.add_node("plan_visualization", self._plan_visualization_wrapper)
        workflow.add_node("format_response", self._format_response_wrapper)
        workflow.add_node("handle_error", self._handle_error_wrapper)
        
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
            "handle_error",
            self._should_retry_or_end,
            {
                "retry_intent": "understand_intent",
                "retry_query": "generate_query",  
                "retry_execute": "execute_query",
                "end": END
            }
        )
        
        return workflow
    
    # Node wrapper functions to handle state conversion
    async def _understand_intent_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for understand_intent node"""
        result = await self.nodes.understand_intent(dict(state))
        return self._convert_to_workflow_state(result)
    
    async def _generate_query_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for generate_mongo_query node"""
        result = await self.nodes.generate_mongo_query(dict(state))
        return self._convert_to_workflow_state(result)
    
    async def _execute_query_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for execute_data_query node"""
        result = await self.nodes.execute_data_query(dict(state))
        return self._convert_to_workflow_state(result)
    
    async def _plan_visualization_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for plan_visualization node"""
        result = await self.nodes.plan_visualization(dict(state))
        return self._convert_to_workflow_state(result)
    
    async def _format_response_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for format_final_response node"""
        result = await self.nodes.format_final_response(dict(state))
        return self._convert_to_workflow_state(result)
    
    async def _handle_error_wrapper(self, state: AnalyticsWorkflowState) -> AnalyticsWorkflowState:
        """Wrapper for handle_error_recovery node"""
        result = await self.nodes.handle_error_recovery(dict(state))
        return self._convert_to_workflow_state(result)
    
    def _convert_to_workflow_state(self, state_dict: Dict[str, Any]) -> AnalyticsWorkflowState:
        """Convert dictionary state back to TypedDict format"""
        # Ensure all required fields exist
        workflow_state = AnalyticsWorkflowState(
            original_question=state_dict.get("original_question", ""),
            user_id=state_dict.get("user_id", "default_user"),
            chat_id=state_dict.get("chat_id", ""),
            thread_id=state_dict.get("thread_id"),
            start_time=state_dict.get("start_time"),
            interpreted_intent=state_dict.get("interpreted_intent"),
            mongo_query=state_dict.get("mongo_query"),
            chart_config=state_dict.get("chart_config"),
            raw_data=state_dict.get("raw_data"),
            formatted_response=state_dict.get("formatted_response"),
            current_step=state_dict.get("current_step", "unknown"),
            retry_count=state_dict.get("retry_count", 0),
            errors=state_dict.get("errors", []),
            success=state_dict.get("success", False),
            final_result=state_dict.get("final_result")
        )
        return workflow_state
    
    def _should_retry_or_continue(self, state: AnalyticsWorkflowState) -> str:
        """Conditional logic for retry/continue decisions"""
        errors = state.get("errors", [])
        retry_count = state.get("retry_count", 0)
        current_step = state.get("current_step", "")
        
        # If there are errors and we haven't exceeded retry limit
        if errors and retry_count < 2:
            return "retry"
        
        # If we have errors but exceeded retries, end workflow
        if errors and retry_count >= 2:
            return "end"
        
        # If no errors, continue normal flow
        return "continue"
    
    def _should_retry_or_end(self, state: AnalyticsWorkflowState) -> str:
        """Conditional logic for error recovery routing"""
        current_step = state.get("current_step", "")
        retry_count = state.get("retry_count", 0)
        
        # Max retries exceeded
        if retry_count >= 3:
            return "end"
        
        # Route based on recovery step
        if current_step == "recovery_intent":
            return "retry_intent"
        elif current_step == "recovery_query": 
            return "retry_query"
        elif current_step == "recovery_restart":
            return "retry_intent"
        else:
            return "end"
    
    async def process_analytics_query(
        self, 
        question: str, 
        chat_id: str, 
        user_id: str = "default_user",
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing analytics queries with LangGraph workflows
        
        Args:
            question: User's analytics question
            chat_id: Chat session identifier
            user_id: User identifier for personalization
            thread_id: Optional thread ID for resuming workflows
            
        Returns:
            Processed analytics result with workflow metadata
        """
        try:
            # Generate thread ID if not provided
            if not thread_id:
                thread_id = f"analytics_{user_id}_{int(datetime.now().timestamp())}"
            
            logger.info(f"🚀 Starting LangGraph workflow for: '{question}' (Thread: {thread_id})")
            
            # Initialize state
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
                    "workflow_type": "analytics",
                    "original_question": question
                }
            )
            
            # Execute workflow
            start_execution = datetime.now()
            final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)
            execution_time = (datetime.now() - start_execution).total_seconds()
            
            # Extract final result
            final_result = final_state.get("final_result", {})
            
            # Add workflow-specific metadata
            if isinstance(final_result, dict):
                final_result["workflow_metadata"] = {
                    "thread_id": thread_id,
                    "execution_time": execution_time,
                    "steps_completed": final_state.get("current_step"),
                    "retry_count": final_state.get("retry_count", 0),
                    "success": final_state.get("success", False),
                    "workflow_type": "langgraph_analytics",
                    "checkpoint_available": self.checkpointer is not None,
                    "errors": final_state.get("errors", [])
                }
                
                # Log workflow completion
                if final_state.get("success"):
                    logger.info(f"✅ LangGraph workflow completed successfully in {execution_time:.2f}s")
                else:
                    logger.warning(f"⚠️ LangGraph workflow completed with errors in {execution_time:.2f}s")
            
            return final_result or {
                "success": False,
                "error": "Workflow execution failed",
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"❌ LangGraph workflow execution failed: {e}")
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "thread_id": thread_id,
                "workflow_metadata": {
                    "execution_failed": True,
                    "error_details": str(e)
                }
            }
    
    async def resume_workflow(self, thread_id: str, user_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Resume a paused or failed workflow from its last checkpoint
        
        Args:
            thread_id: Thread identifier of the workflow to resume
            user_input: Optional user input for interactive workflows
            
        Returns:
            Result of resumed workflow execution
        """
        try:
            if not self.checkpointer:
                return {
                    "success": False,
                    "error": "Checkpointing not available - cannot resume workflow"
                }
            
            logger.info(f"🔄 Resuming workflow thread: {thread_id}")
            
            # Create configuration for resuming
            config = RunnableConfig(
                configurable={
                    "thread_id": thread_id,
                    "resume_mode": True
                }
            )
            
            # Get the last checkpoint
            checkpoint_data = self.checkpointer.get_tuple(config)
            if not checkpoint_data:
                return {
                    "success": False,
                    "error": f"No checkpoint found for thread {thread_id}"
                }
            
            # Resume execution from checkpoint
            final_state = await self.compiled_workflow.ainvoke({}, config=config)
            
            logger.info(f"✅ Workflow resumed and completed for thread {thread_id}")
            return final_state.get("final_result", {
                "success": False,
                "error": "Resume completed but no final result"
            })
            
        except Exception as e:
            logger.error(f"❌ Workflow resume failed: {e}")
            return {
                "success": False,
                "error": f"Workflow resume failed: {str(e)}"
            }
    
    def get_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """
        Get current status of a workflow thread
        
        Args:
            thread_id: Thread identifier to check
            
        Returns:
            Workflow status information
        """
        try:
            if not self.checkpointer:
                return {"error": "Checkpointing not available"}
            
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
                "chat_id": state.get("chat_id")
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return {
                "thread_id": thread_id,
                "status": "error",
                "error": str(e)
            }
    
    def get_user_workflow_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get workflow execution history for a specific user
        
        Args:
            user_id: User identifier
            limit: Maximum number of workflows to return
            
        Returns:
            List of workflow execution records
        """
        try:
            if not self.checkpointer:
                return []
            
            history = self.checkpointer.get_workflow_history(user_id, limit)
            return history
            
        except Exception as e:
            logger.error(f"Failed to get user workflow history: {e}")
            return []
    
    def get_active_workflows(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get currently active (incomplete) workflows
        
        Args:
            user_id: Optional user filter
            
        Returns:
            List of active workflow records
        """
        try:
            if not self.checkpointer:
                return []
            
            active = self.checkpointer.get_active_workflows(user_id)
            return active
            
        except Exception as e:
            logger.error(f"Failed to get active workflows: {e}")
            return []
    
    def cleanup_old_workflows(self, days_old: int = 30) -> int:
        """
        Clean up old completed workflow checkpoints
        
        Args:
            days_old: Age threshold for cleanup
            
        Returns:
            Number of workflows cleaned up
        """
        try:
            if not self.checkpointer:
                return 0
            
            cleaned_count = self.checkpointer.cleanup_old_checkpoints(days_old)
            logger.info(f"🧹 Cleaned up {cleaned_count} old workflow checkpoints")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup workflows: {e}")
            return 0
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get system statistics for the workflow engine
        
        Returns:
            System statistics and health information
        """
        try:
            active_workflows = len(self.get_active_workflows())
            
            stats = {
                "workflow_engine": "LangGraph",
                "checkpointer_available": self.checkpointer is not None,
                "active_workflows": active_workflows,
                "nodes_available": [
                    "understand_intent",
                    "generate_query", 
                    "execute_query",
                    "plan_visualization",
                    "format_response",
                    "handle_error"
                ],
                "features": {
                    "error_recovery": True,
                    "state_persistence": self.checkpointer is not None,
                    "workflow_resume": self.checkpointer is not None,
                    "conditional_branching": True,
                    "multi_step_reasoning": True
                },
                "database_integration": self.db is not None,
                "gemini_integration": self.gemini_client is not None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}