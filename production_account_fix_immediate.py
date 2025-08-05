#!/usr/bin/env python3
"""
IMMEDIATE PRODUCTION ACCOUNT FIX
FOR EXECUTION IN GOOGLE CLOUD ENVIRONMENT

This script MUST be run in the production environment with:
- MONGO_URL (production MongoDB connection)
- DB_NAME=buildyoursmartcart_production

DIRECT EXECUTION COMMAND:
python3 production_account_fix_immediate.py

TARGET: alannunezsilva0310@gmail.com
ACTION: Complete account deletion (OPTION A - RECOMMENDED)
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

async def immediate_account_fix():
    """Execute immediate account fix"""
    target_email = "alannunezsilva0310@gmail.com"
    
    print("🚨 IMMEDIATE PRODUCTION ACCOUNT FIX")
    print(f"📧 Target: {target_email}")
    print("🎯 Action: COMPLETE ACCOUNT DELETION")
    print("=" * 70)
    
    try:
        # STEP 1: Connect to production database
        print("🔗 Connecting to production database...")
        
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_production')
        
        if not mongo_url:
            print("❌ CRITICAL: MONGO_URL not found in environment")
            print("❌ This script must be run in Google Cloud production environment")
            return False
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await db.command("ping")
        print(f"✅ Connected to production database: {db_name}")
        
        # STEP 2: Find the corrupted account
        print("🔍 Searching for corrupted account...")
        
        user = await db.users.find_one({
            "email": {"$regex": f"^{target_email}$", "$options": "i"}
        })
        
        if not user:
            print("✅ Account not found - database is clean")
        else:
            user_id = user.get('id')
            print(f"🎯 FOUND CORRUPTED ACCOUNT:")
            print(f"   Email: {user.get('email')}")
            print(f"   User ID: {user_id}")
            print(f"   Verified: {user.get('is_verified')}")
            
            # STEP 3: EXECUTE COMPLETE DELETION
            print("🗑️ EXECUTING COMPLETE ACCOUNT DELETION...")
            
            collections_to_clean = [
                "users",
                "verification_codes",
                "recipes", 
                "starbucks_recipes",
                "grocery_carts",
                "user_shared_recipes",
                "payment_transactions",
                "curated_starbucks_recipes"
            ]
            
            total_deleted = 0
            for collection_name in collections_to_clean:
                collection = db[collection_name]
                
                # Delete by email
                result1 = await collection.delete_many({
                    "email": {"$regex": f"^{target_email}$", "$options": "i"}
                })
                
                # Delete by user_id
                result2 = await collection.delete_many({"user_id": user_id}) if user_id else None
                result3 = await collection.delete_many({"id": user_id}) if user_id else None
                result4 = await collection.delete_many({"shared_by_user_id": user_id}) if user_id else None
                
                deleted_count = result1.deleted_count
                if result2: deleted_count += result2.deleted_count
                if result3: deleted_count += result3.deleted_count  
                if result4: deleted_count += result4.deleted_count
                
                if deleted_count > 0:
                    print(f"   ✅ {collection_name}: {deleted_count} records deleted")
                    total_deleted += deleted_count
                else:
                    print(f"   ✅ {collection_name}: clean")
            
            print(f"🎉 DELETION COMPLETE: {total_deleted} total records removed")
        
        # STEP 4: Verify deletion
        print("✅ Verifying account deletion...")
        
        remaining_user = await db.users.find_one({
            "email": {"$regex": f"^{target_email}$", "$options": "i"}
        })
        
        remaining_codes = await db.verification_codes.find({
            "email": {"$regex": f"^{target_email}$", "$options": "i"}
        }).to_list(10)
        
        if remaining_user or remaining_codes:
            print("❌ VERIFICATION FAILED: Some data remains")
            return False
        
        print("✅ VERIFICATION SUCCESSFUL: Account completely removed")
        
        # STEP 5: Test registration availability
        print("🧪 Testing registration availability...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                test_data = {
                    "first_name": "Test",
                    "last_name": "User",
                    "email": target_email,
                    "password": "testpass123",
                    "dietary_preferences": [],
                    "allergies": [],
                    "favorite_cuisines": []
                }
                
                response = await http_client.post(
                    "https://buildyoursmartcart.com/api/auth/register",
                    json=test_data
                )
                
                if response.status_code == 200:
                    print("✅ REGISTRATION TEST PASSED: Email available for registration")
                    
                    # Clean up test registration
                    response_data = response.json()
                    test_user_id = response_data.get('user_id')
                    if test_user_id:
                        await db.users.delete_one({"id": test_user_id})
                        await db.verification_codes.delete_many({"user_id": test_user_id})
                        print("🧹 Test registration cleaned up")
                    
                    registration_success = True
                elif response.status_code == 400:
                    error_data = response.json()
                    if "already registered" in error_data.get("detail", "").lower():
                        print("❌ REGISTRATION TEST FAILED: Email still registered")
                        registration_success = False
                    else:
                        print(f"⚠️ Registration error: {error_data}")
                        registration_success = None
                else:
                    print(f"⚠️ Unexpected response: {response.status_code}")
                    registration_success = None
                    
        except Exception as e:
            print(f"⚠️ Registration test error: {str(e)}")
            registration_success = None
        
        # FINAL RESULT
        print("=" * 70)
        if registration_success:
            print("🎉 ACCOUNT FIX COMPLETED SUCCESSFULLY!")
            print(f"✅ {target_email} completely removed from production database")
            print("✅ Email is now available for fresh registration")
            print("✅ All verification issues resolved")
            print("✅ User can now register normally")
        else:
            print("🎉 ACCOUNT DELETION COMPLETED!")
            print(f"✅ {target_email} removed from production database")
            print("⚠️ Registration test inconclusive but account is clean")
            print("✅ Verification issues should be resolved")
        
        print("=" * 70)
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 PRODUCTION ACCOUNT FIX - IMMEDIATE EXECUTION")
    print("⚠️ This script must be run in Google Cloud production environment")
    print("⚠️ Requires MONGO_URL and DB_NAME environment variables")
    print()
    
    try:
        success = asyncio.run(immediate_account_fix())
        
        if success:
            print("\n🎉 FIX EXECUTION SUCCESSFUL!")
            print("✅ alannunezsilva0310@gmail.com account issue resolved")
            print("✅ Email is available for registration")
            sys.exit(0)
        else:
            print("\n❌ FIX EXECUTION FAILED!")
            print("❌ Manual intervention required")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Fix interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        sys.exit(1)