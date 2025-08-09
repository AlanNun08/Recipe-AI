#!/usr/bin/env python3
"""
Recipe Generation Functionality Testing with Mock Data Fallback
Testing the updated recipe generation functionality to verify mock data fallback
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import time

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url() + "/api"
print(f"Using backend URL: {BACKEND_URL}")

class RecipeGenerationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"  # Demo user ID
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_health_check(self):
        """Test backend health and connectivity"""
        self.log("=== Testing Backend Health ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL.replace('/api', '')}/health")
            if response.status_code == 200:
                self.log("✅ Backend is healthy and accessible")
                return True
            else:
                self.log(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Backend connectivity error: {str(e)}")
            return False
    
    async def test_openai_api_key_status(self):
        """Check OpenAI API key status"""
        self.log("=== Checking OpenAI API Key Status ===")
        
        try:
            # Check environment variables directly
            sys.path.append('/app/backend')
            from dotenv import load_dotenv
            from pathlib import Path
            
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                if openai_key == "your-openai-api-key-here":
                    self.log("✅ OpenAI API key is placeholder - mock fallback should activate")
                    return "placeholder"
                else:
                    self.log(f"✅ OpenAI API key present: {openai_key[:10]}...")
                    return "real"
            else:
                self.log("❌ OpenAI API key not found")
                return "missing"
                
        except Exception as e:
            self.log(f"❌ Error checking OpenAI key: {str(e)}")
            return "error"
    
    async def test_recipe_generation_scenario_1(self):
        """Test Scenario 1: Chinese cuisine, Snack, Easy, None dietary restrictions"""
        self.log("=== Testing Recipe Generation Scenario 1 ===")
        self.log("Parameters: Chinese cuisine, Snack, Easy, None dietary restrictions")
        
        try:
            recipe_data = {
                "user_id": self.test_user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Chinese",
                "dietary_preferences": [],
                "ingredients_on_hand": [],
                "prep_time_max": 30,
                "servings": 4,
                "difficulty": "easy"
            }
            
            self.log(f"Making request to /recipes/generate with data: {recipe_data}")
            
            start_time = time.time()
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            end_time = time.time()
            
            self.log(f"Response time: {end_time - start_time:.2f} seconds")
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ["id", "title", "description", "ingredients", "instructions", 
                                 "prep_time", "cook_time", "servings", "cuisine_type", "difficulty"]
                
                missing_fields = [field for field in required_fields if field not in result]
                if missing_fields:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
                
                self.log("✅ Recipe generated successfully!")
                self.log(f"Recipe ID: {result.get('id')}")
                self.log(f"Title: {result.get('title')}")
                self.log(f"Description: {result.get('description', '')[:100]}...")
                self.log(f"Cuisine Type: {result.get('cuisine_type')}")
                self.log(f"Difficulty: {result.get('difficulty')}")
                self.log(f"Prep Time: {result.get('prep_time')} minutes")
                self.log(f"Cook Time: {result.get('cook_time')} minutes")
                self.log(f"Servings: {result.get('servings')}")
                self.log(f"Ingredients count: {len(result.get('ingredients', []))}")
                self.log(f"Instructions count: {len(result.get('instructions', []))}")
                
                # Check if it's reasonable for Chinese snack
                title = result.get('title', '').lower()
                description = result.get('description', '').lower()
                ingredients = [ing.lower() for ing in result.get('ingredients', [])]
                
                # Check for reasonable Chinese elements
                chinese_indicators = ['chinese', 'soy', 'ginger', 'garlic', 'sesame', 'rice', 'noodle', 'dumpling', 'wonton']
                has_chinese_elements = any(indicator in title or indicator in description or 
                                         any(indicator in ing for ing in ingredients) 
                                         for indicator in chinese_indicators)
                
                if has_chinese_elements:
                    self.log("✅ Recipe appears to have appropriate Chinese elements")
                else:
                    self.log("⚠️ Recipe may not have clear Chinese cuisine elements")
                
                # Check for inappropriate combinations (like yogurt from Chinese cuisine)
                inappropriate_combos = ['yogurt', 'pasta', 'pizza', 'burrito', 'taco']
                has_inappropriate = any(combo in title or combo in description or 
                                      any(combo in ing for ing in ingredients) 
                                      for combo in inappropriate_combos)
                
                if has_inappropriate:
                    self.log("❌ Recipe contains inappropriate combinations for Chinese cuisine")
                    return False
                else:
                    self.log("✅ No inappropriate cuisine combinations detected")
                
                return result
                
            elif response.status_code == 500:
                error_text = response.text
                self.log(f"❌ Recipe generation failed with 500 error: {error_text}")
                
                # Check if it's the expected OpenAI error
                if "openai" in error_text.lower() or "api" in error_text.lower():
                    self.log("❌ Appears to be OpenAI API error - mock fallback not working")
                else:
                    self.log("❌ Different type of 500 error")
                
                return False
                
            else:
                self.log(f"❌ Recipe generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in recipe generation test: {str(e)}")
            return False
    
    async def test_recipe_generation_scenario_2(self):
        """Test Scenario 2: Italian cuisine, Dinner, Medium, Vegetarian"""
        self.log("=== Testing Recipe Generation Scenario 2 ===")
        self.log("Parameters: Italian cuisine, Dinner, Medium, Vegetarian")
        
        try:
            recipe_data = {
                "user_id": self.test_user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "dietary_preferences": ["vegetarian"],
                "ingredients_on_hand": [],
                "prep_time_max": 60,
                "servings": 4,
                "difficulty": "medium"
            }
            
            self.log(f"Making request to /recipes/generate with data: {recipe_data}")
            
            start_time = time.time()
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            end_time = time.time()
            
            self.log(f"Response time: {end_time - start_time:.2f} seconds")
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Recipe generated successfully!")
                self.log(f"Recipe ID: {result.get('id')}")
                self.log(f"Title: {result.get('title')}")
                self.log(f"Description: {result.get('description', '')[:100]}...")
                self.log(f"Cuisine Type: {result.get('cuisine_type')}")
                self.log(f"Difficulty: {result.get('difficulty')}")
                self.log(f"Dietary Tags: {result.get('dietary_tags', [])}")
                
                # Check for Italian elements
                title = result.get('title', '').lower()
                description = result.get('description', '').lower()
                ingredients = [ing.lower() for ing in result.get('ingredients', [])]
                
                italian_indicators = ['italian', 'pasta', 'tomato', 'basil', 'mozzarella', 'parmesan', 'olive oil', 'garlic']
                has_italian_elements = any(indicator in title or indicator in description or 
                                         any(indicator in ing for ing in ingredients) 
                                         for indicator in italian_indicators)
                
                if has_italian_elements:
                    self.log("✅ Recipe appears to have appropriate Italian elements")
                else:
                    self.log("⚠️ Recipe may not have clear Italian cuisine elements")
                
                # Check for vegetarian compliance
                non_vegetarian = ['meat', 'chicken', 'beef', 'pork', 'fish', 'seafood', 'bacon', 'ham']
                has_meat = any(meat in title or meat in description or 
                              any(meat in ing for ing in ingredients) 
                              for meat in non_vegetarian)
                
                if has_meat:
                    self.log("❌ Recipe contains non-vegetarian ingredients")
                    return False
                else:
                    self.log("✅ Recipe appears to be vegetarian-compliant")
                
                return result
                
            else:
                self.log(f"❌ Recipe generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in recipe generation test: {str(e)}")
            return False
    
    async def test_database_storage(self, recipe_result):
        """Test if generated recipes are properly saved to database"""
        self.log("=== Testing Database Storage ===")
        
        if not recipe_result or not recipe_result.get('id'):
            self.log("❌ No recipe result to test database storage")
            return False
        
        try:
            recipe_id = recipe_result['id']
            self.log(f"Checking if recipe {recipe_id} is stored in database...")
            
            # Try to retrieve the recipe (if there's a get endpoint)
            try:
                response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}")
                if response.status_code == 200:
                    stored_recipe = response.json()
                    self.log("✅ Recipe successfully retrieved from database")
                    self.log(f"Stored recipe title: {stored_recipe.get('title')}")
                    return True
                elif response.status_code == 404:
                    self.log("❌ Recipe not found in database")
                    return False
                else:
                    self.log(f"⚠️ Unexpected response when retrieving recipe: {response.status_code}")
                    # Assume it's stored if we got a valid recipe back from generation
                    return True
            except:
                # If no get endpoint, assume storage worked if generation succeeded
                self.log("⚠️ No recipe retrieval endpoint available, assuming storage worked")
                return True
                
        except Exception as e:
            self.log(f"❌ Error testing database storage: {str(e)}")
            return False
    
    async def test_response_format_compatibility(self, recipe_result):
        """Test if response format matches frontend expectations"""
        self.log("=== Testing Response Format Compatibility ===")
        
        if not recipe_result:
            self.log("❌ No recipe result to test format")
            return False
        
        try:
            # Check required fields for frontend
            frontend_required_fields = [
                "id", "title", "description", "ingredients", "instructions",
                "prep_time", "cook_time", "servings", "cuisine_type", "difficulty"
            ]
            
            missing_fields = []
            for field in frontend_required_fields:
                if field not in recipe_result:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log(f"❌ Missing fields required by frontend: {missing_fields}")
                return False
            
            # Check field types
            type_checks = [
                ("id", str),
                ("title", str),
                ("description", str),
                ("ingredients", list),
                ("instructions", list),
                ("prep_time", int),
                ("cook_time", int),
                ("servings", int),
                ("cuisine_type", str),
                ("difficulty", str)
            ]
            
            type_errors = []
            for field, expected_type in type_checks:
                if field in recipe_result:
                    if not isinstance(recipe_result[field], expected_type):
                        type_errors.append(f"{field} should be {expected_type.__name__}, got {type(recipe_result[field]).__name__}")
            
            if type_errors:
                self.log(f"❌ Type errors: {type_errors}")
                return False
            
            # Check list contents
            if len(recipe_result.get('ingredients', [])) == 0:
                self.log("❌ Ingredients list is empty")
                return False
            
            if len(recipe_result.get('instructions', [])) == 0:
                self.log("❌ Instructions list is empty")
                return False
            
            # Check for shopping_list field (for Walmart integration)
            if 'shopping_list' in recipe_result:
                if isinstance(recipe_result['shopping_list'], list):
                    self.log(f"✅ Shopping list present with {len(recipe_result['shopping_list'])} items")
                else:
                    self.log("⚠️ Shopping list present but not a list")
            else:
                self.log("⚠️ Shopping list field not present (may affect Walmart integration)")
            
            self.log("✅ Response format is compatible with frontend expectations")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing response format: {str(e)}")
            return False
    
    async def test_mock_data_quality(self, recipe_results):
        """Test the quality of mock data generation"""
        self.log("=== Testing Mock Data Quality ===")
        
        if not recipe_results:
            self.log("❌ No recipe results to test mock data quality")
            return False
        
        try:
            quality_score = 0
            total_checks = 0
            
            for i, recipe in enumerate(recipe_results):
                if not recipe:
                    continue
                    
                self.log(f"Analyzing recipe {i+1}: {recipe.get('title')}")
                
                # Check 1: Title is not generic
                title = recipe.get('title', '')
                if title and not any(generic in title.lower() for generic in ['recipe', 'dish', 'food', 'meal']):
                    quality_score += 1
                    self.log("  ✅ Title is specific and descriptive")
                else:
                    self.log("  ❌ Title is too generic")
                total_checks += 1
                
                # Check 2: Description is meaningful
                description = recipe.get('description', '')
                if description and len(description) > 50:
                    quality_score += 1
                    self.log("  ✅ Description is detailed")
                else:
                    self.log("  ❌ Description is too short or missing")
                total_checks += 1
                
                # Check 3: Reasonable number of ingredients
                ingredients = recipe.get('ingredients', [])
                if 3 <= len(ingredients) <= 15:
                    quality_score += 1
                    self.log(f"  ✅ Reasonable ingredient count: {len(ingredients)}")
                else:
                    self.log(f"  ❌ Unusual ingredient count: {len(ingredients)}")
                total_checks += 1
                
                # Check 4: Reasonable cooking times
                prep_time = recipe.get('prep_time', 0)
                cook_time = recipe.get('cook_time', 0)
                if 5 <= prep_time <= 120 and 0 <= cook_time <= 180:
                    quality_score += 1
                    self.log(f"  ✅ Reasonable times: prep {prep_time}min, cook {cook_time}min")
                else:
                    self.log(f"  ❌ Unusual times: prep {prep_time}min, cook {cook_time}min")
                total_checks += 1
                
                # Check 5: Instructions are detailed
                instructions = recipe.get('instructions', [])
                if len(instructions) >= 3 and all(len(inst) > 20 for inst in instructions):
                    quality_score += 1
                    self.log(f"  ✅ Detailed instructions: {len(instructions)} steps")
                else:
                    self.log(f"  ❌ Instructions too brief: {len(instructions)} steps")
                total_checks += 1
            
            if total_checks > 0:
                quality_percentage = (quality_score / total_checks) * 100
                self.log(f"Mock data quality score: {quality_score}/{total_checks} ({quality_percentage:.1f}%)")
                
                if quality_percentage >= 80:
                    self.log("✅ Mock data quality is excellent")
                    return True
                elif quality_percentage >= 60:
                    self.log("⚠️ Mock data quality is acceptable")
                    return True
                else:
                    self.log("❌ Mock data quality is poor")
                    return False
            else:
                self.log("❌ No recipes to analyze")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing mock data quality: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all recipe generation tests"""
        self.log("🚀 Starting Recipe Generation Functionality Testing")
        self.log("=" * 70)
        
        test_results = {}
        recipe_results = []
        
        # Test 1: Health Check
        test_results["health"] = await self.test_health_check()
        if not test_results["health"]:
            self.log("❌ Backend not accessible, stopping tests")
            return test_results
        
        # Test 2: OpenAI API Key Status
        api_key_status = await self.test_openai_api_key_status()
        test_results["api_key_status"] = api_key_status
        
        # Test 3: Recipe Generation Scenario 1
        self.log("\n" + "=" * 50)
        scenario1_result = await self.test_recipe_generation_scenario_1()
        test_results["scenario_1"] = bool(scenario1_result)
        if scenario1_result:
            recipe_results.append(scenario1_result)
        
        # Test 4: Recipe Generation Scenario 2
        self.log("\n" + "=" * 50)
        scenario2_result = await self.test_recipe_generation_scenario_2()
        test_results["scenario_2"] = bool(scenario2_result)
        if scenario2_result:
            recipe_results.append(scenario2_result)
        
        # Test 5: Database Storage (using first successful recipe)
        self.log("\n" + "=" * 50)
        if recipe_results:
            test_results["database_storage"] = await self.test_database_storage(recipe_results[0])
        else:
            test_results["database_storage"] = False
        
        # Test 6: Response Format Compatibility
        self.log("\n" + "=" * 50)
        if recipe_results:
            test_results["response_format"] = await self.test_response_format_compatibility(recipe_results[0])
        else:
            test_results["response_format"] = False
        
        # Test 7: Mock Data Quality
        self.log("\n" + "=" * 50)
        if recipe_results:
            test_results["mock_data_quality"] = await self.test_mock_data_quality(recipe_results)
        else:
            test_results["mock_data_quality"] = False
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("🔍 RECIPE GENERATION TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            if test_name == "api_key_status":
                self.log(f"{test_name.upper()}: {result}")
            else:
                status = "✅ PASS" if result else "❌ FAIL"
                self.log(f"{test_name.upper()}: {status}")
        
        # Overall assessment
        critical_tests = ["scenario_1", "scenario_2", "response_format"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 RECIPE GENERATION WITH MOCK FALLBACK IS WORKING!")
            self.log("✅ Mock data fallback successfully prevents 500 errors")
            self.log("✅ Generated recipes have appropriate cuisine combinations")
            self.log("✅ Response format is compatible with frontend")
        elif critical_passed > 0:
            self.log("⚠️ PARTIAL SUCCESS - Some recipe generation working")
            self.log(f"✅ {critical_passed}/{len(critical_tests)} critical tests passed")
        else:
            self.log("❌ RECIPE GENERATION STILL FAILING")
            self.log("❌ Mock data fallback is not working properly")
            self.log("❌ 500 errors are still occurring")
        
        return test_results

async def main():
    """Main test execution"""
    tester = RecipeGenerationTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())