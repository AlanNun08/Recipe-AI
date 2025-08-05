#!/usr/bin/env python3
"""
Login Debug Script
Debug the exact login process to find where the issue is
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

DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

async def debug_login_process():
    """Debug the login process step by step"""
    try:
        print("🔍 Debugging Login Process")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Demo Email: {DEMO_USER_EMAIL}")
        print()
        
        # Step 1: Check database directly
        print("Step 1: Direct Database Check")
        sys.path.append('/app/backend')
        from motor.motor_asyncio import AsyncIOMotorClient
        
        mongo_url = os.environ.get('MONGO_URL')
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
        
        # Try different search methods like the backend does
        email_input = DEMO_USER_EMAIL.strip()
        email_lower = email_input.lower()
        
        print(f"Searching for: '{email_input}' and '{email_lower}'")
        
        # 1. Try exact match
        user1 = await db.users.find_one({"email": email_input})
        print(f"Exact match result: {user1 is not None}")
        if user1:
            print(f"  ID: {user1.get('id')}, verified: {user1.get('is_verified')}")
        
        # 2. Try lowercase
        user2 = await db.users.find_one({"email": email_lower})
        print(f"Lowercase match result: {user2 is not None}")
        if user2:
            print(f"  ID: {user2.get('id')}, verified: {user2.get('is_verified')}")
        
        # 3. Try case-insensitive search
        all_users = await db.users.find().to_list(length=100)
        user3 = None
        for u in all_users:
            if u.get('email', '').lower() == email_lower:
                user3 = u
                break
        
        print(f"Case-insensitive search result: {user3 is not None}")
        if user3:
            print(f"  ID: {user3.get('id')}, verified: {user3.get('is_verified')}")
        
        print()
        
        # Step 2: Test API login
        print("Step 2: API Login Test")
        
        client_http = httpx.AsyncClient(timeout=30.0)
        
        login_data = {
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD
        }
        
        response = await client_http.post(f"{BACKEND_URL}/auth/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        await client_http.aclose()
        await client.close()
        
        # Step 3: Check if there are multiple databases
        print("\nStep 3: Database Configuration Check")
        print(f"MONGO_URL: {mongo_url}")
        print(f"DB_NAME: {os.environ.get('DB_NAME', 'buildyoursmartcart_development')}")
        
        # List all databases
        db_list = await client.list_database_names()
        print(f"Available databases: {db_list}")
        
        # Check users in each database that might contain demo users
        for db_name in db_list:
            if 'test' in db_name.lower() or 'build' in db_name.lower() or 'smart' in db_name.lower():
                test_db = client[db_name]
                demo_count = await test_db.users.count_documents({"email": {"$regex": "demo", "$options": "i"}})
                if demo_count > 0:
                    print(f"Database '{db_name}' has {demo_count} demo users")
                    demo_users = await test_db.users.find({"email": {"$regex": "demo", "$options": "i"}}).to_list(10)
                    for user in demo_users:
                        print(f"  {user.get('email')} - ID: {user.get('id')} - verified: {user.get('is_verified')}")
        
    except Exception as e:
        print(f"❌ Error debugging login: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_login_process())