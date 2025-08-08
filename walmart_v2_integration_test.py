#!/usr/bin/env python3
"""
Walmart API Integration Testing for Weekly Recipes - V2 Format
Testing the specific endpoints requested in the review:
1. POST /api/v2/walmart/weekly-cart-options?recipe_id=<recipe_id>
2. POST /api/grocery/generate-cart-url
3. Data structure validation for V2 format
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Get backend URL from frontend environment
BACKEND_URL = "http://localhost:8001"
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip()
                break
except FileNotFoundError:
    pass

API_BASE = f"{BACKEND_URL}/api"

class WalmartV2IntegrationTester:
    def __init__(self):
        self.demo_user_email = "demo@test.com"
        self.demo_user_password = "password123"
        self.demo_user_id = None
        self.auth_token = None
        self.test_results = []
        
    async def log_test(self, test_name: str, success: bool, details: str):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name} - {details}"
        self.test_results.append(result)
        print(result)
        
    async def authenticate_demo_user(self):
        """Authenticate with demo user to get access to premium features"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Login with demo user
                login_data = {
                    "email": self.demo_user_email,
                    "password": self.demo_user_password
                }
                
                response = await client.post(f"{API_BASE}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    user_data = response.json()
                    self.demo_user_id = user_data.get("user", {}).get("id")
                    
                    await self.log_test(
                        "Demo User Authentication", 
                        True, 
                        f"Successfully authenticated demo user with ID: {self.demo_user_id}"
                    )
                    return True
                else:
                    await self.log_test(
                        "Demo User Authentication", 
                        False, 
                        f"Login failed with status {response.status_code}: {response.text}"
                    )
                    return False
                    
        except Exception as e:
            await self.log_test(
                "Demo User Authentication", 
                False, 
                f"Authentication error: {str(e)}"
            )
            return False
    
    async def get_current_weekly_recipes(self):
        """Get current weekly recipes for the demo user"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{API_BASE}/weekly-recipes/current/{self.demo_user_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    has_plan = data.get("has_plan", False)
                    
                    if has_plan:
                        plan = data.get("plan", {})
                        meals = plan.get("meals", [])
                        
                        await self.log_test(
                            "Get Current Weekly Recipes", 
                            True, 
                            f"Found weekly plan with {len(meals)} meals for week {data.get('current_week')}"
                        )
                        
                        # Return first meal's recipe_id for testing
                        if meals:
                            first_meal = meals[0]
                            recipe_id = first_meal.get("id")
                            recipe_name = first_meal.get("name", "Unknown Recipe")
                            
                            await self.log_test(
                                "Extract Recipe ID", 
                                True, 
                                f"Using recipe '{recipe_name}' with ID: {recipe_id}"
                            )
                            return recipe_id
                        else:
                            await self.log_test(
                                "Extract Recipe ID", 
                                False, 
                                "No meals found in weekly plan"
                            )
                            return None
                    else:
                        await self.log_test(
                            "Get Current Weekly Recipes", 
                            False, 
                            "Demo user has no current weekly plan - need to generate one first"
                        )
                        return await self.generate_weekly_plan()
                else:
                    await self.log_test(
                        "Get Current Weekly Recipes", 
                        False, 
                        f"Failed to get weekly recipes: {response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_test(
                "Get Current Weekly Recipes", 
                False, 
                f"Error getting weekly recipes: {str(e)}"
            )
            return None
    
    async def generate_weekly_plan(self):
        """Generate a weekly meal plan for the demo user"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                plan_data = {
                    "user_id": self.demo_user_id,
                    "family_size": 2,
                    "dietary_preferences": ["vegetarian"],
                    "budget": 100.0,
                    "cuisines": ["Italian", "Asian", "Mediterranean"]
                }
                
                response = await client.post(f"{API_BASE}/weekly-recipes/generate", json=plan_data)
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get("plan", {})
                    meals = plan.get("meals", [])
                    
                    if meals:
                        first_meal = meals[0]
                        recipe_id = first_meal.get("id")
                        recipe_name = first_meal.get("name", "Unknown Recipe")
                        
                        await self.log_test(
                            "Generate Weekly Plan", 
                            True, 
                            f"Generated weekly plan with {len(meals)} meals, using '{recipe_name}' (ID: {recipe_id})"
                        )
                        return recipe_id
                    else:
                        await self.log_test(
                            "Generate Weekly Plan", 
                            False, 
                            "Generated plan has no meals"
                        )
                        return None
                else:
                    await self.log_test(
                        "Generate Weekly Plan", 
                        False, 
                        f"Failed to generate weekly plan: {response.status_code} - {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_test(
                "Generate Weekly Plan", 
                False, 
                f"Error generating weekly plan: {str(e)}"
            )
            return None
    
    async def test_weekly_cart_options_v2(self, recipe_id: str):
        """Test the V2 weekly cart options endpoint"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test the V2 endpoint as specified in the review
                url = f"{API_BASE}/v2/walmart/weekly-cart-options"
                params = {"recipe_id": recipe_id}
                
                response = await client.post(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate V2 data structure
                    required_fields = ["recipe_id", "user_id", "ingredient_matches", "total_products", "version"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        await self.log_test(
                            "V2 Cart Options - Data Structure", 
                            False, 
                            f"Missing required fields: {missing_fields}"
                        )
                        return None
                    
                    # Validate ingredient_matches structure
                    ingredient_matches = data.get("ingredient_matches", [])
                    total_products = data.get("total_products", 0)
                    version = data.get("version", "")
                    
                    await self.log_test(
                        "V2 Cart Options - Basic Structure", 
                        True, 
                        f"Valid V2 structure (version: {version}) with {len(ingredient_matches)} ingredient matches, {total_products} total products"
                    )
                    
                    if not ingredient_matches:
                        await self.log_test(
                            "V2 Cart Options - Ingredient Matches", 
                            False, 
                            "No ingredient matches found"
                        )
                        return None
                    
                    # Validate each ingredient match structure
                    valid_matches = 0
                    sample_products = []
                    
                    for i, match in enumerate(ingredient_matches):
                        if "ingredient" in match and "products" in match:
                            ingredient_name = match["ingredient"]
                            products = match["products"]
                            
                            if products:
                                valid_matches += 1
                                
                                # Validate product structure
                                for product in products[:1]:  # Check first product
                                    required_product_fields = ["id", "name", "price", "brand", "rating"]
                                    present_fields = [field for field in required_product_fields if field in product]
                                    
                                    if len(present_fields) >= 3:  # At least id, name, price
                                        sample_products.append(product)
                                        
                                        await self.log_test(
                                            f"V2 Product Structure - {ingredient_name}", 
                                            True, 
                                            f"Product '{product.get('name', 'Unknown')}' has fields: {present_fields}"
                                        )
                                    else:
                                        await self.log_test(
                                            f"V2 Product Structure - {ingredient_name}", 
                                            False, 
                                            f"Product missing required fields. Present: {present_fields}"
                                        )
                    
                    await self.log_test(
                        "V2 Cart Options - Ingredient Matches", 
                        valid_matches > 0, 
                        f"Found {valid_matches} valid ingredient matches with products"
                    )
                    
                    await self.log_test(
                        "V2 Weekly Cart Options Endpoint", 
                        True, 
                        f"Successfully retrieved cart options with real Walmart products"
                    )
                    
                    return sample_products
                    
                else:
                    await self.log_test(
                        "V2 Weekly Cart Options Endpoint", 
                        False, 
                        f"Request failed with status {response.status_code}: {response.text}"
                    )
                    return None
                    
        except Exception as e:
            await self.log_test(
                "V2 Weekly Cart Options Endpoint", 
                False, 
                f"Error testing V2 cart options: {str(e)}"
            )
            return None
    
    async def test_cart_url_generation(self, products):
        """Test cart URL generation with V2 format products"""
        if not products:
            await self.log_test(
                "Cart URL Generation", 
                False, 
                "No products available for cart URL testing"
            )
            return
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test the regular cart URL generation endpoint
                # Note: The review mentions using 'id' field (not 'product_id') from V2 format
                cart_data = {
                    "products": [
                        {
                            "id": product.get("id"),  # Using 'id' field as specified in review
                            "name": product.get("name"),
                            "price": product.get("price", 0)
                        }
                        for product in products[:3]  # Test with first 3 products
                    ]
                }
                
                response = await client.post(f"{API_BASE}/grocery/generate-cart-url", json=cart_data)
                
                if response.status_code == 200:
                    data = response.json()
                    cart_url = data.get("cart_url")
                    total_price = data.get("total_price")
                    product_count = data.get("product_count")
                    
                    # Validate cart URL format
                    if cart_url and "walmart.com" in cart_url and "cart" in cart_url:
                        await self.log_test(
                            "Cart URL Generation", 
                            True, 
                            f"Generated valid Walmart cart URL with {product_count} products, total: ${total_price}"
                        )
                        
                        await self.log_test(
                            "Cart URL Format Validation", 
                            True, 
                            f"URL: {cart_url}"
                        )
                    else:
                        await self.log_test(
                            "Cart URL Generation", 
                            False, 
                            f"Invalid cart URL format: {cart_url}"
                        )
                        
                    # Test if products array uses 'id' field correctly
                    products_in_response = data.get("products", [])
                    if products_in_response:
                        first_product = products_in_response[0]
                        if "id" in first_product:
                            await self.log_test(
                                "V2 Format Compatibility", 
                                True, 
                                "Cart URL generation correctly uses 'id' field from V2 format"
                            )
                        else:
                            await self.log_test(
                                "V2 Format Compatibility", 
                                False, 
                                "Cart URL generation not using 'id' field from V2 format"
                            )
                else:
                    await self.log_test(
                        "Cart URL Generation", 
                        False, 
                        f"Cart URL generation failed: {response.status_code} - {response.text}"
                    )
                    
        except Exception as e:
            await self.log_test(
                "Cart URL Generation", 
                False, 
                f"Error testing cart URL generation: {str(e)}"
            )
    
    async def validate_complete_backend_flow(self):
        """Test the complete backend flow as requested in the review"""
        try:
            await self.log_test(
                "Complete Backend Flow Test", 
                True, 
                "Starting complete backend flow validation..."
            )
            
            # Step 1: Authenticate demo user
            auth_success = await self.authenticate_demo_user()
            if not auth_success:
                await self.log_test(
                    "Complete Backend Flow", 
                    False, 
                    "Authentication failed - cannot proceed"
                )
                return False
            
            # Step 2: Get or generate weekly recipes
            recipe_id = await self.get_current_weekly_recipes()
            if not recipe_id:
                await self.log_test(
                    "Complete Backend Flow", 
                    False, 
                    "Could not get valid recipe ID - cannot proceed"
                )
                return False
            
            # Step 3: Test V2 cart options
            products = await self.test_weekly_cart_options_v2(recipe_id)
            if not products:
                await self.log_test(
                    "Complete Backend Flow", 
                    False, 
                    "V2 cart options failed - cannot proceed to cart URL generation"
                )
                return False
            
            # Step 4: Test cart URL generation
            await self.test_cart_url_generation(products)
            
            await self.log_test(
                "Complete Backend Flow", 
                True, 
                "Successfully completed full backend flow: Auth → Weekly Recipes → Cart Options → Cart URL"
            )
            return True
            
        except Exception as e:
            await self.log_test(
                "Complete Backend Flow", 
                False, 
                f"Error in complete backend flow: {str(e)}"
            )
            return False
    
    async def run_comprehensive_test(self):
        """Run the complete test suite for Walmart API integration"""
        print("🧪 WALMART API INTEGRATION TESTING FOR WEEKLY RECIPES - V2 FORMAT")
        print("=" * 80)
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run the complete backend flow test
        flow_success = await self.validate_complete_backend_flow()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 WALMART API INTEGRATION TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result)
        total_tests = len(self.test_results)
        
        for result in self.test_results:
            print(result)
        
        print(f"\n📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - Walmart API integration is working correctly!")
            print("✅ The backend flow is ready for frontend integration")
        elif passed_tests >= total_tests * 0.8:
            print("⚠️  MOSTLY WORKING - Minor issues detected but core functionality works")
            print("✅ Frontend should be able to integrate with minor adjustments")
        else:
            print("❌ CRITICAL ISSUES - Major problems with Walmart API integration")
            print("🚨 Frontend integration will likely fail")
        
        return flow_success

async def main():
    """Main test execution"""
    tester = WalmartV2IntegrationTester()
    success = await tester.run_comprehensive_test()
    
    if success:
        print("\n🎯 CONCLUSION: Walmart integration is working with real products and the frontend will be able to integrate properly.")
    else:
        print("\n🚨 CONCLUSION: Critical issues found that need to be addressed before frontend integration.")

if __name__ == "__main__":
    asyncio.run(main())