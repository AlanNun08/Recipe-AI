#!/usr/bin/env python3
"""
Backend API Testing for Recipe History Navigation Issue
Testing the specific issue where users click "View" from recipe history but get "Recipe Not Found"
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

def test_recipe_history(user_id):
    """Get recipe history and return first few recipe IDs"""
    print_separator("TESTING RECIPE HISTORY ENDPOINT")
    
    try:
        url = f"{API_BASE}/recipes/history/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Recipe History Response")
        
        if response.status_code == 200 and response_data:
            recipes = response_data.get('recipes', [])
            print(f"\n✅ RECIPE HISTORY SUCCESS - Found {len(recipes)} recipes")
            
            # Get first 5 recipe IDs for testing
            recipe_ids = []
            for i, recipe in enumerate(recipes[:5]):
                recipe_id = recipe.get('id')
                recipe_title = recipe.get('title', 'Unknown')
                recipe_type = recipe.get('type', 'Unknown')
                print(f"Recipe {i+1}: ID={recipe_id}, Title='{recipe_title}', Type='{recipe_type}'")
                if recipe_id:
                    recipe_ids.append({
                        'id': recipe_id,
                        'title': recipe_title,
                        'type': recipe_type
                    })
            
            return recipe_ids
        else:
            print(f"\n❌ RECIPE HISTORY FAILED - Status: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"\n❌ RECIPE HISTORY ERROR: {str(e)}")
        return []

def test_recipe_detail_endpoint(recipe_info):
    """Test the /api/recipes/{recipe_id}/detail endpoint"""
    print_separator(f"TESTING RECIPE DETAIL ENDPOINT - {recipe_info['title']}")
    
    recipe_id = recipe_info['id']
    
    try:
        url = f"{API_BASE}/recipes/{recipe_id}/detail"
        print(f"Testing URL: {url}")
        print(f"Recipe ID: {recipe_id}")
        print(f"Recipe Title: {recipe_info['title']}")
        print(f"Recipe Type: {recipe_info['type']}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Recipe Detail Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ RECIPE DETAIL SUCCESS")
            # Check if the returned recipe matches the requested one
            returned_id = response_data.get('id')
            returned_title = response_data.get('title')
            
            if returned_id == recipe_id:
                print(f"✅ ID MATCH: Requested={recipe_id}, Returned={returned_id}")
            else:
                print(f"❌ ID MISMATCH: Requested={recipe_id}, Returned={returned_id}")
                
            if returned_title:
                print(f"✅ TITLE RETURNED: {returned_title}")
            else:
                print(f"❌ NO TITLE RETURNED")
                
            return True, response_data
        else:
            print(f"\n❌ RECIPE DETAIL FAILED - Status: {response.status_code}")
            if response.status_code == 404:
                print("❌ RECIPE NOT FOUND - This is the issue!")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ RECIPE DETAIL ERROR: {str(e)}")
        return False, None

def test_weekly_recipe_endpoint(recipe_info):
    """Test the /api/weekly-recipes/recipe/{recipe_id} endpoint"""
    print_separator(f"TESTING WEEKLY RECIPE ENDPOINT - {recipe_info['title']}")
    
    recipe_id = recipe_info['id']
    
    try:
        url = f"{API_BASE}/weekly-recipes/recipe/{recipe_id}"
        print(f"Testing URL: {url}")
        print(f"Recipe ID: {recipe_id}")
        print(f"Recipe Title: {recipe_info['title']}")
        print(f"Recipe Type: {recipe_info['type']}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Weekly Recipe Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ WEEKLY RECIPE SUCCESS")
            # Check if the returned recipe matches the requested one
            returned_id = response_data.get('id')
            returned_title = response_data.get('name') or response_data.get('title')
            
            if returned_id == recipe_id:
                print(f"✅ ID MATCH: Requested={recipe_id}, Returned={returned_id}")
            else:
                print(f"❌ ID MISMATCH: Requested={recipe_id}, Returned={returned_id}")
                
            if returned_title:
                print(f"✅ TITLE RETURNED: {returned_title}")
            else:
                print(f"❌ NO TITLE RETURNED")
                
            # Check for cart_ingredients (specific to weekly recipes)
            cart_ingredients = response_data.get('cart_ingredients', [])
            if cart_ingredients:
                print(f"✅ CART INGREDIENTS FOUND: {len(cart_ingredients)} items")
            else:
                print(f"⚠️ NO CART INGREDIENTS (may be normal for non-weekly recipes)")
                
            return True, response_data
        else:
            print(f"\n❌ WEEKLY RECIPE FAILED - Status: {response.status_code}")
            if response.status_code == 404:
                print("❌ RECIPE NOT FOUND in weekly recipes")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ WEEKLY RECIPE ERROR: {str(e)}")
        return False, None

def analyze_results(recipe_ids, detail_results, weekly_results):
    """Analyze the test results to identify the root cause"""
    print_separator("ANALYSIS OF RESULTS")
    
    print(f"Total recipes tested: {len(recipe_ids)}")
    
    detail_success_count = sum(1 for success, _ in detail_results if success)
    weekly_success_count = sum(1 for success, _ in weekly_results if success)
    
    print(f"Recipe Detail Endpoint Success: {detail_success_count}/{len(recipe_ids)}")
    print(f"Weekly Recipe Endpoint Success: {weekly_success_count}/{len(recipe_ids)}")
    
    print("\n--- DETAILED ANALYSIS ---")
    for i, recipe_info in enumerate(recipe_ids):
        recipe_id = recipe_info['id']
        recipe_title = recipe_info['title']
        recipe_type = recipe_info['type']
        
        detail_success, detail_data = detail_results[i]
        weekly_success, weekly_data = weekly_results[i]
        
        print(f"\nRecipe {i+1}: {recipe_title} (ID: {recipe_id}, Type: {recipe_type})")
        print(f"  Detail Endpoint: {'✅ SUCCESS' if detail_success else '❌ FAILED'}")
        print(f"  Weekly Endpoint: {'✅ SUCCESS' if weekly_success else '❌ FAILED'}")
        
        if not detail_success and not weekly_success:
            print(f"  🚨 CRITICAL: Recipe not found in either endpoint!")
        elif detail_success and not weekly_success:
            print(f"  ℹ️ INFO: Recipe found in detail but not weekly (normal for non-weekly recipes)")
        elif not detail_success and weekly_success:
            print(f"  ⚠️ WARNING: Recipe found in weekly but not detail (potential issue)")
        else:
            print(f"  ✅ GOOD: Recipe found in both endpoints")

def main():
    """Main test function"""
    print_separator("RECIPE HISTORY NAVIGATION ISSUE DEBUG")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    
    # Step 1: Login
    user_id = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return
    
    # Step 2: Get recipe history
    recipe_ids = test_recipe_history(user_id)
    if not recipe_ids:
        print("\n🚨 CANNOT PROCEED - No recipes found in history")
        return
    
    # Step 3: Test each recipe ID against both endpoints
    detail_results = []
    weekly_results = []
    
    for recipe_info in recipe_ids:
        # Test detail endpoint
        detail_success, detail_data = test_recipe_detail_endpoint(recipe_info)
        detail_results.append((detail_success, detail_data))
        
        # Test weekly recipe endpoint
        weekly_success, weekly_data = test_weekly_recipe_endpoint(recipe_info)
        weekly_results.append((weekly_success, weekly_data))
    
    # Step 4: Analyze results
    analyze_results(recipe_ids, detail_results, weekly_results)
    
    print_separator("TEST COMPLETE")
    print("Check the analysis above to understand why frontend gets 'Recipe Not Found'")

if __name__ == "__main__":
    main()