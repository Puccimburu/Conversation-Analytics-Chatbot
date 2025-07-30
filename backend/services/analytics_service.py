import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from bson import ObjectId
from config.config import DATABASE_SCHEMA

logger = logging.getLogger(__name__)

class CompleteSimpleQueryProcessor:
    """Complete simple processor with all methods"""
    
    def __init__(self, database):
        self.db = database
        
    def process_question(self, user_question: str) -> Dict[str, Any]:
        """Process questions with pattern matching"""
        question_lower = user_question.lower()
        
        try:
            # AI cost analysis
            if any(word in question_lower for word in ["cost", "spending", "ai cost", "model cost"]) or ("compare" in question_lower and any(word in question_lower for word in ["ai", "model", "cost"])):
                return self._ai_cost_analysis()
            
            # Document confidence analysis
            elif any(word in question_lower for word in ["confidence", "document", "extraction"]) and any(word in question_lower for word in ["top", "best", "analysis"]):
                return self._document_confidence_analysis()
            
            # Compliance obligations
            elif any(word in question_lower for word in ["compliance", "obligation", "legal"]) and any(word in question_lower for word in ["category", "type", "analysis"]):
                return self._compliance_obligations()
            
            # Agent performance
            elif any(word in question_lower for word in ["agent", "performance", "activity"]):
                return self._agent_performance()
            
            # Default: show available data
            else:
                return self._show_available_data()
                
        except Exception as e:
            logger.error(f"Simple processor error: {e}")
            return {
                "success": False,
                "error": f"Query failed: {str(e)}",
                "suggestions": ["Try a different question", "Check your data"]
            }
    
    def _ai_cost_analysis(self):
        """Analyze AI operational costs by model type"""
        pipeline = [
            {"$group": {
                "_id": "$modelType",
                "total_cost": {"$sum": "$totalCost"},
                "total_tokens": {"$sum": {"$add": ["$inputTokens", "$outputTokens"]}},
                "request_count": {"$sum": 1}
            }},
            {"$sort": {"total_cost": -1}}
        ]
        
        results = list(self.db.costevalutionforllm.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No AI cost data found"}
        
        # Create summary
        total_cost = sum(r['total_cost'] for r in results)
        summary_parts = []
        
        for result in results:
            model_type = result['_id']
            cost = result['total_cost']
            tokens = result['total_tokens']
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            
            summary_parts.append(f"{model_type}: ${cost:,.2f} ({percentage:.1f}%) from {tokens:,} tokens")
        
        summary = "AI cost analysis: " + " | ".join(summary_parts)
        
        # Chart configuration
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "AI Cost ($)",
                    "data": [r['total_cost'] for r in results],
                    "backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)"],
                    "borderColor": ["rgba(59, 130, 246, 1)", "rgba(16, 185, 129, 1)"],
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "AI Model Cost Analysis"},
                    "legend": {"display": False}
                },
                "scales": {
                    "y": {"beginAtZero": True, "title": {"display": True, "text": "Cost ($)"}},
                    "x": {"title": {"display": True, "text": "AI Model"}}
                }
            }
        }
        
        insights = [
            f"Total AI operational cost: ${total_cost:,.2f}",
            f"Number of AI model types in use: {len(results)}"
        ]
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": insights,
            "recommendations": ["Focus on cost-effective models", "Analyze token usage patterns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _document_confidence_analysis(self):
        """Analyze document extraction confidence scores"""
        pipeline = [
            {"$group": {
                "_id": "$Type",
                "avg_confidence": {"$avg": "$Confidence_Score"},
                "total_extractions": {"$sum": 1},
                "low_confidence_count": {"$sum": {"$cond": [{"$lt": ["$Confidence_Score", 0.8]}, 1, 0]}}
            }},
            {"$sort": {"avg_confidence": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.documentextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No document extraction data found"}
        
        summary = f"Top {len(results)} document types by confidence: "
        top_3 = results[:3]
        for i, doc_type in enumerate(top_3, 1):
            summary += f"{i}. {doc_type['_id']} ({doc_type['avg_confidence']:.2f} confidence) "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Avg Confidence",
                    "data": [r['avg_confidence'] for r in results],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Document Extraction Confidence by Type"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total document types: {len(results)}", f"Highest confidence: {results[0]['_id']}"],
            "recommendations": ["Focus on high-confidence extractions", "Analyze low-confidence patterns for improvement"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _compliance_obligations(self):
        """Compliance obligations breakdown by type"""
        pipeline = [
            {"$group": {
                "_id": "$obligationType",
                "total_obligations": {"$sum": 1},
                "avg_confidence": {"$avg": "$confidence"}
            }},
            {"$sort": {"total_obligations": -1}}
        ]
        
        results = list(self.db.obligationextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No compliance obligation data found"}
        
        total_obligations = sum(r['total_obligations'] for r in results)
        summary = f"Compliance obligations across {len(results)} types: "
        for result in results[:3]:  # Top 3
            obligation_type = result['_id']
            count = result['total_obligations']
            percentage = (count / total_obligations * 100) if total_obligations > 0 else 0
            summary += f"{obligation_type} {count} obligations ({percentage:.1f}%), "
        
        colors = [
            "rgba(59, 130, 246, 0.8)",   # Blue
            "rgba(16, 185, 129, 0.8)",   # Green
            "rgba(245, 158, 11, 0.8)",   # Yellow
            "rgba(239, 68, 68, 0.8)",    # Red
            "rgba(147, 51, 234, 0.8)",   # Purple
            "rgba(236, 72, 153, 0.8)"    # Pink
        ]
        
        chart_config = {
            "type": "doughnut",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['total_obligations'] for r in results],
                    "backgroundColor": colors[:len(results)]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": "Compliance Obligations by Type"},
                    "legend": {"display": True, "position": "bottom"}
                }
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total categories: {len(results)}", f"Leading category: {results[0]['_id']}"],
            "recommendations": ["Focus on high-priority obligations", "Analyze compliance risk patterns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _agent_performance(self):
        """Agent performance analysis"""
        pipeline = [
            {"$group": {
                "_id": "$Agent",
                "success_count": {"$sum": {"$cond": [{"$eq": ["$Outcome", "Success"]}, 1, 0]}},
                "total_activities": {"$sum": 1},
                "avg_duration": {"$avg": "$duration"}
            }},
            {"$sort": {"success_count": -1}}
        ]
        
        results = list(self.db.agent_activity.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No agent performance data found"}
        
        summary = "Agent performance: "
        for result in results:
            agent = result['_id']
            success = result['success_count']
            total = result['total_activities']
            success_rate = (success / total * 100) if total > 0 else 0
            summary += f"{agent}: {success}/{total} ({success_rate:.1f}% success), "
        
        chart_config = {
            "type": "bar",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "label": "Success Count",
                    "data": [r['success_count'] for r in results],
                    "backgroundColor": "rgba(16, 185, 129, 0.8)",
                    "borderColor": "rgba(16, 185, 129, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Agent Performance Analysis"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary.rstrip(", "),
            "chart_data": chart_config,
            "insights": [f"Total agents: {len(results)}", f"Top performer: {results[0]['_id']}"],
            "recommendations": ["Monitor low-performing agents", "Analyze success patterns"],
            "results_count": len(results),
            "execution_time": 0.1,
            "query_source": "simple_direct"
        }
    
    def _show_available_data(self):
        """Show what data is available"""
        try:
            collections_info = []
            for collection_name in ["costevalutionforllm", "documentextractions", "obligationextractions", "agent_activity", "batches", "users", "conversations"]:
                try:
                    count = self.db[collection_name].count_documents({})
                    collections_info.append(f"{collection_name}: {count} records")
                except:
                    collections_info.append(f"{collection_name}: 0 records")
            
            summary = f"Available data: {', '.join(collections_info)}. Try asking about: AI operational costs, document processing confidence, compliance obligations, agent performance."
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'What are our AI operational costs this month?'",
                    "Try: 'Show me document extraction confidence trends'",
                    "Try: 'Which compliance obligations need attention?'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {"success": False, "error": f"Could not retrieve data info: {str(e)}"}


class PerfectedTwoStageProcessor:
    """Perfected processor that prioritizes Gemini AI"""
    
    def __init__(self, gemini_client, simple_processor, database):
        self.gemini_client = gemini_client
        self.simple_processor = simple_processor
        self.db = database
        self.schema_info = DATABASE_SCHEMA.copy()
    
    async def process_question(self, user_question: str) -> Dict[str, Any]:
        """Enhanced two-stage processing with Gemini priority"""
        start_time = datetime.now()
        
        # STAGE 1: Query Generation with Gemini (Priority)
        logger.info(f"🚀 Starting perfected two-stage processing: '{user_question}'")
        
        stage_1_result = await self.gemini_client.generate_query(user_question, self.schema_info)
        
        if stage_1_result["success"]:
            # Execute the Gemini-generated query
            query_data = stage_1_result["data"]
            raw_results = await self._execute_database_query(query_data)
            
            if raw_results is not None and len(raw_results) > 0:
                # STAGE 2: Visualization Generation with Gemini
                stage_2_result = await self.gemini_client.generate_visualization(
                    user_question, raw_results, query_data
                )
                
                if stage_2_result["success"]:
                    # Complete success with both Gemini stages
                    viz_data = stage_2_result["data"]
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
                    # Stage 2 failed, create enhanced fallback visualization
                    logger.warning("Stage 2 failed, creating enhanced fallback visualization")
                    fallback_viz = self._create_enhanced_visualization(user_question, raw_results, query_data)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    return {
                        "success": True,
                        "summary": fallback_viz["summary"],
                        "chart_data": fallback_viz["chart_config"],
                        "insights": fallback_viz["insights"],
                        "recommendations": fallback_viz["recommendations"],
                        "results_count": len(raw_results),
                        "execution_time": execution_time,
                        "query_source": "gemini_query_enhanced_viz",
                        "ai_powered": True
                    }
            else:
                # Gemini query returned no results, try simple processor
                logger.warning("Gemini query returned no results, trying simple processor")
                simple_result = self.simple_processor.process_question(user_question)
                if simple_result.get("success"):
                    simple_result["query_source"] = "gemini_failed_simple_success"
                    simple_result["ai_powered"] = False
                    return simple_result
                else:
                    return {
                        "success": False,
                        "error": "No data found for your query",
                        "suggestions": [
                            "Try rephrasing your question",
                            "Check if you're asking about available data"
                        ]
                    }
        
        # Stage 1 failed completely, use simple processor as last resort
        logger.warning("Gemini Stage 1 failed, using simple processor as last resort")
        simple_result = self.simple_processor.process_question(user_question)
        
        if simple_result.get("success"):
            simple_result["query_source"] = "simple_last_resort"
            simple_result["ai_powered"] = False
            logger.info(f"✅ Simple processor success as fallback: {simple_result.get('results_count', 0)} results")
            return simple_result
        else:
            return {
                "success": False,
                "error": "Unable to process your question with available methods",
                "suggestions": [
                    "Try a simpler question",
                    "Ask about: 'What are our AI operational costs?'",
                    "Ask about: 'Show me document extraction confidence'",
                    "Ask about: 'Which compliance obligations need attention?'"
                ]
            }
    
    async def _execute_database_query(self, query_data: Dict) -> Optional[List[Dict]]:
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
    
    def _clean_mongodb_result(self, result: Dict) -> Dict:
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
    
    def _create_enhanced_visualization(self, user_question: str, raw_results: List[Dict], query_data: Dict) -> Dict[str, Any]:
        """Create enhanced visualization when Gemini Stage 2 fails"""
        if not raw_results:
            return {
                "summary": "No data found for visualization",
                "chart_config": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["No data available"],
                "recommendations": ["Try a different question"]
            }
        
        # Smart chart type selection based on data and query
        chart_hint = query_data.get("chart_hint", "bar")
        
        # Extract data intelligently
        labels = []
        values = []
        
        for item in raw_results[:15]:  # Limit for readability
            label = str(item.get('_id', 'Unknown'))
            labels.append(label)
            
            # Get value
            value = 0
            for field in ['total_revenue', 'total_spent', 'total_amount', 'customer_count', 'order_count', 'stock']:
                if field in item and item[field] is not None:
                    value = float(item[field])
                    break
            values.append(value)
        
        # Chart configuration
        chart_config = {
            "type": chart_hint,
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Values",
                    "data": values,
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "plugins": {
                    "title": {"display": True, "text": "Enhanced Data Analysis"},
                    "legend": {"display": chart_hint in ['pie', 'doughnut']}
                }
            }
        }
        
        if chart_hint not in ['pie', 'doughnut']:
            chart_config["options"]["scales"] = {
                "y": {"beginAtZero": True},
                "x": {"display": True}
            }
        
        # Generate smart summary
        total_value = sum(values) if values else 0
        summary = f"Enhanced analysis of {len(raw_results)} data points. Total value: {total_value:,.2f}"
        
        insights = [
            f"Analyzed {len(raw_results)} records successfully",
            "Enhanced fallback visualization applied"
        ]
        
        recommendations = [
            "Review data patterns for optimization opportunities",
            "Consider AI-powered analysis for deeper insights"
        ]
        
        return {
            "summary": summary,
            "chart_config": chart_config,
            "insights": insights,
            "recommendations": recommendations
        }