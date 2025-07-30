import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from config.config import Config, DATABASE_SCHEMA

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager for GenAI operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[Config.DATABASE_NAME]
            
            logger.info(f"Connected to MongoDB: {Config.DATABASE_NAME}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    def is_connected(self):
        """Check if database connection is active"""
        try:
            if self.client and self.db:
                self.client.admin.command('ping')
                return True
        except Exception as e:
            logger.warning(f"Database connection check failed: {e}")
        return False
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        if not self.db:
            raise ConnectionError("Database not connected")
        return self.db[collection_name]
    
    def execute_aggregation(self, collection_name, pipeline, max_results=100):
        """Execute aggregation pipeline with error handling"""
        try:
            collection = self.get_collection(collection_name)
            
            # Add safety limit
            pipeline_with_limit = pipeline.copy()
            if not any('$limit' in stage for stage in pipeline_with_limit):
                pipeline_with_limit.append({"$limit": max_results})
            
            results = list(collection.aggregate(pipeline_with_limit))
            logger.info(f"Executed aggregation on {collection_name}: {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Aggregation failed on {collection_name}: {str(e)}")
            raise
    
    def get_collection_stats(self, collection_name):
        """Get basic statistics for a collection"""
        try:
            collection = self.get_collection(collection_name)
            
            # Get document count
            count = collection.count_documents({})
            
            if count == 0:
                return {"name": collection_name, "count": 0, "empty": True}
            
            # Get sample document to understand structure
            sample = collection.find_one()
            
            # Get collection info
            stats = {
                "name": collection_name,
                "count": count,
                "empty": False,
                "sample_fields": list(sample.keys()) if sample else [],
                "estimated_size": collection.estimated_document_count()
            }
            
            # Add schema information if available
            if collection_name in DATABASE_SCHEMA["collections"]:
                schema_info = DATABASE_SCHEMA["collections"][collection_name]
                stats.update({
                    "description": schema_info.get("description", ""),
                    "key_metrics": schema_info.get("key_metrics", []),
                    "numeric_fields": schema_info.get("numeric_fields", []),
                    "date_fields": schema_info.get("date_fields", [])
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {str(e)}")
            return {"name": collection_name, "count": -1, "error": str(e)}
    
    def health_check(self):
        """Perform health check on GenAI database"""
        try:
            if not self.is_connected():
                return False
            
            # Check for key GenAI collections
            collection_names = self.db.list_collection_names()
            
            # Updated for GenAI operations - check for essential collections
            required_collections = [
                'costevalutionforllm',      # AI cost tracking
                'documentextractions',      # Document processing
                'agent_activity',           # Agent performance
                'users'                     # User management
            ]
            
            missing_collections = [col for col in required_collections if col not in collection_names]
            
            if missing_collections:
                logger.warning(f"Missing GenAI collections: {missing_collections}")
                # Don't fail health check for missing collections - they might be created later
                # Just log the warning
            
            # Test basic database operations
            test_collection = self.get_collection('users')
            test_collection.count_documents({})
            
            logger.info("✅ GenAI database health check passed")
            return True
            
        except Exception as e:
            logger.error(f"GenAI database health check failed: {str(e)}")
            return False
    
    def get_database_overview(self):
        """Get overview of entire GenAI database"""
        try:
            overview = {
                "database_name": Config.DATABASE_NAME,
                "database_type": "GenAI Operations & Document Intelligence",
                "collections": {},
                "total_documents": 0,
                "schema_version": "1.0"
            }
            
            collection_names = self.db.list_collection_names()
            
            # Categorize collections by domain
            collection_categories = {
                "ai_operations": [],
                "document_processing": [], 
                "compliance": [],
                "user_management": [],
                "system": []
            }
            
            for collection_name in collection_names:
                stats = self.get_collection_stats(collection_name)
                overview["collections"][collection_name] = stats
                
                if stats and stats.get("count", 0) > 0:
                    overview["total_documents"] += stats["count"]
                
                # Categorize collections
                if collection_name in ['costevalutionforllm', 'llmpricing', 'agent_activity']:
                    collection_categories["ai_operations"].append(collection_name)
                elif collection_name in ['documentextractions', 'batches', 'files']:
                    collection_categories["document_processing"].append(collection_name)
                elif collection_name in ['obligationextractions', 'obligationmappings', 'compliances']:
                    collection_categories["compliance"].append(collection_name)
                elif collection_name in ['users', 'allowedusers', 'conversations']:
                    collection_categories["user_management"].append(collection_name)
                else:
                    collection_categories["system"].append(collection_name)
            
            overview["collection_categories"] = collection_categories
            overview["total_collections"] = len(collection_names)
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting GenAI database overview: {str(e)}")
            return None
    
    def get_collection_sample_data(self, collection_name, limit=5):
        """Get sample data from a collection for analysis"""
        try:
            collection = self.get_collection(collection_name)
            
            # Get recent documents
            sample_docs = list(collection.find().sort("_id", -1).limit(limit))
            
            # Clean up ObjectIds for JSON serialization
            cleaned_docs = []
            for doc in sample_docs:
                cleaned_doc = {}
                for key, value in doc.items():
                    if hasattr(value, 'isoformat'):  # datetime
                        cleaned_doc[key] = value.isoformat()
                    elif hasattr(value, 'hex'):  # ObjectId
                        cleaned_doc[key] = str(value)
                    else:
                        cleaned_doc[key] = value
                cleaned_docs.append(cleaned_doc)
            
            return cleaned_docs
            
        except Exception as e:
            logger.error(f"Failed to get sample data from {collection_name}: {str(e)}")
            return []
    
    def test_genai_operations(self):
        """Test specific GenAI operations to ensure database readiness"""
        tests = {
            "cost_data_available": False,
            "document_extractions_available": False,
            "user_data_available": False,
            "agent_activity_available": False
        }
        
        try:
            # Test AI cost data
            if 'costevalutionforllm' in self.db.list_collection_names():
                cost_collection = self.get_collection('costevalutionforllm')
                if cost_collection.count_documents({}) > 0:
                    tests["cost_data_available"] = True
            
            # Test document extractions
            if 'documentextractions' in self.db.list_collection_names():
                doc_collection = self.get_collection('documentextractions')
                if doc_collection.count_documents({}) > 0:
                    tests["document_extractions_available"] = True
            
            # Test user data
            if 'users' in self.db.list_collection_names():
                user_collection = self.get_collection('users')
                if user_collection.count_documents({}) > 0:
                    tests["user_data_available"] = True
            
            # Test agent activity
            if 'agent_activity' in self.db.list_collection_names():
                agent_collection = self.get_collection('agent_activity')
                if agent_collection.count_documents({}) > 0:
                    tests["agent_activity_available"] = True
            
        except Exception as e:
            logger.error(f"GenAI operations test failed: {str(e)}")
        
        return tests
    
    def get_genai_metrics_summary(self):
        """Get high-level metrics summary for GenAI operations"""
        try:
            summary = {
                "ai_operations": {},
                "document_processing": {},
                "compliance": {},
                "system_health": {}
            }
            
            # AI Operations metrics
            if 'costevalutionforllm' in self.db.list_collection_names():
                cost_collection = self.get_collection('costevalutionforllm')
                total_cost_pipeline = [
                    {"$group": {"_id": None, "total_cost": {"$sum": "$totalCost"}, "count": {"$sum": 1}}}
                ]
                cost_result = list(cost_collection.aggregate(total_cost_pipeline))
                if cost_result:
                    summary["ai_operations"] = {
                        "total_cost": round(cost_result[0].get("total_cost", 0), 2),
                        "total_operations": cost_result[0].get("count", 0)
                    }
            
            # Document processing metrics
            if 'documentextractions' in self.db.list_collection_names():
                doc_collection = self.get_collection('documentextractions')
                doc_count = doc_collection.count_documents({})
                
                # Average confidence score
                confidence_pipeline = [
                    {"$group": {"_id": None, "avg_confidence": {"$avg": "$Confidence_Score"}}}
                ]
                confidence_result = list(doc_collection.aggregate(confidence_pipeline))
                
                summary["document_processing"] = {
                    "total_documents": doc_count,
                    "avg_confidence": round(confidence_result[0].get("avg_confidence", 0), 2) if confidence_result else 0
                }
            
            # Compliance metrics
            if 'obligationextractions' in self.db.list_collection_names():
                obligation_collection = self.get_collection('obligationextractions')
                obligation_count = obligation_collection.count_documents({})
                summary["compliance"] = {"total_obligations": obligation_count}
            
            # System health
            collections = self.db.list_collection_names()
            summary["system_health"] = {
                "total_collections": len(collections),
                "database_connected": self.is_connected()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get GenAI metrics summary: {str(e)}")
            return {"error": str(e)}
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("GenAI database connection closed")

# Global database instance
db_manager = DatabaseManager()

def get_db():
    """Get database instance"""
    return db_manager.db

def get_db_manager():
    """Get database manager instance"""
    return db_manager

def get_genai_collections():
    """Get list of available GenAI collections"""
    try:
        return list(DATABASE_SCHEMA["collections"].keys())
    except:
        return []

def validate_genai_collection(collection_name):
    """Validate if a collection is part of the GenAI schema"""
    return collection_name in DATABASE_SCHEMA.get("collections", {})

def get_collection_schema(collection_name):
    """Get schema information for a specific collection"""
    return DATABASE_SCHEMA.get("collections", {}).get(collection_name, {})