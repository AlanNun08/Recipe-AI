#!/usr/bin/env python3
"""
Demo User Verification Fix
Verify the demo user is now accessible and fix if needed
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

async def fix_demo_user():
    """Check and fix demo user verification status"""
    try:
        print("🔍 Demo User Verification Fix")
        print("=" * 40)
        
        # Connect to database
        sys.path.append('/app/backend')
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
        
        # Find demo user
        demo_user = await db.users.find_one({"email": "demo@test.com"})
        
        if demo_user:
            print(f"Demo user found:")
            print(f"  ID: {demo_user.get('id')}")
            print(f"  Email: {demo_user.get('email')}")
            print(f"  is_verified: {demo_user.get('is_verified')}")
            print(f"  verified_at: {demo_user.get('verified_at')}")
            
            if demo_user.get('is_verified'):
                print("✅ Demo user is already verified!")
            else:
                print("❌ Demo user is not verified, fixing...")
                
                # Update demo user to be verified
                await db.users.update_one(
                    {"email": "demo@test.com"},
                    {
                        "$set": {
                            "is_verified": True,
                            "verified_at": datetime.utcnow()
                        }
                    }
                )
                print("✅ Demo user verification status fixed!")
        else:
            print("❌ Demo user not found in database")
        
        # Clear rate limiting for demo user (if possible)
        print("\nClearing rate limits...")
        # Rate limits are stored in memory, so restarting the backend would clear them
        # For now, let's just note this
        print("Note: Rate limits are in memory and will clear after backend restart")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_demo_user())