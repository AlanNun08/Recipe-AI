#!/usr/bin/env python3
"""
Quick Database Test
Test if API and local database are now the same
"""

import asyncio
import httpx
import os
import sys
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

# Load backend environment
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

async def quick_database_test():
    """Quick test to see if API and local database are the same"""
    try:
        print("🔍 Quick Database Sync Test")
        print("=" * 40)
        
        # Check local database
        sys.path.append('/app/backend')
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
        
        # Create a unique test user via API
        client_http = httpx.AsyncClient(timeout=30.0)
        
        test_email = f"sync_test_{int(datetime.now().timestamp())}@example.com"
        user_data = {
            "first_name": "Sync",
            "last_name": "Test",
            "email": test_email,
            "password": "synctest123",
            "dietary_preferences": [],
            "allergies": [],
            "favorite_cuisines": []
        }
        
        response = await client_http.post("http://localhost:8001/api/auth/register", json=user_data)
        print(f"API registration: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            api_user_id = result.get("user_id")
            print(f"API created user ID: {api_user_id}")
            
            # Check if this user appears in local database
            await asyncio.sleep(1)  # Give it a moment
            local_user = await db.users.find_one({"id": api_user_id})
            if local_user:
                print("✅ API and local database are now SYNCHRONIZED!")
                print(f"User found in local DB: {local_user.get('email')}")
            else:
                print("❌ Still using different databases")
        
        await client_http.aclose()
        await client.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(quick_database_test())