"""
Database service and connection management
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Singleton database service"""
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize database connection"""
        # Load environment variables from multiple sources
        ROOT_DIR = Path(__file__).parent.parent.parent.parent
        env_files = [
            ROOT_DIR / 'src' / 'backend' / '.env',
            ROOT_DIR / 'backend' / '.env',  # Fallback for old structure
            ROOT_DIR / '.env'  # Root level env file
        ]
        
        # Try to load from any existing env file
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                break
        
        # Get connection details from environment
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_development')
        
        if not mongo_url:
            # Final fallback to default values for development
            mongo_url = "mongodb://localhost:27017"
            logger.warning("MONGO_URL not found, using default: mongodb://localhost:27017")
        
        # Create connection
        self._client = AsyncIOMotorClient(mongo_url)
        self._db = self._client[db_name]
        
        logger.info(f"Database connection initialized: {db_name}")
    
    @property
    def client(self):
        """Get MongoDB client"""
        return self._client
    
    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    # Collection properties
    @property
    def users_collection(self):
        return self._db["users"]
    
    @property
    def verification_codes_collection(self):
        return self._db["verification_codes"]
    
    @property
    def recipes_collection(self):
        return self._db["recipes"]
    
    @property
    def weekly_recipes_collection(self):
        return self._db["weekly_recipes"]
    
    @property
    def starbucks_recipes_collection(self):
        return self._db["starbucks_recipes"]
    
    @property
    def curated_starbucks_recipes_collection(self):
        return self._db["curated_starbucks_recipes"]
    
    @property
    def grocery_carts_collection(self):
        return self._db["grocery_carts"]
    
    @property
    def shared_recipes_collection(self):
        return self._db["shared_recipes"]
    
    @property
    def payment_transactions_collection(self):
        return self._db["payment_transactions"]

# Create singleton instance
db_service = None

def get_db_service():
    """Get or create database service instance"""
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service