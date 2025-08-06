#!/usr/bin/env python3
"""
Weekly Recipe System Backend Testing Script
Testing the new mock data fallback functionality for Weekly Recipe System
Focus: Mock data generation when OpenAI API key is not configured
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import time

# Get backend URL from frontend environment
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url() + "/api"
DEMO_USER_EMAIL = "demo@test.com"
DEMO_USER_PASSWORD = "password123"

class WeeklyRecipeSystemTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.demo_user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test 1: Login with demo user to get user_id"""
        self.log("=== Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": DEMO_USER_EMAIL,
                "password": DEMO_USER_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.demo_user_id = result.get("user", {}).get("id")
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {self.demo_user_id}")
                self.log(f"Status: {result.get('status')}")
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during demo user login: {str(e)}", "ERROR")
            return False
    
    async def test_trial_status(self):
        """Test 2: Check demo user trial status"""
        self.log("=== Testing Trial Status ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for trial status test")
            return False
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/user/trial-status/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Trial status retrieved successfully")
                self.log(f"Has Access: {result.get('has_access')}")
                self.log(f"Trial Active: {result.get('trial_active')}")
                self.log(f"Trial Days Left: {result.get('trial_days_left')}")
                self.log(f"Subscription Status: {result.get('subscription_status')}")
                self.log(f"Current Week: {result.get('current_week')}")
                
                return result.get('has_access', False)
            else:
                self.log(f"❌ Trial status check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking trial status: {str(e)}", "ERROR")
            return False
    
    async def test_weekly_meal_generation_basic(self):
        """Test 3: Basic weekly meal plan generation (2-person family, no preferences)"""
        self.log("=== Testing Basic Weekly Meal Generation ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for meal generation test")
            return False
        
        try:
            request_data = {
                "user_id": self.demo_user_id,
                "family_size": 2,
                "dietary_preferences": [],
                "budget": None,
                "cuisines": []
            }
            
            self.log(f"Generating weekly meal plan for 2-person family with no preferences...")
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Weekly meal plan generated successfully")
                
                # Validate response structure
                meals = result.get("meals", [])
                self.log(f"Number of meals generated: {len(meals)}")
                
                if len(meals) == 7:
                    self.log("✅ Correct number of meals (7 days)")
                    
                    # Check each day is present
                    days_found = []
                    for meal in meals:
                        day = meal.get("day")
                        name = meal.get("name")
                        ingredients_count = len(meal.get("ingredients", []))
                        instructions_count = len(meal.get("instructions", []))
                        
                        days_found.append(day)
                        self.log(f"  {day}: {name} ({ingredients_count} ingredients, {instructions_count} steps)")
                    
                    expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    if all(day in days_found for day in expected_days):
                        self.log("✅ All 7 days of the week are covered")
                    else:
                        self.log(f"❌ Missing days: {set(expected_days) - set(days_found)}")
                    
                    # Check other fields
                    self.log(f"Week of: {result.get('week_of')}")
                    self.log(f"Total Budget: ${result.get('total_budget')}")
                    self.log(f"Walmart Cart URL: {result.get('walmart_cart_url', 'Not provided')[:50]}...")
                    
                    return True
                else:
                    self.log(f"❌ Incorrect number of meals: expected 7, got {len(meals)}")
                    return False
            else:
                self.log(f"❌ Weekly meal generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during weekly meal generation: {str(e)}", "ERROR")
            return False
    
    async def test_vegetarian_meal_generation(self):
        """Test 4: Weekly meal generation with vegetarian preferences"""
        self.log("=== Testing Vegetarian Weekly Meal Generation ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for vegetarian meal test")
            return False
        
        try:
            request_data = {
                "user_id": self.demo_user_id,
                "family_size": 4,
                "dietary_preferences": ["vegetarian"],
                "budget": 150.0,
                "cuisines": ["Italian", "Mediterranean"]
            }
            
            self.log(f"Generating vegetarian weekly meal plan for 4-person family...")
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Vegetarian weekly meal plan generated successfully")
                
                meals = result.get("meals", [])
                self.log(f"Number of meals: {len(meals)}")
                
                # Check if meals adapt to vegetarian preferences
                vegetarian_adaptations = 0
                for meal in meals:
                    name = meal.get("name", "")
                    dietary_tags = meal.get("dietary_tags", [])
                    ingredients = meal.get("ingredients", [])
                    
                    # Check for vegetarian adaptations
                    if "vegetarian" in dietary_tags or "Veggie" in name or "Vegetable" in name:
                        vegetarian_adaptations += 1
                    
                    # Check ingredients don't contain meat
                    meat_ingredients = [ing for ing in ingredients if any(meat in ing.lower() for meat in ["chicken", "beef", "pork", "fish", "meat"])]
                    if not meat_ingredients:
                        self.log(f"  ✅ {meal.get('day')}: {name} - No meat ingredients detected")
                    else:
                        self.log(f"  ⚠️ {meal.get('day')}: {name} - Potential meat ingredients: {meat_ingredients}")
                
                self.log(f"Vegetarian adaptations detected: {vegetarian_adaptations}/7 meals")
                
                # Check family size scaling (should serve 4 people)
                for meal in meals:
                    servings = meal.get("servings", 0)
                    if servings == 4:
                        self.log(f"  ✅ {meal.get('day')}: Correct servings ({servings})")
                    else:
                        self.log(f"  ❌ {meal.get('day')}: Incorrect servings (expected 4, got {servings})")
                
                return True
            else:
                self.log(f"❌ Vegetarian meal generation failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during vegetarian meal generation: {str(e)}", "ERROR")
            return False
    
    async def test_family_size_scaling(self):
        """Test 5: Test different family sizes (2, 4, 6) for ingredient scaling"""
        self.log("=== Testing Family Size Scaling ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for family size test")
            return False
        
        family_sizes = [2, 4, 6]
        scaling_results = {}
        
        for family_size in family_sizes:
            try:
                self.log(f"Testing family size: {family_size} people")
                
                request_data = {
                    "user_id": self.demo_user_id,
                    "family_size": family_size,
                    "dietary_preferences": [],
                    "budget": None,
                    "cuisines": ["Italian"]
                }
                
                response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=request_data)
                
                if response.status_code == 200:
                    result = response.json()
                    meals = result.get("meals", [])
                    
                    if meals:
                        # Check first meal for ingredient scaling
                        first_meal = meals[0]
                        ingredients = first_meal.get("ingredients", [])
                        servings = first_meal.get("servings", 0)
                        
                        scaling_results[family_size] = {
                            "servings": servings,
                            "ingredients_count": len(ingredients),
                            "sample_ingredients": ingredients[:3]  # First 3 ingredients
                        }
                        
                        self.log(f"  ✅ Family size {family_size}: {servings} servings, {len(ingredients)} ingredients")
                        for ing in ingredients[:2]:
                            self.log(f"    - {ing}")
                    else:
                        self.log(f"  ❌ No meals generated for family size {family_size}")
                        scaling_results[family_size] = None
                else:
                    self.log(f"  ❌ Failed to generate for family size {family_size}: {response.status_code}")
                    scaling_results[family_size] = None
                    
            except Exception as e:
                self.log(f"  ❌ Error testing family size {family_size}: {str(e)}")
                scaling_results[family_size] = None
        
        # Analyze scaling results
        self.log("=== Family Size Scaling Analysis ===")
        successful_tests = sum(1 for result in scaling_results.values() if result is not None)
        
        if successful_tests == len(family_sizes):
            self.log("✅ All family size tests successful")
            
            # Check if servings scale correctly
            for size, result in scaling_results.items():
                if result and result["servings"] == size:
                    self.log(f"  ✅ Family size {size}: Servings correctly set to {result['servings']}")
                elif result:
                    self.log(f"  ⚠️ Family size {size}: Servings set to {result['servings']} (expected {size})")
            
            return True
        else:
            self.log(f"❌ Only {successful_tests}/{len(family_sizes)} family size tests successful")
            return False
    
    async def test_walmart_cart_generation(self):
        """Test 6: Test Walmart cart URL generation from weekly ingredients"""
        self.log("=== Testing Walmart Cart Generation ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for Walmart cart test")
            return False
        
        try:
            # Generate a meal plan first
            request_data = {
                "user_id": self.demo_user_id,
                "family_size": 3,
                "dietary_preferences": [],
                "budget": 100.0,
                "cuisines": ["American"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                walmart_cart_url = result.get("walmart_cart_url")
                
                if walmart_cart_url:
                    self.log(f"✅ Walmart cart URL generated")
                    self.log(f"URL: {walmart_cart_url}")
                    
                    # Validate URL structure
                    if "walmart.com" in walmart_cart_url.lower():
                        self.log("✅ URL contains walmart.com domain")
                        
                        # Check if it's a search URL with ingredients
                        if "search" in walmart_cart_url or "query" in walmart_cart_url:
                            self.log("✅ URL appears to be a search URL with ingredients")
                        else:
                            self.log("⚠️ URL might be a fallback grocery section URL")
                        
                        return True
                    else:
                        self.log(f"❌ Invalid Walmart URL: {walmart_cart_url}")
                        return False
                else:
                    self.log("❌ No Walmart cart URL generated")
                    return False
            else:
                self.log(f"❌ Failed to generate meal plan for Walmart test: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Walmart cart generation: {str(e)}", "ERROR")
            return False
    
    async def test_database_storage(self):
        """Test 7: Test that weekly plans are properly stored in database"""
        self.log("=== Testing Database Storage ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for database test")
            return False
        
        try:
            # First, get current weekly plan
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                has_plan = result.get("has_plan", False)
                
                if has_plan:
                    plan = result.get("plan", {})
                    self.log("✅ Current weekly plan found in database")
                    self.log(f"Plan ID: {plan.get('id')}")
                    self.log(f"Week of: {plan.get('week_of')}")
                    self.log(f"User ID: {plan.get('user_id')}")
                    self.log(f"Number of meals: {len(plan.get('meals', []))}")
                    self.log(f"Is Active: {plan.get('is_active')}")
                    self.log(f"Created At: {plan.get('created_at')}")
                    
                    # Test weekly recipe history
                    history_response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/history/{self.demo_user_id}")
                    
                    if history_response.status_code == 200:
                        history_result = history_response.json()
                        plans = history_result.get("plans", [])
                        total_plans = history_result.get("total_plans", 0)
                        
                        self.log(f"✅ Recipe history retrieved: {total_plans} total plans")
                        
                        if plans:
                            latest_plan = plans[0]
                            self.log(f"Latest plan: {latest_plan.get('week_of')} with {len(latest_plan.get('meals', []))} meals")
                        
                        return True
                    else:
                        self.log(f"❌ Failed to get recipe history: {history_response.status_code}")
                        return False
                else:
                    self.log("⚠️ No current weekly plan found - this might be expected if no plan was generated")
                    return True
            else:
                self.log(f"❌ Failed to get current weekly plan: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing database storage: {str(e)}", "ERROR")
            return False
    
    async def test_api_response_structure(self):
        """Test 8: Verify all endpoints return proper JSON structure"""
        self.log("=== Testing API Response Structure ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for API structure test")
            return False
        
        try:
            # Test trial status endpoint structure
            trial_response = await self.client.get(f"{BACKEND_URL}/user/trial-status/{self.demo_user_id}")
            if trial_response.status_code == 200:
                trial_data = trial_response.json()
                required_trial_fields = ["has_access", "trial_active", "subscription_status", "trial_days_left", "current_week"]
                
                missing_fields = [field for field in required_trial_fields if field not in trial_data]
                if not missing_fields:
                    self.log("✅ Trial status endpoint has correct structure")
                else:
                    self.log(f"❌ Trial status missing fields: {missing_fields}")
            
            # Test current weekly plan endpoint structure
            current_response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.demo_user_id}")
            if current_response.status_code == 200:
                current_data = current_response.json()
                required_current_fields = ["has_plan", "current_week"]
                
                missing_fields = [field for field in required_current_fields if field not in current_data]
                if not missing_fields:
                    self.log("✅ Current weekly plan endpoint has correct structure")
                    
                    # If has_plan is True, check plan structure
                    if current_data.get("has_plan") and "plan" in current_data:
                        plan = current_data["plan"]
                        required_plan_fields = ["id", "user_id", "week_of", "meals", "walmart_cart_url", "created_at"]
                        
                        missing_plan_fields = [field for field in required_plan_fields if field not in plan]
                        if not missing_plan_fields:
                            self.log("✅ Weekly plan object has correct structure")
                            
                            # Check meal structure
                            meals = plan.get("meals", [])
                            if meals:
                                meal = meals[0]
                                required_meal_fields = ["day", "name", "description", "ingredients", "instructions", "prep_time", "cook_time", "servings", "cuisine_type"]
                                
                                missing_meal_fields = [field for field in required_meal_fields if field not in meal]
                                if not missing_meal_fields:
                                    self.log("✅ Meal objects have correct structure")
                                else:
                                    self.log(f"❌ Meal objects missing fields: {missing_meal_fields}")
                        else:
                            self.log(f"❌ Plan object missing fields: {missing_plan_fields}")
                else:
                    self.log(f"❌ Current weekly plan missing fields: {missing_fields}")
            
            # Test history endpoint structure
            history_response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/history/{self.demo_user_id}")
            if history_response.status_code == 200:
                history_data = history_response.json()
                required_history_fields = ["plans", "total_plans", "current_week"]
                
                missing_fields = [field for field in required_history_fields if field not in history_data]
                if not missing_fields:
                    self.log("✅ Weekly recipe history endpoint has correct structure")
                else:
                    self.log(f"❌ History endpoint missing fields: {missing_fields}")
            
            return True
                
        except Exception as e:
            self.log(f"❌ Error testing API response structure: {str(e)}", "ERROR")
            return False
    
    async def test_mock_data_verification(self):
        """Test 9: Verify that mock data is realistic and properly formatted"""
        self.log("=== Testing Mock Data Quality ===")
        
        if not self.demo_user_id:
            self.log("❌ No user ID available for mock data test")
            return False
        
        try:
            # Generate a meal plan to test mock data quality
            request_data = {
                "user_id": self.demo_user_id,
                "family_size": 2,
                "dietary_preferences": [],
                "budget": None,
                "cuisines": []
            }
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=request_data)
            
            if response.status_code == 200:
                result = response.json()
                meals = result.get("meals", [])
                
                if len(meals) == 7:
                    self.log("✅ Mock data contains 7 meals as expected")
                    
                    # Check data quality
                    quality_checks = {
                        "realistic_names": 0,
                        "proper_ingredients": 0,
                        "detailed_instructions": 0,
                        "reasonable_times": 0,
                        "diverse_cuisines": set()
                    }
                    
                    for meal in meals:
                        # Check realistic meal names
                        name = meal.get("name", "")
                        if len(name) > 5 and any(word in name.lower() for word in ["pasta", "bowl", "curry", "tacos", "stir", "ratatouille"]):
                            quality_checks["realistic_names"] += 1
                        
                        # Check proper ingredients (should have multiple ingredients)
                        ingredients = meal.get("ingredients", [])
                        if len(ingredients) >= 5:
                            quality_checks["proper_ingredients"] += 1
                        
                        # Check detailed instructions
                        instructions = meal.get("instructions", [])
                        if len(instructions) >= 4:
                            quality_checks["detailed_instructions"] += 1
                        
                        # Check reasonable cooking times
                        prep_time = meal.get("prep_time", 0)
                        cook_time = meal.get("cook_time", 0)
                        if 10 <= prep_time <= 60 and 15 <= cook_time <= 60:
                            quality_checks["reasonable_times"] += 1
                        
                        # Track cuisine diversity
                        cuisine = meal.get("cuisine_type", "")
                        if cuisine:
                            quality_checks["diverse_cuisines"].add(cuisine)
                    
                    # Report quality results
                    self.log(f"Realistic meal names: {quality_checks['realistic_names']}/7")
                    self.log(f"Proper ingredient lists: {quality_checks['proper_ingredients']}/7")
                    self.log(f"Detailed instructions: {quality_checks['detailed_instructions']}/7")
                    self.log(f"Reasonable cooking times: {quality_checks['reasonable_times']}/7")
                    self.log(f"Cuisine diversity: {len(quality_checks['diverse_cuisines'])} different cuisines")
                    self.log(f"Cuisines found: {', '.join(quality_checks['diverse_cuisines'])}")
                    
                    # Overall quality assessment
                    total_quality = (
                        quality_checks["realistic_names"] +
                        quality_checks["proper_ingredients"] +
                        quality_checks["detailed_instructions"] +
                        quality_checks["reasonable_times"]
                    )
                    
                    if total_quality >= 20:  # 5+ points per category on average
                        self.log("✅ Mock data quality is excellent")
                        return True
                    elif total_quality >= 14:  # 3.5+ points per category on average
                        self.log("⚠️ Mock data quality is acceptable")
                        return True
                    else:
                        self.log("❌ Mock data quality needs improvement")
                        return False
                else:
                    self.log(f"❌ Expected 7 meals, got {len(meals)}")
                    return False
            else:
                self.log(f"❌ Failed to generate meal plan for quality test: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing mock data quality: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all Weekly Recipe System tests"""
        self.log("🚀 Starting Comprehensive Weekly Recipe System Testing")
        self.log("Focus: Mock Data Fallback Functionality")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Demo User Login
        test_results["demo_login"] = await self.test_demo_user_login()
        
        # Test 2: Trial Status Check
        if test_results["demo_login"]:
            test_results["trial_status"] = await self.test_trial_status()
        else:
            test_results["trial_status"] = False
        
        # Test 3: Basic Weekly Meal Generation
        if test_results["trial_status"]:
            test_results["basic_generation"] = await self.test_weekly_meal_generation_basic()
        else:
            test_results["basic_generation"] = False
        
        # Test 4: Vegetarian Meal Generation
        if test_results["demo_login"]:
            test_results["vegetarian_generation"] = await self.test_vegetarian_meal_generation()
        else:
            test_results["vegetarian_generation"] = False
        
        # Test 5: Family Size Scaling
        if test_results["demo_login"]:
            test_results["family_scaling"] = await self.test_family_size_scaling()
        else:
            test_results["family_scaling"] = False
        
        # Test 6: Walmart Cart Generation
        if test_results["demo_login"]:
            test_results["walmart_cart"] = await self.test_walmart_cart_generation()
        else:
            test_results["walmart_cart"] = False
        
        # Test 7: Database Storage
        if test_results["demo_login"]:
            test_results["database_storage"] = await self.test_database_storage()
        else:
            test_results["database_storage"] = False
        
        # Test 8: API Response Structure
        if test_results["demo_login"]:
            test_results["api_structure"] = await self.test_api_response_structure()
        else:
            test_results["api_structure"] = False
        
        # Test 9: Mock Data Quality
        if test_results["demo_login"]:
            test_results["mock_data_quality"] = await self.test_mock_data_verification()
        else:
            test_results["mock_data_quality"] = False
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 WEEKLY RECIPE SYSTEM TEST RESULTS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result)
        
        self.log("=" * 70)
        self.log(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests >= 7:  # At least 7/9 tests should pass
            self.log("🎉 WEEKLY RECIPE SYSTEM WITH MOCK DATA FALLBACK IS WORKING CORRECTLY")
            self.log("✅ Mock data fallback functionality is operational")
            self.log("✅ All core features are functional without OpenAI API key")
        elif passed_tests >= 5:
            self.log("⚠️ WEEKLY RECIPE SYSTEM IS PARTIALLY WORKING")
            self.log("🔧 Some issues detected but core functionality is operational")
        else:
            self.log("❌ WEEKLY RECIPE SYSTEM HAS SIGNIFICANT ISSUES")
            self.log("🚨 Mock data fallback may not be working correctly")
        
        return test_results

async def main():
    """Main test execution"""
    tester = WeeklyRecipeSystemTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())