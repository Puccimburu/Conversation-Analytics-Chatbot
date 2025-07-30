import json
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from config.config import DATABASE_SCHEMA, CHART_TYPE_MAPPING

logger = logging.getLogger(__name__)

class QueryBuilder:
    """Utility class for building and validating MongoDB queries - Enhanced for GenAI operations"""
    
    def __init__(self, db):
        self.db = db
        self.schema = DATABASE_SCHEMA['collections']
        
        # Enhanced GenAI-specific query patterns
        self.genai_patterns = {
            'cost_analysis': [
                'cost', 'spending', 'expensive', 'budget', 'price', 'money', 'dollar',
                'token', 'billing', 'charge', 'rate', 'pricing', 'investment', 'roi',
                'economical', 'cost-effective', 'affordable', 'financial', 'expense'
            ],
            'document_processing': [
                'document', 'extraction', 'confidence', 'processing', 'extract', 'process',
                'parse', 'analyze', 'read', 'scan', 'digitize', 'convert', 'transform',
                'content', 'text', 'data', 'information', 'file', 'pdf', 'upload',
                'accuracy', 'quality', 'reliability', 'precision'
            ],
            'compliance': [
                'compliance', 'obligation', 'legal', 'risk', 'regulatory', 'law',
                'requirement', 'mandate', 'policy', 'rule', 'guideline', 'standard',
                'audit', 'violation', 'breach', 'penalty', 'fine', 'liability',
                'confidential', 'privacy', 'gdpr', 'data protection', 'security',
                'contractual', 'agreement', 'terms', 'conditions'
            ],
            'performance': [
                'performance', 'efficiency', 'success', 'failure', 'speed', 'fast',
                'slow', 'quick', 'time', 'duration', 'latency', 'throughput',
                'reliability', 'uptime', 'downtime', 'availability', 'stability',
                'error', 'bug', 'issue', 'problem', 'quality', 'accuracy',
                'benchmark', 'metric', 'kpi', 'sla', 'optimization'
            ],
            'user_analytics': [
                'user', 'activity', 'engagement', 'productivity', 'person', 'people',
                'team', 'member', 'employee', 'staff', 'worker', 'operator',
                'login', 'session', 'active', 'inactive', 'usage', 'behavior',
                'pattern', 'trend', 'adoption', 'utilization', 'interaction'
            ],
            'operational': [
                'batch', 'agent', 'system', 'health', 'status', 'job', 'task',
                'workflow', 'pipeline', 'queue', 'process', 'operation',
                'running', 'completed', 'failed', 'pending', 'cancelled',
                'monitoring', 'alert', 'notification', 'log', 'event',
                'deployment', 'infrastructure', 'service', 'application'
            ],
            'ai_models': [
                'model', 'ai', 'ml', 'artificial intelligence', 'machine learning',
                'llm', 'language model', 'gpt', 'gemini', 'claude', 'openai',
                'anthropic', 'google', 'huggingface', 'transformer', 'neural',
                'training', 'inference', 'prediction', 'classification'
            ],
            'time_analysis': [
                'today', 'yesterday', 'week', 'month', 'year', 'daily', 'weekly',
                'monthly', 'quarterly', 'annually', 'recent', 'latest', 'current',
                'historical', 'trend', 'over time', 'timeline', 'period', 'range',
                'since', 'until', 'before', 'after', 'between'
            ],
            'data_analysis': [
                'show', 'list', 'display', 'find', 'search', 'get', 'retrieve',
                'count', 'total', 'sum', 'average', 'mean', 'median', 'max',
                'maximum', 'min', 'minimum', 'top', 'bottom', 'best', 'worst',
                'compare', 'comparison', 'versus', 'vs', 'against', 'between',
                'distribution', 'breakdown', 'summary', 'overview', 'report'
            ]
        }
        
        # Collection keyword mapping for improved query routing
        self.collection_keywords = {
            'costevalutionforllm': [
                'cost', 'spending', 'budget', 'token', 'price', 'billing', 'llm',
                'model', 'ai cost', 'expensive', 'cheap', 'usage cost'
            ],
            'documentextractions': [
                'document', 'extraction', 'confidence', 'extract', 'process',
                'accuracy', 'text', 'content', 'parse', 'scan', 'read'
            ],
            'obligationextractions': [
                'obligation', 'compliance', 'legal', 'requirement', 'mandate',
                'policy', 'rule', 'law', 'regulation', 'contractual'
            ],
            'agent_activity': [
                'agent', 'performance', 'activity', 'success', 'failure',
                'outcome', 'digitization', 'automation', 'bot'
            ],
            'batches': [
                'batch', 'job', 'processing', 'bulk', 'queue', 'workflow',
                'pipeline', 'task', 'operation', 'status'
            ],
            'files': [
                'file', 'upload', 'storage', 'document', 'pdf', 'image',
                'size', 'download', 'blob', 'container'
            ],
            'users': [
                'user', 'person', 'people', 'member', 'employee', 'staff',
                'account', 'profile', 'login', 'active'
            ],
            'conversations': [
                'conversation', 'chat', 'message', 'talk', 'discussion',
                'session', 'communication', 'dialogue'
            ],
            'prompts': [
                'prompt', 'template', 'instruction', 'query', 'request',
                'command', 'ai prompt', 'question', 'input'
            ],
            'compliances': [
                'compliance', 'audit', 'review', 'check', 'validation',
                'verification', 'assessment', 'evaluation'
            ]
        }
    
    def validate_pipeline(self, pipeline, collection_name):
        """Validate MongoDB aggregation pipeline for GenAI collections"""
        try:
            if not isinstance(pipeline, list):
                raise ValueError("Pipeline must be a list")
            
            if collection_name not in self.schema:
                raise ValueError(f"Unknown collection: {collection_name}")
            
            # Basic validation - check for required fields
            valid_fields = self.schema[collection_name]['fields']
            
            # Validate pipeline stages contain valid fields
            for stage in pipeline:
                if isinstance(stage, dict):
                    self._validate_stage_fields(stage, valid_fields, collection_name)
            
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid pipeline: {str(e)}")
    
    def _validate_stage_fields(self, stage: Dict, valid_fields: List[str], collection_name: str):
        """Validate that stage uses valid fields for the collection"""
        # Extract field references from stage
        stage_str = json.dumps(stage)
        
        # Find field references (basic validation)
        field_patterns = re.findall(r'"([a-zA-Z_][a-zA-Z0-9_]*)":', stage_str)
        
        for field in field_patterns:
            if field not in valid_fields and not field.startswith('$'):
                logger.warning(f"Field '{field}' not found in {collection_name} schema")
    
    def optimize_pipeline(self, pipeline):
        """Optimize MongoDB aggregation pipeline for better performance"""
        if not isinstance(pipeline, list):
            return pipeline
        
        optimized = []
        match_stages = []
        other_stages = []
        
        # Separate match stages from other stages
        for stage in pipeline:
            if isinstance(stage, dict) and '$match' in stage:
                match_stages.append(stage)
            else:
                other_stages.append(stage)
        
        # Add match stages first (better performance)
        optimized.extend(match_stages)
        optimized.extend(other_stages)
        
        # Add default limit if not present
        has_limit = any(isinstance(stage, dict) and '$limit' in stage for stage in optimized)
        if not has_limit:
            optimized.append({"$limit": 50})
        
        return optimized
    
    def add_date_filters(self, pipeline, date_range=None, date_field=None):
        """Add date filters to pipeline based on common patterns for GenAI operations"""
        if not date_range:
            return pipeline
        
        # Determine date field to use
        if not date_field:
            # Smart date field detection for GenAI collections
            common_date_fields = ['createdAt', 'updatedAt', 'timestamp', 'date', 'last_updated']
            date_field = common_date_fields[0]  # Default
        
        # Calculate date ranges
        now = datetime.now()
        date_match = {}
        
        if date_range == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_match = {date_field: {"$gte": start_of_day}}
            
        elif date_range == "yesterday":
            yesterday = now - timedelta(days=1)
            start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            date_match = {
                date_field: {
                    "$gte": start_of_yesterday,
                    "$lte": end_of_yesterday
                }
            }
            
        elif date_range == "last_week":
            week_ago = now - timedelta(days=7)
            date_match = {date_field: {"$gte": week_ago}}
            
        elif date_range == "last_month":
            month_ago = now - timedelta(days=30)
            date_match = {date_field: {"$gte": month_ago}}
            
        elif date_range == "last_quarter":
            quarter_ago = now - timedelta(days=90)
            date_match = {date_field: {"$gte": quarter_ago}}
            
        elif date_range == "last_year":
            year_ago = now - timedelta(days=365)
            date_match = {date_field: {"$gte": year_ago}}
        
        # Add date filter to pipeline
        if date_match:
            pipeline.insert(0, {"$match": date_match})
        
        return pipeline
    
    def get_collection_info(self, collection_name):
        """Get metadata about a GenAI collection"""
        if collection_name not in self.schema:
            return None
        
        schema_info = self.schema[collection_name]
        
        try:
            # Get actual document count
            collection = self.db[collection_name]
            sample_count = collection.count_documents({})
        except Exception as e:
            logger.warning(f"Could not get document count for {collection_name}: {e}")
            sample_count = 0
        
        return {
            "name": collection_name,
            "description": schema_info.get('description', f'GenAI {collection_name} collection'),
            "fields": schema_info['fields'],
            "numeric_fields": schema_info.get('numeric_fields', []),
            "date_fields": schema_info.get('date_fields', []),
            "group_by_fields": schema_info.get('group_by_fields', []),
            "key_metrics": schema_info.get('key_metrics', []),
            "sample_count": sample_count,
            "domain": "AI Operations & Document Intelligence"
        }
    
    def suggest_collection_for_query(self, user_question: str) -> str:
        """Suggest the best collection based on query content"""
        question_lower = user_question.lower()
        
        # Score each collection based on keyword matches
        collection_scores = {}
        
        for collection_name, schema_info in self.schema.items():
            score = 0
            
            # Check description keywords
            description = schema_info.get('description', '').lower()
            if any(word in description for word in question_lower.split()):
                score += 2
            
            # Check field name matches
            fields = [field.lower() for field in schema_info.get('fields', [])]
            for word in question_lower.split():
                if word in fields:
                    score += 3
            
            # GenAI-specific pattern matching
            for pattern_type, keywords in self.genai_patterns.items():
                if any(keyword in question_lower for keyword in keywords):
                    if pattern_type == 'cost_analysis' and 'cost' in collection_name.lower():
                        score += 5
                    elif pattern_type == 'document_processing' and 'document' in collection_name.lower():
                        score += 5
                    elif pattern_type == 'compliance' and 'obligation' in collection_name.lower():
                        score += 5
                    elif pattern_type == 'performance' and 'agent' in collection_name.lower():
                        score += 5
                    else:
                        score += 1
            
            collection_scores[collection_name] = score
        
        # Return collection with highest score
        if collection_scores:
            best_collection = max(collection_scores, key=collection_scores.get)
            if collection_scores[best_collection] > 0:
                return best_collection
        
        # Default fallback to most data-rich collection
        return 'documentextractions'
    
    def build_simple_pipeline(self, collection_name: str, query_type: str = 'overview') -> List[Dict]:
        """Build a simple pipeline for basic queries"""
        pipeline = []
        
        schema_info = self.schema.get(collection_name, {})
        
        # Add basic match if needed
        if query_type == 'recent':
            date_fields = schema_info.get('date_fields', [])
            if date_fields:
                recent_date = datetime.now() - timedelta(days=7)
                pipeline.append({
                    "$match": {date_fields[0]: {"$gte": recent_date}}
                })
        
        # Add grouping for summary queries
        if query_type == 'summary':
            group_fields = schema_info.get('group_by_fields', [])
            if group_fields:
                pipeline.append({
                    "$group": {
                        "_id": f"${group_fields[0]}",
                        "count": {"$sum": 1}
                    }
                })
                pipeline.append({"$sort": {"count": -1}})
        
        # Add default sort and limit
        if not any('$group' in str(stage) for stage in pipeline):
            date_fields = schema_info.get('date_fields', [])
            sort_field = date_fields[0] if date_fields else '_id'
            pipeline.append({"$sort": {sort_field: -1}})
        
        pipeline.append({"$limit": 15})
        
        return pipeline


