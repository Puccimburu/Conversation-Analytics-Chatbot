# backend/workflows/analytics_flow.py
"""
Analytics Workflow Definitions
Pre-configured workflow templates for different types of analytics queries
"""

import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowComplexity(Enum):
    """Enumeration of workflow complexity levels"""
    SIMPLE = "simple"           # Direct path: Intent → Query → Execute → Format
    COMPLEX = "complex"         # Multi-step with validation and error handling
    INTERACTIVE = "interactive" # User feedback loops and decision points
    EXPLORATORY = "exploratory" # Data discovery with multiple iterations

class AnalyticsIntent(Enum):
    """Enumeration of analytics intent types"""
    COST_ANALYSIS = "cost_analysis"
    DOCUMENT_PROCESSING = "document_processing"  
    COMPLIANCE_REVIEW = "compliance_review"
    USER_MANAGEMENT = "user_management"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    GENERAL_QUERY = "general_query"

@dataclass
class WorkflowConfig:
    """Configuration for different workflow types"""
    name: str
    complexity: WorkflowComplexity
    intent: AnalyticsIntent
    description: str
    steps: List[str]
    max_retries: int
    timeout_minutes: int
    requires_user_input: bool = False

class AnalyticsWorkflowTemplates:
    """
    Pre-defined workflow templates for different analytics scenarios
    
    This class provides workflow configurations that can be selected based on:
    - Query complexity
    - Intent type  
    - User preferences
    - Data availability
    """
    
    # Simple workflow configurations
    SIMPLE_USER_QUERY = WorkflowConfig(
        name="Simple User Query",
        complexity=WorkflowComplexity.SIMPLE,
        intent=AnalyticsIntent.USER_MANAGEMENT,
        description="Direct query for user information",
        steps=["understand_intent", "generate_query", "execute_query", "format_response"],
        max_retries=1,
        timeout_minutes=2
    )
    
    SIMPLE_COST_QUERY = WorkflowConfig(
        name="Simple Cost Query", 
        complexity=WorkflowComplexity.SIMPLE,
        intent=AnalyticsIntent.COST_ANALYSIS,
        description="Direct query for cost information",
        steps=["understand_intent", "generate_query", "execute_query", "plan_visualization", "format_response"],
        max_retries=1,
        timeout_minutes=2
    )
    
    # Complex workflow configurations
    COMPLEX_COST_ANALYSIS = WorkflowConfig(
        name="Complex Cost Analysis",
        complexity=WorkflowComplexity.COMPLEX,
        intent=AnalyticsIntent.COST_ANALYSIS,
        description="Multi-step cost analysis with trend detection and forecasting",
        steps=[
            "understand_intent", "validate_requirements", "generate_query", 
            "execute_query", "analyze_trends", "plan_visualization", 
            "generate_insights", "format_response"
        ],
        max_retries=3,
        timeout_minutes=10
    )
    
    COMPLEX_DOCUMENT_ANALYSIS = WorkflowConfig(
        name="Complex Document Analysis",
        complexity=WorkflowComplexity.COMPLEX,
        intent=AnalyticsIntent.DOCUMENT_PROCESSING,
        description="Comprehensive document processing analysis with quality assessment",
        steps=[
            "understand_intent", "identify_document_types", "generate_query",
            "execute_query", "assess_quality", "identify_issues", 
            "plan_visualization", "generate_recommendations", "format_response"
        ],
        max_retries=3,
        timeout_minutes=15
    )
    
    # Interactive workflow configurations  
    INTERACTIVE_EXPLORATION = WorkflowConfig(
        name="Interactive Data Exploration",
        complexity=WorkflowComplexity.INTERACTIVE,
        intent=AnalyticsIntent.GENERAL_QUERY,
        description="Guided data exploration with user feedback",
        steps=[
            "understand_intent", "present_options", "get_user_choice",
            "generate_query", "execute_query", "present_results",
            "ask_follow_up", "plan_visualization", "format_response"
        ],
        max_retries=2,
        timeout_minutes=20,
        requires_user_input=True
    )
    
    INTERACTIVE_COMPLIANCE_REVIEW = WorkflowConfig(
        name="Interactive Compliance Review",
        complexity=WorkflowComplexity.INTERACTIVE, 
        intent=AnalyticsIntent.COMPLIANCE_REVIEW,
        description="Step-by-step compliance review with user decisions",
        steps=[
            "understand_intent", "identify_compliance_areas", "present_findings",
            "get_user_priorities", "generate_detailed_query", "execute_query",
            "assess_compliance_status", "plan_visualization", "format_response"
        ],
        max_retries=2,
        timeout_minutes=25,
        requires_user_input=True
    )
    
    # Exploratory workflow configurations
    EXPLORATORY_PERFORMANCE = WorkflowConfig(
        name="Exploratory Performance Analysis",
        complexity=WorkflowComplexity.EXPLORATORY,
        intent=AnalyticsIntent.PERFORMANCE_ANALYSIS,
        description="Open-ended performance exploration with multiple iterations",
        steps=[
            "understand_intent", "scan_performance_metrics", "identify_patterns",
            "generate_hypotheses", "test_hypotheses", "refine_analysis",
            "plan_visualization", "format_response"
        ],
        max_retries=5,
        timeout_minutes=30
    )

