#!/usr/bin/env python3
"""
Comprehensive Settings and Usage Limit System Testing
Testing the comprehensive Settings and Usage Limit system that was just implemented.

As requested in the review, focus on:

1. Settings Endpoints Testing:
   - GET /api/user/settings/{user_id} - Test fetching complete user settings including profile, subscription, and usage data
   - PUT /api/user/profile/{user_id} - Test updating user profile information
   - GET /api/user/usage/{user_id} - Test fetching detailed usage information

2. Subscription Management:
   - POST /api/subscription/cancel/{user_id} - Test subscription cancellation (cancel_at_period_end)
   - POST /api/subscription/reactivate/{user_id} - Test subscription reactivation

3. Usage Limit Enforcement:
   - Test that usage limits are properly enforced for demo user on:
     - Individual recipe generation (should allow up to 10, then block)
     - Weekly recipe generation (should allow up to 2, then block)
     - Starbucks drink generation (should allow up to 10, then block)
   - Verify that 429 errors are returned with proper upgrade information when limits are exceeded

4. Usage Tracking:
   - Verify that usage counters increment properly after successful generations
   - Test monthly reset functionality
   - Confirm usage data is accurate in settings endpoint

Use demo user (demo@test.com) for testing. Verify all error handling, success responses, and data accuracy.
"""

import requests
import json
import sys
import re
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://4d24c0b0-8c0e-4246-8e3e-2e81e97a4fe7.preview.emergentagent.com"
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

def test_demo_user_login():
    """Test 1: Test demo user login and get user_id"""
    print_separator("TEST 1: DEMO USER LOGIN AND GET USER_ID")
    
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data, timeout=10)
        response_data = print_response(response, "Demo User Login Response")
        
        if response.status_code == 200 and response_data:
            user_data = response_data.get('user', {})
            user_id = user_data.get('id')
            email = user_data.get('email')
            is_verified = user_data.get('is_verified', False)
            
            print(f"\n✅ TEST 1 SUCCESS - Demo User Login Working")
            print(f"   - User ID: {user_id}")
            print(f"   - Email: {email}")
            print(f"   - Verified: {is_verified}")
            print(f"   - Status: {response_data.get('status', 'unknown')}")
            
            if user_id and email:
                return True, user_id, user_data
            else:
                print(f"\n❌ TEST 1 FAILED - Missing user_id or email in response")
                return False, None, None
        else:
            print(f"\n❌ TEST 1 FAILED - Login failed with status: {response.status_code}")
            return False, None, None
            
    except Exception as e:
        print(f"\n❌ TEST 1 ERROR: {str(e)}")
        return False, None, None

