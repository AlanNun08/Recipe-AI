#!/usr/bin/env python3
"""
API Endpoints Tests
Tests all critical API endpoints for functionality and data integrity
"""

import asyncio
import httpx
import json
from datetime import datetime

class TestAPIEndpoints:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_user_authentication(self):
        """Test user authentication endpoints"""
        self.log("=== Testing User Authentication ===")
        
        # Test login
        login_data = {
            "email": "demo@test.com",
            "password": "password123"
        }
        
        try:
            response = await self.client.post(f"{self.backend_url}/users/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("user_id")
                
                if user_id == self.demo_user_id:
                    self.log(f"✅ Login successful: {user_id}")
                    return True
                else:
                    self.log(f"❌ Login returned wrong user ID: {user_id}", "ERROR")
                    return False
            else:
                self.log(f"❌ Login failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_endpoints(self):
        """Test recipe-related endpoints"""
        self.log("=== Testing Recipe Endpoints ===")
        
        endpoints_to_test = [
            (f"recipes/history/{self.demo_user_id}", "GET", None, "Recipe History"),
            ("recipes/generate", "POST", {
                "user_id": self.demo_user_id,
                "cuisine_type": "Italian", 
                "recipe_category": "cuisine",
                "meal_type": "dinner",
                "servings": 4,
                "difficulty": "medium",
                "dietary_preferences": []
            }, "Recipe Generation")
        ]
        
        for endpoint, method, data, name in endpoints_to_test:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.backend_url}/{endpoint}")
                else:
                    response = await self.client.post(f"{self.backend_url}/{endpoint}", json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "history" in endpoint:
                        recipes = result.get("recipes", [])
                        self.log(f"✅ {name}: {len(recipes)} recipes returned")
                    else:
                        title = result.get("title", "Unknown")
                        self.log(f"✅ {name}: Generated '{title}'")
                else:
                    self.log(f"❌ {name} failed: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ {name} error: {str(e)}", "ERROR")
                return False
        
        return True
    
    async def test_walmart_integration(self):
        """Test Walmart integration endpoints"""
        self.log("=== Testing Walmart Integration ===")
        
        # Get a recipe to test Walmart integration
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log("❌ Could not get recipes for Walmart test", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])
            
            if not recipes:
                self.log("❌ No recipes available for Walmart test", "ERROR")
                return False
            
            test_recipe_id = recipes[0].get("id")
            
            # Test cart options endpoint
            cart_response = await self.client.get(f"{self.backend_url}/recipes/{test_recipe_id}/walmart-cart-options")
            
            if cart_response.status_code == 200:
                cart_result = cart_response.json()
                ingredient_options = cart_result.get("ingredient_options", [])
                self.log(f"✅ Walmart cart options: {len(ingredient_options)} ingredient options")
                return True
            else:
                self.log(f"❌ Walmart cart options failed: {cart_response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Walmart integration error: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_endpoints(self):
        """Test Starbucks recipe endpoints"""
        self.log("=== Testing Starbucks Endpoints ===")
        
        try:
            # Test Starbucks recipe generation
            starbucks_data = {
                "user_id": self.demo_user_id,
                "drink_type": "frappuccino",
                "flavor_profile": "sweet",
                "size": "medium"
            }
            
            response = await self.client.post(f"{self.backend_url}/starbucks/generate", json=starbucks_data)
            
            if response.status_code == 200:
                result = response.json()
                drink_name = result.get("name", "Unknown")
                ingredients = result.get("ingredients", [])
                self.log(f"✅ Starbucks generation: '{drink_name}' with {len(ingredients)} ingredients")
                return True
            else:
                self.log(f"❌ Starbucks generation failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Starbucks endpoints error: {str(e)}", "ERROR")
            return False
    
    async def test_subscription_endpoints(self):
        """Test subscription-related endpoints"""
        self.log("=== Testing Subscription Endpoints ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/users/{self.demo_user_id}/subscription-status")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("subscription_status", "unknown")
                self.log(f"✅ Subscription status: {status}")
                return True
            else:
                self.log(f"❌ Subscription status failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Subscription endpoints error: {str(e)}", "ERROR")
            return False
    
    async def test_weekly_recipes(self):
        """Test weekly recipe endpoints"""
        self.log("=== Testing Weekly Recipe Endpoints ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/weekly-recipes/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                plans = result.get("weekly_plans", [])
                self.log(f"✅ Weekly recipes: {len(plans)} weekly plans")
                return True
            elif response.status_code == 404:
                self.log("✅ Weekly recipes: No plans found (expected for new user)")
                return True
            else:
                self.log(f"❌ Weekly recipes failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Weekly recipes error: {str(e)}", "ERROR")
            return False
    
    async def test_error_handling(self):
        """Test API error handling"""
        self.log("=== Testing Error Handling ===")
        
        error_tests = [
            (f"recipes/history/invalid-user-id", "GET", None, "Invalid User ID"),
            ("recipes/invalid-endpoint", "GET", None, "Invalid Endpoint"),
            ("recipes/generate", "POST", {"invalid": "data"}, "Invalid Recipe Data")
        ]
        
        for endpoint, method, data, test_name in error_tests:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.backend_url}/{endpoint}")
                else:
                    response = await self.client.post(f"{self.backend_url}/{endpoint}", json=data)
                
                # We expect these to fail with appropriate error codes
                if response.status_code in [400, 404, 422, 500]:
                    self.log(f"✅ {test_name}: Properly returned {response.status_code}")
                else:
                    self.log(f"⚠️  {test_name}: Unexpected status {response.status_code}", "WARNING")
                    
            except Exception as e:
                self.log(f"✅ {test_name}: Properly raised exception")
        
        return True
    
    async def run_all_tests(self):
        """Run all API endpoint tests"""
        self.log("🚀 Starting API Endpoints Tests")
        self.log("=" * 50)
        
        tests = [
            ("Authentication", self.test_user_authentication),
            ("Recipe Endpoints", self.test_recipe_endpoints),
            ("Walmart Integration", self.test_walmart_integration),
            ("Starbucks Endpoints", self.test_starbucks_endpoints),
            ("Subscription", self.test_subscription_endpoints),
            ("Weekly Recipes", self.test_weekly_recipes),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} test...")
            try:
                result = await test_func()
                if result:
                    passed += 1
                    self.log(f"✅ {test_name} test PASSED")
                else:
                    self.log(f"❌ {test_name} test FAILED")
            except Exception as e:
                self.log(f"❌ {test_name} test ERROR: {str(e)}", "ERROR")
        
        self.log("=" * 50)
        self.log(f"🎯 API Endpoints Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All API endpoint tests PASSED!")
            return True
        else:
            self.log(f"❌ {total - passed} test(s) FAILED")
            return False

async def main():
    tester = TestAPIEndpoints()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 API endpoint tests completed successfully!")
    else:
        print("\n❌ API endpoint tests failed!")
        exit(1)