#!/usr/bin/env python3
"""
Verification Issue Fix Testing Script
Testing user verification status maintenance and login flow
Focus: Ensuring once a user is verified, they stay verified
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
import time

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path

# Load backend environment
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

# Load frontend environment for backend URL
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)

# Get backend URL from frontend environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://buildyoursmartcart.com/api')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = BACKEND_URL.rstrip('/') + '/api'

# Demo user credentials from test_result.md
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class VerificationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = None
        self.test_user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_verification_status(self):
        """Test 1: Check Demo User Verification Status in Database"""
        self.log("=== TEST 1: Demo User Verification Status ===")
        
        try:
            # First, try to login with demo user to get user ID
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            self.log(f"Demo login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Demo login response: {result}")
                
                if result.get("status") == "success":
                    self.demo_user_id = result.get("user_id")
                    self.log(f"✅ Demo user exists and is verified")
                    self.log(f"Demo user ID: {self.demo_user_id}")
                    self.log(f"User name: {result.get('first_name', 'Unknown')}")
                    return True
                elif result.get("status") == "unverified":
                    self.log(f"❌ Demo user exists but is NOT verified")
                    self.log(f"Message: {result.get('message')}")
                    return False
                else:
                    self.log(f"❌ Unexpected login status: {result.get('status')}")
                    return False
            else:
                self.log(f"❌ Demo user login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking demo user: {str(e)}", "ERROR")
            return False
    
    async def test_demo_user_login_flow(self):
        """Test 2: Test Login Flow with Demo User"""
        self.log("=== TEST 2: Demo User Login Flow ===")
        
        try:
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                self.log(f"Login status: {status}")
                self.log(f"Full response: {result}")
                
                if status == "success":
                    self.log("✅ Login returns 'success' status - verification working correctly")
                    return True
                elif status == "unverified":
                    self.log("❌ Login returns 'unverified' status - verification issue detected")
                    return False
                else:
                    self.log(f"❌ Unexpected status: {status}")
                    return False
            else:
                self.log(f"❌ Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing login flow: {str(e)}", "ERROR")
            return False
    
    async def create_test_user_for_verification(self):
        """Create a test user to test verification endpoint"""
        self.log("=== Creating Test User for Verification Testing ===")
        
        try:
            # Generate unique test user
            timestamp = int(time.time())
            test_email = f"verification_test_{timestamp}@example.com"
            test_password = "testpass123"
            
            user_data = {
                "first_name": "Verification",
                "last_name": "Test",
                "email": test_email,
                "password": test_password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            self.log(f"Registration response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.test_user_id = result.get("user_id")
                self.log(f"✅ Test user created: {test_email}")
                self.log(f"Test user ID: {self.test_user_id}")
                return test_email, test_password
            else:
                self.log(f"❌ Test user registration failed: {response.text}")
                return None, None
                
        except Exception as e:
            self.log(f"❌ Error creating test user: {str(e)}", "ERROR")
            return None, None
    
    async def test_verification_endpoint(self):
        """Test 3: Test Verification Endpoint"""
        self.log("=== TEST 3: Verification Endpoint Testing ===")
        
        try:
            # Create test user
            test_email, test_password = await self.create_test_user_for_verification()
            if not test_email:
                self.log("❌ Could not create test user for verification testing")
                return False
            
            # Try to get verification code (this might require database access)
            # For now, let's test with a dummy code to see the endpoint behavior
            verify_data = {
                "email": test_email,
                "code": "123456"  # Dummy code
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
            self.log(f"Verification response status: {response.status_code}")
            self.log(f"Verification response: {response.text}")
            
            if response.status_code == 400:
                result = response.json()
                if "Invalid or expired verification code" in result.get("detail", ""):
                    self.log("✅ Verification endpoint working - properly rejects invalid codes")
                    
                    # Now let's try to get the actual verification code
                    # We'll need to access the database directly for this
                    try:
                        # Import database connection
                        sys.path.append('/app/backend')
                        from motor.motor_asyncio import AsyncIOMotorClient
                        
                        mongo_url = os.environ.get('MONGO_URL')
                        if mongo_url:
                            client = AsyncIOMotorClient(mongo_url)
                            db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
                            
                            # Get verification code from database
                            code_doc = await db.verification_codes.find_one(
                                {"email": test_email, "is_used": False},
                                sort=[("created_at", -1)]
                            )
                            
                            if code_doc:
                                actual_code = code_doc["code"]
                                self.log(f"Found verification code: {actual_code}")
                                
                                # Test with actual code
                                verify_data["code"] = actual_code
                                response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                                
                                if response.status_code == 200:
                                    self.log("✅ Verification endpoint working - successfully verifies with correct code")
                                    
                                    # Test login after verification
                                    login_data = {
                                        "email": test_email,
                                        "password": test_password
                                    }
                                    
                                    login_response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                                    if login_response.status_code == 200:
                                        login_result = login_response.json()
                                        if login_result.get("status") == "success":
                                            self.log("✅ User can login successfully after verification")
                                            return True
                                        else:
                                            self.log(f"❌ Login after verification failed: {login_result}")
                                            return False
                                else:
                                    self.log(f"❌ Verification with correct code failed: {response.text}")
                                    return False
                            else:
                                self.log("❌ Could not find verification code in database")
                                return False
                        else:
                            self.log("❌ No database connection available")
                            return False
                            
                    except Exception as db_e:
                        self.log(f"❌ Database access error: {str(db_e)}")
                        return False
                else:
                    self.log(f"❌ Unexpected verification error: {result}")
                    return False
            else:
                self.log(f"❌ Unexpected verification response: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing verification endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_database_verification_check(self):
        """Test 4: Direct Database Verification Check"""
        self.log("=== TEST 4: Database Verification Check ===")
        
        try:
            # Import database connection
            sys.path.append('/app/backend')
            from motor.motor_asyncio import AsyncIOMotorClient
            
            mongo_url = os.environ.get('MONGO_URL')
            if not mongo_url:
                self.log("❌ No database connection available")
                return False
            
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
            
            # Check demo user in database
            demo_user = await db.users.find_one({"email": DEMO_USER_EMAIL})
            
            if demo_user:
                is_verified = demo_user.get("is_verified", False)
                verified_at = demo_user.get("verified_at")
                
                self.log(f"Demo user found in database:")
                self.log(f"  Email: {demo_user.get('email')}")
                self.log(f"  ID: {demo_user.get('id')}")
                self.log(f"  is_verified: {is_verified}")
                self.log(f"  verified_at: {verified_at}")
                self.log(f"  created_at: {demo_user.get('created_at')}")
                
                if is_verified:
                    self.log("✅ Demo user is marked as verified in database")
                    return True
                else:
                    self.log("❌ Demo user is NOT marked as verified in database")
                    return False
            else:
                self.log("❌ Demo user not found in database")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking database: {str(e)}", "ERROR")
            return False
    
    async def test_password_reset_verification_preservation(self):
        """Test 5: Password Reset Verification Preservation"""
        self.log("=== TEST 5: Password Reset Verification Preservation ===")
        
        try:
            if not self.demo_user_id:
                self.log("❌ Demo user ID not available for password reset test")
                return False
            
            # Step 1: Verify demo user is currently verified
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            if response.status_code != 200 or response.json().get("status") != "success":
                self.log("❌ Demo user is not currently verified - cannot test password reset")
                return False
            
            self.log("✅ Demo user is verified before password reset")
            
            # Step 2: Request password reset
            reset_request = {
                "email": DEMO_USER_EMAIL
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request)
            self.log(f"Password reset request status: {response.status_code}")
            
            if response.status_code == 200:
                self.log("✅ Password reset request successful")
                
                # Step 3: Get reset code from database
                try:
                    sys.path.append('/app/backend')
                    from motor.motor_asyncio import AsyncIOMotorClient
                    
                    mongo_url = os.environ.get('MONGO_URL')
                    client = AsyncIOMotorClient(mongo_url)
                    db = client[os.environ.get('DB_NAME', 'buildyoursmartcart_development')]
                    
                    # Get reset code
                    reset_doc = await db.password_reset_codes.find_one(
                        {"email": DEMO_USER_EMAIL, "is_used": False},
                        sort=[("created_at", -1)]
                    )
                    
                    if reset_doc:
                        reset_code = reset_doc["code"]
                        self.log(f"Found reset code: {reset_code}")
                        
                        # Step 4: Reset password
                        new_password = "newpassword123"
                        reset_data = {
                            "email": DEMO_USER_EMAIL,
                            "reset_code": reset_code,
                            "new_password": new_password
                        }
                        
                        response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
                        self.log(f"Password reset status: {response.status_code}")
                        
                        if response.status_code == 200:
                            self.log("✅ Password reset successful")
                            
                            # Step 5: Test login with new password
                            login_data = {
                                "email": DEMO_USER_EMAIL,
                                "password": new_password
                            }
                            
                            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("status") == "success":
                                    self.log("✅ Login successful with new password - verification status preserved")
                                    
                                    # Step 6: Restore original password
                                    # Request another reset
                                    response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request)
                                    if response.status_code == 200:
                                        # Get new reset code
                                        reset_doc = await db.password_reset_codes.find_one(
                                            {"email": DEMO_USER_EMAIL, "is_used": False},
                                            sort=[("created_at", -1)]
                                        )
                                        
                                        if reset_doc:
                                            reset_code = reset_doc["code"]
                                            restore_data = {
                                                "email": DEMO_USER_EMAIL,
                                                "reset_code": reset_code,
                                                "new_password": DEMO_USER_PASSWORD
                                            }
                                            
                                            await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=restore_data)
                                            self.log("✅ Original password restored")
                                    
                                    return True
                                elif result.get("status") == "unverified":
                                    self.log("❌ VERIFICATION BUG DETECTED: User lost verification status after password reset")
                                    return False
                                else:
                                    self.log(f"❌ Unexpected login status after password reset: {result.get('status')}")
                                    return False
                            else:
                                self.log(f"❌ Login failed after password reset: {response.text}")
                                return False
                        else:
                            self.log(f"❌ Password reset failed: {response.text}")
                            return False
                    else:
                        self.log("❌ Could not find reset code in database")
                        return False
                        
                except Exception as db_e:
                    self.log(f"❌ Database access error during password reset test: {str(db_e)}")
                    return False
            else:
                self.log(f"❌ Password reset request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing password reset verification preservation: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_verification_test(self):
        """Run all verification tests"""
        self.log("🔍 Starting Comprehensive Verification Issue Fix Testing")
        self.log("=" * 70)
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log(f"Demo User: {DEMO_USER_EMAIL}")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Demo User Verification Status
        test_results["demo_user_status"] = await self.test_demo_user_verification_status()
        
        # Test 2: Demo User Login Flow
        test_results["demo_login_flow"] = await self.test_demo_user_login_flow()
        
        # Test 3: Verification Endpoint
        test_results["verification_endpoint"] = await self.test_verification_endpoint()
        
        # Test 4: Database Verification Check
        test_results["database_check"] = await self.test_database_verification_check()
        
        # Test 5: Password Reset Verification Preservation
        test_results["password_reset_preservation"] = await self.test_password_reset_verification_preservation()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 VERIFICATION TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = ["demo_user_status", "demo_login_flow", "database_check"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL VERIFICATION TESTS PASSED")
            self.log("✅ User verification status is properly maintained")
            self.log("✅ Demo user is verified and can login successfully")
            self.log("✅ Database state is correct")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 VERIFICATION ISSUES IDENTIFIED:")
            
            if not test_results.get("demo_user_status"):
                self.log("  - Demo user verification status issue")
            if not test_results.get("demo_login_flow"):
                self.log("  - Login flow returning 'unverified' instead of 'success'")
            if not test_results.get("database_check"):
                self.log("  - Database verification status not properly stored")
        
        # Additional findings
        if test_results.get("password_reset_preservation"):
            self.log("✅ Password reset preserves verification status correctly")
        elif test_results.get("password_reset_preservation") is False:
            self.log("❌ PASSWORD RESET BUG: Verification status lost during password reset")
        
        return test_results

async def main():
    """Main test execution"""
    tester = VerificationTester()
    
    try:
        results = await tester.run_comprehensive_verification_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())