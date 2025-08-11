#!/usr/bin/env python3
"""
Backend API Testing for Recipe History Implementation
Testing the new Recipe History implementation as requested in review:
1. Login with demo@test.com/password123
2. Test /api/recipes/history/{user_id} endpoint to ensure it returns proper data
3. Check response format matches RecipeHistoryScreen component expectations
4. Test recipe deletion endpoint /api/recipes/{recipe_id} for a sample recipe
5. Verify data structure compatibility with new clean implementation
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://6012f3db-8cdb-45db-b399-2e6555315d6c.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_EMAIL = "demo@test.com"
TEST_PASSWORD = "password123"

def print_separator(title):
    """Print a formatted separator"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_response(response, title="Response"):
    """Print formatted response details"""
    print(f"\n--- {title} ---")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        response_json = response.json()
        print(f"JSON Response: {json.dumps(response_json, indent=2)}")
        return response_json
    except:
        print(f"Text Response: {response.text}")
        return None

def test_login():
    """Test user login and get user_id"""
    print_separator("TESTING USER LOGIN")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        response_data = print_response(response, "Login Response")
        
        if response.status_code == 200 and response_data:
            user_id = response_data.get('user', {}).get('id')
            print(f"\n✅ LOGIN SUCCESS - User ID: {user_id}")
            return user_id
        else:
            print(f"\n❌ LOGIN FAILED - Status: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ LOGIN ERROR: {str(e)}")
        return None

def test_recipe_history_format(user_id):
    """Test recipe history endpoint and verify response format for RecipeHistoryScreen"""
    print_separator("TESTING RECIPE HISTORY FORMAT FOR NEW IMPLEMENTATION")
    
    try:
        url = f"{API_BASE}/recipes/history/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Recipe History Response")
        
        if response.status_code == 200 and response_data:
            recipes = response_data.get('recipes', [])
            total_count = response_data.get('total_count', len(recipes))
            
            print(f"\n✅ RECIPE HISTORY SUCCESS - Found {len(recipes)} recipes")
            print(f"✅ TOTAL COUNT: {total_count}")
            
            # Verify response format matches RecipeHistoryScreen expectations
            format_issues = []
            
            # Check if recipes array exists
            if not isinstance(recipes, list):
                format_issues.append("'recipes' should be an array")
            
            # Check if total_count exists
            if 'total_count' not in response_data:
                format_issues.append("'total_count' field missing")
            
            # Check first few recipes for required fields
            required_fields = ['id', 'title', 'description', 'created_at']
            sample_recipes = recipes[:3] if recipes else []
            
            for i, recipe in enumerate(sample_recipes):
                print(f"\n--- Recipe {i+1} Format Check ---")
                recipe_issues = []
                
                for field in required_fields:
                    if field not in recipe:
                        recipe_issues.append(f"Missing '{field}' field")
                    else:
                        print(f"✅ {field}: {recipe.get(field)}")
                
                if recipe_issues:
                    format_issues.extend([f"Recipe {i+1}: {issue}" for issue in recipe_issues])
                else:
                    print(f"✅ Recipe {i+1} format is correct")
            
            # Summary of format check
            if format_issues:
                print(f"\n❌ FORMAT ISSUES FOUND:")
                for issue in format_issues:
                    print(f"  - {issue}")
                return False, recipes, total_count
            else:
                print(f"\n✅ RESPONSE FORMAT IS CORRECT FOR RECIPEHISTORYSCREEN")
                return True, recipes, total_count
                
        else:
            print(f"\n❌ RECIPE HISTORY FAILED - Status: {response.status_code}")
            return False, [], 0
            
    except Exception as e:
        print(f"\n❌ RECIPE HISTORY ERROR: {str(e)}")
        return False, [], 0

