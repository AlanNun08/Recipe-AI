#!/usr/bin/env python3
"""
Database Investigation Script
Check for duplicate demo users and verification status issues
"""

import asyncio
import os
import sys
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

# Load backend environment
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

async def investigate_database():
    """Investigate database for demo user issues"""
    try:
        # Import database connection
        sys.path.append('/app/backend')
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            print("❌ No database connection available")
            return
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
        
        print("🔍 Investigating demo@test.com users in database...")
        print("=" * 60)
        
        # Find all users with demo@test.com email (case insensitive)
        demo_users = await db.users.find({
            "email": {"$regex": "^demo@test.com$", "$options": "i"}
        }).to_list(100)
        
        print(f"Found {len(demo_users)} demo users:")
        print()
        
        for i, user in enumerate(demo_users, 1):
            print(f"Demo User #{i}:")
            print(f"  ID: {user.get('id')}")
            print(f"  Email: {user.get('email')}")
            print(f"  is_verified: {user.get('is_verified')}")
            print(f"  verified_at: {user.get('verified_at')}")
            print(f"  created_at: {user.get('created_at')}")
            print(f"  first_name: {user.get('first_name')}")
            print(f"  last_name: {user.get('last_name')}")
            print()
        
        # Also check for any case variations
        print("Checking for case variations...")
        all_demo_variations = await db.users.find({
            "email": {"$regex": "demo.*test", "$options": "i"}
        }).to_list(100)
        
        print(f"Found {len(all_demo_variations)} users with demo/test in email:")
        for user in all_demo_variations:
            print(f"  {user.get('email')} - verified: {user.get('is_verified')} - ID: {user.get('id')}")
        
        # Check verification codes for demo user
        print("\nChecking verification codes...")
        verification_codes = await db.verification_codes.find({
            "email": {"$regex": "^demo@test.com$", "$options": "i"}
        }).sort("created_at", -1).to_list(10)
        
        print(f"Found {len(verification_codes)} verification codes:")
        for code in verification_codes:
            print(f"  Code: {code.get('code')} - Used: {code.get('is_used')} - Created: {code.get('created_at')}")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error investigating database: {str(e)}")

if __name__ == "__main__":
    asyncio.run(investigate_database())