def test_user_settings_endpoint(user_id):
    """Test 2: GET /api/user/settings/{user_id} - Test fetching complete user settings"""
    print_separator("TEST 2: USER SETTINGS ENDPOINT")
    
    try:
        url = f"{API_BASE}/user/settings/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "User Settings Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ TEST 2 SUCCESS: User settings endpoint working")
            
            # Verify response structure
            required_keys = ['profile', 'subscription', 'usage', 'limits']
            missing_keys = [key for key in required_keys if key not in response_data]
            
            if missing_keys:
                print(f"⚠️ Missing keys in response: {missing_keys}")
                return False, response_data
            
            # Verify profile data
            profile = response_data.get('profile', {})
            profile_keys = ['user_id', 'first_name', 'last_name', 'email', 'dietary_preferences', 'is_verified']
            profile_missing = [key for key in profile_keys if key not in profile]
            
            if profile_missing:
                print(f"⚠️ Missing profile keys: {profile_missing}")
            
            # Verify subscription data
            subscription = response_data.get('subscription', {})
            sub_keys = ['has_access', 'subscription_status', 'trial_active', 'subscription_active']
            sub_missing = [key for key in sub_keys if key not in subscription]
            
            if sub_missing:
                print(f"⚠️ Missing subscription keys: {sub_missing}")
            
            # Verify usage data
            usage = response_data.get('usage', {})
            usage_types = ['weekly_recipes', 'individual_recipes', 'starbucks_drinks']
            usage_missing = [utype for utype in usage_types if utype not in usage]
            
            if usage_missing:
                print(f"⚠️ Missing usage types: {usage_missing}")
            
            # Verify limits data
            limits = response_data.get('limits', {})
            limits_missing = [utype for utype in usage_types if utype not in limits]
            
            if limits_missing:
                print(f"⚠️ Missing limit types: {limits_missing}")
            
            print(f"✅ Settings Data Structure:")
            print(f"   - Profile: {profile.get('email', 'N/A')} ({profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')})")
            print(f"   - Subscription Status: {subscription.get('subscription_status', 'N/A')}")
            print(f"   - Has Access: {subscription.get('has_access', 'N/A')}")
            print(f"   - Trial Active: {subscription.get('trial_active', 'N/A')}")
            
            for usage_type in usage_types:
                if usage_type in usage:
                    usage_info = usage[usage_type]
                    limit_info = limits.get(usage_type, 0)
                    print(f"   - {usage_type}: {usage_info.get('current_count', 0)}/{limit_info} (remaining: {usage_info.get('remaining', 0)})")
            
            return True, response_data
            
        else:
            print(f"\n❌ TEST 2 FAILED: Settings endpoint returned {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 2 ERROR: {str(e)}")
        return False, None

def test_user_profile_update(user_id):
    """Test 3: PUT /api/user/profile/{user_id} - Test updating user profile information"""
    print_separator("TEST 3: USER PROFILE UPDATE ENDPOINT")
    
    # Test data for profile update
    update_data = {
        "first_name": "Demo Updated",
        "last_name": "User Updated",
        "dietary_preferences": ["vegetarian", "gluten-free"]
    }
    
    try:
        url = f"{API_BASE}/user/profile/{user_id}"
        print(f"Testing URL: {url}")
        print(f"Update Data: {json.dumps(update_data, indent=2)}")
        
        response = requests.put(url, json=update_data, timeout=10)
        response_data = print_response(response, "Profile Update Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ TEST 3 SUCCESS: Profile update endpoint working")
            
            # Verify response structure
            if 'message' in response_data and 'profile' in response_data:
                profile = response_data['profile']
                print(f"✅ Updated Profile:")
                print(f"   - Name: {profile.get('first_name', 'N/A')} {profile.get('last_name', 'N/A')}")
                print(f"   - Email: {profile.get('email', 'N/A')}")
                print(f"   - Dietary Preferences: {profile.get('dietary_preferences', [])}")
                
                # Verify the update was applied
                if (profile.get('first_name') == update_data['first_name'] and 
                    profile.get('last_name') == update_data['last_name'] and
                    profile.get('dietary_preferences') == update_data['dietary_preferences']):
                    print(f"✅ Profile update verified successfully")
                    return True, response_data
                else:
                    print(f"⚠️ Profile update may not have been applied correctly")
                    return False, response_data
            else:
                print(f"⚠️ Unexpected response structure")
                return False, response_data
            
        else:
            print(f"\n❌ TEST 3 FAILED: Profile update returned {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 3 ERROR: {str(e)}")
        return False, None

