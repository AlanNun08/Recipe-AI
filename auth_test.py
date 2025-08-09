#!/usr/bin/env python3
"""
Authentication Testing Script
Focus: Debug authentication issues blocking comprehensive testing
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import uuid

# Add backend to path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class AuthenticationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.working_user_id = None
        self.working_email = None
        self.working_password = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def check_demo_user_status(self):
        """Test 1: Check if demo@test.com exists and its status"""
        self.log("=== Checking Demo User Status ===")
        
        try:
            # Use debug endpoint to check user
            response = await self.client.get(f"{BACKEND_URL}/debug/user/{DEMO_USER_EMAIL}")
            
            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    self.log(f"❌ Demo user not found: {result['error']}")
                    return False
                else:
                    user = result.get("user", {})
                    self.log(f"✅ Demo user found:")
                    self.log(f"  Email: {user.get('email')}")
                    self.log(f"  First Name: {user.get('first_name')}")
                    self.log(f"  Last Name: {user.get('last_name')}")
                    self.log(f"  Is Verified: {user.get('is_verified')}")
                    self.log(f"  Created At: {user.get('created_at')}")
                    self.log(f"  User ID: {user.get('id')}")
                    
                    return user.get('is_verified', False)
            else:
                self.log(f"❌ Debug endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking demo user: {str(e)}", "ERROR")
            return False
    
    async def test_demo_login(self):
        """Test 2: Test login with demo@test.com/password123"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            self.log(f"Attempting login with {DEMO_USER_EMAIL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Login successful!")
                self.log(f"Status: {result.get('status')}")
                self.log(f"Message: {result.get('message')}")
                
                if result.get('status') == 'unverified':
                    self.log("⚠️ User exists but is not verified")
                    return "unverified"
                elif result.get('status') == 'success':
                    user = result.get('user', {})
                    self.log(f"User ID: {user.get('id')}")
                    self.log(f"Name: {user.get('first_name')} {user.get('last_name')}")
                    self.working_user_id = user.get('id')
                    self.working_email = DEMO_USER_EMAIL
                    self.working_password = DEMO_USER_PASSWORD
                    return "success"
                    
            elif response.status_code == 401:
                result = response.json()
                self.log(f"❌ Login failed (401): {result.get('detail', 'Unknown error')}")
                return "failed"
            else:
                self.log(f"❌ Login failed ({response.status_code}): {response.text}")
                return "failed"
                
        except Exception as e:
            self.log(f"❌ Error testing demo login: {str(e)}", "ERROR")
            return "error"
    
    async def test_demo_registration(self):
        """Test 3: Test registration with demo@test.com"""
        self.log("=== Testing Demo User Registration ===")
        
        try:
            user_data = {
                "first_name": "Demo",
                "last_name": "User",
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": ["Italian"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            self.log(f"Registration response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Registration successful!")
                self.log(f"Message: {result.get('message')}")
                self.log(f"User ID: {result.get('user_id')}")
                return True
                
            elif response.status_code == 400:
                result = response.json()
                detail = result.get('detail', 'Unknown error')
                if "already registered" in detail:
                    self.log(f"⚠️ Email already registered: {detail}")
                    return "exists"
                else:
                    self.log(f"❌ Registration failed (400): {detail}")
                    return False
            else:
                self.log(f"❌ Registration failed ({response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing demo registration: {str(e)}", "ERROR")
            return False
    
    async def create_fresh_test_user(self):
        """Test 4: Create a fresh test user with unique email"""
        self.log("=== Creating Fresh Test User ===")
        
        try:
            # Generate unique email
            timestamp = int(datetime.now().timestamp())
            test_email = f"test.user.{timestamp}@example.com"
            test_password = "testpass123"
            
            self.log(f"Creating user with email: {test_email}")
            
            user_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": test_email,
                "password": test_password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": ["Italian"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("user_id")
                self.log(f"✅ User registered successfully: {user_id}")
                
                # Get verification code
                debug_response = await self.client.get(f"{BACKEND_URL}/debug/verification-codes/{test_email}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    codes = debug_data.get("codes", [])
                    if codes:
                        verification_code = codes[0]["code"]
                        self.log(f"Got verification code: {verification_code}")
                        
                        # Verify user
                        verify_data = {
                            "email": test_email,
                            "code": verification_code
                        }
                        
                        verify_response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                        if verify_response.status_code == 200:
                            self.log("✅ User verified successfully")
                            
                            # Test login
                            login_data = {
                                "email": test_email,
                                "password": test_password
                            }
                            
                            login_response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                            if login_response.status_code == 200:
                                login_result = login_response.json()
                                if login_result.get('status') == 'success':
                                    self.log("✅ Login test successful!")
                                    self.working_user_id = login_result.get('user', {}).get('id')
                                    self.working_email = test_email
                                    self.working_password = test_password
                                    return True
                                else:
                                    self.log(f"❌ Login failed: {login_result}")
                                    return False
                            else:
                                self.log(f"❌ Login test failed: {login_response.text}")
                                return False
                        else:
                            self.log(f"❌ Verification failed: {verify_response.text}")
                            return False
                    else:
                        self.log("❌ No verification codes found")
                        return False
                else:
                    self.log(f"❌ Debug endpoint failed: {debug_response.text}")
                    return False
            else:
                self.log(f"❌ Registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating fresh user: {str(e)}", "ERROR")
            return False
    
    async def test_protected_endpoints(self):
        """Test 5: Test access to protected endpoints"""
        self.log("=== Testing Protected Endpoints ===")
        
        if not self.working_user_id:
            self.log("❌ No working user available for testing")
            return False
        
        try:
            # Test recipe generation
            self.log("Testing recipe generation endpoint...")
            recipe_data = {
                "user_id": self.working_user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "dietary_preferences": [],
                "ingredients_on_hand": [],
                "prep_time_max": 30,
                "servings": 4,
                "difficulty": "medium"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                recipe_id = result.get("id")
                recipe_title = result.get("title", "Unknown")
                shopping_list = result.get("shopping_list", [])
                
                self.log(f"✅ Recipe generated: {recipe_title}")
                self.log(f"Recipe ID: {recipe_id}")
                self.log(f"Shopping list: {shopping_list}")
                
                # Test grocery cart options
                self.log("Testing grocery cart options endpoint...")
                params = {
                    "recipe_id": recipe_id,
                    "user_id": self.working_user_id
                }
                
                cart_response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params=params)
                
                if cart_response.status_code == 200:
                    cart_result = cart_response.json()
                    total_products = cart_result.get('total_products', 0)
                    ingredient_options = cart_result.get('ingredient_options', [])
                    
                    self.log(f"✅ Cart options endpoint working")
                    self.log(f"Total products: {total_products}")
                    self.log(f"Ingredient options: {len(ingredient_options)}")
                    
                    if total_products > 0:
                        self.log("✅ Walmart integration is working with authenticated user")
                        return True
                    else:
                        self.log("⚠️ Cart options endpoint working but no products returned")
                        return True  # Endpoint is accessible, which is what we're testing
                else:
                    self.log(f"❌ Cart options failed: {cart_response.text}")
                    return False
            else:
                self.log(f"❌ Recipe generation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing protected endpoints: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_auth_test(self):
        """Run all authentication tests in sequence"""
        self.log("🚀 Starting Comprehensive Authentication Debug Tests")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Check demo user status
        test_results["demo_user_exists"] = await self.check_demo_user_status()
        
        # Test 2: Test demo login
        demo_login_result = await self.test_demo_login()
        test_results["demo_login"] = demo_login_result == "success"
        
        # Test 3: Test demo registration (to understand the issue)
        demo_reg_result = await self.test_demo_registration()
        test_results["demo_registration"] = demo_reg_result == True
        
        # Test 4: Create fresh test user if demo doesn't work
        if not test_results["demo_login"]:
            self.log("Demo login failed, creating fresh test user...")
            test_results["fresh_user"] = await self.create_fresh_test_user()
        else:
            test_results["fresh_user"] = True  # Demo user works
        
        # Test 5: Test protected endpoints
        if test_results["demo_login"] or test_results.get("fresh_user"):
            test_results["protected_endpoints"] = await self.test_protected_endpoints()
        else:
            test_results["protected_endpoints"] = False
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 AUTHENTICATION TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Provide working credentials
        self.log("=" * 60)
        if self.working_email and self.working_password:
            self.log("🎉 WORKING CREDENTIALS FOUND:")
            self.log(f"Email: {self.working_email}")
            self.log(f"Password: {self.working_password}")
            self.log(f"User ID: {self.working_user_id}")
            self.log("✅ These credentials can be used for comprehensive testing")
        else:
            self.log("❌ NO WORKING CREDENTIALS FOUND")
            self.log("🔧 AUTHENTICATION ISSUES IDENTIFIED:")
            
            if not test_results.get("demo_user_exists"):
                self.log("  - Demo user does not exist in database")
            if not test_results.get("demo_login"):
                self.log("  - Demo user login fails (401 Unauthorized)")
            if demo_reg_result == "exists":
                self.log("  - Demo user exists but login still fails (password mismatch?)")
            if not test_results.get("fresh_user"):
                self.log("  - Unable to create and verify fresh test user")
        
        return test_results, self.working_email, self.working_password, self.working_user_id

async def main():
    """Main test execution"""
    tester = AuthenticationTester()
    
    try:
        results, email, password, user_id = await tester.run_comprehensive_auth_test()
        return results, email, password, user_id
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results, email, password, user_id = asyncio.run(main())
    
    if email and password:
        print(f"\n🎯 FINAL RESULT: Working credentials found!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"User ID: {user_id}")
    else:
        print(f"\n❌ FINAL RESULT: No working credentials found")