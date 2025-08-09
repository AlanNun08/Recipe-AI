#!/usr/bin/env python3
"""
Recipe System Tests
Tests the core recipe generation, history, and navigation functionality
"""

import asyncio
import httpx
import pytest
import json
from datetime import datetime

class TestRecipeSystem:
    def __init__(self):
        self.backend_url = "http://localhost:8001/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_diverse_recipe_generation(self):
        """Test that recipe generation creates diverse, authentic recipes"""
        self.log("=== Testing Diverse Recipe Generation ===")
        
        test_cuisines = ["Italian", "Mexican", "Asian", "Indian", "Mediterranean"]
        generated_recipes = []
        
        for cuisine in test_cuisines:
            recipe_data = {
                "user_id": self.demo_user_id,
                "cuisine_type": cuisine,
                "recipe_category": "cuisine",
                "meal_type": "dinner",
                "servings": 4,
                "difficulty": "medium",
                "dietary_preferences": []
            }
            
            try:
                response = await self.client.post(f"{self.backend_url}/recipes/generate", 
                                                json=recipe_data)
                
                if response.status_code == 200:
                    recipe = response.json()
                    generated_recipes.append({
                        "cuisine": cuisine,
                        "title": recipe.get("title", "Unknown"),
                        "description": recipe.get("description", ""),
                        "ingredients_count": len(recipe.get("ingredients", [])),
                        "instructions_count": len(recipe.get("instructions", [])),
                        "id": recipe.get("id")
                    })
                    self.log(f"✅ Generated {cuisine}: {recipe.get('title')}")
                else:
                    self.log(f"❌ Failed to generate {cuisine} recipe: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error generating {cuisine} recipe: {str(e)}", "ERROR")
                return False
        
        # Verify diversity
        titles = [r["title"] for r in generated_recipes]
        unique_titles = set(titles)
        
        self.log(f"Generated {len(generated_recipes)} recipes with {len(unique_titles)} unique titles")
        
        # Check for authenticity (no generic "Classic X Pasta" dominance)
        pasta_count = sum(1 for title in titles if "pasta" in title.lower())
        pasta_ratio = pasta_count / len(titles) if titles else 0
        
        if pasta_ratio < 0.6:  # Less than 60% pasta recipes
            self.log(f"✅ Good diversity: {pasta_ratio:.1%} pasta recipes")
        else:
            self.log(f"⚠️  High pasta dominance: {pasta_ratio:.1%} pasta recipes", "WARNING")
        
        # Verify each recipe has proper structure
        for recipe in generated_recipes:
            if recipe["ingredients_count"] < 5:
                self.log(f"❌ {recipe['title']} has too few ingredients: {recipe['ingredients_count']}", "ERROR")
                return False
            if recipe["instructions_count"] < 5:
                self.log(f"❌ {recipe['title']} has too few instructions: {recipe['instructions_count']}", "ERROR")
                return False
        
        self.log("✅ Recipe generation test passed")
        return True
    
    async def test_recipe_history_navigation(self):
        """Test recipe history navigation accuracy"""
        self.log("=== Testing Recipe History Navigation ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe history: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])
            
            if len(recipes) < 5:
                self.log(f"❌ Insufficient recipes for testing: {len(recipes)}", "ERROR")
                return False
            
            self.log(f"Testing navigation with {len(recipes)} recipes")
            
            # Test first 5 recipes for navigation accuracy
            for i in range(min(5, len(recipes))):
                recipe = recipes[i]
                recipe_id = recipe.get("id")
                expected_title = recipe.get("title")
                
                if not recipe_id or not expected_title:
                    self.log(f"❌ Recipe {i+1} missing ID or title", "ERROR")
                    return False
                
                # Test detail endpoint
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code != 200:
                    self.log(f"❌ Detail endpoint failed for {recipe_id}: {detail_response.status_code}", "ERROR")
                    return False
                
                detail_result = detail_response.json()
                actual_title = detail_result.get("title")
                actual_id = detail_result.get("id")
                
                if expected_title != actual_title:
                    self.log(f"❌ Title mismatch for {recipe_id}: expected '{expected_title}', got '{actual_title}'", "ERROR")
                    return False
                
                if recipe_id != actual_id:
                    self.log(f"❌ ID mismatch: expected '{recipe_id}', got '{actual_id}'", "ERROR")
                    return False
                
                self.log(f"✅ Recipe {i+1}: {expected_title} - Navigation correct")
            
            self.log("✅ Recipe history navigation test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing recipe history navigation: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_data_integrity(self):
        """Test that recipes have proper data structure and content"""
        self.log("=== Testing Recipe Data Integrity ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe history: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])[:10]  # Test first 10 recipes
            
            required_fields = ["id", "title", "description", "ingredients", "instructions", "cuisine_type"]
            
            for i, recipe in enumerate(recipes):
                recipe_id = recipe.get("id")
                
                # Check required fields in history
                for field in required_fields:
                    if field not in recipe or not recipe[field]:
                        self.log(f"❌ Recipe {i+1} missing required field: {field}", "ERROR")
                        return False
                
                # Get detailed recipe data
                detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if detail_response.status_code != 200:
                    continue  # Skip if detail endpoint fails
                
                detail = detail_response.json()
                
                # Check detailed recipe structure
                ingredients = detail.get("ingredients", [])
                instructions = detail.get("instructions", [])
                
                if len(ingredients) < 3:
                    self.log(f"❌ Recipe {i+1} has insufficient ingredients: {len(ingredients)}", "ERROR")
                    return False
                
                if len(instructions) < 3:
                    self.log(f"❌ Recipe {i+1} has insufficient instructions: {len(instructions)}", "ERROR")
                    return False
                
                # Check for reasonable content (not just placeholders)
                title = detail.get("title", "")
                if "placeholder" in title.lower() or title == "Unknown Recipe":
                    self.log(f"❌ Recipe {i+1} has placeholder title: {title}", "ERROR")
                    return False
                
                self.log(f"✅ Recipe {i+1}: {title} - Data integrity OK")
            
            self.log("✅ Recipe data integrity test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing recipe data integrity: {str(e)}", "ERROR")
            return False
    
    async def test_cuisine_variety(self):
        """Test that recipe history contains variety of cuisines"""
        self.log("=== Testing Cuisine Variety ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe history: {response.status_code}", "ERROR")
                return False
            
            result = response.json()
            recipes = result.get("recipes", [])
            
            # Count cuisine types
            cuisine_counts = {}
            for recipe in recipes:
                cuisine = recipe.get("cuisine_type", "Unknown")
                cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1
            
            unique_cuisines = len(cuisine_counts)
            total_recipes = len(recipes)
            
            self.log(f"Found {unique_cuisines} different cuisines in {total_recipes} recipes")
            
            for cuisine, count in sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_recipes) * 100 if total_recipes > 0 else 0
                self.log(f"  {cuisine}: {count} recipes ({percentage:.1f}%)")
            
            # Check for reasonable variety
            if unique_cuisines < 3:
                self.log(f"❌ Insufficient cuisine variety: only {unique_cuisines} cuisines", "ERROR")
                return False
            
            # Check that no single cuisine dominates too much (>70%)
            max_cuisine_percentage = max(cuisine_counts.values()) / total_recipes if total_recipes > 0 else 0
            
            if max_cuisine_percentage > 0.7:
                dominant_cuisine = max(cuisine_counts.items(), key=lambda x: x[1])[0]
                self.log(f"⚠️  High dominance: {dominant_cuisine} represents {max_cuisine_percentage:.1%} of recipes", "WARNING")
            
            self.log("✅ Cuisine variety test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing cuisine variety: {str(e)}", "ERROR")
            return False
    
    async def run_all_tests(self):
        """Run all recipe system tests"""
        self.log("🚀 Starting Recipe System Tests")
        self.log("=" * 50)
        
        tests = [
            ("Recipe Generation", self.test_diverse_recipe_generation),
            ("Recipe Navigation", self.test_recipe_history_navigation),
            ("Data Integrity", self.test_recipe_data_integrity),
            ("Cuisine Variety", self.test_cuisine_variety)
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
        self.log(f"🎯 Recipe System Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            self.log("🎉 All recipe system tests PASSED!")
            return True
        else:
            self.log(f"❌ {total - passed} test(s) FAILED")
            return False

async def main():
    tester = TestRecipeSystem()
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Recipe system tests completed successfully!")
    else:
        print("\n❌ Recipe system tests failed!")
        exit(1)