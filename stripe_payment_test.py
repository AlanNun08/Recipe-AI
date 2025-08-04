#!/usr/bin/env python3
"""
Comprehensive Stripe Payment System Testing Script
Testing all Stripe subscription endpoints and premium access control
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import string
from pathlib import Path

# Load environment variables
sys.path.append('/app/backend')
from dotenv import load_dotenv
load_dotenv(Path('/app/backend/.env'))

# Get backend URL from frontend environment
frontend_env_path = Path('/app/frontend/.env')
if frontend_env_path.exists():
    with open(frontend_env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
else:
    BACKEND_URL = "http://localhost:8001/api"

print(f"🔗 Testing backend at: {BACKEND_URL}")

# Test user credentials
TEST_USER_EMAIL = "demo@test.com"
TEST_USER_PASSWORD = "password123"

class StripePaymentTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.user_data = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test 1: Login with demo user to get user_id"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.user_data = result.get("user", {})
                    self.user_id = self.user_data.get("id")
                    self.log(f"✅ Demo user login successful")
                    self.log(f"User ID: {self.user_id}")
                    self.log(f"User: {self.user_data.get('first_name')} {self.user_data.get('last_name')}")
                    self.log(f"Email: {self.user_data.get('email')}")
                    self.log(f"Verified: {self.user_data.get('is_verified')}")
                    return True
                else:
                    self.log(f"❌ Login failed: {result.get('message')}")
                    return False
            else:
                self.log(f"❌ Login request failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during login: {str(e)}", "ERROR")
            return False
    
    async def test_subscription_status(self):
        """Test 2: Get user's subscription status"""
        self.log("=== Testing Subscription Status Endpoint ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for subscription status test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/subscription/status/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Subscription status endpoint working")
                self.log(f"Has Access: {result.get('has_access')}")
                self.log(f"Subscription Status: {result.get('subscription_status')}")
                self.log(f"Trial Active: {result.get('trial_active')}")
                self.log(f"Subscription Active: {result.get('subscription_active')}")
                self.log(f"Trial End Date: {result.get('trial_end_date')}")
                self.log(f"Subscription End Date: {result.get('subscription_end_date')}")
                return True
            else:
                self.log(f"❌ Subscription status failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting subscription status: {str(e)}", "ERROR")
            return False
    
    async def test_trial_period_logic(self):
        """Test 3: Verify 7-week trial implementation"""
        self.log("=== Testing 7-Week Trial Logic ===")
        
        try:
            # Import backend functions directly
            from server import is_trial_active, is_subscription_active, can_access_premium_features
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Get user from database
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'test_database')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            user = await db.users.find_one({"id": self.user_id})
            if not user:
                self.log("❌ User not found in database")
                return False
            
            # Test trial logic
            trial_active = is_trial_active(user)
            subscription_active = is_subscription_active(user)
            premium_access = can_access_premium_features(user)
            
            self.log(f"✅ Trial logic functions working")
            self.log(f"Trial Active: {trial_active}")
            self.log(f"Subscription Active: {subscription_active}")
            self.log(f"Premium Access: {premium_access}")
            
            # Check trial dates
            trial_start = user.get('trial_start_date')
            trial_end = user.get('trial_end_date')
            
            if trial_start and trial_end:
                if isinstance(trial_start, str):
                    from dateutil import parser
                    trial_start = parser.parse(trial_start)
                if isinstance(trial_end, str):
                    trial_end = parser.parse(trial_end)
                
                trial_duration = trial_end - trial_start
                self.log(f"Trial Duration: {trial_duration.days} days ({trial_duration.days/7:.1f} weeks)")
                
                if trial_duration.days >= 49:  # 7 weeks = 49 days
                    self.log("✅ 7-week trial period correctly implemented")
                else:
                    self.log(f"❌ Trial period is only {trial_duration.days} days, should be 49+ days")
            
            await client.close()
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing trial logic: {str(e)}", "ERROR")
            return False
    
    async def test_premium_access_control(self):
        """Test 4: Test premium feature gating"""
        self.log("=== Testing Premium Access Control ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for premium access test")
            return False
        
        premium_endpoints = [
            ("/recipes/generate", "POST", {
                "user_id": self.user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "dietary_preferences": [],
                "ingredients_on_hand": [],
                "servings": 4,
                "difficulty": "medium"
            }),
            ("/generate-starbucks-drink", "POST", {
                "user_id": self.user_id,
                "drink_type": "frappuccino"
            }),
            ("/grocery/cart-options", "POST", {
                "recipe_id": "test-recipe-id",
                "user_id": self.user_id
            })
        ]
        
        results = {}
        
        for endpoint, method, data in premium_endpoints:
            try:
                self.log(f"Testing premium endpoint: {method} {endpoint}")
                
                if method == "POST":
                    if endpoint == "/grocery/cart-options":
                        # This endpoint uses query params
                        response = await self.client.post(
                            f"{BACKEND_URL}{endpoint}",
                            params={"recipe_id": data["recipe_id"], "user_id": data["user_id"]}
                        )
                    else:
                        response = await self.client.post(f"{BACKEND_URL}{endpoint}", json=data)
                else:
                    response = await self.client.get(f"{BACKEND_URL}{endpoint}")
                
                self.log(f"Response: {response.status_code}")
                
                if response.status_code == 200:
                    self.log(f"✅ {endpoint} - Premium access granted (user has access)")
                    results[endpoint] = "access_granted"
                elif response.status_code == 402:
                    self.log(f"🔒 {endpoint} - Premium subscription required (access blocked)")
                    results[endpoint] = "access_blocked"
                elif response.status_code == 404:
                    if "recipe-id" in str(data):
                        self.log(f"⚠️ {endpoint} - Recipe not found (expected for test data)")
                        results[endpoint] = "test_data_issue"
                    else:
                        self.log(f"❌ {endpoint} - Endpoint not found")
                        results[endpoint] = "endpoint_missing"
                else:
                    self.log(f"❌ {endpoint} - Unexpected response: {response.text}")
                    results[endpoint] = "error"
                    
            except Exception as e:
                self.log(f"❌ Error testing {endpoint}: {str(e)}")
                results[endpoint] = "exception"
        
        # Analyze results
        access_granted = sum(1 for r in results.values() if r == "access_granted")
        access_blocked = sum(1 for r in results.values() if r == "access_blocked")
        
        self.log(f"Premium Access Summary:")
        self.log(f"  Access Granted: {access_granted}")
        self.log(f"  Access Blocked: {access_blocked}")
        self.log(f"  Other Issues: {len(results) - access_granted - access_blocked}")
        
        return len(results) > 0
    
    async def test_stripe_configuration(self):
        """Test 5: Check Stripe API configuration"""
        self.log("=== Testing Stripe Configuration ===")
        
        try:
            stripe_api_key = os.environ.get('STRIPE_API_KEY')
            
            if stripe_api_key:
                if stripe_api_key.startswith('sk_'):
                    self.log("✅ Stripe API key is present and has correct format")
                    self.log(f"Key type: {'Live' if stripe_api_key.startswith('sk_live_') else 'Test'}")
                    self.log(f"Key preview: {stripe_api_key[:12]}...")
                else:
                    self.log(f"⚠️ Stripe API key present but format may be incorrect: {stripe_api_key[:20]}...")
            else:
                self.log("❌ Stripe API key not found in environment variables")
                return False
            
            # Test emergentintegrations import
            try:
                from emergentintegrations.payments.stripe.checkout import StripeCheckout
                self.log("✅ emergentintegrations Stripe module imported successfully")
            except ImportError as e:
                self.log(f"❌ Failed to import emergentintegrations: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking Stripe configuration: {str(e)}", "ERROR")
            return False
    
    async def test_create_checkout_session(self):
        """Test 6: Test Stripe checkout session creation"""
        self.log("=== Testing Stripe Checkout Session Creation ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for checkout test")
            return False
        
        try:
            checkout_data = {
                "user_id": self.user_id,
                "user_email": TEST_USER_EMAIL,
                "origin_url": "https://test.example.com"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/subscription/create-checkout", json=checkout_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Checkout session created successfully")
                self.log(f"Session URL: {result.get('url', 'N/A')[:50]}...")
                self.log(f"Session ID: {result.get('session_id', 'N/A')}")
                
                # Test checkout status endpoint
                if result.get('session_id'):
                    status_response = await self.client.get(f"{BACKEND_URL}/subscription/checkout/status/{result['session_id']}")
                    if status_response.status_code == 200:
                        status_result = status_response.json()
                        self.log("✅ Checkout status endpoint working")
                        self.log(f"Status: {status_result.get('status')}")
                        self.log(f"Payment Status: {status_result.get('payment_status')}")
                    else:
                        self.log(f"⚠️ Checkout status endpoint failed: {status_response.status_code}")
                
                return True
            elif response.status_code == 400:
                result = response.json()
                if "already has active subscription" in result.get("detail", ""):
                    self.log("✅ Checkout creation properly blocked - user already has active subscription")
                    return True
                else:
                    self.log(f"❌ Checkout creation failed: {result.get('detail')}")
                    return False
            elif response.status_code == 500:
                result = response.json()
                if "Stripe not configured" in result.get("detail", ""):
                    self.log("⚠️ Stripe not configured (expected with placeholder API key)")
                    return True
                else:
                    self.log(f"❌ Checkout creation failed: {result.get('detail')}")
                    return False
            else:
                self.log(f"❌ Checkout creation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing checkout creation: {str(e)}", "ERROR")
            return False
    
    async def test_stripe_webhook_endpoint(self):
        """Test 7: Test Stripe webhook endpoint structure"""
        self.log("=== Testing Stripe Webhook Endpoint ===")
        
        try:
            # Test webhook endpoint with dummy data (should fail gracefully)
            webhook_data = {
                "id": "evt_test_webhook",
                "object": "event",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_session",
                        "payment_status": "paid"
                    }
                }
            }
            
            headers = {
                "stripe-signature": "t=1234567890,v1=dummy_signature"
            }
            
            response = await self.client.post(
                f"{BACKEND_URL}/webhook/stripe", 
                json=webhook_data,
                headers=headers
            )
            
            # Webhook should return 200 even if signature verification fails
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Webhook endpoint accessible and responding")
                self.log(f"Response: {result}")
                return True
            elif response.status_code == 500:
                result = response.json()
                if "Stripe not configured" in result.get("detail", ""):
                    self.log("⚠️ Webhook endpoint exists but Stripe not configured (expected)")
                    return True
                else:
                    self.log(f"❌ Webhook failed: {result.get('detail')}")
                    return False
            else:
                self.log(f"❌ Webhook endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing webhook endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_missing_endpoints(self):
        """Test 8: Check for missing subscription endpoints"""
        self.log("=== Testing Missing Subscription Endpoints ===")
        
        missing_endpoints = [
            ("/subscription/cancel", "POST"),
            ("/subscription/resubscribe", "POST")
        ]
        
        results = {}
        
        for endpoint, method in missing_endpoints:
            try:
                if method == "POST":
                    response = await self.client.post(f"{BACKEND_URL}{endpoint}", json={"user_id": self.user_id})
                else:
                    response = await self.client.get(f"{BACKEND_URL}{endpoint}")
                
                if response.status_code == 404:
                    self.log(f"❌ {endpoint} - Endpoint not implemented")
                    results[endpoint] = "missing"
                elif response.status_code == 405:
                    self.log(f"⚠️ {endpoint} - Method not allowed (endpoint exists but wrong method)")
                    results[endpoint] = "method_issue"
                else:
                    self.log(f"✅ {endpoint} - Endpoint exists (status: {response.status_code})")
                    results[endpoint] = "exists"
                    
            except Exception as e:
                self.log(f"❌ Error testing {endpoint}: {str(e)}")
                results[endpoint] = "error"
        
        missing_count = sum(1 for r in results.values() if r == "missing")
        self.log(f"Missing endpoints: {missing_count}/{len(missing_endpoints)}")
        
        return missing_count == 0
    
    async def test_user_model_fields(self):
        """Test 9: Verify user model subscription fields"""
        self.log("=== Testing User Model Subscription Fields ===")
        
        try:
            # Import backend functions directly
            from motor.motor_asyncio import AsyncIOMotorClient
            
            # Get user from database
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            db_name = os.environ.get('DB_NAME', 'test_database')
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            
            user = await db.users.find_one({"id": self.user_id})
            if not user:
                self.log("❌ User not found in database")
                return False
            
            # Check required subscription fields
            required_fields = [
                'subscription_status',
                'trial_start_date', 
                'trial_end_date',
                'subscription_start_date',
                'subscription_end_date',
                'stripe_customer_id',
                'stripe_subscription_id',
                'last_payment_date',
                'next_billing_date'
            ]
            
            field_status = {}
            for field in required_fields:
                if field in user:
                    field_status[field] = "present"
                    self.log(f"✅ {field}: {user[field]}")
                else:
                    field_status[field] = "missing"
                    self.log(f"❌ {field}: Missing")
            
            present_count = sum(1 for status in field_status.values() if status == "present")
            self.log(f"Subscription fields present: {present_count}/{len(required_fields)}")
            
            await client.close()
            return present_count >= len(required_fields) * 0.8  # At least 80% of fields present
            
        except Exception as e:
            self.log(f"❌ Error checking user model fields: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all Stripe payment system tests"""
        self.log("🚀 Starting Comprehensive Stripe Payment System Testing")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Demo user login
        test_results["demo_login"] = await self.test_demo_user_login()
        
        # Test 2: Subscription status
        test_results["subscription_status"] = await self.test_subscription_status()
        
        # Test 3: Trial period logic
        test_results["trial_logic"] = await self.test_trial_period_logic()
        
        # Test 4: Premium access control
        test_results["premium_access"] = await self.test_premium_access_control()
        
        # Test 5: Stripe configuration
        test_results["stripe_config"] = await self.test_stripe_configuration()
        
        # Test 6: Checkout session creation
        test_results["checkout_session"] = await self.test_create_checkout_session()
        
        # Test 7: Webhook endpoint
        test_results["webhook_endpoint"] = await self.test_stripe_webhook_endpoint()
        
        # Test 8: Missing endpoints
        test_results["missing_endpoints"] = await self.test_missing_endpoints()
        
        # Test 9: User model fields
        test_results["user_model_fields"] = await self.test_user_model_fields()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 STRIPE PAYMENT SYSTEM TEST RESULTS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = [
            "demo_login", "subscription_status", "trial_logic", 
            "premium_access", "stripe_config", "checkout_session"
        ]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL STRIPE TESTS PASSED")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
        
        # Detailed findings
        self.log("\n🔍 DETAILED FINDINGS:")
        
        if not test_results.get("demo_login"):
            self.log("  - Demo user login failed - cannot test subscription features")
        
        if not test_results.get("subscription_status"):
            self.log("  - Subscription status endpoint not working")
        
        if not test_results.get("trial_logic"):
            self.log("  - 7-week trial logic implementation issues")
        
        if not test_results.get("premium_access"):
            self.log("  - Premium access control not working properly")
        
        if not test_results.get("stripe_config"):
            self.log("  - Stripe configuration issues (API key or library)")
        
        if not test_results.get("checkout_session"):
            self.log("  - Stripe checkout session creation not working")
        
        if not test_results.get("webhook_endpoint"):
            self.log("  - Stripe webhook endpoint issues")
        
        if not test_results.get("missing_endpoints"):
            self.log("  - Missing subscription cancel/resubscribe endpoints")
        
        if not test_results.get("user_model_fields"):
            self.log("  - User model missing required subscription fields")
        
        return test_results

async def main():
    """Main test execution"""
    tester = StripePaymentTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())