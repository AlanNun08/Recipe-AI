#!/usr/bin/env python3
"""
Clear Recipe History and Rebuild From Scratch
This script will:
1. Delete all existing recipes for the demo user
2. Generate fresh, diverse recipes from different cuisines
3. Create a realistic recipe history that demonstrates the app's functionality
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
import random

class RecipeHistoryRebuilder:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def clear_existing_recipes(self):
        """Clear all existing recipes for the demo user"""
        self.log("=== CLEARING EXISTING RECIPE HISTORY ===")
        
        try:
            # Get current recipe history
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"Found {len(recipes)} existing recipes to delete")
                
                # Delete each recipe
                deleted_count = 0
                for recipe in recipes:
                    recipe_id = recipe.get("id")
                    if recipe_id:
                        try:
                            delete_response = await self.client.delete(f"{self.backend_url}/recipes/{recipe_id}")
                            if delete_response.status_code in [200, 204, 404]:  # 404 is OK if already deleted
                                deleted_count += 1
                                if deleted_count % 10 == 0:
                                    self.log(f"Deleted {deleted_count}/{len(recipes)} recipes...")
                        except Exception as e:
                            self.log(f"Error deleting recipe {recipe_id}: {str(e)}", "WARNING")
                
                self.log(f"✅ Successfully deleted {deleted_count} recipes")
                return True
            else:
                self.log(f"❌ Failed to get recipe history: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error clearing recipe history: {str(e)}", "ERROR")
            return False
    
    async def generate_diverse_recipe(self, cuisine, meal_type, dietary_prefs=None):
        """Generate a single diverse recipe"""
        
        recipe_data = {
            "user_id": self.demo_user_id,
            "cuisine_type": cuisine,
            "recipe_category": "cuisine",
            "meal_type": meal_type,
            "servings": random.choice([2, 4, 6, 8]),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "dietary_preferences": dietary_prefs or []
        }
        
        try:
            response = await self.client.post(f"{self.backend_url}/recipes/generate", 
                                            json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Generated: {result.get('title')} ({cuisine})")
                return result
            else:
                self.log(f"❌ Failed to generate {cuisine} recipe: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error generating {cuisine} recipe: {str(e)}")
            return None
    
    async def build_fresh_recipe_history(self):
        """Build a fresh, diverse recipe history"""
        self.log("=== BUILDING FRESH RECIPE HISTORY ===")
        
        # Define diverse recipe combinations
        recipe_plans = [
            # Italian recipes
            {"cuisine": "Italian", "meal_type": "dinner", "dietary": []},
            {"cuisine": "Italian", "meal_type": "lunch", "dietary": ["Vegetarian"]},
            
            # Mexican recipes  
            {"cuisine": "Mexican", "meal_type": "dinner", "dietary": []},
            {"cuisine": "Mexican", "meal_type": "lunch", "dietary": ["Vegetarian"]},
            
            # Asian recipes
            {"cuisine": "Asian", "meal_type": "dinner", "dietary": []},
            {"cuisine": "Asian", "meal_type": "lunch", "dietary": []},
            {"cuisine": "Asian", "meal_type": "breakfast", "dietary": ["Vegetarian"]},
            
            # Indian recipes
            {"cuisine": "Indian", "meal_type": "dinner", "dietary": []},
            {"cuisine": "Indian", "meal_type": "lunch", "dietary": ["Vegetarian"]},
            
            # American recipes
            {"cuisine": "American", "meal_type": "dinner", "dietary": []},
            {"cuisine": "American", "meal_type": "breakfast", "dietary": []},
            
            # French recipes
            {"cuisine": "French", "meal_type": "dinner", "dietary": []},
            
            # Mediterranean recipes
            {"cuisine": "Mediterranean", "meal_type": "lunch", "dietary": ["Vegetarian"]},
            {"cuisine": "Mediterranean", "meal_type": "dinner", "dietary": []},
            
            # Thai recipes
            {"cuisine": "Thai", "meal_type": "dinner", "dietary": []},
        ]
        
        # Shuffle to create variety
        random.shuffle(recipe_plans)
        
        generated_recipes = []
        for i, plan in enumerate(recipe_plans):
            self.log(f"Generating recipe {i+1}/{len(recipe_plans)}: {plan['cuisine']} {plan['meal_type']}")
            
            recipe = await self.generate_diverse_recipe(
                plan["cuisine"], 
                plan["meal_type"], 
                plan["dietary"]
            )
            
            if recipe:
                generated_recipes.append(recipe)
                # Small delay to avoid overwhelming the API
                await asyncio.sleep(0.5)
            
        self.log(f"✅ Successfully generated {len(generated_recipes)} diverse recipes")
        return generated_recipes
    
    async def verify_recipe_history(self):
        """Verify the new recipe history"""
        self.log("=== VERIFYING NEW RECIPE HISTORY ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Recipe history now contains {len(recipes)} recipes")
                
                # Show first 5 recipes for verification
                self.log("📋 First 5 recipes in new history:")
                for i, recipe in enumerate(recipes[:5]):
                    title = recipe.get("title", "Unknown")
                    cuisine = recipe.get("cuisine_type", "Unknown")
                    self.log(f"  {i+1}. {title} ({cuisine})")
                
                return True
            else:
                self.log(f"❌ Failed to verify recipe history: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying recipe history: {str(e)}")
            return False
    
    async def test_navigation(self):
        """Test that recipe navigation is working correctly"""
        self.log("=== TESTING RECIPE NAVIGATION ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                if len(recipes) > 0:
                    # Test first recipe navigation
                    test_recipe = recipes[0]
                    recipe_id = test_recipe.get("id")
                    expected_title = test_recipe.get("title")
                    
                    self.log(f"Testing recipe navigation for: {expected_title}")
                    
                    # Test recipe detail endpoint
                    detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                    
                    if detail_response.status_code == 200:
                        detail_result = detail_response.json()
                        actual_title = detail_result.get("title")
                        
                        if expected_title == actual_title:
                            self.log(f"✅ Navigation test PASSED: {expected_title}")
                            return True
                        else:
                            self.log(f"❌ Navigation test FAILED: Expected '{expected_title}', got '{actual_title}'")
                            return False
                    else:
                        self.log(f"❌ Detail endpoint failed: {detail_response.status_code}")
                        return False
                else:
                    self.log("❌ No recipes available for navigation test")
                    return False
            else:
                self.log(f"❌ Failed to get recipe history for navigation test: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing navigation: {str(e)}")
            return False
    
    async def run_complete_rebuild(self):
        """Run the complete recipe history rebuild process"""
        self.log("🚀 Starting Complete Recipe History Rebuild")
        self.log("=" * 60)
        
        # Step 1: Clear existing recipes
        if not await self.clear_existing_recipes():
            self.log("❌ Failed to clear existing recipes, aborting")
            return False
        
        # Small delay to let database update
        await asyncio.sleep(2)
        
        # Step 2: Build fresh recipe history
        generated_recipes = await self.build_fresh_recipe_history()
        if len(generated_recipes) == 0:
            self.log("❌ Failed to generate any recipes, aborting")
            return False
        
        # Small delay to let database update
        await asyncio.sleep(2)
        
        # Step 3: Verify the new recipe history
        if not await self.verify_recipe_history():
            self.log("❌ Failed to verify new recipe history")
            return False
        
        # Step 4: Test navigation
        if not await self.test_navigation():
            self.log("❌ Navigation test failed")
            return False
        
        self.log("=" * 60)
        self.log("🎉 RECIPE HISTORY REBUILD COMPLETED SUCCESSFULLY!")
        self.log(f"✅ Generated {len(generated_recipes)} diverse recipes")
        self.log("✅ Recipe navigation verified working")
        self.log("✅ Ready for user testing")
        
        return True

async def main():
    rebuilder = RecipeHistoryRebuilder()
    try:
        success = await rebuilder.run_complete_rebuild()
        return success
    finally:
        await rebuilder.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Recipe history rebuild completed successfully!")
    else:
        print("\n❌ Recipe history rebuild failed!")
        exit(1)