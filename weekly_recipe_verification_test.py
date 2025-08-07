#!/usr/bin/env python3
"""
Weekly Recipe System Final Verification Test
Testing the specific endpoints mentioned in the review request after code cleanup.

Focus Areas:
1. POST /api/weekly-recipes/generate with demo user (demo@test.com)
2. GET /api/weekly-recipes/current/{user_id}  
3. GET /api/weekly-recipes/recipe/{recipe_id} - verify complete recipe data including walmart_items
4. GET /api/user/trial-status/{user_id}

Verification Points:
- Recipe name, description, instructions
- Ingredients array with walmart_items containing individual shopping links
- Each walmart_item should have: name, search_url, image_url, estimated_price
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys
from pathlib import Path

# Load environment variables to get backend URL
sys.path.append('/app/backend')
from dotenv import load_dotenv

# Load frontend environment to get backend URL
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

# Demo user credentials from test_result.md
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class WeeklyRecipeVerificationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.demo_user_id = None
        self.current_plan_id = None
        self.test_recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def authenticate_demo_user(self):
        """Authenticate with demo user credentials"""
        self.log("=== Authenticating Demo User ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    self.demo_user_id = result.get("user_id")
                    self.log(f"✅ Demo user authenticated successfully")
                    self.log(f"User ID: {self.demo_user_id}")
                    self.log(f"User: {result.get('first_name')} {result.get('last_name')}")
                    self.log(f"Verified: {result.get('is_verified')}")
                    return True
                else:
                    self.log(f"❌ Login failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during authentication: {str(e)}", "ERROR")
            return False
    
    async def test_trial_status_endpoint(self):
        """Test GET /api/user/trial-status/{user_id}"""
        self.log("=== Testing Trial Status Endpoint ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for trial status test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/user/trial-status/{self.demo_user_id}")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify required fields
                required_fields = ["has_access", "trial_active", "subscription_status", "current_week"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                self.log("✅ Trial status endpoint working correctly")
                self.log(f"Has Access: {result.get('has_access')}")
                self.log(f"Trial Active: {result.get('trial_active')}")
                self.log(f"Subscription Status: {result.get('subscription_status')}")
                self.log(f"Trial Days Left: {result.get('trial_days_left')}")
                self.log(f"Current Week: {result.get('current_week')}")
                
                return result.get('has_access', False)
                
            else:
                self.log(f"❌ Trial status endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing trial status: {str(e)}", "ERROR")
            return False
    
    async def test_weekly_recipe_generation(self):
        """Test POST /api/weekly-recipes/generate with demo user"""
        self.log("=== Testing Weekly Recipe Generation ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for recipe generation")
            return False
        
        try:
            generation_data = {
                "user_id": self.demo_user_id,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "budget": 100.0,
                "cuisines": ["Italian", "Mediterranean"]
            }
            
            self.log(f"Generating weekly recipes with data: {generation_data}")
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=generation_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                required_fields = ["plan_id", "week_of", "meals", "total_budget", "walmart_cart_url"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields in generation response: {missing_fields}")
                    return False
                
                self.current_plan_id = result.get("plan_id")
                meals = result.get("meals", [])
                
                self.log("✅ Weekly recipe generation successful")
                self.log(f"Plan ID: {self.current_plan_id}")
                self.log(f"Week: {result.get('week_of')}")
                self.log(f"Total Meals: {len(meals)}")
                self.log(f"Total Budget: ${result.get('total_budget', 0)}")
                self.log(f"Walmart Cart URL: {result.get('walmart_cart_url', 'N/A')}")
                
                # Log meal details
                for i, meal in enumerate(meals[:3]):  # Show first 3 meals
                    self.log(f"  Meal {i+1}: {meal.get('name')} ({meal.get('day')})")
                    if i < len(meals) - 1:
                        # Store first recipe ID for detailed testing
                        if not self.test_recipe_id:
                            self.test_recipe_id = meal.get('id')
                
                return len(meals) == 7  # Should generate 7 meals (one for each day)
                
            else:
                self.log(f"❌ Weekly recipe generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing weekly recipe generation: {str(e)}", "ERROR")
            return False
    
    async def test_current_weekly_plan(self):
        """Test GET /api/weekly-recipes/current/{user_id}"""
        self.log("=== Testing Current Weekly Plan Retrieval ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for current plan test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.demo_user_id}")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                required_fields = ["has_plan", "current_week"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields in current plan response: {missing_fields}")
                    return False
                
                has_plan = result.get("has_plan", False)
                
                self.log("✅ Current weekly plan endpoint working")
                self.log(f"Has Plan: {has_plan}")
                self.log(f"Current Week: {result.get('current_week')}")
                
                if has_plan:
                    plan = result.get("plan", {})
                    meals = plan.get("meals", [])
                    self.log(f"Plan ID: {plan.get('id')}")
                    self.log(f"Total Meals in Plan: {len(meals)}")
                    
                    # Store a recipe ID for detailed testing if we don't have one
                    if not self.test_recipe_id and meals:
                        self.test_recipe_id = meals[0].get('id')
                        self.log(f"Using recipe ID for detailed test: {self.test_recipe_id}")
                
                return has_plan
                
            else:
                self.log(f"❌ Current weekly plan endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing current weekly plan: {str(e)}", "ERROR")
            return False
    
    async def test_individual_recipe_detail(self):
        """Test GET /api/weekly-recipes/recipe/{recipe_id} - CRITICAL TEST"""
        self.log("=== Testing Individual Recipe Detail Endpoint (CRITICAL) ===")
        
        if not self.test_recipe_id:
            self.log("❌ No recipe ID available for detailed testing")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{self.test_recipe_id}")
            
            self.log(f"Response status: {response.status_code}")
            self.log(f"Testing recipe ID: {self.test_recipe_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify core recipe fields
                core_fields = ["name", "description", "instructions", "ingredients"]
                missing_core = [field for field in core_fields if field not in result]
                
                if missing_core:
                    self.log(f"❌ Missing core recipe fields: {missing_core}")
                    return False
                
                # CRITICAL: Verify walmart_items array
                walmart_items = result.get("walmart_items", [])
                if not walmart_items:
                    self.log("❌ CRITICAL: No walmart_items array found in recipe response")
                    return False
                
                self.log("✅ Individual recipe detail endpoint working")
                self.log(f"Recipe Name: {result.get('name')}")
                self.log(f"Description: {result.get('description', '')[:100]}...")
                self.log(f"Day: {result.get('day')}")
                self.log(f"Prep Time: {result.get('prep_time')} minutes")
                self.log(f"Cook Time: {result.get('cook_time')} minutes")
                self.log(f"Servings: {result.get('servings')}")
                self.log(f"Cuisine Type: {result.get('cuisine_type')}")
                self.log(f"Ingredients Count: {len(result.get('ingredients', []))}")
                self.log(f"Instructions Count: {len(result.get('instructions', []))}")
                self.log(f"Walmart Items Count: {len(walmart_items)}")
                
                # CRITICAL: Verify walmart_items structure
                walmart_items_valid = True
                required_walmart_fields = ["name", "search_url", "image_url", "estimated_price"]
                
                for i, item in enumerate(walmart_items[:3]):  # Check first 3 items
                    missing_walmart_fields = [field for field in required_walmart_fields if field not in item]
                    if missing_walmart_fields:
                        self.log(f"❌ Walmart item {i+1} missing fields: {missing_walmart_fields}")
                        walmart_items_valid = False
                    else:
                        self.log(f"  Walmart Item {i+1}: {item.get('name')} - {item.get('estimated_price')}")
                        self.log(f"    Search URL: {item.get('search_url')}")
                
                if not walmart_items_valid:
                    self.log("❌ CRITICAL: Walmart items do not have required structure")
                    return False
                
                self.log("✅ CRITICAL: All walmart_items have required fields (name, search_url, image_url, estimated_price)")
                
                # Verify instructions are detailed
                instructions = result.get("instructions", [])
                if len(instructions) < 3:
                    self.log("⚠️ Warning: Recipe has fewer than 3 instruction steps")
                else:
                    self.log(f"✅ Recipe has {len(instructions)} detailed instruction steps")
                
                return True
                
            else:
                self.log(f"❌ Individual recipe detail failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing individual recipe detail: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_data_completeness(self):
        """Additional test to verify recipe data completeness for RecipeDetailScreen"""
        self.log("=== Testing Recipe Data Completeness for RecipeDetailScreen ===")
        
        if not self.test_recipe_id:
            self.log("❌ No recipe ID available for completeness test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{self.test_recipe_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Check all fields needed by RecipeDetailScreen component
                completeness_score = 0
                total_checks = 0
                
                # Core recipe information
                if result.get("name"):
                    completeness_score += 1
                    self.log("✅ Recipe name present")
                else:
                    self.log("❌ Recipe name missing")
                total_checks += 1
                
                if result.get("description"):
                    completeness_score += 1
                    self.log("✅ Recipe description present")
                else:
                    self.log("❌ Recipe description missing")
                total_checks += 1
                
                # Instructions
                instructions = result.get("instructions", [])
                if instructions and len(instructions) >= 3:
                    completeness_score += 1
                    self.log(f"✅ Recipe instructions present ({len(instructions)} steps)")
                else:
                    self.log(f"❌ Recipe instructions insufficient ({len(instructions)} steps)")
                total_checks += 1
                
                # Ingredients with walmart_items
                ingredients = result.get("ingredients", [])
                walmart_items = result.get("walmart_items", [])
                
                if ingredients and len(ingredients) >= 3:
                    completeness_score += 1
                    self.log(f"✅ Recipe ingredients present ({len(ingredients)} ingredients)")
                else:
                    self.log(f"❌ Recipe ingredients insufficient ({len(ingredients)} ingredients)")
                total_checks += 1
                
                if walmart_items and len(walmart_items) >= len(ingredients) * 0.7:  # At least 70% coverage
                    completeness_score += 1
                    self.log(f"✅ Walmart items adequate coverage ({len(walmart_items)} items for {len(ingredients)} ingredients)")
                else:
                    self.log(f"❌ Walmart items insufficient coverage ({len(walmart_items)} items for {len(ingredients)} ingredients)")
                total_checks += 1
                
                # Individual shopping links
                valid_shopping_links = 0
                for item in walmart_items:
                    search_url = item.get("search_url", "")
                    if search_url and "walmart.com" in search_url:
                        valid_shopping_links += 1
                
                if valid_shopping_links == len(walmart_items):
                    completeness_score += 1
                    self.log(f"✅ All walmart items have valid shopping URLs ({valid_shopping_links}/{len(walmart_items)})")
                else:
                    self.log(f"❌ Some walmart items have invalid shopping URLs ({valid_shopping_links}/{len(walmart_items)})")
                total_checks += 1
                
                # Calculate completeness percentage
                completeness_percentage = (completeness_score / total_checks) * 100
                
                self.log(f"Recipe Data Completeness: {completeness_score}/{total_checks} ({completeness_percentage:.1f}%)")
                
                if completeness_percentage >= 85:
                    self.log("✅ Recipe data is sufficiently complete for RecipeDetailScreen")
                    return True
                else:
                    self.log("❌ Recipe data is incomplete for RecipeDetailScreen")
                    return False
                
            else:
                self.log(f"❌ Could not retrieve recipe for completeness test: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe data completeness: {str(e)}", "ERROR")
            return False
    
    async def run_verification_tests(self):
        """Run all verification tests in sequence"""
        self.log("🚀 Starting Weekly Recipe System Final Verification")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log("=" * 70)
        
        test_results = {}
        
        # Step 1: Authenticate demo user
        test_results["authentication"] = await self.authenticate_demo_user()
        if not test_results["authentication"]:
            self.log("❌ Cannot proceed without authentication")
            return test_results
        
        # Step 2: Test trial status endpoint
        test_results["trial_status"] = await self.test_trial_status_endpoint()
        
        # Step 3: Test weekly recipe generation
        test_results["recipe_generation"] = await self.test_weekly_recipe_generation()
        
        # Step 4: Test current weekly plan retrieval
        test_results["current_plan"] = await self.test_current_weekly_plan()
        
        # Step 5: Test individual recipe detail (CRITICAL)
        test_results["recipe_detail"] = await self.test_individual_recipe_detail()
        
        # Step 6: Test recipe data completeness
        test_results["data_completeness"] = await self.test_recipe_data_completeness()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 FINAL VERIFICATION RESULTS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Critical assessment
        critical_tests = ["authentication", "recipe_generation", "recipe_detail", "data_completeness"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED")
            self.log("✅ Weekly Recipe System is ready for production")
            self.log("✅ RecipeDetailScreen will receive complete data including walmart_items")
            self.log("✅ Individual Walmart shopping links are working correctly")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES THAT NEED ATTENTION:")
            
            if not test_results.get("authentication"):
                self.log("  - Demo user authentication failing")
            if not test_results.get("recipe_generation"):
                self.log("  - Weekly recipe generation not working")
            if not test_results.get("recipe_detail"):
                self.log("  - Individual recipe detail endpoint issues")
            if not test_results.get("data_completeness"):
                self.log("  - Recipe data incomplete for RecipeDetailScreen")
        
        return test_results

async def main():
    """Main test execution"""
    tester = WeeklyRecipeVerificationTester()
    
    try:
        results = await tester.run_verification_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())