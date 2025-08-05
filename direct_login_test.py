#!/usr/bin/env python3
"""
Direct Backend Login Test
"""

import asyncio
import sys
from pathlib import Path

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

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

async def test_direct_login():
    """Test login logic directly"""
    print("=== DIRECT BACKEND LOGIN TEST ===")
    
    email_input = "demo@test.com"
    password_input = "password123"
    email_lower = email_input.lower()
    
    print(f"Testing login for: {email_input}")
    print(f"Database URL: {mongo_url}")
    print(f"Database name: {db_name}")
    
    # Step 1: Find user (same logic as login function)
    user = None
    
    # 1. Try exact match
    user = await db.users.find_one({"email": email_input})
    print(f"Exact match search: {'Found' if user else 'Not found'}")
    
    # 2. Try lowercase
    if not user:
        user = await db.users.find_one({"email": email_lower})
        print(f"Lowercase search: {'Found' if user else 'Not found'}")
    
    # 3. Try case-insensitive search
    if not user:
        all_users = await db.users.find().to_list(length=100)
        for u in all_users:
            if u.get('email', '').lower() == email_lower:
                user = u
                break
        print(f"Case-insensitive search: {'Found' if user else 'Not found'}")
    
    if not user:
        print("❌ User not found")
        return
    
    print(f"✅ User found:")
    print(f"   Email: {user.get('email')}")
    print(f"   ID: {user.get('id')}")
    print(f"   Is verified: {user.get('is_verified', False)}")
    print(f"   Verified at: {user.get('verified_at', 'N/A')}")
    
    # Step 2: Verify password
    password_valid = verify_password(password_input, user["password_hash"])
    print(f"Password valid: {password_valid}")
    
    if not password_valid:
        print("❌ Invalid password")
        return
    
    # Step 3: Check verification status (same logic as login function)
    is_verified = user.get("is_verified", False)
    print(f"Verification check: {is_verified}")
    
    if not is_verified:
        print("❌ User not verified - would return 'unverified' status")
        return {
            "status": "unverified",
            "message": "Email not verified. Please verify your email first.",
            "email": user["email"],
            "user_id": user["id"],
            "needs_verification": True
        }
    else:
        print("✅ User verified - would return 'success' status")
        return {
            "status": "success",
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "email": user["email"],
                "is_verified": user["is_verified"]
            },
            "user_id": user["id"],
            "email": user["email"]
        }

async def main():
    try:
        result = await test_direct_login()
        print(f"\nResult: {result}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())