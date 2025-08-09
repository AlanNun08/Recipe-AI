#!/usr/bin/env python3
"""
Recipe History Navigation Issue Testing Script
Testing the specific issue where recipes from history aren't showing correct details
Focus: French recipe with chicken, mushrooms, and onions navigation
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

class RecipeHistoryTester:
    def __init__(self):
        # Use the external URL from frontend/.env
        self.backend_url = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Demo user credentials from test_result.md
        self.demo_email = "demo@test.com"
        self.demo_password = "password123"
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
        self.test_results = {}
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test 1: Verify demo user can login successfully"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": self.demo_email,
                "password": self.demo_password
            }
            
            response = await self.client.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                user_id = result.get("user", {}).get("id")
                is_verified = result.get("user", {}).get("is_verified")
                
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {user_id}")
                self.log(f"Verified: {is_verified}")
                
                if user_id == self.demo_user_id:
                    self.log("✅ User ID matches expected demo user ID")
                else:
                    self.log(f"⚠️ User ID mismatch. Expected: {self.demo_user_id}, Got: {user_id}")
                
                return True, user_id
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error during login: {str(e)}", "ERROR")
            return False, None
    
    async def test_recipe_history_endpoint(self, user_id: str):
        """Test 2: Get recipe history for demo user and look for French recipes"""
        self.log("=== Testing Recipe History Endpoint ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Recipe history endpoint working")
                self.log(f"Total recipes found: {total}")
                self.log(f"Recipes in response: {len(recipes)}")
                
                # Look for French recipes with chicken, mushrooms, onions
                french_recipes = []
                chicken_mushroom_recipes = []
                
                for recipe in recipes:
                    recipe_id = recipe.get("id")
                    title = recipe.get("title", "").lower()
                    description = recipe.get("description", "").lower()
                    ingredients = recipe.get("ingredients", [])
                    cuisine_type = recipe.get("cuisine_type", "").lower()
                    recipe_type = recipe.get("type", "unknown")
                    
                    # Check for French cuisine
                    if "french" in cuisine_type or "french" in title:
                        french_recipes.append({
                            "id": recipe_id,
                            "title": recipe.get("title"),
                            "type": recipe_type,
                            "cuisine": cuisine_type
                        })
                    
                    # Check for chicken, mushroom, onion ingredients
                    ingredient_text = " ".join(ingredients).lower() if ingredients else ""
                    full_text = f"{title} {description} {ingredient_text}"
                    
                    if ("chicken" in full_text and "mushroom" in full_text and "onion" in full_text):
                        chicken_mushroom_recipes.append({
                            "id": recipe_id,
                            "title": recipe.get("title"),
                            "type": recipe_type,
                            "ingredients": ingredients[:5],  # First 5 ingredients
                            "cuisine": cuisine_type
                        })
                
                self.log(f"French recipes found: {len(french_recipes)}")
                for recipe in french_recipes:
                    self.log(f"  - {recipe['title']} (ID: {recipe['id']}, Type: {recipe['type']})")
                
                self.log(f"Chicken+Mushroom+Onion recipes found: {len(chicken_mushroom_recipes)}")
                for recipe in chicken_mushroom_recipes:
                    self.log(f"  - {recipe['title']} (ID: {recipe['id']}, Type: {recipe['type']})")
                    self.log(f"    Ingredients: {recipe['ingredients']}")
                
                # Check for null recipe IDs
                null_ids = [r for r in recipes if not r.get("id")]
                if null_ids:
                    self.log(f"❌ Found {len(null_ids)} recipes with null IDs")
                else:
                    self.log("✅ All recipes have valid IDs")
                
                return True, recipes, french_recipes, chicken_mushroom_recipes
                
            else:
                self.log(f"❌ Recipe history endpoint failed: {response.status_code} - {response.text}")
                return False, [], [], []
                
        except Exception as e:
            self.log(f"❌ Error getting recipe history: {str(e)}", "ERROR")
            return False, [], [], []
    
    async def test_recipe_detail_retrieval(self, target_recipes: List[Dict]):
        """Test 3: Test recipe detail retrieval for target recipes"""
        self.log("=== Testing Recipe Detail Retrieval ===")
        
        if not target_recipes:
            self.log("⚠️ No target recipes to test")
            return True
        
        success_count = 0
        total_count = len(target_recipes)
        
        for recipe in target_recipes:
            recipe_id = recipe.get("id")
            recipe_title = recipe.get("title")
            recipe_type = recipe.get("type", "unknown")
            
            self.log(f"Testing recipe detail for: {recipe_title} (ID: {recipe_id}, Type: {recipe_type})")
            
            try:
                response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verify recipe data structure
                    required_fields = ["id", "title", "description", "ingredients", "instructions"]
                    missing_fields = [field for field in required_fields if not result.get(field)]
                    
                    if missing_fields:
                        self.log(f"❌ Recipe detail missing fields: {missing_fields}")
                    else:
                        self.log(f"✅ Recipe detail retrieved successfully")
                        self.log(f"  Title: {result.get('title')}")
                        self.log(f"  Ingredients count: {len(result.get('ingredients', []))}")
                        self.log(f"  Instructions count: {len(result.get('instructions', []))}")
                        
                        # Check if ingredients match expected content
                        ingredients = result.get("ingredients", [])
                        ingredient_text = " ".join(ingredients).lower()
                        
                        has_chicken = "chicken" in ingredient_text
                        has_mushroom = "mushroom" in ingredient_text
                        has_onion = "onion" in ingredient_text
                        
                        self.log(f"  Contains chicken: {has_chicken}")
                        self.log(f"  Contains mushroom: {has_mushroom}")
                        self.log(f"  Contains onion: {has_onion}")
                        
                        success_count += 1
                
                elif response.status_code == 404:
                    self.log(f"❌ Recipe not found (404) - This is the reported issue!")
                    self.log(f"  Recipe ID: {recipe_id}")
                    self.log(f"  Recipe Type: {recipe_type}")
                    
                elif response.status_code == 500:
                    self.log(f"❌ Server error (500) retrieving recipe")
                    self.log(f"  Error details: {response.text}")
                    
                else:
                    self.log(f"❌ Unexpected status code: {response.status_code}")
                    self.log(f"  Response: {response.text}")
                
            except Exception as e:
                self.log(f"❌ Error retrieving recipe detail: {str(e)}", "ERROR")
        
        self.log(f"Recipe detail retrieval success rate: {success_count}/{total_count}")
        return success_count == total_count
    
    async def test_recipe_collections_search(self):
        """Test 4: Debug which collections contain recipes"""
        self.log("=== Testing Recipe Collections Search ===")
        
        try:
            # Test different recipe endpoints to understand the data structure
            endpoints_to_test = [
                "/curated-starbucks-recipes",
                "/shared-recipes?limit=5",
            ]
            
            for endpoint in endpoints_to_test:
                self.log(f"Testing endpoint: {endpoint}")
                
                try:
                    response = await self.client.get(f"{self.backend_url}{endpoint}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if "recipes" in result:
                            recipes = result["recipes"]
                            self.log(f"  ✅ Found {len(recipes)} recipes")
                            
                            if recipes:
                                sample_recipe = recipes[0]
                                self.log(f"  Sample recipe ID: {sample_recipe.get('id')}")
                                self.log(f"  Sample recipe name: {sample_recipe.get('name', sample_recipe.get('recipe_name', 'Unknown'))}")
                        else:
                            self.log(f"  ✅ Response received: {list(result.keys())}")
                    else:
                        self.log(f"  ❌ Failed: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"  ❌ Error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing collections: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_recipe_navigation(self):
        """Test 5: Specifically test Starbucks recipe navigation issue"""
        self.log("=== Testing Starbucks Recipe Navigation ===")
        
        try:
            # Get curated Starbucks recipes
            response = await self.client.get(f"{self.backend_url}/curated-starbucks-recipes")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Found {len(recipes)} curated Starbucks recipes")
                
                if recipes:
                    # Test the first few Starbucks recipes
                    for i, recipe in enumerate(recipes[:3]):
                        recipe_id = recipe.get("id")
                        recipe_name = recipe.get("name")
                        
                        self.log(f"Testing Starbucks recipe {i+1}: {recipe_name} (ID: {recipe_id})")
                        
                        # Try to get detail using the regular recipe detail endpoint
                        detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                        
                        if detail_response.status_code == 200:
                            self.log(f"  ✅ Starbucks recipe detail retrieved successfully")
                        elif detail_response.status_code == 404:
                            self.log(f"  ❌ Starbucks recipe not found via detail endpoint (This was the bug!)")
                        else:
                            self.log(f"  ❌ Unexpected status: {detail_response.status_code}")
                
                return True
            else:
                self.log(f"❌ Failed to get curated Starbucks recipes: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Starbucks navigation: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all recipe history navigation tests"""
        self.log("🚀 Starting Recipe History Navigation Issue Testing")
        self.log("=" * 70)
        
        # Test 1: Demo user login
        login_success, user_id = await self.test_demo_user_login()
        if not login_success:
            self.log("❌ Cannot proceed without successful login")
            return False
        
        # Test 2: Recipe history endpoint
        history_success, all_recipes, french_recipes, chicken_mushroom_recipes = await self.test_recipe_history_endpoint(user_id)
        if not history_success:
            self.log("❌ Recipe history endpoint failed")
            return False
        
        # Test 3: Recipe detail retrieval for target recipes
        target_recipes = french_recipes + chicken_mushroom_recipes
        if target_recipes:
            detail_success = await self.test_recipe_detail_retrieval(target_recipes)
        else:
            self.log("⚠️ No French or chicken+mushroom+onion recipes found to test")
            detail_success = True
        
        # Test 4: Collections search
        collections_success = await self.test_recipe_collections_search()
        
        # Test 5: Starbucks recipe navigation (known issue from test_result.md)
        starbucks_success = await self.test_starbucks_recipe_navigation()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 RECIPE HISTORY NAVIGATION TEST RESULTS")
        self.log("=" * 70)
        
        results = {
            "demo_login": login_success,
            "recipe_history": history_success,
            "recipe_detail": detail_success,
            "collections_search": collections_success,
            "starbucks_navigation": starbucks_success
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Specific findings
        self.log("=" * 70)
        self.log("🔍 SPECIFIC FINDINGS:")
        
        if target_recipes:
            self.log(f"• Found {len(target_recipes)} recipes matching criteria")
            for recipe in target_recipes:
                self.log(f"  - {recipe['title']} (ID: {recipe['id']}, Type: {recipe.get('type')})")
        else:
            self.log("• No French recipes with chicken, mushrooms, and onions found in history")
        
        # Overall assessment
        critical_tests = ["demo_login", "recipe_history", "recipe_detail"]
        critical_passed = sum(1 for test in critical_tests if results.get(test, False))
        
        if critical_passed == len(critical_tests):
            self.log("🎉 RECIPE HISTORY NAVIGATION WORKING CORRECTLY")
        else:
            self.log("❌ RECIPE HISTORY NAVIGATION ISSUES DETECTED")
        
        return results

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