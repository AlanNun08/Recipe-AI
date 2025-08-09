#!/usr/bin/env python3
"""
Starbucks Recipe Testing Script
Testing Starbucks recipe generation and data structure
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

class StarbucksRecipeTester:
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
    
    async def generate_starbucks_recipe(self, drink_type: str = "frappuccino"):
        """Generate a Starbucks recipe"""
        self.log(f"=== Generating Starbucks {drink_type} Recipe ===")
        
        try:
            starbucks_data = {
                "user_id": self.user_id,
                "drink_type": drink_type,
                "flavor_inspiration": "vanilla caramel"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/generate-starbucks-drink", json=starbucks_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Starbucks recipe generated successfully")
                
                # Analyze the response structure
                self.log(f"Recipe ID: {result.get('id')}")
                self.log(f"Drink Name: {result.get('drink_name')}")
                self.log(f"Base Drink: {result.get('base_drink')}")
                self.log(f"Category: {result.get('category')}")
                self.log(f"Available fields: {list(result.keys())}")
                
                return result
                
            else:
                self.log(f"❌ Starbucks recipe generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error generating Starbucks recipe: {str(e)}", "ERROR")
            return None
    
    async def test_recipe_history_with_starbucks(self):
        """Test recipe history after generating Starbucks recipes"""
        self.log("=== Testing Recipe History with Starbucks Recipes ===")
        
        try:
            # Get recipe history
            response = await self.client.get(f"{BACKEND_URL}/recipes/history/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                recipes = result.get("recipes", [])
                
                self.log(f"Total recipes in history: {len(recipes)}")
                
                # Analyze different recipe types
                starbucks_recipes = []
                regular_recipes = []
                
                for recipe in recipes:
                    # Check if it's a Starbucks recipe
                    if any(key in recipe for key in ["drink_name", "base_drink", "ordering_script", "modifications"]):
                        starbucks_recipes.append(recipe)
                    else:
                        regular_recipes.append(recipe)
                
                self.log(f"Found {len(starbucks_recipes)} Starbucks recipes")
                self.log(f"Found {len(regular_recipes)} regular recipes")
                
                # Analyze Starbucks recipes in detail
                if starbucks_recipes:
                    self.log("\n=== STARBUCKS RECIPE ANALYSIS ===")
                    
                    for i, recipe in enumerate(starbucks_recipes[:3]):
                        self.log(f"\n--- Starbucks Recipe {i+1} ---")
                        
                        # Check ID field
                        recipe_id = recipe.get("id")
                        self.log(f"Recipe ID: {recipe_id} ({'✅ Present' if recipe_id else '❌ NULL/Missing'})")
                        
                        # Check Starbucks-specific fields
                        drink_name = recipe.get("drink_name")
                        base_drink = recipe.get("base_drink")
                        category = recipe.get("category")
                        
                        self.log(f"Drink Name: {drink_name}")
                        self.log(f"Base Drink: {base_drink}")
                        self.log(f"Category: {category}")
                        self.log(f"All fields: {list(recipe.keys())}")
                        
                        # Test if this recipe can be used for navigation
                        if recipe_id:
                            await self.test_starbucks_recipe_detail(recipe_id)
                
                return True
                
            else:
                self.log(f"❌ Recipe history failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe history: {str(e)}", "ERROR")
            return False
    
    async def test_starbucks_recipe_detail(self, recipe_id: str):
        """Test accessing Starbucks recipe detail"""
        self.log(f"=== Testing Starbucks Recipe Detail: {recipe_id} ===")
        
        try:
            # Try regular recipe detail endpoint
            response = await self.client.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
            
            self.log(f"Regular detail endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Starbucks recipe accessible via regular detail endpoint")
                self.log(f"Fields in detail: {list(result.keys())}")
                return True
            else:
                self.log(f"❌ Regular detail endpoint failed: {response.text}")
                
                # Check if there's a specific Starbucks endpoint
                # (This might not exist, but let's check)
                try:
                    starbucks_response = await self.client.get(f"{BACKEND_URL}/starbucks-recipes/{recipe_id}")
                    self.log(f"Starbucks-specific endpoint status: {starbucks_response.status_code}")
                    
                    if starbucks_response.status_code == 200:
                        self.log("✅ Starbucks recipe accessible via specific endpoint")
                        return True
                except:
                    pass
                
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing Starbucks recipe detail: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all Starbucks recipe tests"""
        self.log("🚀 Starting Starbucks Recipe Testing")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Login
        test_results["login"] = await self.login_demo_user()
        
        if not test_results["login"]:
            self.log("❌ Cannot proceed without login")
            return test_results
        
        # Test 2: Generate different types of Starbucks recipes
        drink_types = ["frappuccino", "refresher", "lemonade", "iced_matcha_latte"]
        generated_recipes = []
        
        for drink_type in drink_types:
            recipe = await self.generate_starbucks_recipe(drink_type)
            if recipe:
                generated_recipes.append(recipe)
        
        test_results["generation"] = len(generated_recipes) > 0
        
        # Test 3: Check recipe history with Starbucks recipes
        test_results["history_with_starbucks"] = await self.test_recipe_history_with_starbucks()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 STARBUCKS RECIPE TEST RESULTS")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        self.log(f"Generated {len(generated_recipes)} Starbucks recipes")
        
        return test_results

async def main():
    """Main test execution"""
    tester = StarbucksRecipeTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())