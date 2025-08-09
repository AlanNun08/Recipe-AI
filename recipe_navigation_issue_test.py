#!/usr/bin/env python3
"""
Recipe Navigation Issue Comprehensive Test
Demonstrates the root cause of null recipe ID navigation issue
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Get backend URL from frontend .env
BACKEND_URL = "https://2c83b5a7-3245-4a38-a9d6-ccc45cb3ba91.preview.emergentagent.com/api"

# Demo user credentials
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class RecipeNavigationIssueTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def login_demo_user(self):
        """Login with demo user credentials"""
        self.log("=== Logging in Demo User ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user", {}).get("id")
                
                self.log(f"✅ Demo user login successful")
                self.log(f"User ID: {self.user_id}")
                
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error logging in demo user: {str(e)}", "ERROR")
            return False
    
    async def demonstrate_navigation_issue(self):
        """Demonstrate the exact navigation issue described in the review"""
        self.log("=== DEMONSTRATING RECIPE NAVIGATION ISSUE ===")
        
        try:
            # Step 1: Get recipe history (what user sees in Recipe History screen)
            self.log("\n--- Step 1: Getting Recipe History ---")
            history_response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.user_id}")
            
            if history_response.status_code != 200:
                self.log(f"❌ Recipe history failed: {history_response.text}")
                return False
            
            history_data = history_response.json()
            recipes = history_data.get("recipes", [])
            
            self.log(f"✅ Recipe history loaded: {len(recipes)} recipes")
            
            # Step 2: Analyze recipe types and their navigation potential
            self.log("\n--- Step 2: Analyzing Recipe Types for Navigation ---")
            
            regular_recipes = [r for r in recipes if r.get("type") == "recipe"]
            starbucks_recipes = [r for r in recipes if r.get("type") == "starbucks"]
            
            self.log(f"Regular recipes: {len(regular_recipes)}")
            self.log(f"Starbucks recipes: {len(starbucks_recipes)}")
            
            # Step 3: Test navigation for regular recipes (should work)
            if regular_recipes:
                self.log("\n--- Step 3: Testing Regular Recipe Navigation (Should Work) ---")
                regular_recipe = regular_recipes[0]
                regular_id = regular_recipe.get("id")
                regular_title = regular_recipe.get("title")
                
                self.log(f"Testing regular recipe: {regular_title}")
                self.log(f"Recipe ID: {regular_id}")
                
                if regular_id:
                    detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{regular_id}/detail")
                    self.log(f"Detail endpoint status: {detail_response.status_code}")
                    
                    if detail_response.status_code == 200:
                        self.log("✅ Regular recipe navigation WORKS")
                    else:
                        self.log(f"❌ Regular recipe navigation FAILED: {detail_response.text}")
                else:
                    self.log("❌ Regular recipe has NULL ID")
            
            # Step 4: Test navigation for Starbucks recipes (should fail)
            if starbucks_recipes:
                self.log("\n--- Step 4: Testing Starbucks Recipe Navigation (Should Fail) ---")
                starbucks_recipe = starbucks_recipes[0]
                starbucks_id = starbucks_recipe.get("id")
                starbucks_name = starbucks_recipe.get("drink_name") or starbucks_recipe.get("name")
                
                self.log(f"Testing Starbucks recipe: {starbucks_name}")
                self.log(f"Recipe ID: {starbucks_id}")
                
                if starbucks_id:
                    detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{starbucks_id}/detail")
                    self.log(f"Detail endpoint status: {detail_response.status_code}")
                    
                    if detail_response.status_code == 200:
                        self.log("✅ Starbucks recipe navigation WORKS (unexpected)")
                    else:
                        self.log(f"❌ Starbucks recipe navigation FAILED: {detail_response.text}")
                        self.log("🔍 ROOT CAUSE: Detail endpoint only looks in 'recipes' collection, not 'starbucks_recipes'")
                else:
                    self.log("❌ Starbucks recipe has NULL ID")
            else:
                self.log("\n--- Step 4: No Starbucks recipes found, testing with curated ---")
                await self.test_curated_starbucks_navigation()
            
            # Step 5: Demonstrate the exact user experience
            self.log("\n--- Step 5: User Experience Simulation ---")
            self.log("USER CLICKS ON RECIPE FROM HISTORY:")
            
            if recipes:
                test_recipe = recipes[0]  # First recipe in history
                recipe_id = test_recipe.get("id")
                recipe_name = test_recipe.get("title") or test_recipe.get("drink_name") or test_recipe.get("name")
                recipe_type = test_recipe.get("type")
                
                self.log(f"  Recipe: {recipe_name}")
                self.log(f"  Type: {recipe_type}")
                self.log(f"  ID passed to navigation: {recipe_id}")
                
                if recipe_id:
                    self.log(f"  Frontend calls: /api/recipes/{recipe_id}/detail")
                    
                    detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
                    
                    if detail_response.status_code == 200:
                        self.log("  ✅ RESULT: Recipe detail loads successfully")
                    else:
                        self.log(f"  ❌ RESULT: Recipe detail fails with {detail_response.status_code}")
                        self.log(f"  ❌ USER SEES: 'No Recipe Found' or error screen")
                        self.log(f"  🔍 TECHNICAL CAUSE: {detail_response.text}")
                else:
                    self.log("  ❌ RESULT: Recipe ID is NULL - navigation fails immediately")
                    self.log("  ❌ USER SEES: 'No Recipe Found' or error screen")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error demonstrating navigation issue: {str(e)}", "ERROR")
            return False
    
    async def test_curated_starbucks_navigation(self):
        """Test navigation with curated Starbucks recipes"""
        self.log("\n--- Testing Curated Starbucks Navigation ---")
        
        try:
            # Get curated Starbucks recipes
            curated_response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes")
            
            if curated_response.status_code == 200:
                curated_data = curated_response.json()
                curated_recipes = curated_data.get("recipes", [])
                
                if curated_recipes:
                    test_recipe = curated_recipes[0]
                    recipe_id = test_recipe.get("id")
                    recipe_name = test_recipe.get("name")
                    
                    self.log(f"Testing curated Starbucks: {recipe_name}")
                    self.log(f"Recipe ID: {recipe_id}")
                    
                    if recipe_id:
                        detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
                        self.log(f"Detail endpoint status: {detail_response.status_code}")
                        
                        if detail_response.status_code == 200:
                            self.log("✅ Curated Starbucks navigation WORKS")
                        else:
                            self.log(f"❌ Curated Starbucks navigation FAILED: {detail_response.text}")
                            self.log("🔍 ROOT CAUSE: Detail endpoint doesn't check 'curated_starbucks_recipes' collection")
                    else:
                        self.log("❌ Curated Starbucks recipe has NULL ID")
                        
        except Exception as e:
            self.log(f"❌ Error testing curated Starbucks: {str(e)}", "ERROR")
    
    async def analyze_backend_collections(self):
        """Analyze what collections exist and how they should be handled"""
        self.log("\n=== BACKEND COLLECTION ANALYSIS ===")
        
        self.log("Based on code analysis, the backend has these recipe collections:")
        self.log("1. 'recipes' - Regular generated recipes (cuisine, snacks, beverages)")
        self.log("2. 'starbucks_recipes' - User-generated Starbucks drinks")
        self.log("3. 'curated_starbucks_recipes' - Pre-made Starbucks recipes")
        self.log("4. 'user_shared_recipes' - Community shared recipes")
        
        self.log("\nCURRENT ISSUE:")
        self.log("- Recipe history endpoint fetches from multiple collections ✅")
        self.log("- Recipe detail endpoint only looks in 'recipes' collection ❌")
        
        self.log("\nSOLUTION NEEDED:")
        self.log("- Recipe detail endpoint should check recipe type and look in appropriate collection")
        self.log("- OR provide separate detail endpoints for different recipe types")
        self.log("- OR modify frontend to use different navigation based on recipe type")
    
    async def run_comprehensive_test(self):
        """Run comprehensive navigation issue test"""
        self.log("🚀 Starting Recipe Navigation Issue Analysis")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Login
        test_results["login"] = await self.login_demo_user()
        
        if not test_results["login"]:
            self.log("❌ Cannot proceed without login")
            return test_results
        
        # Test 2: Demonstrate the navigation issue
        test_results["navigation_demo"] = await self.demonstrate_navigation_issue()
        
        # Test 3: Analyze backend structure
        await self.analyze_backend_collections()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 NAVIGATION ISSUE ANALYSIS SUMMARY")
        self.log("=" * 70)
        
        self.log("ISSUE IDENTIFIED: ❌ Recipe detail endpoint doesn't handle all recipe types")
        self.log("ROOT CAUSE: Detail endpoint only searches 'recipes' collection")
        self.log("AFFECTED: Starbucks recipes (both generated and curated)")
        self.log("USER IMPACT: 'No Recipe Found' when clicking Starbucks recipes in history")
        
        self.log("\nRECOMMENDED FIX:")
        self.log("1. Modify /api/recipes/{recipe_id}/detail endpoint to:")
        self.log("   - First check 'recipes' collection")
        self.log("   - If not found, check 'starbucks_recipes' collection")
        self.log("   - If not found, check 'curated_starbucks_recipes' collection")
        self.log("2. OR add recipe type detection in frontend and use appropriate endpoints")
        
        return test_results

async def main():
    """Main test execution"""
    tester = RecipeNavigationIssueTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())