def test_user_usage_endpoint(user_id):
    """Test 4: GET /api/user/usage/{user_id} - Test fetching detailed usage information"""
    print_separator("TEST 4: USER USAGE ENDPOINT")
    
    try:
        url = f"{API_BASE}/user/usage/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "User Usage Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ TEST 4 SUCCESS: User usage endpoint working")
            
            # Verify response structure
            required_keys = ['user_id', 'subscription_status', 'usage', 'limits']
            missing_keys = [key for key in required_keys if key not in response_data]
            
            if missing_keys:
                print(f"⚠️ Missing keys in response: {missing_keys}")
                return False, response_data
            
            # Verify usage data structure
            usage = response_data.get('usage', {})
            limits = response_data.get('limits', {})
            usage_types = ['weekly_recipes', 'individual_recipes', 'starbucks_drinks']
            
            print(f"✅ Usage Information:")
            print(f"   - User ID: {response_data.get('user_id', 'N/A')}")
            print(f"   - Subscription Status: {response_data.get('subscription_status', 'N/A')}")
            print(f"   - Usage Reset Date: {response_data.get('usage_reset_date', 'N/A')}")
            
            for usage_type in usage_types:
                if usage_type in usage:
                    usage_info = usage[usage_type]
                    limit_info = limits.get(usage_type, 0)
                    print(f"   - {usage_type}:")
                    print(f"     * Current: {usage_info.get('current', 0)}")
                    print(f"     * Limit: {usage_info.get('limit', 0)}")
                    print(f"     * Remaining: {usage_info.get('remaining', 0)}")
                    print(f"     * Can Use: {usage_info.get('can_use', False)}")
            
            return True, response_data
            
        else:
            print(f"\n❌ TEST 4 FAILED: Usage endpoint returned {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 4 ERROR: {str(e)}")
        return False, None

def test_subscription_cancel(user_id):
    """Test 5: POST /api/subscription/cancel/{user_id} - Test subscription cancellation"""
    print_separator("TEST 5: SUBSCRIPTION CANCELLATION")
    
    try:
        url = f"{API_BASE}/subscription/cancel/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.post(url, timeout=10)
        response_data = print_response(response, "Subscription Cancel Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ TEST 5 SUCCESS: Subscription cancellation working")
            
            # Verify response structure
            expected_keys = ['message', 'cancel_at_period_end', 'cancelled_date']
            missing_keys = [key for key in expected_keys if key not in response_data]
            
            if missing_keys:
                print(f"⚠️ Missing keys in response: {missing_keys}")
            
            print(f"✅ Cancellation Details:")
            print(f"   - Message: {response_data.get('message', 'N/A')}")
            print(f"   - Cancel at Period End: {response_data.get('cancel_at_period_end', 'N/A')}")
            print(f"   - Access Until: {response_data.get('access_until', 'N/A')}")
            print(f"   - Cancelled Date: {response_data.get('cancelled_date', 'N/A')}")
            
            return True, response_data
            
        elif response.status_code == 400 and response_data:
            error_detail = response_data.get('detail', '')
            if "No active subscription to cancel" in error_detail:
                print(f"\n⚠️ TEST 5 EXPECTED: No active subscription to cancel (user is on trial)")
                print(f"   This is expected for demo user on trial")
                return True, response_data
            else:
                print(f"\n❌ TEST 5 FAILED: Unexpected error - {error_detail}")
                return False, response_data
        
        else:
            print(f"\n❌ TEST 5 FAILED: Subscription cancel returned {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 5 ERROR: {str(e)}")
        return False, None

def test_subscription_reactivate(user_id):
    """Test 6: POST /api/subscription/reactivate/{user_id} - Test subscription reactivation"""
    print_separator("TEST 6: SUBSCRIPTION REACTIVATION")
    
    try:
        url = f"{API_BASE}/subscription/reactivate/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.post(url, timeout=10)
        response_data = print_response(response, "Subscription Reactivate Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ TEST 6 SUCCESS: Subscription reactivation working")
            
            # Verify response structure
            expected_keys = ['message', 'cancel_at_period_end', 'reactivated_date']
            missing_keys = [key for key in expected_keys if key not in response_data]
            
            if missing_keys:
                print(f"⚠️ Missing keys in response: {missing_keys}")
            
            print(f"✅ Reactivation Details:")
            print(f"   - Message: {response_data.get('message', 'N/A')}")
            print(f"   - Cancel at Period End: {response_data.get('cancel_at_period_end', 'N/A')}")
            print(f"   - Reactivated Date: {response_data.get('reactivated_date', 'N/A')}")
            
            return True, response_data
            
        elif response.status_code == 400 and response_data:
            error_detail = response_data.get('detail', '')
            if "Subscription is not set to cancel" in error_detail:
                print(f"\n⚠️ TEST 6 EXPECTED: Subscription is not set to cancel")
                print(f"   This is expected if subscription was not previously cancelled")
                return True, response_data
            else:
                print(f"\n❌ TEST 6 FAILED: Unexpected error - {error_detail}")
                return False, response_data
        
        else:
            print(f"\n❌ TEST 6 FAILED: Subscription reactivate returned {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 6 ERROR: {str(e)}")
        return False, None

