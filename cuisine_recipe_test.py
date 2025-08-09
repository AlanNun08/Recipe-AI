#!/usr/bin/env python3
"""
Cuisine-Specific Recipe Generation Testing Script
Testing improved mock data generation for Chinese, Mexican, and Indian cuisines
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Get backend URL from environment
BACKEND_URL = "http://localhost:8001/api"
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=')[1].strip() + '/api'
                break
except:
    pass

print(f"Using backend URL: {BACKEND_URL}")

class CuisineRecipeTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"  # Demo user ID
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_backend_health(self):
        """Test backend connectivity"""
        self.log("=== Testing Backend Health ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                self.log("✅ Backend is healthy and accessible")
                return True
            else:
                self.log(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Backend connectivity error: {str(e)}")
            return False
    
    async def test_cuisine_recipe_generation(self, cuisine: str, meal_type: str, difficulty: str, user_id: str):
        """Test recipe generation for specific cuisine"""
        self.log(f"=== Testing {cuisine} Cuisine Recipe Generation ===")
        
        try:
            recipe_data = {
                "user_id": user_id,
                "recipe_category": "cuisine",
                "cuisine_type": cuisine,
                "dietary_preferences": [],
                "ingredients_on_hand": [],
                "prep_time_max": 45,
                "servings": 4,
                "difficulty": difficulty
            }
            
            self.log(f"Generating {cuisine} {meal_type} recipe (difficulty: {difficulty})")
            self.log(f"Request data: {json.dumps(recipe_data, indent=2)}")
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract recipe details
                recipe_title = result.get("title", "Unknown")
                recipe_description = result.get("description", "")
                ingredients = result.get("ingredients", [])
                instructions = result.get("instructions", [])
                cuisine_type = result.get("cuisine_type", "")
                shopping_list = result.get("shopping_list", [])
                
                self.log(f"✅ Recipe generated successfully!")
                self.log(f"Title: {recipe_title}")
                self.log(f"Description: {recipe_description[:100]}...")
                self.log(f"Cuisine Type: {cuisine_type}")
                self.log(f"Ingredients ({len(ingredients)}): {ingredients}")
                self.log(f"Instructions ({len(instructions)} steps)")
                self.log(f"Shopping List ({len(shopping_list)}): {shopping_list}")
                
                # Analyze cuisine appropriateness
                analysis = self.analyze_cuisine_appropriateness(cuisine, recipe_title, ingredients, recipe_description)
                
                return {
                    "success": True,
                    "recipe": result,
                    "analysis": analysis
                }
                
            elif response.status_code == 500:
                error_text = response.text
                self.log(f"❌ Recipe generation failed with 500 error")
                self.log(f"Error details: {error_text}")
                
                # Check if it's falling back to mock data
                if "OpenAI" in error_text or "API" in error_text:
                    self.log("🔍 This appears to be an OpenAI API issue - checking if mock fallback is working")
                
                return {
                    "success": False,
                    "error": error_text,
                    "status_code": 500
                }
                
            else:
                self.log(f"❌ Recipe generation failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            self.log(f"❌ Error testing {cuisine} recipe generation: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_cuisine_appropriateness(self, expected_cuisine: str, title: str, ingredients: List[str], description: str) -> Dict[str, Any]:
        """Analyze if the generated recipe matches the expected cuisine"""
        
        # Define cuisine-specific keywords and ingredients
        cuisine_indicators = {
            "Chinese": {
                "keywords": ["chinese", "stir", "fry", "wok", "soy", "ginger", "garlic", "rice", "noodles", "sesame", "scallion", "bok choy"],
                "ingredients": ["soy sauce", "ginger", "garlic", "rice", "noodles", "sesame oil", "scallions", "bok choy", "shiitake", "tofu"],
                "inappropriate": ["pasta", "marinara", "parmesan", "mozzarella", "basil", "oregano", "tortilla", "salsa", "cumin"]
            },
            "Mexican": {
                "keywords": ["mexican", "taco", "burrito", "salsa", "guacamole", "enchilada", "quesadilla", "cilantro", "lime", "chili", "pepper"],
                "ingredients": ["tortilla", "salsa", "cilantro", "lime", "cumin", "chili", "pepper", "avocado", "cheese", "beans", "corn"],
                "inappropriate": ["pasta", "marinara", "parmesan", "basil", "oregano", "soy sauce", "ginger", "curry", "turmeric"]
            },
            "Indian": {
                "keywords": ["indian", "curry", "masala", "tandoori", "biryani", "naan", "basmati", "turmeric", "cumin", "coriander", "garam"],
                "ingredients": ["curry", "turmeric", "cumin", "coriander", "garam masala", "basmati rice", "naan", "yogurt", "onion", "tomato"],
                "inappropriate": ["pasta", "marinara", "parmesan", "mozzarella", "tortilla", "salsa", "soy sauce", "sesame oil"]
            }
        }
        
        expected_indicators = cuisine_indicators.get(expected_cuisine, {})
        
        # Combine all text for analysis
        all_text = f"{title} {description} {' '.join(ingredients)}".lower()
        
        # Count appropriate indicators
        appropriate_keywords = sum(1 for keyword in expected_indicators.get("keywords", []) if keyword in all_text)
        appropriate_ingredients = sum(1 for ingredient in expected_indicators.get("ingredients", []) if ingredient in all_text)
        
        # Count inappropriate indicators
        inappropriate_count = sum(1 for inappropriate in expected_indicators.get("inappropriate", []) if inappropriate in all_text)
        
        # Calculate appropriateness score
        total_appropriate = appropriate_keywords + appropriate_ingredients
        appropriateness_score = max(0, total_appropriate - inappropriate_count)
        
        # Determine if cuisine is appropriate
        is_appropriate = total_appropriate > 0 and inappropriate_count == 0
        
        analysis = {
            "expected_cuisine": expected_cuisine,
            "appropriate_keywords_found": appropriate_keywords,
            "appropriate_ingredients_found": appropriate_ingredients,
            "inappropriate_elements_found": inappropriate_count,
            "appropriateness_score": appropriateness_score,
            "is_cuisine_appropriate": is_appropriate,
            "analysis_text": all_text[:200] + "..." if len(all_text) > 200 else all_text
        }
        
        # Log analysis results
        if is_appropriate:
            self.log(f"✅ Cuisine Analysis: Recipe appears appropriate for {expected_cuisine} cuisine")
            self.log(f"   - Found {appropriate_keywords} appropriate keywords")
            self.log(f"   - Found {appropriate_ingredients} appropriate ingredients")
            self.log(f"   - Found {inappropriate_count} inappropriate elements")
        else:
            self.log(f"❌ Cuisine Analysis: Recipe may not be appropriate for {expected_cuisine} cuisine")
            self.log(f"   - Found {appropriate_keywords} appropriate keywords")
            self.log(f"   - Found {appropriate_ingredients} appropriate ingredients")
            self.log(f"   - Found {inappropriate_count} inappropriate elements")
            if inappropriate_count > 0:
                self.log(f"   - WARNING: Contains elements from other cuisines")
        
        return analysis
    
    async def run_cuisine_tests(self):
        """Run all cuisine-specific tests as requested in review"""
        self.log("🚀 Starting Cuisine-Specific Recipe Generation Tests")
        self.log("=" * 70)
        
        # Test backend health first
        if not await self.test_backend_health():
            self.log("❌ Backend is not accessible - aborting tests")
            return {}
        
        # Test scenarios from review request
        test_scenarios = [
            {
                "cuisine": "Chinese",
                "meal_type": "Dinner", 
                "difficulty": "Easy",
                "user_id": "test-user-123"
            },
            {
                "cuisine": "Mexican",
                "meal_type": "Lunch",
                "difficulty": "Medium", 
                "user_id": "test-user-123"
            },
            {
                "cuisine": "Indian",
                "meal_type": "Dinner",
                "difficulty": "Medium",
                "user_id": "test-user-123"
            }
        ]
        
        test_results = {}
        
        for scenario in test_scenarios:
            cuisine = scenario["cuisine"]
            result = await self.test_cuisine_recipe_generation(
                cuisine=cuisine,
                meal_type=scenario["meal_type"],
                difficulty=scenario["difficulty"],
                user_id=scenario["user_id"]
            )
            
            test_results[cuisine] = result
            
            # Add some delay between tests
            await asyncio.sleep(2)
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 CUISINE RECIPE GENERATION TEST RESULTS")
        self.log("=" * 70)
        
        successful_tests = 0
        appropriate_cuisines = 0
        
        for cuisine, result in test_results.items():
            if result.get("success"):
                successful_tests += 1
                status = "✅ SUCCESS"
                
                analysis = result.get("analysis", {})
                if analysis.get("is_cuisine_appropriate"):
                    appropriate_cuisines += 1
                    cuisine_status = "✅ APPROPRIATE"
                else:
                    cuisine_status = "❌ INAPPROPRIATE"
                
                self.log(f"{cuisine.upper()}: {status} - Cuisine Match: {cuisine_status}")
                
                if analysis:
                    self.log(f"  - Appropriate elements: {analysis.get('appropriate_keywords_found', 0)} keywords, {analysis.get('appropriate_ingredients_found', 0)} ingredients")
                    self.log(f"  - Inappropriate elements: {analysis.get('inappropriate_elements_found', 0)}")
                    self.log(f"  - Appropriateness score: {analysis.get('appropriateness_score', 0)}")
                
            else:
                status = "❌ FAILED"
                error = result.get("error", "Unknown error")
                self.log(f"{cuisine.upper()}: {status} - Error: {error[:100]}...")
        
        self.log("=" * 70)
        self.log("📊 FINAL SUMMARY")
        self.log(f"✅ Successful recipe generations: {successful_tests}/3")
        self.log(f"✅ Cuisine-appropriate recipes: {appropriate_cuisines}/3")
        
        if successful_tests == 3 and appropriate_cuisines == 3:
            self.log("🎉 ALL TESTS PASSED - Cuisine-specific recipe generation is working correctly!")
        elif successful_tests == 3:
            self.log("⚠️ All recipes generated but some may not be cuisine-appropriate")
        else:
            self.log("❌ Some recipe generations failed - check backend logs")
        
        # Specific findings for the review request
        self.log("=" * 70)
        self.log("📋 REVIEW REQUEST FINDINGS")
        self.log("=" * 70)
        
        for cuisine in ["Chinese", "Mexican", "Indian"]:
            result = test_results.get(cuisine, {})
            if result.get("success"):
                recipe = result.get("recipe", {})
                title = recipe.get("title", "Unknown")
                ingredients = recipe.get("ingredients", [])
                
                self.log(f"{cuisine.upper()} RECIPE:")
                self.log(f"  - Title: {title}")
                self.log(f"  - Key ingredients: {ingredients[:5]}")  # Show first 5 ingredients
                
                # Check for the specific issue mentioned in review (pasta for all cuisines)
                has_pasta = any("pasta" in ingredient.lower() for ingredient in ingredients)
                if has_pasta and cuisine != "Italian":
                    self.log(f"  - ⚠️ WARNING: Contains pasta ingredients for {cuisine} cuisine")
                else:
                    self.log(f"  - ✅ No inappropriate pasta ingredients detected")
            else:
                self.log(f"{cuisine.upper()} RECIPE: ❌ Generation failed")
        
        return test_results

async def main():
    """Main test execution"""
    tester = CuisineRecipeTester()
    
    try:
        results = await tester.run_cuisine_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())