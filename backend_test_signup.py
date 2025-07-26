#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for AI Recipe + Grocery Delivery App
Focus: Test Signup and Reset Password Functionality with Email Service
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

# Add backend to path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://6b4e57e4-7e21-4efb-941c-e036b94930bd.preview.emergentagent.com/api"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "testpassword123"
TEST_USER_NAME = "Test User"

class SignupResetPasswordTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.test_results = {}
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def generate_unique_email(self):
        """Generate a unique email for testing"""
        timestamp = str(int(time.time()))
        return f"testuser{timestamp}@example.com"
    
    async def test_environment_variables(self):
        """Test: Verify email service environment variables are loaded"""
        self.log("=== Testing Email Service Environment Variables ===")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            from pathlib import Path
            
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            mailjet_api_key = os.environ.get('MAILJET_API_KEY')
            mailjet_secret_key = os.environ.get('MAILJET_SECRET_KEY')
            sender_email = os.environ.get('SENDER_EMAIL')
            
            self.log(f"MAILJET_API_KEY: {'✅ Present' if mailjet_api_key else '❌ Missing'}")
            self.log(f"MAILJET_SECRET_KEY: {'✅ Present' if mailjet_secret_key else '❌ Missing'}")
            self.log(f"SENDER_EMAIL: {'✅ Present' if sender_email else '❌ Missing'}")
            
            if mailjet_api_key:
                self.log(f"API Key: {mailjet_api_key[:8]}...")
            if sender_email:
                self.log(f"Sender Email: {sender_email}")
            
            return all([mailjet_api_key, mailjet_secret_key, sender_email])
            
        except Exception as e:
            self.log(f"❌ Error checking environment variables: {str(e)}", "ERROR")
            return False
    
    async def test_user_registration_valid(self):
        """Test: User registration with valid data"""
        self.log("=== Testing User Registration (Valid Data) ===")
        
        try:
            # Clean up any existing test data first
            await self.client.delete(f"{BACKEND_URL}/debug/cleanup-test-data")
            
            unique_email = self.generate_unique_email()
            user_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": unique_email,
                "password": TEST_USER_PASSWORD,
                "dietary_preferences": ["vegetarian"],
                "allergies": ["nuts"],
                "favorite_cuisines": ["Italian", "Mexican"]
            }
            
            self.log(f"Registering user with email: {unique_email}")
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                self.log(f"✅ User registered successfully")
                self.log(f"User ID: {self.user_id}")
                self.log(f"Email: {result.get('email')}")
                self.log(f"Message: {result.get('message')}")
                
                # Store for later tests
                self.test_email = unique_email
                return True
            else:
                self.log(f"❌ Registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in user registration test: {str(e)}", "ERROR")
            return False
    
    async def test_email_verification(self):
        """Test: Email verification with code"""
        self.log("=== Testing Email Verification ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available for verification")
            return False
        
        try:
            # Get verification code from debug endpoint
            debug_response = await self.client.get(f"{BACKEND_URL}/debug/verification-codes/{self.test_email}")
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                codes = debug_data.get("codes", [])
                
                if codes:
                    verification_code = codes[0]["code"]
                    is_expired = codes[0]["is_expired"]
                    
                    self.log(f"Found verification code: {verification_code}")
                    self.log(f"Code expired: {is_expired}")
                    
                    if is_expired:
                        self.log("⚠️ Code is expired, but continuing test")
                    
                    # Verify email with code
                    verify_data = {
                        "email": self.test_email,
                        "code": verification_code
                    }
                    
                    verify_response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                    
                    self.log(f"Verification response status: {verify_response.status_code}")
                    
                    if verify_response.status_code == 200:
                        result = verify_response.json()
                        self.log("✅ Email verified successfully")
                        self.log(f"Message: {result.get('message')}")
                        self.log(f"User verified: {result.get('user', {}).get('is_verified')}")
                        return True
                    else:
                        self.log(f"❌ Email verification failed: {verify_response.text}")
                        return False
                else:
                    self.log("❌ No verification codes found")
                    return False
            else:
                self.log(f"❌ Failed to get verification codes: {debug_response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in email verification test: {str(e)}", "ERROR")
            return False
    
    async def test_login_after_verification(self):
        """Test: Login after successful verification"""
        self.log("=== Testing Login After Verification ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available for login")
            return False
        
        try:
            login_data = {
                "email": self.test_email,
                "password": TEST_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                if status == "success":
                    self.log("✅ Login successful after verification")
                    self.log(f"User ID: {result.get('user', {}).get('id')}")
                    self.log(f"User verified: {result.get('user', {}).get('is_verified')}")
                    return True
                elif status == "unverified":
                    self.log("❌ User still shows as unverified")
                    return False
                else:
                    self.log(f"❌ Unexpected login status: {status}")
                    return False
            else:
                self.log(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in login test: {str(e)}", "ERROR")
            return False
    
    async def test_duplicate_email_prevention(self):
        """Test: Duplicate email registration prevention"""
        self.log("=== Testing Duplicate Email Prevention ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available for duplicate test")
            return False
        
        try:
            # Try to register with same email
            user_data = {
                "first_name": "Another",
                "last_name": "User",
                "email": self.test_email,
                "password": "anotherpassword123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            self.log(f"Duplicate registration response status: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                detail = result.get("detail", "")
                
                if "already registered" in detail.lower():
                    self.log("✅ Duplicate email correctly prevented")
                    self.log(f"Error message: {detail}")
                    return True
                else:
                    self.log(f"❌ Unexpected error message: {detail}")
                    return False
            else:
                self.log(f"❌ Duplicate registration should have failed with 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in duplicate email test: {str(e)}", "ERROR")
            return False
    
    async def test_password_validation(self):
        """Test: Password validation (minimum 6 characters)"""
        self.log("=== Testing Password Validation ===")
        
        try:
            # Test with short password
            unique_email = self.generate_unique_email()
            user_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": unique_email,
                "password": "12345",  # Only 5 characters
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            self.log(f"Short password response status: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                detail = result.get("detail", "")
                
                if "6 characters" in detail:
                    self.log("✅ Password validation working correctly")
                    self.log(f"Error message: {detail}")
                    return True
                else:
                    self.log(f"❌ Unexpected error message: {detail}")
                    return False
            else:
                self.log(f"❌ Short password should have failed with 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in password validation test: {str(e)}", "ERROR")
            return False
    
    async def test_forgot_password_request(self):
        """Test: Forgot password request"""
        self.log("=== Testing Forgot Password Request ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available for password reset")
            return False
        
        try:
            reset_request = {
                "email": self.test_email
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_request)
            
            self.log(f"Forgot password response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Forgot password request successful")
                self.log(f"Message: {result.get('message')}")
                self.log(f"Email: {result.get('email')}")
                return True
            else:
                self.log(f"❌ Forgot password request failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in forgot password test: {str(e)}", "ERROR")
            return False
    
    async def test_reset_code_generation(self):
        """Test: Reset code generation and storage"""
        self.log("=== Testing Reset Code Generation ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available for reset code test")
            return False
        
        try:
            # Check if reset codes were generated (using database directly)
            from motor.motor_asyncio import AsyncIOMotorClient
            from dotenv import load_dotenv
            from pathlib import Path
            
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            mongo_url = os.environ['MONGO_URL']
            db_name = os.environ.get('DB_NAME', 'test_database')
            
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            # Find reset codes for our test email
            reset_codes = []
            cursor = db.password_reset_codes.find({"email": self.test_email, "is_used": False}).sort("created_at", -1).limit(5)
            async for code in cursor:
                reset_codes.append({
                    "code": code["code"],
                    "expires_at": code["expires_at"],
                    "created_at": code["created_at"]
                })
            
            client.close()
            
            if reset_codes:
                self.log(f"✅ Found {len(reset_codes)} reset codes")
                latest_code = reset_codes[0]
                self.log(f"Latest code: {latest_code['code']}")
                self.log(f"Created at: {latest_code['created_at']}")
                
                # Store for next test
                self.reset_code = latest_code['code']
                return True
            else:
                self.log("❌ No reset codes found in database")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking reset codes: {str(e)}", "ERROR")
            return False
    
    async def test_password_reset(self):
        """Test: Password reset with valid code"""
        self.log("=== Testing Password Reset ===")
        
        if not hasattr(self, 'test_email') or not hasattr(self, 'reset_code'):
            self.log("❌ No test email or reset code available")
            return False
        
        try:
            new_password = "newpassword123"
            reset_data = {
                "email": self.test_email,
                "reset_code": self.reset_code,
                "new_password": new_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
            
            self.log(f"Password reset response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Password reset successful")
                self.log(f"Message: {result.get('message')}")
                
                # Store new password for login test
                self.new_password = new_password
                return True
            else:
                self.log(f"❌ Password reset failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in password reset test: {str(e)}", "ERROR")
            return False
    
    async def test_login_with_new_password(self):
        """Test: Login with new password after reset"""
        self.log("=== Testing Login with New Password ===")
        
        if not hasattr(self, 'test_email') or not hasattr(self, 'new_password'):
            self.log("❌ No test email or new password available")
            return False
        
        try:
            login_data = {
                "email": self.test_email,
                "password": self.new_password
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            self.log(f"Login with new password response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                
                if status == "success":
                    self.log("✅ Login successful with new password")
                    self.log(f"User ID: {result.get('user', {}).get('id')}")
                    return True
                else:
                    self.log(f"❌ Login status: {status}")
                    return False
            else:
                self.log(f"❌ Login with new password failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in login with new password test: {str(e)}", "ERROR")
            return False
    
    async def test_invalid_reset_code(self):
        """Test: Invalid/expired reset code handling"""
        self.log("=== Testing Invalid Reset Code Handling ===")
        
        if not hasattr(self, 'test_email'):
            self.log("❌ No test email available")
            return False
        
        try:
            # Test with invalid code
            reset_data = {
                "email": self.test_email,
                "reset_code": "999999",  # Invalid code
                "new_password": "anothernewpassword123"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/reset-password", json=reset_data)
            
            self.log(f"Invalid reset code response status: {response.status_code}")
            
            if response.status_code == 400:
                result = response.json()
                detail = result.get("detail", "")
                
                if "invalid" in detail.lower() or "expired" in detail.lower():
                    self.log("✅ Invalid reset code correctly rejected")
                    self.log(f"Error message: {detail}")
                    return True
                else:
                    self.log(f"❌ Unexpected error message: {detail}")
                    return False
            else:
                self.log(f"❌ Invalid reset code should have failed with 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in invalid reset code test: {str(e)}", "ERROR")
            return False
    
    async def test_email_service_configuration(self):
        """Test: Email service configuration"""
        self.log("=== Testing Email Service Configuration ===")
        
        try:
            # Import email service to test configuration
            sys.path.append('/app/backend')
            from email_service import email_service
            
            # Test if email service is properly configured
            self.log("Testing email service configuration...")
            
            # Check if email service is initialized
            if hasattr(email_service, 'initialized') and email_service.initialized:
                self.log("✅ Email service is initialized")
                
                # Test code generation
                test_code = email_service.generate_verification_code()
                if test_code and len(test_code) == 6 and test_code.isdigit():
                    self.log(f"✅ Verification code generation working: {test_code}")
                    return True
                else:
                    self.log(f"❌ Invalid verification code generated: {test_code}")
                    return False
            else:
                self.log("❌ Email service not initialized")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing email service: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all signup and reset password tests"""
        self.log("🚀 Starting Comprehensive Signup & Reset Password Tests")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Environment Variables
        test_results["env_vars"] = await self.test_environment_variables()
        
        # Test 2: Email Service Configuration
        test_results["email_config"] = await self.test_email_service_configuration()
        
        # Test 3: User Registration (Valid)
        test_results["registration"] = await self.test_user_registration_valid()
        
        # Test 4: Email Verification
        if test_results["registration"]:
            test_results["verification"] = await self.test_email_verification()
        else:
            test_results["verification"] = False
        
        # Test 5: Login After Verification
        if test_results["verification"]:
            test_results["login_after_verify"] = await self.test_login_after_verification()
        else:
            test_results["login_after_verify"] = False
        
        # Test 6: Duplicate Email Prevention
        test_results["duplicate_prevention"] = await self.test_duplicate_email_prevention()
        
        # Test 7: Password Validation
        test_results["password_validation"] = await self.test_password_validation()
        
        # Test 8: Forgot Password Request
        test_results["forgot_password"] = await self.test_forgot_password_request()
        
        # Test 9: Reset Code Generation
        if test_results["forgot_password"]:
            test_results["reset_code_gen"] = await self.test_reset_code_generation()
        else:
            test_results["reset_code_gen"] = False
        
        # Test 10: Password Reset
        if test_results["reset_code_gen"]:
            test_results["password_reset"] = await self.test_password_reset()
        else:
            test_results["password_reset"] = False
        
        # Test 11: Login with New Password
        if test_results["password_reset"]:
            test_results["login_new_password"] = await self.test_login_with_new_password()
        else:
            test_results["login_new_password"] = False
        
        # Test 12: Invalid Reset Code Handling
        test_results["invalid_reset_code"] = await self.test_invalid_reset_code()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = [
            "registration", "verification", "login_after_verify", 
            "duplicate_prevention", "password_validation", 
            "forgot_password", "password_reset", "login_new_password"
        ]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED - Signup and Reset Password flows are working")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("env_vars"):
                self.log("  - Missing or invalid email service credentials")
            if not test_results.get("registration"):
                self.log("  - User registration failing")
            if not test_results.get("verification"):
                self.log("  - Email verification failing")
            if not test_results.get("login_after_verify"):
                self.log("  - Login after verification failing")
            if not test_results.get("duplicate_prevention"):
                self.log("  - Duplicate email prevention not working")
            if not test_results.get("password_validation"):
                self.log("  - Password validation not working")
            if not test_results.get("forgot_password"):
                self.log("  - Forgot password request failing")
            if not test_results.get("password_reset"):
                self.log("  - Password reset failing")
            if not test_results.get("login_new_password"):
                self.log("  - Login with new password failing")
        
        return test_results

async def main():
    """Main test execution"""
    tester = SignupResetPasswordTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())