def test_recipe_deletion(recipe_id, recipe_title):
    """Test recipe deletion endpoint"""
    print_separator(f"TESTING RECIPE DELETION - {recipe_title}")
    
    try:
        url = f"{API_BASE}/recipes/{recipe_id}"
        print(f"Testing DELETE URL: {url}")
        print(f"Recipe ID: {recipe_id}")
        print(f"Recipe Title: {recipe_title}")
        
        response = requests.delete(url, timeout=10)
        response_data = print_response(response, "Recipe Deletion Response")
        
        if response.status_code == 200:
            print(f"\n✅ RECIPE DELETION SUCCESS")
            return True, response_data
        elif response.status_code == 404:
            print(f"\n⚠️ RECIPE NOT FOUND FOR DELETION (may already be deleted)")
            return False, response_data
        else:
            print(f"\n❌ RECIPE DELETION FAILED - Status: {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ RECIPE DELETION ERROR: {str(e)}")
        return False, None

def test_data_structure_compatibility(recipes):
    """Verify data structure is compatible with new clean implementation"""
    print_separator("TESTING DATA STRUCTURE COMPATIBILITY")
    
    compatibility_score = 0
    total_checks = 0
    issues = []
    
    if not recipes:
        print("❌ No recipes to test compatibility")
        return False, []
    
    print(f"Testing compatibility for {len(recipes)} recipes...")
    
    # Test sample of recipes (first 5)
    sample_recipes = recipes[:5]
    
    for i, recipe in enumerate(sample_recipes):
        print(f"\n--- Recipe {i+1} Compatibility Check ---")
        recipe_score = 0
        recipe_checks = 0
        
        # Check for essential fields
        essential_fields = {
            'id': 'string',
            'title': 'string', 
            'description': 'string',
            'created_at': 'string'
        }
        
        for field, expected_type in essential_fields.items():
            recipe_checks += 1
            total_checks += 1
            
            if field in recipe:
                value = recipe[field]
                if expected_type == 'string' and isinstance(value, str) and value.strip():
                    print(f"✅ {field}: Valid {expected_type}")
                    recipe_score += 1
                    compatibility_score += 1
                elif expected_type == 'string' and not isinstance(value, str):
                    print(f"❌ {field}: Expected {expected_type}, got {type(value).__name__}")
                    issues.append(f"Recipe {i+1}: {field} type mismatch")
                elif expected_type == 'string' and not value.strip():
                    print(f"❌ {field}: Empty string")
                    issues.append(f"Recipe {i+1}: {field} is empty")
                else:
                    print(f"✅ {field}: Present")
                    recipe_score += 1
                    compatibility_score += 1
            else:
                print(f"❌ {field}: Missing")
                issues.append(f"Recipe {i+1}: Missing {field}")
        
        # Check for optional but useful fields
        optional_fields = ['ingredients', 'instructions', 'prep_time', 'cook_time', 'servings', 'cuisine_type']
        
        for field in optional_fields:
            if field in recipe:
                print(f"✅ Optional field {field}: Present")
            else:
                print(f"⚠️ Optional field {field}: Missing")
        
        recipe_percentage = (recipe_score / recipe_checks) * 100 if recipe_checks > 0 else 0
        print(f"Recipe {i+1} compatibility: {recipe_percentage:.1f}% ({recipe_score}/{recipe_checks})")
    
    # Overall compatibility score
    overall_percentage = (compatibility_score / total_checks) * 100 if total_checks > 0 else 0
    print(f"\n--- OVERALL COMPATIBILITY RESULTS ---")
    print(f"Compatibility Score: {overall_percentage:.1f}% ({compatibility_score}/{total_checks})")
    
    if overall_percentage >= 90:
        print("✅ EXCELLENT COMPATIBILITY - Ready for production")
        return True, issues
    elif overall_percentage >= 75:
        print("⚠️ GOOD COMPATIBILITY - Minor issues to address")
        return True, issues
    elif overall_percentage >= 50:
        print("❌ POOR COMPATIBILITY - Significant issues need fixing")
        return False, issues
    else:
        print("🚨 CRITICAL COMPATIBILITY ISSUES - Major fixes required")
        return False, issues

