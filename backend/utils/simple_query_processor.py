# backend/utils/simple_query_processor.py

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CompleteSimpleQueryProcessor:
    """Complete simple processor with all methods for direct pattern matching queries"""
    
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
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total models analyzed: {len(results)}", f"Total cost: ${total_cost:,.2f}"],
            "recommendations": ["Focus on cost optimization", "Analyze token efficiency"],
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
                "total_extractions": {"$sum": 1}
            }},
            {"$sort": {"avg_confidence": -1}},
            {"$limit": 10}
        ]
        
        results = list(self.db.documentextractions.aggregate(pipeline))
        
        if not results:
            return {"success": False, "error": "No document extraction data found"}
        
        summary = f"Top {len(results)} document types by confidence"
        
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
                "plugins": {"title": {"display": True, "text": "Document Extraction Confidence"}},
                "scales": {"y": {"beginAtZero": True}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total document types: {len(results)}", f"Highest confidence: {results[0]['_id']}"],
            "recommendations": ["Focus on high-confidence extractions", "Improve low-confidence patterns"],
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
        summary = f"Compliance obligations across {len(results)} types"
        
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
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total categories: {len(results)}", f"Leading category: {results[0]['_id']}"],
            "recommendations": ["Review compliance requirements", "Address high-risk categories"],
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
        
        summary = "Agent performance analysis"
        
        chart_config = {
            "type": "pie",
            "data": {
                "labels": [r['_id'] for r in results],
                "datasets": [{
                    "data": [r['success_count'] for r in results],
                    "backgroundColor": [
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(16, 185, 129, 0.8)",
                        "rgba(245, 158, 11, 0.8)"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": "Agent Success Distribution"}}
            }
        }
        
        return {
            "success": True,
            "summary": summary,
            "chart_data": chart_config,
            "insights": [f"Total agents: {len(results)}", f"Top agent: {results[0]['_id']}"],
            "recommendations": ["Optimize agent performance", "Focus on successful patterns"],
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
            
            summary = f"Available data: {', '.join(collections_info)}"
            
            return {
                "success": True,
                "summary": summary,
                "chart_data": {"type": "bar", "data": {"labels": [], "datasets": []}},
                "insights": ["System ready", "Multiple question types supported"],
                "recommendations": [
                    "Try: 'What are our AI operational costs?'",
                    "Try: 'Show me document extraction confidence'",
                    "Try: 'Which compliance obligations need attention?'"
                ],
                "results_count": 0,
                "execution_time": 0.1,
                "query_source": "simple_direct"
            }
        except Exception as e:
            return {"success": False, "error": f"Could not retrieve data info: {str(e)}"}