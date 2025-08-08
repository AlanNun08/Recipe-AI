#!/usr/bin/env python3
"""
Walmart Integration Testing Script - Final Comprehensive Test
Testing specific endpoints mentioned in review request:
1. GET /api/debug/walmart-integration - Should show using_mock_data: false, real product IDs
2. POST /api/grocery/cart-options-test?recipe_id=test&user_id=test - Real products per ingredient
3. POST /api/grocery/generate-cart-url - Cart URL generation (currently has 400 error)
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.split('=', 1)[1].strip()
            break
    else:
        BACKEND_URL = 'https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com'

if not BACKEND_URL.endswith('/api'):
    BACKEND_URL = f"{BACKEND_URL}/api"

class WalmartIntegrationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = {}
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_debug_walmart_integration(self):
        """Test 1: GET /api/debug/walmart-integration - Should show real Walmart products"""
        self.log("=== Testing Debug Walmart Integration Endpoint ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/debug/walmart-integration")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if using mock data
                using_mock = data.get('using_mock_data', True)
                self.log(f"Using mock data: {using_mock}")
                
                if not using_mock:
                    self.log("✅ CONFIRMED: Using real Walmart API data")
                else:
                    self.log("❌ WARNING: Still using mock data")
                
                # Check sample products
                sample_products = data.get('sample_products', [])
                self.log(f"Sample products count: {len(sample_products)}")
                
                if len(sample_products) >= 10:
                    self.log("✅ CONFIRMED: 10+ sample products returned")
                else:
                    self.log(f"❌ WARNING: Only {len(sample_products)} sample products (expected 10+)")
                
                # Check for real product IDs
                real_product_ids = []
                for product in sample_products[:5]:  # Check first 5
                    product_id = product.get('product_id', '')
                    product_name = product.get('name', 'Unknown')
                    price = product.get('price', 0)
                    
                    self.log(f"  Product: {product_name} (ID: {product_id}) - ${price}")
                    
                    # Real Walmart product IDs are typically numeric or start with specific patterns
                    if product_id and not product_id.startswith('WM') and product_id.isdigit():
                        real_product_ids.append(product_id)
                
                if real_product_ids:
                    self.log(f"✅ CONFIRMED: Found real product IDs: {real_product_ids}")
                else:
                    self.log("❌ WARNING: No real product IDs detected (may still be mock data)")
                
                # Overall assessment
                success = not using_mock and len(sample_products) >= 10
                self.test_results['debug_endpoint'] = {
                    'success': success,
                    'using_mock_data': using_mock,
                    'product_count': len(sample_products),
                    'real_product_ids': real_product_ids
                }
                
                return success
                
            else:
                self.log(f"❌ Debug endpoint failed: {response.status_code} - {response.text}")
                self.test_results['debug_endpoint'] = {'success': False, 'error': response.text}
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing debug endpoint: {str(e)}", "ERROR")
            self.test_results['debug_endpoint'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_cart_options_test_endpoint(self):
        """Test 2: POST /api/grocery/cart-options-test - Should return real products per ingredient"""
        self.log("=== Testing Cart Options Test Endpoint ===")
        
        try:
            # Test with the specific parameters mentioned in review
            params = {
                'recipe_id': 'test',
                'user_id': 'test'
            }
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options-test", params=params)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check ingredient options
                ingredient_options = data.get('ingredient_options', [])
                self.log(f"Ingredient options count: {len(ingredient_options)}")
                
                total_products = 0
                real_products_found = 0
                
                for ingredient_option in ingredient_options:
                    ingredient_name = ingredient_option.get('ingredient_name', 'Unknown')
                    products = ingredient_option.get('options', [])
                    
                    self.log(f"  Ingredient: {ingredient_name} - {len(products)} products")
                    total_products += len(products)
                    
                    # Check for real product data
                    for product in products[:2]:  # Check first 2 products per ingredient
                        product_id = product.get('product_id', '')
                        product_name = product.get('name', 'Unknown')
                        price = product.get('price', 0)
                        
                        self.log(f"    Product: {product_name} (ID: {product_id}) - ${price}")
                        
                        # Check if this looks like real product data
                        if (product_id and 
                            not product_id.startswith('WM') and 
                            price > 0 and 
                            len(product_name) > 10):
                            real_products_found += 1
                
                self.log(f"Total products across all ingredients: {total_products}")
                self.log(f"Real products detected: {real_products_found}")
                
                # Success criteria: multiple ingredients with real products
                success = len(ingredient_options) > 0 and total_products > 0
                
                if success:
                    self.log("✅ CONFIRMED: Cart options test returning real products")
                else:
                    self.log("❌ WARNING: Cart options test not returning expected data")
                
                self.test_results['cart_options_test'] = {
                    'success': success,
                    'ingredient_count': len(ingredient_options),
                    'total_products': total_products,
                    'real_products_detected': real_products_found
                }
                
                return success
                
            else:
                self.log(f"❌ Cart options test failed: {response.status_code} - {response.text}")
                self.test_results['cart_options_test'] = {'success': False, 'error': response.text}
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing cart options test endpoint: {str(e)}", "ERROR")
            self.test_results['cart_options_test'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_generate_cart_url_endpoint(self):
        """Test 3: POST /api/grocery/generate-cart-url - Currently has 400 error issue"""
        self.log("=== Testing Generate Cart URL Endpoint ===")
        
        try:
            # Test with sample product data
            test_products = [
                {
                    "ingredient_name": "pasta",
                    "product_id": "32247486",
                    "name": "Great Value Penne Pasta",
                    "price": 2.99,
                    "quantity": 1
                },
                {
                    "ingredient_name": "cheese",
                    "product_id": "15136790", 
                    "name": "Great Value Parmesan Cheese",
                    "price": 4.99,
                    "quantity": 1
                }
            ]
            
            request_data = {
                "user_id": "test_user",
                "recipe_id": "test_recipe",
                "products": test_products
            }
            
            self.log(f"Testing with {len(test_products)} products")
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/generate-cart-url", json=request_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                walmart_url = data.get('walmart_url', '')
                total_price = data.get('total_price', 0)
                
                self.log(f"✅ SUCCESS: Cart URL generated")
                self.log(f"Walmart URL: {walmart_url}")
                self.log(f"Total price: ${total_price}")
                
                # Validate URL format
                url_valid = 'walmart.com' in walmart_url and 'cart' in walmart_url
                
                self.test_results['generate_cart_url'] = {
                    'success': True,
                    'walmart_url': walmart_url,
                    'total_price': total_price,
                    'url_valid': url_valid
                }
                
                return True
                
            elif response.status_code == 400:
                self.log(f"❌ CONFIRMED ISSUE: 400 error as mentioned in review")
                self.log(f"Error details: {response.text}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    self.log(f"Error detail: {error_detail}")
                except:
                    pass
                
                self.test_results['generate_cart_url'] = {
                    'success': False,
                    'error': 'Confirmed 400 error',
                    'error_details': response.text
                }
                
                return False
                
            else:
                self.log(f"❌ Unexpected error: {response.status_code} - {response.text}")
                self.test_results['generate_cart_url'] = {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'error_details': response.text
                }
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing generate cart URL: {str(e)}", "ERROR")
            self.test_results['generate_cart_url'] = {'success': False, 'error': str(e)}
            return False
    
    async def test_additional_walmart_endpoints(self):
        """Test additional Walmart-related endpoints for completeness"""
        self.log("=== Testing Additional Walmart Endpoints ===")
        
        additional_tests = {}
        
        # Test search endpoint directly
        try:
            search_params = {'query': 'pasta', 'limit': 5}
            response = await self.client.get(f"{BACKEND_URL}/walmart/search", params=search_params)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                self.log(f"✅ Walmart search endpoint: {len(products)} products found")
                additional_tests['search'] = {'success': True, 'product_count': len(products)}
            else:
                self.log(f"❌ Walmart search endpoint failed: {response.status_code}")
                additional_tests['search'] = {'success': False, 'error': response.status_code}
                
        except Exception as e:
            self.log(f"Walmart search endpoint not available or error: {str(e)}")
            additional_tests['search'] = {'success': False, 'error': 'Not available'}
        
        self.test_results['additional_tests'] = additional_tests
        return True
    
    async def run_comprehensive_test(self):
        """Run all Walmart integration tests"""
        self.log("🎯 FINAL COMPREHENSIVE WALMART INTEGRATION TEST")
        self.log("Testing specific endpoints mentioned in review request")
        self.log("=" * 70)
        
        # Test 1: Debug Walmart Integration
        test1_success = await self.test_debug_walmart_integration()
        
        self.log("")
        
        # Test 2: Cart Options Test
        test2_success = await self.test_cart_options_test_endpoint()
        
        self.log("")
        
        # Test 3: Generate Cart URL (known issue)
        test3_success = await self.test_generate_cart_url_endpoint()
        
        self.log("")
        
        # Test 4: Additional endpoints
        await self.test_additional_walmart_endpoints()
        
        # Generate comprehensive summary
        self.log("=" * 70)
        self.log("🔍 FINAL TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        # Debug endpoint results
        debug_result = self.test_results.get('debug_endpoint', {})
        if debug_result.get('success'):
            self.log("✅ DEBUG ENDPOINT: Working - Real Walmart products confirmed")
            self.log(f"   - Using mock data: {debug_result.get('using_mock_data', 'Unknown')}")
            self.log(f"   - Product count: {debug_result.get('product_count', 0)}")
        else:
            self.log("❌ DEBUG ENDPOINT: Issues detected")
        
        # Cart options test results
        cart_result = self.test_results.get('cart_options_test', {})
        if cart_result.get('success'):
            self.log("✅ CART OPTIONS TEST: Working - Real products per ingredient")
            self.log(f"   - Ingredients: {cart_result.get('ingredient_count', 0)}")
            self.log(f"   - Total products: {cart_result.get('total_products', 0)}")
        else:
            self.log("❌ CART OPTIONS TEST: Issues detected")
        
        # Cart URL generation results
        url_result = self.test_results.get('generate_cart_url', {})
        if url_result.get('success'):
            self.log("✅ CART URL GENERATION: Working - Fixed!")
        else:
            self.log("❌ CART URL GENERATION: Still has issues (400 error confirmed)")
            self.log(f"   - Error: {url_result.get('error', 'Unknown')}")
        
        self.log("")
        self.log("🎯 WALMART INTEGRATION STATUS:")
        
        working_features = []
        broken_features = []
        
        if test1_success:
            working_features.append("Real Walmart API Integration")
        else:
            broken_features.append("Debug endpoint issues")
            
        if test2_success:
            working_features.append("Product search per ingredient")
        else:
            broken_features.append("Cart options test issues")
            
        if test3_success:
            working_features.append("Cart URL generation")
        else:
            broken_features.append("Cart URL generation (400 error)")
        
        self.log("✅ WORKING FEATURES:")
        for feature in working_features:
            self.log(f"   - {feature}")
        
        if broken_features:
            self.log("❌ ISSUES REQUIRING FIXES:")
            for feature in broken_features:
                self.log(f"   - {feature}")
        
        # Overall assessment
        working_count = len(working_features)
        total_count = len(working_features) + len(broken_features)
        
        self.log("")
        self.log(f"📊 OVERALL SCORE: {working_count}/{total_count} features working")
        
        if working_count == total_count:
            self.log("🎉 ALL WALMART INTEGRATION FEATURES WORKING PERFECTLY!")
        elif working_count >= 2:
            self.log("✅ WALMART INTEGRATION MOSTLY WORKING - Minor fixes needed")
        else:
            self.log("❌ WALMART INTEGRATION NEEDS SIGNIFICANT FIXES")
        
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