#!/usr/bin/env python3
"""
Simple Password Reset Fix Test
"""

import asyncio
import httpx
import sys
from datetime import datetime, timedelta
from pathlib import Path
import uuid

# Add backend to path
sys.path.append('/app/backend')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import bcrypt

# Load environment variables
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

# Database connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Get backend URL
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://buildyoursmartcart.com') + '/api'

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

async def test_password_reset_fix():
    """Simple test of password reset fix"""
    print("=== SIMPLE PASSWORD RESET FIX TEST ===")
    
    test_email = "simple_reset_test@example.com"
    original_password = "original123"
    new_password = "newpass456"
    
    http_client = httpx.AsyncClient(timeout=30.0)
    
    try:
        # Clean up
        await db.users.delete_many({"email": test_email})
        await db.verification_codes.delete_many({"email": test_email})
        await db.password_reset_codes.delete_many({"email": test_email})
        
        # Create verified user directly in database
        user_doc = {
            "id": str(uuid.uuid4()),
            "first_name": "Simple",
            "last_name": "Test",
            "email": test_email,
            "password_hash": hash_password(original_password),
            "dietary_preferences": [],
            "allergies": [],
            "favorite_cuisines": [],
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "verified_at": datetime.utcnow(),
            "subscription_status": "trial",
            "trial_start_date": datetime.utcnow(),
            "trial_end_date": datetime.utcnow() + timedelta(weeks=7)
        }
        
        await db.users.insert_one(user_doc)
        print(f"✅ Created verified test user: {test_email}")
        
        # Test login before reset
        login_data = {"email": test_email, "password": original_password}
        response = await http_client.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            status_before = result.get('status', 'unknown')
            print(f"✅ Login before reset: {status_before}")
        else:
            print(f"❌ Login before reset failed: {response.text}")
            return False
        
        # Check database before reset
        user_before = await db.users.find_one({"email": test_email})
        print(f"Before reset - is_verified: {user_before.get('is_verified', False)}")
        
        # Create password reset code directly
        reset_code = "123456"
        reset_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_doc["id"],
            "email": test_email,
            "code": reset_code,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=15),
            "is_used": False
        }
        
        await db.password_reset_codes.insert_one(reset_doc)
        print("✅ Created password reset code")
        
        # Execute password reset
        reset_data = {
            "email": test_email,
            "reset_code": reset_code,
            "new_password": new_password
        }
        
        response = await http_client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
        
        if response.status_code == 200:
            print("✅ Password reset completed")
        else:
            print(f"❌ Password reset failed: {response.text}")
            return False
        
        # Check database after reset
        user_after = await db.users.find_one({"email": test_email})
        is_verified_after = user_after.get('is_verified', False)
        print(f"After reset - is_verified: {is_verified_after}")
        
        # Test login after reset
        login_data_new = {"email": test_email, "password": new_password}
        response = await http_client.post(f"{BACKEND_URL}/auth/login", json=login_data_new)
        
        if response.status_code == 200:
            result = response.json()
            status_after = result.get('status', 'unknown')
            print(f"✅ Login after reset: {status_after}")
            
            if status_after == 'success':
                print("🎉 FIX SUCCESSFUL: Password reset preserves verification status")
                success = True
            else:
                print("🚨 FIX FAILED: User still needs verification after password reset")
                success = False
        else:
            print(f"❌ Login after reset failed: {response.text}")
            success = False
        
        # Cleanup
        await db.users.delete_many({"email": test_email})
        await db.password_reset_codes.delete_many({"email": test_email})
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    finally:
        await http_client.aclose()
        client.close()

if __name__ == "__main__":
    result = asyncio.run(test_password_reset_fix())
    print(f"\nTest result: {'PASSED' if result else 'FAILED'}")