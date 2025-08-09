#!/usr/bin/env python3
"""
Frontend Navigation Flow Test for Weekly Recipe System
Testing the specific navigation issue: WeeklyRecipesScreen → RecipeDetailScreen
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com') + '/api'

# Demo user credentials
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class FrontendNavigationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.user_id = None
        
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
                self.user_id = result.get("user_id")
                self.log(f"✅ Demo user authenticated successfully")
                self.log(f"User ID: {self.user_id}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    async def simulate_frontend_navigation_flow(self):
        """Simulate the exact frontend navigation flow"""
        self.log("=== Simulating Frontend Navigation Flow ===")
        
        try:
            # Step 1: Get current weekly plan (simulating WeeklyRecipesScreen load)
            self.log("Step 1: Loading WeeklyRecipesScreen - Getting current weekly plan")
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get current plan: {response.status_code}")
                return False
            
            result = response.json()
            if not result.get("has_plan", False):
                self.log("❌ No current weekly plan found")
                return False
            
            plan = result.get("plan", {})
            meals = plan.get("meals", [])
            
            if not meals:
                self.log("❌ No meals in current plan")
                return False
            
            self.log(f"✅ WeeklyRecipesScreen loaded with {len(meals)} meals")
            
            # Step 2: Simulate clicking "View Full Recipe" button
            first_meal = meals[0]
            meal_id = first_meal.get("id")
            meal_name = first_meal.get("name")
            meal_day = first_meal.get("day")
            
            self.log(f"Step 2: User clicks 'View Full Recipe' for {meal_day}: {meal_name}")
            self.log(f"Frontend calls onViewRecipe('{meal_id}')")
            
            # Step 3: Simulate frontend state management
            self.log("Step 3: Frontend sets currentRecipeId and switches to 'recipe-detail' screen")
            self.log(f"currentRecipeId = '{meal_id}'")
            self.log("currentScreen = 'recipe-detail'")
            
            # Step 4: Simulate RecipeDetailScreen component loading
            self.log("Step 4: RecipeDetailScreen component loads with recipeId prop")
            self.log(f"RecipeDetailScreen receives recipeId: '{meal_id}'")
            
            # Step 5: Simulate the API call that RecipeDetailScreen makes
            self.log("Step 5: RecipeDetailScreen calls loadRecipeDetail()")
            self.log(f"Making API call: GET /api/weekly-recipes/recipe/{meal_id}")
            
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{meal_id}")
            
            if response.status_code == 200:
                recipe_data = response.json()
                returned_name = recipe_data.get("name")
                returned_day = recipe_data.get("day")
                ingredients_count = len(recipe_data.get("ingredients", []))
                walmart_items_count = len(recipe_data.get("walmart_items", []))
                
                self.log("✅ SUCCESS: RecipeDetailScreen successfully loaded recipe data")
                self.log(f"  Recipe name: {returned_name}")
                self.log(f"  Day: {returned_day}")
                self.log(f"  Ingredients: {ingredients_count}")
                self.log(f"  Walmart items: {walmart_items_count}")
                
                # Verify data consistency
                if returned_name == meal_name and returned_day == meal_day:
                    self.log("✅ Data consistency verified - names and days match")
                    return True
                else:
                    self.log("⚠️ Data inconsistency detected:")
                    self.log(f"  Expected: {meal_name} ({meal_day})")
                    self.log(f"  Received: {returned_name} ({returned_day})")
                    return False
                    
            elif response.status_code == 404:
                self.log("❌ CRITICAL: Recipe detail endpoint returned 404")
                self.log("This would cause 'No Recipe Found' error in frontend")
                return False
            else:
                self.log(f"❌ Recipe detail endpoint error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Navigation flow simulation error: {str(e)}", "ERROR")
            return False
    
    async def test_multiple_recipes(self):
        """Test navigation flow for multiple recipes"""
        self.log("=== Testing Multiple Recipe Navigation ===")
        
        try:
            # Get current weekly plan
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            result = response.json()
            meals = result.get("plan", {}).get("meals", [])
            
            success_count = 0
            total_count = len(meals)
            
            for i, meal in enumerate(meals):
                meal_id = meal.get("id")
                meal_name = meal.get("name")
                meal_day = meal.get("day")
                
                self.log(f"Testing recipe {i+1}/{total_count}: {meal_day} - {meal_name}")
                
                # Simulate the navigation flow for this recipe
                response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{meal_id}")
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    walmart_items = recipe_data.get("walmart_items", [])
                    
                    self.log(f"  ✅ SUCCESS: Recipe loaded with {len(walmart_items)} Walmart items")
                    success_count += 1
                else:
                    self.log(f"  ❌ FAILED: {response.status_code} - Recipe not accessible")
            
            self.log(f"\nNavigation Test Results: {success_count}/{total_count} recipes accessible")
            
            if success_count == total_count:
                self.log("✅ ALL RECIPES ACCESSIBLE - Navigation should work perfectly")
                return True
            else:
                self.log("❌ SOME RECIPES INACCESSIBLE - This would cause navigation failures")
                return False
                
        except Exception as e:
            self.log(f"❌ Multiple recipe test error: {str(e)}", "ERROR")
            return False
    
    async def test_walmart_shopping_buttons(self):
        """Test that Walmart shopping buttons would display correctly"""
        self.log("=== Testing Walmart Shopping Button Data ===")
        
        try:
            # Get first recipe
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            result = response.json()
            meals = result.get("plan", {}).get("meals", [])
            
            if not meals:
                self.log("❌ No meals to test")
                return False
            
            first_meal = meals[0]
            meal_id = first_meal.get("id")
            
            # Get recipe detail
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{meal_id}")
            
            if response.status_code != 200:
                self.log("❌ Cannot get recipe detail for Walmart button test")
                return False
            
            recipe_data = response.json()
            walmart_items = recipe_data.get("walmart_items", [])
            
            self.log(f"Recipe has {len(walmart_items)} Walmart items")
            
            if not walmart_items:
                self.log("❌ No Walmart items - shopping buttons would not display")
                return False
            
            # Check each Walmart item structure
            valid_items = 0
            for i, item in enumerate(walmart_items):
                name = item.get("name")
                search_url = item.get("search_url")
                image_url = item.get("image_url")
                estimated_price = item.get("estimated_price")
                
                if name and search_url and estimated_price:
                    self.log(f"  Item {i+1}: {name} - {estimated_price}")
                    self.log(f"    URL: {search_url}")
                    valid_items += 1
                else:
                    self.log(f"  Item {i+1}: ❌ Missing required fields")
            
            self.log(f"\nWalmart Button Test: {valid_items}/{len(walmart_items)} items have valid data")
            
            if valid_items == len(walmart_items):
                self.log("✅ ALL WALMART ITEMS VALID - Shopping buttons would display correctly")
                return True
            else:
                self.log("❌ SOME WALMART ITEMS INVALID - Some shopping buttons would not work")
                return False
                
        except Exception as e:
            self.log(f"❌ Walmart button test error: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_navigation_test(self):
        """Run comprehensive frontend navigation test"""
        self.log("🔍 Starting Frontend Navigation Flow Test")
        self.log("=" * 70)
        
        # Step 1: Authenticate
        if not await self.authenticate_demo_user():
            self.log("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Test main navigation flow
        self.log("\n" + "=" * 50)
        self.log("MAIN NAVIGATION FLOW TEST")
        self.log("=" * 50)
        
        main_flow_success = await self.simulate_frontend_navigation_flow()
        
        # Step 3: Test multiple recipes
        self.log("\n" + "=" * 50)
        self.log("MULTIPLE RECIPE NAVIGATION TEST")
        self.log("=" * 50)
        
        multiple_recipes_success = await self.test_multiple_recipes()
        
        # Step 4: Test Walmart shopping buttons
        self.log("\n" + "=" * 50)
        self.log("WALMART SHOPPING BUTTONS TEST")
        self.log("=" * 50)
        
        walmart_buttons_success = await self.test_walmart_shopping_buttons()
        
        # Final summary
        self.log("\n" + "=" * 70)
        self.log("🔍 FRONTEND NAVIGATION TEST SUMMARY")
        self.log("=" * 70)
        
        if main_flow_success and multiple_recipes_success and walmart_buttons_success:
            self.log("✅ ALL NAVIGATION TESTS PASSED")
            self.log("The frontend navigation flow should work correctly.")
            self.log("The reported 'No Recipe Found' issue is likely NOT due to backend problems.")
            self.log("The issue may be in frontend state management, caching, or timing.")
            
            self.log("\nPOSSIBLE FRONTEND ISSUES TO INVESTIGATE:")
            self.log("1. React state not updating correctly between screens")
            self.log("2. currentRecipeId being reset or overwritten")
            self.log("3. Component re-rendering issues")
            self.log("4. Browser caching of old data")
            self.log("5. Race conditions in state updates")
            
        else:
            self.log("❌ SOME NAVIGATION TESTS FAILED")
            self.log("This indicates backend issues that could cause frontend problems.")
            
            if not main_flow_success:
                self.log("- Main navigation flow failed")
            if not multiple_recipes_success:
                self.log("- Multiple recipe access failed")
            if not walmart_buttons_success:
                self.log("- Walmart shopping button data incomplete")
        
        return main_flow_success and multiple_recipes_success and walmart_buttons_success

async def main():
    """Main test execution"""
    tester = FrontendNavigationTester()
    
    try:
        success = await tester.run_comprehensive_navigation_test()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    result = asyncio.run(main())