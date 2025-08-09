#!/usr/bin/env python3
"""
Recipe Generation Testing Script
Testing the current behavior of recipe generation functionality as requested in review
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import time

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BACKEND_URL = get_backend_url() + "/api"
print(f"Using backend URL: {BACKEND_URL}")

class RecipeGenerationTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_openai_api_key_status(self):
        """Test 1: Check if OpenAI API key is working via debug/health endpoint"""
        self.log("=== Testing OpenAI API Key Status ===")
        
        try:
            # Try debug/health endpoint
            response = await self.client.get(f"{BACKEND_URL}/debug/health")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Health endpoint accessible")
                
                # Check for OpenAI API key info
                openai_status = data.get('openai_api_key')
                if openai_status:
                    if 'placeholder' in str(openai_status).lower() or 'your-' in str(openai_status).lower():
                        self.log("⚠️ OpenAI API key appears to be placeholder")
                        return "placeholder"
                    else:
                        self.log("✅ OpenAI API key appears to be configured")
                        return "configured"
                else:
                    self.log("❓ OpenAI API key status not available in health endpoint")
            else:
                self.log(f"❌ Health endpoint failed: {response.status_code}")
                
            # Try alternative debug endpoint
            response = await self.client.get(f"{BACKEND_URL}/debug/environment")
            if response.status_code == 200:
                data = response.json()
                openai_key = data.get('OPENAI_API_KEY', '')
                if 'placeholder' in openai_key.lower() or 'your-' in openai_key.lower():
                    self.log("⚠️ OpenAI API key is placeholder")
                    return "placeholder"
                elif openai_key:
                    self.log("✅ OpenAI API key is configured")
                    return "configured"
                    
        except Exception as e:
            self.log(f"❌ Error checking OpenAI API key: {str(e)}", "ERROR")
            
        return "unknown"
    
    async def setup_demo_user(self):
        """Setup demo user for testing"""
        self.log("=== Setting up Demo User ===")
        
        try:
            # Try to login with demo user
            login_data = {
                "email": "demo@test.com",
                "password": "password123"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.user_id = result.get('user_id')
                    self.log(f"✅ Demo user logged in successfully: {self.user_id}")
                    return True
                else:
                    self.log(f"❌ Demo user login failed: {result}")
                    return False
            else:
                self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error setting up demo user: {str(e)}", "ERROR")
            return False
    
    async def test_recipe_generation_scenario_1(self):
        """Test Scenario 1: Chinese Snack with yogurt"""
        self.log("=== Testing Recipe Generation Scenario 1 ===")
        self.log("Parameters: Chinese cuisine, Snack, Easy difficulty, yogurt ingredient")
        
        try:
            recipe_data = {
                "user_id": "test-user-123",
                "recipe_category": "snack",
                "cuisine_type": "Chinese",
                "dietary_preferences": ["None"],
                "ingredients_on_hand": ["yogurt"],
                "prep_time_max": 30,
                "servings": 2,
                "difficulty": "easy"
            }
            
            self.log(f"Making request with data: {json.dumps(recipe_data, indent=2)}")
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Recipe generation successful!")
                self.log(f"Recipe Title: {result.get('title', 'N/A')}")
                self.log(f"Description: {result.get('description', 'N/A')[:100]}...")
                self.log(f"Cuisine Type: {result.get('cuisine_type', 'N/A')}")
                self.log(f"Difficulty: {result.get('difficulty', 'N/A')}")
                self.log(f"Prep Time: {result.get('prep_time', 'N/A')} minutes")
                self.log(f"Cook Time: {result.get('cook_time', 'N/A')} minutes")
                self.log(f"Servings: {result.get('servings', 'N/A')}")
                
                ingredients = result.get('ingredients', [])
                self.log(f"Ingredients ({len(ingredients)}): {ingredients}")
                
                instructions = result.get('instructions', [])
                self.log(f"Instructions ({len(instructions)} steps)")
                
                # Check if this looks like real AI content or mock data
                title = result.get('title', '').lower()
                description = result.get('description', '').lower()
                
                if 'mock' in title or 'test' in title or 'sample' in title:
                    self.log("⚠️ This appears to be MOCK DATA")
                    return "mock_data"
                elif 'chinese' in title or 'yogurt' in description or len(ingredients) > 3:
                    self.log("✅ This appears to be REAL AI-GENERATED CONTENT")
                    return "ai_generated"
                else:
                    self.log("❓ Content type unclear")
                    return "unclear"
                    
            elif response.status_code == 402:
                self.log("❌ Payment required - subscription needed")
                return "subscription_required"
            elif response.status_code == 500:
                error_text = response.text
                if 'openai' in error_text.lower() or 'api key' in error_text.lower():
                    self.log("❌ OpenAI API error - likely placeholder key")
                    return "openai_error"
                else:
                    self.log(f"❌ Server error: {error_text}")
                    return "server_error"
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}")
                return "request_failed"
                
        except Exception as e:
            self.log(f"❌ Error in recipe generation test: {str(e)}", "ERROR")
            return "exception"
    
    async def test_recipe_generation_scenario_2(self):
        """Test Scenario 2: Chinese Dinner with specific ingredients"""
        self.log("=== Testing Recipe Generation Scenario 2 ===")
        self.log("Parameters: Chinese cuisine, Dinner, Medium difficulty, chicken & rice")
        
        try:
            recipe_data = {
                "user_id": "test-user-123",
                "recipe_category": "cuisine",
                "cuisine_type": "Chinese",
                "dietary_preferences": ["None"],
                "ingredients_on_hand": ["chicken", "rice"],
                "prep_time_max": 45,
                "servings": 4,
                "difficulty": "medium"
            }
            
            self.log(f"Making request with data: {json.dumps(recipe_data, indent=2)}")
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Recipe generation successful!")
                self.log(f"Recipe Title: {result.get('title', 'N/A')}")
                self.log(f"Description: {result.get('description', 'N/A')[:100]}...")
                self.log(f"Cuisine Type: {result.get('cuisine_type', 'N/A')}")
                self.log(f"Difficulty: {result.get('difficulty', 'N/A')}")
                
                ingredients = result.get('ingredients', [])
                self.log(f"Ingredients ({len(ingredients)}): {ingredients}")
                
                # Check for inappropriate combinations
                title = result.get('title', '').lower()
                description = result.get('description', '').lower()
                ingredients_text = ' '.join(ingredients).lower()
                
                # Check if chicken and rice are properly used
                has_chicken = 'chicken' in ingredients_text or 'chicken' in title
                has_rice = 'rice' in ingredients_text or 'rice' in title
                is_chinese = 'chinese' in result.get('cuisine_type', '').lower()
                
                self.log(f"Analysis: Chicken={has_chicken}, Rice={has_rice}, Chinese={is_chinese}")
                
                if has_chicken and has_rice and is_chinese:
                    self.log("✅ Recipe appropriately uses requested ingredients and cuisine")
                    return "appropriate"
                else:
                    self.log("⚠️ Recipe may not properly incorporate requested parameters")
                    return "inappropriate"
                    
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}")
                return "failed"
                
        except Exception as e:
            self.log(f"❌ Error in recipe generation test: {str(e)}", "ERROR")
            return "exception"
    
    async def test_subscription_access(self):
        """Test subscription access for recipe generation"""
        self.log("=== Testing Subscription Access ===")
        
        if not self.user_id:
            self.log("❌ No user_id available for subscription test")
            return False
            
        try:
            # Check subscription status
            response = await self.client.get(f"{BACKEND_URL}/subscription/status/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Subscription status retrieved")
                self.log(f"Has Access: {result.get('has_access', False)}")
                self.log(f"Trial Active: {result.get('trial_active', False)}")
                self.log(f"Subscription Status: {result.get('subscription_status', 'N/A')}")
                
                if result.get('trial_days_left'):
                    self.log(f"Trial Days Left: {result.get('trial_days_left')}")
                    
                return result.get('has_access', False)
            else:
                self.log(f"❌ Subscription status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error checking subscription: {str(e)}", "ERROR")
            return False
    
    async def test_with_demo_user(self):
        """Test recipe generation with demo user"""
        self.log("=== Testing with Demo User ===")
        
        if not self.user_id:
            self.log("❌ Demo user not available")
            return "no_user"
            
        try:
            recipe_data = {
                "user_id": self.user_id,
                "recipe_category": "cuisine",
                "cuisine_type": "Chinese",
                "dietary_preferences": [],
                "ingredients_on_hand": ["yogurt"],
                "prep_time_max": 30,
                "servings": 2,
                "difficulty": "easy"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/recipes/generate", json=recipe_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ Recipe generation with demo user successful!")
                self.log(f"Recipe Title: {result.get('title', 'N/A')}")
                return "success"
            elif response.status_code == 402:
                self.log("❌ Demo user doesn't have access - subscription required")
                return "no_access"
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}")
                return "failed"
                
        except Exception as e:
            self.log(f"❌ Error testing with demo user: {str(e)}", "ERROR")
            return "exception"
    
    async def run_comprehensive_test(self):
        """Run all recipe generation tests"""
        self.log("🚀 Starting Recipe Generation Testing")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Check OpenAI API key status
        results["openai_status"] = await self.test_openai_api_key_status()
        
        # Test 2: Setup demo user
        results["demo_user_setup"] = await self.setup_demo_user()
        
        # Test 3: Check subscription access
        if results["demo_user_setup"]:
            results["subscription_access"] = await self.test_subscription_access()
        
        # Test 4: Recipe generation scenario 1
        results["scenario_1"] = await self.test_recipe_generation_scenario_1()
        
        # Test 5: Recipe generation scenario 2
        results["scenario_2"] = await self.test_recipe_generation_scenario_2()
        
        # Test 6: Test with demo user
        if results["demo_user_setup"]:
            results["demo_user_test"] = await self.test_with_demo_user()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 RECIPE GENERATION TEST RESULTS")
        self.log("=" * 60)
        
        # OpenAI API Key Analysis
        openai_status = results.get("openai_status", "unknown")
        if openai_status == "placeholder":
            self.log("🔑 OpenAI API Key: ⚠️ PLACEHOLDER - System will use mock data")
        elif openai_status == "configured":
            self.log("🔑 OpenAI API Key: ✅ CONFIGURED - System should generate real AI content")
        else:
            self.log("🔑 OpenAI API Key: ❓ UNKNOWN STATUS")
        
        # Recipe Generation Analysis
        scenario_1 = results.get("scenario_1", "failed")
        scenario_2 = results.get("scenario_2", "failed")
        
        if scenario_1 == "ai_generated":
            self.log("🤖 Scenario 1: ✅ REAL AI-GENERATED CONTENT")
        elif scenario_1 == "mock_data":
            self.log("🤖 Scenario 1: ⚠️ MOCK DATA FALLBACK")
        elif scenario_1 == "openai_error":
            self.log("🤖 Scenario 1: ❌ OPENAI API ERROR")
        elif scenario_1 == "subscription_required":
            self.log("🤖 Scenario 1: 💳 SUBSCRIPTION REQUIRED")
        else:
            self.log(f"🤖 Scenario 1: ❌ FAILED ({scenario_1})")
        
        if scenario_2 == "appropriate":
            self.log("🎯 Scenario 2: ✅ APPROPRIATE RECIPE GENERATED")
        elif scenario_2 == "inappropriate":
            self.log("🎯 Scenario 2: ⚠️ INAPPROPRIATE COMBINATIONS DETECTED")
        else:
            self.log(f"🎯 Scenario 2: ❌ FAILED ({scenario_2})")
        
        # Demo User Analysis
        demo_test = results.get("demo_user_test", "not_tested")
        if demo_test == "success":
            self.log("👤 Demo User: ✅ CAN GENERATE RECIPES")
        elif demo_test == "no_access":
            self.log("👤 Demo User: ❌ NO ACCESS - SUBSCRIPTION REQUIRED")
        else:
            self.log(f"👤 Demo User: ❌ FAILED ({demo_test})")
        
        # Overall Assessment
        self.log("=" * 60)
        self.log("📊 OVERALL ASSESSMENT")
        self.log("=" * 60)
        
        if openai_status == "placeholder" and scenario_1 == "mock_data":
            self.log("🔍 CONCLUSION: System is using MOCK DATA due to placeholder OpenAI API key")
        elif openai_status == "configured" and scenario_1 == "ai_generated":
            self.log("🔍 CONCLUSION: System is generating REAL AI CONTENT with working OpenAI API")
        elif scenario_1 == "subscription_required":
            self.log("🔍 CONCLUSION: System requires SUBSCRIPTION for recipe generation")
        elif scenario_1 == "openai_error":
            self.log("🔍 CONCLUSION: System has OPENAI API CONFIGURATION ISSUES")
        else:
            self.log("🔍 CONCLUSION: System behavior is UNCLEAR - needs investigation")
        
        return results

async def main():
    """Main test execution"""
    tester = RecipeGenerationTester()
    
    try:
        results = await tester.run_comprehensive_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())