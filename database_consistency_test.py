#!/usr/bin/env python3
"""
Database Consistency Investigation for Weekly Recipe System
Testing for recipe ID mismatches between weekly plans and individual recipe documents
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Any
import sys

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://f27522a1-c4ec-4127-af1d-ec55a4acb311.preview.emergentagent.com') + '/api'

# Demo user credentials
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class DatabaseConsistencyTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.user_id = None
        self.auth_token = None
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def authenticate_demo_user(self):
        """Authenticate with demo user credentials"""
        self.log("=== Authenticating Demo User ===")
        
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                self.user_id = result.get("user_id")
                self.log(f"✅ Demo user authenticated successfully")
                self.log(f"User ID: {self.user_id}")
                return True
            else:
                self.log(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Authentication error: {str(e)}", "ERROR")
            return False
    
    async def get_trial_status(self):
        """Check demo user trial status"""
        self.log("=== Checking Trial Status ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/user/trial-status/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Trial status retrieved")
                self.log(f"Has access: {result.get('has_access')}")
                self.log(f"Trial active: {result.get('trial_active')}")
                self.log(f"Days left: {result.get('trial_days_left')}")
                return result.get('has_access', False)
            else:
                self.log(f"❌ Trial status check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Trial status error: {str(e)}", "ERROR")
            return False
    
    async def generate_fresh_weekly_plan(self):
        """Generate a fresh weekly meal plan for demo user"""
        self.log("=== Generating Fresh Weekly Meal Plan ===")
        
        try:
            plan_data = {
                "user_id": self.user_id,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "budget": 100.0,
                "cuisines": ["Italian", "Mexican", "Asian"]
            }
            
            response = await self.client.post(f"{BACKEND_URL}/weekly-recipes/generate", json=plan_data)
            
            if response.status_code == 200:
                result = response.json()
                plan_id = result.get("id")
                meals = result.get("meals", [])
                
                self.log(f"✅ Weekly plan generated successfully")
                self.log(f"Plan ID: {plan_id}")
                self.log(f"Number of meals: {len(meals)}")
                
                # Log meal IDs for tracking
                for i, meal in enumerate(meals):
                    meal_id = meal.get("id")
                    meal_name = meal.get("name")
                    meal_day = meal.get("day")
                    self.log(f"  Meal {i+1} ({meal_day}): {meal_name} - ID: {meal_id}")
                
                return result
            else:
                self.log(f"❌ Weekly plan generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Weekly plan generation error: {str(e)}", "ERROR")
            return None
    
    async def get_current_weekly_plan(self):
        """Get the current weekly plan and extract meal IDs"""
        self.log("=== Getting Current Weekly Plan ===")
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/current/{self.user_id}")
            
            if response.status_code == 200:
                result = response.json()
                has_plan = result.get("has_plan", False)
                
                if has_plan:
                    plan = result.get("plan", {})
                    meals = plan.get("meals", [])
                    
                    self.log(f"✅ Current weekly plan retrieved")
                    self.log(f"Plan has {len(meals)} meals")
                    
                    meal_ids = []
                    for meal in meals:
                        meal_id = meal.get("id")
                        meal_name = meal.get("name")
                        meal_day = meal.get("day")
                        meal_ids.append({
                            "id": meal_id,
                            "name": meal_name,
                            "day": meal_day
                        })
                        self.log(f"  {meal_day}: {meal_name} (ID: {meal_id})")
                    
                    return meal_ids
                else:
                    self.log("❌ No current weekly plan found")
                    return []
            else:
                self.log(f"❌ Failed to get current plan: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log(f"❌ Get current plan error: {str(e)}", "ERROR")
            return []
    
    async def test_individual_recipe_endpoints(self, meal_ids):
        """Test each meal ID against the individual recipe endpoint"""
        self.log("=== Testing Individual Recipe Endpoints ===")
        
        consistency_results = []
        
        for meal in meal_ids:
            meal_id = meal["id"]
            meal_name = meal["name"]
            meal_day = meal["day"]
            
            self.log(f"Testing recipe endpoint for {meal_day}: {meal_name} (ID: {meal_id})")
            
            try:
                response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{meal_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    returned_name = result.get("name")
                    returned_day = result.get("day")
                    ingredients_count = len(result.get("ingredients", []))
                    walmart_items_count = len(result.get("walmart_items", []))
                    
                    self.log(f"  ✅ SUCCESS: Recipe found")
                    self.log(f"    Name: {returned_name}")
                    self.log(f"    Day: {returned_day}")
                    self.log(f"    Ingredients: {ingredients_count}")
                    self.log(f"    Walmart items: {walmart_items_count}")
                    
                    # Check for consistency
                    name_match = returned_name == meal_name
                    day_match = returned_day == meal_day
                    
                    consistency_results.append({
                        "meal_id": meal_id,
                        "meal_name": meal_name,
                        "meal_day": meal_day,
                        "endpoint_accessible": True,
                        "name_match": name_match,
                        "day_match": day_match,
                        "returned_name": returned_name,
                        "returned_day": returned_day,
                        "ingredients_count": ingredients_count,
                        "walmart_items_count": walmart_items_count
                    })
                    
                    if not name_match:
                        self.log(f"  ⚠️ NAME MISMATCH: Expected '{meal_name}', got '{returned_name}'")
                    if not day_match:
                        self.log(f"  ⚠️ DAY MISMATCH: Expected '{meal_day}', got '{returned_day}'")
                        
                elif response.status_code == 404:
                    self.log(f"  ❌ CRITICAL: Recipe not found (404)")
                    consistency_results.append({
                        "meal_id": meal_id,
                        "meal_name": meal_name,
                        "meal_day": meal_day,
                        "endpoint_accessible": False,
                        "error": "Recipe not found (404)"
                    })
                    
                else:
                    self.log(f"  ❌ ERROR: {response.status_code} - {response.text}")
                    consistency_results.append({
                        "meal_id": meal_id,
                        "meal_name": meal_name,
                        "meal_day": meal_day,
                        "endpoint_accessible": False,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                self.log(f"  ❌ EXCEPTION: {str(e)}")
                consistency_results.append({
                    "meal_id": meal_id,
                    "meal_name": meal_name,
                    "meal_day": meal_day,
                    "endpoint_accessible": False,
                    "error": f"Exception: {str(e)}"
                })
        
        return consistency_results
    
    async def investigate_database_collections(self):
        """Investigate database collections structure"""
        self.log("=== Investigating Database Collections ===")
        
        try:
            # Import database connection from backend
            sys.path.append('/app/backend')
            from server import db, weekly_recipes_collection
            
            # Count documents in weekly_recipes_collection
            weekly_count = await weekly_recipes_collection.count_documents({})
            self.log(f"Weekly recipes collection document count: {weekly_count}")
            
            # Find documents for demo user
            user_plans = await weekly_recipes_collection.find({"user_id": self.user_id}).to_list(10)
            self.log(f"Weekly plans for demo user: {len(user_plans)}")
            
            for i, plan in enumerate(user_plans):
                plan_id = plan.get("id")
                week_of = plan.get("week_of")
                meals_count = len(plan.get("meals", []))
                self.log(f"  Plan {i+1}: ID={plan_id}, Week={week_of}, Meals={meals_count}")
                
                # Check individual meal IDs in the plan
                meals = plan.get("meals", [])
                for j, meal in enumerate(meals[:3]):  # Check first 3 meals
                    meal_id = meal.get("id")
                    meal_name = meal.get("name")
                    self.log(f"    Meal {j+1}: {meal_name} (ID: {meal_id})")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Database investigation error: {str(e)}", "ERROR")
            return False
    
    async def test_specific_scenario(self):
        """Test the specific scenario: Generate → Get meal.id → Call recipe detail"""
        self.log("=== Testing Specific Scenario ===")
        
        try:
            # Step 1: Generate weekly plan
            self.log("Step 1: Generating weekly plan...")
            weekly_plan = await self.generate_fresh_weekly_plan()
            
            if not weekly_plan:
                self.log("❌ Failed to generate weekly plan")
                return False
            
            # Step 2: Get meal ID from first recipe
            meals = weekly_plan.get("meals", [])
            if not meals:
                self.log("❌ No meals in generated plan")
                return False
            
            first_meal = meals[0]
            meal_id = first_meal.get("id")
            meal_name = first_meal.get("name")
            
            self.log(f"Step 2: Got first meal ID: {meal_id} ({meal_name})")
            
            # Step 3: Call recipe detail endpoint with that exact ID
            self.log(f"Step 3: Calling recipe detail endpoint with ID: {meal_id}")
            
            response = await self.client.get(f"{BACKEND_URL}/weekly-recipes/recipe/{meal_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ SUCCESS: Recipe detail endpoint returned data")
                self.log(f"  Recipe name: {result.get('name')}")
                self.log(f"  Day: {result.get('day')}")
                self.log(f"  Ingredients: {len(result.get('ingredients', []))}")
                self.log(f"  Walmart items: {len(result.get('walmart_items', []))}")
                return True
            elif response.status_code == 404:
                self.log("❌ CRITICAL DATABASE ISSUE: Recipe detail endpoint returned 404")
                self.log("This confirms the database consistency issue!")
                return False
            else:
                self.log(f"❌ Recipe detail endpoint error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Specific scenario test error: {str(e)}", "ERROR")
            return False
    
    async def run_comprehensive_investigation(self):
        """Run comprehensive database consistency investigation"""
        self.log("🔍 Starting Database Consistency Investigation")
        self.log("=" * 70)
        
        # Step 1: Authenticate
        if not await self.authenticate_demo_user():
            self.log("❌ Cannot proceed without authentication")
            return False
        
        # Step 2: Check trial status
        if not await self.get_trial_status():
            self.log("❌ Demo user doesn't have access to premium features")
            return False
        
        # Step 3: Test specific scenario first
        self.log("\n" + "=" * 50)
        self.log("CRITICAL TEST: Generate → Get ID → Call Detail Endpoint")
        self.log("=" * 50)
        
        scenario_success = await self.test_specific_scenario()
        
        if scenario_success:
            self.log("✅ Specific scenario test PASSED - No database consistency issue detected")
        else:
            self.log("❌ Specific scenario test FAILED - Database consistency issue confirmed!")
        
        # Step 4: Detailed investigation
        self.log("\n" + "=" * 50)
        self.log("DETAILED INVESTIGATION")
        self.log("=" * 50)
        
        # Get current weekly plan
        meal_ids = await self.get_current_weekly_plan()
        
        if meal_ids:
            # Test each individual recipe endpoint
            consistency_results = await self.test_individual_recipe_endpoints(meal_ids)
            
            # Analyze results
            self.log("\n=== CONSISTENCY ANALYSIS ===")
            
            accessible_count = sum(1 for r in consistency_results if r.get("endpoint_accessible", False))
            total_count = len(consistency_results)
            
            self.log(f"Total meals tested: {total_count}")
            self.log(f"Accessible endpoints: {accessible_count}")
            self.log(f"Failed endpoints: {total_count - accessible_count}")
            
            if accessible_count == total_count:
                self.log("✅ ALL RECIPE ENDPOINTS ACCESSIBLE - No database consistency issue")
            else:
                self.log("❌ SOME RECIPE ENDPOINTS FAILED - Database consistency issue confirmed!")
                
                # Show failed endpoints
                for result in consistency_results:
                    if not result.get("endpoint_accessible", False):
                        self.log(f"  FAILED: {result['meal_day']} - {result['meal_name']} (ID: {result['meal_id']})")
                        self.log(f"    Error: {result.get('error', 'Unknown')}")
        
        # Step 5: Database investigation
        await self.investigate_database_collections()
        
        # Final summary
        self.log("\n" + "=" * 70)
        self.log("🔍 INVESTIGATION SUMMARY")
        self.log("=" * 70)
        
        if scenario_success and meal_ids and accessible_count == total_count:
            self.log("✅ NO DATABASE CONSISTENCY ISSUE DETECTED")
            self.log("The reported 'No Recipe Found' issue is likely NOT due to database problems.")
            self.log("The issue may be in frontend state management or navigation logic.")
        else:
            self.log("❌ DATABASE CONSISTENCY ISSUE CONFIRMED")
            self.log("Recipe IDs in weekly plans do not correspond to accessible recipe documents.")
            self.log("This explains why users see 'No Recipe Found' even with valid navigation.")
            
            self.log("\nRECOMMENDED FIXES:")
            self.log("1. Check weekly recipe generation logic")
            self.log("2. Verify recipe document storage in database")
            self.log("3. Ensure meal.id matches stored recipe document IDs")
            self.log("4. Review database collection relationships")
        
        return scenario_success

async def main():
    """Main investigation execution"""
    tester = DatabaseConsistencyTester()
    
    try:
        success = await tester.run_comprehensive_investigation()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    result = asyncio.run(main())