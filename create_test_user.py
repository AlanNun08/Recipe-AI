#!/usr/bin/env python3
"""
Create a test user in MongoDB for authentication testing
"""
import asyncio
import os
import sys
import hashlib
import uuid
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def create_test_user():
    """Create test user fresh@test.com in MongoDB"""
    
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
        
        # Check if user already exists
        existing_user = await users_collection.find_one({"email": "fresh@test.com"})
        if existing_user:
            print("⚠️ User fresh@test.com already exists")
            print(f"   User ID: {existing_user.get('id')}")
            print(f"   Verified: {existing_user.get('verified', False)}")
            
            # Update to ensure user is verified
            await users_collection.update_one(
                {"email": "fresh@test.com"},
                {"$set": {"verified": True}}
            )
            print("✅ User updated to verified status")
            return
        
        # Create test user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password("password123")
        
        user_document = {
            "id": user_id,
            "email": "fresh@test.com",
            "password_hash": hashed_password,
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
        
        # Insert user
        result = await users_collection.insert_one(user_document)
        print(f"✅ Test user created successfully!")
        print(f"   Email: fresh@test.com")
        print(f"   Password: password123")
        print(f"   User ID: {user_id}")
        print(f"   Database ID: {result.inserted_id}")
        print(f"   Verified: True")
        
        # List all users for verification
        user_count = await users_collection.count_documents({})
        print(f"📊 Total users in database: {user_count}")
        
        await client.close()
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        sys.exit(1)

if __name__ == "__main__":
    print("🧪 Creating test user for authentication testing...")
    asyncio.run(create_test_user())
    print("🎉 Test user creation complete!")
    print("\n📝 Test login credentials:")
    print("   Email: fresh@test.com")
    print("   Password: password123")
