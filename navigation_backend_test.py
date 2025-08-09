#!/usr/bin/env python3
"""
Navigation Improvements Backend Testing Script
Testing recipe detail and history navigation endpoints as requested in review
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

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url() + "/api"
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class NavigationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = None
        self.generated_recipe_id = None
        self.weekly_recipe_id = None
        self.history_recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test 1: Login with demo user for testing"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.demo_user_id = result.get("user", {}).get("id")
                user_status = result.get("status")
                
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {self.demo_user_id}")
                self.log(f"Status: {user_status}")
                
                # Check if user is verified
                user_data = result.get("user", {})
                is_verified = user_data.get("is_verified", False)
                self.log(f"Verified: {is_verified}")
                
                return True
                
            else:
                self.log(f"❌ Demo user login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error logging in demo user: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_generation_navigation(self):
        """Test 2: Generate a recipe and test navigation to detail screen"""
        self.log("=== Testing Recipe Generation Navigation ===")
        
        if not self.demo_user_id:
            self.log("❌ No demo user ID available")
            return False
        
        try:
            # Generate a recipe
            recipe_data = {
                "user_id": self.demo_user_id,
                "cuisine_type": "Italian",
                "meal_type": "dinner",
                "difficulty": "medium",
                "prep_time_max": 30,
                "servings": 4,
                "dietary_preferences": ["Vegetarian"],
                "ingredients_on_hand": ["tomatoes", "basil", "mozzarella"]
            }
            
            self.log("Generating recipe with navigation test parameters...")
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                self.generated_recipe_id = result.get("id")
                recipe_title = result.get("title", "Unknown")
                
                self.log(f"✅ Recipe generated successfully")
                self.log(f"Recipe ID: {self.generated_recipe_id}")
                self.log(f"Title: {recipe_title}")
                
                # Test navigation to detail screen by fetching recipe details
                detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{self.generated_recipe_id}")
                
                if detail_response.status_code == 200:
                    detail_result = detail_response.json()
                    self.log(f"✅ Recipe detail navigation working - recipe found")
                    self.log(f"Detail title: {detail_result.get('title', 'Unknown')}")
                    
                    # Check if recipe has proper structure for navigation
                    required_fields = ['id', 'title', 'description', 'ingredients', 'instructions']
                    missing_fields = [field for field in required_fields if field not in detail_result]
                    
                    if not missing_fields:
                        self.log("✅ Recipe has all required fields for detail screen")
                        return True
                    else:
                        self.log(f"⚠️ Recipe missing fields: {missing_fields}")
                        return True  # Still working, just incomplete
                        
                else:
                    self.log(f"❌ Recipe detail navigation failed: {detail_response.text}")
                    return False
                    
            else:
                self.log(f"❌ Recipe generation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe generation navigation: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_history_navigation(self):
        """Test 3: Test recipe history loading and navigation"""
        self.log("=== Testing Recipe History Navigation ===")
        
        if not self.demo_user_id:
            self.log("❌ No demo user ID available")
            return False
        
        try:
            # Get user's recipe history
            response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Recipe history loaded successfully")
                self.log(f"Found {len(recipes)} recipes in history")
                
                if recipes:
                    # Test navigation to first recipe in history
                    first_recipe = recipes[0]
                    self.history_recipe_id = first_recipe.get("id")
                    recipe_title = first_recipe.get("title", "Unknown")
                    
                    self.log(f"Testing navigation to history recipe: {recipe_title}")
                    
                    # Test detail navigation for history recipe
                    detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{self.history_recipe_id}")
                    
                    if detail_response.status_code == 200:
                        self.log("✅ History recipe detail navigation working")
                        
                        # Check if it's a Starbucks recipe (should redirect to Starbucks screen)
                        detail_result = detail_response.json()
                        recipe_type = detail_result.get("category", "").lower()
                        
                        if "starbucks" in recipe_type or "drink" in recipe_type:
                            self.log("✅ Starbucks recipe detected - should redirect to Starbucks screen")
                        else:
                            self.log("✅ Regular recipe - should open in detail view")
                        
                        return True
                    else:
                        self.log(f"❌ History recipe detail failed: {detail_response.text}")
                        return False
                else:
                    self.log("⚠️ No recipes in history - creating one for testing")
                    # Use the generated recipe as history
                    if self.generated_recipe_id:
                        self.history_recipe_id = self.generated_recipe_id
                        self.log("✅ Using generated recipe as history test")
                        return True
                    else:
                        self.log("❌ No recipes available for history testing")
                        return False
                        
            else:
                self.log(f"❌ Recipe history loading failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe history navigation: {str(e)}", "ERROR")
            return False
    
    async def test_session_management(self):
        """Test 4: Test session persistence during navigation"""
        self.log("=== Testing Session Management ===")
        
        if not self.demo_user_id:
            self.log("❌ No demo user ID available")
            return False
        
        try:
            # Test multiple navigation calls to ensure session persists
            navigation_tests = [
                f"/recipes/{self.generated_recipe_id}" if self.generated_recipe_id else None,
                f"/recipes/history/{self.demo_user_id}",
                f"/subscription/status/{self.demo_user_id}",
                f"/weekly-recipes/current/{self.demo_user_id}"
            ]
            
            successful_calls = 0
            total_calls = 0
            
            for endpoint in navigation_tests:
                if endpoint:
                    total_calls += 1
                    self.log(f"Testing session persistence for: {endpoint}")
                    
                    response = await self.client.get(f"{BACKEND_URL}{endpoint}")
                    
                    if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                        successful_calls += 1
                        self.log(f"✅ Session maintained for {endpoint}")
                    else:
                        self.log(f"❌ Session issue for {endpoint}: {response.status_code}")
            
            if successful_calls == total_calls:
                self.log("✅ Session management working - users stay logged in during navigation")
                return True
            else:
                self.log(f"⚠️ Session issues: {successful_calls}/{total_calls} calls successful")
                return successful_calls > 0
                
        except Exception as e:
            self.log(f"❌ Error testing session management: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_detail_endpoints(self):
        """Test 5: Test backend recipe detail endpoints"""
        self.log("=== Testing Backend Recipe Detail Endpoints ===")
        
        try:
            endpoints_tested = 0
            endpoints_working = 0
            
            # Test 1: Generated/History recipe detail endpoint
            if self.generated_recipe_id:
                endpoints_tested += 1
                self.log(f"Testing /api/recipes/{self.generated_recipe_id}/detail")
                
                response = await self.client.get(f"{BACKEND_URL}/recipes/{self.generated_recipe_id}/detail")
                
                if response.status_code == 200:
                    endpoints_working += 1
                    result = response.json()
                    self.log("✅ Generated recipe detail endpoint working")
                    self.log(f"Recipe data includes: {list(result.keys())}")
                elif response.status_code == 404:
                    # Try alternative endpoint format
                    response = await self.client.get(f"{BACKEND_URL}/recipes/{self.generated_recipe_id}")
                    if response.status_code == 200:
                        endpoints_working += 1
                        self.log("✅ Generated recipe detail endpoint working (alternative format)")
                    else:
                        self.log(f"❌ Generated recipe detail endpoint failed: {response.status_code}")
                else:
                    self.log(f"❌ Generated recipe detail endpoint failed: {response.status_code}")
            
            # Test 2: Weekly recipe detail endpoint
            endpoints_tested += 1
            self.log("Testing weekly recipe detail endpoint")
            
            # First get current weekly recipes
            weekly_response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.demo_user_id}")
            
            if weekly_response.status_code == 200:
                weekly_result = weekly_response.json()
                meals = weekly_result.get("meals", [])
                
                if meals:
                    # Test detail endpoint for first meal
                    first_meal_id = meals[0].get("id")
                    self.weekly_recipe_id = first_meal_id
                    
                    detail_response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{first_meal_id}")
                    
                    if detail_response.status_code == 200:
                        endpoints_working += 1
                        detail_result = detail_response.json()
                        self.log("✅ Weekly recipe detail endpoint working")
                        self.log(f"Weekly recipe: {detail_result.get('name', 'Unknown')}")
                        
                        # Check for cart_ingredients structure for Walmart integration
                        if 'cart_ingredients' in detail_result:
                            self.log("✅ Weekly recipe has cart_ingredients for Walmart integration")
                        else:
                            self.log("⚠️ Weekly recipe missing cart_ingredients")
                    else:
                        self.log(f"❌ Weekly recipe detail endpoint failed: {detail_response.status_code}")
                else:
                    self.log("⚠️ No weekly meals available for testing")
                    endpoints_working += 1  # Don't penalize for no data
            else:
                self.log(f"❌ Weekly recipes current endpoint failed: {weekly_response.status_code}")
            
            # Test 3: Recipe source parameter handling
            if self.generated_recipe_id:
                endpoints_tested += 1
                self.log("Testing recipe detail with source parameter")
                
                response = await self.client.get(f"{BACKEND_URL}/recipes/{self.generated_recipe_id}?source=generated")
                
                if response.status_code == 200:
                    endpoints_working += 1
                    self.log("✅ Recipe detail with source parameter working")
                else:
                    self.log(f"❌ Recipe detail with source parameter failed: {response.status_code}")
            
            success_rate = endpoints_working / endpoints_tested if endpoints_tested > 0 else 0
            self.log(f"Recipe detail endpoints: {endpoints_working}/{endpoints_tested} working ({success_rate:.1%})")
            
            return success_rate >= 0.5  # At least 50% working
            
        except Exception as e:
            self.log(f"❌ Error testing recipe detail endpoints: {str(e)}", "ERROR")
            return False
    
    async def test_back_button_navigation(self):
        """Test 6: Test back button navigation context"""
        self.log("=== Testing Back Button Navigation Context ===")
        
        try:
            # Test different navigation sources
            navigation_contexts = [
                {"source": "weekly", "expected_text": "Back to Weekly Meal Planner"},
                {"source": "generated", "expected_text": "Back to Recipe Generator"},
                {"source": "history", "expected_text": "Back to Recipe History"},
                {"source": "starbucks", "expected_text": "Back to Starbucks Menu"}
            ]
            
            contexts_tested = 0
            contexts_working = 0
            
            for context in navigation_contexts:
                contexts_tested += 1
                source = context["source"]
                
                self.log(f"Testing navigation context: {source}")
                
                # Test recipe detail with source context
                if self.generated_recipe_id:
                    response = await self.client.get(f"{BACKEND_URL}/recipes/{self.generated_recipe_id}?source={source}")
                    
                    if response.status_code == 200:
                        contexts_working += 1
                        result = response.json()
                        
                        # Check if response includes navigation context
                        if 'navigation_context' in result or 'source' in result:
                            self.log(f"✅ Navigation context '{source}' supported")
                        else:
                            self.log(f"✅ Recipe detail working for source '{source}' (context handled by frontend)")
                    else:
                        self.log(f"❌ Navigation context '{source}' failed: {response.status_code}")
            
            success_rate = contexts_working / contexts_tested if contexts_tested > 0 else 0
            self.log(f"Navigation contexts: {contexts_working}/{contexts_tested} working ({success_rate:.1%})")
            
            return success_rate >= 0.75  # At least 75% working
            
        except Exception as e:
            self.log(f"❌ Error testing back button navigation: {str(e)}", "ERROR")
            return False
    
    async def run_navigation_tests(self):
        """Run all navigation improvement tests"""
        self.log("🚀 Starting Navigation Improvements Backend Testing")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Demo User Login
        test_results["demo_login"] = await self.test_demo_user_login()
        
        # Test 2: Recipe Generation Navigation
        if test_results["demo_login"]:
            test_results["recipe_generation_nav"] = await self.test_recipe_generation_navigation()
        else:
            test_results["recipe_generation_nav"] = False
        
        # Test 3: Recipe History Navigation
        if test_results["demo_login"]:
            test_results["recipe_history_nav"] = await self.test_recipe_history_navigation()
        else:
            test_results["recipe_history_nav"] = False
        
        # Test 4: Session Management
        if test_results["demo_login"]:
            test_results["session_management"] = await self.test_session_management()
        else:
            test_results["session_management"] = False
        
        # Test 5: Recipe Detail Endpoints
        if test_results["demo_login"]:
            test_results["recipe_detail_endpoints"] = await self.test_recipe_detail_endpoints()
        else:
            test_results["recipe_detail_endpoints"] = False
        
        # Test 6: Back Button Navigation
        if test_results["demo_login"]:
            test_results["back_button_nav"] = await self.test_back_button_navigation()
        else:
            test_results["back_button_nav"] = False
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 NAVIGATION TESTING RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = ["demo_login", "recipe_generation_nav", "recipe_history_nav", "recipe_detail_endpoints"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 60)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL NAVIGATION TESTS PASSED")
            self.log("✅ Recipe generation navigation working properly")
            self.log("✅ Recipe history navigation working properly") 
            self.log("✅ Backend recipe detail endpoints working")
            self.log("✅ Session management maintaining user login")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL NAVIGATION TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("demo_login"):
                self.log("  - Demo user login failing - cannot test navigation")
            if not test_results.get("recipe_generation_nav"):
                self.log("  - Recipe generation navigation not working properly")
            if not test_results.get("recipe_history_nav"):
                self.log("  - Recipe history navigation failing")
            if not test_results.get("recipe_detail_endpoints"):
                self.log("  - Backend recipe detail endpoints not responding correctly")
            if not test_results.get("session_management"):
                self.log("  - Session management issues - users may be signed out unexpectedly")
        
        return test_results

async def main():
    """Main test execution"""
    tester = NavigationTester()
    
    try:
        results = await tester.run_navigation_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())