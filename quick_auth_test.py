#!/usr/bin/env python3
"""
Quick Backend Authentication Flow Verification
Testing additional authentication scenarios to ensure robustness
"""

import asyncio
import httpx
import json
from datetime import datetime

BACKEND_URL = 'http://localhost:8001'

class QuickAuthTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_demo_user_login(self):
        """Test demo user login"""
        self.log("=== Testing Demo User Login ===")
        
        login_data = {
            "email": "demo@test.com",
            "password": "password123"
        }
        
        response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Demo user login successful")
            self.log(f"   Status: {result.get('status')}")
            self.log(f"   User ID: {result.get('user_id')}")
            self.log(f"   Is Verified: {result.get('user', {}).get('is_verified')}")
            return True
        else:
            self.log(f"❌ Demo user login failed: {response.status_code} - {response.text}")
            return False
    
    async def test_subscription_status(self):
        """Test subscription status endpoint"""
        self.log("=== Testing Subscription Status ===")
        
        user_id = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"  # Demo user ID
        
        response = await self.client.get(f"{BACKEND_URL}/subscription/status/{user_id}")
        
        if response.status_code == 200:
            result = response.json()
            self.log(f"✅ Subscription status retrieved")
            self.log(f"   Has Access: {result.get('has_access')}")
            self.log(f"   Trial Active: {result.get('trial_active')}")
            self.log(f"   Subscription Status: {result.get('subscription_status')}")
            return True
        else:
            self.log(f"❌ Subscription status failed: {response.status_code} - {response.text}")
            return False
    
    async def test_curated_recipes(self):
        """Test curated Starbucks recipes endpoint"""
        self.log("=== Testing Curated Starbucks Recipes ===")
        
        response = await self.client.get(f"{BACKEND_URL}/curated-starbucks-recipes")
        
        if response.status_code == 200:
            result = response.json()
            recipes = result.get('recipes', [])
            self.log(f"✅ Curated recipes retrieved")
            self.log(f"   Total recipes: {len(recipes)}")
            if recipes:
                self.log(f"   First recipe: {recipes[0].get('name')}")
            return True
        else:
            self.log(f"❌ Curated recipes failed: {response.status_code} - {response.text}")
            return False
    
    async def run_quick_tests(self):
        """Run quick authentication and endpoint tests"""
        self.log("🚀 STARTING QUICK BACKEND AUTHENTICATION TESTS")
        self.log("=" * 60)
        
        test_results = {}
        
        # Test 1: Demo user login
        test_results["demo_login"] = await self.test_demo_user_login()
        
        # Test 2: Subscription status
        test_results["subscription_status"] = await self.test_subscription_status()
        
        # Test 3: Curated recipes
        test_results["curated_recipes"] = await self.test_curated_recipes()
        
        # Summary
        self.log("=" * 60)
        self.log("🔍 QUICK TEST RESULTS")
        self.log("=" * 60)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.upper()}: {status}")
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        self.log("=" * 60)
        if passed_tests == total_tests:
            self.log(f"🎉 ALL {total_tests} TESTS PASSED - Backend authentication working correctly")
        else:
            self.log(f"⚠️  {passed_tests}/{total_tests} TESTS PASSED")
        
        return test_results

async def main():
    """Main test execution"""
    tester = QuickAuthTester()
    
    try:
        results = await tester.run_quick_tests()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())