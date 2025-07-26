#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for AI Recipe + Grocery Delivery App
Focus: Test OpenAI API integration, Starbucks generator, Walmart API, User Auth, Recipe Storage, and Cart Options
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

# Add backend to path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://6b4e57e4-7e21-4efb-941c-e036b94930bd.preview.emergentagent.com/api"
TEST_USER_EMAIL = "aitest.user@example.com"
TEST_USER_PASSWORD = "testpass123"

class AIRecipeAppTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)  # Increased timeout for AI calls
        self.user_id = None
        self.recipe_id = None
        self.starbucks_recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_environment_variables(self):
        """Test 1: Verify all required environment variables are loaded"""
        self.log("=== Testing Environment Variables ===")
        
        try:
            # Import backend modules to check environment
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Load environment variables
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            # Check OpenAI API Key
            openai_key = os.environ.get('OPENAI_API_KEY')
            self.log(f"OPENAI_API_KEY: {'✅ Present' if openai_key else '❌ Missing'}")
            if openai_key:
                self.log(f"OpenAI Key: {openai_key[:20]}...")
            
            # Check Walmart API credentials
            walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')
            walmart_key_version = os.environ.get('WALMART_KEY_VERSION')
            
            self.log(f"WALMART_CONSUMER_ID: {'✅ Present' if walmart_consumer_id else '❌ Missing'}")
            self.log(f"WALMART_PRIVATE_KEY: {'✅ Present' if walmart_private_key else '❌ Missing'}")
            self.log(f"WALMART_KEY_VERSION: {'✅ Present' if walmart_key_version else '❌ Missing'}")
            
            # Check MongoDB connection
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME')
            self.log(f"MONGO_URL: {'✅ Present' if mongo_url else '❌ Missing'}")
            self.log(f"DB_NAME: {'✅ Present' if db_name else '❌ Missing'}")
            
            if mongo_url:
                self.log(f"MongoDB URL: {mongo_url}")
            if db_name:
                self.log(f"Database Name: {db_name}")
            
            return all([openai_key, walmart_consumer_id, walmart_private_key, walmart_key_version, mongo_url, db_name])
            
        except Exception as e:
            self.log(f"❌ Error checking environment variables: {str(e)}", "ERROR")
            return False
    
    async def test_user_authentication(self):
        """Test 2: Test user registration, verification, and login"""
        self.log("=== Testing User Authentication ===")
        
        try:
            # Generate unique email for this test run
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            test_email = f"aitest.{random_suffix}@example.com"
            
            # Step 1: Register new user
            self.log("Step 1: Registering new user...")
            user_data = {
                "first_name": "AI",
                "last_name": "Tester",
                "email": test_email,
                "password": TEST_USER_PASSWORD,
                "dietary_preferences": ["Vegetarian"],
                "allergies": ["Nuts"],
                "favorite_cuisines": ["Italian", "Mexican"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                self.log(f"✅ User registered successfully: {self.user_id}")
                
                # Step 2: Get verification code and verify
                self.log("Step 2: Verifying user email...")
                debug_response = await self.client.get(f"{BACKEND_URL}/debug/verification-codes/{test_email}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    if debug_data.get("codes"):
                        verify_code = debug_data["codes"][0]["code"]
                        
                        verify_data = {
                            "email": test_email,
                            "code": verify_code
                        }
                        
                        verify_response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                        if verify_response.status_code == 200:
                            self.log("✅ User verified successfully")
                        else:
                            self.log(f"❌ User verification failed: {verify_response.text}")
                            return False
                
                # Step 3: Test login
                self.log("Step 3: Testing user login...")
                login_data = {
                    "email": test_email,
                    "password": TEST_USER_PASSWORD
                }
                
                login_response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                if login_response.status_code == 200:
                    login_result = login_response.json()
                    if login_result.get("status") == "success":
                        self.log("✅ User login successful")
                        self.user_id = login_result.get("user_id")
                        return True
                    else:
                        self.log(f"❌ Login failed: {login_result}")
                        return False
                else:
                    self.log(f"❌ Login request failed: {login_response.text}")
                    return False
                    
            else:
                self.log(f"❌ User registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in user authentication test: {str(e)}", "ERROR")
            return False
    
    async def test_openai_recipe_generation(self):
        """Test 3: Test OpenAI API integration for recipe generation"""
        self.log("=== Testing OpenAI Recipe Generation ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for recipe generation test")
            return False
        
        try:
            # Test different recipe categories and dietary preferences
            test_scenarios = [
                {
                    "name": "Italian Cuisine with Vegetarian preference",
                    "data": {
                        "user_id": self.user_id,
                        "recipe_category": "cuisine",
                        "cuisine_type": "Italian",
                        "dietary_preferences": ["Vegetarian"],
                        "ingredients_on_hand": [],
                        "prep_time_max": 45,
                        "servings": 4,
                        "difficulty": "medium"
                    }
                },
                {
                    "name": "Healthy Snack with Gluten-Free preference",
                    "data": {
                        "user_id": self.user_id,
                        "recipe_category": "snack",
                        "dietary_preferences": ["Gluten-Free"],
                        "ingredients_on_hand": ["almonds", "honey"],
                        "prep_time_max": 20,
                        "servings": 2,
                        "difficulty": "easy",
                        "is_healthy": True,
                        "max_calories_per_serving": 200
                    }
                },
                {
                    "name": "Refreshing Beverage",
                    "data": {
                        "user_id": self.user_id,
                        "recipe_category": "beverage",
                        "dietary_preferences": [],
                        "ingredients_on_hand": ["lemon", "mint"],
                        "prep_time_max": 10,
                        "servings": 2,
                        "difficulty": "easy"
                    }
                }
            ]
            
            successful_tests = 0
            
            for scenario in test_scenarios:
                self.log(f"Testing: {scenario['name']}")
                
                try:
                    response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=scenario["data"])
                    
                    if response.status_code == 200:
                        result = response.json()
                        recipe_title = result.get("title", "Unknown")
                        recipe_id = result.get("id")
                        shopping_list = result.get("shopping_list", [])
                        ingredients = result.get("ingredients", [])
                        instructions = result.get("instructions", [])
                        
                        self.log(f"✅ Recipe generated: {recipe_title}")
                        self.log(f"   Recipe ID: {recipe_id}")
                        self.log(f"   Ingredients: {len(ingredients)} items")
                        self.log(f"   Instructions: {len(instructions)} steps")
                        self.log(f"   Shopping list: {len(shopping_list)} items")
                        
                        # Store first recipe ID for later tests
                        if not self.recipe_id:
                            self.recipe_id = recipe_id
                        
                        successful_tests += 1
                        
                    else:
                        self.log(f"❌ Recipe generation failed for {scenario['name']}: {response.text}")
                        
                except Exception as e:
                    self.log(f"❌ Error testing {scenario['name']}: {str(e)}")
            
            self.log(f"Recipe generation test results: {successful_tests}/{len(test_scenarios)} successful")
            return successful_tests > 0
            
        except Exception as e:
            self.log(f"❌ Error in OpenAI recipe generation test: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_generator(self):
        """Test 4: Test AI-powered Starbucks drink generation"""
        self.log("=== Testing Starbucks Generator ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for Starbucks generation test")
            return False
        
        try:
            # Test different drink types and flavor inspirations
            test_scenarios = [
                {
                    "name": "Frappuccino with vanilla inspiration",
                    "data": {
                        "user_id": self.user_id,
                        "drink_type": "frappuccino",
                        "flavor_inspiration": "vanilla bean"
                    }
                },
                {
                    "name": "Refresher with tropical inspiration",
                    "data": {
                        "user_id": self.user_id,
                        "drink_type": "refresher",
                        "flavor_inspiration": "tropical mango"
                    }
                },
                {
                    "name": "Iced Matcha Latte with strawberry inspiration",
                    "data": {
                        "user_id": self.user_id,
                        "drink_type": "iced_matcha_latte",
                        "flavor_inspiration": "strawberry"
                    }
                },
                {
                    "name": "Random drink type",
                    "data": {
                        "user_id": self.user_id,
                        "drink_type": "random"
                    }
                }
            ]
            
            successful_tests = 0
            
            for scenario in test_scenarios:
                self.log(f"Testing: {scenario['name']}")
                
                try:
                    response = await self.client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=scenario["data"])
                    
                    if response.status_code == 200:
                        result = response.json()
                        drink_name = result.get("drink_name", "Unknown")
                        base_drink = result.get("base_drink", "Unknown")
                        modifications = result.get("modifications", [])
                        ordering_script = result.get("ordering_script", "")
                        category = result.get("category", "Unknown")
                        
                        self.log(f"✅ Starbucks drink generated: {drink_name}")
                        self.log(f"   Base: {base_drink}")
                        self.log(f"   Category: {category}")
                        self.log(f"   Modifications: {len(modifications)} items")
                        self.log(f"   Has ordering script: {'Yes' if ordering_script else 'No'}")
                        
                        # Store first drink ID for later tests
                        if not self.starbucks_recipe_id:
                            self.starbucks_recipe_id = result.get("id")
                        
                        successful_tests += 1
                        
                    else:
                        self.log(f"❌ Starbucks generation failed for {scenario['name']}: {response.text}")
                        
                except Exception as e:
                    self.log(f"❌ Error testing {scenario['name']}: {str(e)}")
            
            self.log(f"Starbucks generation test results: {successful_tests}/{len(test_scenarios)} successful")
            return successful_tests > 0
            
        except Exception as e:
            self.log(f"❌ Error in Starbucks generator test: {str(e)}", "ERROR")
            return False
    
    async def test_walmart_integration(self):
        """Test 5: Test Walmart API integration for product search"""
        self.log("=== Testing Walmart API Integration ===")
        
        if not self.user_id or not self.recipe_id:
            self.log("❌ No user_id or recipe_id available for Walmart integration test")
            return False
        
        try:
            # Test cart options endpoint
            params = {
                "recipe_id": self.recipe_id,
                "user_id": self.user_id
            }
            
            self.log(f"Testing /grocery/cart-options with params: {params}")
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params=params)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Cart options endpoint responded successfully")
                self.log(f"Recipe ID: {result.get('recipe_id')}")
                self.log(f"User ID: {result.get('user_id')}")
                self.log(f"Total products: {result.get('total_products', 0)}")
                self.log(f"Ingredient options count: {len(result.get('ingredient_options', []))}")
                
                if result.get('message'):
                    self.log(f"Message: {result['message']}")
                
                ingredient_options = result.get('ingredient_options', [])
                if ingredient_options:
                    for option in ingredient_options:
                        ingredient_name = option.get('ingredient_name')
                        products = option.get('options', [])
                        self.log(f"  {ingredient_name}: {len(products)} products")
                        for product in products[:2]:  # Show first 2 products
                            self.log(f"    - {product.get('name')} - ${product.get('price')}")
                    
                    return result.get('total_products', 0) > 0
                else:
                    self.log("❌ No ingredient options returned")
                    return False
                
            else:
                self.log(f"❌ Cart options endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Walmart integration: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_storage(self):
        """Test 6: Test recipe storage in MongoDB database"""
        self.log("=== Testing Recipe Storage ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for recipe storage test")
            return False
        
        try:
            # Test getting user's recipes
            response = await self.client.get(f"{BACKEND_URL}/recipes", params={"user_id": self.user_id})
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Retrieved {len(recipes)} recipes from database")
                
                if recipes:
                    for i, recipe in enumerate(recipes[:3]):  # Show first 3 recipes
                        self.log(f"  Recipe {i+1}: {recipe.get('title', 'Unknown')} (ID: {recipe.get('id', 'Unknown')})")
                    
                    return True
                else:
                    self.log("⚠️ No recipes found in database (this might be expected for new user)")
                    return True  # Not necessarily a failure
                    
            else:
                self.log(f"❌ Failed to retrieve recipes: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe storage: {str(e)}", "ERROR")
            return False
    
    async def test_curated_starbucks_recipes(self):
        """Test 7: Test curated Starbucks recipes endpoint"""
        self.log("=== Testing Curated Starbucks Recipes ===")
        
        try:
            # Test getting curated recipes
            response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Retrieved {total} curated Starbucks recipes")
                
                if recipes:
                    # Test different categories
                    categories = ["frappuccino", "refresher", "iced_matcha_latte", "lemonade"]
                    
                    for category in categories:
                        cat_response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes", params={"category": category})
                        if cat_response.status_code == 200:
                            cat_result = cat_response.json()
                            cat_recipes = cat_result.get("recipes", [])
                            self.log(f"  {category}: {len(cat_recipes)} recipes")
                        else:
                            self.log(f"  ❌ Failed to get {category} recipes")
                    
                    return True
                else:
                    self.log("❌ No curated recipes found")
                    return False
                    
            else:
                self.log(f"❌ Failed to retrieve curated recipes: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing curated Starbucks recipes: {str(e)}", "ERROR")
            return False
    
    async def test_error_handling(self):
        """Test 8: Test error handling for invalid inputs"""
        self.log("=== Testing Error Handling ===")
        
        try:
            successful_tests = 0
            total_tests = 0
            
            # Test 1: Invalid recipe generation request
            total_tests += 1
            try:
                invalid_recipe_data = {
                    "user_id": "invalid-user-id",
                    "recipe_category": "invalid-category"
                }
                
                response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=invalid_recipe_data)
                
                if response.status_code in [400, 422, 404]:  # Expected error codes
                    self.log("✅ Recipe generation properly handles invalid input")
                    successful_tests += 1
                else:
                    self.log(f"⚠️ Unexpected response for invalid recipe input: {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ Error testing invalid recipe input: {str(e)}")
            
            # Test 2: Invalid Starbucks drink request
            total_tests += 1
            try:
                invalid_starbucks_data = {
                    "user_id": "invalid-user-id",
                    "drink_type": "invalid-drink-type"
                }
                
                response = await self.client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=invalid_starbucks_data)
                
                if response.status_code in [400, 422, 404]:  # Expected error codes
                    self.log("✅ Starbucks generation properly handles invalid input")
                    successful_tests += 1
                else:
                    self.log(f"⚠️ Unexpected response for invalid Starbucks input: {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ Error testing invalid Starbucks input: {str(e)}")
            
            # Test 3: Invalid cart options request
            total_tests += 1
            try:
                invalid_params = {
                    "recipe_id": "invalid-recipe-id",
                    "user_id": "invalid-user-id"
                }
                
                response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params=invalid_params)
                
                if response.status_code in [400, 422, 404]:  # Expected error codes
                    self.log("✅ Cart options properly handles invalid input")
                    successful_tests += 1
                else:
                    self.log(f"⚠️ Unexpected response for invalid cart options input: {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ Error testing invalid cart options input: {str(e)}")
            
            self.log(f"Error handling test results: {successful_tests}/{total_tests} successful")
            return successful_tests > 0
            
        except Exception as e:
            self.log(f"❌ Error in error handling test: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Comprehensive AI Recipe + Grocery Delivery App Backend Tests")
        self.log("=" * 80)
        
        test_results = {}
        
        # Test 1: Environment Variables
        test_results["environment_variables"] = await self.test_environment_variables()
        
        # Test 2: User Authentication
        test_results["user_authentication"] = await self.test_user_authentication()
        
        # Test 3: OpenAI Recipe Generation
        if test_results["user_authentication"]:
            test_results["openai_recipe_generation"] = await self.test_openai_recipe_generation()
        else:
            test_results["openai_recipe_generation"] = False
        
        # Test 4: Starbucks Generator
        if test_results["user_authentication"]:
            test_results["starbucks_generator"] = await self.test_starbucks_generator()
        else:
            test_results["starbucks_generator"] = False
        
        # Test 5: Walmart Integration
        if test_results["openai_recipe_generation"]:
            test_results["walmart_integration"] = await self.test_walmart_integration()
        else:
            test_results["walmart_integration"] = False
        
        # Test 6: Recipe Storage
        if test_results["user_authentication"]:
            test_results["recipe_storage"] = await self.test_recipe_storage()
        else:
            test_results["recipe_storage"] = False
        
        # Test 7: Curated Starbucks Recipes
        test_results["curated_starbucks_recipes"] = await self.test_curated_starbucks_recipes()
        
        # Test 8: Error Handling
        test_results["error_handling"] = await self.test_error_handling()
        
        # Summary
        self.log("=" * 80)
        self.log("🔍 COMPREHENSIVE TEST RESULTS SUMMARY")
        self.log("=" * 80)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = [
            "environment_variables", 
            "user_authentication", 
            "openai_recipe_generation", 
            "starbucks_generator", 
            "walmart_integration"
        ]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        total_passed = sum(1 for result in test_results.values() if result)
        
        self.log("=" * 80)
        self.log(f"📊 OVERALL RESULTS: {total_passed}/{len(test_results)} tests passed")
        self.log(f"🎯 CRITICAL TESTS: {critical_passed}/{len(critical_tests)} passed")
        
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED - AI Recipe + Grocery Delivery App backend is working correctly!")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("environment_variables"):
                self.log("  - Missing or invalid environment variables (OpenAI, Walmart, MongoDB)")
            if not test_results.get("user_authentication"):
                self.log("  - User authentication system not working")
            if not test_results.get("openai_recipe_generation"):
                self.log("  - OpenAI API integration for recipe generation failing")
            if not test_results.get("starbucks_generator"):
                self.log("  - AI-powered Starbucks drink generation failing")
            if not test_results.get("walmart_integration"):
                self.log("  - Walmart API integration not returning products")
        
        return test_results

async def main():
    """Main test execution"""
    tester = AIRecipeAppTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())