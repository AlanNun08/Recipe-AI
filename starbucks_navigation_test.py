#!/usr/bin/env python3
"""
Starbucks Recipe Navigation Testing
Testing Starbucks recipes specifically to ensure multi-collection search is working
"""

import asyncio
import httpx
import json
from datetime import datetime

class StarbucksNavigationTester:
    def __init__(self):
        self.backend_url = "https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com/api"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_starbucks_collections(self):
        """Test all Starbucks recipe collections"""
        self.log("=== Testing Starbucks Recipe Collections ===")
        
        collections_tested = []
        
        # Test curated Starbucks recipes
        try:
            response = await self.client.get(f"{self.backend_url}/curated-starbucks-recipes")
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                self.log(f"✅ Curated Starbucks recipes: {len(recipes)} found")
                collections_tested.extend(recipes[:3])  # Take first 3 for testing
            else:
                self.log(f"❌ Curated Starbucks recipes failed: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Error getting curated Starbucks recipes: {str(e)}")
        
        return collections_tested
    
    async def test_starbucks_detail_navigation(self, starbucks_recipes):
        """Test Starbucks recipe detail navigation"""
        self.log("=== Testing Starbucks Recipe Detail Navigation ===")
        
        successful_tests = 0
        total_tests = len(starbucks_recipes)
        
        for i, recipe in enumerate(starbucks_recipes):
            recipe_id = recipe.get("id")
            recipe_name = recipe.get("name", "Unknown")
            
            self.log(f"\n--- Testing Starbucks Recipe {i+1}: {recipe_name} ---")
            self.log(f"Recipe ID: {recipe_id}")
            
            try:
                # Test detail endpoint
                response = await self.client.get(f"{self.backend_url}/recipes/{recipe_id}/detail")
                
                if response.status_code == 200:
                    result = response.json()
                    actual_id = result.get("id")
                    actual_name = result.get("title") or result.get("name", "Unknown")
                    actual_type = result.get("type", "unknown")
                    
                    self.log(f"✅ Successfully retrieved Starbucks recipe")
                    self.log(f"  Actual ID: {actual_id}")
                    self.log(f"  Actual Name: {actual_name}")
                    self.log(f"  Actual Type: {actual_type}")
                    
                    # Check ID match
                    if actual_id == recipe_id:
                        self.log("✅ Recipe ID matches perfectly")
                        successful_tests += 1
                    else:
                        self.log("❌ Recipe ID mismatch!")
                        self.log(f"  Expected: {recipe_id}")
                        self.log(f"  Got:      {actual_id}")
                        
                elif response.status_code == 404:
                    self.log("❌ Starbucks recipe not found (404)")
                    self.log("This indicates multi-collection search is NOT working!")
                    
                else:
                    self.log(f"❌ Starbucks recipe detail failed: {response.status_code}")
                    self.log(f"Response: {response.text}")
                    
            except Exception as e:
                self.log(f"❌ Error testing Starbucks recipe: {str(e)}")
        
        return successful_tests, total_tests
    
    async def run_starbucks_navigation_test(self):
        """Run comprehensive Starbucks navigation test"""
        self.log("🚀 Starting Starbucks Recipe Navigation Testing")
        self.log("=" * 70)
        
        # Step 1: Get Starbucks recipes from collections
        starbucks_recipes = await self.test_starbucks_collections()
        
        if not starbucks_recipes:
            self.log("❌ No Starbucks recipes found for testing")
            return False
        
        # Step 2: Test detail navigation
        successful, total = await self.test_starbucks_detail_navigation(starbucks_recipes)
        
        # Step 3: Results
        self.log("\n" + "=" * 70)
        self.log("🔍 STARBUCKS NAVIGATION TEST RESULTS")
        self.log("=" * 70)
        self.log(f"Total Starbucks recipes tested: {total}")
        self.log(f"Successful navigations: {successful}")
        self.log(f"Failed navigations: {total - successful}")
        
        if successful == total and total > 0:
            self.log("🎉 ALL STARBUCKS NAVIGATION TESTS PASSED")
            self.log("✅ Multi-collection search is working correctly")
            self.log("✅ Starbucks recipes are accessible via detail endpoint")
            return True
        else:
            self.log("❌ STARBUCKS NAVIGATION ISSUES DETECTED")
            self.log("🔧 Multi-collection search may not be working properly")
            return False

async def main():
    """Main test execution"""
    tester = StarbucksNavigationTester()
    
    try:
        success = await tester.run_starbucks_navigation_test()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)