import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from config import DATABASE_SCHEMA  # Import the new schema

logger = logging.getLogger(__name__)

@dataclass
class AnalyticsResult:
    """Complete analytics result with all stages"""
    success: bool
    query_data: Dict[str, Any]
    raw_results: List[Dict]
    visualization: Dict[str, Any]
    execution_time: float
    total_attempts: int
    error: Optional[str] = None
    stage_details: Dict[str, Any] = None

class TwoStageAnalyticsProcessor:
    """
    Main processor that orchestrates the two-stage Gemini analysis
    Enhanced for GenAI database with document intelligence and AI operations
    """
    
    def __init__(self, gemini_client, database_manager):
        self.gemini_client = gemini_client
        self.db_manager = database_manager
        self.schema_info = self._load_schema_info()
        
    def _load_schema_info(self) -> Dict:
        """Load comprehensive schema information from config"""
        # Load the complete schema from config.py
        schema_data = DATABASE_SCHEMA.copy()
        
        # Enhance with additional metadata for AI processing
        enhanced_schema = {
            "collections": schema_data["collections"],
            "database_type": "genai_operations",
            "domain": "AI Operations & Document Intelligence",
            "common_queries": {
                "ai_operations": "Cost tracking, model performance, token usage analysis",
                "document_processing": "Extraction results, batch processing, confidence analysis", 
                "compliance": "Legal obligations, risk assessment, compliance tracking",
                "user_analytics": "Activity tracking, performance metrics, engagement analysis",
                "cross_collection": "Complex relationship analysis across workflow pipeline",
                "temporal": "Time-based trends, processing patterns, cost evolution",
                "efficiency": "ROI analysis, performance optimization, resource utilization"
            },
            "analysis_types": {
                "cost_analysis": "AI spending, cost per extraction, model efficiency",
                "performance": "Processing times, success rates, confidence scores",
                "compliance": "Risk assessment, obligation tracking, regulatory analysis",
                "operational": "Batch processing, workflow efficiency, user productivity",
                "content": "Document types, extraction quality, text analysis"
            },
            "key_relationships": {
                "cost_flow": "users → batches → documentextractions → costevalutionforllm",
                "document_pipeline": "files → documentextractions → obligationextractions → obligationmappings",
                "ai_workflow": "prompts → documentmappings → extractions → compliance",
                "user_journey": "users → conversations → batches → results"
            }
        }
        
        return enhanced_schema
        
    async def process_question(self, user_question: str, context: Dict = None) -> AnalyticsResult:
        """
        Process analytics question using two-stage Gemini approach
        Enhanced for AI operations and document intelligence domain
        """
        start_time = datetime.now()
        total_attempts = 0
        stage_details = {"stage_1": {}, "stage_2": {}}
        
        try:
            logger.info(f"🎯 Processing GenAI Analytics Question: {user_question}")
            
            # STAGE 1: Generate MongoDB Query
            logger.info("📊 Stage 1: Generating MongoDB aggregation pipeline...")
            stage_1_result = await self._stage_1_generate_query(user_question, context)
            total_attempts += stage_1_result.get("attempts", 0)
            stage_details["stage_1"] = stage_1_result
            
            if not stage_1_result.get("success"):
                logger.warning("⚠️ Stage 1 failed, attempting fallback...")
                return await self._fallback_processing(user_question, stage_details, total_attempts)
            
            # STAGE 2: Execute Query and Generate Insights
            logger.info("🧠 Stage 2: Executing query and generating insights...")
            query_data = stage_1_result["query_data"]
            raw_results = await self._execute_database_query(query_data)
            
            if not raw_results:
                logger.warning("⚠️ No data found, generating informative response...")
                return await self._handle_no_data_response(user_question, query_data, stage_details, total_attempts)
            
            # Generate AI-powered insights and visualization
            stage_2_result = await self._stage_2_generate_insights(
                user_question, query_data, raw_results, context
            )
            total_attempts += stage_2_result.get("attempts", 0)
            stage_details["stage_2"] = stage_2_result
            
            if not stage_2_result.get("success"):
                logger.warning("⚠️ Stage 2 failed, creating fallback visualization...")
                visualization = self._create_fallback_visualization(raw_results, query_data)
            else:
                visualization = stage_2_result["visualization"]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ GenAI Analytics processing completed in {execution_time:.2f}s")
            
            return AnalyticsResult(
                success=True,
                query_data=query_data,
                raw_results=raw_results,
                visualization=visualization,
                execution_time=execution_time,
                total_attempts=total_attempts,
                stage_details=stage_details
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ GenAI Analytics processing failed: {str(e)}")
            
            return AnalyticsResult(
                success=False,
                query_data={},
                raw_results=[],
                visualization={},
                execution_time=execution_time,
                total_attempts=total_attempts,
                error=str(e),
                stage_details=stage_details
            )

    async def _stage_1_generate_query(self, user_question: str, context: Dict = None) -> Dict:
        """
        Stage 1: Generate MongoDB aggregation pipeline for GenAI operations
        """
        try:
            # Enhanced context for AI operations domain
            enhanced_context = {
                "domain": "AI Operations & Document Intelligence",
                "question": user_question,
                "available_collections": list(self.schema_info["collections"].keys()),
                "key_analysis_types": [
                    "AI cost analysis", "document processing metrics", 
                    "compliance tracking", "agent performance", "batch efficiency"
                ],
                "sample_questions": [
                    "What's our AI spending this month?",
                    "Show me document extraction confidence scores",
                    "Which compliance obligations need attention?",
                    "Compare agent performance across document types"
                ]
            }
            
            if context:
                enhanced_context.update(context)
            
            # Call your existing Gemini client for query generation
            query_result = await self.gemini_client.generate_query(
                user_question, 
                self.schema_info, 
                enhanced_context
            )
            
            return {
                "success": query_result.get("success", False),
                "query_data": query_result.get("query_data", {}),
                "attempts": query_result.get("attempts", 0),
                "reasoning": query_result.get("reasoning", "")
            }
            
        except Exception as e:
            logger.error(f"Stage 1 error: {str(e)}")
            return {"success": False, "error": str(e), "attempts": 1}

    async def _stage_2_generate_insights(self, user_question: str, query_data: Dict, 
                                       raw_results: List[Dict], context: Dict = None) -> Dict:
        """
        Stage 2: Generate insights and visualization for AI operations data
        """
        try:
            # Enhanced context for AI operations insights
            insight_context = {
                "domain": "AI Operations & Document Intelligence",
                "data_type": query_data.get("collection", "unknown"),
                "result_count": len(raw_results),
                "analysis_focus": self._determine_analysis_focus(user_question, query_data),
                "business_context": {
                    "cost_optimization": "AI spending efficiency and ROI",
                    "quality_assurance": "Document extraction accuracy and confidence",
                    "compliance_management": "Legal obligation tracking and risk assessment",
                    "operational_efficiency": "Processing times and batch success rates"
                }
            }
            
            if context:
                insight_context.update(context)
            
            # Call your existing Gemini client for insight generation
            insights_result = await self.gemini_client.generate_insights(
                user_question,
                query_data,
                raw_results,
                insight_context
            )
            
            return {
                "success": insights_result.get("success", False),
                "visualization": insights_result.get("visualization", {}),
                "attempts": insights_result.get("attempts", 0),
                "insights": insights_result.get("insights", [])
            }
            
        except Exception as e:
            logger.error(f"Stage 2 error: {str(e)}")
            return {"success": False, "error": str(e), "attempts": 1}

    def _determine_analysis_focus(self, user_question: str, query_data: Dict) -> str:
        """Determine the primary analysis focus for better insights"""
        question_lower = user_question.lower()
        collection = query_data.get("collection", "")
        
        # AI Operations focus
        if any(keyword in question_lower for keyword in ["cost", "spending", "price", "expensive"]):
            return "cost_analysis"
        elif any(keyword in question_lower for keyword in ["performance", "speed", "time", "efficiency"]):
            return "performance_analysis"
        elif any(keyword in question_lower for keyword in ["compliance", "obligation", "legal", "risk"]):
            return "compliance_analysis"
        elif any(keyword in question_lower for keyword in ["confidence", "accuracy", "quality", "extraction"]):
            return "quality_analysis"
        elif any(keyword in question_lower for keyword in ["user", "activity", "engagement", "usage"]):
            return "user_analysis"
        elif collection in ["costevalutionforllm", "llmpricing"]:
            return "cost_analysis"
        elif collection in ["documentextractions", "obligationextractions"]:
            return "content_analysis"
        elif collection in ["batches", "agent_activity"]:
            return "operational_analysis"
        else:
            return "general_analysis"

    async def _execute_database_query(self, query_data: Dict) -> List[Dict]:
        """
        Execute the MongoDB query generated by Stage 1 - Enhanced for GenAI collections
        """
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            logger.info(f"📊 Executing query on GenAI collection: {collection_name}")
            logger.info(f"   Pipeline stages: {len(pipeline)}")
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return []
            
            # Check database connection
            if not self.db_manager.is_connected():
                logger.error("Database is not connected")
                return []
            
            # Get the collection
            collection = self.db_manager.get_collection(collection_name)
            if collection is None:
                logger.error(f"Failed to get collection: {collection_name}")
                return []
            
            # Test collection availability
            doc_count = collection.count_documents({})
            logger.info(f"   Collection {collection_name} has {doc_count} total documents")
            
            if doc_count == 0:
                logger.warning(f"Collection {collection_name} is empty!")
                return []
            
            # Execute the aggregation pipeline
            results = list(collection.aggregate(pipeline))
            
            # Clean results for JSON serialization
            cleaned_results = []
            for result in results:
                cleaned_result = self._clean_mongodb_result(result)
                cleaned_results.append(cleaned_result)
            
            logger.info(f"   ✅ Query executed successfully: {len(cleaned_results)} results")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {str(e)}")
            logger.error(f"Collection: {query_data.get('collection')}")
            logger.error(f"Pipeline: {query_data.get('pipeline')}")
            return []

    def _clean_mongodb_result(self, result: Dict) -> Dict:
        """Clean MongoDB result by converting ObjectIds and dates to strings"""
        from bson import ObjectId
        
        cleaned = {}
        for key, value in result.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_mongodb_result(value)
            elif isinstance(value, list):
                cleaned[key] = [self._clean_mongodb_result(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        return cleaned

    async def _fallback_processing(self, user_question: str, stage_details: Dict, total_attempts: int) -> AnalyticsResult:
        """Enhanced fallback processing for GenAI operations"""
        try:
            logger.info("🔄 Using GenAI-aware fallback processing...")
            
            # Determine likely collection based on question keywords
            collection_name = self._guess_collection_from_question(user_question)
            
            if collection_name:
                # Create simple aggregation for the guessed collection
                simple_pipeline = [
                    {"$limit": 10},
                    {"$sort": {"_id": -1}}
                ]
                
                query_data = {
                    "collection": collection_name,
                    "pipeline": simple_pipeline,
                    "chart_hint": "bar"
                }
                
                raw_results = await self._execute_database_query(query_data)
                
                if raw_results:
                    visualization = self._create_fallback_visualization(raw_results, query_data)
                    
                    return AnalyticsResult(
                        success=True,
                        query_data=query_data,
                        raw_results=raw_results,
                        visualization=visualization,
                        execution_time=0.5,
                        total_attempts=total_attempts,
                        stage_details=stage_details
                    )
            
            # If all else fails, return helpful message about available data
            return AnalyticsResult(
                success=True,
                query_data={"collection": "system_info"},
                raw_results=[],
                visualization=self._create_help_visualization(),
                execution_time=0.1,
                total_attempts=total_attempts,
                stage_details=stage_details
            )
            
        except Exception as e:
            logger.error(f"Fallback processing failed: {str(e)}")
            return AnalyticsResult(
                success=False,
                query_data={},
                raw_results=[],
                visualization={},
                execution_time=0.1,
                total_attempts=total_attempts,
                error=f"Fallback failed: {str(e)}",
                stage_details=stage_details
            )

    def _guess_collection_from_question(self, user_question: str) -> Optional[str]:
        """Guess the most relevant collection based on question keywords"""
        question_lower = user_question.lower()
        
        # AI Operations keywords
        if any(keyword in question_lower for keyword in ["cost", "spending", "token", "price"]):
            return "costevalutionforllm"
        elif any(keyword in question_lower for keyword in ["document", "extraction", "confidence"]):
            return "documentextractions"
        elif any(keyword in question_lower for keyword in ["obligation", "compliance", "legal"]):
            return "obligationextractions"
        elif any(keyword in question_lower for keyword in ["batch", "processing", "job"]):
            return "batches"
        elif any(keyword in question_lower for keyword in ["agent", "performance", "activity"]):
            return "agent_activity"
        elif any(keyword in question_lower for keyword in ["user", "people", "who"]):
            return "users"
        elif any(keyword in question_lower for keyword in ["conversation", "chat", "message"]):
            return "conversations"
        elif any(keyword in question_lower for keyword in ["file", "upload", "storage"]):
            return "files"
        elif any(keyword in question_lower for keyword in ["prompt", "template", "ai"]):
            return "prompts"
        
        # Default to most data-rich collection
        return "documentextractions"

    def _create_fallback_visualization(self, raw_results: List[Dict], query_data: Dict) -> Dict:
        """Create fallback visualization for GenAI data"""
        if not raw_results:
            return self._create_help_visualization()
        
        # Determine chart type based on data structure
        first_result = raw_results[0]
        chart_type = "bar"
        
        # Look for numeric fields to determine best visualization
        numeric_fields = []
        for key, value in first_result.items():
            if isinstance(value, (int, float)) and key != "_id":
                numeric_fields.append(key)
        
        if len(numeric_fields) > 0:
            chart_type = "bar" if len(raw_results) > 1 else "pie"
        
        # Create appropriate chart data
        labels = []
        data = []
        
        for i, result in enumerate(raw_results[:10]):  # Limit to 10 items
            # Create label from available data
            label = self._create_label_from_result(result)
            labels.append(label)
            
            # Get numeric value
            if numeric_fields:
                data.append(result.get(numeric_fields[0], 0))
            else:
                data.append(i + 1)
        
        return {
            "chart_type": chart_type,
            "chart_config": {
                "type": chart_type,
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": f"{query_data.get('collection', 'Data')} Analysis",
                        "data": data,
                        "backgroundColor": self._get_colors(len(data)),
                        "borderColor": "#3B82F6",
                        "borderWidth": 2
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {"display": True, "text": f"GenAI Analytics: {query_data.get('collection', 'Data')}"},
                        "legend": {"display": chart_type in ["pie", "doughnut"]}
                    }
                }
            },
            "summary": f"Showing {len(raw_results)} results from {query_data.get('collection', 'database')}",
            "insights": [
                f"Found {len(raw_results)} records in the {query_data.get('collection', 'selected')} collection",
                f"Data includes {len(numeric_fields)} numeric fields for analysis"
            ],
            "recommendations": [
                "Try asking more specific questions about costs, document processing, or compliance",
                "Use time-based queries to see trends in your AI operations"
            ]
        }

    def _create_label_from_result(self, result: Dict) -> str:
        """Create a meaningful label from a database result"""
        # Priority order for label fields
        label_fields = [
            "name", "Name", "title", "promptName", "Agent", 
            "Type", "category", "status", "collection", "_id"
        ]
        
        for field in label_fields:
            if field in result and result[field]:
                value = str(result[field])
                return value[:30] + "..." if len(value) > 30 else value
        
        return f"Item {result.get('_id', 'Unknown')}"

    def _create_help_visualization(self) -> Dict:
        """Create help visualization showing available GenAI collections"""
        collections = list(self.schema_info["collections"].keys())
        doc_counts = [100] * len(collections)  # Placeholder values
        
        return {
            "chart_type": "bar",
            "chart_config": {
                "type": "bar",
                "data": {
                    "labels": collections[:10],  # Show top 10 collections
                    "datasets": [{
                        "label": "Available Collections",
                        "data": doc_counts[:10],
                        "backgroundColor": self._get_colors(len(collections[:10])),
                        "borderColor": "#3B82F6",
                        "borderWidth": 2
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "title": {"display": True, "text": "GenAI Database Collections"},
                        "legend": {"display": False}
                    },
                    "scales": {
                        "y": {"beginAtZero": True},
                        "x": {"display": True}
                    }
                }
            },
            "summary": "Your GenAI database contains AI operations and document intelligence data",
            "insights": [
                f"Database contains {len(collections)} collections for AI operations analysis",
                "Primary focus areas: AI costs, document processing, compliance tracking",
                "Rich data available for operational insights and optimization"
            ],
            "recommendations": [
                "Ask about AI spending: 'What's our AI costs this month?'",
                "Explore document processing: 'Show me extraction confidence scores'",
                "Check compliance: 'What are our critical obligations?'",
                "Analyze performance: 'Which agents perform best?'"
            ]
        }

    def _get_colors(self, count: int) -> List[str]:
        """Get a list of colors for charts"""
        colors = [
            "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
            "#06B6D4", "#F97316", "#84CC16", "#EC4899", "#6366F1"
        ]
        return (colors * ((count // len(colors)) + 1))[:count]

    async def _handle_no_data_response(self, user_question: str, query_data: Dict, 
                                     stage_details: Dict, total_attempts: int) -> AnalyticsResult:
        """Handle cases where no data is found"""
        collection_name = query_data.get("collection", "unknown")
        
        return AnalyticsResult(
            success=True,
            query_data=query_data,
            raw_results=[],
            visualization={
                "chart_type": "info",
                "summary": f"No data found in {collection_name} for your query",
                "insights": [
                    f"The {collection_name} collection may be empty or your filter criteria didn't match any records",
                    "Try broadening your search criteria or asking about a different collection"
                ],
                "recommendations": [
                    "Check available collections with: 'What collections do we have?'",
                    "Ask about overall system status: 'Show me system overview'",
                    "Try different time ranges or criteria"
                ]
            },
            execution_time=0.1,
            total_attempts=total_attempts,
            stage_details=stage_details
        )


class ConversationManager:
    """
    Manages conversation state and context for multi-turn analytics
    Enhanced for GenAI operations domain
    """
    
    def __init__(self, analytics_processor):
        self.analytics_processor = analytics_processor
        self.conversation_history = []
        self.session_context = {}
    
    async def process_conversational_question(self, user_question: str) -> AnalyticsResult:
        """
        Process a question with full conversation context for AI operations
        """
        # Build context from previous interactions
        context = self.analytics_processor.get_conversation_context(self.conversation_history)
        
        # Add current session context
        enhanced_context = {
            **context,
            **self.session_context,
            "conversation_turn": len(self.conversation_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "domain": "AI Operations & Document Intelligence"
        }
        
        # Process the question
        result = await self.analytics_processor.process_question(user_question, enhanced_context)
        
        # Store in conversation history
        self.conversation_history.append(result)
        
        # Update session context based on result
        if result.success and result.query_data:
            self.session_context.update({
                "last_collection": result.query_data.get("collection"),
                "last_analysis_type": self._determine_analysis_type(user_question),
                "last_successful_query": user_question
            })
        
        return result
    
    def _determine_analysis_type(self, question: str) -> str:
        """Determine the type of analysis being performed"""
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ["cost", "spending", "price"]):
            return "cost_analysis"
        elif any(keyword in question_lower for keyword in ["document", "extraction"]):
            return "document_analysis"
        elif any(keyword in question_lower for keyword in ["compliance", "obligation"]):
            return "compliance_analysis"
        elif any(keyword in question_lower for keyword in ["performance", "agent"]):
            return "performance_analysis"
        else:
            return "general_analysis"
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of the conversation session"""
        if not self.conversation_history:
            return {"total_queries": 0}
        
        successful_queries = [r for r in self.conversation_history if r.success]
        failed_queries = [r for r in self.conversation_history if not r.success]
        
        total_execution_time = sum(r.execution_time for r in self.conversation_history)
        total_attempts = sum(r.total_attempts for r in self.conversation_history)
        
        collections_used = set()
        analysis_types_used = set()
        
        for result in successful_queries:
            if result.query_data:
                collections_used.add(result.query_data.get("collection", ""))
                
        return {
            "total_queries": len(self.conversation_history),
            "successful_queries": len(successful_queries),
            "failed_queries": len(failed_queries),
            "success_rate": len(successful_queries) / len(self.conversation_history) * 100,
            "total_execution_time": round(total_execution_time, 2),
            "average_execution_time": round(total_execution_time / len(self.conversation_history), 2),
            "total_ai_attempts": total_attempts,
            "average_attempts_per_query": round(total_attempts / len(self.conversation_history), 1),
            "collections_explored": list(collections_used),
            "session_context": self.session_context
        }
    
    def reset_conversation(self):
        """Reset the conversation history and context"""
        self.conversation_history = []
        self.session_context = {}
        logger.info("🔄 Conversation history reset for new GenAI session")


class PerformanceMonitor:
    """
    Monitor and track performance metrics for the GenAI two-stage system
    """
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "stage_1_failures": 0,
            "stage_2_failures": 0,
            "total_execution_time": 0.0,
            "total_ai_attempts": 0,
            "collections_queried": {},
            "analysis_types": {},
            "gemini_reliability": {
                "stage_1": {"attempts": 0, "successes": 0},
                "stage_2": {"attempts": 0, "successes": 0}
            }
        }
    
    def record_result(self, result: AnalyticsResult):
        """Record metrics from a processing result"""
        self.metrics["total_requests"] += 1
        
        if result.success:
            self.metrics["successful_requests"] += 1
        
        self.metrics["total_execution_time"] += result.execution_time
        self.metrics["total_ai_attempts"] += result.total_attempts
        
        # Track collection usage
        if result.query_data and "collection" in result.query_data:
            collection = result.query_data["collection"]
            self.metrics["collections_queried"][collection] = \
                self.metrics["collections_queried"].get(collection, 0) + 1
        
        # Record stage-specific metrics
        if result.stage_details:
            if "stage_1" in result.stage_details:
                stage_1 = result.stage_details["stage_1"]
                self.metrics["gemini_reliability"]["stage_1"]["attempts"] += stage_1.get("attempts", 0)
                if stage_1.get("success"):
                    self.metrics["gemini_reliability"]["stage_1"]["successes"] += 1
                else:
                    self.metrics["stage_1_failures"] += 1
            
            if "stage_2" in result.stage_details:
                stage_2 = result.stage_details["stage_2"]
                self.metrics["gemini_reliability"]["stage_2"]["attempts"] += stage_2.get("attempts", 0)
                if stage_2.get("success"):
                    self.metrics["gemini_reliability"]["stage_2"]["successes"] += 1
                else:
                    self.metrics["stage_2_failures"] += 1
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        if self.metrics["total_requests"] == 0:
            return {"status": "No requests processed yet"}
        
        # Calculate reliability percentages
        stage_1_reliability = 0
        stage_2_reliability = 0
        
        if self.metrics["gemini_reliability"]["stage_1"]["attempts"] > 0:
            stage_1_reliability = (
                self.metrics["gemini_reliability"]["stage_1"]["successes"] /
                self.metrics["gemini_reliability"]["stage_1"]["attempts"] * 100
            )
        
        if self.metrics["gemini_reliability"]["stage_2"]["attempts"] > 0:
            stage_2_reliability = (
                self.metrics["gemini_reliability"]["stage_2"]["successes"] /
                self.metrics["gemini_reliability"]["stage_2"]["attempts"] * 100
            )
        
        return {
            "overview": {
                "total_requests": self.metrics["total_requests"],
                "success_rate": (self.metrics["successful_requests"] / self.metrics["total_requests"]) * 100,
                "average_execution_time": self.metrics["total_execution_time"] / self.metrics["total_requests"],
                "total_ai_attempts": self.metrics["total_ai_attempts"]
            },
            "stage_performance": {
                "stage_1_reliability": round(stage_1_reliability, 2),
                "stage_2_reliability": round(stage_2_reliability, 2),
                "stage_1_failures": self.metrics["stage_1_failures"],
                "stage_2_failures": self.metrics["stage_2_failures"]
            },
            "collection_usage": self.metrics["collections_queried"],
            "analysis_types": self.metrics["analysis_types"],
            "recommendations": self._generate_performance_recommendations(stage_1_reliability, stage_2_reliability)
        }
    
    def _generate_performance_recommendations(self, stage_1_reliability: float, stage_2_reliability: float) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if stage_1_reliability < 80:
            recommendations.append("Consider refining query generation prompts for better Stage 1 reliability")
        
        if stage_2_reliability < 80:
            recommendations.append("Optimize insight generation prompts for improved Stage 2 performance")
        
        if self.metrics["total_ai_attempts"] / self.metrics["total_requests"] > 3:
            recommendations.append("High retry rate detected - consider prompt optimization")
        
        if len(recommendations) == 0:
            recommendations.append("System performing well - no immediate optimizations needed")
        
        return recommendations
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "stage_1_failures": 0,
            "stage_2_failures": 0,
            "total_execution_time": 0.0,
            "total_ai_attempts": 0,
            "collections_queried": {},
            "analysis_types": {},
            "gemini_reliability": {
                "stage_1": {"attempts": 0, "successes": 0},
                "stage_2": {"attempts": 0, "successes": 0}
            }
        }
        logger.info("🔄 Performance metrics reset")


# Simple processor for fallback when Gemini is not available
class SimpleAnalyticsProcessor:
    """
    Simple fallback processor for when Gemini AI is not available
    Enhanced for GenAI database operations
    """
    
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.schema_info = DATABASE_SCHEMA["collections"]
    
    def process_question(self, user_question: str) -> AnalyticsResult:
        """
        Process question using pattern matching for GenAI operations
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔄 Simple processing GenAI question: {user_question}")
            
            # Determine collection and create basic query
            collection_name = self._determine_collection(user_question)
            pipeline = self._create_simple_pipeline(user_question, collection_name)
            
            query_data = {
                "collection": collection_name,
                "pipeline": pipeline,
                "chart_hint": self._suggest_chart_type(user_question)
            }
            
            # Execute query
            raw_results = self._execute_simple_query(query_data)
            
            # Create visualization
            visualization = self._create_simple_visualization(raw_results, query_data, user_question)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AnalyticsResult(
                success=True,
                query_data=query_data,
                raw_results=raw_results,
                visualization=visualization,
                execution_time=execution_time,
                total_attempts=1
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Simple processing failed: {str(e)}")
            
            return AnalyticsResult(
                success=False,
                query_data={},
                raw_results=[],
                visualization={},
                execution_time=execution_time,
                total_attempts=1,
                error=str(e)
            )
    
    def _determine_collection(self, user_question: str) -> str:
        """Determine the best collection based on question keywords"""
        question_lower = user_question.lower()
        
        # GenAI-specific collection mapping
        if any(keyword in question_lower for keyword in ["cost", "spending", "token", "price", "expensive"]):
            return "costevalutionforllm"
        elif any(keyword in question_lower for keyword in ["document", "extraction", "confidence", "extract"]):
            return "documentextractions"
        elif any(keyword in question_lower for keyword in ["obligation", "compliance", "legal", "risk"]):
            return "obligationextractions"
        elif any(keyword in question_lower for keyword in ["batch", "processing", "job", "process"]):
            return "batches"
        elif any(keyword in question_lower for keyword in ["agent", "performance", "activity", "success"]):
            return "agent_activity"
        elif any(keyword in question_lower for keyword in ["user", "people", "who", "person"]):
            return "users"
        elif any(keyword in question_lower for keyword in ["conversation", "chat", "message", "talk"]):
            return "conversations"
        elif any(keyword in question_lower for keyword in ["file", "upload", "storage", "document"]):
            return "files"
        elif any(keyword in question_lower for keyword in ["prompt", "template", "ai", "model"]):
            return "prompts"
        else:
            # Default to the most data-rich collection
            return "documentextractions"
    
    def _create_simple_pipeline(self, user_question: str, collection_name: str) -> List[Dict]:
        """Create a simple aggregation pipeline"""
        question_lower = user_question.lower()
        pipeline = []
        
        # Add match stage for common filters
        match_stage = {}
        
        if "today" in question_lower:
            match_stage["createdAt"] = {"$gte": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)}
        elif "week" in question_lower:
            week_ago = datetime.now() - timedelta(days=7)
            match_stage["createdAt"] = {"$gte": week_ago}
        elif "month" in question_lower:
            month_ago = datetime.now() - timedelta(days=30)
            match_stage["createdAt"] = {"$gte": month_ago}
        
        if match_stage:
            pipeline.append({"$match": match_stage})
        
        # Add grouping for aggregation questions
        if any(keyword in question_lower for keyword in ["count", "total", "sum", "average", "group"]):
            group_field = self._determine_group_field(collection_name, question_lower)
            if group_field:
                pipeline.append({
                    "$group": {
                        "_id": f"${group_field}",
                        "count": {"$sum": 1}
                    }
                })
                pipeline.append({"$sort": {"count": -1}})
        
        # Add sort and limit
        if not any("$group" in stage for stage in pipeline):
            sort_field = self._determine_sort_field(collection_name, question_lower)
            pipeline.append({"$sort": {sort_field: -1}})
        
        pipeline.append({"$limit": 15})
        
        return pipeline
    
    def _determine_group_field(self, collection_name: str, question_lower: str) -> str:
        """Determine the field to group by"""
        collection_schema = self.schema_info.get(collection_name, {})
        group_by_fields = collection_schema.get("group_by_fields", [])
        
        if not group_by_fields:
            return None
        
        # Choose group field based on question context
        if "type" in question_lower and "Type" in group_by_fields:
            return "Type"
        elif "status" in question_lower and "status" in group_by_fields:
            return "status"
        elif "user" in question_lower and any("user" in field.lower() for field in group_by_fields):
            return next(field for field in group_by_fields if "user" in field.lower())
        else:
            return group_by_fields[0]  # Default to first available
    
    def _determine_sort_field(self, collection_name: str, question_lower: str) -> str:
        """Determine the field to sort by"""
        collection_schema = self.schema_info.get(collection_name, {})
        date_fields = collection_schema.get("date_fields", [])
        
        if date_fields:
            return date_fields[0]  # Sort by first date field
        else:
            return "_id"  # Default sort
    
    def _suggest_chart_type(self, user_question: str) -> str:
        """Suggest appropriate chart type based on question"""
        question_lower = user_question.lower()
        
        if any(keyword in question_lower for keyword in ["trend", "over time", "timeline", "history"]):
            return "line"
        elif any(keyword in question_lower for keyword in ["distribution", "breakdown", "percentage", "share"]):
            return "pie"
        elif any(keyword in question_lower for keyword in ["compare", "vs", "versus", "top", "ranking"]):
            return "bar"
        else:
            return "bar"  # Default
    
    def _execute_simple_query(self, query_data: Dict) -> List[Dict]:
        """Execute the simple query"""
        try:
            collection_name = query_data["collection"]
            pipeline = query_data["pipeline"]
            
            if not self.db_manager.is_connected():
                return []
            
            collection = self.db_manager.get_collection(collection_name)
            if not collection:
                return []
            
            results = list(collection.aggregate(pipeline))
            
            # Clean results
            cleaned_results = []
            for result in results:
                cleaned_result = {}
                for key, value in result.items():
                    if hasattr(value, 'isoformat'):  # datetime
                        cleaned_result[key] = value.isoformat()
                    else:
                        cleaned_result[key] = str(value) if hasattr(value, '__str__') else value
                cleaned_results.append(cleaned_result)
            
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Simple query execution failed: {str(e)}")
            return []
    
    def _create_simple_visualization(self, raw_results: List[Dict], query_data: Dict, user_question: str) -> Dict:
        """Create simple visualization for the results"""
        if not raw_results:
            return {
                "chart_type": "info",
                "summary": f"No data found for your query about {query_data['collection']}",
                "insights": ["The collection may be empty or your criteria didn't match any records"],
                "recommendations": ["Try a broader search or check a different collection"]
            }
        
        chart_type = query_data.get("chart_hint", "bar")
        collection_name = query_data["collection"]
        
        # Prepare chart data
        labels = []
        data = []
        
        for result in raw_results[:10]:
            # Create label
            if "_id" in result and result["_id"]:
                labels.append(str(result["_id"])[:20])
            else:
                labels.append(f"Item {len(labels) + 1}")
            
            # Get data value
            if "count" in result:
                data.append(result["count"])
            else:
                # Find first numeric field
                numeric_value = 1
                for key, value in result.items():
                    if isinstance(value, (int, float)) and key != "_id":
                        numeric_value = value
                        break
                data.append(numeric_value)
        
        # Create chart configuration
        chart_config = {
            "type": chart_type,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": f"{collection_name.title()} Data",
                    "data": data,
                    "backgroundColor": [
                        "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
                        "#06B6D4", "#F97316", "#84CC16", "#EC4899", "#6366F1"
                    ][:len(data)],
                    "borderColor": "#3B82F6",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": f"GenAI Analytics: {collection_name.title()}"},
                    "legend": {"display": chart_type in ["pie", "doughnut"]}
                }
            }
        }
        
        if chart_type not in ["pie", "doughnut"]:
            chart_config["options"]["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
        
        # Generate insights
        insights = [
            f"Found {len(raw_results)} records in the {collection_name} collection",
            f"Showing top {min(len(raw_results), 10)} results"
        ]
        
        if data:
            total = sum(data)
            average = total / len(data)
            insights.append(f"Total value: {total}, Average: {average:.2f}")
        
        return {
            "chart_type": chart_type,
            "chart_config": chart_config,
            "summary": f"Analysis of {collection_name} data shows {len(raw_results)} results",
            "insights": insights,
            "recommendations": [
                "For more detailed analysis, try asking about specific time periods",
                "Use AI-powered queries for deeper insights and trends",
                "Ask about relationships between different data collections"
            ]
        }