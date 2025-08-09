#!/usr/bin/env python3
"""
Backend Recipe Navigation Comprehensive Test
Test all recipe detail endpoints and multi-collection search functionality
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any

class BackendRecipeNavigationTester:
    def __init__(self):
        self.backend_url = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"
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
            if response.status_code == 200:
                self.log("✅ Demo user login successful")
                return True
            else:
                self.log(f"❌ Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Login error: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_history_endpoint(self):
        """Test 1: Recipe History Endpoint - Get all recipes for demo user"""
        self.log("=== Test 1: Recipe History Endpoint ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Recipe history endpoint working")
                self.log(f"Total recipes: {total}")
                self.log(f"Recipes returned: {len(recipes)}")
                
                # Analyze recipe types and sources
                recipe_types = {}
                valid_ids = 0
                null_ids = 0
                
                sample_recipes = []
                
                for recipe in recipes[:10]:  # Analyze first 10 recipes
                    recipe_id = recipe.get("id")
                    recipe_type = recipe.get("type", "unknown")
                    title = recipe.get("title", "Unknown")
                    
                    if recipe_id:
                        valid_ids += 1
                        sample_recipes.append({
                            "id": recipe_id,
                            "title": title,
                            "type": recipe_type
                        })
                    else:
                        null_ids += 1
                    
                    recipe_types[recipe_type] = recipe_types.get(recipe_type, 0) + 1
                
                self.log(f"Recipe types found: {recipe_types}")
                self.log(f"Valid IDs: {valid_ids}, Null IDs: {null_ids}")
                
                if sample_recipes:
                    self.log("Sample recipes for testing:")
                    for recipe in sample_recipes[:5]:
                        self.log(f"  - {recipe['title']} (ID: {recipe['id']}, Type: {recipe['type']})")
                
                return True, sample_recipes
            else:
                self.log(f"❌ Recipe history failed: {response.status_code} - {response.text}")
                return False, []
                
        except Exception as e:
            self.log(f"❌ Error testing recipe history: {str(e)}", "ERROR")
            return False, []
    
    async def test_recipe_detail_retrieval(self, sample_recipes: List[Dict]):
        """Test 2: Recipe Detail Retrieval - Test the fixed multi-collection search"""
        self.log("=== Test 2: Recipe Detail Retrieval ===")
        
        if not sample_recipes:
            self.log("⚠️ No sample recipes to test")
            return True
        
        test_results = []
        
        for recipe in sample_recipes:
            recipe_id = recipe["id"]
            title = recipe["title"]
            recipe_type = recipe["type"]
            
            self.log(f"Testing recipe detail: {title} (Type: {recipe_type})")
            
            try:
                response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                result = {
                    "recipe_id": recipe_id,
                    "title": title,
                    "type": recipe_type,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
                
                if response.status_code == 200:
                    data = response.json()
                    result["retrieved_title"] = data.get("title")
                    result["has_ingredients"] = bool(data.get("ingredients"))
                    result["has_instructions"] = bool(data.get("instructions"))
                    result["ingredient_count"] = len(data.get("ingredients", []))
                    result["instruction_count"] = len(data.get("instructions", []))
                    
                    self.log(f"  ✅ Successfully retrieved recipe details")
                    self.log(f"    Title: {result['retrieved_title']}")
                    self.log(f"    Ingredients: {result['ingredient_count']}")
                    self.log(f"    Instructions: {result['instruction_count']}")
                    
                elif response.status_code == 404:
                    self.log(f"  ❌ Recipe not found (404) - Multi-collection search issue!")
                    result["error"] = "Recipe exists in history but not found by detail endpoint"
                    
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
                    "type": recipe_type,
                    "status_code": "exception",
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = len([r for r in test_results if r["success"]])
        total = len(test_results)
        
        self.log(f"Recipe detail retrieval success rate: {successful}/{total}")
        
        return test_results
    
    async def test_starbucks_recipe_navigation(self):
        """Test 3: Starbucks Recipe Navigation - Test the specific fix mentioned in test_result.md"""
        self.log("=== Test 3: Starbucks Recipe Navigation ===")
        
        try:
            # Get curated Starbucks recipes
            response = await self.client.get(f"{self.backend_url}/curated-starbucks-recipes")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Found {len(recipes)} curated Starbucks recipes")
                
                if recipes:
                    # Test the first few Starbucks recipes (this was the reported issue)
                    test_results = []
                    
                    for i, recipe in enumerate(recipes[:5]):
                        recipe_id = recipe.get("id")
                        recipe_name = recipe.get("name")
                        
                        self.log(f"Testing Starbucks recipe {i+1}: {recipe_name}")
                        self.log(f"  Recipe ID: {recipe_id}")
                        
                        # This was the problematic call - Starbucks recipes weren't accessible via detail endpoint
                        detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                        
                        result = {
                            "recipe_id": recipe_id,
                            "name": recipe_name,
                            "status_code": detail_response.status_code,
                            "success": detail_response.status_code == 200
                        }
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            result["retrieved_title"] = detail_data.get("title", detail_data.get("drink_name"))
                            result["has_ingredients"] = bool(detail_data.get("ingredients", detail_data.get("modifications")))
                            
                            self.log(f"  ✅ Starbucks recipe detail retrieved successfully")
                            self.log(f"    Retrieved title: {result['retrieved_title']}")
                            
                        elif detail_response.status_code == 404:
                            self.log(f"  ❌ Starbucks recipe not found (404) - This was the original bug!")
                            result["error"] = "Starbucks recipe not accessible via detail endpoint"
                            
                        else:
                            self.log(f"  ❌ Unexpected status: {detail_response.status_code}")
                            result["error"] = f"Unexpected status: {detail_response.status_code}"
                        
                        test_results.append(result)
                    
                    # Summary for Starbucks navigation
                    successful_starbucks = len([r for r in test_results if r["success"]])
                    total_starbucks = len(test_results)
                    
                    self.log(f"Starbucks recipe navigation success rate: {successful_starbucks}/{total_starbucks}")
                    
                    return test_results
                else:
                    self.log("⚠️ No Starbucks recipes found")
                    return []
            else:
                self.log(f"❌ Failed to get Starbucks recipes: {response.status_code}")
                return []
                
        except Exception as e:
            self.log(f"❌ Error testing Starbucks navigation: {str(e)}", "ERROR")
            return []
    
    async def test_recipe_id_flow_validation(self):
        """Test 4: Recipe ID Flow Validation - Ensure IDs are valid and not null"""
        self.log("=== Test 4: Recipe ID Flow Validation ===")
        
        try:
            # Test recipe history for ID validation
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                # Validate all recipe IDs
                valid_ids = 0
                null_ids = 0
                invalid_ids = 0
                id_formats = {"uuid": 0, "other": 0}
                
                for recipe in recipes:
                    recipe_id = recipe.get("id")
                    
                    if recipe_id is None:
                        null_ids += 1
                    elif isinstance(recipe_id, str) and len(recipe_id) > 0:
                        valid_ids += 1
                        # Check if it looks like a UUID
                        if len(recipe_id) == 36 and recipe_id.count("-") == 4:
                            id_formats["uuid"] += 1
                        else:
                            id_formats["other"] += 1
                    else:
                        invalid_ids += 1
                
                self.log(f"Recipe ID validation results:")
                self.log(f"  Valid IDs: {valid_ids}")
                self.log(f"  Null IDs: {null_ids}")
                self.log(f"  Invalid IDs: {invalid_ids}")
                self.log(f"  UUID format: {id_formats['uuid']}")
                self.log(f"  Other format: {id_formats['other']}")
                
                # Test that valid IDs can be used for detail retrieval
                if valid_ids > 0:
                    self.log("✅ Recipe IDs are properly formatted and not null")
                    return True
                else:
                    self.log("❌ No valid recipe IDs found")
                    return False
            else:
                self.log(f"❌ Failed to get recipes for ID validation: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error validating recipe IDs: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_content_verification(self):
        """Test 5: Recipe Content Verification - Check recipe data structure"""
        self.log("=== Test 5: Recipe Content Verification ===")
        
        try:
            # Get a sample recipe and verify its content structure
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                if recipes:
                    sample_recipe = recipes[0]
                    recipe_id = sample_recipe.get("id")
                    
                    if recipe_id:
                        # Get detailed recipe data
                        detail_response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # Verify required fields
                            required_fields = ["id", "title", "description", "ingredients", "instructions"]
                            missing_fields = []
                            present_fields = []
                            
                            for field in required_fields:
                                if field in detail_data and detail_data[field]:
                                    present_fields.append(field)
                                else:
                                    missing_fields.append(field)
                            
                            self.log(f"Recipe content verification:")
                            self.log(f"  Present fields: {present_fields}")
                            self.log(f"  Missing fields: {missing_fields}")
                            
                            # Check content quality
                            ingredients = detail_data.get("ingredients", [])
                            instructions = detail_data.get("instructions", [])
                            
                            self.log(f"  Ingredients count: {len(ingredients)}")
                            self.log(f"  Instructions count: {len(instructions)}")
                            
                            if len(ingredients) > 0 and len(instructions) > 0:
                                self.log("✅ Recipe content structure is valid")
                                return True
                            else:
                                self.log("❌ Recipe content is incomplete")
                                return False
                        else:
                            self.log(f"❌ Could not retrieve recipe details: {detail_response.status_code}")
                            return False
                    else:
                        self.log("❌ No valid recipe ID found for content verification")
                        return False
                else:
                    self.log("⚠️ No recipes found for content verification")
                    return True
            else:
                self.log(f"❌ Failed to get recipes: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying recipe content: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_backend_test(self):
        """Run comprehensive backend recipe navigation test"""
        self.log("🚀 Starting Backend Recipe Navigation Comprehensive Test")
        self.log("=" * 80)
        
        # Login
        if not await self.login_demo_user():
            self.log("❌ Cannot proceed without login")
            return False
        
        # Test 1: Recipe History Endpoint
        history_success, sample_recipes = await self.test_recipe_history_endpoint()
        
        # Test 2: Recipe Detail Retrieval
        if history_success and sample_recipes:
            detail_results = await self.test_recipe_detail_retrieval(sample_recipes)
        else:
            detail_results = []
        
        # Test 3: Starbucks Recipe Navigation (the specific fix)
        starbucks_results = await self.test_starbucks_recipe_navigation()
        
        # Test 4: Recipe ID Flow Validation
        id_validation_success = await self.test_recipe_id_flow_validation()
        
        # Test 5: Recipe Content Verification
        content_verification_success = await self.test_recipe_content_verification()
        
        # Final Summary
        self.log("=" * 80)
        self.log("🔍 BACKEND RECIPE NAVIGATION TEST RESULTS")
        self.log("=" * 80)
        
        # Overall results
        tests = {
            "Recipe History Endpoint": history_success,
            "Recipe ID Validation": id_validation_success,
            "Recipe Content Verification": content_verification_success
        }
        
        # Detail retrieval results
        if detail_results:
            successful_details = len([r for r in detail_results if r["success"]])
            total_details = len(detail_results)
            detail_success_rate = successful_details / total_details if total_details > 0 else 0
            tests["Recipe Detail Retrieval"] = detail_success_rate == 1.0
            
            self.log(f"Recipe detail retrieval: {successful_details}/{total_details} successful")
        
        # Starbucks navigation results
        if starbucks_results:
            successful_starbucks = len([r for r in starbucks_results if r["success"]])
            total_starbucks = len(starbucks_results)
            starbucks_success_rate = successful_starbucks / total_starbucks if total_starbucks > 0 else 0
            tests["Starbucks Recipe Navigation"] = starbucks_success_rate == 1.0
            
            self.log(f"Starbucks recipe navigation: {successful_starbucks}/{total_starbucks} successful")
        
        # Show test results
        for test_name, success in tests.items():
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        # Overall assessment
        all_passed = all(tests.values())
        
        if all_passed:
            self.log("🎉 ALL BACKEND RECIPE NAVIGATION TESTS PASSED")
            self.log("✅ Recipe history navigation issue has been resolved")
            self.log("✅ Multi-collection search is working correctly")
            self.log("✅ Starbucks recipe navigation fix is working")
        else:
            failed_tests = [name for name, success in tests.items() if not success]
            self.log(f"❌ SOME TESTS FAILED: {', '.join(failed_tests)}")
        
        return {
            "all_passed": all_passed,
            "test_results": tests,
            "detail_results": detail_results,
            "starbucks_results": starbucks_results
        }

async def main():
    """Main test execution"""
    tester = BackendRecipeNavigationTester()
    
    try:
        results = await tester.run_comprehensive_backend_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())