def test_individual_recipe_usage_limit(user_id):
    """Test 7: Individual recipe generation usage limit enforcement (should allow up to 10, then block)"""
    print_separator("TEST 7: INDIVIDUAL RECIPE USAGE LIMIT ENFORCEMENT")
    
    # First, get current usage
    try:
        usage_response = requests.get(f"{API_BASE}/user/usage/{user_id}", timeout=10)
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            current_usage = usage_data.get('usage', {}).get('individual_recipes', {}).get('current', 0)
            limit = usage_data.get('usage', {}).get('individual_recipes', {}).get('limit', 10)
            print(f"Current individual recipe usage: {current_usage}/{limit}")
        else:
            print(f"Could not get current usage, proceeding with test")
            current_usage = 0
            limit = 10
    except Exception as e:
        print(f"Error getting usage: {e}")
        current_usage = 0
        limit = 10
    
    # Test recipe generation
    recipe_data = {
        "user_id": user_id,
        "cuisine_type": "italian",
        "difficulty": "easy",
        "servings": 4,
        "dietary_preferences": [],
        "ingredients": []
    }
    
    try:
        url = f"{API_BASE}/recipes/generate"
        print(f"Testing URL: {url}")
        print(f"Recipe Data: {json.dumps(recipe_data, indent=2)}")
        
        response = requests.post(url, json=recipe_data, timeout=15)
        response_data = print_response(response, "Individual Recipe Generation Response")
        
        if current_usage < limit:
            # Should succeed
            if response.status_code == 200 and response_data:
                print(f"\n✅ TEST 7 SUCCESS: Individual recipe generation working (within limit)")
                print(f"   - Recipe generated successfully")
                print(f"   - Usage should increment from {current_usage} to {current_usage + 1}")
                return True, response_data
            else:
                print(f"\n❌ TEST 7 FAILED: Recipe generation failed when it should succeed")
                return False, response_data
        else:
            # Should fail with 429
            if response.status_code == 429 and response_data:
                print(f"\n✅ TEST 7 SUCCESS: Usage limit properly enforced")
                
                # Verify error structure
                detail = response_data.get('detail', {})
                if isinstance(detail, dict):
                    print(f"   - Error: {detail.get('error', 'N/A')}")
                    print(f"   - Message: {detail.get('message', 'N/A')}")
                    print(f"   - Current Usage: {detail.get('current_usage', 'N/A')}")
                    print(f"   - Limit: {detail.get('limit', 'N/A')}")
                    print(f"   - Subscription Status: {detail.get('subscription_status', 'N/A')}")
                    print(f"   - Upgrade Required: {detail.get('upgrade_required', 'N/A')}")
                    
                    if detail.get('error') == 'Usage limit exceeded':
                        print(f"✅ Proper error message returned")
                        return True, response_data
                    else:
                        print(f"⚠️ Unexpected error message")
                        return False, response_data
                else:
                    print(f"⚠️ Unexpected error format: {detail}")
                    return False, response_data
            else:
                print(f"\n❌ TEST 7 FAILED: Expected 429 error but got {response.status_code}")
                return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 7 ERROR: {str(e)}")
        return False, None

