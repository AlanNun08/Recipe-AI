#!/usr/bin/env python3
"""
Fix the test user in MongoDB to ensure proper authentication
"""
import asyncio
import os
import hashlib
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

def hash_password(password: str) -> str:
    """Hash password using SHA-256 (same as backend)"""
    return hashlib.sha256(password.encode()).hexdigest()

async def fix_test_user():
    """Fix or create the test user with proper structure"""
    
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_production')
    
    print(f"🔗 Connecting to MongoDB: {mongo_url}")
    print(f"📊 Database: {db_name}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        users_collection = db["users"]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check if user exists
        existing_user = await users_collection.find_one({"email": "fresh@test.com"})
        
        if existing_user:
            print("⚠️ Existing user found:")
            print(f"   Email: {existing_user.get('email')}")
            print(f"   Fields: {list(existing_user.keys())}")
            print(f"   Has password_hash: {'password_hash' in existing_user}")
            print(f"   Verified: {existing_user.get('verified', False)}")
            
            # Delete the existing user and recreate properly
            await users_collection.delete_one({"email": "fresh@test.com"})
            print("🗑️ Deleted existing user to recreate properly")
        
        # Create test user with proper structure from scratch
        user_id = str(uuid.uuid4())
        hashed_password = hash_password("password123")
        
        user_document = {
            "id": user_id,
            "email": "fresh@test.com",
            "password_hash": hashed_password,  # This is the critical field!
            "name": "Test User",
            "phone": None,
            "verified": True,  # Pre-verify for testing
            "created_at": datetime.utcnow(),
            "last_login": None,
            "preferences": {
                "dietaryRestrictions": ["Vegetarian"],
                "cuisinePreferences": ["Italian", "Mexican"],
                "cookingSkillLevel": "intermediate",
                "householdSize": 4,
                "weeklyBudget": "moderate"
            },
            "subscription_status": "free",
            "onboarding_completed": True
        }
        
        result = await users_collection.insert_one(user_document)
        print(f"✅ Test user created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Database ID: {result.inserted_id}")
        
        # Verify the user is correct now
        final_user = await users_collection.find_one({"email": "fresh@test.com"})
        print("\n🔍 Final user verification:")
        print(f"   Email: {final_user.get('email')}")
        print(f"   Has password_hash: {'password_hash' in final_user}")
        print(f"   Password hash: {final_user.get('password_hash', 'MISSING')[:20]}...")
        print(f"   Verified: {final_user.get('verified')}")
        print(f"   Name: {final_user.get('name')}")
        print(f"   ID: {final_user.get('id')}")
        
        # Test password verification
        test_password = "password123"
        stored_hash = final_user.get('password_hash')
        test_hash = hash_password(test_password)
        password_match = test_hash == stored_hash
        
        print(f"\n🔐 Password verification test:")
        print(f"   Test password: {test_password}")
        print(f"   Generated hash: {test_hash[:20]}...")
        print(f"   Stored hash: {stored_hash[:20] if stored_hash else 'NONE'}...")
        print(f"   Passwords match: {password_match}")
        
        if not password_match:
            print("❌ Password hashes don't match - this shouldn't happen!")
        
        await client.close()
        
        print(f"\n🎉 Test user ready!")
        print(f"📝 Login credentials:")
        print(f"   Email: fresh@test.com")
        print(f"   Password: password123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Error type: {type(e).__name__}")

if __name__ == "__main__":
    # Set environment variables if not set
    if not os.environ.get('MONGO_URL'):
        os.environ['MONGO_URL'] = 'mongodb://localhost:27017'
    if not os.environ.get('DB_NAME'):
        os.environ['DB_NAME'] = 'buildyoursmartcart_production'
    
    print("🔧 Fixing test user in MongoDB...")
    asyncio.run(fix_test_user())
