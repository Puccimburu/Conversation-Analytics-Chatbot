import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and operations manager"""
    
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
            
            logger.info(f"Executed aggregation on {collection_name}, returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Aggregation error on {collection_name}: {str(e)}")
            raise
    
    def get_collection_stats(self, collection_name):
        """Get basic statistics about a collection"""
        try:
            collection = self.get_collection(collection_name)
            stats = {
                "count": collection.count_documents({}),
                "size": collection.estimated_document_count(),
                "indexes": list(collection.list_indexes())
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {str(e)}")
            return None
    
    def get_sample_documents(self, collection_name, limit=5):
        """Get sample documents from collection"""
        try:
            collection = self.get_collection(collection_name)
            samples = list(collection.find().limit(limit))
            return samples
        except Exception as e:
            logger.error(f"Error getting samples from {collection_name}: {str(e)}")
            return []
    
    def health_check(self):
        """Check database health"""
        try:
            if not self.client:
                return False
            
            # Test connection
            self.client.admin.command('ping')
            
            # Check if required collections exist
            collection_names = self.db.list_collection_names()
            required_collections = ['sales', 'products', 'customers']
            
            missing_collections = [col for col in required_collections if col not in collection_names]
            
            if missing_collections:
                logger.warning(f"Missing collections: {missing_collections}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_database_overview(self):
        """Get overview of entire database"""
        try:
            overview = {
                "database_name": Config.DATABASE_NAME,
                "collections": {},
                "total_documents": 0
            }
            
            for collection_name in self.db.list_collection_names():
                stats = self.get_collection_stats(collection_name)
                overview["collections"][collection_name] = stats
                if stats:
                    overview["total_documents"] += stats.get("count", 0)
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting database overview: {str(e)}")
            return None
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")

# Global database instance
db_manager = DatabaseManager()

def get_db():
    """Get database instance"""
    return db_manager.db

def get_db_manager():
    """Get database manager instance"""
    return db_manager