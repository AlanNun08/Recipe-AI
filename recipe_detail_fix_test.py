#!/usr/bin/env python3
"""
Recipe Detail Endpoint Fix Testing Script
Testing the fixed recipe detail endpoint to verify Starbucks recipes can be accessed properly
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class RecipeDetailTester:
    def __init__(self):
        self.results = []
        self.demo_user_id = None
        
    async def log_result(self, test_name, success, details, error=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            result["error"] = str(error)
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()

    async def authenticate_demo_user(self):
        """Authenticate demo user for testing"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_data = {
                    "email": "demo@test.com",
                    "password": "password123"
                }
                
                response = await client.post(f"{API_BASE}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.demo_user_id = user_data.get('user', {}).get('id')
                    await self.log_result(
                        "Demo User Authentication",
                        True,
                        f"Successfully authenticated demo user with ID: {self.demo_user_id}"
                    )
                    return True
                else:
                    await self.log_result(
                        "Demo User Authentication",
                        False,
                        f"Failed to authenticate demo user. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Demo User Authentication",
                False,
                "Exception during demo user authentication",
                str(e)
            )
            return False

    async def test_starbucks_recipe_detail(self):
        """Test the problematic Starbucks recipe ID from the review request"""
        starbucks_recipe_id = "262099f5-e16f-4c75-9546-d91f86977cdc"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/recipes/{starbucks_recipe_id}/detail")
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    
                    # Verify it's a Starbucks recipe
                    recipe_type = recipe_data.get('type', 'unknown')
                    recipe_title = recipe_data.get('title') or recipe_data.get('drink_name') or recipe_data.get('name', 'Unknown')
                    
                    await self.log_result(
                        "Starbucks Recipe Detail Access",
                        True,
                        f"Successfully retrieved Starbucks recipe: '{recipe_title}' (Type: {recipe_type})"
                    )
                    
                    # Verify required fields are present
                    required_fields = ['id', 'title', 'type']
                    missing_fields = [field for field in required_fields if not recipe_data.get(field)]
                    
                    if missing_fields:
                        await self.log_result(
                            "Starbucks Recipe Structure Validation",
                            False,
                            f"Missing required fields: {missing_fields}",
                            f"Recipe data: {json.dumps(recipe_data, indent=2)}"
                        )
                    else:
                        await self.log_result(
                            "Starbucks Recipe Structure Validation",
                            True,
                            f"All required fields present. Recipe type: {recipe_type}"
                        )
                    
                    return True
                    
                elif response.status_code == 404:
                    await self.log_result(
                        "Starbucks Recipe Detail Access",
                        False,
                        f"Starbucks recipe {starbucks_recipe_id} still returns 404 - fix not working",
                        response.text
                    )
                    return False
                else:
                    await self.log_result(
                        "Starbucks Recipe Detail Access",
                        False,
                        f"Unexpected status code: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Starbucks Recipe Detail Access",
                False,
                f"Exception testing Starbucks recipe {starbucks_recipe_id}",
                str(e)
            )
            return False

    async def test_regular_recipe_detail(self):
        """Test regular recipe ID to ensure it still works"""
        regular_recipe_id = "6fa791db-f555-41bc-abd9-c503fe0d3fa7"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/recipes/{regular_recipe_id}/detail")
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    
                    recipe_type = recipe_data.get('type', 'unknown')
                    recipe_title = recipe_data.get('title', 'Unknown')
                    
                    await self.log_result(
                        "Regular Recipe Detail Access",
                        True,
                        f"Successfully retrieved regular recipe: '{recipe_title}' (Type: {recipe_type})"
                    )
                    
                    # Verify it's a regular recipe
                    if recipe_type == 'regular':
                        await self.log_result(
                            "Regular Recipe Type Validation",
                            True,
                            f"Recipe correctly identified as regular type"
                        )
                    else:
                        await self.log_result(
                            "Regular Recipe Type Validation",
                            False,
                            f"Expected 'regular' type but got '{recipe_type}'"
                        )
                    
                    return True
                    
                elif response.status_code == 404:
                    await self.log_result(
                        "Regular Recipe Detail Access",
                        False,
                        f"Regular recipe {regular_recipe_id} not found - may not exist in database",
                        response.text
                    )
                    return False
                else:
                    await self.log_result(
                        "Regular Recipe Detail Access",
                        False,
                        f"Unexpected status code: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Regular Recipe Detail Access",
                False,
                f"Exception testing regular recipe {regular_recipe_id}",
                str(e)
            )
            return False

    async def test_multi_collection_search(self):
        """Test that the endpoint searches multiple collections properly"""
        
        # Test with different recipe types to verify multi-collection search
        generated_recipe_id = None
        
        # First generate a recipe to test with
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{API_BASE}/recipes/generate",
                    json={
                        "user_id": self.demo_user_id,
                        "cuisine_type": "Italian",
                        "meal_type": "dinner", 
                        "difficulty": "medium",
                        "servings": 4
                    }
                )
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    generated_recipe_id = recipe_data.get('id')
                    
                    await self.log_result(
                        "Recipe Generation for Multi-Collection Test",
                        True,
                        f"Generated test recipe with ID: {generated_recipe_id}"
                    )
                else:
                    await self.log_result(
                        "Recipe Generation for Multi-Collection Test",
                        False,
                        f"Failed to generate test recipe. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Recipe Generation for Multi-Collection Test",
                False,
                "Exception generating test recipe",
                str(e)
            )
            return False
        
        # Now test the detail endpoint with the generated recipe
        if generated_recipe_id:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{API_BASE}/recipes/{generated_recipe_id}/detail")
                    
                    if response.status_code == 200:
                        recipe_data = response.json()
                        await self.log_result(
                            "Multi-Collection Search - Generated Recipe",
                            True,
                            f"Successfully found generated recipe in multi-collection search"
                        )
                        return True
                    else:
                        await self.log_result(
                            "Multi-Collection Search - Generated Recipe",
                            False,
                            f"Failed to find generated recipe. Status: {response.status_code}",
                            response.text
                        )
                        return False
                        
            except Exception as e:
                await self.log_result(
                    "Multi-Collection Search - Generated Recipe",
                    False,
                    "Exception testing multi-collection search",
                    str(e)
                )
                return False
        
        return False

    async def test_curated_starbucks_recipes(self):
        """Test access to curated Starbucks recipes"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # First get list of curated recipes
                response = await client.get(f"{API_BASE}/curated-starbucks-recipes")
                
                if response.status_code == 200:
                    recipes_data = response.json()
                    recipes = recipes_data.get('recipes', [])
                    
                    if recipes:
                        # Test the first curated recipe
                        first_recipe = recipes[0]
                        recipe_id = first_recipe.get('id')
                        recipe_name = first_recipe.get('name', 'Unknown')
                        
                        await self.log_result(
                            "Curated Starbucks Recipes List",
                            True,
                            f"Found {len(recipes)} curated recipes. Testing first: '{recipe_name}'"
                        )
                        
                        # Test detail endpoint with curated recipe
                        detail_response = await client.get(f"{API_BASE}/recipes/{recipe_id}/detail")
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            await self.log_result(
                                "Curated Starbucks Recipe Detail Access",
                                True,
                                f"Successfully accessed curated recipe detail: '{recipe_name}'"
                            )
                            return True
                        else:
                            await self.log_result(
                                "Curated Starbucks Recipe Detail Access",
                                False,
                                f"Failed to access curated recipe detail. Status: {detail_response.status_code}",
                                detail_response.text
                            )
                            return False
                    else:
                        await self.log_result(
                            "Curated Starbucks Recipes List",
                            False,
                            "No curated recipes found in database"
                        )
                        return False
                else:
                    await self.log_result(
                        "Curated Starbucks Recipes List",
                        False,
                        f"Failed to get curated recipes. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Curated Starbucks Recipe Testing",
                False,
                "Exception testing curated Starbucks recipes",
                str(e)
            )
            return False

    async def test_navigation_fix_verification(self):
        """Verify that the null recipe ID navigation issue is resolved"""
        
        # Test recipe history endpoint to ensure it returns proper IDs
        if not self.demo_user_id:
            await self.log_result(
                "Navigation Fix Verification",
                False,
                "Cannot test navigation fix - no authenticated user"
            )
            return False
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/recipes/history/{self.demo_user_id}")
                
                if response.status_code == 200:
                    history_data = response.json()
                    recipes = history_data.get('recipes', [])
                    
                    if recipes:
                        # Check that all recipes have valid IDs
                        null_id_count = 0
                        valid_id_count = 0
                        starbucks_count = 0
                        
                        for recipe in recipes:
                            recipe_id = recipe.get('id')
                            recipe_type = recipe.get('type', 'unknown')
                            
                            if not recipe_id or recipe_id == 'null':
                                null_id_count += 1
                            else:
                                valid_id_count += 1
                                
                            if recipe_type == 'starbucks':
                                starbucks_count += 1
                        
                        await self.log_result(
                            "Recipe History ID Validation",
                            null_id_count == 0,
                            f"Found {valid_id_count} valid IDs, {null_id_count} null IDs, {starbucks_count} Starbucks recipes"
                        )
                        
                        # Test navigation to a Starbucks recipe from history if available
                        starbucks_recipes = [r for r in recipes if r.get('type') == 'starbucks']
                        if starbucks_recipes:
                            test_recipe = starbucks_recipes[0]
                            test_id = test_recipe.get('id')
                            test_name = test_recipe.get('name') or test_recipe.get('drink_name', 'Unknown')
                            
                            # Test detail endpoint
                            detail_response = await client.get(f"{API_BASE}/recipes/{test_id}/detail")
                            
                            if detail_response.status_code == 200:
                                await self.log_result(
                                    "Starbucks Navigation from History",
                                    True,
                                    f"Successfully navigated to Starbucks recipe '{test_name}' from history"
                                )
                                return True
                            else:
                                await self.log_result(
                                    "Starbucks Navigation from History",
                                    False,
                                    f"Failed to navigate to Starbucks recipe from history. Status: {detail_response.status_code}",
                                    detail_response.text
                                )
                                return False
                        else:
                            await self.log_result(
                                "Starbucks Navigation from History",
                                True,
                                "No Starbucks recipes in history to test navigation"
                            )
                            return True
                    else:
                        await self.log_result(
                            "Recipe History ID Validation",
                            True,
                            "No recipes in history - cannot test null ID issue"
                        )
                        return True
                else:
                    await self.log_result(
                        "Recipe History Access",
                        False,
                        f"Failed to access recipe history. Status: {response.status_code}",
                        response.text
                    )
                    return False
                    
        except Exception as e:
            await self.log_result(
                "Navigation Fix Verification",
                False,
                "Exception testing navigation fix",
                str(e)
            )
            return False

    async def run_all_tests(self):
        """Run all tests for the recipe detail endpoint fix"""
        print("🧪 RECIPE DETAIL ENDPOINT FIX TESTING")
        print("=" * 50)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print()
        
        # Authenticate first
        auth_success = await self.authenticate_demo_user()
        if not auth_success:
            print("❌ Cannot proceed without authentication")
            return
        
        # Run all tests
        test_methods = [
            self.test_starbucks_recipe_detail,
            self.test_regular_recipe_detail,
            self.test_multi_collection_search,
            self.test_curated_starbucks_recipes,
            self.test_navigation_fix_verification
        ]
        
        passed = 0
        total = len(test_methods)
        
        for test_method in test_methods:
            try:
                success = await test_method()
                if success:
                    passed += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_method.__name__}: {e}")
        
        # Summary
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print(f"Passed: {passed}/{total} tests")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Recipe detail endpoint fix is working correctly!")
        elif passed >= total * 0.8:
            print("✅ MOSTLY WORKING - Minor issues detected but core functionality works")
        else:
            print("❌ CRITICAL ISSUES - Recipe detail endpoint fix needs attention")
        
        return passed, total

async def main():
    """Main test execution"""
    tester = RecipeDetailTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())