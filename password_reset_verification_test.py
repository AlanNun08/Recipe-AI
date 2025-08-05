#!/usr/bin/env python3
"""
Password Reset Verification Issue Testing Script
Testing the specific bug where users lose verification status after password reset

SPECIFIC TEST SCENARIO:
1. Check if demo user (demo@test.com/password123) currently exists and is verified
2. Test the password reset flow: 
   - Request password reset for demo@test.com
   - Get the reset code from database 
   - Use reset code to change password 
   - Check if user's is_verified status remains true after password reset
3. Test login with new password and check if verification status is maintained
4. If verification is lost, identify exactly where in the password reset flow this happens
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import random
import string
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

# Get backend URL from frontend env
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)
BACKEND_URL = 'http://localhost:8001'

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Test user credentials
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"
NEW_PASSWORD = "newpassword456"

class PasswordResetVerificationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.db_client = None
        self.db = None
        self.demo_user = None
        self.reset_code = None
        
    async def setup_database(self):
        """Setup database connection"""
        try:
            self.db_client = AsyncIOMotorClient(MONGO_URL)
            self.db = self.db_client[DB_NAME]
            self.log("✅ Database connection established")
            return True
        except Exception as e:
            self.log(f"❌ Database connection failed: {str(e)}", "ERROR")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()
        if self.db_client:
            self.db_client.close()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_1_check_demo_user_exists(self):
        """Test 1: Check if demo user exists and is verified"""
        self.log("=== TEST 1: Checking Demo User Status ===")
        
        try:
            # Check in database directly
            user = await self.db.users.find_one({"email": DEMO_EMAIL})
            
            if not user:
                self.log(f"❌ Demo user {DEMO_EMAIL} not found in database")
                return False
            
            self.demo_user = user
            user_id = user.get('id')
            is_verified = user.get('is_verified', False)
            created_at = user.get('created_at')
            verified_at = user.get('verified_at')
            
            self.log(f"✅ Demo user found in database")
            self.log(f"   User ID: {user_id}")
            self.log(f"   Email: {user.get('email')}")
            self.log(f"   Is Verified: {is_verified}")
            self.log(f"   Created At: {created_at}")
            self.log(f"   Verified At: {verified_at}")
            
            # Test login with current password
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                login_result = response.json()
                self.log(f"✅ Demo user can login with current password")
                self.log(f"   Login Status: {login_result.get('status', 'success')}")
                self.log(f"   User ID from login: {login_result.get('user_id')}")
                
                if not is_verified:
                    self.log("⚠️  WARNING: Demo user exists but is not verified")
                    return False
                
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking demo user: {str(e)}", "ERROR")
            return False
    
    async def test_2_request_password_reset(self):
        """Test 2: Request password reset for demo user"""
        self.log("=== TEST 2: Requesting Password Reset ===")
        
        try:
            reset_data = {
                "email": DEMO_EMAIL
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Password reset requested successfully")
                self.log(f"   Message: {result.get('message')}")
                return True
            else:
                self.log(f"❌ Password reset request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error requesting password reset: {str(e)}", "ERROR")
            return False
    
    async def test_3_get_reset_code_from_database(self):
        """Test 3: Get the reset code from database"""
        self.log("=== TEST 3: Getting Reset Code from Database ===")
        
        try:
            # Find the most recent reset code for the demo user
            reset_codes = await self.db.password_reset_codes.find(
                {"email": DEMO_EMAIL}
            ).sort("created_at", -1).to_list(5)
            
            if not reset_codes:
                self.log(f"❌ No reset codes found for {DEMO_EMAIL}")
                return False
            
            # Get the most recent unused code
            for code_doc in reset_codes:
                if not code_doc.get('is_used', False):
                    self.reset_code = code_doc.get('code')
                    expires_at = code_doc.get('expires_at')
                    created_at = code_doc.get('created_at')
                    
                    self.log(f"✅ Reset code found in database")
                    self.log(f"   Code: {self.reset_code}")
                    self.log(f"   Created At: {created_at}")
                    self.log(f"   Expires At: {expires_at}")
                    self.log(f"   Is Used: {code_doc.get('is_used', False)}")
                    
                    return True
            
            self.log(f"❌ No unused reset codes found for {DEMO_EMAIL}")
            return False
                
        except Exception as e:
            self.log(f"❌ Error getting reset code: {str(e)}", "ERROR")
            return False
    
    async def test_4_check_user_verification_before_reset(self):
        """Test 4: Check user verification status before password reset"""
        self.log("=== TEST 4: Checking User Verification Before Reset ===")
        
        try:
            user = await self.db.users.find_one({"email": DEMO_EMAIL})
            
            if not user:
                self.log(f"❌ User not found")
                return False
            
            is_verified_before = user.get('is_verified', False)
            verified_at = user.get('verified_at')
            
            self.log(f"✅ User verification status BEFORE password reset:")
            self.log(f"   Is Verified: {is_verified_before}")
            self.log(f"   Verified At: {verified_at}")
            
            return is_verified_before
                
        except Exception as e:
            self.log(f"❌ Error checking verification before reset: {str(e)}", "ERROR")
            return False
    
    async def test_5_reset_password_with_code(self):
        """Test 5: Reset password using the code"""
        self.log("=== TEST 5: Resetting Password with Code ===")
        
        if not self.reset_code:
            self.log("❌ No reset code available")
            return False
        
        try:
            reset_data = {
                "email": DEMO_EMAIL,
                "reset_code": self.reset_code,
                "new_password": NEW_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Password reset completed successfully")
                self.log(f"   Message: {result.get('message')}")
                return True
            else:
                self.log(f"❌ Password reset failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error resetting password: {str(e)}", "ERROR")
            return False
    
    async def test_6_check_user_verification_after_reset(self):
        """Test 6: Check user verification status after password reset - CRITICAL TEST"""
        self.log("=== TEST 6: Checking User Verification After Reset (CRITICAL) ===")
        
        try:
            user = await self.db.users.find_one({"email": DEMO_EMAIL})
            
            if not user:
                self.log(f"❌ User not found")
                return False
            
            is_verified_after = user.get('is_verified', False)
            verified_at = user.get('verified_at')
            
            self.log(f"✅ User verification status AFTER password reset:")
            self.log(f"   Is Verified: {is_verified_after}")
            self.log(f"   Verified At: {verified_at}")
            
            if is_verified_after:
                self.log("🎉 VERIFICATION STATUS MAINTAINED - No bug detected")
                return True
            else:
                self.log("🚨 BUG CONFIRMED: User lost verification status after password reset!")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking verification after reset: {str(e)}", "ERROR")
            return False
    
    async def test_7_login_with_new_password(self):
        """Test 7: Test login with new password"""
        self.log("=== TEST 7: Testing Login with New Password ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": NEW_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                login_status = result.get('status', 'success')
                
                self.log(f"✅ Login with new password successful")
                self.log(f"   Status: {login_status}")
                self.log(f"   User ID: {result.get('user_id')}")
                
                if login_status == 'unverified':
                    self.log("🚨 BUG CONFIRMED: User is being asked to verify again after password reset!")
                    return False
                elif login_status == 'success':
                    self.log("🎉 Login successful - verification status maintained")
                    return True
                else:
                    self.log(f"⚠️  Unexpected login status: {login_status}")
                    return False
                    
            else:
                self.log(f"❌ Login with new password failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing login with new password: {str(e)}", "ERROR")
            return False
    
    async def test_8_restore_original_password(self):
        """Test 8: Restore original password for future tests"""
        self.log("=== TEST 8: Restoring Original Password ===")
        
        try:
            # Request another password reset
            reset_data = {"email": DEMO_EMAIL}
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_data)
            
            if response.status_code != 200:
                self.log(f"❌ Failed to request password reset for restoration")
                return False
            
            # Get new reset code
            await asyncio.sleep(1)  # Wait a moment for code to be generated
            reset_codes = await self.db.password_reset_codes.find(
                {"email": DEMO_EMAIL}
            ).sort("created_at", -1).to_list(5)
            
            new_reset_code = None
            for code_doc in reset_codes:
                if not code_doc.get('is_used', False):
                    new_reset_code = code_doc.get('code')
                    break
            
            if not new_reset_code:
                self.log(f"❌ Could not get new reset code for restoration")
                return False
            
            # Reset back to original password
            restore_data = {
                "email": DEMO_EMAIL,
                "reset_code": new_reset_code,
                "new_password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=restore_data)
            
            if response.status_code == 200:
                self.log(f"✅ Original password restored successfully")
                return True
            else:
                self.log(f"❌ Failed to restore original password: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error restoring original password: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all password reset verification tests"""
        self.log("🔍 STARTING PASSWORD RESET VERIFICATION BUG TESTING")
        self.log("=" * 70)
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log(f"Demo User: {DEMO_EMAIL}")
        self.log("=" * 70)
        
        # Setup database connection
        if not await self.setup_database():
            return {"error": "Database connection failed"}
        
        test_results = {}
        
        # Test 1: Check demo user exists and is verified
        test_results["demo_user_exists"] = await self.test_1_check_demo_user_exists()
        
        if not test_results["demo_user_exists"]:
            self.log("❌ Cannot proceed - demo user not found or not verified")
            return test_results
        
        # Test 2: Request password reset
        test_results["password_reset_requested"] = await self.test_2_request_password_reset()
        
        if not test_results["password_reset_requested"]:
            self.log("❌ Cannot proceed - password reset request failed")
            return test_results
        
        # Test 3: Get reset code from database
        test_results["reset_code_retrieved"] = await self.test_3_get_reset_code_from_database()
        
        if not test_results["reset_code_retrieved"]:
            self.log("❌ Cannot proceed - reset code not found")
            return test_results
        
        # Test 4: Check verification before reset
        test_results["verified_before_reset"] = await self.test_4_check_user_verification_before_reset()
        
        # Test 5: Reset password with code
        test_results["password_reset_completed"] = await self.test_5_reset_password_with_code()
        
        if not test_results["password_reset_completed"]:
            self.log("❌ Cannot proceed - password reset failed")
            return test_results
        
        # Test 6: Check verification after reset (CRITICAL)
        test_results["verified_after_reset"] = await self.test_6_check_user_verification_after_reset()
        
        # Test 7: Login with new password
        test_results["login_with_new_password"] = await self.test_7_login_with_new_password()
        
        # Test 8: Restore original password
        test_results["original_password_restored"] = await self.test_8_restore_original_password()
        
        # Analysis and Summary
        self.log("=" * 70)
        self.log("🔍 TEST RESULTS ANALYSIS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Bug detection logic
        self.log("=" * 70)
        self.log("🐛 BUG DETECTION ANALYSIS")
        self.log("=" * 70)
        
        bug_detected = False
        bug_location = None
        
        if test_results.get("verified_before_reset") and not test_results.get("verified_after_reset"):
            bug_detected = True
            bug_location = "Password reset process removes is_verified flag from user record"
            self.log("🚨 BUG CONFIRMED: User loses verification status during password reset")
            self.log(f"   Location: {bug_location}")
        
        elif test_results.get("verified_after_reset") and not test_results.get("login_with_new_password"):
            bug_detected = True
            bug_location = "Login process after password reset returns 'unverified' status"
            self.log("🚨 BUG CONFIRMED: Login returns unverified status after password reset")
            self.log(f"   Location: {bug_location}")
        
        elif test_results.get("verified_before_reset") and test_results.get("verified_after_reset") and test_results.get("login_with_new_password"):
            self.log("🎉 NO BUG DETECTED: Verification status maintained throughout password reset flow")
        
        else:
            self.log("⚠️  INCONCLUSIVE: Could not complete full test flow to determine bug status")
        
        # Final summary
        self.log("=" * 70)
        self.log("📋 FINAL SUMMARY")
        self.log("=" * 70)
        
        if bug_detected:
            self.log("🚨 PASSWORD RESET VERIFICATION BUG CONFIRMED")
            self.log(f"   Root Cause: {bug_location}")
            self.log("   Impact: Users lose verification status after password reset")
            self.log("   Fix Required: Ensure is_verified flag is preserved during password reset")
        else:
            self.log("✅ PASSWORD RESET VERIFICATION FLOW WORKING CORRECTLY")
            self.log("   No bug detected in the password reset verification process")
        
        test_results["bug_detected"] = bug_detected
        test_results["bug_location"] = bug_location
        
        return test_results

async def main():
    """Main test execution"""
    tester = PasswordResetVerificationTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())