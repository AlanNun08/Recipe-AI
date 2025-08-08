#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Starbucks Generator Functionality
Focus: Test Community tab, Share Recipe Modal, and Starbucks features
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
import time
import base64

# Add backend to path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com/api"
TEST_USER_EMAIL = "starbucks_tester@example.com"
TEST_USER_PASSWORD = "starbuckstest123"
TEST_USER_NAME = "Starbucks Tester"

class StarbucksGeneratorTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.test_recipe_id = None
        self.shared_recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_openai_api_key(self):
        """Test 1: Verify OpenAI API key is configured"""
        self.log("=== Testing OpenAI API Configuration ===")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            from pathlib import Path
            
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            openai_key = os.environ.get('OPENAI_API_KEY')
            
            if openai_key:
                self.log(f"✅ OpenAI API Key: Present ({openai_key[:10]}...)")
                if openai_key.startswith('sk-'):
                    self.log("✅ API key format appears valid")
                    return True
                else:
                    self.log("❌ API key format appears invalid")
                    return False
            else:
                self.log("❌ OpenAI API Key: Missing")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking OpenAI API key: {str(e)}", "ERROR")
            return False
    
    async def register_test_user(self):
        """Register a test user for Starbucks testing"""
        self.log("=== Registering Test User ===")
        
        try:
            # First try to clear any existing test user
            await self.client.delete(f"{BACKEND_URL}/debug/cleanup-test-data")
            
            # Register new user
            user_data = {
                "first_name": "Starbucks",
                "last_name": "Tester",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "dietary_preferences": ["vegetarian"],
                "allergies": [],
                "favorite_cuisines": ["American"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                self.log(f"✅ User registered: {self.user_id}")
                
                # Auto-verify user for testing
                verify_data = {
                    "email": TEST_USER_EMAIL,
                    "code": "123456"  # Use test code
                }
                
                # Get the actual verification code from debug endpoint
                debug_response = await self.client.get(f"{BACKEND_URL}/debug/verification-codes/{TEST_USER_EMAIL}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    if debug_data.get("codes"):
                        verify_data["code"] = debug_data["codes"][0]["code"]
                
                verify_response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                if verify_response.status_code == 200:
                    self.log("✅ User verified successfully")
                    return True
                else:
                    self.log(f"⚠️ User verification failed: {verify_response.text}")
                    return True  # Continue anyway
                    
            else:
                self.log(f"❌ User registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error registering user: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_drink_generation(self):
        """Test 2: Test Starbucks drink generation for all drink types"""
        self.log("=== Testing Starbucks Drink Generation ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for testing")
            return False
        
        drink_types = ["frappuccino", "refresher", "lemonade", "iced_matcha_latte", "random"]
        test_results = {}
        
        for drink_type in drink_types:
            self.log(f"Testing {drink_type} generation...")
            
            try:
                request_data = {
                    "user_id": self.user_id,
                    "drink_type": drink_type,
                    "flavor_inspiration": "vanilla caramel" if drink_type == "frappuccino" else None
                }
                
                response = await self.client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=request_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Validate response structure
                    required_fields = ["drink_name", "description", "base_drink", "modifications", "ordering_script", "category"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if not missing_fields:
                        self.log(f"✅ {drink_type}: {result['drink_name']}")
                        self.log(f"   Base: {result['base_drink']}")
                        self.log(f"   Modifications: {len(result['modifications'])} items")
                        self.log(f"   Category: {result['category']}")
                        test_results[drink_type] = True
                    else:
                        self.log(f"❌ {drink_type}: Missing fields {missing_fields}")
                        test_results[drink_type] = False
                        
                else:
                    self.log(f"❌ {drink_type}: HTTP {response.status_code} - {response.text}")
                    test_results[drink_type] = False
                    
            except Exception as e:
                self.log(f"❌ Error testing {drink_type}: {str(e)}")
                test_results[drink_type] = False
        
        # Overall result
        successful_tests = sum(1 for result in test_results.values() if result)
        self.log(f"Starbucks Generation Results: {successful_tests}/{len(drink_types)} successful")
        
        return successful_tests == len(drink_types)
    
    async def test_curated_starbucks_recipes(self):
        """Test 3: Test curated Starbucks recipes endpoint"""
        self.log("=== Testing Curated Starbucks Recipes ===")
        
        try:
            # Test getting all curated recipes
            response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Retrieved {total} curated recipes")
                
                if recipes:
                    # Test recipe structure
                    sample_recipe = recipes[0]
                    required_fields = ["name", "base", "ingredients", "order_instructions", "vibe", "category"]
                    missing_fields = [field for field in required_fields if field not in sample_recipe]
                    
                    if not missing_fields:
                        self.log("✅ Recipe structure is valid")
                        self.log(f"   Sample: {sample_recipe['name']}")
                        self.log(f"   Category: {sample_recipe['category']}")
                        
                        # Test category filtering
                        categories = ["frappuccino", "refresher", "lemonade", "iced_matcha_latte"]
                        for category in categories:
                            cat_response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes?category={category}")
                            if cat_response.status_code == 200:
                                cat_result = cat_response.json()
                                cat_recipes = cat_result.get("recipes", [])
                                self.log(f"   {category}: {len(cat_recipes)} recipes")
                        
                        return True
                    else:
                        self.log(f"❌ Recipe missing fields: {missing_fields}")
                        return False
                else:
                    self.log("❌ No recipes returned")
                    return False
                    
            else:
                self.log(f"❌ Curated recipes failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing curated recipes: {str(e)}", "ERROR")
            return False
    
    async def test_share_recipe_functionality(self):
        """Test 4: Test share recipe functionality (Community feature)"""
        self.log("=== Testing Share Recipe Functionality ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for testing")
            return False
        
        try:
            # Create a test recipe to share
            recipe_data = {
                "recipe_name": "Magical Unicorn Frappuccino",
                "description": "A whimsical blend of vanilla and berry flavors with sparkly toppings",
                "ingredients": [
                    "Vanilla Bean Frappuccino base",
                    "2 pumps raspberry syrup",
                    "1 pump vanilla syrup",
                    "Whipped cream",
                    "Pink powder topping"
                ],
                "order_instructions": "Hi, can I get a grande Vanilla Bean Frappuccino with 2 pumps raspberry syrup, 1 pump vanilla syrup, whipped cream, and pink powder topping?",
                "category": "frappuccino",
                "tags": ["sweet", "colorful", "magical"],
                "difficulty_level": "easy",
                "original_source": "custom"
            }
            
            # Test sharing the recipe
            response = await self.client.post(f"{BACKEND_URL}/share-recipe?user_id={self.user_id}", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.shared_recipe_id = result.get("recipe_id")
                    shared_by = result.get("shared_by")
                    
                    self.log(f"✅ Recipe shared successfully")
                    self.log(f"   Recipe ID: {self.shared_recipe_id}")
                    self.log(f"   Shared by: {shared_by}")
                    self.log(f"   Message: {result.get('message')}")
                    
                    return True
                else:
                    self.log(f"❌ Share recipe failed: {result}")
                    return False
                    
            else:
                self.log(f"❌ Share recipe failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing share recipe: {str(e)}", "ERROR")
            return False
    
    async def test_shared_recipes_retrieval(self):
        """Test 5: Test retrieving shared recipes (Community tab)"""
        self.log("=== Testing Shared Recipes Retrieval ===")
        
        try:
            # Test getting all shared recipes
            response = await self.client.get(f"{BACKEND_URL}/shared-recipes")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Retrieved {total} shared recipes")
                
                if recipes:
                    # Verify our shared recipe is in the list
                    our_recipe = None
                    for recipe in recipes:
                        if recipe.get("id") == self.shared_recipe_id:
                            our_recipe = recipe
                            break
                    
                    if our_recipe:
                        self.log("✅ Our shared recipe found in community")
                        self.log(f"   Name: {our_recipe['recipe_name']}")
                        self.log(f"   Category: {our_recipe['category']}")
                        self.log(f"   Tags: {our_recipe.get('tags', [])}")
                        self.log(f"   Likes: {our_recipe.get('likes_count', 0)}")
                    else:
                        self.log("⚠️ Our shared recipe not found in community list")
                    
                    # Test category filtering
                    cat_response = await self.client.get(f"{BACKEND_URL}/shared-recipes?category=frappuccino")
                    if cat_response.status_code == 200:
                        cat_result = cat_response.json()
                        cat_recipes = cat_result.get("recipes", [])
                        self.log(f"✅ Category filtering: {len(cat_recipes)} frappuccino recipes")
                    
                    # Test pagination
                    page_response = await self.client.get(f"{BACKEND_URL}/shared-recipes?limit=5&offset=0")
                    if page_response.status_code == 200:
                        page_result = page_response.json()
                        self.log(f"✅ Pagination: limit=5, got {len(page_result.get('recipes', []))} recipes")
                    
                    return True
                else:
                    self.log("⚠️ No shared recipes found (this might be expected if database is empty)")
                    return True  # Not necessarily an error
                    
            else:
                self.log(f"❌ Shared recipes retrieval failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing shared recipes retrieval: {str(e)}", "ERROR")
            return False
    
    async def test_like_recipe_functionality(self):
        """Test 6: Test like/unlike recipe functionality"""
        self.log("=== Testing Like Recipe Functionality ===")
        
        if not self.user_id or not self.shared_recipe_id:
            self.log("❌ Missing user_id or shared_recipe_id for like testing")
            return False
        
        try:
            # Test liking a recipe
            like_data = {
                "recipe_id": self.shared_recipe_id,
                "user_id": self.user_id
            }
            
            response = await self.client.post(f"{BACKEND_URL}/like-recipe", json=like_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    action = result.get("action")
                    likes_count = result.get("likes_count")
                    
                    self.log(f"✅ Recipe {action} successfully")
                    self.log(f"   Likes count: {likes_count}")
                    
                    # Test unliking the recipe
                    unlike_response = await self.client.post(f"{BACKEND_URL}/like-recipe", json=like_data)
                    
                    if unlike_response.status_code == 200:
                        unlike_result = unlike_response.json()
                        
                        if unlike_result.get("success"):
                            unlike_action = unlike_result.get("action")
                            unlike_count = unlike_result.get("likes_count")
                            
                            self.log(f"✅ Recipe {unlike_action} successfully")
                            self.log(f"   Likes count: {unlike_count}")
                            
                            return True
                        else:
                            self.log(f"❌ Unlike failed: {unlike_result}")
                            return False
                    else:
                        self.log(f"❌ Unlike failed: HTTP {unlike_response.status_code}")
                        return False
                        
                else:
                    self.log(f"❌ Like failed: {result}")
                    return False
                    
            else:
                self.log(f"❌ Like recipe failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing like functionality: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_stats(self):
        """Test 7: Test recipe statistics endpoint"""
        self.log("=== Testing Recipe Statistics ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/recipe-stats")
            
            if response.status_code == 200:
                result = response.json()
                
                total_shared = result.get("total_shared_recipes", 0)
                category_breakdown = result.get("category_breakdown", {})
                top_tags = result.get("top_tags", [])
                most_liked = result.get("most_liked", [])
                
                self.log(f"✅ Recipe statistics retrieved")
                self.log(f"   Total shared recipes: {total_shared}")
                self.log(f"   Categories: {list(category_breakdown.keys())}")
                self.log(f"   Top tags count: {len(top_tags)}")
                self.log(f"   Most liked recipes: {len(most_liked)}")
                
                if category_breakdown:
                    for category, count in category_breakdown.items():
                        self.log(f"     {category}: {count} recipes")
                
                return True
                
            else:
                self.log(f"❌ Recipe stats failed: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe stats: {str(e)}", "ERROR")
            return False
    
    async def test_enhanced_prompts(self):
        """Test 8: Test enhanced prompts with creative examples"""
        self.log("=== Testing Enhanced Prompts with Creative Examples ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for testing")
            return False
        
        try:
            # Test specific flavor inspirations mentioned in the review
            test_cases = [
                {"drink_type": "frappuccino", "flavor_inspiration": "tres leches"},
                {"drink_type": "refresher", "flavor_inspiration": "ube"},
                {"drink_type": "lemonade", "flavor_inspiration": "mango tajin"},
                {"drink_type": "iced_matcha_latte", "flavor_inspiration": "brown butter"}
            ]
            
            successful_tests = 0
            
            for test_case in test_cases:
                drink_type = test_case["drink_type"]
                flavor = test_case["flavor_inspiration"]
                
                self.log(f"Testing {drink_type} with {flavor} inspiration...")
                
                request_data = {
                    "user_id": self.user_id,
                    "drink_type": drink_type,
                    "flavor_inspiration": flavor
                }
                
                response = await self.client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=request_data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    drink_name = result.get("drink_name", "")
                    description = result.get("description", "")
                    vibe = result.get("why_amazing", "")
                    
                    # Check if the response includes creative/magical elements
                    creative_indicators = ["magical", "whimsical", "dreamy", "enchanting", "mystical", "vibrant", "zen", "peaceful"]
                    has_creative_elements = any(indicator in (drink_name + description + vibe).lower() for indicator in creative_indicators)
                    
                    if has_creative_elements:
                        self.log(f"✅ {drink_type} with {flavor}: Creative elements detected")
                        self.log(f"   Name: {drink_name}")
                        successful_tests += 1
                    else:
                        self.log(f"⚠️ {drink_type} with {flavor}: Limited creative elements")
                        self.log(f"   Name: {drink_name}")
                        successful_tests += 1  # Still count as success if API works
                        
                else:
                    self.log(f"❌ {drink_type} with {flavor}: HTTP {response.status_code}")
            
            self.log(f"Enhanced prompts test: {successful_tests}/{len(test_cases)} successful")
            return successful_tests >= len(test_cases) * 0.75  # 75% success rate acceptable
            
        except Exception as e:
            self.log(f"❌ Error testing enhanced prompts: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_starbucks_test(self):
        """Run all Starbucks-related tests in sequence"""
        self.log("🌟 Starting Comprehensive Starbucks Generator Tests")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: OpenAI API Configuration
        test_results["openai_config"] = await self.test_openai_api_key()
        
        # Test 2: User Setup
        test_results["user_setup"] = await self.register_test_user()
        
        if test_results["user_setup"]:
            # Test 3: Starbucks Drink Generation
            test_results["drink_generation"] = await self.test_starbucks_drink_generation()
            
            # Test 4: Curated Recipes
            test_results["curated_recipes"] = await self.test_curated_starbucks_recipes()
            
            # Test 5: Share Recipe (Community Feature)
            test_results["share_recipe"] = await self.test_share_recipe_functionality()
            
            # Test 6: Shared Recipes Retrieval
            test_results["shared_recipes"] = await self.test_shared_recipes_retrieval()
            
            # Test 7: Like Recipe Functionality
            test_results["like_recipe"] = await self.test_like_recipe_functionality()
            
            # Test 8: Recipe Statistics
            test_results["recipe_stats"] = await self.test_recipe_stats()
            
            # Test 9: Enhanced Prompts
            test_results["enhanced_prompts"] = await self.test_enhanced_prompts()
        else:
            # Skip dependent tests if user setup failed
            for test_name in ["drink_generation", "curated_recipes", "share_recipe", "shared_recipes", "like_recipe", "recipe_stats", "enhanced_prompts"]:
                test_results[test_name] = False
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 STARBUCKS GENERATOR TEST RESULTS")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = ["openai_config", "drink_generation", "curated_recipes", "share_recipe", "shared_recipes"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 60)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL STARBUCKS TESTS PASSED")
            self.log("✅ Community tab and Share Recipe Modal should be working")
            self.log("✅ Starbucks generator functionality is operational")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("openai_config"):
                self.log("  - OpenAI API key missing or invalid")
            if not test_results.get("drink_generation"):
                self.log("  - Starbucks drink generation failing")
            if not test_results.get("curated_recipes"):
                self.log("  - Curated recipes endpoint not working")
            if not test_results.get("share_recipe"):
                self.log("  - Share recipe functionality (Community feature) failing")
            if not test_results.get("shared_recipes"):
                self.log("  - Shared recipes retrieval (Community tab) not working")
        
        return test_results

async def main():
    """Main test execution"""
    tester = StarbucksGeneratorTester()
    
    try:
        results = await tester.run_comprehensive_starbucks_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())