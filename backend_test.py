#!/usr/bin/env python3
"""
Backend Testing Script for Recipe History Navigation Issue
Testing the specific issue where recipe navigation shows null currentRecipeId
"""

import requests
import json
import uuid
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration
BACKEND_URL = "https://045a81c9-33d7-4680-8c7f-a77bc911fd54.preview.emergentagent.com/api"
DEMO_USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
DEMO_EMAIL = "demo@test.com"
DEMO_PASSWORD = "password123"

class RecipeHistoryTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
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
        if data and isinstance(data, dict) and len(str(data)) < 200:
            print(f"   Data: {data}")
        print()

    def is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False

    def test_demo_user_authentication(self) -> bool:
        """Test demo user login"""
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
                    self.log_test("Demo User Authentication", True, 
                                f"Successfully authenticated demo user with ID: {user_id}")
                    return True
                else:
                    self.log_test("Demo User Authentication", False, 
                                f"User ID mismatch or not verified. Got: {user_id}, verified: {is_verified}")
                    return False
            else:
                self.log_test("Demo User Authentication", False, 
                            f"Login failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Demo User Authentication", False, f"Exception: {str(e)}")
            return False

    def test_recipe_history_endpoint(self) -> Optional[List[Dict]]:
        """Test recipe history endpoint and return recipes"""
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/history/{DEMO_USER_ID}")
            
            if response.status_code == 200:
                data = response.json()
                recipes = data.get("recipes", [])
                total_count = len(recipes)
                
                if total_count > 0:
                    # Check for null recipe IDs
                    null_ids = [r for r in recipes if not r.get("id") or r.get("id") is None]
                    valid_ids = [r for r in recipes if r.get("id") and self.is_valid_uuid(r.get("id"))]
                    
                    self.log_test("Recipe History Endpoint", True, 
                                f"Retrieved {total_count} recipes, {len(null_ids)} null IDs, {len(valid_ids)} valid UUIDs",
                                {"total": total_count, "null_ids": len(null_ids), "valid_uuids": len(valid_ids)})
                    
                    if null_ids:
                        self.log_test("Recipe ID Validation", False, 
                                    f"Found {len(null_ids)} recipes with null/invalid IDs",
                                    {"null_recipes": [r.get("title", "Unknown") for r in null_ids[:3]]})
                    else:
                        self.log_test("Recipe ID Validation", True, 
                                    f"All {total_count} recipes have valid UUID IDs")
                    
                    return recipes
                else:
                    self.log_test("Recipe History Endpoint", False, "No recipes found in history")
                    return []
            else:
                self.log_test("Recipe History Endpoint", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Recipe History Endpoint", False, f"Exception: {str(e)}")
            return None

    def test_recipe_detail_endpoint(self, recipe_id: str, recipe_title: str = "Unknown") -> Optional[Dict]:
        """Test recipe detail endpoint for a specific recipe ID"""
        try:
            response = self.session.get(f"{BACKEND_URL}/recipes/{recipe_id}/detail")
            
            if response.status_code == 200:
                data = response.json()
                returned_id = data.get("id")
                returned_title = data.get("title", "No Title")
                
                # Verify the returned recipe matches the requested ID
                if returned_id == recipe_id:
                    self.log_test(f"Recipe Detail - {recipe_title[:30]}", True, 
                                f"Successfully retrieved recipe with matching ID: {recipe_id}",
                                {"id": returned_id, "title": returned_title})
                    return data
                else:
                    self.log_test(f"Recipe Detail - {recipe_title[:30]}", False, 
                                f"ID mismatch! Requested: {recipe_id}, Got: {returned_id}")
                    return None
            else:
                self.log_test(f"Recipe Detail - {recipe_title[:30]}", False, 
                            f"Failed with status {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test(f"Recipe Detail - {recipe_title[:30]}", False, f"Exception: {str(e)}")
            return None

    def test_recipe_navigation_consistency(self, recipes: List[Dict]) -> None:
        """Test that recipe IDs from history work correctly in detail endpoint"""
        if not recipes:
            self.log_test("Recipe Navigation Consistency", False, "No recipes to test")
            return
        
        # Test first 5 recipes to avoid overwhelming the API
        test_recipes = recipes[:5]
        successful_navigations = 0
        
        for recipe in test_recipes:
            recipe_id = recipe.get("id")
            recipe_title = recipe.get("title", "Unknown Recipe")
            
            if not recipe_id:
                continue
                
            detail_data = self.test_recipe_detail_endpoint(recipe_id, recipe_title)
            if detail_data:
                successful_navigations += 1
        
        success_rate = (successful_navigations / len(test_recipes)) * 100
        
        if success_rate == 100:
            self.log_test("Recipe Navigation Consistency", True, 
                        f"All {len(test_recipes)} tested recipes navigate correctly (100% success rate)")
        elif success_rate >= 80:
            self.log_test("Recipe Navigation Consistency", True, 
                        f"{successful_navigations}/{len(test_recipes)} recipes navigate correctly ({success_rate:.1f}% success rate)")
        else:
            self.log_test("Recipe Navigation Consistency", False, 
                        f"Only {successful_navigations}/{len(test_recipes)} recipes navigate correctly ({success_rate:.1f}% success rate)")

    def test_recipe_data_integrity(self, recipes: List[Dict]) -> None:
        """Test recipe data integrity and structure"""
        if not recipes:
            self.log_test("Recipe Data Integrity", False, "No recipes to test")
            return
        
        required_fields = ["id", "title"]
        optional_fields = ["description", "ingredients", "instructions", "cuisine_type"]
        
        issues = []
        valid_recipes = 0
        
        for i, recipe in enumerate(recipes[:10]):  # Test first 10 recipes
            recipe_issues = []
            
            # Check required fields
            for field in required_fields:
                if not recipe.get(field):
                    recipe_issues.append(f"Missing {field}")
            
            # Check ID format
            recipe_id = recipe.get("id")
            if recipe_id and not self.is_valid_uuid(recipe_id):
                recipe_issues.append(f"Invalid UUID format: {recipe_id}")
            
            # Check title
            title = recipe.get("title")
            if title and len(title.strip()) == 0:
                recipe_issues.append("Empty title")
            
            if not recipe_issues:
                valid_recipes += 1
            else:
                issues.append(f"Recipe {i+1} ({title[:20] if title else 'No Title'}): {', '.join(recipe_issues)}")
        
        if not issues:
            self.log_test("Recipe Data Integrity", True, 
                        f"All {min(10, len(recipes))} tested recipes have valid data structure")
        else:
            self.log_test("Recipe Data Integrity", False, 
                        f"{len(issues)} recipes have data issues",
                        {"issues": issues[:3]})  # Show first 3 issues

    def test_starbucks_recipe_navigation(self, recipes: List[Dict]) -> None:
        """Test navigation for Starbucks recipes specifically"""
        starbucks_recipes = [r for r in recipes if r.get("type") == "starbucks" or "starbucks" in r.get("title", "").lower()]
        
        if not starbucks_recipes:
            self.log_test("Starbucks Recipe Navigation", True, 
                        "No Starbucks recipes found in history (expected for demo user)")
            return
        
        successful_starbucks = 0
        for recipe in starbucks_recipes[:3]:  # Test first 3 Starbucks recipes
            recipe_id = recipe.get("id")
            recipe_title = recipe.get("title", "Unknown Starbucks Recipe")
            
            if recipe_id:
                detail_data = self.test_recipe_detail_endpoint(recipe_id, recipe_title)
                if detail_data:
                    successful_starbucks += 1
        
        if successful_starbucks == len(starbucks_recipes[:3]):
            self.log_test("Starbucks Recipe Navigation", True, 
                        f"All {successful_starbucks} Starbucks recipes navigate correctly")
        else:
            self.log_test("Starbucks Recipe Navigation", False, 
                        f"Only {successful_starbucks}/{len(starbucks_recipes[:3])} Starbucks recipes navigate correctly")

    def test_recipe_source_parameter(self, recipes: List[Dict]) -> None:
        """Test if recipes have proper source information"""
        if not recipes:
            self.log_test("Recipe Source Parameter", False, "No recipes to test")
            return
        
        recipes_with_source = 0
        source_types = {}
        
        for recipe in recipes[:10]:
            source = recipe.get("source") or recipe.get("type") or "unknown"
            source_types[source] = source_types.get(source, 0) + 1
            
            if source != "unknown":
                recipes_with_source += 1
        
        if recipes_with_source > 0:
            self.log_test("Recipe Source Parameter", True, 
                        f"{recipes_with_source}/10 recipes have source information",
                        {"source_breakdown": source_types})
        else:
            self.log_test("Recipe Source Parameter", False, 
                        "No recipes have source/type information - this could cause navigation issues")

    def run_comprehensive_test(self):
        """Run all tests for recipe history navigation"""
        print("🔍 RECIPE HISTORY NAVIGATION COMPREHENSIVE TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Demo User ID: {DEMO_USER_ID}")
        print()
        
        # Test 1: Authentication
        auth_success = self.test_demo_user_authentication()
        if not auth_success:
            print("❌ Authentication failed - cannot proceed with other tests")
            return self.results
        
        # Test 2: Recipe History Endpoint
        recipes = self.test_recipe_history_endpoint()
        if recipes is None:
            print("❌ Recipe history endpoint failed - cannot proceed with navigation tests")
            return self.results
        
        # Test 3: Recipe Data Integrity
        self.test_recipe_data_integrity(recipes)
        
        # Test 4: Recipe Source Information
        self.test_recipe_source_parameter(recipes)
        
        # Test 5: Recipe Navigation Consistency
        self.test_recipe_navigation_consistency(recipes)
        
        # Test 6: Starbucks Recipe Navigation (if any)
        self.test_starbucks_recipe_navigation(recipes)
        
        return self.results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total = self.results["total_tests"]
        passed = self.results["passed_tests"]
        failed = self.results["failed_tests"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed > 0:
            print(f"\n🚨 FAILED TESTS:")
            for test in self.results["test_details"]:
                if "❌ FAIL" in test["status"]:
                    print(f"   • {test['test']}: {test['details']}")
        
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        # Analyze results for the specific issue mentioned in review
        recipe_history_passed = any("Recipe History Endpoint" in t["test"] and "✅ PASS" in t["status"] for t in self.results["test_details"])
        navigation_passed = any("Recipe Navigation Consistency" in t["test"] and "✅ PASS" in t["status"] for t in self.results["test_details"])
        data_integrity_passed = any("Recipe Data Integrity" in t["test"] and "✅ PASS" in t["status"] for t in self.results["test_details"])
        
        if recipe_history_passed and navigation_passed and data_integrity_passed:
            print("   ✅ Recipe history navigation appears to be working correctly")
            print("   ✅ Recipe IDs are valid UUIDs and navigation is functional")
            print("   ✅ No evidence of null currentRecipeId issue in backend data")
        else:
            print("   ❌ Issues detected in recipe history navigation system")
            if not recipe_history_passed:
                print("   ❌ Recipe history endpoint has problems")
            if not navigation_passed:
                print("   ❌ Recipe navigation consistency issues detected")
            if not data_integrity_passed:
                print("   ❌ Recipe data integrity problems found")
        
        print(f"\n📝 RECOMMENDATION:")
        if success_rate >= 90:
            print("   Backend recipe history navigation is working correctly.")
            print("   If frontend shows null currentRecipeId, the issue is likely in frontend state management.")
        elif success_rate >= 70:
            print("   Backend has minor issues but core functionality works.")
            print("   Review failed tests for specific problems to address.")
        else:
            print("   Backend has significant issues that need immediate attention.")
            print("   Multiple components of recipe navigation are failing.")

def main():
    """Main test execution"""
    tester = RecipeHistoryTester()
    
    try:
        results = tester.run_comprehensive_test()
        tester.print_summary()
        
        # Return appropriate exit code
        if results["failed_tests"] == 0:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()