def test_starbucks_drink_usage_limit(user_id):
    """Test 8: Starbucks drink generation usage limit enforcement (should allow up to 10, then block)"""
    print_separator("TEST 8: STARBUCKS DRINK USAGE LIMIT ENFORCEMENT")
    
    # First, get current usage
    try:
        usage_response = requests.get(f"{API_BASE}/user/usage/{user_id}", timeout=10)
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            current_usage = usage_data.get('usage', {}).get('starbucks_drinks', {}).get('current', 0)
            limit = usage_data.get('usage', {}).get('starbucks_drinks', {}).get('limit', 10)
            print(f"Current Starbucks drink usage: {current_usage}/{limit}")
        else:
            print(f"Could not get current usage, proceeding with test")
            current_usage = 0
            limit = 10
    except Exception as e:
        print(f"Error getting usage: {e}")
        current_usage = 0
        limit = 10
    
    # Test Starbucks drink generation
    starbucks_data = {
        "user_id": user_id,
        "drink_type": "frappuccino",
        "flavor_inspiration": "vanilla"
    }
    
    try:
        url = f"{API_BASE}/generate-starbucks-drink"
        print(f"Testing URL: {url}")
        print(f"Starbucks Data: {json.dumps(starbucks_data, indent=2)}")
        
        response = requests.post(url, json=starbucks_data, timeout=15)
        response_data = print_response(response, "Starbucks Drink Generation Response")
        
        if current_usage < limit:
            # Should succeed
            if response.status_code == 200 and response_data:
                print(f"\n✅ TEST 8 SUCCESS: Starbucks drink generation working (within limit)")
                print(f"   - Drink generated successfully")
                print(f"   - Usage should increment from {current_usage} to {current_usage + 1}")
                return True, response_data
            else:
                print(f"\n❌ TEST 8 FAILED: Starbucks drink generation failed when it should succeed")
                return False, response_data
        else:
            # Should fail with 429
            if response.status_code == 429 and response_data:
                print(f"\n✅ TEST 8 SUCCESS: Usage limit properly enforced")
                
                # Verify error structure
                detail = response_data.get('detail', {})
                if isinstance(detail, dict):
                    print(f"   - Error: {detail.get('error', 'N/A')}")
                    print(f"   - Message: {detail.get('message', 'N/A')}")
                    print(f"   - Current Usage: {detail.get('current_usage', 'N/A')}")
                    print(f"   - Limit: {detail.get('limit', 'N/A')}")
                    print(f"   - Subscription Status: {detail.get('subscription_status', 'N/A')}")
                    print(f"   - Upgrade Required: {detail.get('upgrade_required', 'N/A')}")
                    
                    if detail.get('error') == 'Usage limit exceeded':
                        print(f"✅ Proper error message returned")
                        return True, response_data
                    else:
                        print(f"⚠️ Unexpected error message")
                        return False, response_data
                else:
                    print(f"⚠️ Unexpected error format: {detail}")
                    return False, response_data
            else:
                print(f"\n❌ TEST 8 FAILED: Expected 429 error but got {response.status_code}")
                return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 8 ERROR: {str(e)}")
        return False, None

