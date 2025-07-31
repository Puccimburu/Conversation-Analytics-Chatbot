# backend/utils/perfected_processor.py

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId
from config import DATABASE_SCHEMA

logger = logging.getLogger(__name__)

class PerfectedTwoStageProcessor:
    """Perfected processor that prioritizes Gemini AI for enhanced two-stage processing"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor
        self.db = database
        # Import GenAI schema from config
        self.schema_info = DATABASE_SCHEMA.copy()
    
    async def process_question(self, user_question: str) -> Dict[str, Any]:
        """Enhanced two-stage processing with Gemini priority"""
        start_time = datetime.now()
        
        # STAGE 1: Query Generation with Gemini (Priority)
        logger.info(f"🚀 Starting perfected two-stage processing: '{user_question}'")
        
        stage_1_result = await self.gemini_client.generate_query(user_question, self.schema_info)
        
        if stage_1_result.get('success'):
            # Execute the Gemini-generated query
            query_data = stage_1_result.get('data')
            raw_results = await self._execute_database_query(query_data)
            
            if raw_results is not None and len(raw_results) > 0:
                # STAGE 2: Visualization Generation with Gemini
                stage_2_result = await self.gemini_client.generate_visualization(
                    user_question, raw_results, query_data
                )
                
                if stage_2_result.get('success'):
                    # Complete success with both Gemini stages
                    viz_data = stage_2_result.get('data')
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"✅ Perfected two-stage Gemini processing successful: {len(raw_results)} results in {execution_time:.2f}s")
                    
                    return {
                        "success": True,
                        "summary": viz_data.get("summary", "AI-powered analysis completed successfully"),
                        "chart_data": viz_data.get("chart_config", {}),
                        "insights": viz_data.get("insights", ["AI-generated insights"]),
                        "recommendations": viz_data.get("recommendations", ["AI-powered recommendations"]),
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_two_stage_perfect",
                        "ai_powered": True
                    }
                else:
                    # Stage 2 failed, use simple processor fallback
                    logger.warning("Stage 2 failed, falling back to simple processor")
                    fallback_result = self.simple_processor.process_question(user_question)
                    if fallback_result.get("success"):
                        fallback_result["query_source"] = "gemini_stage1_simple_fallback"
                        return fallback_result
            else:
                # Gemini query returned no results, try simple processor
                logger.warning("Gemini query returned no results, trying simple processor")
                simple_result = self.simple_processor.process_question(user_question)
                if simple_result.get("success"):
                    simple_result["query_source"] = "gemini_failed_simple_success"
                    simple_result["ai_powered"] = False
                    return simple_result
        
        # Complete fallback to simple processor
        logger.warning("Using simple processor as last resort")
        simple_result = self.simple_processor.process_question(user_question)
        
        if simple_result.get("success"):
            simple_result["query_source"] = "simple_last_resort"
            simple_result["ai_powered"] = False
            return simple_result
        else:
            return {
                "success": False,
                "error": "Unable to process your question",
                "suggestions": [
                    "Try a simpler question",
                    "Ask about AI costs, document confidence, or compliance obligations"
                ]
            }
    
    async def _execute_database_query(self, query_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Execute MongoDB query with enhanced error handling"""
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return None
            
            collection = self.db[collection_name]
            results = list(collection.aggregate(pipeline))
            
            # Convert ObjectIds to strings for JSON serialization
            cleaned_results = []
            for result in results:
                cleaned_result = self._clean_mongodb_result(result)
                cleaned_results.append(cleaned_result)
            
            logger.info(f"Database query executed: {len(cleaned_results)} results from {collection_name}")
            return cleaned_results
            
        except Exception as e:
            logger.error(f"Database query execution failed: {e}")
            return None
    
    def _clean_mongodb_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean MongoDB result by converting ObjectIds to strings"""
        cleaned = {}
        
        for key, value in result.items():
            if isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = self._clean_mongodb_result(value)
            else:
                cleaned[key] = value
        
        return cleaned