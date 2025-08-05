#!/usr/bin/env python3
"""
Environment Debug Script
Check what database the API is actually using
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

# Load frontend environment for backend URL
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)

# Get backend URL from frontend environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://buildyoursmartcart.com/api')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = BACKEND_URL.rstrip('/') + '/api'

async def debug_environment():
    """Debug environment and database connections"""
    try:
        print("🔍 Environment Debug")
        print("=" * 50)
        
        # Check local environment
        print("Local Environment Variables:")
        print(f"MONGO_URL: {os.environ.get('MONGO_URL')}")
        print(f"DB_NAME: {os.environ.get('DB_NAME', 'buildyoursmartcart_development')}")
        print(f"REACT_APP_BACKEND_URL: {os.environ.get('REACT_APP_BACKEND_URL')}")
        print()
        
        # Check what database the local connection uses
        print("Local Database Check:")
        sys.path.append('/app/backend')
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
        
        # Count users in local database
        user_count = await db.users.count_documents({})
        demo_users = await db.users.find({"email": {"$regex": "demo", "$options": "i"}}).to_list(10)
        
        print(f"Local database has {user_count} users")
        print("Demo users in local database:")
        for user in demo_users:
            print(f"  {user.get('email')} - ID: {user.get('id')} - verified: {user.get('is_verified')}")
        print()
        
        # Test API to see what database it's using
        print("API Database Check:")
        client_http = httpx.AsyncClient(timeout=30.0)
        
        # Try to create a unique test user via API
        test_email = f"env_debug_{int(datetime.now().timestamp())}@example.com"
        user_data = {
            "first_name": "Debug",
            "last_name": "Test",
            "email": test_email,
            "password": "debugtest123",
            "dietary_preferences": [],
            "allergies": [],
            "favorite_cuisines": []
        }
        
        response = await client_http.post(f"{BACKEND_URL}/auth/register", json=user_data)
        print(f"API registration response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            api_user_id = result.get("user_id")
            print(f"API created user with ID: {api_user_id}")
            
            # Check if this user appears in local database
            local_user = await db.users.find_one({"id": api_user_id})
            if local_user:
                print("✅ User created by API appears in local database - same database")
            else:
                print("❌ User created by API does NOT appear in local database - different databases")
                
                # Check if user appears with email search
                local_user_by_email = await db.users.find_one({"email": test_email})
                if local_user_by_email:
                    print(f"  But found user by email with different ID: {local_user_by_email.get('id')}")
                else:
                    print("  User not found by email either - definitely different databases")
        
        await client_http.aclose()
        await client.close()
        
    except Exception as e:
        print(f"❌ Error debugging environment: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_environment())