# backend/utils/perfected_processor.py

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from bson import ObjectId
from config import DATABASE_SCHEMA

logger = logging.getLogger(__name__)

class PerfectedTwoStageProcessor:
    """Perfected processor that prioritizes Gemini AI for enhanced two-stage processing"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor  # Can be None for Gemini-only architecture
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
                    
                    # Check if this is a text-only response (no visualization needed)
                    if viz_data.get("text_only"):
                        logger.info("📝 Returning text-only response without chart")
                        return {
                            "success": True,
                            "summary": viz_data.get("summary", "Analysis completed successfully"),
                            "insights": viz_data.get("insights", []),
                            "recommendations": viz_data.get("recommendations", []),
                            "results_count": len(raw_results),
                            "execution_time": execution_time,
                            "query_source": "gemini_two_stage_text_only",
                            "ai_powered": True
                            # Note: No chart_data field - frontend won't render chart
                        }
                    
                    # Normal visualization response
                    chart_data = viz_data.get("chart_config", {})
                    
                    return {
                        "success": True,
                        "summary": viz_data.get("summary", "AI-powered analysis completed successfully"),
                        "chart_data": chart_data,
                        "insights": viz_data.get("insights", ["AI-generated insights"]),
                        "recommendations": viz_data.get("recommendations", ["AI-powered recommendations"]),
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        # NEW: Multi-output support
                        "outputs": viz_data.get("outputs", []),
                        "primary_insights": viz_data.get("primary_insights", viz_data.get("insights", [])),
                        "query_source": "gemini_two_stage_perfect",
                        "ai_powered": True
                    }
                else:
                    # Stage 2 failed
                    logger.warning("Stage 2 (visualization) failed")
                    if self.simple_processor:
                        logger.info("Trying simple processor fallback")
                        fallback_result = self.simple_processor.process_question(user_question)
                        if fallback_result.get("success"):
                            fallback_result["query_source"] = "gemini_stage1_simple_fallback"
                            return fallback_result
                    else:
                        # Return basic response with data but no visualization
                        return {
                            "success": True,
                            "summary": f"Found {len(raw_results)} results but could not generate visualization.",
                            "insights": ["Data retrieved successfully from database."],
                            "recommendations": ["Try a different question format for better visualization."],
                            "results_count": len(raw_results),
                            "query_source": "gemini_stage1_only",
                            "ai_powered": True
                        }
            else:
                # Gemini query returned no results
                logger.warning("Gemini query returned no results")
                if self.simple_processor:
                    logger.info("Trying simple processor fallback")
                    simple_result = self.simple_processor.process_question(user_question)
                    if simple_result.get("success"):
                        simple_result["query_source"] = "gemini_failed_simple_success"
                        simple_result["ai_powered"] = False
                        return simple_result
                else:
                    logger.info("No simple processor available, returning empty result message")
        
        # Final fallback
        if self.simple_processor:
            logger.warning("Using simple processor as last resort")
            simple_result = self.simple_processor.process_question(user_question)
            
            if simple_result.get("success"):
                simple_result["query_source"] = "simple_last_resort" 
                simple_result["ai_powered"] = False
                return simple_result
        
        # No processors available or all failed
        return {
            "success": False,
            "error": "Unable to process your question - no data found or query too complex",
            "suggestions": [
                "Try a more specific question",
                "Check if data exists for this request",
                "Ask about users, costs, documents, or compliance"
            ]
        }
    
    async def _execute_database_query(self, query_data: Dict[str, Any]) -> Optional[List[Dict]]:
        """Execute MongoDB query with enhanced error handling"""
        try:
            collection_name = query_data.get("collection")
            pipeline = query_data.get("pipeline", [])
            
            # Fix common collection name variants
            collection_name = self._fix_collection_name(collection_name)
            
            if not collection_name or not pipeline:
                logger.error("Invalid query data - missing collection or pipeline")
                return None
            
            # Convert date strings back to datetime objects for MongoDB
            pipeline = self._process_pipeline_dates(pipeline)
            
            # Apply fuzzy matching for better search results
            pipeline = self._apply_fuzzy_matching(pipeline)
            
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
    
    def _process_pipeline_dates(self, pipeline: list) -> list:
        """Convert date strings in pipeline back to datetime objects"""
        from datetime import datetime
        import re
        
        def convert_dates_recursive(obj):
            if isinstance(obj, dict):
                converted = {}
                for key, value in obj.items():
                    converted[key] = convert_dates_recursive(value)
                return converted
            elif isinstance(obj, list):
                return [convert_dates_recursive(item) for item in obj]
            elif isinstance(obj, str):
                # Check if it's an ISO date string
                if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?$', obj):
                    try:
                        # Parse ISO date string to datetime
                        return datetime.fromisoformat(obj.replace('Z', '+00:00'))
                    except ValueError:
                        return obj
                return obj
            else:
                return obj
        
        return convert_dates_recursive(pipeline)
    
    def _apply_fuzzy_matching(self, pipeline: List[Dict]) -> List[Dict]:
        """Convert exact matches to fuzzy regex matches for better search results"""
        def make_fuzzy_match(match_stage):
            """Convert exact matches to regex patterns"""
            new_match = {}
            
            for field, condition in match_stage.get('$match', {}).items():
                if isinstance(condition, str):
                    # Convert exact string match to case-insensitive regex
                    # Handle spaces by making them optional and flexible
                    fuzzy_pattern = condition.replace(' ', r'\s*').strip()
                    new_match[field] = {'$regex': f'.*{fuzzy_pattern}.*', '$options': 'i'}
                elif isinstance(condition, dict):
                    # Handle nested conditions
                    new_condition = {}
                    for op, value in condition.items():
                        if op in ['$eq', '$in'] and isinstance(value, str):
                            fuzzy_pattern = value.replace(' ', r'\s*').strip()
                            new_condition = {'$regex': f'.*{fuzzy_pattern}.*', '$options': 'i'}
                        elif op == '$in' and isinstance(value, list):
                            # Convert array of exact matches to regex patterns
                            regex_patterns = []
                            for item in value:
                                if isinstance(item, str):
                                    fuzzy_pattern = item.replace(' ', r'\s*').strip()
                                    regex_patterns.append({'$regex': f'.*{fuzzy_pattern}.*', '$options': 'i'})
                            if regex_patterns:
                                new_condition = {'$or': [{field: pattern} for pattern in regex_patterns]}
                            else:
                                new_condition = condition
                        else:
                            new_condition[op] = value
                    new_match[field] = new_condition
                else:
                    new_match[field] = condition
            
            return {'$match': new_match}
        
        # Apply fuzzy matching to $match stages
        fuzzy_pipeline = []
        for stage in pipeline:
            if '$match' in stage:
                fuzzy_stage = make_fuzzy_match(stage)
                fuzzy_pipeline.append(fuzzy_stage)
            else:
                fuzzy_pipeline.append(stage)
        
        return fuzzy_pipeline
    
    def _clean_mongodb_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Clean MongoDB result by converting ObjectIds to strings and handling NaN values"""
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
                cleaned[key] = None  # Convert NaN to null for JSON compatibility
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _fix_collection_name(self, collection_name: str) -> str:
        """Fix common collection name spelling variants"""
        if not collection_name:
            return collection_name
        
        # Common collection name corrections
        collection_fixes = {
            'costevaluationforllm': 'costevalutionforllm',  # Missing 'a' in evaluation
            'costeevaluationforllm': 'costevalutionforllm',  # Extra 'e' variant
            'cost_evaluation_for_llm': 'costevalutionforllm',  # Underscore variant
            'costsforllm': 'costevalutionforllm',  # Shortened variant
        }
        
        # Apply correction if found
        corrected_name = collection_fixes.get(collection_name.lower(), collection_name)
        
        if corrected_name != collection_name:
            logger.info(f"🔧 Corrected collection name: '{collection_name}' → '{corrected_name}'")
        
        return corrected_name