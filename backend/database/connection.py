import motor.motor_asyncio
import os
from typing import Optional

# Global database connection
_database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

async def get_database():
    """Get database connection"""
    global _database
    
    if _database is None:
        # Initialize database connection
        mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "buildyoursmartcart_production")
        
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        _database = client[db_name]
    
    return _database
