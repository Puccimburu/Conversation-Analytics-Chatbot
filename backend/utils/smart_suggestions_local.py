# backend/utils/smart_suggestions.py
"""
Smart Follow-up Question Generator using Memory RAG + Gemini
Generates contextual suggestions that can be answered by the existing system
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartSuggestionGenerator:
    """
    Generates intelligent follow-up questions using conversation context
    """
    
    def __init__(self, gemini_client, memory_manager=None):
        self.gemini_client = gemini_client
        self.memory_manager = memory_manager
        
        # Default fallback suggestions (your current ones)
        self.default_suggestions = [
            'Show this as a different chart type',
            'What are the monthly trends?',
            'How does this compare to last year?',
            'Show me the top 10 results',
            'Break this down by region',
            'Analyze the seasonal patterns'
        ]
        
        # Database schema awareness for generating answerable questions
        self.available_collections = ['sales', 'products', 'customers', 'user_engagement']
        self.available_fields = {
            'sales': ['order_id', 'customer_id', 'product_id', 'product_name', 'category', 
                     'quantity', 'unit_price', 'total_amount', 'discount', 'date', 'month', 
                     'quarter', 'sales_rep', 'region'],
            'products': ['product_id', 'name', 'category', 'brand', 'price', 'cost', 
                        'stock', 'rating', 'reviews_count'],
            'customers': ['customer_id', 'name', 'email', 'age', 'gender', 'country', 
                         'state', 'city', 'customer_segment', 'total_spent', 'order_count']
        }
    
    async def generate_smart_suggestions(self, chat_id: str, current_result: Dict, 
                                       user_question: str) -> List[str]:
        """
        Generate context-aware follow-up suggestions
        Returns default suggestions if AI generation fails (failsafe)
        """
        try:
            # Quick background generation - don't block main response
            suggestions = await asyncio.wait_for(
                self._generate_contextual_suggestions(chat_id, current_result, user_question),
                timeout=5.0  # 5 second timeout to not delay UI
            )
            
            # Validate suggestions are answerable by our system
            validated_suggestions = self._validate_suggestions(suggestions)
            
            if len(validated_suggestions) >= 3:
                logger.info(f"✅ Generated {len(validated_suggestions)} smart suggestions")
                return validated_suggestions[:6]  # Max 6 suggestions
            else:
                logger.info("🔄 Using default suggestions (validation failed)")
                return self.default_suggestions
                
        except asyncio.TimeoutError:
            logger.info("⏱️ Suggestion generation timeout - using defaults")
            return self.default_suggestions
        except Exception as e:
            logger.error(f"❌ Suggestion generation failed: {e}")
            return self.default_suggestions
    
    async def _generate_contextual_suggestions(self, chat_id: str, current_result: Dict, 
                                             user_question: str) -> List[str]:
        """Generate suggestions using Gemini with full context"""
        
        # Build context from memory if available
        memory_context = ""
        if self.memory_manager and chat_id:
            try:
                context = await self.memory_manager.build_conversation_context(chat_id, user_question)
                memory_context = f"""
CONVERSATION CONTEXT:
- Themes: {', '.join(context.conversation_themes[:3])}
- Recent entities: {', '.join(context.recent_entities[:5])}
- User preferences: {json.dumps(context.user_preferences) if context.user_preferences else 'None'}
"""
            except:
                memory_context = ""
        
        # Extract key info from current result
        chart_type = current_result.get('chart_data', {}).get('type', 'unknown')
        summary = current_result.get('summary', '')
        insights = current_result.get('insights', [])
        data_points = len(current_result.get('chart_data', {}).get('data', {}).get('labels', []))
        
        # Create intelligent prompt
        prompt = f"""
You are an analytics assistant. Based on the user's question and current results, generate 5 smart follow-up questions that naturally extend the analysis.

USER QUESTION: "{user_question}"

CURRENT ANALYSIS:
- Chart type: {chart_type}
- Summary: {summary}
- Key insights: {'; '.join(insights[:2]) if insights else 'None'}
- Data points shown: {data_points}

{memory_context}

AVAILABLE DATA STRUCTURE:
- Sales data: order_id, customer_id, product_name, category, quantity, unit_price, total_amount, date, month, quarter, region
- Product data: name, category, brand, price, cost, stock, rating
- Customer data: customer_segment, age, gender, country, state, city, total_spent

GENERATE 5 follow-up questions that:
1. Build naturally on the current analysis
2. Can be answered with the available data fields
3. Provide deeper business insights
4. Use conversational, business-friendly language
5. Focus on actionable analysis (trends, comparisons, segments)

Examples of good follow-ups:
- "What drove the January sales spike?"
- "Which product categories performed best?"
- "How do our top customers compare by region?"
- "What's the seasonal pattern in this data?"

Return ONLY a JSON array of 5 question strings, no other text:
["question 1", "question 2", "question 3", "question 4", "question 5"]
"""

        try:
            response = await self.gemini_client.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Find JSON array in response
            import re
            json_match = re.search(r'\[.*?\]', response_text, re.DOTALL)
            if json_match:
                suggestions_json = json_match.group()
                suggestions = json.loads(suggestions_json)
                
                if isinstance(suggestions, list) and len(suggestions) > 0:
                    return [str(s).strip() for s in suggestions if s.strip()]
            
            logger.warning("⚠️ Failed to parse Gemini suggestions response")
            return []
            
        except Exception as e:
            logger.error(f"❌ Gemini suggestion generation failed: {e}")
            return []
    
    def _validate_suggestions(self, suggestions: List[str]) -> List[str]:
        """
        Validate that suggestions can likely be answered by our system
        Filter out questions that reference unavailable data
        """
        validated = []
        
        # Keywords that indicate answerable questions
        good_keywords = [
            'sales', 'revenue', 'customers', 'products', 'category', 'region', 
            'month', 'quarter', 'trends', 'compare', 'top', 'bottom', 'best', 
            'worst', 'segment', 'price', 'cost', 'rating', 'brand', 'age',
            'country', 'state', 'city', 'total', 'average', 'highest', 'lowest'
        ]
        
        # Keywords that indicate potentially problematic questions
        bad_keywords = [
            'external', 'api', 'real-time', 'live', 'current', 'today',
            'competitor', 'market share', 'social media', 'weather',
            'stock price', 'exchange rate', 'gdp', 'inflation'
        ]
        
        for suggestion in suggestions:
            suggestion_lower = suggestion.lower()
            
            # Check for bad keywords
            has_bad_keywords = any(bad_word in suggestion_lower for bad_word in bad_keywords)
            if has_bad_keywords:
                continue
            
            # Check for good keywords or general analytical patterns
            has_good_keywords = any(good_word in suggestion_lower for good_word in good_keywords)
            has_analytical_pattern = any(pattern in suggestion_lower for pattern in [
                'what', 'which', 'how', 'show', 'compare', 'analyze', 'breakdown'
            ])
            
            if has_good_keywords or has_analytical_pattern:
                validated.append(suggestion)
        
        return validated

    def get_default_suggestions(self) -> List[str]:
        """Get the default fallback suggestions"""
        return self.default_suggestions.copy()