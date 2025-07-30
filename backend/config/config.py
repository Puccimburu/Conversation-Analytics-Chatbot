import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """General application configuration class"""
    
    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genai')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'genai')
    
    # Flask Configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Query Limits
    MAX_RESULTS_LIMIT = int(os.getenv('MAX_RESULTS_LIMIT', 100))
    DEFAULT_RESULTS_LIMIT = int(os.getenv('DEFAULT_RESULTS_LIMIT', 15))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is required")
        
        return True

# GenAI Database Schema Configuration
DATABASE_SCHEMA = {
    "collections": {
        # AI Operations & Cost Tracking
        "costevalutionforllm": {
            "description": "LLM cost evaluation and usage tracking",
            "fields": [
                "_id", "batchId", "userId", "modelType", "operationType",
                "inputTokens", "outputTokens", "totalCost", "costPerToken",
                "requestDuration", "timestamp", "status", "metadata"
            ],
            "date_fields": ["timestamp"],
            "numeric_fields": ["inputTokens", "outputTokens", "totalCost", "costPerToken", "requestDuration"],
            "group_by_fields": ["modelType", "operationType", "status", "userId", "batchId"],
            "key_metrics": ["inputTokens", "outputTokens", "totalCost", "costPerToken", "requestDuration"]
        },
        
        "llmpricing": {
            "description": "AI model pricing and rate information",
            "fields": [
                "_id", "modelVariant", "ratePerMillionInputTokens", "ratePerMillionOutputTokens",
                "effectiveDate", "currency"
            ],
            "date_fields": ["effectiveDate"],
            "numeric_fields": ["ratePerMillionInputTokens", "ratePerMillionOutputTokens"],
            "group_by_fields": ["modelVariant"],
            "key_metrics": ["ratePerMillionInputTokens", "ratePerMillionOutputTokens"]
        },
        
        "agent_activity": {
            "description": "AI agent performance and activity tracking",
            "fields": [
                "_id", "Agent", "Contract_Name", "Outcome", "Timestamp",
                "agentType", "action", "duration", "status", "performanceMetrics"
            ],
            "date_fields": ["Timestamp"],
            "numeric_fields": ["duration"],
            "group_by_fields": ["Agent", "Contract_Name", "Outcome", "status"],
            "key_metrics": ["duration"],
            "available_agents": ["Digitization Agent"],
            "available_outcomes": ["Success"]
        },
        
        # Document Processing Pipeline
        "documentextractions": {
            "description": "Document content extraction results",
            "fields": [
                "_id", "Value", "Type", "Name", "Confidence_Score", "Status",
                "batchId", "fileId", "extractionType", "processingTime", "timestamp"
            ],
            "date_fields": ["timestamp"],
            "numeric_fields": ["Confidence_Score", "processingTime"],
            "group_by_fields": ["Type", "Name", "Status", "batchId", "fileId"],
            "key_metrics": ["Confidence_Score", "processingTime"]
        },
        
        "obligationextractions": {
            "description": "Legal obligation extraction and analysis",
            "fields": [
                "_id", "obligationExtractionId", "name", "description", "metadata",
                "obligationType", "confidence", "category", "severity", "complianceFlag"
            ],
            "date_fields": [],
            "numeric_fields": ["confidence", "severity"],
            "group_by_fields": ["name", "obligationType", "category", "complianceFlag"],
            "key_metrics": ["confidence", "severity"]
        },
        
        "obligationmappings": {
            "description": "Mapping between obligations and documents",
            "fields": [
                "_id", "mappingId", "batchId", "fileId", "obligationIds",
                "documentId", "mappingType", "createdAt"
            ],
            "date_fields": ["createdAt"],
            "numeric_fields": [],
            "group_by_fields": ["batchId", "fileId", "mappingId", "mappingType"],
            "key_metrics": []
        },
        
        "batches": {
            "description": "Document processing batch information",
            "fields": [
                "_id", "batchId", "batchType", "status", "createdAt", "startedAt",
                "completedAt", "totalItems", "processedItems", "failedItems",
                "userId", "processingTime", "metadata"
            ],
            "date_fields": ["createdAt", "startedAt", "completedAt"],
            "numeric_fields": ["totalItems", "processedItems", "failedItems", "processingTime"],
            "group_by_fields": ["batchType", "status", "userId"],
            "key_metrics": ["totalItems", "processedItems", "failedItems", "processingTime"]
        },
        
        "files": {
            "description": "File storage and metadata",
            "fields": [
                "_id", "fileId", "fileName", "blobName", "container", "url",
                "size", "status", "createdAt", "updatedAt", "createdBy", "updatedBy"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": ["size"],
            "group_by_fields": ["fileName", "container", "status", "createdBy"],
            "key_metrics": ["size"]
        },
        
        # AI Prompt Management
        "prompts": {
            "description": "AI prompt templates and configuration",
            "fields": [
                "_id", "promptId", "promptName", "description", "promptType",
                "promptText", "createdBy", "updatedBy", "createdAt", "updatedAt",
                "usageCount", "effectivenessScore"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": ["usageCount", "effectivenessScore"],
            "group_by_fields": ["promptType", "createdBy"],
            "key_metrics": ["usageCount", "effectivenessScore"]
        },
        
        "prompts3": {
            "description": "Extended AI prompt library",
            "fields": [
                "_id", "promptId", "promptName", "description", "promptType",
                "promptText", "createdBy", "updatedBy", "createdAt", "updatedAt"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["promptType", "createdBy"],
            "key_metrics": []
        },
        
        "promptmappings": {
            "description": "Prompt relationship and mapping data",
            "fields": [
                "_id", "sysId", "dataPoint", "promptId", "createdBy", "updatedBy",
                "createdAt", "updatedAt"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["dataPoint", "promptId", "createdBy"],
            "key_metrics": []
        },
        
        # Document Management
        "documentmappings": {
            "description": "Document to prompt mapping relationships",
            "fields": [
                "_id", "sysId", "documentId", "promptIds", "createdBy", "updatedBy",
                "createdAt", "updatedAt", "mappingType"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["documentId", "createdBy", "mappingType"],
            "key_metrics": []
        },
        
        "documenttypes": {
            "description": "Document type classification and schema",
            "fields": [
                "_id", "documentId", "typeName", "description", "schema",
                "validationRules", "createdAt", "updatedAt"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["typeName"],
            "key_metrics": []
        },
        
        # Communication System
        "conversations": {
            "description": "Chat conversation sessions",
            "fields": [
                "_id", "conversationId", "userId", "title", "feature", "messages",
                "createdAt", "updatedAt", "createdBy", "updatedBy", "status"
            ],
            "date_fields": ["createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["userId", "feature", "status", "createdBy"],
            "key_metrics": []
        },
        
        # User Management
        "users": {
            "description": "User accounts and profiles",
            "fields": [
                "_id", "userId", "emailId", "name", "role", "permissions",
                "createdAt", "lastLogin", "profile"
            ],
            "date_fields": ["createdAt", "lastLogin"],
            "numeric_fields": [],
            "group_by_fields": ["role"],
            "key_metrics": []
        },
        
        "allowedusers": {
            "description": "User access control and permissions",
            "fields": [
                "_id", "emailId", "permissions", "accessLevel", "grantedAt",
                "createdAt", "updatedAt"
            ],
            "date_fields": ["grantedAt", "createdAt", "updatedAt"],
            "numeric_fields": [],
            "group_by_fields": ["accessLevel"],
            "key_metrics": []
        },
        
        # Compliance & Audit
        "compliances": {
            "description": "Compliance tracking and validation",
            "fields": [
                "_id", "complianceId", "userId", "documentId", "complianceType",
                "status", "reviewedAt", "findings"
            ],
            "date_fields": ["reviewedAt"],
            "numeric_fields": [],
            "group_by_fields": ["complianceType", "status", "userId"],
            "key_metrics": []
        },
        
        # Workflow Management
        "langgraph_checkpoints": {
            "description": "Workflow state management and checkpoints",
            "fields": [
                "_id", "thread_id", "state", "last_updated", "checkpointId", "workflowType"
            ],
            "date_fields": ["last_updated"],
            "numeric_fields": [],
            "group_by_fields": ["thread_id", "workflowType"],
            "key_metrics": []
        },
        
        # Legacy Analytics (if present)
        "customers": {
            "description": "Customer information and profiles",
            "fields": [
                "_id", "customer_id", "name", "email", "age", "gender",
                "country", "state", "city", "customer_segment", "total_spent", "order_count"
            ],
            "date_fields": [],
            "numeric_fields": ["age", "total_spent", "order_count"],
            "group_by_fields": ["customer_segment", "country", "gender"],
            "key_metrics": ["total_spent", "order_count"]
        },
        
        "orders": {
            "description": "Order transaction records",
            "fields": [
                "_id", "customer_id", "item", "order_date", "quantity", "total_price"
            ],
            "date_fields": ["order_date"],
            "numeric_fields": ["quantity", "total_price"],
            "group_by_fields": ["item"],
            "key_metrics": ["quantity", "total_price"]
        }
    }
}

# Chart Type Mapping
CHART_TYPE_MAPPING = {
    "time_series": "line",
    "categorical_comparison": "bar",
    "distribution": "pie",
    "percentage": "doughnut",
    "trend": "line",
    "ranking": "bar",
    "cost_analysis": "line",
    "performance": "bar",
    "compliance": "pie"
}

# GenAI Sample Query Templates
SAMPLE_QUERIES = [
    # AI Operations Analytics
    "What's our AI spending this month?",
    "Which AI models are most cost-effective?",
    "Show me token usage patterns by user",
    "What's our average processing time per request?",
    "Compare AI costs across different document types",
    
    # Document Processing Analytics
    "How many documents did we process today?",
    "What's our extraction success rate?",
    "Show me processing volume by document type",
    "Which batches took longest to complete?",
    "What are our confidence score distributions?",
    
    # Legal & Compliance Analytics
    "What are our most critical compliance obligations?",
    "Show me high-risk compliance items",
    "Which documents have data confidentiality requirements?",
    "List all insurance-related obligations",
    "Show compliance obligations by category",
    
    # User & Performance Analytics
    "Who are our most active users?",
    "Show agent performance over time",
    "Which users generate highest AI costs?",
    "Track document processing efficiency",
    "Compare user engagement patterns",
    
    # Cross-Collection Complex Analytics
    "Show AI costs for documents that failed compliance",
    "Which prompts are most effective for legal documents?",
    "Compare extraction confidence vs processing costs",
    "Track document processing pipeline success rates"
]