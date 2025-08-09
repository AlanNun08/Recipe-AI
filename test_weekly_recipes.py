#!/usr/bin/env python3
"""
Test Weekly Recipe Generation with Mock Data Fallback
"""

import asyncio
import httpx
import json
from datetime import datetime

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

class WeeklyRecipeTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.user_id = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def setup_demo_user(self):
        """Setup demo user for testing"""
        self.log("=== Setting up Demo User ===")
        
        try:
            login_data = {
                "email": "demo@test.com",
                "password": "password123"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.user_id = result.get('user_id')
                    self.log(f"✅ Demo user logged in: {self.user_id}")
                    return True
            
            self.log(f"❌ Demo user login failed: {response.status_code}")
            return False
                
        except Exception as e:
            self.log(f"❌ Error setting up demo user: {str(e)}", "ERROR")
            return False
    
    async def test_weekly_recipe_generation(self):
        """Test weekly recipe generation (should use mock data)"""
        self.log("=== Testing Weekly Recipe Generation ===")
        
        try:
            recipe_data = {
                "user_id": self.user_id,
                "family_size": 2,
                "dietary_preferences": [],
                "budget": 100.0,
                "cuisines": ["Italian", "Asian"]
            }
            
            self.log(f"Making request with data: {json.dumps(recipe_data, indent=2)}")
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=recipe_data)
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                self.log("✅ Weekly recipe generation successful!")
                self.log(f"Plan ID: {result.get('id', 'N/A')}")
                self.log(f"Week: {result.get('week_of', 'N/A')}")
                self.log(f"Total Budget: ${result.get('total_budget', 'N/A')}")
                
                meals = result.get('meals', [])
                self.log(f"Generated {len(meals)} meals:")
                
                for i, meal in enumerate(meals):
                    self.log(f"  {i+1}. {meal.get('day', 'Unknown')}: {meal.get('name', 'Unknown')}")
                    self.log(f"     Cuisine: {meal.get('cuisine_type', 'N/A')}")
                    self.log(f"     Ingredients: {len(meal.get('ingredients', []))} items")
                
                # Check if this looks like mock data
                first_meal_name = meals[0].get('name', '') if meals else ''
                if 'Italian Pasta Primavera' in first_meal_name:
                    self.log("✅ This appears to be MOCK DATA (expected with placeholder OpenAI key)")
                    return "mock_data"
                else:
                    self.log("✅ This appears to be REAL AI-GENERATED CONTENT")
                    return "ai_generated"
                    
            elif response.status_code == 402:
                self.log("❌ Payment required - subscription needed")
                return "subscription_required"
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}")
                return "failed"
                
        except Exception as e:
            self.log(f"❌ Error in weekly recipe test: {str(e)}", "ERROR")
            return "exception"
    
    async def test_current_weekly_plan(self):
        """Test getting current weekly plan"""
        self.log("=== Testing Current Weekly Plan Retrieval ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            
            self.log(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                has_plan = result.get('has_plan', False)
                self.log(f"Has Plan: {has_plan}")
                
                if has_plan:
                    plan = result.get('plan', {})
                    meals = plan.get('meals', [])
                    self.log(f"✅ Found existing plan with {len(meals)} meals")
                    
                    for meal in meals[:3]:  # Show first 3 meals
                        self.log(f"  - {meal.get('day', 'Unknown')}: {meal.get('name', 'Unknown')}")
                    
                    return "has_plan"
                else:
                    self.log("✅ No existing plan found")
                    return "no_plan"
                    
            else:
                self.log(f"❌ Request failed: {response.status_code} - {response.text}")
                return "failed"
                
        except Exception as e:
            self.log(f"❌ Error getting current plan: {str(e)}", "ERROR")
            return "exception"
    
    async def run_test(self):
        """Run all weekly recipe tests"""
        self.log("🚀 Starting Weekly Recipe Testing")
        self.log("=" * 60)
        
        results = {}
        
        # Test 1: Setup demo user
        results["demo_user_setup"] = await self.setup_demo_user()
        
        if not results["demo_user_setup"]:
            self.log("❌ Cannot continue without demo user")
            return results
        
        # Test 2: Check current weekly plan
        results["current_plan"] = await self.test_current_weekly_plan()
        
        # Test 3: Generate weekly recipes
        results["weekly_generation"] = await self.test_weekly_recipe_generation()
        
        # Test 4: Check current plan again
        results["current_plan_after"] = await self.test_current_weekly_plan()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 WEEKLY RECIPE TEST RESULTS")
        self.log("=" * 60)
        
        if results["weekly_generation"] == "mock_data":
            self.log("🎯 CONCLUSION: Weekly recipe system is working with MOCK DATA fallback")
            self.log("    This is expected behavior when OpenAI API key is placeholder")
        elif results["weekly_generation"] == "ai_generated":
            self.log("🎯 CONCLUSION: Weekly recipe system is working with REAL AI CONTENT")
        elif results["weekly_generation"] == "subscription_required":
            self.log("🎯 CONCLUSION: Weekly recipe system requires SUBSCRIPTION")
        else:
            self.log("🎯 CONCLUSION: Weekly recipe system has ISSUES")
        
        return results

async def main():
    """Main test execution"""
    tester = WeeklyRecipeTester()
    
    try:
        results = await tester.run_test()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())