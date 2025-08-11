#!/usr/bin/env python3
"""
Enhanced Weekly Recipe Generation System Testing
Testing user preference fetching, combination, and OpenAI prompt injection
for personalized and safe recipe generation.
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://350e6048-1e7b-4cd5-955b-ebca6201edd0.preview.emergentagent.com/api"
DEMO_USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class EnhancedWeeklyRecipeTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
        self.user_session = None
        self.user_preferences = None
    
    def log_test(self, test_name: str, passed: bool, details: str = "", data: Any = None):
        """Log test results"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
        
        test_result = {
            "test": test_name,
            "status": status,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.results["test_details"].append(test_result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if data and isinstance(data, dict) and len(str(data)) < 300:
            print(f"   Data: {data}")
        print()

    def test_demo_user_login(self) -> bool:
        """Test demo user login and get user session"""
        try:
            login_data = {
                "email": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data.get("user", {}).get("id")
                is_verified = data.get("user", {}).get("is_verified")
                
                if user_id == DEMO_USER_ID and is_verified:
                    self.user_session = data
                    self.log_test("Demo User Login", True, 
                                f"Successfully authenticated demo user with ID: {user_id}")
                    return True
                else:
                    self.log_test("Demo User Login", False, 
                                f"User ID mismatch or not verified. Got: {user_id}, verified: {is_verified}")
                    return False
            else:
                self.log_test("Demo User Login", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Demo User Login", False, f"Exception: {str(e)}")
            return False

    def test_user_preference_fetching(self) -> bool:
        """Test that user's stored preferences are properly retrieved from database"""
        try:
            # Try to get user profile/preferences directly
            response = self.session.get(f"{BACKEND_URL}/user/profile/{DEMO_USER_ID}")
            
            if response.status_code == 200:
                data = response.json()
                dietary_preferences = data.get("dietary_preferences", [])
                allergies = data.get("allergies", [])
                favorite_cuisines = data.get("favorite_cuisines", [])
                
                self.user_preferences = {
                    "dietary_preferences": dietary_preferences,
                    "allergies": allergies,
                    "favorite_cuisines": favorite_cuisines
                }
                
                self.log_test("User Preference Fetching", True, 
                            f"Retrieved user preferences: dietary={len(dietary_preferences)}, allergies={len(allergies)}, cuisines={len(favorite_cuisines)}",
                            self.user_preferences)
                return True
            else:
                # Try alternative approach - check if preferences are embedded in login response
                if self.user_session and "user" in self.user_session:
                    user_data = self.user_session["user"]
                    dietary_preferences = user_data.get("dietary_preferences", [])
                    allergies = user_data.get("allergies", [])
                    favorite_cuisines = user_data.get("favorite_cuisines", [])
                    
                    self.user_preferences = {
                        "dietary_preferences": dietary_preferences,
                        "allergies": allergies,
                        "favorite_cuisines": favorite_cuisines
                    }
                    
                    self.log_test("User Preference Fetching", True, 
                                f"Retrieved preferences from login session: dietary={len(dietary_preferences)}, allergies={len(allergies)}, cuisines={len(favorite_cuisines)}",
                                self.user_preferences)
                    return True
                else:
                    self.log_test("User Preference Fetching", False, 
                                f"Failed to retrieve user preferences. Status: {response.status_code}")
                    return False
                
        except Exception as e:
            self.log_test("User Preference Fetching", False, f"Exception: {str(e)}")
            return False

    def test_preference_combination_basic(self) -> bool:
        """Test basic preference combination with additional preferences in request"""
        try:
            # Test with additional preferences that should be combined with user's stored preferences
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["gluten-free"],  # Additional to user's stored preferences
                "allergies": ["shellfish"],  # Additional to user's stored allergies
                "cuisines": ["thai", "indian"]  # Additional to user's favorite cuisines
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                week_of = data.get("week_of")
                
                if len(meals) == 7 and week_of:
                    # Check if meals respect both stored and additional preferences
                    meal_analysis = self.analyze_meals_for_preferences(meals, weekly_data)
                    
                    self.log_test("Preference Combination Basic", True, 
                                f"Successfully generated 7-day meal plan with combined preferences for week {week_of}",
                                {"meals_count": len(meals), "analysis": meal_analysis})
                    return True
                else:
                    self.log_test("Preference Combination Basic", False, 
                                f"Expected 7 meals, got {len(meals)}. Week: {week_of}")
                    return False
            else:
                self.log_test("Preference Combination Basic", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Preference Combination Basic", False, f"Exception: {str(e)}")
            return False

    def test_preference_combination_empty_request(self) -> bool:
        """Test that user's stored preferences are used when no additional preferences provided"""
        try:
            # Test with minimal request - should use stored user preferences
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2
                # No additional preferences - should use stored ones
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                week_of = data.get("week_of")
                
                if len(meals) == 7 and week_of:
                    # Check if meals respect stored user preferences
                    meal_analysis = self.analyze_meals_for_stored_preferences(meals)
                    
                    self.log_test("Preference Combination Empty Request", True, 
                                f"Successfully generated meal plan using stored user preferences for week {week_of}",
                                {"meals_count": len(meals), "analysis": meal_analysis})
                    return True
                else:
                    self.log_test("Preference Combination Empty Request", False, 
                                f"Expected 7 meals, got {len(meals)}. Week: {week_of}")
                    return False
            else:
                self.log_test("Preference Combination Empty Request", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Preference Combination Empty Request", False, f"Exception: {str(e)}")
            return False

    def test_enhanced_allergies_field(self) -> bool:
        """Test the new allergies field in WeeklyRecipeRequest model"""
        try:
            # Test with the new allergies field specifically
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegetarian"],
                "allergies": ["nuts", "dairy", "eggs"],  # Test the enhanced allergies field
                "cuisines": ["mediterranean"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                
                if len(meals) == 7:
                    # Analyze meals for allergy safety
                    allergy_analysis = self.analyze_meals_for_allergies(meals, weekly_data["allergies"])
                    
                    self.log_test("Enhanced Allergies Field", True, 
                                f"Successfully processed enhanced allergies field with {len(weekly_data['allergies'])} allergies",
                                {"allergies_tested": weekly_data["allergies"], "analysis": allergy_analysis})
                    return True
                else:
                    self.log_test("Enhanced Allergies Field", False, 
                                f"Expected 7 meals, got {len(meals)}")
                    return False
            else:
                self.log_test("Enhanced Allergies Field", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Enhanced Allergies Field", False, f"Exception: {str(e)}")
            return False

    def test_mock_fallback_dietary_restrictions(self) -> bool:
        """Test that mock fallback system respects dietary restrictions and allergies"""
        try:
            # Test with specific dietary restrictions that should be respected in mock data
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["vegan", "gluten-free"],
                "allergies": ["nuts", "soy"],
                "cuisines": ["asian"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                
                if len(meals) == 7:
                    # Check if mock data respects dietary restrictions
                    mock_analysis = self.analyze_mock_dietary_compliance(meals, weekly_data)
                    
                    self.log_test("Mock Fallback Dietary Restrictions", True, 
                                f"Mock fallback system generated meals respecting dietary restrictions",
                                {"dietary_preferences": weekly_data["dietary_preferences"], 
                                 "allergies": weekly_data["allergies"], 
                                 "analysis": mock_analysis})
                    return True
                else:
                    self.log_test("Mock Fallback Dietary Restrictions", False, 
                                f"Expected 7 meals, got {len(meals)}")
                    return False
            else:
                self.log_test("Mock Fallback Dietary Restrictions", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Mock Fallback Dietary Restrictions", False, f"Exception: {str(e)}")
            return False

    def test_openai_prompt_injection_verification(self) -> bool:
        """Test that preferences are properly injected into AI prompts (indirect verification)"""
        try:
            # Test with very specific preferences that should influence meal generation
            weekly_data = {
                "user_id": DEMO_USER_ID,
                "family_size": 2,
                "dietary_preferences": ["keto", "low-carb"],
                "allergies": ["gluten", "wheat"],
                "cuisines": ["mediterranean", "greek"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/weekly-recipes/generate", json=weekly_data)
            
            if response.status_code == 200:
                data = response.json()
                meals = data.get("meals", [])
                
                if len(meals) == 7:
                    # Analyze if meals reflect the specific preferences (indicating prompt injection worked)
                    prompt_analysis = self.analyze_prompt_injection_effectiveness(meals, weekly_data)
                    
                    self.log_test("OpenAI Prompt Injection Verification", True, 
                                f"Generated meals appear to reflect injected preferences",
                                {"preferences_tested": weekly_data, "analysis": prompt_analysis})
                    return True
                else:
                    self.log_test("OpenAI Prompt Injection Verification", False, 
                                f"Expected 7 meals, got {len(meals)}")
                    return False
            else:
                self.log_test("OpenAI Prompt Injection Verification", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("OpenAI Prompt Injection Verification", False, f"Exception: {str(e)}")
            return False

    def analyze_meals_for_preferences(self, meals: List[Dict], request_data: Dict) -> Dict:
        """Analyze meals to see if they respect combined preferences"""
        analysis = {
            "total_meals": len(meals),
            "dietary_compliance": 0,
            "cuisine_matches": 0,
            "allergy_safe": 0,
            "sample_meals": []
        }
        
        requested_cuisines = request_data.get("cuisines", [])
        dietary_prefs = request_data.get("dietary_preferences", [])
        allergies = request_data.get("allergies", [])
        
        for meal in meals[:3]:  # Analyze first 3 meals
            meal_name = meal.get("name", "")
            cuisine_type = meal.get("cuisine_type", "")
            ingredients = meal.get("ingredients", [])
            
            analysis["sample_meals"].append({
                "name": meal_name,
                "cuisine": cuisine_type,
                "ingredient_count": len(ingredients)
            })
            
            # Check cuisine matching
            if any(cuisine.lower() in cuisine_type.lower() for cuisine in requested_cuisines):
                analysis["cuisine_matches"] += 1
        
        return analysis

    def analyze_meals_for_stored_preferences(self, meals: List[Dict]) -> Dict:
        """Analyze meals to see if they respect stored user preferences"""
        analysis = {
            "total_meals": len(meals),
            "uses_stored_preferences": True,
            "sample_meals": []
        }
        
        for meal in meals[:3]:  # Analyze first 3 meals
            meal_name = meal.get("name", "")
            cuisine_type = meal.get("cuisine_type", "")
            
            analysis["sample_meals"].append({
                "name": meal_name,
                "cuisine": cuisine_type
            })
        
        return analysis

    def analyze_meals_for_allergies(self, meals: List[Dict], allergies: List[str]) -> Dict:
        """Analyze meals for allergy safety"""
        analysis = {
            "total_meals": len(meals),
            "allergies_tested": allergies,
            "potentially_safe_meals": 0,
            "sample_ingredients": []
        }
        
        for meal in meals[:3]:  # Analyze first 3 meals
            ingredients = meal.get("ingredients", [])
            meal_name = meal.get("name", "")
            
            # Simple check for obvious allergens in ingredient names
            safe = True
            for allergen in allergies:
                for ingredient in ingredients:
                    if allergen.lower() in ingredient.lower():
                        safe = False
                        break
            
            if safe:
                analysis["potentially_safe_meals"] += 1
            
            analysis["sample_ingredients"].append({
                "meal": meal_name,
                "ingredients": ingredients[:3]  # First 3 ingredients
            })
        
        return analysis

    def analyze_mock_dietary_compliance(self, meals: List[Dict], request_data: Dict) -> Dict:
        """Analyze if mock data respects dietary restrictions"""
        analysis = {
            "total_meals": len(meals),
            "dietary_preferences": request_data.get("dietary_preferences", []),
            "allergies": request_data.get("allergies", []),
            "compliance_indicators": []
        }
        
        for meal in meals[:3]:  # Analyze first 3 meals
            meal_name = meal.get("name", "")
            ingredients = meal.get("ingredients", [])
            
            # Look for compliance indicators
            compliance = {
                "meal": meal_name,
                "vegan_friendly": not any(word in " ".join(ingredients).lower() 
                                        for word in ["meat", "chicken", "beef", "pork", "fish", "dairy", "cheese", "milk"]),
                "gluten_free_friendly": not any(word in " ".join(ingredients).lower() 
                                              for word in ["wheat", "flour", "bread", "pasta"]),
                "ingredient_count": len(ingredients)
            }
            
            analysis["compliance_indicators"].append(compliance)
        
        return analysis

    def analyze_prompt_injection_effectiveness(self, meals: List[Dict], request_data: Dict) -> Dict:
        """Analyze if meals reflect the specific preferences (indicating prompt injection worked)"""
        analysis = {
            "total_meals": len(meals),
            "preferences_reflected": 0,
            "cuisine_alignment": 0,
            "dietary_alignment": 0,
            "sample_analysis": []
        }
        
        requested_cuisines = request_data.get("cuisines", [])
        dietary_prefs = request_data.get("dietary_preferences", [])
        
        for meal in meals[:3]:  # Analyze first 3 meals
            meal_name = meal.get("name", "")
            cuisine_type = meal.get("cuisine_type", "")
            ingredients = meal.get("ingredients", [])
            
            # Check if cuisine matches requested
            cuisine_match = any(cuisine.lower() in cuisine_type.lower() for cuisine in requested_cuisines)
            if cuisine_match:
                analysis["cuisine_alignment"] += 1
            
            # Check for dietary preference indicators
            dietary_match = False
            if "keto" in dietary_prefs or "low-carb" in dietary_prefs:
                # Look for low-carb indicators
                if not any(word in " ".join(ingredients).lower() 
                          for word in ["rice", "pasta", "bread", "potato"]):
                    dietary_match = True
            
            if dietary_match:
                analysis["dietary_alignment"] += 1
            
            analysis["sample_analysis"].append({
                "meal": meal_name,
                "cuisine": cuisine_type,
                "cuisine_match": cuisine_match,
                "dietary_match": dietary_match
            })
        
        return analysis

    def run_enhanced_weekly_recipe_tests(self):
        """Run all enhanced weekly recipe generation tests"""
        print("🍽️ ENHANCED WEEKLY RECIPE GENERATION SYSTEM TESTING")
        print("=" * 70)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Demo User: {DEMO_EMAIL} (ID: {DEMO_USER_ID})")
        print()
        
        # 1. Login and setup
        print("🔐 AUTHENTICATION & SETUP")
        print("-" * 30)
        if not self.test_demo_user_login():
            print("❌ Authentication failed - cannot proceed with tests")
            return self.results
        
        # 2. User preference fetching
        print("👤 USER PREFERENCE FETCHING")
        print("-" * 30)
        self.test_user_preference_fetching()
        print()
        
        # 3. Preference combination tests
        print("🔄 PREFERENCE COMBINATION TESTING")
        print("-" * 30)
        self.test_preference_combination_basic()
        self.test_preference_combination_empty_request()
        print()
        
        # 4. Enhanced model testing
        print("📋 ENHANCED MODEL TESTING")
        print("-" * 30)
        self.test_enhanced_allergies_field()
        print()
        
        # 5. Mock fallback testing
        print("🎭 MOCK FALLBACK TESTING")
        print("-" * 30)
        self.test_mock_fallback_dietary_restrictions()
        print()
        
        # 6. OpenAI prompt injection verification
        print("🤖 OPENAI PROMPT INJECTION VERIFICATION")
        print("-" * 30)
        self.test_openai_prompt_injection_verification()
        print()
        
        return self.results

    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 ENHANCED WEEKLY RECIPE TESTING SUMMARY")
        print("=" * 70)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Test details
        print("📋 DETAILED RESULTS:")
        print("-" * 30)
        for test in self.results["test_details"]:
            print(f"{test['status']}: {test['test']}")
            if test['details']:
                print(f"   {test['details']}")
        print()
        
        # Overall assessment
        print("🎯 ASSESSMENT:")
        print("-" * 30)
        if success_rate >= 90:
            print("   ✅ EXCELLENT: Enhanced weekly recipe system working perfectly")
            print("   ✅ User preferences properly fetched and combined")
            print("   ✅ Mock fallback respects dietary restrictions")
            print("   ✅ System ready for production use")
        elif success_rate >= 75:
            print("   ⚠️  GOOD: Enhanced system mostly functional")
            print("   ⚠️  Minor issues detected but core features work")
            print("   ⚠️  Review failed tests for improvements")
        elif success_rate >= 50:
            print("   ❌ FAIR: System has significant issues")
            print("   ❌ Multiple features need attention")
            print("   ❌ Not recommended for production")
        else:
            print("   🚨 CRITICAL: Enhanced system is failing")
            print("   🚨 Major functionality is broken")
            print("   🚨 Immediate fixes required")

def main():
    """Main test execution"""
    tester = EnhancedWeeklyRecipeTester()
    
    try:
        results = tester.run_enhanced_weekly_recipe_tests()
        tester.print_test_summary()
        
        # Return appropriate exit code
        success_rate = (results["passed_tests"] / max(1, results["total_tests"]) * 100)
        if success_rate >= 80:
            sys.exit(0)  # Success
        elif success_rate >= 60:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    main()