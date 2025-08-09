#!/usr/bin/env python3
"""
Enhanced Recipe Generation System Testing Script
Testing the improved recipe generation system with session management and UI improvements
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import string
import time

# Load environment variables
from dotenv import load_dotenv
from pathlib import Path
env_path = Path('/app/backend/.env')
load_dotenv(env_path)

# Get backend URL from frontend environment
frontend_env_path = Path('/app/frontend/.env')
load_dotenv(frontend_env_path)
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

class EnhancedRecipeSystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user_id = None
        self.test_user_email = f"test_user_{int(time.time())}@example.com"
        self.test_user_password = "testpass123"
        self.generated_recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_backend_health(self):
        """Test 1: Verify backend is accessible"""
        self.log("=== Testing Backend Health ===")
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/health")
            
            if response.status_code == 200:
                self.log("✅ Backend is healthy and accessible")
                return True
            else:
                self.log(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Backend connection failed: {str(e)}", "ERROR")
            return False
    
    async def test_session_management(self):
        """Test 2: Test session management with 7-day expiry feature"""
        self.log("=== Testing Session Management with 7-Day Expiry ===")
        
        try:
            # Register a new test user
            user_data = {
                "first_name": "Enhanced",
                "last_name": "Tester",
                "email": self.test_user_email,
                "password": self.test_user_password,
                "dietary_preferences": ["Vegetarian"],
                "allergies": [],
                "favorite_cuisines": ["Italian"]
            }
            
            response = await self.client.post(f"{API_BASE_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.test_user_id = result.get("user_id")
                self.log(f"✅ User registered successfully: {self.test_user_id}")
                
                # Verify the user has 7-day trial period
                user_response = await self.client.get(f"{API_BASE_URL}/users/{self.test_user_id}")
                if user_response.status_code == 200:
                    user_info = user_response.json()
                    trial_end_date = user_info.get("trial_end_date")
                    
                    if trial_end_date:
                        # Parse trial end date
                        from dateutil import parser
                        trial_end = parser.parse(trial_end_date)
                        trial_start = parser.parse(user_info.get("trial_start_date", user_info.get("created_at")))
                        trial_duration = (trial_end - trial_start).days
                        
                        self.log(f"✅ Trial period configured: {trial_duration} days")
                        self.log(f"Trial ends: {trial_end_date}")
                        
                        if trial_duration >= 7:
                            self.log("✅ 7-day trial period correctly configured")
                            return True
                        else:
                            self.log(f"❌ Trial period is only {trial_duration} days, expected 7+")
                            return False
                    else:
                        self.log("❌ No trial end date found")
                        return False
                else:
                    self.log("❌ Could not retrieve user information")
                    return False
            else:
                self.log(f"❌ User registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Session management test failed: {str(e)}", "ERROR")
            return False
    
    async def test_enhanced_recipe_generation_step_by_step(self):
        """Test 3: Test enhanced recipe generation with step-by-step parameters"""
        self.log("=== Testing Enhanced Recipe Generation Step-by-Step ===")
        
        if not self.test_user_id:
            self.log("❌ No test user available for recipe generation")
            return False
        
        try:
            # Step 1: cuisine: "Italian", meal_type: "dinner"
            self.log("Step 1: Testing cuisine and meal_type parameters")
            
            step1_data = {
                "user_id": self.test_user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "meal_type": "dinner"
            }
            
            # Step 2: difficulty: "medium"
            self.log("Step 2: Adding difficulty parameter")
            step1_data["difficulty"] = "medium"
            
            # Step 3: servings: 4, prep_time: "30 minutes", dietary_restrictions: "Vegetarian"
            self.log("Step 3: Adding servings, prep_time, and dietary restrictions")
            step1_data.update({
                "servings": 4,
                "prep_time_max": 30,
                "dietary_preferences": ["Vegetarian"]
            })
            
            # Step 4: Generate recipe and verify all fields are returned
            self.log("Step 4: Generating recipe with all parameters")
            
            response = await self.client.post(f"{API_BASE_URL}/recipes/generate", json=step1_data)
            
            if response.status_code == 200:
                recipe = response.json()
                self.generated_recipe_id = recipe.get("id")
                
                self.log("✅ Recipe generated successfully")
                self.log(f"Recipe ID: {self.generated_recipe_id}")
                self.log(f"Recipe Title: {recipe.get('title', 'N/A')}")
                self.log(f"Cuisine Type: {recipe.get('cuisine_type', 'N/A')}")
                self.log(f"Difficulty: {recipe.get('difficulty', 'N/A')}")
                self.log(f"Servings: {recipe.get('servings', 'N/A')}")
                self.log(f"Prep Time: {recipe.get('prep_time', 'N/A')} minutes")
                self.log(f"Cook Time: {recipe.get('cook_time', 'N/A')} minutes")
                
                # Verify all required fields are present
                required_fields = ['id', 'title', 'description', 'ingredients', 'instructions', 
                                 'prep_time', 'cook_time', 'servings', 'cuisine_type', 'difficulty']
                
                missing_fields = []
                for field in required_fields:
                    if field not in recipe or recipe[field] is None:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log("✅ All required fields present in recipe response")
                    
                    # Verify dietary restrictions are respected
                    ingredients = recipe.get('ingredients', [])
                    self.log(f"Ingredients count: {len(ingredients)}")
                    
                    # Check if recipe appears to be vegetarian (basic check)
                    meat_keywords = ['beef', 'chicken', 'pork', 'fish', 'meat', 'bacon', 'ham']
                    has_meat = any(any(keyword in ingredient.lower() for keyword in meat_keywords) 
                                 for ingredient in ingredients)
                    
                    if not has_meat:
                        self.log("✅ Recipe appears to respect vegetarian dietary restriction")
                    else:
                        self.log("⚠️ Recipe may contain meat ingredients despite vegetarian restriction")
                    
                    return True
                else:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                    return False
            else:
                self.log(f"❌ Recipe generation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Enhanced recipe generation test failed: {str(e)}", "ERROR")
            return False
    
    async def test_data_mapping(self):
        """Test 4: Test data mapping between frontend and backend"""
        self.log("=== Testing Data Mapping Between Frontend and Backend ===")
        
        if not self.test_user_id:
            self.log("❌ No test user available for data mapping test")
            return False
        
        try:
            # Test various data formats that frontend might send
            test_cases = [
                {
                    "name": "Standard Format",
                    "data": {
                        "user_id": self.test_user_id,
                        "recipe_category": "cuisine",
                        "cuisine_type": "Chinese",
                        "difficulty": "easy",
                        "servings": 2,
                        "prep_time_max": 15,
                        "dietary_preferences": ["Gluten-free"]
                    }
                },
                {
                    "name": "Extended Format",
                    "data": {
                        "user_id": self.test_user_id,
                        "recipe_category": "snack",
                        "cuisine_type": "Mexican",
                        "difficulty": "hard",
                        "servings": 6,
                        "prep_time_max": 45,
                        "dietary_preferences": ["Vegan", "Low-sodium"],
                        "ingredients_on_hand": ["tomatoes", "avocado", "lime"],
                        "is_healthy": True,
                        "max_calories_per_serving": 300
                    }
                }
            ]
            
            for test_case in test_cases:
                self.log(f"Testing {test_case['name']} data mapping")
                
                response = await self.client.post(f"{API_BASE_URL}/recipes/generate", json=test_case['data'])
                
                if response.status_code == 200:
                    recipe = response.json()
                    
                    # Verify that input parameters are reflected in output
                    expected_cuisine = test_case['data']['cuisine_type']
                    expected_difficulty = test_case['data']['difficulty']
                    expected_servings = test_case['data']['servings']
                    
                    actual_cuisine = recipe.get('cuisine_type', '')
                    actual_difficulty = recipe.get('difficulty', '')
                    actual_servings = recipe.get('servings', 0)
                    
                    mapping_success = True
                    
                    if expected_cuisine.lower() not in actual_cuisine.lower():
                        self.log(f"⚠️ Cuisine mapping issue: expected {expected_cuisine}, got {actual_cuisine}")
                        mapping_success = False
                    
                    if expected_difficulty != actual_difficulty:
                        self.log(f"⚠️ Difficulty mapping issue: expected {expected_difficulty}, got {actual_difficulty}")
                        mapping_success = False
                    
                    if expected_servings != actual_servings:
                        self.log(f"⚠️ Servings mapping issue: expected {expected_servings}, got {actual_servings}")
                        mapping_success = False
                    
                    if mapping_success:
                        self.log(f"✅ {test_case['name']} data mapping successful")
                    else:
                        self.log(f"❌ {test_case['name']} data mapping failed")
                        return False
                else:
                    self.log(f"❌ {test_case['name']} request failed: {response.text}")
                    return False
            
            self.log("✅ All data mapping tests passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Data mapping test failed: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_quality_mock_fallback(self):
        """Test 5: Test recipe quality with mock data fallback"""
        self.log("=== Testing Recipe Quality with Mock Data Fallback ===")
        
        if not self.test_user_id:
            self.log("❌ No test user available for recipe quality test")
            return False
        
        try:
            # Test different cuisines to verify mock data quality
            cuisines_to_test = ["Italian", "Chinese", "Mexican", "Indian", "French"]
            
            for cuisine in cuisines_to_test:
                self.log(f"Testing mock data quality for {cuisine} cuisine")
                
                recipe_data = {
                    "user_id": self.test_user_id,
                    "recipe_category": "cuisine",
                    "cuisine_type": cuisine,
                    "difficulty": "medium",
                    "servings": 4,
                    "prep_time_max": 30
                }
                
                response = await self.client.post(f"{API_BASE_URL}/recipes/generate", json=recipe_data)
                
                if response.status_code == 200:
                    recipe = response.json()
                    
                    # Analyze recipe quality
                    title = recipe.get('title', '').lower()
                    description = recipe.get('description', '').lower()
                    ingredients = recipe.get('ingredients', [])
                    
                    # Check if recipe is cuisine-appropriate
                    cuisine_keywords = {
                        'Italian': ['pasta', 'tomato', 'basil', 'parmesan', 'olive oil', 'garlic'],
                        'Chinese': ['soy sauce', 'ginger', 'garlic', 'rice', 'sesame', 'scallion'],
                        'Mexican': ['cumin', 'chili', 'lime', 'cilantro', 'pepper', 'onion'],
                        'Indian': ['curry', 'turmeric', 'garam masala', 'ginger', 'garlic', 'rice'],
                        'French': ['butter', 'wine', 'herbs', 'cream', 'onion', 'garlic']
                    }
                    
                    expected_keywords = cuisine_keywords.get(cuisine, [])
                    found_keywords = []
                    
                    # Check title and description
                    for keyword in expected_keywords:
                        if keyword in title or keyword in description:
                            found_keywords.append(keyword)
                    
                    # Check ingredients
                    for keyword in expected_keywords:
                        for ingredient in ingredients:
                            if keyword in ingredient.lower():
                                found_keywords.append(keyword)
                                break
                    
                    # Remove duplicates
                    found_keywords = list(set(found_keywords))
                    
                    appropriateness_score = len(found_keywords)
                    self.log(f"Cuisine appropriateness score for {cuisine}: {appropriateness_score}/10")
                    self.log(f"Found keywords: {found_keywords}")
                    
                    if appropriateness_score >= 2:  # At least 2 appropriate keywords
                        self.log(f"✅ {cuisine} recipe quality acceptable")
                    else:
                        self.log(f"⚠️ {cuisine} recipe quality could be improved")
                        
                    # Check basic recipe structure
                    if (len(ingredients) >= 3 and 
                        len(recipe.get('instructions', [])) >= 3 and
                        recipe.get('prep_time', 0) > 0):
                        self.log(f"✅ {cuisine} recipe structure is complete")
                    else:
                        self.log(f"❌ {cuisine} recipe structure is incomplete")
                        return False
                        
                else:
                    self.log(f"❌ {cuisine} recipe generation failed: {response.text}")
                    return False
            
            self.log("✅ Recipe quality test completed successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Recipe quality test failed: {str(e)}", "ERROR")
            return False
    
    async def test_error_handling(self):
        """Test 6: Test error handling for invalid requests"""
        self.log("=== Testing Error Handling for Invalid Requests ===")
        
        try:
            error_test_cases = [
                {
                    "name": "Missing user_id",
                    "data": {
                        "recipe_category": "cuisine",
                        "cuisine_type": "Italian"
                    },
                    "expected_status": [400, 422]
                },
                {
                    "name": "Invalid cuisine_type",
                    "data": {
                        "user_id": self.test_user_id or "test_user",
                        "recipe_category": "cuisine",
                        "cuisine_type": "InvalidCuisine123"
                    },
                    "expected_status": [200, 400]  # Should either work or fail gracefully
                },
                {
                    "name": "Negative servings",
                    "data": {
                        "user_id": self.test_user_id or "test_user",
                        "recipe_category": "cuisine",
                        "cuisine_type": "Italian",
                        "servings": -5
                    },
                    "expected_status": [400, 422]
                },
                {
                    "name": "Invalid difficulty",
                    "data": {
                        "user_id": self.test_user_id or "test_user",
                        "recipe_category": "cuisine",
                        "cuisine_type": "Italian",
                        "difficulty": "impossible"
                    },
                    "expected_status": [200, 400]  # Should either work or fail gracefully
                }
            ]
            
            for test_case in error_test_cases:
                self.log(f"Testing error handling: {test_case['name']}")
                
                response = await self.client.post(f"{API_BASE_URL}/recipes/generate", json=test_case['data'])
                
                if response.status_code in test_case['expected_status']:
                    if response.status_code >= 400:
                        self.log(f"✅ Correctly rejected invalid request with status {response.status_code}")
                    else:
                        self.log(f"✅ Gracefully handled edge case with status {response.status_code}")
                else:
                    self.log(f"❌ Unexpected status code {response.status_code}, expected one of {test_case['expected_status']}")
                    return False
            
            self.log("✅ Error handling tests completed successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test failed: {str(e)}", "ERROR")
            return False
    
    async def test_subscription_access_control(self):
        """Test 7: Test subscription access control for premium features"""
        self.log("=== Testing Subscription Access Control ===")
        
        if not self.test_user_id:
            self.log("❌ No test user available for subscription test")
            return False
        
        try:
            # Test subscription status endpoint
            response = await self.client.get(f"{API_BASE_URL}/subscription/status/{self.test_user_id}")
            
            if response.status_code == 200:
                subscription_info = response.json()
                
                self.log(f"Subscription status: {subscription_info.get('subscription_status', 'N/A')}")
                self.log(f"Has access: {subscription_info.get('has_access', False)}")
                self.log(f"Trial active: {subscription_info.get('trial_active', False)}")
                
                # Verify user has access during trial period
                if subscription_info.get('has_access') and subscription_info.get('trial_active'):
                    self.log("✅ User has proper trial access")
                    
                    # Test premium feature access (recipe generation)
                    recipe_data = {
                        "user_id": self.test_user_id,
                        "recipe_category": "cuisine",
                        "cuisine_type": "Italian"
                    }
                    
                    recipe_response = await self.client.post(f"{API_BASE_URL}/recipes/generate", json=recipe_data)
                    
                    if recipe_response.status_code == 200:
                        self.log("✅ Premium feature (recipe generation) accessible during trial")
                        return True
                    else:
                        self.log(f"❌ Premium feature blocked despite trial access: {recipe_response.text}")
                        return False
                else:
                    self.log("❌ User does not have proper trial access")
                    return False
            else:
                self.log(f"❌ Subscription status check failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Subscription access test failed: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all enhanced recipe system tests"""
        self.log("🚀 Starting Enhanced Recipe Generation System Tests")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Backend Health
        test_results["backend_health"] = await self.test_backend_health()
        
        # Test 2: Session Management
        test_results["session_management"] = await self.test_session_management()
        
        # Test 3: Enhanced Recipe Generation
        test_results["enhanced_recipe_generation"] = await self.test_enhanced_recipe_generation_step_by_step()
        
        # Test 4: Data Mapping
        test_results["data_mapping"] = await self.test_data_mapping()
        
        # Test 5: Recipe Quality
        test_results["recipe_quality"] = await self.test_recipe_quality_mock_fallback()
        
        # Test 6: Error Handling
        test_results["error_handling"] = await self.test_error_handling()
        
        # Test 7: Subscription Access
        test_results["subscription_access"] = await self.test_subscription_access_control()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 ENHANCED RECIPE SYSTEM TEST RESULTS")
        self.log("=" * 70)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
            if result:
                passed_tests += 1
        
        # Overall assessment
        self.log("=" * 70)
        self.log(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - Enhanced recipe generation system is working correctly!")
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            self.log("✅ MOSTLY WORKING - Enhanced recipe generation system is functional with minor issues")
        else:
            self.log("❌ SIGNIFICANT ISSUES - Enhanced recipe generation system needs attention")
        
        return test_results

async def main():
    """Main test execution"""
    tester = EnhancedRecipeSystemTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())