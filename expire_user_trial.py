#!/usr/bin/env python3
"""
Script to expire a user's trial for testing subscription access control
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def expire_user_trial():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ.get('DB_NAME', 'test_database')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    users_collection = db["users"]
    
    # Update the expired user's trial to be expired
    expired_user_id = "6d8c4a48-f297-4dad-9ab0-ef0be1837c1c"
    expired_date = datetime.utcnow() - timedelta(days=1)  # Yesterday
    
    result = await users_collection.update_one(
        {"id": expired_user_id},
        {
            "$set": {
                "trial_end_date": expired_date,
                "subscription_status": "expired"
            }
        }
    )
    
    if result.matched_count > 0:
        print(f"✅ Updated user {expired_user_id} trial to expired")
        print(f"Trial end date set to: {expired_date}")
    else:
        print(f"❌ User {expired_user_id} not found")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(expire_user_trial())