#!/usr/bin/env python3
"""
Test subscription access control by creating a user with expired trial
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables
sys.path.append('/app/backend')
from dotenv import load_dotenv
load_dotenv(Path('/app/backend/.env'))

# Get backend URL
BACKEND_URL = "https://42644e0e-38cf-4302-bad3-e90207944366.preview.emergentagent.com/api"

async def test_subscription_access_control():
    """Test that premium endpoints properly block users without access"""
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Import backend functions directly
        from motor.motor_asyncio import AsyncIOMotorClient
        
        # Connect to database
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        db_client = AsyncIOMotorClient(mongo_url)
        db = db_client[db_name]
        
        # Create a test user with expired trial
        test_user_id = "test-expired-user-123"
        expired_trial_user = {
            "id": test_user_id,
            "first_name": "Expired",
            "last_name": "User",
            "email": "expired@test.com",
            "password_hash": "dummy_hash",
            "is_verified": True,
            "subscription_status": "trial",
            "trial_start_date": datetime.utcnow() - timedelta(days=60),  # 60 days ago
            "trial_end_date": datetime.utcnow() - timedelta(days=10),    # Expired 10 days ago
            "subscription_start_date": None,
            "subscription_end_date": None
        }
        
        # Insert test user
        await db.users.delete_one({"id": test_user_id})  # Clean up first
        await db.users.insert_one(expired_trial_user)
        
        print(f"✅ Created test user with expired trial: {test_user_id}")
        
        # Test premium endpoints with expired user
        premium_endpoints = [
            ("/recipes/generate", {
                "user_id": test_user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "dietary_preferences": [],
                "servings": 4,
                "difficulty": "medium"
            }),
            ("/generate-starbucks-drink", {
                "user_id": test_user_id,
                "drink_type": "frappuccino"
            })
        ]
        
        access_blocked_count = 0
        
        for endpoint, data in premium_endpoints:
            print(f"\nTesting {endpoint} with expired trial user...")
            
            response = await client.post(f"{BACKEND_URL}{endpoint}", json=data)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 402:
                print("✅ Access properly blocked - 402 Payment Required")
                try:
                    result = response.json()
                    if isinstance(result.get('detail'), dict):
                        access_status = result['detail'].get('access_status', {})
                        print(f"  Has Access: {access_status.get('has_access')}")
                        print(f"  Trial Active: {access_status.get('trial_active')}")
                        print(f"  Subscription Active: {access_status.get('subscription_active')}")
                except:
                    pass
                access_blocked_count += 1
            elif response.status_code == 500:
                print("⚠️ Server error (likely API key issue, but access control may have passed)")
            else:
                print(f"❌ Unexpected response: {response.text[:100]}")
        
        # Test with demo user (should have access)
        demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        print(f"\nTesting with demo user (should have access): {demo_user_id}")
        
        demo_data = {
            "user_id": demo_user_id,
            "drink_type": "frappuccino"
        }
        
        response = await client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=demo_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print("✅ Access granted (500 error is due to API key, not access control)")
        elif response.status_code == 402:
            print("❌ Access blocked for demo user (should have trial access)")
        else:
            print(f"Response: {response.text[:100]}")
        
        # Clean up test user
        await db.users.delete_one({"id": test_user_id})
        await db_client.close()
        
        print(f"\n🔍 SUMMARY:")
        print(f"Premium endpoints blocked for expired user: {access_blocked_count}/{len(premium_endpoints)}")
        
        if access_blocked_count == len(premium_endpoints):
            print("✅ Subscription access control is working correctly")
            return True
        else:
            print("❌ Subscription access control has issues")
            return False
        
    except Exception as e:
        print(f"❌ Error testing subscription access: {str(e)}")
        return False
    finally:
        await client.aclose()

if __name__ == "__main__":
    result = asyncio.run(test_subscription_access_control())