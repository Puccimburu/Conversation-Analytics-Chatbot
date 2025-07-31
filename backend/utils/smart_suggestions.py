# backend/utils/smart_suggestions.py
"""
Smart Suggestions Generator for GenAI Operations
Generates intelligent follow-up questions based on conversation context and analysis results
"""

import logging
import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from config import DATABASE_SCHEMA  # Import GenAI schema

logger = logging.getLogger(__name__)

class SmartSuggestionGenerator:
    """
    Generates intelligent follow-up questions for GenAI operations and document intelligence
    """
    
    def __init__(self, gemini_client, memory_manager=None):
        self.gemini_client = gemini_client
        self.memory_manager = memory_manager
        
        # GenAI-specific default suggestions
        self.default_suggestions = [
            "What are our AI operational costs this month?",
            "Show me document extraction confidence trends",
            "Which compliance obligations need attention?",
            "How are our AI agents performing?",
            "Compare processing efficiency across document types"
        ]
        
        # Domain context for GenAI operations
        self.domain_context = {
            "domain": "AI Operations & Document Intelligence",
            "primary_collections": list(DATABASE_SCHEMA["collections"].keys()),
            "key_metrics": [
                "AI costs and spending", "document processing efficiency",
                "extraction confidence scores", "compliance obligation tracking",
                "agent performance metrics", "batch processing success rates"
            ],
            "analysis_focus_areas": [
                "cost_optimization", "quality_assurance", "compliance_management",
                "operational_efficiency", "user_productivity", "system_health"
            ]
        }
    
    async def generate_smart_suggestions(self, question: str, result: Dict, 
                                       conversation_context: Optional[Dict] = None) -> List[str]:
        """
        Generate contextual follow-up suggestions for GenAI operations
        """
        try:
            if not self.gemini_client:
                return self._get_contextual_fallback_suggestions(question, result)
            
            # Build context for suggestion generation
            suggestion_context = {
                "original_question": question,
                "result_summary": self._extract_result_summary(result),
                "domain": self.domain_context["domain"],
                "available_collections": self.domain_context["primary_collections"][:10],  # Top 10
                "conversation_context": conversation_context or {}
            }
            
            # Generate suggestions using Gemini
            suggestions = await self._generate_with_gemini(suggestion_context)
            
            if suggestions:
                # Validate and return suggestions
                validated = self._validate_genai_suggestions(suggestions)
                if validated:
                    logger.info(f"✅ Generated {len(validated)} smart suggestions")
                    return validated[:5]  # Return top 5
            
            # Fallback to contextual suggestions
            return self._get_contextual_fallback_suggestions(question, result)
            
        except Exception as e:
            logger.error(f"Smart suggestion generation failed: {e}")
            return self.get_default_suggestions()
    
    def _extract_result_summary(self, result: Dict) -> str:
        """Extract key information from analysis result"""
        summary_parts = []
        
        if result.get('success'):
            # Collection analyzed
            if result.get('query_data', {}).get('collection'):
                collection = result['query_data']['collection']
                summary_parts.append(f"Analyzed {collection}")
            
            # Results count
            if result.get('raw_results'):
                count = len(result['raw_results'])
                summary_parts.append(f"{count} records found")
            
            # Chart type
            if result.get('visualization', {}).get('chart_type'):
                chart_type = result['visualization']['chart_type']
                summary_parts.append(f"Displayed as {chart_type}")
            
            # Insights count
            if result.get('insights'):
                insight_count = len(result['insights'])
                summary_parts.append(f"{insight_count} insights generated")
        
        return "; ".join(summary_parts) if summary_parts else "Analysis completed"
    
    async def _generate_with_gemini(self, context: Dict) -> List[str]:
        """Generate suggestions using Gemini AI"""
        prompt = self._build_genai_suggestion_prompt(context)
        
        try:
            response = await self.gemini_client.generate_content_async(prompt)
            
            if response and hasattr(response, 'text'):
                return self._parse_suggestions_response(response.text)
            
            logger.warning("No valid response from Gemini")
            return []
            
        except Exception as e:
            logger.error(f"Gemini suggestion generation failed: {e}")
            return []
    
    def _build_genai_suggestion_prompt(self, context: Dict) -> str:
        """Build comprehensive prompt for GenAI operations suggestions"""
        available_collections = ", ".join(context['available_collections'][:8])
        
        return f"""
You are an AI Operations Analytics expert generating intelligent follow-up questions.

CONTEXT:
- Domain: {context['domain']}
- Original Question: "{context['original_question']}"
- Analysis Result: {context['result_summary']}
- Available Data: {available_collections}

TASK: Generate 5 intelligent follow-up questions for AI operations analysis.

FOCUS AREAS FOR GENAI OPERATIONS:
1. Cost Analysis & Optimization
   - AI spending patterns and efficiency
   - Model cost-effectiveness comparisons
   - Token usage optimization

2. Document Processing Intelligence
   - Extraction confidence and quality metrics
   - Processing time and success rates
   - Document type performance analysis

3. Compliance & Risk Management
   - Legal obligation tracking and assessment
   - Compliance status monitoring
   - Risk identification and mitigation

4. Operational Performance
   - Agent performance and success rates
   - Batch processing efficiency
   - System health and reliability

5. User Productivity & Insights
   - User activity and engagement patterns
   - Workflow optimization opportunities
   - System utilization metrics

EXAMPLE GOOD FOLLOW-UPS:
- "Which AI models are driving our highest costs?"
- "Show me documents with confidence scores below 90%"
- "What's causing batch processing delays this week?"
- "Which compliance obligations have the highest risk?"
- "How can we optimize our token usage efficiency?"

REQUIREMENTS:
- Questions should be specific and actionable for AI operations
- Focus on operational insights and business value
- Use natural, conversational language
- Avoid generic or vague questions
- Consider both immediate and strategic analysis needs

Generate exactly 5 smart follow-up questions as a JSON array:
["question 1", "question 2", "question 3", "question 4", "question 5"]
"""
    
    def _parse_suggestions_response(self, response_text: str) -> List[str]:
        """Parse suggestions from Gemini response"""
        try:
            # Find JSON array in response
            import re
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            
            if json_match:
                suggestions_json = json_match.group()
                suggestions = json.loads(suggestions_json)
                
                if isinstance(suggestions, list):
                    # Clean and validate each suggestion
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if isinstance(suggestion, str) and len(suggestion.strip()) > 10:
                            cleaned = suggestion.strip().strip('"\'')
                            if '?' in cleaned or any(word in cleaned.lower() 
                                                   for word in ['what', 'which', 'how', 'show', 'compare']):
                                cleaned_suggestions.append(cleaned)
                    
                    return cleaned_suggestions[:8]  # Return up to 8 for validation
            
            # Fallback: try to extract lines that look like questions
            lines = response_text.strip().split('\n')
            questions = []
            
            for line in lines:
                line = line.strip()
                # Remove numbering, bullets
                line = re.sub(r'^\d+[\.\)]\s*', '', line)
                line = re.sub(r'^[-•*]\s*', '', line)
                line = line.strip('"\'')
                
                if line and len(line) > 10 and ('?' in line or 
                    any(word in line.lower() for word in ['what', 'which', 'how', 'show'])):
                    questions.append(line)
            
            return questions[:8]
            
        except Exception as e:
            logger.error(f"Failed to parse suggestions response: {e}")
            return []
    
    def _validate_genai_suggestions(self, suggestions: List[str]) -> List[str]:
        """Validate suggestions for GenAI operations relevance"""
        if not suggestions:
            return []
        
        validated = []
        
        # GenAI operations keywords (good indicators)
        good_keywords = [
            # AI Operations
            'cost', 'spending', 'efficiency', 'token', 'model', 'ai', 'llm',
            # Document Processing  
            'document', 'extraction', 'confidence', 'processing', 'batch',
            # Compliance & Legal
            'compliance', 'obligation', 'legal', 'risk', 'regulatory',
            # Performance & Analytics
            'performance', 'success', 'failure', 'trend', 'pattern',
            # User & System
            'user', 'agent', 'system', 'operational', 'workflow'
        ]
        
        # Irrelevant or problematic keywords (bad indicators)
        bad_keywords = [
            'weather', 'sports', 'entertainment', 'recipes', 'jokes', 'games',
            'personal', 'dating', 'shopping', 'travel', 'social media',
            'external api', 'real-time stock', 'cryptocurrency'
        ]
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            # Skip if contains bad keywords
            has_bad_keywords = any(bad_word in suggestion_lower for bad_word in bad_keywords)
            if has_bad_keywords:
                continue
            
            # Check for good keywords or analytical patterns
            has_good_keywords = any(good_word in suggestion_lower for good_word in good_keywords)
            has_analytical_pattern = any(pattern in suggestion_lower for pattern in [
                'what', 'which', 'how', 'show', 'compare', 'analyze', 'track', 
                'find', 'identify', 'optimize', 'improve'
            ])
            
            # Check for GenAI-specific collection names
            has_genai_collections = any(collection in suggestion_lower for collection in [
                'cost', 'document', 'extraction', 'obligation', 'compliance',
                'agent', 'batch', 'processing', 'user'
            ])
            
            if (has_good_keywords or has_analytical_pattern or has_genai_collections):
                validated.append(suggestion)
        
        return validated
    
    def _get_contextual_fallback_suggestions(self, question: str, result: Dict) -> List[str]:
        """Generate contextual fallback suggestions based on question and result patterns"""
        question_lower = question.lower()
        suggestions = []
        
        # Cost-related follow-ups
        if any(keyword in question_lower for keyword in ['cost', 'spending', 'price', 'expensive', 'budget']):
            suggestions.extend([
                'Which AI models are most cost-effective?',
                'Show me cost trends over the last 3 months',
                'Compare costs between different document types',
                'Which users or processes generate highest costs?'
            ])
        
        # Document processing follow-ups
        elif any(keyword in question_lower for keyword in ['document', 'extraction', 'confidence', 'processing']):
            suggestions.extend([
                'Show me documents with low confidence scores',
                'Which document types have highest processing accuracy?',
                'What are our document extraction success rates?',
                'Compare processing times by document complexity'
            ])
        
        # Compliance and legal follow-ups
        elif any(keyword in question_lower for keyword in ['compliance', 'obligation', 'legal', 'risk', 'regulatory']):
            suggestions.extend([
                'What are our highest risk compliance items?',
                'Show me recent compliance obligation changes',
                'Which contracts need immediate compliance review?',
                'Track compliance resolution progress over time'
            ])
        
        # Agent and performance follow-ups
        elif any(keyword in question_lower for keyword in ['agent', 'performance', 'batch', 'success', 'failure']):
            suggestions.extend([
                'How can we improve processing agent performance?',
                'Show me batch processing failure patterns',
                'Which agents handle complex documents most effectively?',
                'What are the main causes of processing delays?'
            ])
        
        # User and system follow-ups
        elif any(keyword in question_lower for keyword in ['user', 'activity', 'system', 'health', 'usage']):
            suggestions.extend([
                'Which users are most active in the system?',
                'Show me system health and performance metrics',
                'How can we optimize user workflow efficiency?',
                'What are our peak usage patterns?'
            ])
        
        # General operational follow-ups
        else:
            suggestions.extend([
                'What are our key operational metrics today?',
                'Show me overall system performance overview',
                'Which areas need immediate operational attention?',
                'Compare this month vs last month performance'
            ])
        
        # Add result-specific suggestions based on collection analyzed
        if result.get('query_data', {}).get('collection'):
            collection = result['query_data']['collection']
            
            if collection == 'costevalutionforllm':
                suggestions.append('Break down AI costs by model and operation type')
            elif collection == 'documentextractions':
                suggestions.append('Show extraction confidence score distribution')
            elif collection == 'obligationextractions':
                suggestions.append('Which obligations require immediate action?')
            elif collection == 'agent_activity':
                suggestions.append('Compare agent performance across document types')
            elif collection == 'batches':
                suggestions.append('Analyze batch processing efficiency trends')
            elif collection == 'users':
                suggestions.append('Show user engagement and activity patterns')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Return top 5
    
    def get_default_suggestions(self) -> List[str]:
        """Get default fallback suggestions for GenAI operations"""
        return self.default_suggestions.copy()
    
    def get_domain_specific_suggestions(self, domain_area: str) -> List[str]:
        """Get suggestions specific to a domain area"""
        domain_suggestions = {
            "cost_analysis": [
                "What's driving our highest AI operational costs?",
                "Compare cost efficiency across different AI models",
                "Show me cost optimization opportunities",
                "Which processes have the best cost-to-value ratio?"
            ],
            "document_processing": [
                "Which document types have lowest confidence scores?",
                "Show me processing time trends by document complexity",
                "What's our document extraction accuracy rate?",
                "Compare processing success across different agents"
            ],
            "compliance_management": [
                "What are our most critical compliance gaps?",
                "Show me high-risk legal obligations by category",
                "Which documents need compliance review priority?",
                "Track our compliance resolution progress"
            ],
            "operational_efficiency": [
                "Where are our biggest operational bottlenecks?",
                "Show me system performance and reliability metrics",
                "Which workflows can be optimized for efficiency?",
                "What's our overall operational health score?"
            ],
            "user_productivity": [
                "Which users are most productive in our system?",
                "Show me user engagement and activity patterns",
                "What features drive highest user satisfaction?",
                "How can we improve user workflow efficiency?"
            ]
        }
        
        return domain_suggestions.get(domain_area, self.get_default_suggestions())
    
    def generate_contextual_suggestions_by_collection(self, collection_name: str) -> List[str]:
        """Generate suggestions based on the specific collection being analyzed"""
        collection_suggestions = {
            "costevalutionforllm": [
                "Which AI models have the best cost-performance ratio?",
                "Show me token usage efficiency trends",
                "Compare costs across different operation types",
                "What's driving our AI spending spikes?"
            ],
            "documentextractions": [
                "Which document types have highest confidence scores?",
                "Show me extraction accuracy trends over time",
                "Compare processing success by document complexity",
                "What causes low confidence extractions?"
            ],
            "obligationextractions": [
                "What are our highest priority legal obligations?",
                "Show me compliance risk assessment by category",
                "Which obligations have approaching deadlines?",
                "Compare obligation complexity across document types"
            ],
            "agent_activity": [
                "Which agents have the best success rates?",
                "Show me agent performance trends over time",
                "Compare agent efficiency across document types",
                "What improves agent processing accuracy?"
            ],
            "batches": [
                "Which batch types have highest success rates?",
                "Show me processing time trends by batch size",
                "Compare batch efficiency across time periods",
                "What causes batch processing failures?"
            ],
            "users": [
                "Which users are most active in our system?",
                "Show me user engagement patterns over time",
                "Compare user productivity across different roles",
                "What features do power users utilize most?"
            ],
            "conversations": [
                "What are the most common conversation topics?",
                "Show me user interaction patterns",
                "Compare conversation success rates",
                "Which conversation types need improvement?"
            ]
        }
        
        return collection_suggestions.get(collection_name, self.get_default_suggestions())


