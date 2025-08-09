#!/usr/bin/env python3
"""
Detailed Recipe History Navigation Testing
Generate French recipes with chicken, mushrooms, onions and test navigation
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

class DetailedRecipeHistoryTester:
    def __init__(self):
        # Use the external URL from frontend/.env
        self.backend_url = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Demo user credentials
        self.demo_email = "demo@test.com"
        self.demo_password = "password123"
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
        self.generated_recipe_ids = []
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def login_demo_user(self):
        """Login as demo user"""
        try:
            login_data = {
                "email": self.demo_email,
                "password": self.demo_password
            }
            
            response = await self.client.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("user", {}).get("id")
                self.log(f"✅ Demo user logged in successfully: {user_id}")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    async def generate_french_chicken_recipe(self):
        """Generate a French recipe with chicken, mushrooms, and onions"""
        self.log("=== Generating French Chicken Recipe ===")
        
        try:
            recipe_data = {
                "user_id": self.demo_user_id,
                "cuisine_type": "French",
                "meal_type": "dinner",
                "difficulty": "medium",
                "prep_time": 30,
                "servings": 4,
                "dietary_preferences": [],
                "ingredients_on_hand": ["chicken", "mushrooms", "onions", "garlic", "white wine", "cream"]
            }
            
            response = await self.client.post(f"{self.backend_url}/recipes/generate", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                recipe_id = result.get("id")
                recipe_title = result.get("title")
                ingredients = result.get("ingredients", [])
                
                self.log(f"✅ French recipe generated successfully")
                self.log(f"Recipe ID: {recipe_id}")
                self.log(f"Title: {recipe_title}")
                self.log(f"Ingredients: {ingredients[:5]}...")  # First 5 ingredients
                
                # Check if it contains our target ingredients
                ingredient_text = " ".join(ingredients).lower()
                has_chicken = "chicken" in ingredient_text
                has_mushroom = "mushroom" in ingredient_text
                has_onion = "onion" in ingredient_text
                
                self.log(f"Contains chicken: {has_chicken}")
                self.log(f"Contains mushroom: {has_mushroom}")
                self.log(f"Contains onion: {has_onion}")
                
                if recipe_id:
                    self.generated_recipe_ids.append(recipe_id)
                
                return True, recipe_id, result
            else:
                self.log(f"❌ Recipe generation failed: {response.status_code} - {response.text}")
                return False, None, None
                
        except Exception as e:
            self.log(f"❌ Error generating recipe: {str(e)}", "ERROR")
            return False, None, None
    
    async def test_recipe_history_after_generation(self):
        """Test recipe history after generating new recipes"""
        self.log("=== Testing Recipe History After Generation ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Recipe history retrieved")
                self.log(f"Total recipes: {total}")
                self.log(f"Recipes in response: {len(recipes)}")
                
                # Look for our generated recipes
                found_generated = []
                french_recipes = []
                chicken_mushroom_onion_recipes = []
                
                for recipe in recipes:
                    recipe_id = recipe.get("id")
                    title = recipe.get("title", "").lower()
                    description = recipe.get("description", "").lower()
                    ingredients = recipe.get("ingredients", [])
                    cuisine_type = recipe.get("cuisine_type", "").lower()
                    recipe_type = recipe.get("type", "unknown")
                    
                    # Check if this is one of our generated recipes
                    if recipe_id in self.generated_recipe_ids:
                        found_generated.append(recipe)
                        self.log(f"✅ Found generated recipe in history: {recipe.get('title')}")
                    
                    # Check for French cuisine
                    if "french" in cuisine_type or "french" in title:
                        french_recipes.append(recipe)
                    
                    # Check for chicken, mushroom, onion ingredients
                    ingredient_text = " ".join(ingredients).lower() if ingredients else ""
                    full_text = f"{title} {description} {ingredient_text}"
                    
                    if ("chicken" in full_text and "mushroom" in full_text and "onion" in full_text):
                        chicken_mushroom_onion_recipes.append(recipe)
                
                self.log(f"Generated recipes found in history: {len(found_generated)}")
                self.log(f"French recipes found: {len(french_recipes)}")
                self.log(f"Chicken+Mushroom+Onion recipes found: {len(chicken_mushroom_onion_recipes)}")
                
                return True, recipes, french_recipes, chicken_mushroom_onion_recipes
                
            else:
                self.log(f"❌ Recipe history failed: {response.status_code}")
                return False, [], [], []
                
        except Exception as e:
            self.log(f"❌ Error getting recipe history: {str(e)}", "ERROR")
            return False, [], [], []
    
    async def test_recipe_detail_navigation(self, target_recipes: List[Dict]):
        """Test navigation from recipe history to recipe detail"""
        self.log("=== Testing Recipe Detail Navigation ===")
        
        if not target_recipes:
            self.log("⚠️ No target recipes to test navigation")
            return True
        
        navigation_results = []
        
        for recipe in target_recipes:
            recipe_id = recipe.get("id")
            recipe_title = recipe.get("title")
            recipe_type = recipe.get("type", "unknown")
            
            self.log(f"Testing navigation for: {recipe_title}")
            self.log(f"  Recipe ID: {recipe_id}")
            self.log(f"  Recipe Type: {recipe_type}")
            
            try:
                # Test the recipe detail endpoint (this is what frontend calls)
                response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verify the response has all required fields
                    required_fields = ["id", "title", "description", "ingredients", "instructions"]
                    missing_fields = [field for field in required_fields if not result.get(field)]
                    
                    if missing_fields:
                        self.log(f"❌ Recipe detail missing required fields: {missing_fields}")
                        navigation_results.append({
                            "recipe_id": recipe_id,
                            "title": recipe_title,
                            "status": "incomplete_data",
                            "missing_fields": missing_fields
                        })
                    else:
                        self.log(f"✅ Recipe detail navigation successful")
                        self.log(f"  Retrieved title: {result.get('title')}")
                        self.log(f"  Ingredients count: {len(result.get('ingredients', []))}")
                        self.log(f"  Instructions count: {len(result.get('instructions', []))}")
                        
                        # Verify the content matches what we expect
                        retrieved_title = result.get("title", "")
                        if retrieved_title.lower() != recipe_title.lower():
                            self.log(f"⚠️ Title mismatch - Expected: {recipe_title}, Got: {retrieved_title}")
                        
                        navigation_results.append({
                            "recipe_id": recipe_id,
                            "title": recipe_title,
                            "status": "success",
                            "retrieved_title": retrieved_title,
                            "ingredients_count": len(result.get('ingredients', [])),
                            "instructions_count": len(result.get('instructions', []))
                        })
                
                elif response.status_code == 404:
                    self.log(f"❌ Recipe not found (404) - This is the navigation issue!")
                    self.log(f"  This means the recipe exists in history but can't be retrieved via detail endpoint")
                    navigation_results.append({
                        "recipe_id": recipe_id,
                        "title": recipe_title,
                        "status": "not_found_404",
                        "error": "Recipe exists in history but not accessible via detail endpoint"
                    })
                
                elif response.status_code == 500:
                    self.log(f"❌ Server error (500) - Backend issue")
                    self.log(f"  Error response: {response.text}")
                    navigation_results.append({
                        "recipe_id": recipe_id,
                        "title": recipe_title,
                        "status": "server_error_500",
                        "error": response.text
                    })
                
                else:
                    self.log(f"❌ Unexpected status code: {response.status_code}")
                    navigation_results.append({
                        "recipe_id": recipe_id,
                        "title": recipe_title,
                        "status": f"unexpected_{response.status_code}",
                        "error": response.text
                    })
                
            except Exception as e:
                self.log(f"❌ Exception during navigation test: {str(e)}", "ERROR")
                navigation_results.append({
                    "recipe_id": recipe_id,
                    "title": recipe_title,
                    "status": "exception",
                    "error": str(e)
                })
        
        # Summary of navigation results
        success_count = len([r for r in navigation_results if r["status"] == "success"])
        total_count = len(navigation_results)
        
        self.log(f"Navigation success rate: {success_count}/{total_count}")
        
        return navigation_results
    
    async def test_different_recipe_types(self):
        """Test navigation for different types of recipes (regular vs Starbucks)"""
        self.log("=== Testing Different Recipe Types ===")
        
        try:
            # Test regular recipe navigation (should work)
            if self.generated_recipe_ids:
                regular_recipe_id = self.generated_recipe_ids[0]
                self.log(f"Testing regular recipe navigation: {regular_recipe_id}")
                
                response = await self.client.get(f"{self.backend_url}/recipes/{regular_recipe_id}/detail")
                if response.status_code == 200:
                    self.log("✅ Regular recipe navigation working")
                else:
                    self.log(f"❌ Regular recipe navigation failed: {response.status_code}")
            
            # Test Starbucks recipe navigation (this was the reported issue)
            starbucks_response = await self.client.get(f"{self.backend_url}/curated-starbucks-recipes")
            if starbucks_response.status_code == 200:
                starbucks_data = starbucks_response.json()
                starbucks_recipes = starbucks_data.get("recipes", [])
                
                if starbucks_recipes:
                    starbucks_recipe = starbucks_recipes[0]
                    starbucks_id = starbucks_recipe.get("id")
                    starbucks_name = starbucks_recipe.get("name")
                    
                    self.log(f"Testing Starbucks recipe navigation: {starbucks_name} ({starbucks_id})")
                    
                    detail_response = await self.client.get(f"{self.backend_url}/recipes/{starbucks_id}/detail")
                    if detail_response.status_code == 200:
                        self.log("✅ Starbucks recipe navigation working (issue was fixed)")
                    elif detail_response.status_code == 404:
                        self.log("❌ Starbucks recipe navigation failing (this was the original bug)")
                    else:
                        self.log(f"❌ Starbucks recipe navigation unexpected status: {detail_response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing different recipe types: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run comprehensive recipe history navigation test"""
        self.log("🚀 Starting Detailed Recipe History Navigation Testing")
        self.log("=" * 80)
        
        # Step 1: Login
        if not await self.login_demo_user():
            self.log("❌ Cannot proceed without login")
            return False
        
        # Step 2: Generate French chicken recipe with target ingredients
        generation_success, recipe_id, recipe_data = await self.generate_french_chicken_recipe()
        if not generation_success:
            self.log("⚠️ Recipe generation failed, testing with existing recipes")
        
        # Step 3: Test recipe history after generation
        history_success, all_recipes, french_recipes, chicken_mushroom_recipes = await self.test_recipe_history_after_generation()
        if not history_success:
            self.log("❌ Recipe history test failed")
            return False
        
        # Step 4: Test navigation for target recipes
        target_recipes = french_recipes + chicken_mushroom_recipes
        if target_recipes:
            navigation_results = await self.test_recipe_detail_navigation(target_recipes)
        else:
            self.log("⚠️ No target recipes found for navigation testing")
            navigation_results = []
        
        # Step 5: Test different recipe types
        type_test_success = await self.test_different_recipe_types()
        
        # Final Summary
        self.log("=" * 80)
        self.log("🔍 DETAILED RECIPE HISTORY NAVIGATION TEST RESULTS")
        self.log("=" * 80)
        
        self.log(f"Generated recipes: {len(self.generated_recipe_ids)}")
        self.log(f"French recipes found: {len(french_recipes)}")
        self.log(f"Chicken+Mushroom+Onion recipes found: {len(chicken_mushroom_recipes)}")
        
        if navigation_results:
            success_count = len([r for r in navigation_results if r["status"] == "success"])
            total_count = len(navigation_results)
            
            self.log(f"Navigation tests: {success_count}/{total_count} successful")
            
            # Show detailed results
            for result in navigation_results:
                status_emoji = "✅" if result["status"] == "success" else "❌"
                self.log(f"  {status_emoji} {result['title']} - {result['status']}")
                if result.get("error"):
                    self.log(f"    Error: {result['error']}")
        
        # Overall assessment
        if navigation_results:
            all_successful = all(r["status"] == "success" for r in navigation_results)
            if all_successful:
                self.log("🎉 ALL RECIPE NAVIGATION TESTS PASSED")
            else:
                self.log("❌ SOME RECIPE NAVIGATION ISSUES DETECTED")
                
                # Identify specific issues
                not_found_count = len([r for r in navigation_results if r["status"] == "not_found_404"])
                server_error_count = len([r for r in navigation_results if r["status"] == "server_error_500"])
                
                if not_found_count > 0:
                    self.log(f"  - {not_found_count} recipes exist in history but not accessible via detail endpoint")
                if server_error_count > 0:
                    self.log(f"  - {server_error_count} recipes causing server errors")
        else:
            self.log("⚠️ No navigation tests performed - no target recipes found")
        
        return navigation_results

async def main():
    """Main test execution"""
    tester = DetailedRecipeHistoryTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())