class ChartTypeSelector:
    """Utility class for selecting appropriate chart types for GenAI operations"""
    
    @staticmethod
    def determine_chart_type(query_intent, data_structure=None, collection_name=None):
        """Determine the best chart type based on query intent and GenAI context"""
        
        if not query_intent:
            return 'bar'
        
        query_lower = query_intent.lower()
        
        # Time-based queries (great for AI operations trends)
        if any(keyword in query_lower for keyword in [
            'trend', 'over time', 'monthly', 'quarterly', 'daily', 'weekly',
            'history', 'timeline', 'progression', 'evolution'
        ]):
            return 'line'
        
        # Distribution queries (common in AI operations)
        if any(keyword in query_lower for keyword in [
            'distribution', 'breakdown', 'split', 'percentage', 'share',
            'composition', 'proportion', 'allocation'
        ]):
            return 'pie'
        
        # Comparison queries (important for cost/performance analysis)
        if any(keyword in query_lower for keyword in [
            'compare', 'vs', 'versus', 'top', 'ranking', 'best', 'worst',
            'highest', 'lowest', 'most', 'least'
        ]):
            return 'bar'
        
        # Cost-specific visualizations
        if any(keyword in query_lower for keyword in [
            'cost', 'spending', 'budget', 'expensive', 'price'
        ]):
            if any(time_word in query_lower for time_word in ['month', 'week', 'day', 'time']):
                return 'line'  # Cost trends
            else:
                return 'bar'   # Cost comparisons
        
        # Performance metrics
        if any(keyword in query_lower for keyword in [
            'performance', 'efficiency', 'success rate', 'confidence'
        ]):
            return 'bar'
        
        # Collection-specific defaults
        if collection_name:
            if collection_name in ['costevalutionforllm', 'llmpricing']:
                return 'line'  # Cost data often shown over time
            elif collection_name in ['agent_activity', 'batches']:
                return 'bar'   # Performance metrics
            elif collection_name in ['obligationextractions', 'compliances']:
                return 'pie'   # Distribution of obligation types
        
        # Default based on data structure
        if data_structure:
            if isinstance(data_structure, list) and len(data_structure) <= 5:
                return 'pie'
            elif isinstance(data_structure, list) and len(data_structure) > 10:
                return 'bar'
        
        return 'bar'  # Safe default
    
    @staticmethod
    def get_chart_config(chart_type, title="GenAI Analytics", collection_name=None):
        """Get Chart.js configuration for different chart types with GenAI styling"""
        
        # Enhanced title based on collection
        if collection_name:
            collection_titles = {
                'costevalutionforllm': 'AI Cost Analysis',
                'documentextractions': 'Document Processing Analytics',
                'obligationextractions': 'Compliance Obligation Analysis',
                'agent_activity': 'Agent Performance Metrics',
                'batches': 'Batch Processing Analytics',
                'users': 'User Activity Analysis'
            }
            title = collection_titles.get(collection_name, f"{collection_name.title()} Analytics")
        
        base_config = {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {
                    "display": True,
                    "text": title,
                    "font": {
                        "size": 16,
                        "weight": "bold"
                    },
                    "color": "#1F2937"
                },
                "tooltip": {
                    "backgroundColor": "rgba(0, 0, 0, 0.8)",
                    "titleColor": "#FFFFFF",
                    "bodyColor": "#FFFFFF",
                    "cornerRadius": 6
                }
            }
        }
        
        # Chart-specific configurations
        if chart_type in ['pie', 'doughnut']:
            base_config["plugins"]["legend"] = {
                "display": True,
                "position": "right",
                "labels": {
                    "usePointStyle": True,
                    "padding": 20
                }
            }
            
            # Add percentage display for pie charts
            if chart_type == 'doughnut':
                base_config["cutout"] = "60%"
            
        else:
            # Bar and line charts
            base_config["scales"] = {
                "y": {
                    "beginAtZero": True,
                    "grid": {
                        "color": "rgba(0, 0, 0, 0.1)"
                    },
                    "ticks": {
                        "color": "#6B7280"
                    }
                },
                "x": {
                    "display": True,
                    "grid": {
                        "display": False
                    },
                    "ticks": {
                        "color": "#6B7280",
                        "maxRotation": 45
                    }
                }
            }
            
            base_config["plugins"]["legend"] = {
                "display": False
            }
            
            # Line chart specific settings
            if chart_type == 'line':
                base_config["elements"] = {
                    "line": {
                        "tension": 0.4,
                        "borderWidth": 3
                    },
                    "point": {
                        "radius": 5,
                        "hoverRadius": 7
                    }
                }
        
        return base_config
    
    @staticmethod
    def get_color_palette(chart_type, data_count=1):
        """Get appropriate color palette for GenAI operations charts"""
        
        # Professional color palette for business analytics
        colors = {
            'primary': '#3B82F6',      # Blue
            'success': '#10B981',      # Green
            'warning': '#F59E0B',      # Amber
            'danger': '#EF4444',       # Red
            'info': '#06B6D4',         # Cyan
            'purple': '#8B5CF6',       # Purple
            'pink': '#EC4899',         # Pink
            'indigo': '#6366F1',       # Indigo
            'orange': '#F97316',       # Orange
            'teal': '#14B8A6'          # Teal
        }
        
        color_list = list(colors.values())
        
        if chart_type in ['pie', 'doughnut']:
            # Return multiple colors for pie charts
            return color_list[:data_count] if data_count <= len(color_list) else color_list * ((data_count // len(color_list)) + 1)
        else:
            # Single color for bar/line charts
            return colors['primary']


class PromptBuilder:
    """Utility class for building prompts for Gemini with GenAI operations focus"""
    
    @staticmethod
    def build_query_prompt(user_question, schema_info):
        """Build a comprehensive prompt for MongoDB query generation"""
        
        # Extract available collections and their purposes
        collection_summaries = []
        for collection, details in schema_info.get('collections', {}).items():
            description = details.get('description', f'{collection} data')
            fields = details.get('fields', [])[:5]  # Show first 5 fields
            collection_summaries.append(f"- {collection}: {description} (fields: {', '.join(fields)})")
        
        prompt = f"""
You are an expert MongoDB query generator for AI Operations & Document Intelligence systems.

AVAILABLE COLLECTIONS:
{chr(10).join(collection_summaries[:15])}  

USER QUESTION: "{user_question}"

TASK: Generate a MongoDB aggregation pipeline and chart configuration.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON - no markdown, no explanations
2. Choose the most relevant collection for the query
3. Create an efficient aggregation pipeline
4. Select appropriate chart type for visualization
5. Provide meaningful chart labels and mapping

REQUIRED JSON STRUCTURE:
{{
  "collection": "collection_name",
  "pipeline": [
    {{"$match": {{"field": "value"}}}},
    {{"$group": {{"_id": "$field", "count": {{"$sum": 1}}}}}},
    {{"$sort": {{"count": -1}}}},
    {{"$limit": 10}}
  ],
  "chart_type": "bar|pie|line|doughnut",
  "chart_mapping": {{
    "labels_field": "_id",
    "data_field": "count",
    "title": "Descriptive Chart Title"
  }},
  "reasoning": "Brief explanation of choices"
}}

GENAI OPERATIONS CONTEXT:
- Focus on AI costs, document processing, compliance, and operational metrics
- Prioritize actionable business insights
- Consider time-based analysis for trends
- Group by meaningful dimensions (user, type, status, etc.)

JSON only - no other text:"""
        
        return prompt
    
    @staticmethod
    def build_insights_prompt(user_question, query_data, raw_results, context=None):
        """Build prompt for generating insights from query results"""
        
        # Prepare result summary
        result_summary = {
            "collection": query_data.get("collection", "unknown"),
            "result_count": len(raw_results),
            "sample_data": raw_results[:3] if raw_results else []
        }
        
        # Add context if available
        context_info = ""
        if context:
            context_info = f"\nCONTEXT: {json.dumps(context, indent=2)}"
        
        prompt = f"""
Generate insights and analysis for AI Operations data.

QUERY: "{user_question}"
COLLECTION: {result_summary["collection"]}
RESULTS: {json.dumps(result_summary, indent=2, default=str)}
{context_info}

TASK: Provide business insights, chart configuration, and recommendations.

RESPONSE FORMAT (JSON only):
{{
  "chart_type": "bar|pie|line|doughnut",
  "chart_config": {{
    "type": "chart_type",
    "data": {{
      "labels": ["label1", "label2"],
      "datasets": [{{
        "label": "Dataset Name",
        "data": [100, 200],
        "backgroundColor": ["#3B82F6", "#10B981"],
        "borderColor": "#3B82F6",
        "borderWidth": 2
      }}]
    }},
    "options": {{
      "responsive": true,
      "plugins": {{
        "title": {{"display": true, "text": "Chart Title"}}
      }}
    }}
  }},
  "summary": "2-3 sentence executive summary with key findings",
  "insights": [
    "Specific insight with data points",
    "Operational finding with implications",
    "Trend or pattern identification"
  ],
  "recommendations": [
    "Actionable recommendation for optimization",
    "Strategic suggestion for improvement"
  ]
}}

FOCUS: AI operations optimization, cost efficiency, quality improvement, compliance management.

JSON only:"""
        
        return prompt


def validate_json_response(response_text: str) -> Dict:
    """Validate and parse JSON response from Gemini"""
    try:
        # Clean up response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith('```'):
            lines = cleaned_text.split('\n')
            cleaned_text = '\n'.join(lines[1:-1])
        
        # Remove any non-JSON text before the first {
        json_start = cleaned_text.find('{')
        if json_start > 0:
            cleaned_text = cleaned_text[json_start:]
        
        # Remove any text after the last }
        json_end = cleaned_text.rfind('}')
        if json_end > 0:
            cleaned_text = cleaned_text[:json_end + 1]
        
        # Parse JSON
        result = json.loads(cleaned_text)
        
        if not isinstance(result, dict):
            raise ValueError("Response must be a JSON object")
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to validate response: {str(e)}")


def build_sample_pipeline(collection_name: str, schema_info: Dict) -> List[Dict]:
    """Build a sample pipeline for testing purposes"""
    
    collection_schema = schema_info.get('collections', {}).get(collection_name, {})
    
    pipeline = []
    
    # Add basic match for recent data if date fields available
    date_fields = collection_schema.get('date_fields', [])
    if date_fields:
        recent_date = datetime.now() - timedelta(days=30)
        pipeline.append({
            "$match": {date_fields[0]: {"$gte": recent_date}}
        })
    
    # Add grouping by first group field if available
    group_fields = collection_schema.get('group_by_fields', [])
    if group_fields:
        pipeline.append({
            "$group": {
                "_id": f"${group_fields[0]}",
                "count": {"$sum": 1}
            }
        })
        pipeline.append({"$sort": {"count": -1}})
    
    # Add limit
    pipeline.append({"$limit": 10})
    
    return pipeline