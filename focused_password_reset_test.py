#!/usr/bin/env python3
"""
Focused Password Reset Verification Bug Test
Testing if password reset preserves verification status
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

class PasswordResetVerificationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
        if client:
            client.close()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_password_reset_bug(self):
        """Test the password reset bug with demo user"""
        self.log("=== TESTING PASSWORD RESET VERIFICATION BUG WITH DEMO USER ===")
        
        try:
            demo_email = "demo@test.com"
            original_password = "password123"
            temp_password = "temppassword456"
            
            # Step 1: Check demo user exists and is verified
            demo_user = await db.users.find_one({"email": demo_email})
            if not demo_user:
                self.log("❌ Demo user not found")
                return False
            
            self.log(f"✅ Demo user found: {demo_user['email']}")
            self.log(f"   Is verified: {demo_user.get('is_verified', False)}")
            self.log(f"   Verified at: {demo_user.get('verified_at', 'N/A')}")
            
            if not demo_user.get('is_verified', False):
                self.log("❌ Demo user is not verified - cannot test password reset bug")
                return False
            
            # Step 2: Test login before password reset
            self.log("Testing login BEFORE password reset...")
            login_data = {
                "email": demo_email,
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
            
            # Step 3: Initiate password reset
            self.log("Initiating password reset...")
            reset_request_data = {
                "email": demo_email
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request_data)
            if response.status_code != 200:
                self.log(f"❌ Password reset request failed: {response.text}")
                return False
            
            self.log("✅ Password reset request sent")
            
            # Step 4: Get reset code and reset password
            reset_codes = await db.password_reset_codes.find({"email": demo_email, "is_used": False}).sort("created_at", -1).to_list(10)
            if not reset_codes:
                self.log("❌ No password reset code found")
                return False
            
            reset_code = reset_codes[0]['code']
            self.log(f"✅ Found reset code: {reset_code}")
            
            # Check verification status BEFORE password reset
            user_before_reset = await db.users.find_one({"email": demo_email})
            is_verified_before = user_before_reset.get('is_verified', False)
            verified_at_before = user_before_reset.get('verified_at')
            
            self.log(f"BEFORE password reset:")
            self.log(f"   is_verified: {is_verified_before}")
            self.log(f"   verified_at: {verified_at_before}")
            
            # Execute password reset
            reset_data = {
                "email": demo_email,
                "reset_code": reset_code,
                "new_password": temp_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
            if response.status_code != 200:
                self.log(f"❌ Password reset failed: {response.text}")
                return False
            
            self.log("✅ Password reset completed")
            
            # Step 5: Check verification status AFTER password reset
            user_after_reset = await db.users.find_one({"email": demo_email})
            is_verified_after = user_after_reset.get('is_verified', False)
            verified_at_after = user_after_reset.get('verified_at')
            
            self.log(f"AFTER password reset:")
            self.log(f"   is_verified: {is_verified_after}")
            self.log(f"   verified_at: {verified_at_after}")
            
            # Check if verification status was preserved
            if is_verified_before and not is_verified_after:
                self.log("🚨 BUG DETECTED: Verification status was LOST during password reset!")
                bug_detected = True
            elif is_verified_before and is_verified_after:
                self.log("✅ Verification status preserved during password reset")
                bug_detected = False
            else:
                self.log("⚠️ Unexpected verification status change")
                bug_detected = True
            
            # Step 6: Test login after password reset
            self.log("Testing login AFTER password reset...")
            login_data_new = {
                "email": demo_email,
                "password": temp_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data_new)
            if response.status_code == 200:
                login_result = response.json()
                status_after = login_result.get('status', 'unknown')
                self.log(f"✅ Login after reset - Status: {status_after}")
                
                # This is the critical test
                if status_after == 'unverified':
                    self.log("🚨 BUG CONFIRMED: User is being asked to verify after password reset!")
                    bug_detected = True
                elif status_after == 'success':
                    self.log("✅ No bug: User can login successfully after password reset")
                    if bug_detected:
                        self.log("⚠️ Inconsistency: Database shows verification lost but login works")
                else:
                    self.log(f"⚠️ Unexpected login status after reset: {status_after}")
                    bug_detected = True
            else:
                self.log(f"❌ Login after reset failed: {response.text}")
                bug_detected = True
            
            # Step 7: Restore original password
            self.log("Restoring original password...")
            
            # Get new reset code
            reset_request_data = {
                "email": demo_email
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request_data)
            if response.status_code == 200:
                reset_codes = await db.password_reset_codes.find({"email": demo_email, "is_used": False}).sort("created_at", -1).to_list(10)
                if reset_codes:
                    restore_code = reset_codes[0]['code']
                    
                    restore_data = {
                        "email": demo_email,
                        "reset_code": restore_code,
                        "new_password": original_password
                    }
                    
                    response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=restore_data)
                    if response.status_code == 200:
                        self.log("✅ Original password restored")
                        
                        # If verification was lost, restore it
                        if is_verified_before and not is_verified_after:
                            await db.users.update_one(
                                {"email": demo_email},
                                {
                                    "$set": {
                                        "is_verified": True,
                                        "verified_at": verified_at_before
                                    }
                                }
                            )
                            self.log("✅ Verification status restored")
                    else:
                        self.log(f"❌ Failed to restore original password: {response.text}")
            
            return not bug_detected
            
        except Exception as e:
            self.log(f"❌ Error testing password reset bug: {str(e)}", "ERROR")
            return False
    
    async def analyze_password_reset_code(self):
        """Analyze the password reset endpoint code"""
        self.log("=== ANALYZING PASSWORD RESET CODE ===")
        
        try:
            server_path = Path('/app/backend/server.py')
            if not server_path.exists():
                self.log("❌ server.py not found")
                return False
            
            with open(server_path, 'r') as f:
                content = f.read()
            
            # Find the password reset endpoint
            lines = content.split('\n')
            in_reset_function = False
            reset_function_lines = []
            
            for i, line in enumerate(lines):
                if 'auth/reset-password' in line or 'async def reset_password' in line:
                    in_reset_function = True
                    reset_function_lines.append((i+1, line))
                elif in_reset_function:
                    if line.strip().startswith('@') or (line.strip().startswith('async def ') and 'reset' not in line):
                        break
                    reset_function_lines.append((i+1, line))
            
            if reset_function_lines:
                self.log("Found password reset function:")
                
                # Look for verification-related code
                verification_lines = []
                update_lines = []
                
                for line_num, line in reset_function_lines:
                    if 'is_verified' in line or 'verified_at' in line:
                        verification_lines.append((line_num, line.strip()))
                    if '$set' in line or 'update_one' in line:
                        update_lines.append((line_num, line.strip()))
                
                if verification_lines:
                    self.log("Verification-related lines found:")
                    for line_num, line in verification_lines:
                        self.log(f"   Line {line_num}: {line}")
                else:
                    self.log("🚨 NO verification-related code found in password reset!")
                    self.log("   This confirms the bug - password reset doesn't preserve verification status")
                
                if update_lines:
                    self.log("Database update lines found:")
                    for line_num, line in update_lines:
                        self.log(f"   Line {line_num}: {line}")
                
                # Check if the update preserves verification status
                has_verification_preservation = any('is_verified' in line[1] for line in update_lines)
                
                if not has_verification_preservation:
                    self.log("🚨 CONFIRMED: Password reset does NOT preserve verification status")
                    self.log("   The update operation needs to include is_verified and verified_at fields")
                    return False
                else:
                    self.log("✅ Password reset appears to preserve verification status")
                    return True
            else:
                self.log("❌ Password reset function not found")
                return False
                
        except Exception as e:
            self.log(f"❌ Error analyzing code: {str(e)}", "ERROR")
            return False
    
    async def run_focused_test(self):
        """Run focused password reset verification test"""
        self.log("🔍 FOCUSED PASSWORD RESET VERIFICATION BUG TEST")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Analyze the code
        results["code_analysis"] = await self.analyze_password_reset_code()
        
        # Test 2: Test with demo user
        results["demo_user_test"] = await self.test_demo_user_password_reset_bug()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        self.log("=" * 60)
        self.log("📋 FINAL ASSESSMENT:")
        
        if not results.get("code_analysis", True):
            self.log("🚨 CODE ANALYSIS: Password reset function does NOT preserve verification status")
            self.log("   ROOT CAUSE: The password reset endpoint needs to be fixed to preserve is_verified=True")
        
        if not results.get("demo_user_test", True):
            self.log("🚨 DEMO USER TEST: Password reset causes verification status loss")
            self.log("   IMPACT: Users will be asked to verify their email again after password reset")
        
        if results.get("code_analysis", True) and results.get("demo_user_test", True):
            self.log("✅ NO BUG DETECTED: Password reset preserves verification status correctly")
        else:
            self.log("🚨 BUG CONFIRMED: Password reset verification issue exists and needs to be fixed")
        
        return results

async def main():
    """Main test execution"""
    tester = PasswordResetVerificationTester()
    
    try:
        results = await tester.run_focused_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())