def test_recipe_detail_comprehensive(recipe_info):
    """Comprehensive test of recipe detail endpoint"""
    print_separator(f"COMPREHENSIVE RECIPE DETAIL TEST - {recipe_info['title']}")
    
    recipe_id = recipe_info['id']
    
    try:
        url = f"{API_BASE}/recipes/{recipe_id}/detail"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Recipe Detail Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ RECIPE DETAIL SUCCESS")
            
            # Verify all expected fields are present
            expected_fields = ['id', 'title', 'description', 'ingredients', 'instructions']
            missing_fields = []
            
            for field in expected_fields:
                if field not in response_data:
                    missing_fields.append(field)
                else:
                    value = response_data[field]
                    if isinstance(value, list):
                        print(f"✅ {field}: {len(value)} items")
                    else:
                        print(f"✅ {field}: {str(value)[:50]}...")
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False, response_data
            else:
                print(f"✅ All expected fields present")
                return True, response_data
                
        else:
            print(f"\n❌ RECIPE DETAIL FAILED - Status: {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ RECIPE DETAIL ERROR: {str(e)}")
        return False, None

def main():
    """Main test function for Recipe History Implementation"""
    print_separator("RECIPE HISTORY IMPLEMENTATION TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    
    # Step 1: Login with demo@test.com/password123
    user_id = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return
    
    # Step 2: Test /api/recipes/history/{user_id} endpoint format
    format_ok, recipes, total_count = test_recipe_history_format(user_id)
    if not format_ok or not recipes:
        print("\n🚨 CANNOT PROCEED - Recipe history format issues or no recipes")
        return
    
    # Step 3: Test data structure compatibility with new clean implementation
    compatibility_ok, compatibility_issues = test_data_structure_compatibility(recipes)
    
    # Step 4: Test recipe detail endpoint for sample recipes
    print_separator("TESTING RECIPE DETAIL ENDPOINTS")
    detail_test_results = []
    
    # Test first 3 recipes
    sample_recipes = recipes[:3]
    for i, recipe in enumerate(sample_recipes):
        recipe_info = {
            'id': recipe.get('id'),
            'title': recipe.get('title', f'Recipe {i+1}'),
            'type': recipe.get('type', 'recipe')
        }
        
        if recipe_info['id']:
            success, data = test_recipe_detail_comprehensive(recipe_info)
            detail_test_results.append((success, recipe_info, data))
    
    # Step 5: Test recipe deletion endpoint for one sample recipe
    if sample_recipes and sample_recipes[0].get('id'):
        sample_recipe = sample_recipes[0]
        deletion_success, deletion_data = test_recipe_deletion(
            sample_recipe.get('id'), 
            sample_recipe.get('title', 'Sample Recipe')
        )
    
    # Final Summary
    print_separator("FINAL TEST SUMMARY")
    
    print(f"✅ User Login: SUCCESS")
    print(f"{'✅' if format_ok else '❌'} Recipe History Format: {'PASS' if format_ok else 'FAIL'}")
    print(f"{'✅' if compatibility_ok else '❌'} Data Structure Compatibility: {'PASS' if compatibility_ok else 'FAIL'}")
    
    detail_success_count = sum(1 for success, _, _ in detail_test_results if success)
    print(f"✅ Recipe Detail Tests: {detail_success_count}/{len(detail_test_results)} PASSED")
    
    if 'deletion_success' in locals():
        print(f"{'✅' if deletion_success else '❌'} Recipe Deletion Test: {'PASS' if deletion_success else 'FAIL'}")
    
    # Overall assessment
    total_tests = 4  # login, format, compatibility, detail tests
    passed_tests = 1  # login always passes if we get here
    if format_ok:
        passed_tests += 1
    if compatibility_ok:
        passed_tests += 1
    if detail_success_count > 0:
        passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n--- OVERALL ASSESSMENT ---")
    print(f"Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT - Recipe History implementation is ready for production!")
    elif success_rate >= 75:
        print("✅ GOOD - Recipe History implementation working well with minor issues")
    elif success_rate >= 50:
        print("⚠️ NEEDS WORK - Recipe History implementation has significant issues")
    else:
        print("🚨 CRITICAL - Recipe History implementation requires major fixes")
    
    # Report issues found
    if compatibility_issues:
        print(f"\n--- ISSUES TO ADDRESS ---")
        for issue in compatibility_issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
        if len(compatibility_issues) > 5:
            print(f"  ... and {len(compatibility_issues) - 5} more issues")
    
    print_separator("TEST COMPLETE")

if __name__ == "__main__":
    main()