#!/usr/bin/env python3
"""
Walmart API Integration Debug Test
Testing the real Walmart API integration with provided credentials to identify RSA signature issues.

Current Status:
- Credentials are set: WALMART_CONSUMER_ID = eb0f49e9-fe3f-4c3b-8709-6c0c704c5d62
- Private key is loaded but getting "InvalidByte(1623, 61)" error 
- System is falling back to mock data with fake product IDs like "WM03125"

Test Objectives:
1. Check if the current Walmart API implementation works at all
2. Try calling `/api/debug/walmart-integration` to see credential status
3. Verify if a recipe detail endpoint gets real or mock data
4. Check if we can get any actual product IDs from Walmart
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import time
import base64

# Add backend to path for imports
sys.path.append('/app/backend')

class WalmartAPIDebugTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://d14c8dce-243d-4ebb-a34c-aee1807fadfa.preview.emergentagent.com')
        if not self.backend_url.endswith('/api'):
            self.backend_url += '/api'
        
        # Demo user credentials
        self.demo_email = "demo@test.com"
        self.demo_password = "password123"
        self.demo_user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_environment_credentials(self):
        """Test 1: Check Walmart API credentials in environment"""
        self.log("=== Testing Walmart API Credentials ===")
        
        try:
            # Load environment variables
            from dotenv import load_dotenv
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            walmart_consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            walmart_private_key = os.environ.get('WALMART_PRIVATE_KEY')
            walmart_key_version = os.environ.get('WALMART_KEY_VERSION')
            
            self.log(f"WALMART_CONSUMER_ID: {'✅ Present' if walmart_consumer_id else '❌ Missing'}")
            self.log(f"WALMART_PRIVATE_KEY: {'✅ Present' if walmart_private_key else '❌ Missing'}")
            self.log(f"WALMART_KEY_VERSION: {'✅ Present' if walmart_key_version else '❌ Missing'}")
            
            if walmart_consumer_id:
                self.log(f"Consumer ID: {walmart_consumer_id}")
                expected_id = "eb0f49e9-fe3f-4c3b-8709-6c0c704c5d62"
                if walmart_consumer_id == expected_id:
                    self.log("✅ Consumer ID matches expected value")
                else:
                    self.log(f"⚠️ Consumer ID differs from expected: {expected_id}")
            
            if walmart_private_key:
                self.log(f"Private Key Length: {len(walmart_private_key)} characters")
                # Check PEM format
                if "BEGIN PRIVATE KEY" in walmart_private_key and "END PRIVATE KEY" in walmart_private_key:
                    self.log("✅ Private key appears to be in valid PEM format")
                    
                    # Check for common formatting issues
                    lines = walmart_private_key.split('\n')
                    self.log(f"Private key has {len(lines)} lines")
                    
                    # Check for proper header/footer
                    if lines[0].strip() == "-----BEGIN PRIVATE KEY-----":
                        self.log("✅ Proper PEM header found")
                    else:
                        self.log(f"⚠️ Unexpected header: {lines[0]}")
                    
                    if lines[-1].strip() == "-----END PRIVATE KEY-----" or (len(lines) > 1 and lines[-2].strip() == "-----END PRIVATE KEY-----"):
                        self.log("✅ Proper PEM footer found")
                    else:
                        self.log(f"⚠️ Unexpected footer: {lines[-1] if lines else 'None'}")
                        
                else:
                    self.log("❌ Private key does not appear to be in valid PEM format")
            
            return all([walmart_consumer_id, walmart_private_key, walmart_key_version])
            
        except Exception as e:
            self.log(f"❌ Error checking credentials: {str(e)}", "ERROR")
            return False
    
    async def test_rsa_signature_generation(self):
        """Test 2: Test RSA signature generation to identify the InvalidByte error"""
        self.log("=== Testing RSA Signature Generation ===")
        
        try:
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from dotenv import load_dotenv
            
            # Load environment variables
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            consumer_id = os.environ.get('WALMART_CONSUMER_ID')
            private_key_pem = os.environ.get('WALMART_PRIVATE_KEY')
            key_version = os.environ.get('WALMART_KEY_VERSION', '1')
            
            if not all([consumer_id, private_key_pem]):
                self.log("❌ Missing credentials for signature test")
                return False
            
            self.log("Attempting to load private key...")
            
            try:
                # Try to load the private key
                private_key = serialization.load_pem_private_key(
                    private_key_pem.encode('utf-8'), 
                    password=None
                )
                self.log("✅ Private key loaded successfully")
                
                # Test signature generation
                timestamp = str(int(time.time() * 1000))
                message = f"{consumer_id}\n{timestamp}\n{key_version}\n".encode("utf-8")
                
                self.log(f"Generating signature for message: {message}")
                
                signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
                signature_b64 = base64.b64encode(signature).decode("utf-8")
                
                self.log("✅ Signature generated successfully")
                self.log(f"Timestamp: {timestamp}")
                self.log(f"Signature length: {len(signature_b64)} characters")
                self.log(f"Signature preview: {signature_b64[:50]}...")
                
                return True
                
            except ValueError as e:
                self.log(f"❌ ValueError loading private key: {str(e)}")
                if "InvalidByte" in str(e):
                    self.log("🔍 This is the InvalidByte error mentioned in the review!")
                    self.log("🔧 Possible causes:")
                    self.log("   - Invalid base64 encoding in PEM")
                    self.log("   - Corrupted private key data")
                    self.log("   - Wrong key format (should be PKCS#8)")
                return False
                
            except Exception as e:
                self.log(f"❌ Error loading private key: {str(e)}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in signature generation test: {str(e)}", "ERROR")
            return False
    
    async def test_debug_walmart_integration_endpoint(self):
        """Test 3: Try calling /api/debug/walmart-integration endpoint"""
        self.log("=== Testing Debug Walmart Integration Endpoint ===")
        
        try:
            response = await self.client.get(f"{self.backend_url}/debug/walmart-integration")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Debug endpoint responded successfully")
                self.log(f"Response: {json.dumps(data, indent=2)}")
                return True
            elif response.status_code == 404:
                self.log("⚠️ Debug endpoint not found - may not be implemented")
                return False
            else:
                self.log(f"❌ Debug endpoint error: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error calling debug endpoint: {str(e)}", "ERROR")
            return False
    
    async def login_demo_user(self):
        """Login with demo user to get access to protected endpoints"""
        self.log("=== Logging in Demo User ===")
        
        try:
            login_data = {
                "email": self.demo_email,
                "password": self.demo_password
            }
            
            response = await self.client.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.demo_user_id = data.get("user", {}).get("id")
                self.log(f"✅ Demo user logged in successfully")
                self.log(f"User ID: {self.demo_user_id}")
                return True
            else:
                self.log(f"❌ Demo user login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error logging in demo user: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_detail_endpoint(self):
        """Test 4: Check if recipe detail endpoint returns real or mock Walmart data"""
        self.log("=== Testing Recipe Detail Endpoint for Walmart Data ===")
        
        if not self.demo_user_id:
            self.log("❌ No demo user ID available")
            return False
        
        try:
            # First get current weekly recipes
            response = await self.client.get(f"{self.backend_url}/weekly-recipes/current/{self.demo_user_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get weekly recipes: {response.text}")
                return False
            
            data = response.json()
            if not data.get("has_plan") or not data.get("plan", {}).get("meals"):
                self.log("❌ No weekly meal plan found")
                return False
            
            # Get first recipe ID
            meals = data["plan"]["meals"]
            recipe_id = meals[0]["id"]
            recipe_name = meals[0]["name"]
            
            self.log(f"Testing recipe: {recipe_name} (ID: {recipe_id})")
            
            # Get recipe details
            response = await self.client.get(f"{self.backend_url}/weekly-recipes/recipe/{recipe_id}")
            
            if response.status_code != 200:
                self.log(f"❌ Failed to get recipe details: {response.text}")
                return False
            
            recipe_data = response.json()
            
            # Check for Walmart items
            walmart_items = recipe_data.get("walmart_items", [])
            if not walmart_items:
                self.log("❌ No walmart_items found in recipe")
                return False
            
            self.log(f"✅ Found {len(walmart_items)} Walmart items")
            
            # Analyze the product IDs to determine if they're real or mock
            mock_indicators = 0
            real_indicators = 0
            
            for i, item in enumerate(walmart_items[:3]):  # Check first 3 items
                product_name = item.get("name", "")
                search_url = item.get("search_url", "")
                estimated_price = item.get("estimated_price", "")
                
                self.log(f"  Item {i+1}: {product_name}")
                self.log(f"    URL: {search_url}")
                self.log(f"    Price: {estimated_price}")
                
                # Check for mock data indicators
                if "WM" in search_url and len(search_url.split("WM")[-1]) < 10:
                    # Short WM codes might be mock
                    mock_indicators += 1
                    self.log(f"    🔍 Possible mock indicator: Short WM code")
                
                if "Est." in estimated_price:
                    # Estimated prices might indicate mock data
                    mock_indicators += 1
                    self.log(f"    🔍 Possible mock indicator: Estimated price format")
                
                if "walmart.com/search" in search_url:
                    # Search URLs might indicate fallback to search instead of direct product
                    mock_indicators += 1
                    self.log(f"    🔍 Possible mock indicator: Search URL instead of product URL")
                
                if "walmart.com/ip/" in search_url:
                    # Direct product URLs indicate real data
                    real_indicators += 1
                    self.log(f"    ✅ Real data indicator: Direct product URL")
                
                if "$" in estimated_price and "." in estimated_price:
                    # Specific prices might indicate real data
                    real_indicators += 1
                    self.log(f"    ✅ Real data indicator: Specific price format")
            
            # Determine if data appears to be real or mock
            if mock_indicators > real_indicators:
                self.log("🚨 ANALYSIS: Data appears to be MOCK/FALLBACK")
                self.log(f"   Mock indicators: {mock_indicators}")
                self.log(f"   Real indicators: {real_indicators}")
                return False
            else:
                self.log("✅ ANALYSIS: Data appears to be REAL")
                self.log(f"   Mock indicators: {mock_indicators}")
                self.log(f"   Real indicators: {real_indicators}")
                return True
                
        except Exception as e:
            self.log(f"❌ Error testing recipe endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_direct_walmart_search(self):
        """Test 5: Try to make a direct call to search_walmart_products function"""
        self.log("=== Testing Direct Walmart Search Function ===")
        
        try:
            # Import the search function
            from server import search_walmart_products
            
            test_ingredient = "spaghetti"
            self.log(f"Testing search for: {test_ingredient}")
            
            products = await search_walmart_products(test_ingredient)
            
            if products:
                self.log(f"✅ Found {len(products)} products")
                for i, product in enumerate(products[:2]):
                    self.log(f"  Product {i+1}: {product.name} - ${product.price}")
                    self.log(f"    ID: {product.product_id}")
                    
                    # Check if product ID looks real
                    if product.product_id.startswith("WM") and len(product.product_id) > 5:
                        self.log(f"    ✅ Product ID looks real: {product.product_id}")
                    else:
                        self.log(f"    🔍 Product ID might be mock: {product.product_id}")
                
                return True
            else:
                self.log("❌ No products returned - likely falling back to mock/empty")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing direct search: {str(e)}", "ERROR")
            # Check if the error is related to RSA signature
            if "InvalidByte" in str(e):
                self.log("🚨 FOUND THE ISSUE: InvalidByte error in direct function call!")
            return False
    
    async def run_comprehensive_debug(self):
        """Run all debug tests"""
        self.log("🔍 Starting Walmart API Debug Tests")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Environment credentials
        test_results["credentials"] = await self.test_environment_credentials()
        
        # Test 2: RSA signature generation
        test_results["rsa_signature"] = await self.test_rsa_signature_generation()
        
        # Test 3: Debug endpoint
        test_results["debug_endpoint"] = await self.test_debug_walmart_integration_endpoint()
        
        # Test 4: Login demo user
        test_results["demo_login"] = await self.login_demo_user()
        
        # Test 5: Recipe detail endpoint
        if test_results["demo_login"]:
            test_results["recipe_data"] = await self.test_recipe_detail_endpoint()
        else:
            test_results["recipe_data"] = False
        
        # Test 6: Direct search function
        test_results["direct_search"] = await self.test_direct_walmart_search()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 WALMART API DEBUG RESULTS")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        # Analysis
        self.log("=" * 60)
        self.log("📊 ANALYSIS")
        self.log("=" * 60)
        
        if not test_results.get("credentials"):
            self.log("🚨 ISSUE: Walmart API credentials are missing or invalid")
        
        if not test_results.get("rsa_signature"):
            self.log("🚨 ISSUE: RSA signature generation is failing (InvalidByte error)")
            self.log("   This is likely the root cause of the problem!")
            self.log("   Recommendation: Check private key format and encoding")
        
        if not test_results.get("recipe_data"):
            self.log("🚨 ISSUE: Recipe endpoints are returning mock/fallback data")
            self.log("   This confirms the system is not getting real Walmart data")
        
        if not test_results.get("direct_search"):
            self.log("🚨 ISSUE: Direct search function is failing")
            self.log("   This confirms the backend Walmart integration is broken")
        
        # Overall assessment
        critical_tests = ["credentials", "rsa_signature", "direct_search"]
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        
        if critical_passed == len(critical_tests):
            self.log("✅ Walmart API integration appears to be working")
        else:
            self.log(f"❌ {len(critical_tests) - critical_passed} critical issues found")
            self.log("🔧 RECOMMENDED FIXES:")
            
            if not test_results.get("credentials"):
                self.log("   1. Verify Walmart API credentials are correctly set")
            
            if not test_results.get("rsa_signature"):
                self.log("   2. Fix private key format/encoding (InvalidByte error)")
                self.log("      - Check if key is properly base64 encoded")
                self.log("      - Ensure key is in PKCS#8 format")
                self.log("      - Verify no extra characters or line breaks")
            
            if not test_results.get("direct_search"):
                self.log("   3. Debug the search_walmart_products function")
        
        return test_results

async def main():
    """Main test execution"""
    tester = WalmartAPIDebugTester()
    
    try:
        results = await tester.run_comprehensive_debug()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())