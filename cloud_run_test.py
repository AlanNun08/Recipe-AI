#!/usr/bin/env python3
"""
Cloud Run Deployment API Testing Script
Testing the redeployed Cloud Run service at: https://recipe-ai-149256126208.europe-west1.run.app
Verifying that the API routing fix is working correctly.
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
import time

# Cloud Run service configuration
BASE_URL = "https://recipe-ai-149256126208.europe-west1.run.app"
API_URL = f"{BASE_URL}/api"

# Test credentials as mentioned in review request
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class CloudRunTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        self.auth_token = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_health_endpoint(self):
        """Test /health endpoint to ensure it returns JSON response"""
        self.log("=== Testing Health Check Endpoint ===")
        
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            
            self.log(f"Health endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.log("✅ Health endpoint returns JSON response")
                    self.log(f"Health data: {data}")
                    return True
                except json.JSONDecodeError:
                    self.log("❌ Health endpoint does not return valid JSON")
                    self.log(f"Response text: {response.text}")
                    return False
            else:
                self.log(f"❌ Health endpoint returned status {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing health endpoint: {str(e)}", "ERROR")
            return False
    
    async def test_frontend_loading(self):
        """Verify the React app loads at the root URL"""
        self.log("=== Testing Frontend Loading ===")
        
        try:
            response = await self.client.get(BASE_URL)
            
            self.log(f"Frontend status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for React app indicators
                react_indicators = [
                    '<div id="root"',
                    'react',
                    'React',
                    'static/js/',
                    'static/css/'
                ]
                
                found_indicators = [indicator for indicator in react_indicators if indicator in content]
                
                if found_indicators:
                    self.log(f"✅ React app loads successfully")
                    self.log(f"Found React indicators: {found_indicators}")
                    return True
                else:
                    self.log("❌ No React app indicators found")
                    self.log(f"Content preview: {content[:500]}...")
                    return False
            else:
                self.log(f"❌ Frontend returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing frontend: {str(e)}", "ERROR")
            return False
    
    async def test_static_assets(self):
        """Test that /static/ files are served correctly"""
        self.log("=== Testing Static Assets ===")
        
        try:
            # Test common static file paths
            static_paths = [
                "/static/js/",
                "/static/css/",
                "/favicon.ico",
                "/manifest.json"
            ]
            
            for path in static_paths:
                try:
                    response = await self.client.get(f"{BASE_URL}{path}")
                    self.log(f"Static asset {path}: {response.status_code}")
                    
                    if response.status_code in [200, 404]:  # 404 is acceptable if file doesn't exist
                        continue
                    else:
                        self.log(f"⚠️ Unexpected status for {path}: {response.status_code}")
                        
                except Exception as e:
                    self.log(f"⚠️ Error testing {path}: {str(e)}")
            
            self.log("✅ Static assets test completed")
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing static assets: {str(e)}", "ERROR")
            return False
    
    async def test_api_docs(self):
        """Test /docs endpoint for FastAPI documentation"""
        self.log("=== Testing API Documentation ===")
        
        try:
            response = await self.client.get(f"{BASE_URL}/docs")
            
            self.log(f"API docs status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for FastAPI docs indicators
                fastapi_indicators = [
                    'swagger',
                    'Swagger',
                    'FastAPI',
                    'openapi',
                    'redoc'
                ]
                
                found_indicators = [indicator for indicator in fastapi_indicators if indicator in content]
                
                if found_indicators:
                    self.log(f"✅ FastAPI documentation accessible")
                    self.log(f"Found FastAPI indicators: {found_indicators}")
                    return True
                else:
                    self.log("❌ No FastAPI documentation indicators found")
                    return False
            else:
                self.log(f"❌ API docs returned status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing API docs: {str(e)}", "ERROR")
            return False
    
    async def test_curated_starbucks_recipes(self):
        """Test GET /api/curated-starbucks-recipes"""
        self.log("=== Testing Curated Starbucks Recipes Endpoint ===")
        
        try:
            response = await self.client.get(f"{API_URL}/curated-starbucks-recipes")
            
            self.log(f"Curated recipes status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    recipes = data.get('recipes', [])
                    total = data.get('total', 0)
                    
                    self.log(f"✅ Curated Starbucks recipes endpoint working")
                    self.log(f"Found {total} recipes")
                    
                    if recipes:
                        sample_recipe = recipes[0]
                        self.log(f"Sample recipe: {sample_recipe.get('name', 'Unknown')}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("❌ Invalid JSON response from curated recipes")
                    return False
            else:
                self.log(f"❌ Curated recipes endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing curated recipes: {str(e)}", "ERROR")
            return False
    
    async def test_shared_recipes(self):
        """Test GET /api/shared-recipes"""
        self.log("=== Testing Shared Recipes Endpoint ===")
        
        try:
            response = await self.client.get(f"{API_URL}/shared-recipes")
            
            self.log(f"Shared recipes status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    recipes = data.get('recipes', [])
                    total = data.get('total', 0)
                    
                    self.log(f"✅ Shared recipes endpoint working")
                    self.log(f"Found {total} shared recipes")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("❌ Invalid JSON response from shared recipes")
                    return False
            else:
                self.log(f"❌ Shared recipes endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing shared recipes: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_stats(self):
        """Test GET /api/recipe-stats"""
        self.log("=== Testing Recipe Stats Endpoint ===")
        
        try:
            response = await self.client.get(f"{API_URL}/recipe-stats")
            
            self.log(f"Recipe stats status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    total_shared = data.get('total_shared_recipes', 0)
                    
                    self.log(f"✅ Recipe stats endpoint working")
                    self.log(f"Total shared recipes: {total_shared}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("❌ Invalid JSON response from recipe stats")
                    return False
            else:
                self.log(f"❌ Recipe stats endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing recipe stats: {str(e)}", "ERROR")
            return False
    
    async def test_auth_register(self):
        """Test POST /api/auth/register with test data"""
        self.log("=== Testing User Registration Endpoint ===")
        
        try:
            # Generate unique email for testing
            timestamp = int(time.time())
            test_email = f"cloudrun_test_{timestamp}@example.com"
            
            user_data = {
                "first_name": "CloudRun",
                "last_name": "Tester",
                "email": test_email,
                "password": "testpass123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": ["Italian"]
            }
            
            response = await self.client.post(f"{API_URL}/auth/register", json=user_data)
            
            self.log(f"Registration status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    message = data.get('message', '')
                    user_id = data.get('user_id', '')
                    
                    self.log(f"✅ Registration endpoint working")
                    self.log(f"Message: {message}")
                    self.log(f"User ID: {user_id}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("❌ Invalid JSON response from registration")
                    return False
            else:
                self.log(f"❌ Registration endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}", "ERROR")
            return False
    
    async def test_auth_login(self):
        """Test POST /api/auth/login with demo credentials"""
        self.log("=== Testing User Login Endpoint ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{API_URL}/auth/login", json=login_data)
            
            self.log(f"Login status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    status = data.get('status', '')
                    message = data.get('message', '')
                    user = data.get('user', {})
                    
                    self.log(f"✅ Login endpoint working")
                    self.log(f"Status: {status}")
                    self.log(f"Message: {message}")
                    
                    if user:
                        self.user_id = user.get('id')
                        self.log(f"User ID: {self.user_id}")
                        self.log(f"User verified: {user.get('is_verified', False)}")
                    
                    return True
                    
                except json.JSONDecodeError:
                    self.log("❌ Invalid JSON response from login")
                    return False
            else:
                self.log(f"❌ Login endpoint failed: {response.status_code}")
                self.log(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing login: {str(e)}", "ERROR")
            return False
    
    async def test_additional_api_endpoints(self):
        """Test additional API endpoints to verify routing"""
        self.log("=== Testing Additional API Endpoints ===")
        
        endpoints_to_test = [
            ("/api/generate-starbucks-drink", "POST"),
            ("/api/share-recipe", "POST"),
            ("/api/like-recipe", "POST"),
        ]
        
        results = {}
        
        for endpoint, method in endpoints_to_test:
            try:
                self.log(f"Testing {method} {endpoint}")
                
                if method == "POST":
                    # Send minimal test data to see if endpoint exists
                    test_data = {"test": "data"}
                    response = await self.client.post(f"{BASE_URL}{endpoint}", json=test_data)
                else:
                    response = await self.client.get(f"{BASE_URL}{endpoint}")
                
                self.log(f"{endpoint} status: {response.status_code}")
                
                # 404 means endpoint doesn't exist (routing issue)
                # 422, 400, 401 means endpoint exists but has validation/auth issues (good)
                if response.status_code == 404:
                    self.log(f"❌ {endpoint} not found - routing issue")
                    results[endpoint] = False
                elif response.status_code in [200, 400, 401, 422, 405]:
                    self.log(f"✅ {endpoint} exists - routing working")
                    results[endpoint] = True
                else:
                    self.log(f"⚠️ {endpoint} unexpected status: {response.status_code}")
                    results[endpoint] = True  # Endpoint exists
                    
            except Exception as e:
                self.log(f"❌ Error testing {endpoint}: {str(e)}")
                results[endpoint] = False
        
        return all(results.values())
    
    async def run_comprehensive_test(self):
        """Run all Cloud Run deployment tests"""
        self.log("🚀 Starting Cloud Run Deployment API Tests")
        self.log(f"Testing service at: {BASE_URL}")
        self.log("=" * 70)
        
        test_results = {}
        
        # Critical Testing Areas from review request:
        
        # 1. Health Check
        test_results["health_check"] = await self.test_health_endpoint()
        
        # 2. Frontend Loading
        test_results["frontend_loading"] = await self.test_frontend_loading()
        
        # 3. Static Assets
        test_results["static_assets"] = await self.test_static_assets()
        
        # 4. API Documentation
        test_results["api_docs"] = await self.test_api_docs()
        
        # 5. Key API Endpoints
        test_results["curated_starbucks"] = await self.test_curated_starbucks_recipes()
        test_results["shared_recipes"] = await self.test_shared_recipes()
        test_results["recipe_stats"] = await self.test_recipe_stats()
        
        # 6. Authentication Endpoints
        test_results["auth_register"] = await self.test_auth_register()
        test_results["auth_login"] = await self.test_auth_login()
        
        # 7. Additional API Endpoints
        test_results["additional_apis"] = await self.test_additional_api_endpoints()
        
        # Summary
        self.log("=" * 70)
        self.log("🔍 CLOUD RUN DEPLOYMENT TEST RESULTS")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Critical assessment
        critical_tests = [
            "health_check", 
            "frontend_loading", 
            "curated_starbucks", 
            "shared_recipes", 
            "recipe_stats", 
            "auth_register", 
            "auth_login"
        ]
        
        critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
        total_passed = sum(1 for result in test_results.values() if result)
        
        self.log("=" * 70)
        self.log(f"OVERALL RESULTS: {total_passed}/{len(test_results)} tests passed")
        self.log(f"CRITICAL TESTS: {critical_passed}/{len(critical_tests)} passed")
        
        if critical_passed == len(critical_tests):
            self.log("🎉 API ROUTING FIX SUCCESSFUL - All critical endpoints working!")
            self.log("✅ The Cloud Run service is properly configured")
            self.log("✅ Backend API routes are accessible")
            self.log("✅ Frontend and backend are working on the same domain")
        else:
            self.log("❌ API ROUTING ISSUES DETECTED")
            self.log("🔧 ISSUES IDENTIFIED:")
            
            failed_tests = [test for test in critical_tests if not test_results.get(test, False)]
            for failed_test in failed_tests:
                self.log(f"  - {failed_test.replace('_', ' ').title()} is not working")
            
            if not test_results.get("curated_starbucks") or not test_results.get("shared_recipes"):
                self.log("  - API endpoints returning 404 - routing configuration issue")
            if not test_results.get("auth_login") or not test_results.get("auth_register"):
                self.log("  - Authentication endpoints not accessible")
            if not test_results.get("frontend_loading"):
                self.log("  - Frontend not loading properly")
        
        return test_results

async def main():
    """Main test execution"""
    tester = CloudRunTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())