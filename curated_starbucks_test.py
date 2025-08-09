#!/usr/bin/env python3
"""
Curated Starbucks Recipe Testing Script
Testing curated Starbucks recipes and their data structure
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Get backend URL from frontend .env
BACKEND_URL = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"

class CuratedStarbucksTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_curated_starbucks_recipes(self):
        """Test curated Starbucks recipes endpoint"""
        self.log("=== Testing Curated Starbucks Recipes ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                recipes = result.get("recipes", [])
                total = result.get("total", 0)
                
                self.log(f"✅ Curated Starbucks recipes endpoint working")
                self.log(f"Total curated recipes: {total}")
                self.log(f"Recipes returned: {len(recipes)}")
                
                if recipes:
                    self.log("\n=== CURATED STARBUCKS RECIPE ANALYSIS ===")
                    
                    for i, recipe in enumerate(recipes[:3]):
                        self.log(f"\n--- Curated Recipe {i+1} ---")
                        
                        # Check ID field
                        recipe_id = recipe.get("id")
                        self.log(f"Recipe ID: {recipe_id} ({'✅ Present' if recipe_id else '❌ NULL/Missing'})")
                        
                        # Check Starbucks fields
                        name = recipe.get("name")
                        base = recipe.get("base")
                        category = recipe.get("category")
                        
                        self.log(f"Name: {name}")
                        self.log(f"Base: {base}")
                        self.log(f"Category: {category}")
                        self.log(f"All fields: {list(recipe.keys())}")
                        
                        # Check if this has navigation-friendly structure
                        if recipe_id:
                            self.log(f"✅ Recipe ID available for navigation: {recipe_id}")
                        else:
                            self.log("❌ CRITICAL: Recipe ID missing for navigation!")
                
                return recipes
                
            else:
                self.log(f"❌ Curated Starbucks recipes failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log(f"❌ Error testing curated recipes: {str(e)}", "ERROR")
            return []
    
    async def test_recipe_navigation_simulation(self, recipes):
        """Simulate the navigation issue by testing how frontend would handle these recipes"""
        self.log("=== Simulating Frontend Navigation Issue ===")
        
        if not recipes:
            self.log("❌ No recipes to test navigation with")
            return False
        
        try:
            # Simulate what happens when frontend tries to navigate
            for i, recipe in enumerate(recipes[:3]):
                self.log(f"\n--- Navigation Test {i+1} ---")
                
                recipe_id = recipe.get("id")
                recipe_name = recipe.get("name") or recipe.get("title")
                
                self.log(f"Recipe Name: {recipe_name}")
                self.log(f"Recipe ID from history: {recipe_id}")
                
                # Simulate the navigation call that frontend would make
                if recipe_id:
                    self.log(f"✅ Frontend would navigate with ID: {recipe_id}")
                    
                    # Test if this ID works with detail endpoint
                    try:
                        detail_response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
                        self.log(f"Detail endpoint status: {detail_response.status_code}")
                        
                        if detail_response.status_code == 200:
                            self.log("✅ Navigation would succeed")
                        else:
                            self.log(f"❌ Navigation would fail: {detail_response.text}")
                    except Exception as e:
                        self.log(f"❌ Navigation would fail with error: {str(e)}")
                        
                else:
                    self.log("❌ Frontend would receive NULL ID - navigation would fail!")
                    
                    # Check what the frontend might see
                    self.log("Frontend debugging info:")
                    self.log(f"  typeof recipe_id: {type(recipe_id)}")
                    self.log(f"  recipe_id == null: {recipe_id is None}")
                    self.log(f"  recipe_id == undefined: {recipe_id == ''}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error in navigation simulation: {str(e)}", "ERROR")
            return False
    
    async def test_different_recipe_sources(self):
        """Test different sources of recipes to identify the issue"""
        self.log("=== Testing Different Recipe Sources ===")
        
        # Test 1: Curated Starbucks recipes
        curated_recipes = await self.test_curated_starbucks_recipes()
        
        # Test 2: Check if there are other recipe endpoints
        endpoints_to_test = [
            "/shared-recipes",
            "/recipes/history/f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",  # Demo user ID
        ]
        
        for endpoint in endpoints_to_test:
            self.log(f"\n--- Testing {endpoint} ---")
            
            try:
                response = await self.client.get(f"{BACKEND_URL}{endpoint}")
                self.log(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for recipes in different response formats
                    recipes = result.get("recipes", [])
                    if not recipes and isinstance(result, list):
                        recipes = result
                    
                    self.log(f"Found {len(recipes)} recipes")
                    
                    if recipes:
                        sample_recipe = recipes[0]
                        recipe_id = sample_recipe.get("id")
                        self.log(f"Sample recipe ID: {recipe_id}")
                        self.log(f"Sample recipe fields: {list(sample_recipe.keys())}")
                        
            except Exception as e:
                self.log(f"Error testing {endpoint}: {str(e)}")
        
        return True
    
    async def run_comprehensive_test(self):
        """Run all curated Starbucks tests"""
        self.log("🚀 Starting Curated Starbucks Recipe Testing")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Curated recipes
        curated_recipes = await self.test_curated_starbucks_recipes()
        test_results["curated_recipes"] = len(curated_recipes) > 0
        
        # Test 2: Navigation simulation
        test_results["navigation_simulation"] = await self.test_recipe_navigation_simulation(curated_recipes)
        
        # Test 3: Different recipe sources
        test_results["different_sources"] = await self.test_different_recipe_sources()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 CURATED STARBUCKS TEST RESULTS")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Analysis
        if curated_recipes:
            ids_present = sum(1 for recipe in curated_recipes if recipe.get("id"))
            self.log(f"\nAnalysis: {ids_present}/{len(curated_recipes)} curated recipes have IDs")
            
            if ids_present < len(curated_recipes):
                self.log("❌ ISSUE IDENTIFIED: Some curated recipes missing IDs")
            else:
                self.log("✅ All curated recipes have proper IDs")
        
        return test_results

async def main():
    """Main test execution"""
    tester = CuratedStarbucksTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())