import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Database Configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://127.0.0.1:27017/genaiexeco-development')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'genaiexeco-development')
    
    # Flask Configuration
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # Gemini Configuration
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Query Limits
    MAX_RESULTS_LIMIT = int(os.getenv('MAX_RESULTS_LIMIT', 100))
    DEFAULT_RESULTS_LIMIT = int(os.getenv('DEFAULT_RESULTS_LIMIT', 15))
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI environment variable is required")
        
        return True

# NEW: GenAI Database Schema Configuration
DATABASE_SCHEMA = {
    "collections": {
        # AI Operations & Cost Tracking
        "costevalutionforllm": {
            "description": "LLM cost evaluation and usage tracking",
            "fields": [
                "_id", "batchId", "fileId", "promptId",
                "inputTokens", "outputTokens", "totalTokens", "totalCostInUSD"
            ],
            "date_fields": [],
            "numeric_fields": ["inputTokens", "outputTokens", "totalTokens", "totalCostInUSD"],
            "group_by_fields": ["batchId", "fileId", "promptId"],
            "key_metrics": ["inputTokens", "outputTokens", "totalTokens", "totalCostInUSD"]
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
                "_id", "Value", "Type", "Name", "Confidence Score", "Status",
                "batchId", "fileId", "status"
            ],
            "date_fields": [],
            "numeric_fields": ["Confidence Score"],
            "group_by_fields": ["Type", "Name", "Status", "batchId", "fileId", "status"],
            "key_metrics": ["Confidence Score"]
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
            "available_statuss": ["Processed", "Processing", "queued"],
            "date_fields": ["createdAt", "updatedAt"],
            "description": "Auto-generated schema for the 'batches' collection.",
            "fields": [
                "__v", "_id", "batchId", "batchName", "createdAt", "createdBy",
                "description", "files", "status", "updatedAt", "updatedBy"
            ],
            "group_by_fields": ["batchId", "batchName", "createdBy", "description", "status", "updatedBy"],
            "key_metrics": ["__v"],
            "numeric_fields": ["__v"]
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
            "date_fields": ["createdAt", "updatedAt"],
            "description": "Auto-generated schema for the 'users' collection.",
            "fields": [
                "__v", "_id", "authSource", "createdAt", "emailId", "firstName",
                "googleId", "lastName", "password", "profilePicture", "role", "updatedAt", "userId"
            ],
            "group_by_fields": [
                "authSource", "emailId", "firstName", "googleId", "lastName",
                "password", "profilePicture", "role", "userId"
            ],
            "key_metrics": ["__v"],
            "numeric_fields": ["__v"]
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

# GenAI Operations Sample Query Templates
SAMPLE_QUERIES = [
    # AI Operations Analytics
    "Show AI costs by batch",
    "What's our total token usage?",
    "Display cost breakdown by file",
    "Which batches are most expensive?",
    "Show cost per token analysis",
    
    # Document Processing Analytics
    "Show document extraction confidence scores",
    "Display extraction results by type",
    "What's our processing success rate?",
    "Show confidence scores by document type",
    "List high-confidence extractions",
    
    # Legal & Compliance Analytics
    "Show all compliance obligations",
    "Display obligations by confidence level",
    "What are the most common obligation types?",
    "Show obligation extraction results",
    "List compliance requirements",
    
    # User & Agent Analytics
    "Show all users by role",
    "Display agent activity results",
    "What's our agent success rate?",
    "Show user role distribution",
    "List active users",
    
    # Prompt & Processing Analytics
    "Show prompt usage statistics",
    "Display batch processing results",
    "What are our most used prompts?",
    "Show file processing status",
    "Track conversation activity"
]