#!/usr/bin/env python3
"""
Password Reset Bug Fix Verification Test
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path for direct database access
sys.path.append('/app/backend')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

# Database connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Get backend URL from frontend env
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://buildyoursmartcart.com') + '/api'

class PasswordResetFixTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
        if client:
            client.close()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_password_reset_fix(self):
        """Test that the password reset fix preserves verification status"""
        self.log("=== TESTING PASSWORD RESET FIX ===")
        
        try:
            # Create a test user
            test_email = "password_reset_fix_test@example.com"
            original_password = "originalpass123"
            new_password = "newpassword456"
            
            # Clean up any existing test user
            await db.users.delete_many({"email": test_email})
            await db.verification_codes.delete_many({"email": test_email})
            await db.password_reset_codes.delete_many({"email": test_email})
            
            self.log(f"Creating test user: {test_email}")
            
            # Step 1: Register test user
            register_data = {
                "first_name": "Password",
                "last_name": "ResetTest",
                "email": test_email,
                "password": original_password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code != 200:
                self.log(f"❌ Registration failed: {response.text}")
                return False
            
            self.log("✅ Test user registered")
            
            # Step 2: Verify the user
            verification_codes = await db.verification_codes.find({"email": test_email, "is_used": False}).to_list(10)
            if not verification_codes:
                self.log("❌ No verification code found")
                return False
            
            verify_code = verification_codes[0]['code']
            verify_data = {
                "email": test_email,
                "code": verify_code
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
            if response.status_code != 200:
                self.log(f"❌ Verification failed: {response.text}")
                return False
            
            self.log("✅ Test user verified")
            
            # Step 3: Test login before password reset
            login_data = {
                "email": test_email,
                "password": original_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                login_result = response.json()
                status_before = login_result.get('status', 'unknown')
                self.log(f"✅ Login before reset - Status: {status_before}")
                
                if status_before != 'success':
                    self.log(f"❌ Unexpected login status before reset: {status_before}")
                    return False
            else:
                self.log(f"❌ Login before reset failed: {response.text}")
                return False
            
            # Step 4: Check verification status before reset
            user_before = await db.users.find_one({"email": test_email})
            is_verified_before = user_before.get('is_verified', False)
            verified_at_before = user_before.get('verified_at')
            
            self.log(f"BEFORE password reset:")
            self.log(f"   is_verified: {is_verified_before}")
            self.log(f"   verified_at: {verified_at_before}")
            
            # Step 5: Initiate password reset
            reset_request_data = {
                "email": test_email
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request_data)
            if response.status_code != 200:
                self.log(f"❌ Password reset request failed: {response.text}")
                return False
            
            self.log("✅ Password reset request sent")
            
            # Step 6: Execute password reset
            reset_codes = await db.password_reset_codes.find({"email": test_email, "is_used": False}).sort("created_at", -1).to_list(10)
            if not reset_codes:
                self.log("❌ No password reset code found")
                return False
            
            reset_code = reset_codes[0]['code']
            reset_data = {
                "email": test_email,
                "reset_code": reset_code,
                "new_password": new_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
            if response.status_code != 200:
                self.log(f"❌ Password reset failed: {response.text}")
                return False
            
            self.log("✅ Password reset completed")
            
            # Step 7: Check verification status after reset
            user_after = await db.users.find_one({"email": test_email})
            is_verified_after = user_after.get('is_verified', False)
            verified_at_after = user_after.get('verified_at')
            
            self.log(f"AFTER password reset:")
            self.log(f"   is_verified: {is_verified_after}")
            self.log(f"   verified_at: {verified_at_after}")
            
            # Step 8: Verify the fix worked
            if is_verified_before and is_verified_after:
                self.log("✅ FIX VERIFIED: Verification status preserved during password reset")
                fix_successful = True
            else:
                self.log("🚨 FIX FAILED: Verification status was lost during password reset")
                fix_successful = False
            
            # Step 9: Test login after password reset
            login_data_new = {
                "email": test_email,
                "password": new_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data_new)
            if response.status_code == 200:
                login_result = response.json()
                status_after = login_result.get('status', 'unknown')
                self.log(f"✅ Login after reset - Status: {status_after}")
                
                if status_after == 'success':
                    self.log("✅ FIX CONFIRMED: User can login successfully after password reset")
                elif status_after == 'unverified':
                    self.log("🚨 FIX FAILED: User is still being asked to verify after password reset")
                    fix_successful = False
                else:
                    self.log(f"⚠️ Unexpected login status: {status_after}")
                    fix_successful = False
            else:
                self.log(f"❌ Login after reset failed: {response.text}")
                fix_successful = False
            
            # Step 10: Cleanup
            await db.users.delete_many({"email": test_email})
            await db.verification_codes.delete_many({"email": test_email})
            await db.password_reset_codes.delete_many({"email": test_email})
            self.log("✅ Test user cleaned up")
            
            return fix_successful
            
        except Exception as e:
            self.log(f"❌ Error testing password reset fix: {str(e)}", "ERROR")
            return False
    
    async def test_alannunezsilva_account_reset(self):
        """Verify the target account is completely reset"""
        self.log("=== VERIFYING ALANNUNEZSILVA ACCOUNT RESET ===")
        
        target_email = "alannunezsilva0310@gmail.com"
        
        try:
            # Check if account exists
            user = await db.users.find_one({"email": {"$regex": f"^{target_email}$", "$options": "i"}})
            
            if user:
                self.log(f"❌ Target account {target_email} still exists")
                return False
            else:
                self.log(f"✅ Target account {target_email} completely removed")
            
            # Check for any related data
            verification_codes = await db.verification_codes.find({"email": {"$regex": f"^{target_email}$", "$options": "i"}}).to_list(100)
            reset_codes = await db.password_reset_codes.find({"email": {"$regex": f"^{target_email}$", "$options": "i"}}).to_list(100)
            
            if verification_codes or reset_codes:
                self.log(f"⚠️ Found {len(verification_codes)} verification codes and {len(reset_codes)} reset codes")
                # Clean them up
                await db.verification_codes.delete_many({"email": {"$regex": f"^{target_email}$", "$options": "i"}})
                await db.password_reset_codes.delete_many({"email": {"$regex": f"^{target_email}$", "$options": "i"}})
                self.log("✅ Cleaned up remaining codes")
            
            self.log("✅ Account reset verification complete - clean slate for re-registration")
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying account reset: {str(e)}", "ERROR")
            return False
    
    async def test_new_registration_flow(self):
        """Test that new registration works properly"""
        self.log("=== TESTING NEW REGISTRATION FLOW ===")
        
        try:
            test_email = "new_registration_test@example.com"
            test_password = "newregtest123"
            
            # Clean up any existing test user
            await db.users.delete_many({"email": test_email})
            await db.verification_codes.delete_many({"email": test_email})
            
            # Test registration
            register_data = {
                "first_name": "New",
                "last_name": "Registration",
                "email": test_email,
                "password": test_password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                self.log("✅ New registration works properly")
                
                # Clean up
                await db.users.delete_many({"email": test_email})
                await db.verification_codes.delete_many({"email": test_email})
                return True
            else:
                self.log(f"❌ New registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing new registration: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_fix_test(self):
        """Run comprehensive test of the password reset fix"""
        self.log("🔧 COMPREHENSIVE PASSWORD RESET FIX VERIFICATION")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Verify account reset
        results["account_reset"] = await self.test_alannunezsilva_account_reset()
        
        # Test 2: Test password reset fix
        results["password_reset_fix"] = await self.test_password_reset_fix()
        
        # Test 3: Test new registration
        results["new_registration"] = await self.test_new_registration_flow()
        
        # Summary
        self.log("=" * 60)
        self.log("🔧 FIX VERIFICATION RESULTS")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        self.log("=" * 60)
        self.log("📋 FINAL ASSESSMENT:")
        
        if results.get("account_reset", False):
            self.log("✅ Target account completely reset - ready for re-registration")
        
        if results.get("password_reset_fix", False):
            self.log("✅ PASSWORD RESET BUG FIXED: Verification status preserved during password reset")
        else:
            self.log("🚨 PASSWORD RESET BUG STILL EXISTS: Fix needs additional work")
        
        if results.get("new_registration", False):
            self.log("✅ New registration flow working properly")
        
        all_passed = all(results.values())
        
        if all_passed:
            self.log("🎉 ALL TESTS PASSED: Password reset verification issue is FIXED")
        else:
            self.log("❌ Some tests failed - additional work needed")
        
        return results

async def main():
    """Main test execution"""
    tester = PasswordResetFixTester()
    
    try:
        results = await tester.run_comprehensive_fix_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())