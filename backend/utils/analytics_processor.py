import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
    """
    
    def __init__(self, gemini_client, database_manager):
        self.gemini_client = gemini_client
        self.db_manager = database_manager
        self.schema_info = self._load_schema_info()
        
    def _load_schema_info(self) -> Dict:
        """Load comprehensive schema information"""
        return {
            "collections": {
                "sales": {
                    "description": "Sales transaction records",
                    "fields": [
                        "order_id", "customer_id", "product_id", "product_name", 
                        "category", "quantity", "unit_price", "total_amount", 
                        "discount", "date", "month", "quarter", "sales_rep", "region"
                    ],
                    "field_types": {
                        "order_id": "string",
                        "customer_id": "string", 
                        "product_name": "string",
                        "category": "string",
                        "quantity": "number",
                        "unit_price": "number",
                        "total_amount": "number",
                        "date": "date",
                        "month": "string",
                        "quarter": "string",
                        "region": "string"
                    },
                    "sample_values": {
                        "category": ["Smartphones", "Laptops", "Audio", "Tablets", "Accessories", "Monitors"],
                        "region": ["North America", "Europe", "Asia-Pacific"],
                        "month": ["January", "February", "March", "April", "May", "June", "July"]
                    },
                    "relationships": {
                        "customer_id": "customers.customer_id",
                        "product_id": "products.product_id"
                    },
                    "indexes": ["category", "region", "date", "customer_id"],
                    "data_range": "January 2024 - July 2024"
                },
                "products": {
                    "description": "Product catalog and inventory",
                    "fields": [
                        "product_id", "name", "category", "brand", "price", 
                        "cost", "stock", "rating", "reviews_count", "launch_date"
                    ],
                    "field_types": {
                        "product_id": "string",
                        "name": "string",
                        "category": "string", 
                        "brand": "string",
                        "price": "number",
                        "cost": "number",
                        "stock": "number",
                        "rating": "number",
                        "reviews_count": "number",
                        "launch_date": "date"
                    },
                    "relationships": {
                        "product_id": "sales.product_id"
                    }
                },
                "customers": {
                    "description": "Customer information and profiles",
                    "fields": [
                        "customer_id", "name", "email", "age", "gender", 
                        "country", "state", "city", "customer_segment", 
                        "total_spent", "order_count", "signup_date", "last_purchase"
                    ],
                    "field_types": {
                        "customer_id": "string",
                        "name": "string",
                        "email": "string",
                        "age": "number",
                        "gender": "string",
                        "country": "string",
                        "state": "string", 
                        "city": "string",
                        "customer_segment": "string",
                        "total_spent": "number",
                        "order_count": "number",
                        "signup_date": "date",
                        "last_purchase": "date"
                    },
                    "sample_values": {
                        "customer_segment": ["Regular", "Premium", "VIP"],
                        "gender": ["Male", "Female", "Other"]
                    },
                    "relationships": {
                        "customer_id": "sales.customer_id"
                    }
                },
                "marketing_campaigns": {
                    "description": "Marketing campaign performance data",
                    "fields": [
                        "campaign_id", "name", "type", "start_date", "end_date", 
                        "budget", "spent", "impressions", "clicks", "conversions", 
                        "revenue_generated", "target_audience", "ctr", "conversion_rate"
                    ],
                    "field_types": {
                        "campaign_id": "string",
                        "name": "string",
                        "type": "string",
                        "start_date": "date",
                        "end_date": "date",
                        "budget": "number",
                        "spent": "number",
                        "impressions": "number",
                        "clicks": "number",
                        "conversions": "number",
                        "revenue_generated": "number",
                        "ctr": "number",
                        "conversion_rate": "number"
                    },
                    "sample_values": {
                        "type": ["Email", "Google Ads", "Social Media", "Influencer", "Display Ads"]
                    }
                }
            },
            "common_queries": {
                "comparisons": "Compare categories, regions, time periods",
                "rankings": "Top/bottom performers, best/worst metrics",
                "trends": "Changes over time, growth patterns, seasonality",
                "distributions": "Market share, percentage breakdowns",
                "correlations": "Relationships between metrics",
                "segments": "Customer groups, product categories, regional analysis"
            }
        }
    
    async def _execute_database_query(self, query_data: Dict) -> List[Dict]:
        """
        Execute the MongoDB query generated by Stage 1 - FIXED VERSION
        """
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            logger.info(f"📊 Executing query on collection: {collection_name}")
            logger.info(f"   Pipeline stages: {len(pipeline)}")
            logger.info(f"   Pipeline: {pipeline}")
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return []
            
            # FIXED: Check database connection properly
            if not self.db_manager.is_connected():
                logger.error("Database is not connected")
                return []
            
            # Get the collection with proper error handling
            try:
                collection = self.db_manager.get_collection(collection_name)
                if collection is None:
                    logger.error(f"Failed to get collection: {collection_name}")
                    return []
            except Exception as e:
                logger.error(f"Exception getting collection {collection_name}: {e}")
                return []
            
            # FIXED: Test if collection has data first
            try:
                doc_count = collection.count_documents({})
                logger.info(f"   Collection {collection_name} has {doc_count} total documents")
                
                if doc_count == 0:
                    logger.warning(f"Collection {collection_name} is empty!")
                    return []
                    
            except Exception as e:
                logger.error(f"Failed to count documents in {collection_name}: {e}")
                return []
            
            # Execute the aggregation pipeline
            start_time = datetime.now()
            
            try:
                logger.info("   Executing aggregation pipeline...")
                results = list(collection.aggregate(pipeline))
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"   Query executed in {execution_time:.3f}s")
                logger.info(f"   Returned {len(results)} documents")
                
                # Log sample results for debugging
                if results:
                    logger.info(f"   Sample result: {results[0]}")
                else:
                    logger.warning("   Pipeline returned no results - checking for data issues...")
                    
                    # Debug: Check if the match conditions are too restrictive
                    if pipeline and '$match' in str(pipeline[0]):
                        match_stage = pipeline[0].get('$match', {})
                        logger.info(f"   Match conditions: {match_stage}")
                        
                        # Test a simpler query to see if categories exist
                        if 'category' in match_stage:
                            category_test = list(collection.aggregate([
                                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                                {"$sort": {"count": -1}},
                                {"$limit": 10}
                            ]))
                            logger.info(f"   Available categories: {category_test}")
                
                return results
                
            except Exception as e:
                logger.error(f"Pipeline execution failed: {e}")
                logger.error(f"   Pipeline: {pipeline}")
                return []
            
        except Exception as e:
            logger.error(f"Database query execution failed: {str(e)}")
            logger.error(f"Collection: {query_data.get('collection')}")
            logger.error(f"Pipeline: {query_data.get('pipeline')}")
            return []
    
    async def batch_process_questions(self, questions: List[str]) -> List[AnalyticsResult]:
        """
        Process multiple questions efficiently with concurrent execution
        """
        logger.info(f"🔄 Batch processing {len(questions)} questions")
        
        # Process questions concurrently for better performance
        tasks = [self.process_question(question) for question in questions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that occurred
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Question {i+1} failed: {str(result)}")
                processed_results.append(AnalyticsResult(
                    success=False,
                    query_data={},
                    raw_results=[],
                    visualization={},
                    execution_time=0,
                    total_attempts=0,
                    error=f"Batch processing error: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        successful = sum(1 for r in processed_results if r.success)
        logger.info(f"✅ Batch complete: {successful}/{len(questions)} successful")
        
        return processed_results
    
    def get_conversation_context(self, previous_results: List[AnalyticsResult]) -> Dict:
        """
        Build context from previous queries for better follow-up questions
        """
        if not previous_results:
            return {}
        
        # Analyze previous queries to build context
        collections_used = set()
        categories_analyzed = set()
        metrics_used = set()
        
        for result in previous_results[-3:]:  # Last 3 queries for context
            if result.success:
                query_data = result.query_data
                collections_used.add(query_data.get("collection", ""))
                
                # Extract categories from pipeline
                pipeline = query_data.get("pipeline", [])
                for stage in pipeline:
                    if "$match" in stage:
                        match_conditions = stage["$match"]
                        if "category" in match_conditions:
                            if isinstance(match_conditions["category"], dict):
                                if "$in" in match_conditions["category"]:
                                    categories_analyzed.update(match_conditions["category"]["$in"])
                            else:
                                categories_analyzed.add(match_conditions["category"])
        
        return {
            "previous_collections": list(collections_used),
            "previous_categories": list(categories_analyzed),
            "previous_metrics": list(metrics_used),
            "query_count": len(previous_results)
        }


class ConversationManager:
    """
    Manages conversation state and context for multi-turn analytics
    """
    
    def __init__(self, analytics_processor):
        self.analytics_processor = analytics_processor
        self.conversation_history = []
        self.session_context = {}
    
    async def process_conversational_question(self, user_question: str) -> AnalyticsResult:
        """
        Process a question with full conversation context
        """
        # Build context from previous interactions
        context = self.analytics_processor.get_conversation_context(self.conversation_history)
        
        # Add current session context
        enhanced_context = {
            **context,
            **self.session_context,
            "conversation_turn": len(self.conversation_history) + 1,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process the question
        result = await self.analytics_processor.process_question(user_question, enhanced_context)
        
        # Store in conversation history
        self.conversation_history.append(result)
        
        # Update session context based on result
        if result.success:
            self._update_session_context(result)
        
        # Limit history size to prevent memory issues
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return result
    
    def _update_session_context(self, result: AnalyticsResult):
        """
        Update session context based on successful query result
        """
        query_data = result.query_data
        
        # Track commonly used collections
        collection = query_data.get("collection")
        if collection:
            if "frequent_collections" not in self.session_context:
                self.session_context["frequent_collections"] = {}
            
            self.session_context["frequent_collections"][collection] = \
                self.session_context["frequent_collections"].get(collection, 0) + 1
        
        # Track analysis patterns
        chart_hint = query_data.get("chart_hint")
        if chart_hint:
            if "preferred_visualizations" not in self.session_context:
                self.session_context["preferred_visualizations"] = {}
            
            self.session_context["preferred_visualizations"][chart_hint] = \
                self.session_context["preferred_visualizations"].get(chart_hint, 0) + 1
    
    def get_conversation_summary(self) -> Dict:
        """
        Get summary of the current conversation session
        """
        if not self.conversation_history:
            return {"status": "no_history"}
        
        successful_queries = [r for r in self.conversation_history if r.success]
        failed_queries = [r for r in self.conversation_history if not r.success]
        
        total_execution_time = sum(r.execution_time for r in self.conversation_history)
        total_attempts = sum(r.total_attempts for r in self.conversation_history)
        
        collections_used = set()
        chart_types_used = set()
        
        for result in successful_queries:
            collections_used.add(result.query_data.get("collection", "unknown"))
            if "chart_type" in result.visualization:
                chart_types_used.add(result.visualization["chart_type"])
        
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
            "visualization_types_used": list(chart_types_used),
            "session_context": self.session_context
        }
    
    def reset_conversation(self):
        """
        Reset the conversation history and context
        """
        self.conversation_history = []
        self.session_context = {}
        logger.info("🔄 Conversation history reset")


class PerformanceMonitor:
    """
    Monitor and track performance metrics for the two-stage system
    """
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "stage_1_failures": 0,
            "stage_2_failures": 0,
            "total_execution_time": 0.0,
            "total_ai_attempts": 0,
            "gemini_reliability": {
                "stage_1": {"attempts": 0, "successes": 0},
                "stage_2": {"attempts": 0, "successes": 0}
            }
        }
    
    def record_result(self, result: AnalyticsResult):
        """
        Record metrics from a processing result
        """
        self.metrics["total_requests"] += 1
        
        if result.success:
            self.metrics["successful_requests"] += 1
        
        self.metrics["total_execution_time"] += result.execution_time
        self.metrics["total_ai_attempts"] += result.total_attempts
        
        # Record stage-specific metrics
        if result.stage_details:
            stage_1_info = result.stage_details.get("stage_1", {})
            stage_2_info = result.stage_details.get("stage_2", {})
            
            if stage_1_info.get("status") == "failed":
                self.metrics["stage_1_failures"] += 1
            else:
                # Stage 1 succeeded
                self.metrics["gemini_reliability"]["stage_1"]["attempts"] += stage_1_info.get("attempts", 1)
                self.metrics["gemini_reliability"]["stage_1"]["successes"] += 1
            
            if stage_2_info.get("status") == "failed":
                self.metrics["stage_2_failures"] += 1
            else:
                # Stage 2 succeeded  
                self.metrics["gemini_reliability"]["stage_2"]["attempts"] += stage_2_info.get("attempts", 1)
                self.metrics["gemini_reliability"]["stage_2"]["successes"] += 1
    
    def get_performance_report(self) -> Dict:
        """
        Generate comprehensive performance report
        """
        if self.metrics["total_requests"] == 0:
            return {"status": "no_data"}
        
        # Calculate success rates
        overall_success_rate = (self.metrics["successful_requests"] / self.metrics["total_requests"]) * 100
        
        # Calculate average execution time
        avg_execution_time = self.metrics["total_execution_time"] / self.metrics["total_requests"]
        
        # Calculate average AI attempts per request
        avg_ai_attempts = self.metrics["total_ai_attempts"] / self.metrics["total_requests"]
        
        # Calculate Gemini reliability for each stage
        stage_1_reliability = 0
        stage_2_reliability = 0
        
        s1_attempts = self.metrics["gemini_reliability"]["stage_1"]["attempts"]
        s1_successes = self.metrics["gemini_reliability"]["stage_1"]["successes"]
        
        if s1_attempts > 0:
            stage_1_reliability = (s1_successes / s1_attempts) * 100
        
        s2_attempts = self.metrics["gemini_reliability"]["stage_2"]["attempts"]
        s2_successes = self.metrics["gemini_reliability"]["stage_2"]["successes"]
        
        if s2_attempts > 0:
            stage_2_reliability = (s2_successes / s2_attempts) * 100
        
        return {
            "overview": {
                "total_requests": self.metrics["total_requests"],
                "successful_requests": self.metrics["successful_requests"],
                "overall_success_rate": round(overall_success_rate, 2),
                "average_execution_time": round(avg_execution_time, 3),
                "average_ai_attempts": round(avg_ai_attempts, 1)
            },
            "stage_performance": {
                "stage_1_failures": self.metrics["stage_1_failures"],
                "stage_2_failures": self.metrics["stage_2_failures"],
                "stage_1_reliability": round(stage_1_reliability, 2),
                "stage_2_reliability": round(stage_2_reliability, 2)
            },
            "ai_efficiency": {
                "total_ai_calls": self.metrics["total_ai_attempts"],
                "stage_1_total_attempts": s1_attempts,
                "stage_2_total_attempts": s2_attempts,
                "average_retries_needed": round(avg_ai_attempts - 2, 1)  # -2 because minimum is 2 (one per stage)
            },
            "recommendations": self._generate_recommendations(overall_success_rate, stage_1_reliability, stage_2_reliability)
        }
    
    def _generate_recommendations(self, overall_rate: float, stage_1_rate: float, stage_2_rate: float) -> List[str]:
        """
        Generate performance improvement recommendations
        """
        recommendations = []
        
        if overall_rate < 90:
            recommendations.append("Overall success rate is below 90% - investigate common failure patterns")
        
        if stage_1_rate < 85:
            recommendations.append("Stage 1 (Query Generation) reliability is low - review prompt engineering")
        
        if stage_2_rate < 85:
            recommendations.append("Stage 2 (Visualization) reliability is low - improve data validation")
        
        if not recommendations:
            recommendations.append("System performance is excellent - no immediate improvements needed")
        
        return recommendations