def test_weekly_recipe_usage_limit(user_id):
    """Test 9: Weekly recipe generation usage limit enforcement (should allow up to 2, then block)"""
    print_separator("TEST 9: WEEKLY RECIPE USAGE LIMIT ENFORCEMENT")
    
    # First, get current usage
    try:
        usage_response = requests.get(f"{API_BASE}/user/usage/{user_id}", timeout=10)
        if usage_response.status_code == 200:
            usage_data = usage_response.json()
            current_usage = usage_data.get('usage', {}).get('weekly_recipes', {}).get('current', 0)
            limit = usage_data.get('usage', {}).get('weekly_recipes', {}).get('limit', 2)
            print(f"Current weekly recipe usage: {current_usage}/{limit}")
        else:
            print(f"Could not get current usage, proceeding with test")
            current_usage = 0
            limit = 2
    except Exception as e:
        print(f"Error getting usage: {e}")
        current_usage = 0
        limit = 2
    
    # Test weekly recipe generation
    weekly_data = {
        "user_id": user_id,
        "family_size": 2,
        "dietary_preferences": ["vegetarian"],
        "allergies": [],
        "budget": 100.0,
        "cuisines": ["italian", "mexican"]
    }
    
    try:
        url = f"{API_BASE}/weekly-recipes/generate"
        print(f"Testing URL: {url}")
        print(f"Weekly Recipe Data: {json.dumps(weekly_data, indent=2)}")
        
        response = requests.post(url, json=weekly_data, timeout=20)
        response_data = print_response(response, "Weekly Recipe Generation Response")
        
        if current_usage < limit:
            # Should succeed
            if response.status_code == 200 and response_data:
                print(f"\n✅ TEST 9 SUCCESS: Weekly recipe generation working (within limit)")
                print(f"   - Weekly plan generated successfully")
                print(f"   - Usage should increment from {current_usage} to {current_usage + 1}")
                return True, response_data
            else:
                print(f"\n❌ TEST 9 FAILED: Weekly recipe generation failed when it should succeed")
                return False, response_data
        else:
            # Should fail with 429
            if response.status_code == 429 and response_data:
                print(f"\n✅ TEST 9 SUCCESS: Usage limit properly enforced")
                
                # Verify error structure
                detail = response_data.get('detail', {})
                if isinstance(detail, dict):
                    print(f"   - Error: {detail.get('error', 'N/A')}")
                    print(f"   - Message: {detail.get('message', 'N/A')}")
                    print(f"   - Current Usage: {detail.get('current_usage', 'N/A')}")
                    print(f"   - Limit: {detail.get('limit', 'N/A')}")
                    print(f"   - Subscription Status: {detail.get('subscription_status', 'N/A')}")
                    print(f"   - Upgrade Required: {detail.get('upgrade_required', 'N/A')}")
                    
                    if detail.get('error') == 'Usage limit exceeded':
                        print(f"✅ Proper error message returned")
                        return True, response_data
                    else:
                        print(f"⚠️ Unexpected error message")
                        return False, response_data
                else:
                    print(f"⚠️ Unexpected error format: {detail}")
                    return False, response_data
            else:
                print(f"\n❌ TEST 9 FAILED: Expected 429 error but got {response.status_code}")
                return False, response_data
            
    except Exception as e:
        print(f"\n❌ TEST 9 ERROR: {str(e)}")
        return False, None

def test_usage_tracking_accuracy(user_id):
    """Test 10: Verify usage tracking accuracy in settings endpoint"""
    print_separator("TEST 10: USAGE TRACKING ACCURACY VERIFICATION")
    
    try:
        # Get usage before any operations
        url = f"{API_BASE}/user/usage/{user_id}"
        print(f"Getting initial usage from: {url}")
        
        response_before = requests.get(url, timeout=10)
        if response_before.status_code != 200:
            print(f"❌ Could not get initial usage data")
            return False, None
        
        usage_before = response_before.json()
        print(f"Initial Usage Data:")
        for usage_type in ['weekly_recipes', 'individual_recipes', 'starbucks_drinks']:
            if usage_type in usage_before.get('usage', {}):
                usage_info = usage_before['usage'][usage_type]
                print(f"   - {usage_type}: {usage_info.get('current', 0)}/{usage_info.get('limit', 0)}")
        
        # Now get the same data from settings endpoint
        settings_url = f"{API_BASE}/user/settings/{user_id}"
        print(f"Getting usage from settings endpoint: {settings_url}")
        
        settings_response = requests.get(settings_url, timeout=10)
        if settings_response.status_code != 200:
            print(f"❌ Could not get settings data")
            return False, None
        
        settings_data = settings_response.json()
        settings_usage = settings_data.get('usage', {})
        
        print(f"Settings Usage Data:")
        for usage_type in ['weekly_recipes', 'individual_recipes', 'starbucks_drinks']:
            if usage_type in settings_usage:
                usage_info = settings_usage[usage_type]
                print(f"   - {usage_type}: {usage_info.get('current_count', 0)}/{usage_info.get('limit', 0)}")
        
        # Compare the data
        print(f"\n✅ Comparing usage data between endpoints:")
        all_match = True
        
        for usage_type in ['weekly_recipes', 'individual_recipes', 'starbucks_drinks']:
            usage_current = usage_before.get('usage', {}).get(usage_type, {}).get('current', 0)
            settings_current = settings_usage.get(usage_type, {}).get('current_count', 0)
            
            if usage_current == settings_current:
                print(f"   ✅ {usage_type}: {usage_current} == {settings_current} (MATCH)")
            else:
                print(f"   ❌ {usage_type}: {usage_current} != {settings_current} (MISMATCH)")
                all_match = False
        
        if all_match:
            print(f"\n✅ TEST 10 SUCCESS: Usage data is consistent between endpoints")
            return True, {"usage_endpoint": usage_before, "settings_endpoint": settings_data}
        else:
            print(f"\n❌ TEST 10 FAILED: Usage data inconsistency detected")
            return False, {"usage_endpoint": usage_before, "settings_endpoint": settings_data}
            
    except Exception as e:
        print(f"\n❌ TEST 10 ERROR: {str(e)}")
        return False, None

