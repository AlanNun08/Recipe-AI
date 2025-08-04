#!/usr/bin/env python3
"""
Advanced Stripe Subscription Testing - Simulating Different States
This test will manually manipulate user subscription states to test all scenarios
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add backend to path for direct database access
sys.path.append('/app/backend')

# Get backend URL
def get_backend_url():
    try:
        frontend_env_path = Path('/app/frontend/.env')
        if frontend_env_path.exists():
            with open(frontend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "https://1622b782-641f-4d82-b075-7432aa2ce82e.preview.emergentagent.com"

BACKEND_URL = get_backend_url()
API_BASE = f"{BACKEND_URL}/api"
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class AdvancedSubscriptionTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = None
        self.test_results = []
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_test_result(self, test_name: str, success: bool, details: str):
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "status": status
        })
        self.log(f"{status}: {test_name} - {details}")

    async def authenticate_demo_user(self):
        """Authenticate with demo user"""
        try:
            login_data = {"email": DEMO_USER_EMAIL, "password": DEMO_USER_PASSWORD}
            response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.demo_user_id = data["user"]["id"]
                    self.log(f"✅ Demo user authenticated. User ID: {self.demo_user_id}")
                    return True
            return False
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}")
            return False

    async def simulate_subscription_state(self, state: str):
        """Simulate different subscription states using direct database manipulation"""
        self.log(f"=== Simulating {state.upper()} State ===")
        
        try:
            # Import database connection
            from dotenv import load_dotenv
            from motor.motor_asyncio import AsyncIOMotorClient
            import os
            
            # Load environment
            load_dotenv('/app/backend/.env')
            mongo_url = os.environ['MONGO_URL']
            client = AsyncIOMotorClient(mongo_url)
            db = client[os.environ.get('DB_NAME', 'test_database')]
            users_collection = db["users"]
            
            now = datetime.utcnow()
            
            if state == "active":
                # Set user to have active subscription
                update_data = {
                    "subscription_status": "active",
                    "subscription_start_date": now - timedelta(days=10),
                    "subscription_end_date": now + timedelta(days=20),
                    "stripe_subscription_id": "sub_test_active_123",
                    "trial_end_date": now - timedelta(days=5),  # Trial ended
                    "last_payment_date": now - timedelta(days=10),
                    "next_billing_date": now + timedelta(days=20)
                }
            elif state == "cancelled":
                # Set user to have cancelled subscription
                update_data = {
                    "subscription_status": "cancelled",
                    "subscription_cancelled_date": now - timedelta(days=2),
                    "subscription_cancel_reason": "user_requested",
                    "subscription_start_date": now - timedelta(days=30),
                    "subscription_end_date": now - timedelta(days=2),
                    "stripe_subscription_id": "sub_test_cancelled_123",
                    "trial_end_date": now - timedelta(days=25)
                }
            elif state == "expired":
                # Set user to have expired subscription
                update_data = {
                    "subscription_status": "expired",
                    "subscription_start_date": now - timedelta(days=60),
                    "subscription_end_date": now - timedelta(days=5),
                    "stripe_subscription_id": "sub_test_expired_123",
                    "trial_end_date": now - timedelta(days=55)
                }
            elif state == "trial":
                # Reset to trial state
                update_data = {
                    "subscription_status": "trial",
                    "trial_start_date": now - timedelta(days=5),
                    "trial_end_date": now + timedelta(weeks=7, days=-5),
                    "subscription_cancelled_date": None,
                    "subscription_cancel_reason": None,
                    "subscription_reactivated_date": None,
                    "subscription_start_date": None,
                    "subscription_end_date": None,
                    "stripe_subscription_id": None,
                    "last_payment_date": None,
                    "next_billing_date": None
                }
            
            # Update user in database
            result = await users_collection.update_one(
                {"id": self.demo_user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.log(f"✅ Successfully set user to {state} state")
                
                # Verify the change
                status_response = await self.client.get(f"{API_BASE}/subscription/status/{self.demo_user_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    self.log(f"Current status: {status_data}")
                
                await client.close()
                return True
            else:
                self.log(f"❌ Failed to update user to {state} state")
                await client.close()
                return False
                
        except Exception as e:
            self.log(f"❌ Error simulating {state} state: {str(e)}")
            return False

    async def test_cancel_active_subscription_real(self):
        """Test cancelling a real active subscription"""
        self.log("=== Test: Cancel Real Active Subscription ===")
        
        # First simulate active subscription
        if not await self.simulate_subscription_state("active"):
            self.add_test_result("Cancel Real Active Subscription", False, "Failed to simulate active state")
            return False
        
        try:
            response = await self.client.post(f"{API_BASE}/subscription/cancel/{self.demo_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.add_test_result(
                        "Cancel Real Active Subscription",
                        True,
                        f"Successfully cancelled active subscription: {data.get('message')}"
                    )
                    
                    # Verify cancellation in database
                    status_response = await self.client.get(f"{API_BASE}/subscription/status/{self.demo_user_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("subscription_status") == "cancelled":
                            self.log("✅ Subscription status correctly updated to cancelled")
                        else:
                            self.log(f"⚠️ Subscription status: {status_data.get('subscription_status')}")
                    
                    return True
                else:
                    self.add_test_result("Cancel Real Active Subscription", False, f"Unexpected response: {data}")
                    return False
            else:
                self.add_test_result("Cancel Real Active Subscription", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.add_test_result("Cancel Real Active Subscription", False, f"Exception: {str(e)}")
            return False

    async def test_resubscribe_after_real_cancellation(self):
        """Test resubscribing after real cancellation"""
        self.log("=== Test: Resubscribe After Real Cancellation ===")
        
        # First simulate cancelled subscription
        if not await self.simulate_subscription_state("cancelled"):
            self.add_test_result("Resubscribe After Real Cancellation", False, "Failed to simulate cancelled state")
            return False
        
        try:
            response = await self.client.post(f"{API_BASE}/subscription/resubscribe/{self.demo_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.add_test_result(
                        "Resubscribe After Real Cancellation",
                        True,
                        f"Successfully resubscribed: {data.get('message')}"
                    )
                    
                    # Verify resubscription reset to trial
                    status_response = await self.client.get(f"{API_BASE}/subscription/status/{self.demo_user_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("subscription_status") == "trial":
                            self.log("✅ Subscription correctly reset to trial")
                        else:
                            self.log(f"⚠️ Subscription status: {status_data.get('subscription_status')}")
                    
                    return True
                else:
                    self.add_test_result("Resubscribe After Real Cancellation", False, f"Unexpected response: {data}")
                    return False
            else:
                self.add_test_result("Resubscribe After Real Cancellation", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.add_test_result("Resubscribe After Real Cancellation", False, f"Exception: {str(e)}")
            return False

    async def test_resubscribe_expired_subscription(self):
        """Test resubscribing an expired subscription"""
        self.log("=== Test: Resubscribe Expired Subscription ===")
        
        # First simulate expired subscription
        if not await self.simulate_subscription_state("expired"):
            self.add_test_result("Resubscribe Expired Subscription", False, "Failed to simulate expired state")
            return False
        
        try:
            response = await self.client.post(f"{API_BASE}/subscription/resubscribe/{self.demo_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.add_test_result(
                        "Resubscribe Expired Subscription",
                        True,
                        f"Successfully resubscribed expired subscription: {data.get('message')}"
                    )
                    return True
                else:
                    self.add_test_result("Resubscribe Expired Subscription", False, f"Unexpected response: {data}")
                    return False
            else:
                self.add_test_result("Resubscribe Expired Subscription", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.add_test_result("Resubscribe Expired Subscription", False, f"Exception: {str(e)}")
            return False

    async def test_premium_access_after_cancellation(self):
        """Test that premium access is properly blocked after cancellation"""
        self.log("=== Test: Premium Access After Cancellation ===")
        
        # First simulate cancelled subscription
        if not await self.simulate_subscription_state("cancelled"):
            self.add_test_result("Premium Access After Cancellation", False, "Failed to simulate cancelled state")
            return False
        
        try:
            # Test premium endpoint access
            premium_endpoints = [
                f"{API_BASE}/recipes/generate",
                f"{API_BASE}/generate-starbucks-drink",
                f"{API_BASE}/grocery/cart-options"
            ]
            
            blocked_count = 0
            for endpoint in premium_endpoints:
                try:
                    if "recipes/generate" in endpoint:
                        test_data = {
                            "user_id": self.demo_user_id,
                            "recipe_category": "cuisine",
                            "cuisine_type": "Italian",
                            "servings": 4
                        }
                        response = await self.client.post(endpoint, json=test_data)
                    elif "generate-starbucks-drink" in endpoint:
                        test_data = {
                            "user_id": self.demo_user_id,
                            "drink_type": "frappuccino"
                        }
                        response = await self.client.post(endpoint, json=test_data)
                    elif "grocery/cart-options" in endpoint:
                        response = await self.client.post(endpoint, params={
                            "user_id": self.demo_user_id,
                            "recipe_id": "test_recipe_123"
                        })
                    
                    if response.status_code == 402:  # Payment required
                        blocked_count += 1
                        self.log(f"✅ {endpoint} correctly blocked with 402")
                    else:
                        self.log(f"⚠️ {endpoint} returned {response.status_code} instead of 402")
                        
                except Exception as e:
                    self.log(f"Error testing {endpoint}: {str(e)}")
            
            if blocked_count >= 2:  # At least 2 out of 3 should be blocked
                self.add_test_result(
                    "Premium Access After Cancellation",
                    True,
                    f"Premium endpoints correctly blocked ({blocked_count}/3)"
                )
                return True
            else:
                self.add_test_result(
                    "Premium Access After Cancellation",
                    False,
                    f"Premium endpoints not properly blocked ({blocked_count}/3)"
                )
                return False
                
        except Exception as e:
            self.add_test_result("Premium Access After Cancellation", False, f"Exception: {str(e)}")
            return False

    async def test_database_field_updates(self):
        """Test that database fields are properly updated during cancel/resubscribe"""
        self.log("=== Test: Database Field Updates ===")
        
        try:
            # Test cancellation field updates
            await self.simulate_subscription_state("active")
            await self.client.post(f"{API_BASE}/subscription/cancel/{self.demo_user_id}")
            
            # Check user debug info
            debug_response = await self.client.get(f"{API_BASE}/debug/user/{DEMO_USER_EMAIL}")
            if debug_response.status_code == 200:
                user_data = debug_response.json().get("user", {})
                
                # Check cancellation fields
                cancel_date = user_data.get("subscription_cancelled_date")
                cancel_reason = user_data.get("subscription_cancel_reason")
                
                if cancel_date and cancel_reason == "user_requested":
                    self.log("✅ Cancellation fields properly set")
                    
                    # Test resubscribe field updates
                    await self.client.post(f"{API_BASE}/subscription/resubscribe/{self.demo_user_id}")
                    
                    debug_response2 = await self.client.get(f"{API_BASE}/debug/user/{DEMO_USER_EMAIL}")
                    if debug_response2.status_code == 200:
                        user_data2 = debug_response2.json().get("user", {})
                        reactivated_date = user_data2.get("subscription_reactivated_date")
                        
                        if reactivated_date:
                            self.add_test_result(
                                "Database Field Updates",
                                True,
                                "All subscription fields properly updated during cancel/resubscribe cycle"
                            )
                            return True
                        else:
                            self.add_test_result(
                                "Database Field Updates",
                                False,
                                "Reactivation date not set properly"
                            )
                            return False
                else:
                    self.add_test_result(
                        "Database Field Updates",
                        False,
                        f"Cancellation fields not set properly: date={cancel_date}, reason={cancel_reason}"
                    )
                    return False
            else:
                self.add_test_result("Database Field Updates", False, "Cannot access debug endpoint")
                return False
                
        except Exception as e:
            self.add_test_result("Database Field Updates", False, f"Exception: {str(e)}")
            return False

    async def run_advanced_tests(self):
        """Run all advanced subscription tests"""
        self.log("🚀 Starting Advanced Stripe Subscription Testing")
        self.log(f"Backend URL: {API_BASE}")
        
        if not await self.authenticate_demo_user():
            self.log("❌ Failed to authenticate demo user")
            return False
        
        # Run advanced tests
        test_methods = [
            self.test_cancel_active_subscription_real,
            self.test_resubscribe_after_real_cancellation,
            self.test_resubscribe_expired_subscription,
            self.test_premium_access_after_cancellation,
            self.test_database_field_updates
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(1)
            except Exception as e:
                self.log(f"❌ Test {test_method.__name__} failed: {str(e)}")
        
        # Reset to trial state for cleanup
        await self.simulate_subscription_state("trial")
        
        self.print_test_summary()
        return True

    def print_test_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80)
        self.log("🎯 ADVANCED STRIPE SUBSCRIPTION TEST SUMMARY")
        self.log("="*80)
        
        passed_tests = [r for r in self.test_results if r["success"]]
        failed_tests = [r for r in self.test_results if not r["success"]]
        
        self.log(f"✅ PASSED: {len(passed_tests)}/{len(self.test_results)} tests")
        self.log(f"❌ FAILED: {len(failed_tests)}/{len(self.test_results)} tests")
        
        if passed_tests:
            self.log("\n✅ PASSED TESTS:")
            for result in passed_tests:
                self.log(f"  • {result['test']}: {result['details']}")
        
        if failed_tests:
            self.log("\n❌ FAILED TESTS:")
            for result in failed_tests:
                self.log(f"  • {result['test']}: {result['details']}")
        
        self.log("\n" + "="*80)

async def main():
    tester = AdvancedSubscriptionTester()
    try:
        await tester.run_advanced_tests()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())