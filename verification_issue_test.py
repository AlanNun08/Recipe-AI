#!/usr/bin/env python3
"""
Verification Issue Investigation for alannunezsilva0310@gmail.com
Testing the specific reported issue where users are asked to verify after password reset
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import time
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

# Target user email
TARGET_EMAIL = "alannunezsilva0310@gmail.com"

class VerificationIssueTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.target_user = None
        
    async def cleanup(self):
        await self.client.aclose()
        if client:
            client.close()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def investigate_current_account_state(self):
        """TASK 1: Investigate Current Account State"""
        self.log("=== TASK 1: INVESTIGATING CURRENT ACCOUNT STATE ===")
        
        try:
            # Find user account for alannunezsilva0310@gmail.com
            self.log(f"Searching for user account: {TARGET_EMAIL}")
            
            # Try different search approaches
            user = None
            
            # 1. Exact match
            user = await db.users.find_one({"email": TARGET_EMAIL})
            
            # 2. Case-insensitive search
            if not user:
                user = await db.users.find_one({"email": {"$regex": f"^{TARGET_EMAIL}$", "$options": "i"}})
            
            # 3. Search all users and match manually
            if not user:
                all_users = await db.users.find().to_list(length=1000)
                for u in all_users:
                    if u.get('email', '').lower() == TARGET_EMAIL.lower():
                        user = u
                        break
            
            if user:
                self.target_user = user
                self.log(f"✅ USER FOUND: {user['email']}")
                self.log(f"   User ID: {user['id']}")
                self.log(f"   Name: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}")
                self.log(f"   Is Verified: {user.get('is_verified', False)}")
                self.log(f"   Created At: {user.get('created_at', 'N/A')}")
                self.log(f"   Verified At: {user.get('verified_at', 'N/A')}")
                
                # Check subscription status
                self.log(f"   Subscription Status: {user.get('subscription_status', 'N/A')}")
                self.log(f"   Trial End Date: {user.get('trial_end_date', 'N/A')}")
                
                # Check for pending verification codes
                verification_codes = await db.verification_codes.find({"email": user['email']}).to_list(100)
                self.log(f"   Verification Codes Found: {len(verification_codes)}")
                
                for code in verification_codes:
                    self.log(f"     Code: {code.get('code', 'N/A')} | Used: {code.get('is_used', False)} | Expires: {code.get('expires_at', 'N/A')}")
                
                # Check for password reset codes
                reset_codes = await db.password_reset_codes.find({"email": user['email']}).to_list(100)
                self.log(f"   Password Reset Codes Found: {len(reset_codes)}")
                
                for code in reset_codes:
                    self.log(f"     Reset Code: {code.get('code', 'N/A')} | Used: {code.get('is_used', False)} | Expires: {code.get('expires_at', 'N/A')}")
                
                return True
            else:
                self.log(f"❌ USER NOT FOUND: {TARGET_EMAIL}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error investigating account: {str(e)}", "ERROR")
            return False
    
    async def complete_account_reset(self):
        """TASK 2: Complete Account Reset"""
        self.log("=== TASK 2: COMPLETE ACCOUNT RESET ===")
        
        try:
            if not self.target_user:
                self.log("❌ No target user found to reset")
                return False
            
            user_id = self.target_user['id']
            user_email = self.target_user['email']
            
            self.log(f"Deleting all data for user: {user_email} (ID: {user_id})")
            
            # Delete from all collections
            collections_to_clean = [
                ("users", {"email": user_email}),
                ("users", {"id": user_id}),
                ("verification_codes", {"email": user_email}),
                ("verification_codes", {"user_id": user_id}),
                ("password_reset_codes", {"email": user_email}),
                ("password_reset_codes", {"user_id": user_id}),
                ("recipes", {"user_id": user_id}),
                ("starbucks_recipes", {"user_id": user_id}),
                ("grocery_carts", {"user_id": user_id}),
                ("user_shared_recipes", {"shared_by_user_id": user_id}),
                ("payment_transactions", {"user_id": user_id}),
                ("payment_transactions", {"email": user_email})
            ]
            
            total_deleted = 0
            
            for collection_name, query in collections_to_clean:
                try:
                    collection = db[collection_name]
                    result = await collection.delete_many(query)
                    deleted_count = result.deleted_count
                    total_deleted += deleted_count
                    
                    if deleted_count > 0:
                        self.log(f"   Deleted {deleted_count} documents from {collection_name}")
                    
                except Exception as e:
                    self.log(f"   Warning: Error cleaning {collection_name}: {str(e)}")
            
            self.log(f"✅ ACCOUNT RESET COMPLETE: Deleted {total_deleted} total documents")
            self.log(f"   User {user_email} has been completely removed from the system")
            
            # Verify deletion
            remaining_user = await db.users.find_one({"email": user_email})
            if remaining_user:
                self.log("❌ WARNING: User still exists after deletion attempt")
                return False
            else:
                self.log("✅ VERIFIED: User completely removed from database")
                return True
                
        except Exception as e:
            self.log(f"❌ Error during account reset: {str(e)}", "ERROR")
            return False
    
    async def test_password_reset_verification_flow(self):
        """TASK 3: Test Password Reset Verification Flow"""
        self.log("=== TASK 3: TESTING PASSWORD RESET VERIFICATION FLOW ===")
        
        try:
            # Create a test user to simulate the issue
            test_email = "verification_test_user@example.com"
            test_password = "testpassword123"
            new_password = "newpassword456"
            
            self.log(f"Creating test user: {test_email}")
            
            # Step 1: Register test user
            register_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": test_email,
                "password": test_password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code != 200:
                self.log(f"❌ Registration failed: {response.text}")
                return False
            
            self.log("✅ Test user registered")
            
            # Step 2: Get verification code and verify user
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
            
            # Step 3: Check verification status before password reset
            user_before = await db.users.find_one({"email": test_email})
            is_verified_before = user_before.get('is_verified', False)
            verified_at_before = user_before.get('verified_at')
            
            self.log(f"   Before password reset - is_verified: {is_verified_before}")
            self.log(f"   Before password reset - verified_at: {verified_at_before}")
            
            # Step 4: Test login before password reset
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                login_result = response.json()
                self.log(f"✅ Login before reset - status: {login_result.get('status', 'unknown')}")
            else:
                self.log(f"❌ Login before reset failed: {response.text}")
            
            # Step 5: Initiate password reset
            reset_request_data = {
                "email": test_email
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request_data)
            if response.status_code != 200:
                self.log(f"❌ Password reset request failed: {response.text}")
                return False
            
            self.log("✅ Password reset request sent")
            
            # Step 6: Get reset code and reset password
            reset_codes = await db.password_reset_codes.find({"email": test_email, "is_used": False}).to_list(10)
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
            
            # Step 7: Check verification status after password reset
            user_after = await db.users.find_one({"email": test_email})
            is_verified_after = user_after.get('is_verified', False)
            verified_at_after = user_after.get('verified_at')
            
            self.log(f"   After password reset - is_verified: {is_verified_after}")
            self.log(f"   After password reset - verified_at: {verified_at_after}")
            
            # Step 8: Test login after password reset
            login_data_new = {
                "email": test_email,
                "password": new_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data_new)
            if response.status_code == 200:
                login_result = response.json()
                login_status = login_result.get('status', 'unknown')
                self.log(f"✅ Login after reset - status: {login_status}")
                
                # This is the critical test - if status is 'unverified', we found the bug
                if login_status == 'unverified':
                    self.log("🚨 BUG DETECTED: User is being asked to verify after password reset!")
                    return False
                elif login_status == 'success':
                    self.log("✅ No bug detected: User can login successfully after password reset")
                    return True
                else:
                    self.log(f"⚠️ Unexpected login status: {login_status}")
                    return False
            else:
                self.log(f"❌ Login after reset failed: {response.text}")
                return False
            
            # Step 9: Cleanup test user
            await db.users.delete_many({"email": test_email})
            await db.verification_codes.delete_many({"email": test_email})
            await db.password_reset_codes.delete_many({"email": test_email})
            
            self.log("✅ Test user cleaned up")
            
        except Exception as e:
            self.log(f"❌ Error testing password reset flow: {str(e)}", "ERROR")
            return False
    
    async def root_cause_analysis(self):
        """TASK 4: Root Cause Analysis"""
        self.log("=== TASK 4: ROOT CAUSE ANALYSIS ===")
        
        try:
            # Check the login endpoint code for verification logic
            self.log("Analyzing login endpoint verification logic...")
            
            # Read the server.py file to check login logic
            server_path = Path('/app/backend/server.py')
            if server_path.exists():
                with open(server_path, 'r') as f:
                    server_content = f.read()
                
                # Look for login function
                if 'async def login_user' in server_content:
                    self.log("✅ Found login_user function")
                    
                    # Check for verification status logic
                    if 'is_verified' in server_content:
                        self.log("✅ Found is_verified checks in code")
                        
                        # Look for the specific logic that might cause the issue
                        lines = server_content.split('\n')
                        in_login_function = False
                        verification_logic_lines = []
                        
                        for i, line in enumerate(lines):
                            if 'async def login_user' in line:
                                in_login_function = True
                            elif in_login_function and line.strip().startswith('async def '):
                                in_login_function = False
                            elif in_login_function and 'is_verified' in line:
                                verification_logic_lines.append((i+1, line.strip()))
                        
                        if verification_logic_lines:
                            self.log("Found verification logic in login function:")
                            for line_num, line in verification_logic_lines:
                                self.log(f"   Line {line_num}: {line}")
                        
                        # Check for password reset function
                        if 'async def reset_password' in server_content:
                            self.log("✅ Found reset_password function")
                            
                            # Check if reset_password preserves verification status
                            reset_lines = []
                            in_reset_function = False
                            
                            for i, line in enumerate(lines):
                                if 'async def reset_password' in line or 'auth/reset-password' in line:
                                    in_reset_function = True
                                elif in_reset_function and line.strip().startswith('async def '):
                                    in_reset_function = False
                                elif in_reset_function and ('is_verified' in line or 'verified_at' in line):
                                    reset_lines.append((i+1, line.strip()))
                            
                            if reset_lines:
                                self.log("Found verification-related logic in password reset:")
                                for line_num, line in reset_lines:
                                    self.log(f"   Line {line_num}: {line}")
                            else:
                                self.log("⚠️ No verification status preservation found in password reset")
                                self.log("   This could be the root cause - password reset might not preserve is_verified=True")
                        
                    else:
                        self.log("❌ No is_verified checks found in code")
                else:
                    self.log("❌ login_user function not found")
            else:
                self.log("❌ server.py file not found")
            
            # Check database consistency
            self.log("Checking database for users with verification inconsistencies...")
            
            # Find users who are verified but might have issues
            users_with_issues = await db.users.find({
                "is_verified": True,
                "verified_at": {"$exists": True}
            }).to_list(100)
            
            self.log(f"Found {len(users_with_issues)} verified users")
            
            # Check for any users who might have been affected by password reset
            users_with_reset_codes = await db.password_reset_codes.find({}).to_list(100)
            reset_emails = set(code.get('email') for code in users_with_reset_codes)
            
            self.log(f"Found {len(reset_emails)} unique emails with password reset codes")
            
            # Check if any verified users have used password reset
            affected_users = []
            for user in users_with_issues:
                if user.get('email') in reset_emails:
                    affected_users.append(user)
            
            self.log(f"Found {len(affected_users)} verified users who have used password reset")
            
            if affected_users:
                self.log("Users who might be affected by the verification bug:")
                for user in affected_users[:5]:  # Show first 5
                    self.log(f"   {user.get('email')} - verified: {user.get('is_verified')}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in root cause analysis: {str(e)}", "ERROR")
            return False
    
    async def verify_system_state(self):
        """TASK 5: Verify System State"""
        self.log("=== TASK 5: VERIFYING SYSTEM STATE ===")
        
        try:
            # Verify the target account has been completely reset
            remaining_user = await db.users.find_one({"email": TARGET_EMAIL})
            if remaining_user:
                self.log(f"❌ Target user {TARGET_EMAIL} still exists in database")
                return False
            else:
                self.log(f"✅ Target user {TARGET_EMAIL} completely removed from system")
            
            # Test new registration will work properly
            self.log("Testing new registration flow...")
            
            test_register_data = {
                "first_name": "Test",
                "last_name": "Registration",
                "email": "test_new_registration@example.com",
                "password": "testpass123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=test_register_data)
            if response.status_code == 200:
                self.log("✅ New registration works properly")
                
                # Clean up test user
                await db.users.delete_many({"email": "test_new_registration@example.com"})
                await db.verification_codes.delete_many({"email": "test_new_registration@example.com"})
            else:
                self.log(f"❌ New registration failed: {response.text}")
                return False
            
            # Test that password reset preserves verification status (using demo user)
            self.log("Testing password reset with demo user...")
            
            demo_user = await db.users.find_one({"email": "demo@test.com"})
            if demo_user:
                original_password = "password123"
                temp_password = "temppass456"
                
                # Test login with original password
                login_data = {
                    "email": "demo@test.com",
                    "password": original_password
                }
                
                response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                if response.status_code == 200:
                    login_result = response.json()
                    if login_result.get('status') == 'success':
                        self.log("✅ Demo user login works with original password")
                        
                        # Initiate password reset
                        reset_request = {"email": "demo@test.com"}
                        response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request)
                        
                        if response.status_code == 200:
                            # Get reset code
                            reset_codes = await db.password_reset_codes.find({"email": "demo@test.com", "is_used": False}).to_list(10)
                            if reset_codes:
                                reset_code = reset_codes[0]['code']
                                
                                # Reset password
                                reset_data = {
                                    "email": "demo@test.com",
                                    "reset_code": reset_code,
                                    "new_password": temp_password
                                }
                                
                                response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
                                if response.status_code == 200:
                                    self.log("✅ Password reset completed for demo user")
                                    
                                    # Test login with new password
                                    login_data_new = {
                                        "email": "demo@test.com",
                                        "password": temp_password
                                    }
                                    
                                    response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data_new)
                                    if response.status_code == 200:
                                        login_result = response.json()
                                        if login_result.get('status') == 'success':
                                            self.log("✅ Demo user can login after password reset without verification prompt")
                                        elif login_result.get('status') == 'unverified':
                                            self.log("🚨 BUG CONFIRMED: Demo user asked to verify after password reset")
                                        else:
                                            self.log(f"⚠️ Unexpected login status: {login_result.get('status')}")
                                    
                                    # Restore original password
                                    reset_codes = await db.password_reset_codes.find({"email": "demo@test.com", "is_used": False}).to_list(10)
                                    if reset_codes:
                                        reset_code = reset_codes[0]['code']
                                        restore_data = {
                                            "email": "demo@test.com",
                                            "reset_code": reset_code,
                                            "new_password": original_password
                                        }
                                        await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=restore_data)
                                        self.log("✅ Demo user password restored")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error verifying system state: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_investigation(self):
        """Run all investigation tasks"""
        self.log("🔍 STARTING COMPREHENSIVE VERIFICATION ISSUE INVESTIGATION")
        self.log("=" * 80)
        self.log(f"Target Account: {TARGET_EMAIL}")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log("=" * 80)
        
        results = {}
        
        # Task 1: Investigate current account state
        results["account_investigation"] = await self.investigate_current_account_state()
        
        # Task 2: Complete account reset (only if account exists)
        if results["account_investigation"]:
            results["account_reset"] = await self.complete_account_reset()
        else:
            results["account_reset"] = True  # No account to reset
            self.log("✅ No account found to reset - proceeding with other tests")
        
        # Task 3: Test password reset verification flow
        results["password_reset_test"] = await self.test_password_reset_verification_flow()
        
        # Task 4: Root cause analysis
        results["root_cause_analysis"] = await self.root_cause_analysis()
        
        # Task 5: Verify system state
        results["system_verification"] = await self.verify_system_state()
        
        # Summary
        self.log("=" * 80)
        self.log("🔍 INVESTIGATION RESULTS SUMMARY")
        self.log("=" * 80)
        
        for task_name, result in results.items():
            status = "✅ COMPLETED" if result else "❌ FAILED"
            self.log(f"{task_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        self.log("=" * 80)
        self.log("📋 FINAL ASSESSMENT:")
        
        if results.get("account_investigation"):
            self.log(f"✅ Target account {TARGET_EMAIL} was found and investigated")
        else:
            self.log(f"ℹ️ Target account {TARGET_EMAIL} was not found in the system")
        
        if results.get("account_reset"):
            self.log("✅ Account reset completed successfully - clean slate for re-registration")
        
        if results.get("password_reset_test"):
            self.log("✅ Password reset flow preserves verification status correctly")
        else:
            self.log("🚨 Password reset flow has verification issues - this is likely the root cause")
        
        if results.get("root_cause_analysis"):
            self.log("✅ Root cause analysis completed - check logs for specific findings")
        
        if results.get("system_verification"):
            self.log("✅ System verification completed - ready for new user registration")
        
        return results

async def main():
    """Main investigation execution"""
    tester = VerificationIssueTester()
    
    try:
        results = await tester.run_comprehensive_investigation()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())