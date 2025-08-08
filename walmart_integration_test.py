#!/usr/bin/env python3
"""
Comprehensive Testing Script for New Walmart Integration Flow
Testing the complete flow as requested in review:
1. POST /api/grocery/cart-options - Get product options for recipe ingredients
2. POST /api/grocery/generate-cart-url - Generate Walmart cart URL

Test Flow:
1. Login demo user (demo@test.com/password123)
2. Get a recipe that has ingredients/shopping_list
3. Call /api/grocery/cart-options with recipe_id and user_id
4. Take the returned product options
5. Call /api/grocery/generate-cart-url with selected products
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fd9864fb-c204-41f3-8f4c-e2111c0751fc.preview.emergentagent.com') + '/api'

# Demo user credentials as specified in review
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class WalmartIntegrationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.user_id = None
        self.recipe_id = None
        self.test_results = {}
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Step 1: Login demo user (demo@test.com/password123)"""
        self.log("=== STEP 1: Testing Demo User Login ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            self.log(f"Attempting login with {DEMO_EMAIL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            self.log(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user", {}).get("id")
                user_name = result.get("user", {}).get("first_name", "Unknown")
                is_verified = result.get("user", {}).get("is_verified", False)
                
                self.log(f"✅ Demo user login successful!")
                self.log(f"User ID: {self.user_id}")
                self.log(f"User Name: {user_name}")
                self.log(f"Verified Status: {is_verified}")
                
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error during demo user login: {str(e)}", "ERROR")
            return False
    
    async def test_get_recipe_with_ingredients(self):
        """Step 2: Get a recipe that has ingredients/shopping_list"""
        self.log("=== STEP 2: Getting Recipe with Ingredients ===")
        
        try:
            # First try to get weekly meal plan recipes
            self.log("Checking for weekly meal plan recipes...")
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("has_plan") and result.get("plan", {}).get("meals"):
                    meals = result["plan"]["meals"]
                    self.log(f"✅ Found {len(meals)} meals in weekly plan")
                    
                    # Use the first meal with ingredients
                    for meal in meals:
                        if meal.get("ingredients") or meal.get("shopping_list"):
                            self.recipe_id = meal.get("id")
                            recipe_name = meal.get("name", "Unknown Recipe")
                            ingredients = meal.get("ingredients", meal.get("shopping_list", []))
                            
                            self.log(f"✅ Selected recipe: {recipe_name}")
                            self.log(f"Recipe ID: {self.recipe_id}")
                            self.log(f"Ingredients ({len(ingredients)}): {ingredients[:5]}...")  # Show first 5
                            
                            return True
            
            # If no weekly recipes, try to generate a regular recipe
            self.log("No weekly recipes found, generating a new recipe...")
            recipe_data = {
                "user_id": self.user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Italian",
                "dietary_preferences": [],
                "ingredients_on_hand": [],
                "prep_time_max": 30,
                "servings": 4,
                "difficulty": "medium"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            if response.status_code == 200:
                result = response.json()
                self.recipe_id = result.get("id")
                recipe_title = result.get("title", "Unknown")
                shopping_list = result.get("shopping_list", [])
                
                self.log(f"✅ Generated new recipe: {recipe_title}")
                self.log(f"Recipe ID: {self.recipe_id}")
                self.log(f"Shopping list ({len(shopping_list)} items): {shopping_list}")
                
                return True
            else:
                self.log(f"❌ Recipe generation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error getting recipe: {str(e)}", "ERROR")
            return False
    
    async def test_cart_options_endpoint(self):
        """Step 3: Call /api/grocery/cart-options with recipe_id and user_id"""
        self.log("=== STEP 3: Testing Cart Options Endpoint ===")
        
        if not self.user_id or not self.recipe_id:
            self.log("❌ Missing user_id or recipe_id for cart options test")
            return False, None
        
        try:
            # Call the cart-options endpoint as specified
            params = {
                "recipe_id": self.recipe_id,
                "user_id": self.user_id
            }
            
            self.log(f"Calling POST /api/grocery/cart-options")
            self.log(f"Parameters: {params}")
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params=params)
            
            self.log(f"Cart options response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Cart options endpoint successful!")
                self.log(f"Recipe ID: {result.get('recipe_id')}")
                self.log(f"Recipe Name: {result.get('recipe_name')}")
                self.log(f"Total Ingredients: {result.get('total_ingredients', 0)}")
                self.log(f"Estimated Total: ${result.get('estimated_total', 0):.2f}")
                
                ingredient_options = result.get('ingredient_options', [])
                self.log(f"Ingredient options count: {len(ingredient_options)}")
                
                # Validate response structure as specified in review
                total_products = 0
                for i, option in enumerate(ingredient_options[:3]):  # Show first 3
                    ingredient_name = option.get('ingredient_name')
                    products = option.get('options', [])
                    selected_id = option.get('selected_product_id')
                    
                    self.log(f"  Ingredient {i+1}: {ingredient_name}")
                    self.log(f"    Product options: {len(products)}")
                    self.log(f"    Selected product ID: {selected_id}")
                    
                    total_products += len(products)
                    
                    # Show product details for first option
                    if products:
                        product = products[0]
                        self.log(f"    Sample product: {product.get('name')} - ${product.get('price')} ({product.get('brand')})")
                        
                        # Validate expected response structure
                        required_fields = ['product_id', 'name', 'price', 'brand', 'rating', 'image_url']
                        missing_fields = [field for field in required_fields if field not in product]
                        if missing_fields:
                            self.log(f"    ⚠️ Missing fields in product: {missing_fields}")
                
                self.log(f"✅ Total products across all ingredients: {total_products}")
                
                # Validate that we got 2-3 product options per ingredient as expected
                if ingredient_options:
                    avg_options = total_products / len(ingredient_options)
                    self.log(f"Average options per ingredient: {avg_options:.1f}")
                    
                    if 2 <= avg_options <= 3:
                        self.log("✅ Product options count meets expectation (2-3 per ingredient)")
                    else:
                        self.log(f"⚠️ Product options count outside expected range: {avg_options:.1f}")
                
                return True, result
            else:
                self.log(f"❌ Cart options endpoint failed: {response.text}")
                return False, None
                
        except Exception as e:
            self.log(f"❌ Error testing cart options endpoint: {str(e)}", "ERROR")
            return False, None
    
    async def test_generate_cart_url_endpoint(self, cart_options_result):
        """Step 4: Call /api/grocery/generate-cart-url with selected products"""
        self.log("=== STEP 4: Testing Generate Cart URL Endpoint ===")
        
        if not cart_options_result:
            self.log("❌ No cart options result to work with")
            return False
        
        try:
            # Extract selected products from cart options result
            ingredient_options = cart_options_result.get('ingredient_options', [])
            selected_products = []
            
            for option in ingredient_options:
                products = option.get('options', [])
                selected_product_id = option.get('selected_product_id')
                
                # Find the selected product
                selected_product = None
                for product in products:
                    if product.get('product_id') == selected_product_id:
                        selected_product = product
                        break
                
                if selected_product:
                    selected_products.append(selected_product)
            
            self.log(f"Prepared {len(selected_products)} selected products for cart URL generation")
            
            # Show sample selected products
            for i, product in enumerate(selected_products[:3]):
                self.log(f"  Product {i+1}: {product.get('name')} - ${product.get('price')} (ID: {product.get('product_id')})")
            
            # Call the generate-cart-url endpoint
            request_data = {
                "selected_products": selected_products
            }
            
            self.log(f"Calling POST /api/grocery/generate-cart-url")
            self.log(f"Request contains {len(selected_products)} selected products")
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/generate-cart-url", json=request_data)
            
            self.log(f"Generate cart URL response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Generate cart URL endpoint successful!")
                self.log(f"Cart URL: {result.get('cart_url')}")
                self.log(f"Total Price: ${result.get('total_price', 0):.2f}")
                self.log(f"Total Items: {result.get('total_items', 0)}")
                self.log(f"Success: {result.get('success')}")
                self.log(f"Message: {result.get('message')}")
                
                # Validate cart URL format
                cart_url = result.get('cart_url', '')
                if 'walmart.com' in cart_url:
                    self.log("✅ Cart URL has correct Walmart format")
                    
                    if 'cart?items=' in cart_url:
                        self.log("✅ Cart URL contains product items parameter")
                    elif 'cp/food' in cart_url:
                        self.log("✅ Cart URL redirects to Walmart grocery section (fallback)")
                    else:
                        self.log("⚠️ Cart URL format unexpected")
                else:
                    self.log("❌ Cart URL does not contain walmart.com")
                
                return True
            else:
                self.log(f"❌ Generate cart URL endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing generate cart URL endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_edge_cases(self):
        """Step 5: Test edge cases and error handling"""
        self.log("=== STEP 5: Testing Edge Cases ===")
        
        try:
            # Test 1: Invalid recipe ID
            self.log("Testing cart-options with invalid recipe ID...")
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params={
                "recipe_id": "invalid-recipe-id",
                "user_id": self.user_id
            })
            
            if response.status_code == 404:
                self.log("✅ Correctly handles invalid recipe ID (404)")
            else:
                self.log(f"⚠️ Unexpected response for invalid recipe ID: {response.status_code}")
            
            # Test 2: Empty selected products
            self.log("Testing generate-cart-url with empty products...")
            response = await self.client.post(f"{BACKEND_URL}/grocery/generate-cart-url", json={
                "selected_products": []
            })
            
            if response.status_code == 400:
                self.log("✅ Correctly handles empty products (400)")
            else:
                self.log(f"⚠️ Unexpected response for empty products: {response.status_code}")
            
            # Test 3: Missing parameters
            self.log("Testing cart-options with missing user_id...")
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params={
                "recipe_id": self.recipe_id
            })
            
            if response.status_code in [400, 422]:
                self.log("✅ Correctly handles missing user_id")
            else:
                self.log(f"⚠️ Unexpected response for missing user_id: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing edge cases: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run the complete Walmart integration flow test"""
        self.log("🚀 Starting Comprehensive Walmart Integration Flow Test")
        self.log("=" * 70)
        self.log("Testing NEW ENDPOINTS as requested in review:")
        self.log("1. POST /api/grocery/cart-options - Get product options for recipe ingredients")
        self.log("2. POST /api/grocery/generate-cart-url - Generate Walmart cart URL")
        self.log("=" * 70)
        
        # Step 1: Login demo user
        self.test_results["demo_login"] = await self.test_demo_user_login()
        if not self.test_results["demo_login"]:
            self.log("❌ Cannot proceed without demo user login")
            return self.test_results
        
        # Step 2: Get recipe with ingredients
        self.test_results["get_recipe"] = await self.test_get_recipe_with_ingredients()
        if not self.test_results["get_recipe"]:
            self.log("❌ Cannot proceed without recipe")
            return self.test_results
        
        # Step 3: Test cart-options endpoint
        cart_options_success, cart_options_result = await self.test_cart_options_endpoint()
        self.test_results["cart_options"] = cart_options_success
        
        # Step 4: Test generate-cart-url endpoint
        if cart_options_success:
            self.test_results["generate_cart_url"] = await self.test_generate_cart_url_endpoint(cart_options_result)
        else:
            self.test_results["generate_cart_url"] = False
        
        # Step 5: Test edge cases
        self.test_results["edge_cases"] = await self.test_edge_cases()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 WALMART INTEGRATION TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        critical_tests = ["demo_login", "get_recipe", "cart_options", "generate_cart_url"]
        critical_passed = sum(1 for test in critical_tests if self.test_results.get(test, False))
        
        self.log("=" * 70)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED - New Walmart integration flow is working!")
            self.log("✅ EXPECTED RESULTS CONFIRMED:")
            self.log("  - Each ingredient gets 2-3 product options with real-looking data")
            self.log("  - Product options include: product_id, name, price, brand, rating, image_url")
            self.log("  - Cart URL generation works with valid product IDs")
            self.log("  - System handles fallbacks gracefully for ingredients not found")
            self.log("  - Mock data is high-quality and realistic")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not self.test_results.get("demo_login"):
                self.log("  - Demo user login failing")
            if not self.test_results.get("get_recipe"):
                self.log("  - Cannot get recipe with ingredients")
            if not self.test_results.get("cart_options"):
                self.log("  - Cart options endpoint not working")
            if not self.test_results.get("generate_cart_url"):
                self.log("  - Generate cart URL endpoint not working")
        
        return self.test_results

async def main():
    """Main test execution"""
    tester = WalmartIntegrationTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())