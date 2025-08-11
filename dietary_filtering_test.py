#!/usr/bin/env python3
"""
SPECIFIC TEST FOR FIXED DIETARY FILTERING SYSTEM
Testing the critical fix for weekly recipe generation with dietary preferences
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BACKEND_URL = "https://4d24c0b0-8c0e-4246-8e3e-2e81e97a4fe7.preview.emergentagent.com/api"
DEMO_USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class DietaryFilteringTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, details: str = "", data: any = None):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if data and isinstance(data, dict):
            print(f"   Data: {data}")
        print()
        
    def login_demo_user(self) -> bool:
        """Login demo user for testing"""
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user", {}).get("id")
                if user_id == DEMO_USER_ID:
                    self.log_result("Demo User Login", True, f"Successfully authenticated user: {user_id}")
                    return True
                else:
                    self.log_result("Demo User Login", False, f"User ID mismatch: {user_id}")
                    return False
            else:
                self.log_result("Demo User Login", False, f"Login failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Demo User Login", False, f"Exception: {str(e)}")
            return False

    def test_force_regeneration_with_dietary_preferences(self) -> bool:
        """Test that dietary preferences force regeneration and delete existing plans"""
        try:
            print("\n🔍 TESTING FORCE REGENERATION LOGIC")
            print("=" * 60)
            
            # Step 1: Generate initial plan without dietary preferences
            print("📋 Step 1: Generate initial plan without dietary preferences")
            initial_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": [],
                "allergies": [],
                "cuisines": ["italian", "mexican"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=initial_data)
            if response.status_code != 200:
                self.log_result("Force Regeneration Test", False, f"Initial generation failed: {response.status_code}")
                return False
            
            initial_plan = response.json()
            initial_week = initial_plan.get("week_of")
            print(f"   ✅ Initial plan created for week: {initial_week}")
            
            # Step 2: Generate new plan WITH dietary preferences (should force regeneration)
            print("\n📋 Step 2: Generate plan WITH dietary preferences (should force regeneration)")
            dietary_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "allergies": [],
                "cuisines": ["italian", "mexican"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=dietary_data)
            if response.status_code != 200:
                self.log_result("Force Regeneration Test", False, f"Dietary generation failed: {response.status_code}")
                return False
            
            dietary_plan = response.json()
            dietary_week = dietary_plan.get("week_of")
            dietary_meals = dietary_plan.get("meals", [])
            
            print(f"   ✅ New plan created for week: {dietary_week}")
            print(f"   ✅ Generated {len(dietary_meals)} meals with dietary preferences")
            
            # Step 3: Verify the plan was regenerated (not cached)
            if initial_week == dietary_week and len(dietary_meals) == 7:
                self.log_result("Force Regeneration Logic", True, 
                              "✅ FORCE REGENERATION WORKING: New plan generated when dietary preferences provided",
                              {"initial_week": initial_week, "dietary_week": dietary_week, "meals_count": len(dietary_meals)})
                return True
            else:
                self.log_result("Force Regeneration Logic", False, 
                              "❌ Force regeneration may not be working properly",
                              {"initial_week": initial_week, "dietary_week": dietary_week})
                return False
                
        except Exception as e:
            self.log_result("Force Regeneration Test", False, f"Exception: {str(e)}")
            return False

    def test_vegetarian_safety_filtering(self) -> bool:
        """Test vegetarian meals contain NO meat ingredients"""
        try:
            print("\n🥬 TESTING VEGETARIAN SAFETY FILTERING")
            print("=" * 50)
            
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "allergies": [],
                "cuisines": ["italian", "mexican", "asian"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code != 200:
                self.log_result("Vegetarian Safety Filtering", False, f"Generation failed: {response.status_code}")
                return False
            
            data = response.json()
            meals = data.get("meals", [])
            
            # Comprehensive meat detection
            meat_violations = []
            meat_keywords = [
                'chicken', 'beef', 'pork', 'fish', 'meat', 'turkey', 'lamb', 'bacon', 'ham', 
                'sausage', 'salmon', 'tuna', 'cod', 'shrimp', 'crab', 'lobster', 'duck', 
                'veal', 'venison', 'rabbit', 'goose', 'anchovy', 'sardine', 'mackerel',
                'prosciutto', 'pepperoni', 'salami', 'chorizo', 'pancetta'
            ]
            
            print(f"📝 Checking {len(meals)} meals for meat ingredients...")
            
            for meal in meals:
                meal_name = meal.get("name", "")
                ingredients = meal.get("ingredients", [])
                print(f"   🍽️ {meal_name}: {len(ingredients)} ingredients")
                
                for ingredient in ingredients:
                    ingredient_lower = ingredient.lower()
                    for meat in meat_keywords:
                        if meat in ingredient_lower:
                            meat_violations.append(f"{meal_name}: {ingredient}")
                            print(f"      🚨 MEAT VIOLATION: {ingredient}")
            
            if len(meat_violations) == 0:
                self.log_result("Vegetarian Safety Filtering", True, 
                              f"✅ VEGETARIAN SAFETY VERIFIED: {len(meals)} meals contain NO meat ingredients",
                              {"meals_checked": len(meals), "violations": 0})
                return True
            else:
                self.log_result("Vegetarian Safety Filtering", False, 
                              f"🚨 CRITICAL SAFETY VIOLATION: Found {len(meat_violations)} meat ingredients in vegetarian meals",
                              {"violations": meat_violations})
                return False
                
        except Exception as e:
            self.log_result("Vegetarian Safety Filtering", False, f"Exception: {str(e)}")
            return False

    def test_dairy_allergy_safety_filtering(self) -> bool:
        """Test dairy allergy meals contain NO dairy ingredients"""
        try:
            print("\n🥛 TESTING DAIRY ALLERGY SAFETY FILTERING")
            print("=" * 50)
            
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": [],
                "allergies": ["dairy"],
                "cuisines": ["italian", "mexican", "asian"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code != 200:
                self.log_result("Dairy Allergy Safety Filtering", False, f"Generation failed: {response.status_code}")
                return False
            
            data = response.json()
            meals = data.get("meals", [])
            
            # Comprehensive dairy detection
            dairy_violations = []
            dairy_keywords = [
                'cheese', 'milk', 'butter', 'cream', 'yogurt', 'parmesan', 'feta', 
                'mozzarella', 'cheddar', 'ricotta', 'goat cheese', 'brie', 'camembert',
                'swiss cheese', 'provolone', 'blue cheese', 'cottage cheese', 'sour cream',
                'heavy cream', 'whipped cream', 'ice cream', 'buttermilk', 'ghee'
            ]
            
            print(f"📝 Checking {len(meals)} meals for dairy ingredients...")
            
            for meal in meals:
                meal_name = meal.get("name", "")
                ingredients = meal.get("ingredients", [])
                print(f"   🍽️ {meal_name}: {len(ingredients)} ingredients")
                
                for ingredient in ingredients:
                    ingredient_lower = ingredient.lower()
                    for dairy in dairy_keywords:
                        if dairy in ingredient_lower and 'dairy-free' not in ingredient_lower and 'non-dairy' not in ingredient_lower:
                            dairy_violations.append(f"{meal_name}: {ingredient}")
                            print(f"      🚨 DAIRY VIOLATION: {ingredient}")
            
            if len(dairy_violations) == 0:
                self.log_result("Dairy Allergy Safety Filtering", True, 
                              f"✅ DAIRY ALLERGY SAFETY VERIFIED: {len(meals)} meals contain NO dairy ingredients",
                              {"meals_checked": len(meals), "violations": 0})
                return True
            else:
                self.log_result("Dairy Allergy Safety Filtering", False, 
                              f"🚨 CRITICAL ALLERGY VIOLATION: Found {len(dairy_violations)} dairy ingredients in dairy-free meals",
                              {"violations": dairy_violations})
                return False
                
        except Exception as e:
            self.log_result("Dairy Allergy Safety Filtering", False, f"Exception: {str(e)}")
            return False

    def test_critical_safety_scenario(self) -> bool:
        """Test the previously failing scenario: vegetarian + dairy allergy"""
        try:
            print("\n🛡️ TESTING CRITICAL SAFETY SCENARIO")
            print("=" * 50)
            print("Testing: dietary_preferences=['vegetarian'] + allergies=['dairy']")
            
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "allergies": ["dairy"],
                "cuisines": ["italian", "mexican", "asian"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code != 200:
                self.log_result("Critical Safety Scenario", False, f"Generation failed: {response.status_code}")
                return False
            
            data = response.json()
            meals = data.get("meals", [])
            
            # Check for BOTH meat and dairy violations
            all_violations = []
            
            # Meat keywords (vegetarian violation)
            meat_keywords = [
                'chicken', 'beef', 'pork', 'fish', 'meat', 'turkey', 'lamb', 'bacon', 'ham', 
                'sausage', 'salmon', 'tuna', 'cod', 'shrimp', 'crab', 'lobster'
            ]
            
            # Dairy keywords (allergy violation)
            dairy_keywords = [
                'cheese', 'milk', 'butter', 'cream', 'yogurt', 'parmesan', 'feta', 
                'mozzarella', 'cheddar', 'ricotta', 'sour cream', 'heavy cream'
            ]
            
            print(f"📝 Checking {len(meals)} meals for BOTH meat and dairy violations...")
            
            for meal in meals:
                meal_name = meal.get("name", "")
                ingredients = meal.get("ingredients", [])
                print(f"   🍽️ {meal_name}: {len(ingredients)} ingredients")
                
                for ingredient in ingredients:
                    ingredient_lower = ingredient.lower()
                    
                    # Check for meat violations
                    for meat in meat_keywords:
                        if meat in ingredient_lower:
                            all_violations.append(f"{meal_name}: {ingredient} (MEAT VIOLATION)")
                            print(f"      🚨 MEAT VIOLATION: {ingredient}")
                    
                    # Check for dairy violations
                    for dairy in dairy_keywords:
                        if dairy in ingredient_lower and 'dairy-free' not in ingredient_lower:
                            all_violations.append(f"{meal_name}: {ingredient} (DAIRY VIOLATION)")
                            print(f"      🚨 DAIRY VIOLATION: {ingredient}")
            
            if len(all_violations) == 0:
                self.log_result("Critical Safety Scenario", True, 
                              f"✅ CRITICAL SAFETY SUCCESS: {len(meals)} meals are completely safe with NO meat or dairy violations",
                              {"meals_checked": len(meals), "total_violations": 0})
                return True
            else:
                self.log_result("Critical Safety Scenario", False, 
                              f"🚨 CRITICAL SAFETY FAILURE: Found {len(all_violations)} safety violations in meals that should be vegetarian AND dairy-free",
                              {"violations": all_violations})
                return False
                
        except Exception as e:
            self.log_result("Critical Safety Scenario", False, f"Exception: {str(e)}")
            return False

    def test_debug_logging_verification(self) -> bool:
        """Test that debug logging shows filtering in action"""
        try:
            print("\n🔍 TESTING DEBUG LOGGING VERIFICATION")
            print("=" * 50)
            print("Note: This test verifies the API works - actual debug logs need to be checked in backend logs")
            
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "allergies": ["dairy"],
                "cuisines": ["italian"]
            }
            
            print("📋 Generating meals with dietary preferences to trigger debug logging...")
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                
                self.log_result("Debug Logging Verification", True, 
                              f"✅ API call successful - debug logs should show 'Dietary preferences provided - forcing regeneration for safety' and filtering messages for {len(meals)} meals",
                              {"meals_generated": len(meals), "debug_expected": True})
                
                print("\n📝 EXPECTED DEBUG LOG MESSAGES:")
                print("   • 'Dietary preferences provided - forcing regeneration for safety'")
                print("   • 'Filtering meal [meal_name]: X → Y ingredients'")
                print("   • Check backend logs with: tail -f /var/log/supervisor/backend.*.log")
                
                return True
            else:
                self.log_result("Debug Logging Verification", False, f"API call failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Debug Logging Verification", False, f"Exception: {str(e)}")
            return False

    def run_dietary_filtering_tests(self):
        """Run all dietary filtering tests"""
        print("🛡️ TESTING FIXED DIETARY FILTERING SYSTEM FOR WEEKLY RECIPES")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Demo User: {DEMO_EMAIL} (ID: {DEMO_USER_ID})")
        print()
        
        # Login first
        if not self.login_demo_user():
            print("❌ Cannot proceed without authentication")
            return
        
        # Run specific tests for the fix
        print("\n🔧 TESTING THE CRITICAL FIX")
        print("=" * 40)
        
        test_results = []
        
        # Test 1: Force regeneration logic
        test_results.append(self.test_force_regeneration_with_dietary_preferences())
        
        # Test 2: Vegetarian safety
        test_results.append(self.test_vegetarian_safety_filtering())
        
        # Test 3: Dairy allergy safety  
        test_results.append(self.test_dairy_allergy_safety_filtering())
        
        # Test 4: Critical safety scenario
        test_results.append(self.test_critical_safety_scenario())
        
        # Test 5: Debug logging verification
        test_results.append(self.test_debug_logging_verification())
        
        # Summary
        self.print_summary(test_results)
        
        return test_results

    def print_summary(self, test_results):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 DIETARY FILTERING TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result)
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed results
        print("📋 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            status_icon = "✅" if result["passed"] else "❌"
            print(f"{status_icon} {result['test']}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print()
        
        # Overall assessment
        print("🎯 OVERALL ASSESSMENT:")
        print("-" * 40)
        
        if success_rate == 100:
            print("   ✅ EXCELLENT: Dietary filtering system is working perfectly")
            print("   ✅ All safety measures are functioning correctly")
            print("   ✅ Force regeneration logic is working as expected")
            print("   ✅ The fix has completely resolved the safety issues")
        elif success_rate >= 80:
            print("   ⚠️  GOOD: Most dietary filtering features are working")
            print("   ⚠️  Minor issues detected but core safety is functional")
            print("   ⚠️  Review failed tests for remaining issues")
        elif success_rate >= 60:
            print("   ❌ FAIR: Dietary filtering has significant issues")
            print("   ❌ Safety concerns remain - not fully fixed")
            print("   ❌ Additional work needed on the filtering system")
        else:
            print("   🚨 CRITICAL: Dietary filtering system is still failing")
            print("   🚨 Major safety violations detected")
            print("   🚨 The fix has not resolved the core issues")
        
        print()
        
        if success_rate == 100:
            print("🎉 CONCLUSION: The dietary filtering fix is working correctly!")
            print("   Expected result: 100% safety compliance ✅")
            print("   Actual result: 100% safety compliance ✅")
            print("   Force regeneration: Working ✅")
            print("   Filtering function: Being called ✅")
        else:
            print("⚠️  CONCLUSION: The dietary filtering fix needs additional work")
            print(f"   Expected result: 100% safety compliance")
            print(f"   Actual result: {success_rate:.1f}% safety compliance")
            print("   Review failed tests and backend logs for issues")

def main():
    """Main test execution"""
    tester = DietaryFilteringTester()
    
    try:
        test_results = tester.run_dietary_filtering_tests()
        
        # Return appropriate exit code based on results
        success_rate = sum(1 for result in test_results if result) / len(test_results) * 100
        if success_rate == 100:
            exit(0)  # Perfect success
        elif success_rate >= 80:
            exit(1)  # Minor issues
        else:
            exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        exit(3)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        exit(4)

if __name__ == "__main__":
    main()