class WorkflowSelector:
    """
    Intelligent workflow selector that determines the best workflow configuration
    based on query characteristics and system state
    """
    
    def __init__(self):
        self.templates = AnalyticsWorkflowTemplates()
        
    def select_workflow(
        self, 
        question: str, 
        user_context: Dict[str, Any] = None, 
        system_load: float = 0.5
    ) -> WorkflowConfig:
        """
        Select the most appropriate workflow configuration
        
        Args:
            question: User's analytics question
            user_context: Optional user preferences and history
            system_load: Current system load (0.0 to 1.0)
            
        Returns:
            Selected workflow configuration
        """
        try:
            # Analyze question complexity
            complexity = self._analyze_question_complexity(question)
            
            # Determine intent
            intent = self._determine_intent(question)
            
            # Consider system constraints
            if system_load > 0.8:
                # High load - prefer simple workflows
                complexity = WorkflowComplexity.SIMPLE
            
            # Select appropriate workflow
            workflow_config = self._get_workflow_config(intent, complexity)
            
            logger.info(f"🎯 Selected workflow: {workflow_config.name} for intent: {intent.value}")
            return workflow_config
            
        except Exception as e:
            logger.error(f"Workflow selection failed: {e}")
            # Fallback to simple user query
            return self.templates.SIMPLE_USER_QUERY
    
    def _analyze_question_complexity(self, question: str) -> WorkflowComplexity:
        """Analyze question to determine complexity level"""
        question_lower = question.lower()
        
        # Interactive indicators
        interactive_words = ['help', 'guide', 'show me options', 'what can', 'how do i']
        if any(word in question_lower for word in interactive_words):
            return WorkflowComplexity.INTERACTIVE
        
        # Complex analysis indicators
        complex_words = ['compare', 'trend', 'analyze', 'forecast', 'correlate', 'pattern']
        complex_phrases = ['over time', 'compared to', 'breakdown by', 'deep dive']
        
        complexity_score = 0
        complexity_score += sum(1 for word in complex_words if word in question_lower)
        complexity_score += sum(2 for phrase in complex_phrases if phrase in question_lower)
        
        # Multiple entities = complex
        if len(question.split(' and ')) > 1 or len(question.split(',')) > 1:
            complexity_score += 1
        
        # Question length indicates complexity
        if len(question.split()) > 15:
            complexity_score += 1
        
        # Determine complexity level
        if complexity_score >= 4:
            return WorkflowComplexity.EXPLORATORY
        elif complexity_score >= 2:
            return WorkflowComplexity.COMPLEX
        else:
            return WorkflowComplexity.SIMPLE
    
    def _determine_intent(self, question: str) -> AnalyticsIntent:
        """Determine the primary intent from the question"""
        question_lower = question.lower()
        
        # Cost analysis keywords
        cost_keywords = ['cost', 'spending', 'expense', 'budget', 'price', 'money', 'billing']
        if any(keyword in question_lower for keyword in cost_keywords):
            return AnalyticsIntent.COST_ANALYSIS
        
        # Document processing keywords
        doc_keywords = ['document', 'file', 'extraction', 'processing', 'confidence', 'accuracy']
        if any(keyword in question_lower for keyword in doc_keywords):
            return AnalyticsIntent.DOCUMENT_PROCESSING
        
        # Compliance keywords
        compliance_keywords = ['compliance', 'obligation', 'requirement', 'audit', 'regulation']
        if any(keyword in question_lower for keyword in compliance_keywords):
            return AnalyticsIntent.COMPLIANCE_REVIEW
        
        # User management keywords
        user_keywords = ['user', 'users', 'account', 'role', 'permission', 'access']
        if any(keyword in question_lower for keyword in user_keywords):
            return AnalyticsIntent.USER_MANAGEMENT
        
        # Performance keywords
        performance_keywords = ['performance', 'speed', 'efficiency', 'throughput', 'latency']
        if any(keyword in question_lower for keyword in performance_keywords):
            return AnalyticsIntent.PERFORMANCE_ANALYSIS
        
        # Default to general query
        return AnalyticsIntent.GENERAL_QUERY
    
    def _get_workflow_config(self, intent: AnalyticsIntent, complexity: WorkflowComplexity) -> WorkflowConfig:
        """Get workflow configuration based on intent and complexity"""
        
        # Map intent + complexity to specific workflows
        workflow_mapping = {
            (AnalyticsIntent.USER_MANAGEMENT, WorkflowComplexity.SIMPLE): self.templates.SIMPLE_USER_QUERY,
            (AnalyticsIntent.COST_ANALYSIS, WorkflowComplexity.SIMPLE): self.templates.SIMPLE_COST_QUERY,
            (AnalyticsIntent.COST_ANALYSIS, WorkflowComplexity.COMPLEX): self.templates.COMPLEX_COST_ANALYSIS,
            (AnalyticsIntent.DOCUMENT_PROCESSING, WorkflowComplexity.COMPLEX): self.templates.COMPLEX_DOCUMENT_ANALYSIS,
            (AnalyticsIntent.COMPLIANCE_REVIEW, WorkflowComplexity.INTERACTIVE): self.templates.INTERACTIVE_COMPLIANCE_REVIEW,
            (AnalyticsIntent.PERFORMANCE_ANALYSIS, WorkflowComplexity.EXPLORATORY): self.templates.EXPLORATORY_PERFORMANCE,
            (AnalyticsIntent.GENERAL_QUERY, WorkflowComplexity.INTERACTIVE): self.templates.INTERACTIVE_EXPLORATION,
        }
        
        # Try exact match first
        config = workflow_mapping.get((intent, complexity))
        if config:
            return config
        
        # Fallback strategies
        if complexity == WorkflowComplexity.SIMPLE:
            if intent == AnalyticsIntent.COST_ANALYSIS:
                return self.templates.SIMPLE_COST_QUERY
            else:
                return self.templates.SIMPLE_USER_QUERY
        
        elif complexity == WorkflowComplexity.COMPLEX:
            if intent == AnalyticsIntent.COST_ANALYSIS:
                return self.templates.COMPLEX_COST_ANALYSIS
            elif intent == AnalyticsIntent.DOCUMENT_PROCESSING:
                return self.templates.COMPLEX_DOCUMENT_ANALYSIS
            else:
                return self.templates.COMPLEX_COST_ANALYSIS  # Generic complex workflow
        
        elif complexity == WorkflowComplexity.INTERACTIVE:
            return self.templates.INTERACTIVE_EXPLORATION
        
        else:  # EXPLORATORY
            return self.templates.EXPLORATORY_PERFORMANCE
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of all available workflow configurations"""
        workflows = []
        
        for attr_name in dir(self.templates):
            if not attr_name.startswith('_') and attr_name.isupper():
                workflow = getattr(self.templates, attr_name)
                if isinstance(workflow, WorkflowConfig):
                    workflows.append({
                        "name": workflow.name,
                        "complexity": workflow.complexity.value,
                        "intent": workflow.intent.value,
                        "description": workflow.description,
                        "steps": workflow.steps,
                        "max_retries": workflow.max_retries,
                        "timeout_minutes": workflow.timeout_minutes,
                        "requires_user_input": workflow.requires_user_input
                    })
        
        return workflows

class WorkflowOptimizer:
    """
    Workflow optimization engine that adapts workflows based on:
    - Historical performance
    - System resources
    - User feedback
    - Success rates
    """
    
    def __init__(self, mongodb_client=None):
        self.db = mongodb_client
    
    def optimize_workflow_for_user(self, user_id: str, base_config: WorkflowConfig) -> WorkflowConfig:
        """
        Optimize workflow configuration based on user's historical performance
        
        Args:
            user_id: User identifier
            base_config: Base workflow configuration
            
        Returns:
            Optimized workflow configuration
        """
        try:
            # Get user's workflow history
            if not self.db:
                return base_config
            
            user_history = list(self.db.langgraph_checkpoints.find({
                "user_id": user_id,
                "success": True
            }).sort("last_updated", -1).limit(10))
            
            if not user_history:
                return base_config
            
            # Analyze success patterns
            successful_steps = []
            avg_execution_time = 0
            
            for workflow in user_history:
                if workflow.get('success'):
                    successful_steps.extend(workflow.get('state', {}).get('steps_completed', []))
                    # Add execution time analysis if available
            
            # Optimize based on patterns
            optimized_config = WorkflowConfig(
                name=f"Optimized {base_config.name}",
                complexity=base_config.complexity,
                intent=base_config.intent,
                description=f"User-optimized {base_config.description}",
                steps=base_config.steps,
                max_retries=max(1, base_config.max_retries - 1) if len(user_history) >= 5 else base_config.max_retries,
                timeout_minutes=base_config.timeout_minutes,
                requires_user_input=base_config.requires_user_input
            )
            
            logger.info(f"📊 Optimized workflow for user {user_id}")
            return optimized_config
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {e}")
            return base_config
    
    def get_workflow_performance_stats(self, workflow_name: str) -> Dict[str, Any]:
        """Get performance statistics for a specific workflow"""
        try:
            if not self.db:
                return {}
            
            # Query workflow performance from checkpoints
            pipeline = [
                {"$match": {"workflowType": "analytics"}},
                {"$group": {
                    "_id": "$workflowType",
                    "total_executions": {"$sum": 1},
                    "successful_executions": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "avg_execution_time": {"$avg": "$execution_time"},
                    "avg_retry_count": {"$avg": "$retry_count"}
                }}
            ]
            
            stats = list(self.db.langgraph_checkpoints.aggregate(pipeline))
            
            if stats:
                stat = stats[0]
                success_rate = stat['successful_executions'] / stat['total_executions'] * 100
                
                return {
                    "workflow_name": workflow_name,
                    "total_executions": stat['total_executions'],
                    "success_rate": round(success_rate, 2),
                    "avg_execution_time": round(stat.get('avg_execution_time', 0), 2),
                    "avg_retry_count": round(stat.get('avg_retry_count', 0), 2)
                }
            
            return {"workflow_name": workflow_name, "no_data": True}
            
        except Exception as e:
            logger.error(f"Failed to get workflow performance stats: {e}")
            return {"error": str(e)}