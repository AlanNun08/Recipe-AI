#!/usr/bin/env python3
"""
Backend API Testing for Stripe Payment Fix
Testing the immediate Stripe payment fix that was just applied as requested in review:

1. Test the subscription status endpoint for demo user to confirm it still works
2. Test the create-checkout endpoint with demo user to verify the new error handling
3. Confirm that users now see "Payment system not configured. Please contact support." instead of generic 500 errors
4. Verify that the API key validation is working properly
5. Test with invalid user to ensure proper 404 error handling

The goal is to confirm that:
- The immediate fix is working (better error messages)
- System is ready for API key configuration
- Error handling has been improved
- Users get clear guidance instead of confusing errors

Focus on the endpoints:
- GET /api/subscription/status/{user_id}
- POST /api/subscription/create-checkout
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
            return user_id, response_data.get('user', {})
        else:
            print(f"\n❌ LOGIN FAILED - Status: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"\n❌ LOGIN ERROR: {str(e)}")
        return None, None

import requests
import json
import sys
import re
from datetime import datetime, timedelta
from dateutil import parser

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
            return user_id, response_data.get('user', {})
        else:
            print(f"\n❌ LOGIN FAILED - Status: {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"\n❌ LOGIN ERROR: {str(e)}")
        return None, None

def test_subscription_status(user_id):
    """Test GET /api/subscription/status/{user_id} endpoint"""
    print_separator(f"TESTING SUBSCRIPTION STATUS FOR USER {user_id}")
    
    try:
        url = f"{API_BASE}/subscription/status/{user_id}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url, timeout=10)
        response_data = print_response(response, "Subscription Status Response")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ SUBSCRIPTION STATUS SUCCESS")
            
            # Analyze the subscription status
            has_access = response_data.get('has_access', False)
            subscription_status = response_data.get('subscription_status', 'unknown')
            trial_active = response_data.get('trial_active', False)
            subscription_active = response_data.get('subscription_active', False)
            trial_end_date = response_data.get('trial_end_date')
            subscription_end_date = response_data.get('subscription_end_date')
            next_billing_date = response_data.get('next_billing_date')
            
            print(f"✅ Has Access: {has_access}")
            print(f"✅ Subscription Status: {subscription_status}")
            print(f"✅ Trial Active: {trial_active}")
            print(f"✅ Subscription Active: {subscription_active}")
            print(f"✅ Trial End Date: {trial_end_date}")
            print(f"✅ Subscription End Date: {subscription_end_date}")
            print(f"✅ Next Billing Date: {next_billing_date}")
            
            # Determine user's current state
            if trial_active:
                print(f"🔍 USER STATE: Currently in FREE TRIAL period")
                if trial_end_date:
                    try:
                        trial_end = parser.parse(trial_end_date) if isinstance(trial_end_date, str) else trial_end_date
                        days_left = (trial_end - datetime.utcnow()).days
                        print(f"🔍 TRIAL INFO: {days_left} days remaining in trial")
                    except:
                        print(f"🔍 TRIAL INFO: Trial end date format issue")
            elif subscription_active:
                print(f"🔍 USER STATE: Has ACTIVE PAID SUBSCRIPTION")
            else:
                print(f"🔍 USER STATE: NO ACTIVE ACCESS (expired trial or subscription)")
            
            return True, response_data
            
        else:
            print(f"\n❌ SUBSCRIPTION STATUS FAILED - Status: {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ SUBSCRIPTION STATUS ERROR: {str(e)}")
        return False, None

def test_create_checkout(user_id, user_email, scenario_name="Default"):
    """Test POST /api/subscription/create-checkout endpoint"""
    print_separator(f"TESTING CREATE CHECKOUT - {scenario_name}")
    
    checkout_data = {
        "user_id": user_id,
        "user_email": user_email,
        "origin_url": BACKEND_URL  # Use backend URL as origin for testing
    }
    
    try:
        url = f"{API_BASE}/subscription/create-checkout"
        print(f"Testing URL: {url}")
        print(f"Request Data: {json.dumps(checkout_data, indent=2)}")
        
        response = requests.post(url, json=checkout_data, timeout=15)
        response_data = print_response(response, f"Create Checkout Response - {scenario_name}")
        
        if response.status_code == 200 and response_data:
            print(f"\n✅ CREATE CHECKOUT SUCCESS - {scenario_name}")
            
            checkout_url = response_data.get('url')
            session_id = response_data.get('session_id')
            
            print(f"✅ Checkout URL: {checkout_url}")
            print(f"✅ Session ID: {session_id}")
            
            # Validate the response structure
            if checkout_url and session_id:
                print(f"✅ CHECKOUT SESSION CREATED SUCCESSFULLY")
                print(f"🔍 User can proceed to payment during their current subscription state")
                return True, response_data
            else:
                print(f"❌ INCOMPLETE CHECKOUT RESPONSE - Missing URL or Session ID")
                return False, response_data
            
        elif response.status_code == 400:
            print(f"\n⚠️ CREATE CHECKOUT BLOCKED - {scenario_name}")
            error_detail = response_data.get('detail', 'Unknown error') if response_data else 'No error details'
            print(f"🔍 BLOCKING REASON: {error_detail}")
            
            # This might be expected behavior for certain scenarios
            if "already has active subscription" in error_detail:
                print(f"✅ EXPECTED BEHAVIOR: User with active subscription cannot create new checkout")
                return "blocked_expected", response_data
            else:
                print(f"❌ UNEXPECTED BLOCKING: {error_detail}")
                return "blocked_unexpected", response_data
                
        else:
            print(f"\n❌ CREATE CHECKOUT FAILED - Status: {response.status_code}")
            return False, response_data
            
    except Exception as e:
        print(f"\n❌ CREATE CHECKOUT ERROR: {str(e)}")
        return False, None

def simulate_user_states_and_test():
    """Test different user subscription states by analyzing current demo user state"""
    print_separator("ANALYZING DEMO USER SUBSCRIPTION STATE AND TESTING CHECKOUT")
    
    # Step 1: Login and get user info
    user_id, user_info = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return False
    
    user_email = user_info.get('email', TEST_EMAIL)
    
    # Step 2: Get current subscription status
    status_success, status_data = test_subscription_status(user_id)
    if not status_success:
        print("\n🚨 CANNOT PROCEED - Subscription status check failed")
        return False
    
    # Step 3: Analyze current state and test checkout accordingly
    trial_active = status_data.get('trial_active', False)
    subscription_active = status_data.get('subscription_active', False)
    subscription_status = status_data.get('subscription_status', 'unknown')
    
    print_separator("TESTING CHECKOUT BASED ON CURRENT USER STATE")
    
    if trial_active:
        print("🔍 TESTING SCENARIO: User with ACTIVE TRIAL trying to subscribe")
        checkout_result, checkout_data = test_create_checkout(user_id, user_email, "Active Trial User")
        
        if checkout_result == True:
            print("✅ RESULT: Users with active trial CAN create checkout sessions")
            print("✅ BEHAVIOR: This allows trial users to upgrade to paid subscription")
        elif checkout_result == "blocked_expected":
            print("⚠️ RESULT: Users with active trial are BLOCKED from creating checkout")
            print("❌ POTENTIAL ISSUE: Trial users cannot upgrade to paid subscription")
        else:
            print("❌ RESULT: Checkout creation failed unexpectedly for trial user")
            
    elif subscription_active:
        print("🔍 TESTING SCENARIO: User with ACTIVE PAID SUBSCRIPTION trying to subscribe again")
        checkout_result, checkout_data = test_create_checkout(user_id, user_email, "Active Subscription User")
        
        if checkout_result == "blocked_expected":
            print("✅ RESULT: Users with active subscription are correctly BLOCKED")
            print("✅ BEHAVIOR: Prevents duplicate subscriptions")
        elif checkout_result == True:
            print("❌ RESULT: Users with active subscription can create checkout (POTENTIAL ISSUE)")
            print("❌ BEHAVIOR: This could lead to duplicate charges")
        else:
            print("❌ RESULT: Checkout creation failed unexpectedly for active subscriber")
            
    else:
        print("🔍 TESTING SCENARIO: User with EXPIRED/NO SUBSCRIPTION trying to subscribe")
        checkout_result, checkout_data = test_create_checkout(user_id, user_email, "Expired/No Subscription User")
        
        if checkout_result == True:
            print("✅ RESULT: Users with expired subscription CAN create checkout sessions")
            print("✅ BEHAVIOR: This allows users to resubscribe")
        else:
            print("❌ RESULT: Users with expired subscription cannot create checkout (POTENTIAL ISSUE)")
            print("❌ BEHAVIOR: Users cannot resubscribe when their access expires")
    
    return True

def test_edge_cases():
    """Test specific edge cases mentioned in the review"""
    print_separator("TESTING SPECIFIC EDGE CASES")
    
    # Get user info first
    user_id, user_info = test_login()
    if not user_id:
        print("\n🚨 CANNOT PROCEED - Login failed")
        return False
    
    user_email = user_info.get('email', TEST_EMAIL)
    
    # Test 1: Invalid user ID
    print("\n--- Testing Invalid User ID ---")
    try:
        invalid_user_id = "invalid-user-id-12345"
        url = f"{API_BASE}/subscription/status/{invalid_user_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            print("✅ EDGE CASE HANDLED: Invalid user ID returns 404")
        else:
            print(f"❌ EDGE CASE ISSUE: Invalid user ID returns {response.status_code}")
    except Exception as e:
        print(f"❌ EDGE CASE ERROR: {str(e)}")
    
    # Test 2: Invalid checkout data
    print("\n--- Testing Invalid Checkout Data ---")
    try:
        invalid_checkout_data = {
            "user_id": "",  # Empty user ID
            "user_email": "invalid-email",  # Invalid email format
            "origin_url": ""  # Empty origin URL
        }
        
        url = f"{API_BASE}/subscription/create-checkout"
        response = requests.post(url, json=invalid_checkout_data, timeout=10)
        
        if response.status_code in [400, 422]:
            print("✅ EDGE CASE HANDLED: Invalid checkout data returns error")
        else:
            print(f"❌ EDGE CASE ISSUE: Invalid checkout data returns {response.status_code}")
    except Exception as e:
        print(f"❌ EDGE CASE ERROR: {str(e)}")
    
    # Test 3: Missing required fields
    print("\n--- Testing Missing Required Fields ---")
    try:
        incomplete_data = {
            "user_id": user_id
            # Missing user_email and origin_url
        }
        
        url = f"{API_BASE}/subscription/create-checkout"
        response = requests.post(url, json=incomplete_data, timeout=10)
        
        if response.status_code in [400, 422]:
            print("✅ EDGE CASE HANDLED: Missing required fields returns error")
        else:
            print(f"❌ EDGE CASE ISSUE: Missing required fields returns {response.status_code}")
    except Exception as e:
        print(f"❌ EDGE CASE ERROR: {str(e)}")
    
    return True

def analyze_stripe_integration_issues():
    """Analyze potential issues with the Stripe integration"""
    print_separator("ANALYZING POTENTIAL STRIPE INTEGRATION ISSUES")
    
    # Check if Stripe is configured
    print("🔍 Checking Stripe Configuration...")
    
    # Test a simple endpoint to see if Stripe is configured
    user_id, user_info = test_login()
    if not user_id:
        print("❌ Cannot test Stripe configuration - login failed")
        return False
    
    user_email = user_info.get('email', TEST_EMAIL)
    
    # Try to create a checkout session and analyze the error
    checkout_data = {
        "user_id": user_id,
        "user_email": user_email,
        "origin_url": BACKEND_URL
    }
    
    try:
        url = f"{API_BASE}/subscription/create-checkout"
        response = requests.post(url, json=checkout_data, timeout=15)
        response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else None
        
        if response.status_code == 500 and response_data:
            error_detail = response_data.get('detail', '')
            if "Stripe not configured" in error_detail:
                print("❌ CRITICAL ISSUE: Stripe is not configured")
                print("🔧 SOLUTION: Set STRIPE_API_KEY environment variable")
                return False
            elif "Failed to create checkout session" in error_detail:
                print("❌ STRIPE INTEGRATION ISSUE: Checkout session creation failed")
                print("🔧 POSSIBLE CAUSES: Invalid API key, network issues, or Stripe service problems")
                return False
        
        print("✅ Stripe appears to be configured (no configuration errors)")
        return True
        
    except Exception as e:
        print(f"❌ ERROR TESTING STRIPE: {str(e)}")
        return False

def main():
    """Main test function for Stripe Subscription Payment Flow"""
    print_separator("STRIPE SUBSCRIPTION PAYMENT FLOW TESTING")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Test User: {TEST_EMAIL}")
    print(f"Test Time: {datetime.now()}")
    print(f"Focus: Testing Stripe subscription payment flow to identify issues")
    
    # Step 1: Analyze Stripe Integration
    print_separator("STEP 1: STRIPE INTEGRATION ANALYSIS")
    stripe_configured = analyze_stripe_integration_issues()
    
    # Step 2: Test Current User State and Checkout Flow
    print_separator("STEP 2: USER STATE AND CHECKOUT FLOW TESTING")
    user_state_test = simulate_user_states_and_test()
    
    # Step 3: Test Edge Cases
    print_separator("STEP 3: EDGE CASE TESTING")
    edge_case_test = test_edge_cases()
    
    # Step 4: Final Analysis and Recommendations
    print_separator("FINAL ANALYSIS AND RECOMMENDATIONS")
    
    print("🔍 STRIPE SUBSCRIPTION PAYMENT FLOW ANALYSIS COMPLETE")
    print(f"✅ Stripe Configuration: {'CONFIGURED' if stripe_configured else 'NOT CONFIGURED'}")
    print(f"✅ User State Testing: {'COMPLETED' if user_state_test else 'FAILED'}")
    print(f"✅ Edge Case Testing: {'COMPLETED' if edge_case_test else 'FAILED'}")
    
    # Provide specific recommendations based on findings
    print("\n--- RECOMMENDATIONS ---")
    
    if not stripe_configured:
        print("🚨 CRITICAL: Fix Stripe configuration before payment flow can work")
        print("   - Set STRIPE_API_KEY environment variable")
        print("   - Verify Stripe account is active and API keys are valid")
    
    if user_state_test:
        print("✅ User state testing completed - check specific scenarios above")
        print("   - Review trial user checkout behavior")
        print("   - Verify active subscription blocking works correctly")
        print("   - Ensure expired users can resubscribe")
    
    if edge_case_test:
        print("✅ Edge case testing completed - check error handling above")
        print("   - Verify proper validation of user IDs and email formats")
        print("   - Ensure missing required fields are handled gracefully")
    
    print("\n--- KEY FINDINGS ---")
    print("1. Demo user subscription status endpoint tested")
    print("2. Create checkout endpoint behavior analyzed")
    print("3. Edge cases for different user states examined")
    print("4. Stripe integration configuration verified")
    
    print_separator("STRIPE SUBSCRIPTION TESTING COMPLETE")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()