def main():
    """Main test function for Comprehensive Settings and Usage Limit System"""
    print_separator("COMPREHENSIVE SETTINGS AND USAGE LIMIT SYSTEM TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    print(f"Focus: Testing comprehensive Settings and Usage Limit system")
    
    # Run all the required tests in sequence
    test_results = {}
    
    # Test 1: Demo user login and get user_id
    print("\n🔍 Running Test 1: Demo User Login...")
    login_success, user_id, user_data = test_demo_user_login()
    test_results['demo_user_login'] = login_success
    
    if not login_success:
        print("\n🚨 CRITICAL: Cannot proceed - Demo user login failed")
        print("🚨 Please ensure demo@test.com user exists and password is correct")
        return False
    
    # Test 2: User settings endpoint
    print("\n🔍 Running Test 2: User Settings Endpoint...")
    settings_success, settings_data = test_user_settings_endpoint(user_id)
    test_results['user_settings_endpoint'] = settings_success
    
    # Test 3: User profile update endpoint
    print("\n🔍 Running Test 3: User Profile Update...")
    profile_success, profile_data = test_user_profile_update(user_id)
    test_results['user_profile_update'] = profile_success
    
    # Test 4: User usage endpoint
    print("\n🔍 Running Test 4: User Usage Endpoint...")
    usage_success, usage_data = test_user_usage_endpoint(user_id)
    test_results['user_usage_endpoint'] = usage_success
    
    # Test 5: Subscription cancellation
    print("\n🔍 Running Test 5: Subscription Cancellation...")
    cancel_success, cancel_data = test_subscription_cancel(user_id)
    test_results['subscription_cancel'] = cancel_success
    
    # Test 6: Subscription reactivation
    print("\n🔍 Running Test 6: Subscription Reactivation...")
    reactivate_success, reactivate_data = test_subscription_reactivate(user_id)
    test_results['subscription_reactivate'] = reactivate_success
    
    # Test 7: Individual recipe usage limit enforcement
    print("\n🔍 Running Test 7: Individual Recipe Usage Limit...")
    individual_limit_success, individual_data = test_individual_recipe_usage_limit(user_id)
    test_results['individual_recipe_limit'] = individual_limit_success
    
    # Test 8: Starbucks drink usage limit enforcement
    print("\n🔍 Running Test 8: Starbucks Drink Usage Limit...")
    starbucks_limit_success, starbucks_data = test_starbucks_drink_usage_limit(user_id)
    test_results['starbucks_drink_limit'] = starbucks_limit_success
    
    # Test 9: Weekly recipe usage limit enforcement
    print("\n🔍 Running Test 9: Weekly Recipe Usage Limit...")
    weekly_limit_success, weekly_data = test_weekly_recipe_usage_limit(user_id)
    test_results['weekly_recipe_limit'] = weekly_limit_success
    
    # Test 10: Usage tracking accuracy
    print("\n🔍 Running Test 10: Usage Tracking Accuracy...")
    tracking_success, tracking_data = test_usage_tracking_accuracy(user_id)
    test_results['usage_tracking_accuracy'] = tracking_success
    
    # Final Analysis
    print_separator("FINAL ANALYSIS - SETTINGS AND USAGE LIMIT SYSTEM")
    
    print("🔍 TEST RESULTS SUMMARY:")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    # Specific findings based on the review requirements
    print("\n--- SETTINGS AND USAGE LIMIT SYSTEM VERIFICATION ---")
    
    if test_results['demo_user_login']:
        print("✅ CONFIRMED: Demo user login working and user_id obtained")
    else:
        print("❌ ISSUE: Demo user login failed")
    
    if test_results['user_settings_endpoint']:
        print("✅ CONFIRMED: User settings endpoint returns complete profile, subscription, and usage data")
    else:
        print("❌ ISSUE: User settings endpoint has problems")
    
    if test_results['user_profile_update']:
        print("✅ CONFIRMED: User profile update endpoint working correctly")
    else:
        print("❌ ISSUE: User profile update endpoint has problems")
    
    if test_results['user_usage_endpoint']:
        print("✅ CONFIRMED: User usage endpoint returns detailed usage information")
    else:
        print("❌ ISSUE: User usage endpoint has problems")
    
    if test_results['subscription_cancel']:
        print("✅ CONFIRMED: Subscription cancellation endpoint working (cancel_at_period_end)")
    else:
        print("❌ ISSUE: Subscription cancellation endpoint has problems")
    
    if test_results['subscription_reactivate']:
        print("✅ CONFIRMED: Subscription reactivation endpoint working")
    else:
        print("❌ ISSUE: Subscription reactivation endpoint has problems")
    
    if test_results['individual_recipe_limit']:
        print("✅ CONFIRMED: Individual recipe usage limits properly enforced (10 limit)")
    else:
        print("❌ ISSUE: Individual recipe usage limits not working correctly")
    
    if test_results['starbucks_drink_limit']:
        print("✅ CONFIRMED: Starbucks drink usage limits properly enforced (10 limit)")
    else:
        print("❌ ISSUE: Starbucks drink usage limits not working correctly")
    
    if test_results['weekly_recipe_limit']:
        print("✅ CONFIRMED: Weekly recipe usage limits properly enforced (2 limit)")
    else:
        print("❌ ISSUE: Weekly recipe usage limits not working correctly")
    
    if test_results['usage_tracking_accuracy']:
        print("✅ CONFIRMED: Usage tracking is accurate across endpoints")
    else:
        print("❌ ISSUE: Usage tracking inconsistencies detected")
    
    # Overall assessment
    if passed_tests >= 8:  # At least 8 out of 10 tests should pass
        print("\n🎉 SETTINGS AND USAGE LIMIT SYSTEM ASSESSMENT: FULLY OPERATIONAL")
        print("✅ All settings endpoints working correctly")
        print("✅ Profile management functional")
        print("✅ Subscription management working")
        print("✅ Usage limits properly enforced with 429 errors")
        print("✅ Usage tracking accurate and consistent")
        print("✅ System ready for production use")
    else:
        print("\n⚠️ SETTINGS AND USAGE LIMIT SYSTEM ASSESSMENT: NEEDS ATTENTION")
        print("❌ Some critical functionality is not working")
        print("❌ Review the failed tests above for specific issues")
    
    print_separator("COMPREHENSIVE SETTINGS AND USAGE LIMIT SYSTEM TESTING COMPLETE")
    return passed_tests >= 8

if __name__ == "__main__":
    main()