#!/usr/bin/env python3
"""
Specific Recipe Search and Navigation Test
Search for existing recipes with chicken, mushrooms, onions and test navigation
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any

class SpecificRecipeSearchTester:
    def __init__(self):
        self.backend_url = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Demo user credentials
        self.demo_email = "demo@test.com"
        self.demo_password = "password123"
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
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
            return response.status_code == 200
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    async def search_all_recipe_collections(self):
        """Search all available recipe collections for chicken, mushroom, onion recipes"""
        self.log("=== Searching All Recipe Collections ===")
        
        found_recipes = []
        
        # 1. Search recipe history
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                self.log(f"Recipe history: {len(recipes)} recipes")
                
                for recipe in recipes:
                    if self.contains_target_ingredients(recipe):
                        found_recipes.append({
                            "source": "history",
                            "recipe": recipe,
                            "id": recipe.get("id"),
                            "title": recipe.get("title"),
                            "type": recipe.get("type", "unknown")
                        })
        except Exception as e:
            self.log(f"Error searching recipe history: {str(e)}")
        
        # 2. Search curated Starbucks recipes
        try:
            response = await self.client.get(f"{self.backend_url}/curated-starbucks-recipes")
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                self.log(f"Curated Starbucks: {len(recipes)} recipes")
                
                for recipe in recipes:
                    if self.contains_target_ingredients(recipe):
                        found_recipes.append({
                            "source": "starbucks_curated",
                            "recipe": recipe,
                            "id": recipe.get("id"),
                            "title": recipe.get("name", recipe.get("title")),
                            "type": "starbucks"
                        })
        except Exception as e:
            self.log(f"Error searching Starbucks recipes: {str(e)}")
        
        # 3. Search shared recipes
        try:
            response = await self.client.get(f"{self.backend_url}/shared-recipes?limit=100")
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                self.log(f"Shared recipes: {len(recipes)} recipes")
                
                for recipe in recipes:
                    if self.contains_target_ingredients(recipe):
                        found_recipes.append({
                            "source": "shared",
                            "recipe": recipe,
                            "id": recipe.get("id"),
                            "title": recipe.get("recipe_name", recipe.get("title")),
                            "type": "shared"
                        })
        except Exception as e:
            self.log(f"Error searching shared recipes: {str(e)}")
        
        self.log(f"Total recipes with chicken, mushroom, onion found: {len(found_recipes)}")
        
        for recipe_info in found_recipes:
            self.log(f"  - {recipe_info['title']} (Source: {recipe_info['source']}, ID: {recipe_info['id']})")
        
        return found_recipes
    
    def contains_target_ingredients(self, recipe: Dict) -> bool:
        """Check if recipe contains chicken, mushroom, and onion"""
        # Get all text fields from the recipe
        title = recipe.get("title", recipe.get("name", recipe.get("recipe_name", ""))).lower()
        description = recipe.get("description", "").lower()
        ingredients = recipe.get("ingredients", [])
        
        # Convert ingredients list to text
        ingredient_text = " ".join(ingredients).lower() if ingredients else ""
        
        # Combine all text
        full_text = f"{title} {description} {ingredient_text}"
        
        # Check for target ingredients
        has_chicken = any(word in full_text for word in ["chicken", "poultry"])
        has_mushroom = any(word in full_text for word in ["mushroom", "fungi"])
        has_onion = any(word in full_text for word in ["onion", "onions"])
        
        return has_chicken and has_mushroom and has_onion
    
    async def test_recipe_detail_endpoints(self, found_recipes: List[Dict]):
        """Test different recipe detail endpoints for found recipes"""
        self.log("=== Testing Recipe Detail Endpoints ===")
        
        if not found_recipes:
            self.log("⚠️ No recipes with target ingredients found to test")
            return []
        
        test_results = []
        
        for recipe_info in found_recipes:
            recipe_id = recipe_info["id"]
            title = recipe_info["title"]
            source = recipe_info["source"]
            recipe_type = recipe_info["type"]
            
            self.log(f"Testing recipe: {title} (Source: {source}, Type: {recipe_type})")
            
            # Test the main recipe detail endpoint
            try:
                response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                result = {
                    "recipe_id": recipe_id,
                    "title": title,
                    "source": source,
                    "type": recipe_type,
                    "detail_endpoint_status": response.status_code,
                    "detail_endpoint_success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result["retrieved_title"] = data.get("title", data.get("name"))
                    result["has_ingredients"] = bool(data.get("ingredients"))
                    result["has_instructions"] = bool(data.get("instructions"))
                    self.log(f"  ✅ Detail endpoint successful")
                    self.log(f"    Retrieved title: {result['retrieved_title']}")
                    self.log(f"    Has ingredients: {result['has_ingredients']}")
                    self.log(f"    Has instructions: {result['has_instructions']}")
                elif response.status_code == 404:
                    self.log(f"  ❌ Recipe not found (404) - Navigation issue detected!")
                    result["error"] = "Recipe exists in collection but not accessible via detail endpoint"
                elif response.status_code == 500:
                    self.log(f"  ❌ Server error (500)")
                    result["error"] = f"Server error: {response.text}"
                else:
                    self.log(f"  ❌ Unexpected status: {response.status_code}")
                    result["error"] = f"Unexpected status: {response.status_code}"
                
                test_results.append(result)
                
            except Exception as e:
                self.log(f"  ❌ Exception: {str(e)}")
                test_results.append({
                    "recipe_id": recipe_id,
                    "title": title,
                    "source": source,
                    "type": recipe_type,
                    "detail_endpoint_status": "exception",
                    "detail_endpoint_success": False,
                    "error": str(e)
                })
        
        return test_results
    
    async def test_weekly_recipes_for_target_ingredients(self):
        """Test weekly recipes for chicken, mushroom, onion combinations"""
        self.log("=== Testing Weekly Recipes ===")
        
        try:
            # Get current weekly meal plan
            response = await self.client.get(f"{self.backend_url}/weekly-recipes/current/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                has_plan = result.get("has_plan", False)
                meals = result.get("meals", [])
                
                self.log(f"Weekly meal plan exists: {has_plan}")
                self.log(f"Meals in plan: {len(meals)}")
                
                target_meals = []
                
                for meal in meals:
                    meal_name = meal.get("name", "").lower()
                    meal_description = meal.get("description", "").lower()
                    
                    # Check if this meal might contain our target ingredients
                    full_text = f"{meal_name} {meal_description}"
                    
                    has_chicken = "chicken" in full_text
                    has_mushroom = "mushroom" in full_text
                    has_onion = "onion" in full_text
                    
                    if has_chicken or has_mushroom or has_onion:
                        target_meals.append(meal)
                        self.log(f"  Potential target meal: {meal.get('name')}")
                        self.log(f"    Chicken: {has_chicken}, Mushroom: {has_mushroom}, Onion: {has_onion}")
                        
                        # Test the weekly recipe detail endpoint
                        meal_id = meal.get("id")
                        if meal_id:
                            detail_response = await self.client.get(f"{self.backend_url}/weekly-recipes/recipe/{meal_id}")
                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()
                                ingredients = detail_data.get("ingredients", [])
                                ingredient_text = " ".join(ingredients).lower()
                                
                                actual_chicken = "chicken" in ingredient_text
                                actual_mushroom = "mushroom" in ingredient_text
                                actual_onion = "onion" in ingredient_text
                                
                                self.log(f"    Actual ingredients - Chicken: {actual_chicken}, Mushroom: {actual_mushroom}, Onion: {actual_onion}")
                                
                                if actual_chicken and actual_mushroom and actual_onion:
                                    self.log(f"    ✅ Found weekly recipe with all target ingredients!")
                                    return meal_id, detail_data
                
                return None, None
            else:
                self.log(f"❌ Weekly recipes endpoint failed: {response.status_code}")
                return None, None
                
        except Exception as e:
            self.log(f"❌ Error testing weekly recipes: {str(e)}")
            return None, None
    
    async def run_comprehensive_search(self):
        """Run comprehensive search and navigation test"""
        self.log("🚀 Starting Specific Recipe Search and Navigation Test")
        self.log("=" * 80)
        
        # Login
        if not await self.login_demo_user():
            self.log("❌ Cannot proceed without login")
            return False
        
        # Search all collections
        found_recipes = await self.search_all_recipe_collections()
        
        # Test weekly recipes
        weekly_recipe_id, weekly_recipe_data = await self.test_weekly_recipes_for_target_ingredients()
        
        # Test navigation for found recipes
        navigation_results = await self.test_recipe_detail_endpoints(found_recipes)
        
        # Summary
        self.log("=" * 80)
        self.log("🔍 SPECIFIC RECIPE SEARCH RESULTS")
        self.log("=" * 80)
        
        self.log(f"Recipes with chicken+mushroom+onion found: {len(found_recipes)}")
        
        if found_recipes:
            for recipe_info in found_recipes:
                self.log(f"  - {recipe_info['title']} (Source: {recipe_info['source']})")
        
        if weekly_recipe_id:
            self.log(f"Weekly recipe with target ingredients: {weekly_recipe_data.get('name')}")
        
        # Navigation test results
        if navigation_results:
            successful_navigation = len([r for r in navigation_results if r["detail_endpoint_success"]])
            total_navigation = len(navigation_results)
            
            self.log(f"Navigation success rate: {successful_navigation}/{total_navigation}")
            
            # Show issues
            failed_navigation = [r for r in navigation_results if not r["detail_endpoint_success"]]
            if failed_navigation:
                self.log("❌ Navigation issues detected:")
                for result in failed_navigation:
                    self.log(f"  - {result['title']} (Source: {result['source']}) - {result.get('error', 'Unknown error')}")
            else:
                self.log("✅ All recipe navigation tests passed")
        
        # Overall assessment
        if not found_recipes and not weekly_recipe_id:
            self.log("⚠️ No recipes with chicken, mushroom, and onion ingredients found")
            self.log("This suggests the specific issue mentioned in the review may not be reproducible")
            self.log("with the current demo user data")
        
        return {
            "found_recipes": found_recipes,
            "weekly_recipe": weekly_recipe_data,
            "navigation_results": navigation_results
        }

async def main():
    """Main test execution"""
    tester = SpecificRecipeSearchTester()
    
    try:
        results = await tester.run_comprehensive_search()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())