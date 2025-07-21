# backend/utils/conversational_handler.py
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class ConversationalHandler:
    """
    Handles conversational queries like greetings, system information, and general help.
    Generates dynamic responses based on the available dataset.
    """
    
    def __init__(self, database_manager, gemini_client):
        self.db_manager = database_manager
        self.gemini_client = gemini_client
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> Dict:
        """Get database schema information"""
        return {
            "collections": {
                "sales": {
                    "description": "Sales transaction records",
                    "fields": ["order_id", "customer_id", "product_id", "product_name", 
                              "category", "quantity", "unit_price", "total_amount", 
                              "discount", "date", "month", "quarter", "sales_rep", "region"],
                    "sample_categories": ["Laptops", "Smartphones", "Audio", "Tablets", "Accessories", "Monitors"],
                    "sample_regions": ["North America", "Europe", "Asia-Pacific"]
                },
                "products": {
                    "description": "Product catalog and inventory",
                    "fields": ["product_id", "name", "category", "brand", "price", 
                              "cost", "stock", "rating", "reviews_count"]
                },
                "customers": {
                    "description": "Customer information and profiles",
                    "fields": ["customer_id", "name", "email", "age", "gender", 
                              "country", "state", "city", "customer_segment", 
                              "total_spent", "order_count"]
                }
            }
        }
    
    def is_conversational_query(self, query: str) -> bool:
        """
        Determine if a query is conversational rather than analytical.
        """
        query_lower = query.lower().strip()
        
        # Greeting patterns
        greeting_patterns = [
            'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
            'greetings', 'howdy', 'what\'s up', 'how are you'
        ]
        
        # System information patterns
        system_patterns = [
            'what do you do', 'what can you do', 'how do you work', 'help me',
            'what is this', 'about you', 'your capabilities', 'how to use',
            'getting started', 'introduction', 'what data', 'available data',
            'what information', 'what can i ask', 'examples', 'sample questions'
        ]
        
        # Check for exact matches or patterns
        for pattern in greeting_patterns + system_patterns:
            if pattern in query_lower:
                return True
        
        # Check if query is very short and likely conversational
        if len(query_lower.split()) <= 3 and any(word in query_lower for word in ['hi', 'hello', 'help', 'what', 'how']):
            return True
        
        return False
    
    def get_query_type(self, query: str) -> str:
        """
        Classify the type of conversational query.
        """
        query_lower = query.lower().strip()
        
        if any(word in query_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']):
            return 'greeting'
        elif any(phrase in query_lower for phrase in ['what do you do', 'what can you do', 'your capabilities', 'about you']):
            return 'capabilities'
        elif any(phrase in query_lower for phrase in ['help', 'how to use', 'getting started', 'introduction']):
            return 'help'
        elif any(phrase in query_lower for phrase in ['what data', 'available data', 'what information', 'data types']):
            return 'data_info'
        elif any(phrase in query_lower for phrase in ['examples', 'sample questions', 'what can i ask']):
            return 'examples'
        else:
            return 'general'
    
    async def generate_dynamic_stats(self) -> Dict:
        """
        Generate dynamic statistics from the database for conversational responses.
        """
        try:
            if not self.db_manager.is_connected():
                return {}
            
            db = self.db_manager.get_database()
            
            # Get basic counts
            stats = {
                "total_sales": await self._safe_count(db.sales),
                "total_customers": await self._safe_count(db.customers),
                "total_products": await self._safe_count(db.products),
                "date_range": await self._get_date_range(db.sales),
                "top_categories": await self._get_top_categories(db.sales),
                "regions": await self._get_regions(db.sales),
                "total_revenue": await self._get_total_revenue(db.sales)
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error generating stats: {e}")
            return {}
    
    async def _safe_count(self, collection) -> int:
        """Safely count documents in a collection"""
        try:
            return collection.count_documents({})
        except:
            return 0
    
    async def _get_date_range(self, sales_collection) -> Dict:
        """Get the date range of sales data"""
        try:
            pipeline = [
                {"$group": {
                    "_id": None,
                    "min_date": {"$min": "$date"},
                    "max_date": {"$max": "$date"}
                }}
            ]
            result = list(sales_collection.aggregate(pipeline))
            if result:
                return {
                    "start": result[0]["min_date"],
                    "end": result[0]["max_date"]
                }
        except:
            pass
        return {}
    
    async def _get_top_categories(self, sales_collection) -> List[str]:
        """Get top 3 product categories by sales"""
        try:
            pipeline = [
                {"$group": {"_id": "$category", "total": {"$sum": "$total_amount"}}},
                {"$sort": {"total": -1}},
                {"$limit": 3}
            ]
            result = list(sales_collection.aggregate(pipeline))
            return [item["_id"] for item in result if item["_id"]]
        except:
            return []
    
    async def _get_regions(self, sales_collection) -> List[str]:
        """Get active regions"""
        try:
            pipeline = [
                {"$group": {"_id": "$region"}},
                {"$sort": {"_id": 1}}
            ]
            result = list(sales_collection.aggregate(pipeline))
            return [item["_id"] for item in result if item["_id"]]
        except:
            return []
    
    async def _get_total_revenue(self, sales_collection) -> float:
        """Get total revenue"""
        try:
            pipeline = [
                {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
            ]
            result = list(sales_collection.aggregate(pipeline))
            if result:
                return round(result[0]["total"], 2)
        except:
            pass
        return 0.0
    
    async def generate_conversational_response(self, query: str) -> Dict:
        """
        Generate a conversational response based on the query type and dynamic data.
        """
        query_type = self.get_query_type(query)
        stats = await self.generate_dynamic_stats()
        
        if query_type == 'greeting':
            return await self._generate_greeting_response(stats)
        elif query_type == 'capabilities':
            return await self._generate_capabilities_response(stats)
        elif query_type == 'help':
            return await self._generate_help_response(stats)
        elif query_type == 'data_info':
            return await self._generate_data_info_response(stats)
        elif query_type == 'examples':
            return await self._generate_examples_response(stats)
        else:
            return await self._generate_general_response(query, stats)
    
    async def _generate_greeting_response(self, stats: Dict) -> Dict:
        """Generate a greeting response with dynamic data context"""
        
        # Create dynamic greeting based on available data
        greeting_parts = [
            "Hello! I'm your conversational analytics assistant.",
            "I can help you explore and analyze your business data using natural language."
        ]
        
        if stats:
            data_summary = []
            if stats.get('total_sales'):
                data_summary.append(f"{stats['total_sales']} sales records")
            if stats.get('total_customers'):
                data_summary.append(f"{stats['total_customers']} customers")
            if stats.get('total_products'):
                data_summary.append(f"{stats['total_products']} products")
            
            if data_summary:
                greeting_parts.append(f"I have access to {', '.join(data_summary)} in your database.")
            
            if stats.get('total_revenue'):
                greeting_parts.append(f"Your total revenue is ${stats['total_revenue']:,.2f}.")
            
            if stats.get('top_categories'):
                categories = ', '.join(stats['top_categories'])
                greeting_parts.append(f"Your top product categories include {categories}.")
        
        greeting_parts.append("What would you like to know about your data?")
        
        return {
            "summary": " ".join(greeting_parts),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_capabilities_response(self, stats: Dict) -> Dict:
        """Generate response about system capabilities"""
        
        capabilities = [
            "I'm an AI-powered conversational analytics assistant that can help you:",
            "• Analyze sales performance and revenue trends",
            "• Explore customer behavior and demographics", 
            "• Review product performance and inventory",
            "• Compare data across different time periods and regions",
            "• Generate visualizations (charts and graphs) for your data"
        ]
        
        if stats:
            capabilities.append(f"\nI'm currently connected to your database with:")
            if stats.get('total_sales'):
                capabilities.append(f"• {stats['total_sales']} sales transactions")
            if stats.get('total_customers'):
                capabilities.append(f"• {stats['total_customers']} customer records")
            if stats.get('total_products'):
                capabilities.append(f"• {stats['total_products']} product entries")
            
            if stats.get('regions'):
                regions = ', '.join(stats['regions'])
                capabilities.append(f"• Data across regions: {regions}")
        
        capabilities.append("\nJust ask me questions in natural language, and I'll provide insights with visualizations!")
        
        return {
            "summary": "\n".join(capabilities),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_help_response(self, stats: Dict) -> Dict:
        """Generate help response with dynamic examples"""
        
        help_text = [
            "Here's how to use the conversational analytics system:",
            "",
            "1. **Ask Natural Questions**: Simply type your question in plain English",
            "2. **Get Insights**: I'll analyze your data and provide summaries",
            "3. **View Visualizations**: See charts and graphs for better understanding",
            "",
            "**Example Questions You Can Ask:**"
        ]
        
        # Generate dynamic examples based on available data
        examples = []
        if stats.get('total_sales'):
            examples.append("• \"What were our top 5 selling products last month?\"")
            examples.append("• \"Show me revenue by region\"")
        
        if stats.get('total_customers'):
            examples.append("• \"Which customer segment generates the most profit?\"")
            examples.append("• \"Show me customer distribution by country\"")
        
        if stats.get('top_categories'):
            examples.extend([
                f"• \"Compare sales performance between {stats['top_categories'][0]} and {stats['top_categories'][1] if len(stats['top_categories']) > 1 else 'other categories'}\"",
                "• \"What's the trend in our product categories over time?\""
            ])
        
        if not examples:
            examples = [
                "• \"Show me sales performance\"",
                "• \"What are our top products?\"",
                "• \"How are customers distributed?\""
            ]
        
        help_text.extend(examples)
        help_text.append("\n**Tips:**")
        help_text.extend([
            "• Be specific about time periods (last month, this quarter, etc.)",
            "• Ask for comparisons between different categories or regions",
            "• Request specific chart types if you prefer (bar chart, pie chart, etc.)"
        ])
        
        return {
            "summary": "\n".join(help_text),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_data_info_response(self, stats: Dict) -> Dict:
        """Generate response about available data"""
        
        data_info = ["Here's what data I have access to:\n"]
        
        # Dynamic data overview
        if stats:
            data_info.append("**Dataset Overview:**")
            if stats.get('total_sales'):
                data_info.append(f"• Sales Records: {stats['total_sales']} transactions")
            if stats.get('total_customers'):
                data_info.append(f"• Customer Data: {stats['total_customers']} customer profiles")
            if stats.get('total_products'):
                data_info.append(f"• Product Catalog: {stats['total_products']} products")
            
            if stats.get('total_revenue'):
                data_info.append(f"• Total Revenue: ${stats['total_revenue']:,.2f}")
            
            if stats.get('date_range'):
                date_range = stats['date_range']
                if date_range.get('start') and date_range.get('end'):
                    data_info.append(f"• Date Range: {date_range['start']} to {date_range['end']}")
            
            if stats.get('top_categories'):
                categories = ', '.join(stats['top_categories'])
                data_info.append(f"• Top Categories: {categories}")
            
            if stats.get('regions'):
                regions = ', '.join(stats['regions'])
                data_info.append(f"• Regions: {regions}")
        
        # Static schema information
        data_info.extend([
            "\n**Available Data Types:**",
            "• **Sales Data**: Orders, revenue, products, dates, regions",
            "• **Customer Data**: Demographics, segments, purchase history",
            "• **Product Data**: Categories, pricing, inventory, ratings"
        ])
        
        return {
            "summary": "\n".join(data_info),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_examples_response(self, stats: Dict) -> Dict:
        """Generate response with dynamic examples"""
        
        examples = ["Here are some questions you can ask based on your data:\n"]
        
        # Dynamic examples based on actual data
        if stats.get('total_sales'):
            examples.extend([
                "**Sales Analysis:**",
                "• \"What were our top 10 selling products this quarter?\"",
                "• \"Show me sales performance by month\"",
                "• \"Which sales representative has the highest revenue?\"",
                ""
            ])
        
        if stats.get('total_customers'):
            examples.extend([
                "**Customer Insights:**",
                "• \"Show me customer distribution by age group\"",
                "• \"Which customer segment spends the most?\"",
                "• \"What's the average order value by region?\"",
                ""
            ])
        
        if stats.get('top_categories'):
            categories = stats['top_categories']
            examples.extend([
                "**Product Analysis:**",
                f"• \"Compare sales between {categories[0]} and {categories[1] if len(categories) > 1 else 'other categories'}\"",
                "• \"What are our lowest-rated products?\"",
                "• \"Show me inventory levels for each category\"",
                ""
            ])
        
        if stats.get('regions'):
            regions = stats['regions']
            examples.extend([
                "**Regional Comparisons:**",
                f"• \"How does {regions[0]} compare to {regions[1] if len(regions) > 1 else 'other regions'} in sales?\"",
                "• \"Which region has the highest customer satisfaction?\"",
                ""
            ])
        
        examples.extend([
            "**Trend Analysis:**",
            "• \"Show me revenue trend over the last 6 months\"",
            "• \"What's the seasonal pattern in our sales?\"",
            "• \"How has customer acquisition changed over time?\""
        ])
        
        return {
            "summary": "\n".join(examples),
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    async def _generate_general_response(self, query: str, stats: Dict) -> Dict:
        """Generate a general conversational response using AI when available"""
        
        # Try to use Gemini for more nuanced responses
        if self.gemini_client:
            try:
                context = f"Database contains {stats.get('total_sales', 0)} sales records, {stats.get('total_customers', 0)} customers, and {stats.get('total_products', 0)} products."
                
                prompt = f"""
                You are a conversational analytics assistant. The user asked: "{query}"
                
                Context: {context}
                
                Provide a helpful, conversational response that:
                1. Addresses their question naturally
                2. Offers assistance with data analysis
                3. Suggests how they can explore their data
                4. Keeps it friendly and professional
                
                Limit response to 3-4 sentences.
                """
                
                response = await self.gemini_client.generate_content(prompt)
                return {
                    "summary": response.text.strip(),
                    "chart_data": None,
                    "conversational": True,
                    "suggestions": self._get_dynamic_suggestions(stats)
                }
            except Exception as e:
                logger.error(f"Error generating AI response: {e}")
        
        # Fallback response
        return {
            "summary": "I'm here to help you analyze your data! You can ask me questions about sales, customers, products, or any other aspect of your business data. What would you like to explore?",
            "chart_data": None,
            "conversational": True,
            "suggestions": self._get_dynamic_suggestions(stats)
        }
    
    def _get_dynamic_suggestions(self, stats: Dict) -> List[str]:
        """Generate dynamic suggestions based on available data"""
        
        suggestions = []
        
        if stats.get('total_sales'):
            suggestions.append("Show me top selling products")
            suggestions.append("What's our revenue by region?")
        
        if stats.get('total_customers'):
            suggestions.append("Customer distribution by segment")
            suggestions.append("Which customers spend the most?")
        
        if stats.get('top_categories'):
            categories = stats['top_categories']
            if len(categories) >= 2:
                suggestions.append(f"Compare {categories[0]} vs {categories[1]} sales")
        
        if stats.get('date_range'):
            suggestions.append("Show sales trends over time")
        
        # Default suggestions if no dynamic data
        if not suggestions:
            suggestions = [
                "What can you tell me about my data?",
                "Show me some insights",
                "Help me get started"
            ]
        
        return suggestions[:6]  # Limit to 6 suggestions