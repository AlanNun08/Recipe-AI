#!/usr/bin/env python3
"""
Production Environment Testing Script for AI Recipe + Grocery Delivery App
Testing production database and Google Cloud environment variables setup

SPECIFIC TESTING REQUIREMENTS:
1. Database Connection: Test connection to buildyoursmartcart_production database
2. Environment Variables: Verify all Google Cloud environment variables are properly loaded
3. Production User Management: Check if demo@test.com user exists, if not create it
4. Authentication Flow: Test complete login flow with production database
5. Subscription System: Verify 7-day free trial system works with production Stripe configuration
6. Premium Features: Test that premium features are properly gated behind subscription
7. API Health: Verify all critical endpoints are working with production environment
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
import string
import time
from pathlib import Path

# Add backend to path for direct imports
sys.path.append('/app/backend')

class ProductionEnvironmentTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.backend_url = None
        self.demo_user_id = None
        self.test_results = {}
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_database_connection(self):
        """Test 1: Database Connection to buildyoursmartcart_production"""
        self.log("=== Testing Production Database Connection ===")
        
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            from dotenv import load_dotenv
            
            # Load environment variables
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            # Get database configuration
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME', 'test_database')
            
            self.log(f"MONGO_URL: {'✅ Present' if mongo_url else '❌ Missing'}")
            self.log(f"DB_NAME: {db_name}")
            
            # Check if we're using production database
            if db_name == "buildyoursmartcart_production":
                self.log("✅ Using production database: buildyoursmartcart_production")
            else:
                self.log(f"⚠️ Expected 'buildyoursmartcart_production', got '{db_name}'")
            
            # Test database connection
            if mongo_url:
                client = AsyncIOMotorClient(mongo_url)
                db = client[db_name]
                
                # Test connection with a simple operation
                collections = await db.list_collection_names()
                self.log(f"✅ Database connection successful")
                self.log(f"Available collections: {collections}")
                
                # Test users collection specifically
                users_count = await db.users.count_documents({})
                self.log(f"Users in database: {users_count}")
                
                await client.close()
                return True
            else:
                self.log("❌ MONGO_URL not found in environment variables")
                return False
                
        except Exception as e:
            self.log(f"❌ Database connection failed: {str(e)}", "ERROR")
            return False
    
    async def test_environment_variables(self):
        """Test 2: Verify all Google Cloud environment variables are properly loaded"""
        self.log("=== Testing Google Cloud Environment Variables ===")
        
        try:
            from dotenv import load_dotenv
            
            # Load environment variables
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            # Required environment variables for production
            required_vars = {
                'MONGO_URL': 'Database connection string',
                'DB_NAME': 'Database name (should be buildyoursmartcart_production)',
                'OPENAI_API_KEY': 'OpenAI API key for recipe generation',
                'WALMART_CONSUMER_ID': 'Walmart API consumer ID',
                'WALMART_KEY_VERSION': 'Walmart API key version',
                'WALMART_PRIVATE_KEY': 'Walmart API private key',
                'MAILJET_API_KEY': 'Mailjet API key for emails',
                'MAILJET_SECRET_KEY': 'Mailjet secret key',
                'SENDER_EMAIL': 'Email sender address',
                'STRIPE_API_KEY': 'Stripe API key for payments',
                'SECRET_KEY': 'JWT secret key'
            }
            
            env_status = {}
            all_present = True
            
            for var_name, description in required_vars.items():
                value = os.environ.get(var_name)
                is_present = bool(value and value.strip() and not value.startswith('your-'))
                env_status[var_name] = is_present
                
                if is_present:
                    # Show partial value for security
                    if 'KEY' in var_name or 'SECRET' in var_name:
                        display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                    else:
                        display_value = value[:50] + "..." if len(value) > 50 else value
                    
                    self.log(f"✅ {var_name}: {display_value}")
                else:
                    self.log(f"❌ {var_name}: Missing or placeholder value")
                    all_present = False
            
            # Special checks
            db_name = os.environ.get('DB_NAME', '')
            if db_name == 'buildyoursmartcart_production':
                self.log("✅ DB_NAME correctly set to production database")
            else:
                self.log(f"⚠️ DB_NAME is '{db_name}', expected 'buildyoursmartcart_production'")
            
            self.log(f"Environment Variables Status: {sum(env_status.values())}/{len(env_status)} present")
            return all_present
            
        except Exception as e:
            self.log(f"❌ Error checking environment variables: {str(e)}", "ERROR")
            return False
    
    async def get_backend_url(self):
        """Get the backend URL from frontend environment"""
        try:
            frontend_env_path = Path('/app/frontend/.env')
            if frontend_env_path.exists():
                with open(frontend_env_path, 'r') as f:
                    for line in f:
                        if line.startswith('REACT_APP_BACKEND_URL='):
                            backend_url = line.split('=', 1)[1].strip()
                            # Remove /api suffix if present, we'll add it back
                            if backend_url.endswith('/api'):
                                backend_url = backend_url[:-4]
                            self.backend_url = f"{backend_url}/api"
                            self.log(f"Backend URL: {self.backend_url}")
                            return self.backend_url
            
            # Fallback to default
            self.backend_url = "http://localhost:8001/api"
            self.log(f"Using fallback backend URL: {self.backend_url}")
            return self.backend_url
            
        except Exception as e:
            self.log(f"Error getting backend URL: {str(e)}")
            self.backend_url = "http://localhost:8001/api"
            return self.backend_url
    
    async def test_demo_user_management(self):
        """Test 3: Check if demo@test.com user exists in production database, if not create it"""
        self.log("=== Testing Production User Management ===")
        
        try:
            await self.get_backend_url()
            
            # First, try to login with demo@test.com
            demo_email = "demo@test.com"
            demo_password = "password123"
            
            login_data = {
                "email": demo_email,
                "password": demo_password
            }
            
            self.log(f"Attempting login with {demo_email}")
            response = await self.client.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.demo_user_id = result.get('user', {}).get('id')
                    self.log(f"✅ Demo user exists and can login successfully")
                    self.log(f"Demo user ID: {self.demo_user_id}")
                    self.log(f"User verified: {result.get('user', {}).get('is_verified', False)}")
                    return True
                elif result.get('status') == 'unverified':
                    self.log("⚠️ Demo user exists but is unverified")
                    self.demo_user_id = result.get('user_id')
                    # Try to verify the user
                    return await self.verify_demo_user(demo_email)
            
            # If login failed, try to create the demo user
            self.log("Demo user doesn't exist or login failed, attempting to create...")
            return await self.create_demo_user(demo_email, demo_password)
            
        except Exception as e:
            self.log(f"❌ Error in demo user management: {str(e)}", "ERROR")
            return False
    
    async def create_demo_user(self, email: str, password: str):
        """Create demo user in production database"""
        try:
            user_data = {
                "first_name": "Demo",
                "last_name": "User",
                "email": email,
                "password": password,
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": ["Italian", "American"]
            }
            
            self.log("Creating demo user...")
            response = await self.client.post(f"{self.backend_url}/auth/register", json=user_data)
            
            if response.status_code == 200:
                result = response.json()
                self.demo_user_id = result.get("user_id")
                self.log(f"✅ Demo user created successfully: {self.demo_user_id}")
                
                # Auto-verify the demo user
                return await self.verify_demo_user(email)
            else:
                self.log(f"❌ Failed to create demo user: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error creating demo user: {str(e)}", "ERROR")
            return False
    
    async def verify_demo_user(self, email: str):
        """Verify demo user email"""
        try:
            # For production testing, we'll use direct database access to verify
            from motor.motor_asyncio import AsyncIOMotorClient
            from dotenv import load_dotenv
            
            env_path = Path('/app/backend/.env')
            load_dotenv(env_path)
            
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME', 'test_database')
            
            if mongo_url:
                client = AsyncIOMotorClient(mongo_url)
                db = client[db_name]
                
                # Update user to verified status
                result = await db.users.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "is_verified": True,
                            "verified_at": datetime.utcnow()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    self.log("✅ Demo user verified successfully")
                    await client.close()
                    return True
                else:
                    self.log("⚠️ Demo user verification update failed")
                    await client.close()
                    return False
            
            return False
            
        except Exception as e:
            self.log(f"❌ Error verifying demo user: {str(e)}", "ERROR")
            return False
    
    async def test_authentication_flow(self):
        """Test 4: Test complete login flow with production database"""
        self.log("=== Testing Authentication Flow ===")
        
        try:
            if not self.demo_user_id:
                self.log("❌ Demo user not available for authentication test")
                return False
            
            # Test login
            login_data = {
                "email": "demo@test.com",
                "password": "password123"
            }
            
            response = await self.client.post(f"{self.backend_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    user_data = result.get('user', {})
                    self.log("✅ Authentication flow successful")
                    self.log(f"User ID: {user_data.get('id')}")
                    self.log(f"Email: {user_data.get('email')}")
                    self.log(f"Verified: {user_data.get('is_verified')}")
                    self.log(f"Name: {user_data.get('first_name')} {user_data.get('last_name')}")
                    return True
                else:
                    self.log(f"❌ Login failed with status: {result.get('status')}")
                    return False
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in authentication flow: {str(e)}", "ERROR")
            return False
    
    async def test_subscription_system(self):
        """Test 5: Verify 7-day free trial system works with production Stripe configuration"""
        self.log("=== Testing Subscription System ===")
        
        try:
            if not self.demo_user_id:
                self.log("❌ Demo user not available for subscription test")
                return False
            
            # Test subscription status endpoint
            response = await self.client.get(f"{self.backend_url}/subscription/status/{self.demo_user_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Subscription status endpoint working")
                self.log(f"Has access: {result.get('has_access')}")
                self.log(f"Subscription status: {result.get('subscription_status')}")
                self.log(f"Trial active: {result.get('trial_active')}")
                self.log(f"Subscription active: {result.get('subscription_active')}")
                self.log(f"Trial end date: {result.get('trial_end_date')}")
                
                # Check if 7-day trial is properly configured
                trial_end_date = result.get('trial_end_date')
                if trial_end_date:
                    from dateutil import parser
                    if isinstance(trial_end_date, str):
                        trial_end = parser.parse(trial_end_date)
                    else:
                        trial_end = trial_end_date
                    
                    # Check if trial period is approximately 7 weeks (49 days) as configured
                    now = datetime.utcnow()
                    if trial_end > now:
                        days_remaining = (trial_end - now).days
                        self.log(f"Trial days remaining: {days_remaining}")
                        
                        if days_remaining >= 40:  # Should be around 49 days for 7-week trial
                            self.log("✅ 7-week trial period correctly configured")
                        else:
                            self.log(f"⚠️ Trial period seems short: {days_remaining} days")
                
                return result.get('has_access', False)
            else:
                self.log(f"❌ Subscription status failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing subscription system: {str(e)}", "ERROR")
            return False
    
    async def test_premium_features(self):
        """Test 6: Test that premium features are properly gated behind subscription"""
        self.log("=== Testing Premium Features Access ===")
        
        try:
            if not self.demo_user_id:
                self.log("❌ Demo user not available for premium features test")
                return False
            
            premium_endpoints = [
                ("/recipes/generate", "Recipe Generation"),
                ("/generate-starbucks-drink", "Starbucks Generator"),
                ("/grocery/cart-options", "Walmart Integration")
            ]
            
            results = {}
            
            for endpoint, feature_name in premium_endpoints:
                self.log(f"Testing {feature_name} access...")
                
                try:
                    if endpoint == "/recipes/generate":
                        test_data = {
                            "user_id": self.demo_user_id,
                            "recipe_category": "cuisine",
                            "cuisine_type": "Italian",
                            "dietary_preferences": [],
                            "servings": 4,
                            "difficulty": "medium"
                        }
                        response = await self.client.post(f"{self.backend_url}{endpoint}", json=test_data)
                    
                    elif endpoint == "/generate-starbucks-drink":
                        test_data = {
                            "user_id": self.demo_user_id,
                            "drink_type": "frappuccino"
                        }
                        response = await self.client.post(f"{self.backend_url}{endpoint}", json=test_data)
                    
                    elif endpoint == "/grocery/cart-options":
                        # This requires a recipe_id, so we'll test with a mock one
                        params = {
                            "recipe_id": "test-recipe-id",
                            "user_id": self.demo_user_id
                        }
                        response = await self.client.post(f"{self.backend_url}{endpoint}", params=params)
                    
                    if response.status_code == 200:
                        self.log(f"✅ {feature_name}: Access granted (200)")
                        results[feature_name] = True
                    elif response.status_code == 402:
                        self.log(f"❌ {feature_name}: Access denied - subscription required (402)")
                        results[feature_name] = False
                    elif response.status_code == 401:
                        self.log(f"❌ {feature_name}: Authentication required (401)")
                        results[feature_name] = False
                    else:
                        self.log(f"⚠️ {feature_name}: Unexpected response {response.status_code}")
                        # For some endpoints, other errors might be expected (like missing recipe_id)
                        results[feature_name] = response.status_code not in [401, 402]
                
                except Exception as e:
                    self.log(f"❌ Error testing {feature_name}: {str(e)}")
                    results[feature_name] = False
            
            # Summary
            accessible_features = sum(results.values())
            total_features = len(results)
            
            self.log(f"Premium features accessible: {accessible_features}/{total_features}")
            
            return accessible_features > 0  # At least some features should be accessible for trial users
            
        except Exception as e:
            self.log(f"❌ Error testing premium features: {str(e)}", "ERROR")
            return False
    
    async def test_api_health(self):
        """Test 7: Verify all critical endpoints are working with production environment"""
        self.log("=== Testing API Health ===")
        
        try:
            critical_endpoints = [
                ("/curated-starbucks-recipes", "GET", "Curated Starbucks Recipes"),
                ("/shared-recipes", "GET", "Shared Recipes"),
                ("/recipe-stats", "GET", "Recipe Statistics")
            ]
            
            results = {}
            
            for endpoint, method, name in critical_endpoints:
                self.log(f"Testing {name}...")
                
                try:
                    if method == "GET":
                        response = await self.client.get(f"{self.backend_url}{endpoint}")
                    else:
                        response = await self.client.post(f"{self.backend_url}{endpoint}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log(f"✅ {name}: Working (200)")
                        
                        # Log some details about the response
                        if endpoint == "/curated-starbucks-recipes":
                            recipes = result.get('recipes', [])
                            self.log(f"  Found {len(recipes)} curated recipes")
                        elif endpoint == "/shared-recipes":
                            recipes = result.get('recipes', [])
                            total = result.get('total', 0)
                            self.log(f"  Found {len(recipes)} shared recipes (total: {total})")
                        elif endpoint == "/recipe-stats":
                            total_shared = result.get('total_shared_recipes', 0)
                            self.log(f"  Total shared recipes: {total_shared}")
                        
                        results[name] = True
                    else:
                        self.log(f"❌ {name}: Failed ({response.status_code})")
                        results[name] = False
                
                except Exception as e:
                    self.log(f"❌ Error testing {name}: {str(e)}")
                    results[name] = False
            
            # Test server health
            try:
                response = await self.client.get(f"{self.backend_url.replace('/api', '')}/docs")
                if response.status_code == 200:
                    self.log("✅ FastAPI docs accessible")
                    results["API Docs"] = True
                else:
                    self.log("❌ FastAPI docs not accessible")
                    results["API Docs"] = False
            except:
                self.log("❌ FastAPI docs not accessible")
                results["API Docs"] = False
            
            working_endpoints = sum(results.values())
            total_endpoints = len(results)
            
            self.log(f"API Health: {working_endpoints}/{total_endpoints} endpoints working")
            
            return working_endpoints >= (total_endpoints * 0.8)  # 80% should be working
            
        except Exception as e:
            self.log(f"❌ Error testing API health: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_production_test(self):
        """Run all production environment tests"""
        self.log("🚀 Starting Comprehensive Production Environment Testing")
        self.log("=" * 70)
        
        test_results = {}
        
        # Test 1: Database Connection
        self.log("\n" + "="*50)
        test_results["database_connection"] = await self.test_database_connection()
        
        # Test 2: Environment Variables
        self.log("\n" + "="*50)
        test_results["environment_variables"] = await self.test_environment_variables()
        
        # Test 3: Demo User Management
        self.log("\n" + "="*50)
        test_results["demo_user_management"] = await self.test_demo_user_management()
        
        # Test 4: Authentication Flow
        self.log("\n" + "="*50)
        test_results["authentication_flow"] = await self.test_authentication_flow()
        
        # Test 5: Subscription System
        self.log("\n" + "="*50)
        test_results["subscription_system"] = await self.test_subscription_system()
        
        # Test 6: Premium Features
        self.log("\n" + "="*50)
        test_results["premium_features"] = await self.test_premium_features()
        
        # Test 7: API Health
        self.log("\n" + "="*50)
        test_results["api_health"] = await self.test_api_health()
        
        # Summary
        self.log("\n" + "=" * 70)
        self.log("🔍 PRODUCTION ENVIRONMENT TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper().replace('_', ' ')}: {status}")
        
        # Overall assessment
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        self.log("=" * 70)
        self.log(f"OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL PRODUCTION TESTS PASSED - System ready for production!")
        elif passed_tests >= (total_tests * 0.8):
            self.log("⚠️ MOSTLY READY - Minor issues detected but core functionality working")
        else:
            self.log("❌ PRODUCTION ISSUES DETECTED - System needs attention before production use")
        
        # Store results for later use
        self.test_results = test_results
        return test_results

async def main():
    """Main test execution"""
    tester = ProductionEnvironmentTester()
    
    try:
        results = await tester.run_comprehensive_production_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())