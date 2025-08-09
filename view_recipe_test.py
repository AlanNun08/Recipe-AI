#!/usr/bin/env python3
"""
View Recipe Feature Testing Script for Weekly Recipe System
Testing the newly implemented recipe detail endpoint and related functionality
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

# Test configuration using frontend environment URL
BACKEND_URL = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class ViewRecipeFeatureTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.user_id = None
        self.weekly_plan = None
        self.recipe_ids = []
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test 1: Login with demo user credentials"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                user_status = result.get("status")
                
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {self.user_id}")
                self.log(f"Status: {user_status}")
                
                if result.get("is_verified"):
                    self.log("✅ User is verified")
                else:
                    self.log("⚠️ User is not verified")
                
                return True
                
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during demo user login: {str(e)}", "ERROR")
            return False
    
    async def test_trial_status(self):
        """Test 2: Check demo user trial status"""
        self.log("=== Testing Demo User Trial Status ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for trial status test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/user/trial-status/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log(f"✅ Trial status retrieved successfully")
                self.log(f"Has Access: {result.get('has_access')}")
                self.log(f"Trial Active: {result.get('trial_active')}")
                self.log(f"Subscription Status: {result.get('subscription_status')}")
                self.log(f"Trial Days Left: {result.get('trial_days_left')}")
                
                return result.get('has_access', False)
                
            else:
                self.log(f"❌ Trial status check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking trial status: {str(e)}", "ERROR")
            return False
    
    async def test_weekly_recipe_generation(self):
        """Test 3: Generate weekly meal plan with mock data"""
        self.log("=== Testing Weekly Recipe Generation ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for recipe generation")
            return False
        
        try:
            # Test with realistic family preferences
            recipe_request = {
                "user_id": self.user_id,
                "family_size": 4,
                "dietary_preferences": ["vegetarian"],
                "budget": 100.0,
                "cuisines": ["Italian", "Mexican", "Asian"]
            }
            
            self.log(f"Generating weekly meal plan for user: {self.user_id}")
            self.log(f"Request: {recipe_request}")
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=recipe_request)
            
            if response.status_code == 200:
                result = response.json()
                self.weekly_plan = result
                
                self.log(f"✅ Weekly meal plan generated successfully")
                self.log(f"Plan ID: {result.get('id')}")
                self.log(f"Week Of: {result.get('week_of')}")
                self.log(f"Total Budget: ${result.get('total_budget')}")
                
                meals = result.get('meals', [])
                self.log(f"Generated {len(meals)} meals:")
                
                for meal in meals:
                    meal_id = meal.get('id')
                    meal_name = meal.get('name')
                    meal_day = meal.get('day')
                    ingredients_count = len(meal.get('ingredients', []))
                    
                    self.log(f"  {meal_day}: {meal_name} (ID: {meal_id}, {ingredients_count} ingredients)")
                    self.recipe_ids.append(meal_id)
                
                # Test Walmart cart URL
                walmart_url = result.get('walmart_cart_url')
                if walmart_url:
                    self.log(f"✅ Walmart cart URL generated: {walmart_url[:100]}...")
                else:
                    self.log("⚠️ No Walmart cart URL generated")
                
                return len(meals) == 7  # Should have 7 meals for the week
                
            else:
                self.log(f"❌ Weekly recipe generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error generating weekly recipes: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_detail_endpoint(self):
        """Test 4: Test the new GET /api/weekly-recipes/recipe/{recipe_id} endpoint"""
        self.log("=== Testing Recipe Detail Endpoint ===")
        
        if not self.recipe_ids:
            self.log("❌ No recipe IDs available for detail testing")
            return False
        
        successful_tests = 0
        total_tests = min(3, len(self.recipe_ids))  # Test first 3 recipes
        
        for i, recipe_id in enumerate(self.recipe_ids[:total_tests]):
            try:
                self.log(f"Testing recipe detail for ID: {recipe_id}")
                
                response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{recipe_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    self.log(f"✅ Recipe detail retrieved successfully")
                    self.log(f"Recipe Name: {result.get('name')}")
                    self.log(f"Day: {result.get('day')}")
                    self.log(f"Description: {result.get('description', '')[:100]}...")
                    self.log(f"Prep Time: {result.get('prep_time')} minutes")
                    self.log(f"Cook Time: {result.get('cook_time')} minutes")
                    self.log(f"Servings: {result.get('servings')}")
                    self.log(f"Cuisine Type: {result.get('cuisine_type')}")
                    
                    # Test ingredients structure
                    ingredients = result.get('ingredients', [])
                    self.log(f"Ingredients ({len(ingredients)}): {ingredients}")
                    
                    # Test instructions structure
                    instructions = result.get('instructions', [])
                    self.log(f"Instructions ({len(instructions)} steps):")
                    for j, instruction in enumerate(instructions[:3]):  # Show first 3 steps
                        self.log(f"  Step {j+1}: {instruction[:80]}...")
                    
                    # Test Walmart items structure
                    walmart_items = result.get('walmart_items', [])
                    self.log(f"Walmart Items ({len(walmart_items)}):")
                    for item in walmart_items[:3]:  # Show first 3 items
                        self.log(f"  - {item.get('name')}: {item.get('search_url')}")
                    
                    # Test dietary tags
                    dietary_tags = result.get('dietary_tags', [])
                    if dietary_tags:
                        self.log(f"Dietary Tags: {dietary_tags}")
                    
                    # Test nutritional info
                    calories = result.get('calories_per_serving')
                    if calories:
                        self.log(f"Calories per serving: {calories}")
                    
                    successful_tests += 1
                    
                else:
                    self.log(f"❌ Recipe detail failed for {recipe_id}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log(f"❌ Error testing recipe detail for {recipe_id}: {str(e)}", "ERROR")
        
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        self.log(f"Recipe detail endpoint success rate: {successful_tests}/{total_tests} ({success_rate*100:.1f}%)")
        
        return success_rate >= 0.8  # 80% success rate required
    
    async def test_recipe_detail_structure(self):
        """Test 5: Verify recipe detail response structure matches requirements"""
        self.log("=== Testing Recipe Detail Structure ===")
        
        if not self.recipe_ids:
            self.log("❌ No recipe IDs available for structure testing")
            return False
        
        try:
            # Test with first recipe
            recipe_id = self.recipe_ids[0]
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{recipe_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe for structure test: {response.status_code}")
                return False
            
            result = response.json()
            
            # Required fields according to review request
            required_fields = [
                'id', 'name', 'description', 'day', 'ingredients', 'instructions',
                'prep_time', 'cook_time', 'servings', 'cuisine_type', 'walmart_items'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in result:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log(f"❌ Missing required fields: {missing_fields}")
                return False
            
            self.log("✅ All required fields present")
            
            # Test walmart_items structure
            walmart_items = result.get('walmart_items', [])
            if not walmart_items:
                self.log("❌ No Walmart items found")
                return False
            
            # Check first Walmart item structure
            first_item = walmart_items[0]
            walmart_required_fields = ['name', 'search_url']
            
            for field in walmart_required_fields:
                if field not in first_item:
                    self.log(f"❌ Missing Walmart item field: {field}")
                    return False
            
            self.log("✅ Walmart items structure is correct")
            
            # Test that each ingredient has a corresponding Walmart item
            ingredients = result.get('ingredients', [])
            if len(walmart_items) != len(ingredients):
                self.log(f"⚠️ Walmart items count ({len(walmart_items)}) doesn't match ingredients count ({len(ingredients)})")
            else:
                self.log("✅ Each ingredient has a corresponding Walmart item")
            
            # Test URL format
            for item in walmart_items[:3]:  # Check first 3
                url = item.get('search_url', '')
                if not url.startswith('https://www.walmart.com/search/'):
                    self.log(f"⚠️ Unexpected Walmart URL format: {url}")
                else:
                    self.log(f"✅ Walmart URL format correct: {url}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing recipe detail structure: {str(e)}", "ERROR")
            return False
    
    async def test_error_handling(self):
        """Test 6: Test error handling for non-existent recipe IDs"""
        self.log("=== Testing Error Handling ===")
        
        try:
            # Test with non-existent recipe ID
            fake_recipe_id = "non-existent-recipe-id-12345"
            
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{fake_recipe_id}")
            
            if response.status_code == 404:
                self.log("✅ Correctly returns 404 for non-existent recipe ID")
                
                try:
                    error_response = response.json()
                    if 'detail' in error_response:
                        self.log(f"✅ Error message provided: {error_response['detail']}")
                    else:
                        self.log("⚠️ No error detail provided")
                except:
                    self.log("⚠️ Error response is not JSON")
                
                return True
                
            else:
                self.log(f"❌ Expected 404, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing error handling: {str(e)}", "ERROR")
            return False
    
    async def test_walmart_integration(self):
        """Test 7: Verify Walmart item links are properly generated"""
        self.log("=== Testing Walmart Integration ===")
        
        if not self.recipe_ids:
            self.log("❌ No recipe IDs available for Walmart testing")
            return False
        
        try:
            # Test with first recipe
            recipe_id = self.recipe_ids[0]
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{recipe_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe for Walmart test: {response.status_code}")
                return False
            
            result = response.json()
            walmart_items = result.get('walmart_items', [])
            
            if not walmart_items:
                self.log("❌ No Walmart items found")
                return False
            
            self.log(f"Testing {len(walmart_items)} Walmart items")
            
            valid_urls = 0
            for item in walmart_items:
                name = item.get('name', '')
                url = item.get('search_url', '')
                
                # Check URL format
                if url.startswith('https://www.walmart.com/search/'):
                    valid_urls += 1
                    self.log(f"✅ {name}: {url}")
                else:
                    self.log(f"❌ Invalid URL for {name}: {url}")
            
            success_rate = valid_urls / len(walmart_items) if walmart_items else 0
            self.log(f"Walmart URL success rate: {valid_urls}/{len(walmart_items)} ({success_rate*100:.1f}%)")
            
            return success_rate >= 0.9  # 90% success rate required
            
        except Exception as e:
            self.log(f"❌ Error testing Walmart integration: {str(e)}", "ERROR")
            return False
    
    async def test_current_weekly_plan(self):
        """Test 8: Test GET /api/weekly-recipes/current/{user_id} endpoint"""
        self.log("=== Testing Current Weekly Plan Endpoint ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for current plan test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Current weekly plan retrieved successfully")
                self.log(f"Has Plan: {result.get('has_plan')}")
                self.log(f"Current Week: {result.get('current_week')}")
                
                if result.get('has_plan'):
                    plan = result.get('plan', {})
                    meals = plan.get('meals', [])
                    self.log(f"Plan contains {len(meals)} meals")
                    
                    return len(meals) > 0
                else:
                    self.log("⚠️ No current plan found")
                    return True  # This is acceptable
                
            else:
                self.log(f"❌ Current weekly plan failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing current weekly plan: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all View Recipe feature tests"""
        self.log("🚀 Starting View Recipe Feature Comprehensive Testing")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Demo User Login
        test_results["demo_login"] = await self.test_demo_user_login()
        
        # Test 2: Trial Status Check
        if test_results["demo_login"]:
            test_results["trial_status"] = await self.test_trial_status()
        else:
            test_results["trial_status"] = False
        
        # Test 3: Weekly Recipe Generation
        if test_results["trial_status"]:
            test_results["recipe_generation"] = await self.test_weekly_recipe_generation()
        else:
            test_results["recipe_generation"] = False
        
        # Test 4: Recipe Detail Endpoint
        if test_results["recipe_generation"]:
            test_results["recipe_detail"] = await self.test_recipe_detail_endpoint()
        else:
            test_results["recipe_detail"] = False
        
        # Test 5: Recipe Detail Structure
        if test_results["recipe_detail"]:
            test_results["detail_structure"] = await self.test_recipe_detail_structure()
        else:
            test_results["detail_structure"] = False
        
        # Test 6: Error Handling
        test_results["error_handling"] = await self.test_error_handling()
        
        # Test 7: Walmart Integration
        if test_results["recipe_detail"]:
            test_results["walmart_integration"] = await self.test_walmart_integration()
        else:
            test_results["walmart_integration"] = False
        
        # Test 8: Current Weekly Plan
        if test_results["demo_login"]:
            test_results["current_plan"] = await self.test_current_weekly_plan()
        else:
            test_results["current_plan"] = False
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 VIEW RECIPE FEATURE TEST RESULTS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = ["demo_login", "trial_status", "recipe_generation", "recipe_detail", "detail_structure", "walmart_integration"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED - View Recipe feature is working correctly")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("demo_login"):
                self.log("  - Demo user login failing")
            if not test_results.get("trial_status"):
                self.log("  - Trial status check failing")
            if not test_results.get("recipe_generation"):
                self.log("  - Weekly recipe generation failing")
            if not test_results.get("recipe_detail"):
                self.log("  - Recipe detail endpoint failing")
            if not test_results.get("detail_structure"):
                self.log("  - Recipe detail structure incorrect")
            if not test_results.get("walmart_integration"):
                self.log("  - Walmart item links not working properly")
        
        return test_results

async def main():
    """Main test execution"""
    tester = ViewRecipeFeatureTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())