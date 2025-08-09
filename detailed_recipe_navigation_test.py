#!/usr/bin/env python3
"""
Detailed Recipe History Navigation Testing
Testing the specific issue where clicking on a recipe in recipe history 
should show that exact same recipe in the detail page, not a different one.

Focus on testing 3-5 recipe IDs from history as requested in the review.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any

class DetailedRecipeNavigationTester:
    def __init__(self):
        # Use the external URL from frontend/.env
        self.backend_url = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Demo user credentials
        self.demo_email = "demo@test.com"
        self.demo_user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def get_recipe_history(self):
        """Get recipe history for demo user"""
        self.log("=== Getting Recipe History ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/history/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"✅ Retrieved {len(recipes)} recipes from history")
                
                # Return first 5 recipes for detailed testing
                test_recipes = []
                for i, recipe in enumerate(recipes[:5]):
                    recipe_info = {
                        "id": recipe.get("id"),
                        "title": recipe.get("title", "Unknown"),
                        "type": recipe.get("type", "unknown"),
                        "description": recipe.get("description", ""),
                        "ingredients": recipe.get("ingredients", []),
                        "position_in_history": i + 1
                    }
                    test_recipes.append(recipe_info)
                    
                    self.log(f"Recipe {i+1}: {recipe_info['title']} (ID: {recipe_info['id']}, Type: {recipe_info['type']})")
                
                return test_recipes
                
            else:
                self.log(f"❌ Failed to get recipe history: {response.status_code}")
                return []
                
        except Exception as e:
            self.log(f"❌ Error getting recipe history: {str(e)}", "ERROR")
            return []
    
    async def test_recipe_detail(self, recipe_info):
        """Test individual recipe detail endpoint with comprehensive checks"""
        recipe_id = recipe_info["id"]
        expected_title = recipe_info["title"]
        expected_type = recipe_info["type"]
        position = recipe_info["position_in_history"]
        
        self.log(f"\n--- Testing Recipe {position}: {expected_title} ---")
        self.log(f"Expected ID: {recipe_id}")
        self.log(f"Expected Type: {expected_type}")
        
        try:
            response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract actual data
                actual_id = result.get("id")
                actual_title = result.get("title", "Unknown")
                actual_type = result.get("type", "unknown")
                actual_description = result.get("description", "")
                actual_ingredients = result.get("ingredients", [])
                actual_instructions = result.get("instructions", [])
                
                # Perform detailed comparison
                id_match = actual_id == recipe_id
                title_match = actual_title == expected_title
                
                self.log(f"Actual ID: {actual_id}")
                self.log(f"Actual Title: {actual_title}")
                self.log(f"Actual Type: {actual_type}")
                
                # Check for exact matches
                if id_match:
                    self.log("✅ Recipe ID matches perfectly")
                else:
                    self.log("❌ RECIPE ID MISMATCH!")
                    self.log(f"  Expected: {recipe_id}")
                    self.log(f"  Got:      {actual_id}")
                
                if title_match:
                    self.log("✅ Recipe title matches perfectly")
                else:
                    self.log("❌ RECIPE TITLE MISMATCH!")
                    self.log(f"  Expected: '{expected_title}'")
                    self.log(f"  Got:      '{actual_title}'")
                
                # Check content integrity
                ingredients_count = len(actual_ingredients)
                instructions_count = len(actual_instructions)
                
                self.log(f"Content: {ingredients_count} ingredients, {instructions_count} instructions")
                
                # Check for required fields
                required_fields = ["id", "title", "description", "ingredients", "instructions"]
                missing_fields = [field for field in required_fields if not result.get(field)]
                
                if missing_fields:
                    self.log(f"❌ Missing required fields: {missing_fields}")
                else:
                    self.log("✅ All required fields present")
                
                # Return detailed analysis
                return {
                    "success": True,
                    "id_match": id_match,
                    "title_match": title_match,
                    "expected_id": recipe_id,
                    "actual_id": actual_id,
                    "expected_title": expected_title,
                    "actual_title": actual_title,
                    "expected_type": expected_type,
                    "actual_type": actual_type,
                    "ingredients_count": ingredients_count,
                    "instructions_count": instructions_count,
                    "has_required_fields": len(missing_fields) == 0,
                    "position": position
                }
                
            elif response.status_code == 404:
                self.log("❌ Recipe not found (404 error)")
                self.log("This indicates the recipe ID from history is invalid or the detail endpoint can't find it")
                
                return {
                    "success": False,
                    "error": "Recipe not found",
                    "status_code": 404,
                    "expected_id": recipe_id,
                    "expected_title": expected_title,
                    "position": position
                }
                
            else:
                self.log(f"❌ Recipe detail endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "status_code": response.status_code,
                    "expected_id": recipe_id,
                    "expected_title": expected_title,
                    "position": position
                }
                
        except Exception as e:
            self.log(f"❌ Exception testing recipe detail: {str(e)}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "expected_id": recipe_id,
                "expected_title": expected_title,
                "position": position
            }
    
    async def run_comprehensive_navigation_test(self):
        """Run comprehensive navigation test as requested in review"""
        self.log("🚀 Starting Detailed Recipe History Navigation Testing")
        self.log("=" * 80)
        self.log(f"Backend URL: {self.backend_url}")
        self.log(f"Demo User ID: {self.demo_user_id}")
        self.log("Testing 3-5 recipe IDs from history as requested")
        self.log("=" * 80)
        
        # Step 1: Get recipe history
        test_recipes = await self.get_recipe_history()
        
        if not test_recipes:
            self.log("❌ No recipes available for testing")
            return False
        
        # Step 2: Test each recipe detail endpoint
        test_results = []
        successful_tests = 0
        id_mismatches = 0
        title_mismatches = 0
        not_found_errors = 0
        
        for recipe_info in test_recipes:
            result = await self.test_recipe_detail(recipe_info)
            test_results.append(result)
            
            if result["success"]:
                successful_tests += 1
                if not result["id_match"]:
                    id_mismatches += 1
                if not result["title_match"]:
                    title_mismatches += 1
            else:
                if result.get("status_code") == 404:
                    not_found_errors += 1
        
        # Step 3: Analyze results
        self.log("\n" + "=" * 80)
        self.log("🔍 DETAILED NAVIGATION TEST RESULTS")
        self.log("=" * 80)
        
        total_tests = len(test_results)
        self.log(f"Total recipes tested: {total_tests}")
        self.log(f"Successful retrievals: {successful_tests}")
        self.log(f"Failed retrievals: {total_tests - successful_tests}")
        self.log(f"Recipe ID mismatches: {id_mismatches}")
        self.log(f"Recipe title mismatches: {title_mismatches}")
        self.log(f"Not found errors (404): {not_found_errors}")
        
        # Step 4: Identify specific issues
        if id_mismatches > 0 or title_mismatches > 0 or not_found_errors > 0:
            self.log("\n❌ NAVIGATION ISSUES IDENTIFIED:")
            
            for result in test_results:
                if not result["success"]:
                    self.log(f"  Recipe {result['position']}: {result['expected_title']}")
                    self.log(f"    Issue: {result['error']}")
                    self.log(f"    Expected ID: {result['expected_id']}")
                    
                elif not result["id_match"]:
                    self.log(f"  Recipe {result['position']}: ID MISMATCH")
                    self.log(f"    Expected: {result['expected_id']}")
                    self.log(f"    Got:      {result['actual_id']}")
                    
                elif not result["title_match"]:
                    self.log(f"  Recipe {result['position']}: TITLE MISMATCH")
                    self.log(f"    Expected: '{result['expected_title']}'")
                    self.log(f"    Got:      '{result['actual_title']}'")
        
        # Step 5: Final assessment
        self.log("\n" + "=" * 80)
        if successful_tests == total_tests and id_mismatches == 0 and title_mismatches == 0:
            self.log("🎉 ALL NAVIGATION TESTS PASSED")
            self.log("✅ Recipe history navigation is working correctly")
            self.log("✅ All recipe IDs from history return the correct recipe details")
            self.log("✅ No data mismatches detected")
            return True
        else:
            self.log("❌ NAVIGATION ISSUES DETECTED")
            
            if not_found_errors > 0:
                self.log("🔧 Issue: Recipe history returning IDs that don't exist in detail endpoint")
                
            if id_mismatches > 0:
                self.log("🔧 Issue: Recipe detail endpoint returning wrong recipe for given ID")
                
            if title_mismatches > 0:
                self.log("🔧 Issue: Data mismatch causing wrong recipe to be displayed")
            
            return False

async def main():
    """Main test execution"""
    tester = DetailedRecipeNavigationTester()
    
    try:
        success = await tester.run_comprehensive_navigation_test()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)