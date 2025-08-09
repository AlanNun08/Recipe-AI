#!/usr/bin/env python3
"""
Recipe History Endpoint Testing Script
Testing recipe history data structure and recipe ID navigation issues
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Get backend URL from frontend .env
BACKEND_URL = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"

# Demo user credentials from test results
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class RecipeHistoryTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.demo_user_data = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def login_demo_user(self):
        """Login with demo user credentials"""
        self.log("=== Logging in Demo User ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user", {}).get("id")
                self.demo_user_data = result.get("user", {})
                
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {self.user_id}")
                self.log(f"User Name: {self.demo_user_data.get('first_name')} {self.demo_user_data.get('last_name')}")
                self.log(f"Verified: {self.demo_user_data.get('is_verified')}")
                
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error logging in demo user: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_history_endpoint(self):
        """Test the recipe history endpoint for data structure and IDs"""
        self.log("=== Testing Recipe History Endpoint ===")
        
        if not self.user_id:
            self.log("❌ No user ID available for testing")
            return False
        
        try:
            # Test the recipe history endpoint
            response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.user_id}")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Recipe history endpoint responded successfully")
                
                # Check response structure
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"Total recipes in history: {total}")
                self.log(f"Recipes returned: {len(recipes)}")
                
                if not recipes:
                    self.log("⚠️ No recipes found in history - generating a test recipe first")
                    await self.generate_test_recipe()
                    # Retry after generating recipe
                    response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.user_id}")
                    if response.status_code == 200:
                        result = response.json()
                        recipes = result.get("recipes", [])
                        total = result.get("total", 0)
                        self.log(f"After generating recipe - Total: {total}, Returned: {len(recipes)}")
                
                # Analyze recipe data structure
                if recipes:
                    self.log("\n=== RECIPE DATA STRUCTURE ANALYSIS ===")
                    
                    for i, recipe in enumerate(recipes[:3]):  # Analyze first 3 recipes
                        self.log(f"\n--- Recipe {i+1} Analysis ---")
                        
                        # Check for ID field
                        recipe_id = recipe.get("id")
                        self.log(f"Recipe ID: {recipe_id} ({'✅ Present' if recipe_id else '❌ NULL/Missing'})")
                        
                        # Check other key fields
                        title = recipe.get("title") or recipe.get("name")
                        self.log(f"Title/Name: {title}")
                        
                        # Check recipe type/category
                        recipe_type = recipe.get("type") or recipe.get("category") or recipe.get("cuisine_type")
                        self.log(f"Type/Category: {recipe_type}")
                        
                        # Check if it's a Starbucks recipe
                        is_starbucks = any(key in recipe for key in ["drink_name", "base_drink", "ordering_script"])
                        self.log(f"Is Starbucks Recipe: {'✅ Yes' if is_starbucks else '❌ No'}")
                        
                        # Check created date
                        created_at = recipe.get("created_at")
                        self.log(f"Created At: {created_at}")
                        
                        # Log all available fields
                        self.log(f"Available fields: {list(recipe.keys())}")
                        
                        # Test navigation data
                        if recipe_id:
                            self.log(f"✅ Recipe ID available for navigation: {recipe_id}")
                        else:
                            self.log("❌ CRITICAL: Recipe ID is NULL - navigation will fail!")
                            
                            # Check if there's an alternative ID field
                            alt_ids = []
                            for key in recipe.keys():
                                if 'id' in key.lower() and recipe.get(key):
                                    alt_ids.append(f"{key}: {recipe[key]}")
                            
                            if alt_ids:
                                self.log(f"Alternative ID fields found: {alt_ids}")
                            else:
                                self.log("❌ No alternative ID fields found")
                
                return len(recipes) > 0
                
            else:
                self.log(f"❌ Recipe history endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe history endpoint: {str(e)}", "ERROR")
            return False
    
    async def generate_test_recipe(self):
        """Generate a test recipe to ensure we have data"""
        self.log("=== Generating Test Recipe ===")
        
        try:
            recipe_data = {
                "user_id": self.user_id,
                "cuisine_type": "Italian",
                "meal_type": "dinner",
                "difficulty": "medium",
                "prep_time": 30,
                "servings": 4,
                "dietary_preferences": ["Vegetarian"],
                "ingredients_on_hand": ["tomatoes", "basil", "mozzarella"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                recipe_id = result.get("id")
                recipe_title = result.get("title")
                
                self.log(f"✅ Test recipe generated successfully")
                self.log(f"Recipe ID: {recipe_id}")
                self.log(f"Recipe Title: {recipe_title}")
                
                return recipe_id
            else:
                self.log(f"❌ Test recipe generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error generating test recipe: {str(e)}", "ERROR")
            return None
    
    async def test_recipe_detail_endpoint(self, recipe_id: str):
        """Test the recipe detail endpoint with a specific recipe ID"""
        self.log(f"=== Testing Recipe Detail Endpoint with ID: {recipe_id} ===")
        
        try:
            # Test the recipe detail endpoint
            response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Recipe detail endpoint responded successfully")
                
                # Check response structure
                self.log(f"Recipe ID in response: {result.get('id')}")
                self.log(f"Recipe Title: {result.get('title')}")
                self.log(f"Description: {result.get('description', 'N/A')[:100]}...")
                self.log(f"Ingredients count: {len(result.get('ingredients', []))}")
                self.log(f"Instructions count: {len(result.get('instructions', []))}")
                
                # Check all available fields
                self.log(f"Available fields in detail: {list(result.keys())}")
                
                return True
                
            elif response.status_code == 404:
                self.log(f"❌ Recipe not found: {response.text}")
                return False
            else:
                self.log(f"❌ Recipe detail endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe detail endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_vs_regular_recipes(self):
        """Test to identify differences between Starbucks and regular recipes"""
        self.log("=== Testing Starbucks vs Regular Recipe Identification ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.user_id}")
            
            if response.status_code != 200:
                self.log("❌ Could not get recipe history for comparison")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])
            
            starbucks_recipes = []
            regular_recipes = []
            
            for recipe in recipes:
                # Check if it's a Starbucks recipe based on fields
                if any(key in recipe for key in ["drink_name", "base_drink", "ordering_script", "modifications"]):
                    starbucks_recipes.append(recipe)
                else:
                    regular_recipes.append(recipe)
            
            self.log(f"Found {len(starbucks_recipes)} Starbucks recipes")
            self.log(f"Found {len(regular_recipes)} regular recipes")
            
            # Analyze Starbucks recipes
            if starbucks_recipes:
                self.log("\n--- Starbucks Recipe Structure ---")
                sample_starbucks = starbucks_recipes[0]
                self.log(f"Starbucks ID: {sample_starbucks.get('id')}")
                self.log(f"Starbucks fields: {list(sample_starbucks.keys())}")
                
                # Test Starbucks recipe detail endpoint
                starbucks_id = sample_starbucks.get("id")
                if starbucks_id:
                    await self.test_recipe_detail_endpoint(starbucks_id)
            
            # Analyze regular recipes
            if regular_recipes:
                self.log("\n--- Regular Recipe Structure ---")
                sample_regular = regular_recipes[0]
                self.log(f"Regular ID: {sample_regular.get('id')}")
                self.log(f"Regular fields: {list(sample_regular.keys())}")
                
                # Test regular recipe detail endpoint
                regular_id = sample_regular.get("id")
                if regular_id:
                    await self.test_recipe_detail_endpoint(regular_id)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing recipe types: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all recipe history tests"""
        self.log("🚀 Starting Recipe History Endpoint Testing")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Login demo user
        test_results["login"] = await self.login_demo_user()
        
        if not test_results["login"]:
            self.log("❌ Cannot proceed without demo user login")
            return test_results
        
        # Test 2: Recipe history endpoint
        test_results["history_endpoint"] = await self.test_recipe_history_endpoint()
        
        # Test 3: Recipe type identification
        test_results["recipe_types"] = await self.test_starbucks_vs_regular_recipes()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 RECIPE HISTORY TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Overall assessment
        if all(test_results.values()):
            self.log("🎉 ALL TESTS PASSED - Recipe history should be working correctly")
        else:
            self.log("❌ SOME TESTS FAILED - Issues identified with recipe history")
            
            if not test_results.get("history_endpoint"):
                self.log("  - Recipe history endpoint has issues")
            if not test_results.get("recipe_types"):
                self.log("  - Recipe type identification has issues")
        
        return test_results

async def main():
    """Main test execution"""
    tester = RecipeHistoryTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())