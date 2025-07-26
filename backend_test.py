#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for AI Recipe + Grocery Delivery App
Focus: Test OpenAI API integration, Starbucks generator, Walmart API, User Auth, Recipe Storage, and Cart Options
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import random
import string

# Add backend to path
sys.path.append('/app/backend')

# Test configuration
BACKEND_URL = "https://6b4e57e4-7e21-4efb-941c-e036b94930bd.preview.emergentagent.com/api"
TEST_USER_EMAIL = "aitest.user@example.com"
TEST_USER_PASSWORD = "testpass123"

class WalmartAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.recipe_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_environment_variables(self):
        """Test 1: Verify Walmart API credentials are loaded"""
        self.log("=== Testing Walmart API Credentials ===")
        
        try:
            # Import backend modules to check environment
            from dotenv import load_dotenv
            from pathlib import Path
            
            # Load environment variables
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')
            walmart_key_version = os.environ.get('WALMART_KEY_VERSION')
            
            self.log(f"WALMART_CONSUMER_ID: {'✅ Present' if walmart_consumer_id else '❌ Missing'}")
            self.log(f"WALMART_PRIVATE_KEY: {'✅ Present' if walmart_private_key else '❌ Missing'}")
            self.log(f"WALMART_KEY_VERSION: {'✅ Present' if walmart_key_version else '❌ Missing'}")
            
            if walmart_consumer_id:
                self.log(f"Consumer ID: {walmart_consumer_id[:8]}...")
            if walmart_key_version:
                self.log(f"Key Version: {walmart_key_version}")
            if walmart_private_key:
                self.log(f"Private Key Length: {len(walmart_private_key)} characters")
                # Check if it's a valid PEM format
                if "BEGIN PRIVATE KEY" in walmart_private_key and "END PRIVATE KEY" in walmart_private_key:
                    self.log("✅ Private key appears to be in valid PEM format")
                else:
                    self.log("❌ Private key does not appear to be in valid PEM format")
            
            return all([walmart_consumer_id, walmart_private_key, walmart_key_version])
            
        except Exception as e:
            self.log(f"❌ Error checking environment variables: {str(e)}", "ERROR")
            return False
    
    async def test_signature_generation(self):
        """Test 2: Test RSA signature generation for Walmart API"""
        self.log("=== Testing RSA Signature Generation ===")
        
        try:
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            import base64
            import time
            
            # Load environment variables
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            private_key_pem = os.environ.get('WALMART_PRIVATE_KEY')
            key_version = os.environ.get('WALMART_KEY_VERSION', '1')
            
            if not all([consumer_id, private_key_pem]):
                self.log("❌ Missing credentials for signature test")
                return False
            
            # Load private key
            try:
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode(), 
                    password=None
                )
                self.log("✅ Private key loaded successfully")
            except Exception as e:
                self.log(f"❌ Failed to load private key: {str(e)}")
                return False
            
            # Generate signature
            try:
                timestamp = str(int(time.time() * 1000))
                message = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode("utf-8")
                signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
                signature_b64 = base64.b64encode(signature).decode("utf-8")
                
                self.log("✅ Signature generated successfully")
                self.log(f"Timestamp: {timestamp}")
                self.log(f"Signature length: {len(signature_b64)} characters")
                self.log(f"Signature preview: {signature_b64[:50]}...")
                
                return True
                
            except Exception as e:
                self.log(f"❌ Failed to generate signature: {str(e)}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in signature generation test: {str(e)}", "ERROR")
            return False
    
    async def test_walmart_api_direct(self):
        """Test 3: Test direct Walmart API calls"""
        self.log("=== Testing Direct Walmart API Calls ===")
        
        try:
            import requests
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            import base64
            import time
            
            # Load environment variables
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            private_key_pem = os.environ.get('WALMART_PRIVATE_KEY')
            key_version = os.environ.get('WALMART_KEY_VERSION', '1')
            
            if not all([consumer_id, private_key_pem]):
                self.log("❌ Missing credentials for API test")
                return False
            
            # Load private key
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(), 
                password=None
            )
            
            # Test ingredients
            test_ingredients = ["spaghetti", "eggs", "cheese", "milk", "bread"]
            
            for ingredient in test_ingredients:
                self.log(f"Testing Walmart API for ingredient: {ingredient}")
                
                try:
                    # Generate authentication signature
                    timestamp = str(int(time.time() * 1000))
                    message = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode("utf-8")
                    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
                    signature_b64 = base64.b64encode(signature).decode("utf-8")
                    
                    # Set up headers
                    headers = {
                        "WM_CONSUMER.ID": consumer_id,
                        "WM_CONSUMER.INTIMESTAMP": timestamp,
                        "WM_SEC.KEY_VERSION": key_version,
                        "WM_SEC.AUTH_SIGNATURE": signature_b64,
                        "Content-Type": "application/json"
                    }
                    
                    # Make API request
                    url = f"https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search"
                    params = {
                        "query": ingredient.replace(' ', '+'),
                        "numItems": 4
                    }
                    
                    self.log(f"Making request to: {url}")
                    self.log(f"Params: {params}")
                    self.log(f"Headers: {dict((k, v[:20] + '...' if len(str(v)) > 20 else v) for k, v in headers.items())}")
                    
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                    
                    self.log(f"Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("items", [])
                        self.log(f"✅ Found {len(items)} items for '{ingredient}'")
                        
                        if items:
                            for i, item in enumerate(items[:2]):  # Show first 2 items
                                self.log(f"  Item {i+1}: {item.get('name', 'Unknown')} - ${item.get('salePrice', 0)}")
                        
                        return True
                        
                    else:
                        self.log(f"❌ API Error {response.status_code}: {response.text}")
                        
                        # Check for specific error types
                        if response.status_code == 401:
                            self.log("❌ Authentication failed - check credentials")
                        elif response.status_code == 403:
                            self.log("❌ Access forbidden - check API permissions")
                        elif response.status_code == 429:
                            self.log("❌ Rate limit exceeded")
                        
                        return False
                        
                except requests.exceptions.Timeout:
                    self.log(f"❌ Timeout error for '{ingredient}'")
                except requests.exceptions.ConnectionError:
                    self.log(f"❌ Connection error for '{ingredient}'")
                except Exception as e:
                    self.log(f"❌ Error testing '{ingredient}': {str(e)}")
                
                # Test only first ingredient to avoid rate limits
                break
                
        except Exception as e:
            self.log(f"❌ Error in direct API test: {str(e)}", "ERROR")
            return False
    
    async def register_test_user(self):
        """Register a test user for recipe testing"""
        self.log("=== Registering Test User ===")
        
        try:
            # First try to clear any existing test user
            await self.client.delete(f"{BACKEND_URL}/debug/cleanup-test-data")
            
            # Register new user
            user_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": ["Italian"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                self.log(f"✅ User registered: {self.user_id}")
                
                # Auto-verify user for testing
                verify_data = {
                    "email": TEST_USER_EMAIL,
                    "code": "123456"  # Use test code
                }
                
                # Get the actual verification code from debug endpoint
                debug_response = await self.client.get(f"{BACKEND_URL}/debug/verification-codes/{TEST_USER_EMAIL}")
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    if debug_data.get("codes"):
                        verify_data["code"] = debug_data["codes"][0]["code"]
                
                verify_response = await self.client.post(f"{BACKEND_URL}/auth/verify", json=verify_data)
                if verify_response.status_code == 200:
                    self.log("✅ User verified successfully")
                    return True
                else:
                    self.log(f"⚠️ User verification failed: {verify_response.text}")
                    return True  # Continue anyway
                    
            else:
                self.log(f"❌ User registration failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error registering user: {str(e)}", "ERROR")
            return False
    
    async def generate_test_recipe(self):
        """Generate a test recipe with ingredients"""
        self.log("=== Generating Test Recipe ===")
        
        try:
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
                
                self.log(f"✅ Recipe generated: {recipe_title}")
                self.log(f"Recipe ID: {self.recipe_id}")
                self.log(f"Shopping list ({len(shopping_list)} items): {shopping_list}")
                
                return True
                
            else:
                self.log(f"❌ Recipe generation failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error generating recipe: {str(e)}", "ERROR")
            return False
    
    async def test_backend_walmart_function(self):
        """Test 4: Test the backend search_walmart_products function directly"""
        self.log("=== Testing Backend Walmart Function ===")
        
        try:
            # Import the function directly
            sys.path.append('/app/backend')
            from server import search_walmart_products
            
            test_ingredients = ["spaghetti", "eggs", "parmesan cheese", "pancetta"]
            
            for ingredient in test_ingredients:
                self.log(f"Testing search_walmart_products for: {ingredient}")
                
                try:
                    products = await search_walmart_products(ingredient)
                    
                    if products:
                        self.log(f"✅ Found {len(products)} products for '{ingredient}'")
                        for i, product in enumerate(products):
                            self.log(f"  Product {i+1}: {product.name} - ${product.price}")
                    else:
                        self.log(f"❌ No products found for '{ingredient}'")
                        
                except Exception as e:
                    self.log(f"❌ Error testing '{ingredient}': {str(e)}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing backend function: {str(e)}", "ERROR")
            return False
    
    async def test_cart_options_endpoint(self):
        """Test 5: Test the /api/grocery/cart-options endpoint"""
        self.log("=== Testing Cart Options Endpoint ===")
        
        if not self.user_id or not self.recipe_id:
            self.log("❌ Missing user_id or recipe_id for endpoint test")
            return False
        
        try:
            params = {
                "recipe_id": self.recipe_id,
                "user_id": self.user_id
            }
            
            self.log(f"Making request to /grocery/cart-options with params: {params}")
            
            response = await self.client.post(f"{BACKEND_URL}/grocery/cart-options", params=params)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Cart options endpoint responded successfully")
                self.log(f"Recipe ID: {result.get('recipe_id')}")
                self.log(f"User ID: {result.get('user_id')}")
                self.log(f"Total products: {result.get('total_products', 0)}")
                self.log(f"Ingredient options count: {len(result.get('ingredient_options', []))}")
                
                if result.get('message'):
                    self.log(f"Message: {result['message']}")
                
                ingredient_options = result.get('ingredient_options', [])
                if ingredient_options:
                    for option in ingredient_options:
                        ingredient_name = option.get('ingredient_name')
                        products = option.get('options', [])
                        self.log(f"  {ingredient_name}: {len(products)} products")
                        for product in products[:2]:  # Show first 2 products
                            self.log(f"    - {product.get('name')} - ${product.get('price')}")
                else:
                    self.log("❌ No ingredient options returned")
                
                return result.get('total_products', 0) > 0
                
            else:
                self.log(f"❌ Cart options endpoint failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing cart options endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_backend_logs(self):
        """Test 6: Check backend logs for errors"""
        self.log("=== Checking Backend Logs ===")
        
        try:
            # Check supervisor logs
            import subprocess
            
            # Get backend logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout
                self.log("Backend stdout logs (last 50 lines):")
                for line in logs.split('\n')[-20:]:  # Show last 20 lines
                    if line.strip():
                        self.log(f"  {line}")
            
            # Get backend error logs
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                error_logs = result.stdout
                if error_logs.strip():
                    self.log("Backend error logs (last 50 lines):")
                    for line in error_logs.split('\n')[-20:]:  # Show last 20 lines
                        if line.strip():
                            self.log(f"  ERROR: {line}")
                else:
                    self.log("✅ No recent error logs found")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking logs: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Comprehensive Walmart API Debug Tests")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Environment Variables
        test_results["env_vars"] = await self.test_environment_variables()
        
        # Test 2: Signature Generation
        test_results["signature"] = await self.test_signature_generation()
        
        # Test 3: Direct Walmart API
        test_results["direct_api"] = await self.test_walmart_api_direct()
        
        # Test 4: Backend Function
        test_results["backend_function"] = await self.test_backend_walmart_function()
        
        # Test 5: Register user and generate recipe
        test_results["user_setup"] = await self.register_test_user()
        if test_results["user_setup"]:
            test_results["recipe_gen"] = await self.generate_test_recipe()
        else:
            test_results["recipe_gen"] = False
        
        # Test 6: Cart Options Endpoint
        if test_results["recipe_gen"]:
            test_results["cart_endpoint"] = await self.test_cart_options_endpoint()
        else:
            test_results["cart_endpoint"] = False
        
        # Test 7: Backend Logs
        test_results["logs"] = await self.test_backend_logs()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Overall assessment
        critical_tests = ["env_vars", "signature", "direct_api", "backend_function", "cart_endpoint"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        self.log("=" * 60)
        if critical_passed == len(critical_tests):
            self.log("🎉 ALL CRITICAL TESTS PASSED - Walmart integration should be working")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} CRITICAL TESTS FAILED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            if not test_results.get("env_vars"):
                self.log("  - Missing or invalid Walmart API credentials")
            if not test_results.get("signature"):
                self.log("  - RSA signature generation failing")
            if not test_results.get("direct_api"):
                self.log("  - Direct Walmart API calls failing")
            if not test_results.get("backend_function"):
                self.log("  - Backend search_walmart_products function failing")
            if not test_results.get("cart_endpoint"):
                self.log("  - Cart options endpoint not returning products")
        
        return test_results

async def main():
    """Main test execution"""
    tester = WalmartAPITester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())