# Utility functions for suggestion enhancement
def extract_key_metrics_from_result(result: Dict) -> List[str]:
    """Extract key metrics mentioned in the analysis result"""
    metrics = []
    
    if result.get('insights'):
        for insight in result['insights']:
            # Extract numbers with units (currency, percentages, counts)
            import re
            currency_matches = re.findall(r'\$[\d,]+(?:\.\d{2})?', insight)
            percentage_matches = re.findall(r'\d+(?:\.\d+)?%', insight)
            count_matches = re.findall(r'\b\d+\s*(?:documents|users|batches|items)\b', insight, re.IGNORECASE)
            
            metrics.extend(currency_matches)
            metrics.extend(percentage_matches)
            metrics.extend(count_matches)
    
    return list(set(metrics))  # Remove duplicates

def identify_improvement_opportunities(result: Dict) -> List[str]:
    """Identify potential improvement opportunities from analysis results"""
    opportunities = []
    
    if result.get('insights'):
        for insight in result['insights']:
            insight_lower = insight.lower()
            
            # Look for improvement indicators
            if any(indicator in insight_lower for indicator in ['low', 'below', 'decrease', 'poor', 'fail']):
                opportunities.append(f"Investigate: {insight[:50]}...")
            elif any(indicator in insight_lower for indicator in ['high', 'above', 'increase', 'excellent', 'success']):
                opportunities.append(f"Leverage: {insight[:50]}...")
    
    return opportunities[:3]  # Return top 3 opportunities

def suggest_comparative_analysis(collection_name: str, result: Dict) -> List[str]:
    """Suggest comparative analysis based on current result"""
    comparative_suggestions = []
    
    # Time-based comparisons
    comparative_suggestions.append(f"Compare current {collection_name} metrics with last month")
    comparative_suggestions.append(f"Show {collection_name} trends over the last 6 months")
    
    # Category-based comparisons
    if collection_name == 'costevalutionforllm':
        comparative_suggestions.append("Compare costs across different AI models")
    elif collection_name == 'documentextractions':
        comparative_suggestions.append("Compare extraction accuracy across document types")
    elif collection_name == 'obligationextractions':
        comparative_suggestions.append("Compare compliance risk across obligation categories")
    
    return comparative_suggestions