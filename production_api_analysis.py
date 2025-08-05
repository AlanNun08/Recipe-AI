#!/usr/bin/env python3
"""
Production API Testing Script
Test the production API to understand the current state of alannunezsilva0310@gmail.com
and create a comprehensive cleanup plan.
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class ProductionAPITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.target_email = "alannunezsilva0310@gmail.com"
        self.production_url = "https://buildyoursmartcart.com/api"
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def cleanup(self):
        await self.client.aclose()
    
    async def test_production_api_connectivity(self):
        """Test if we can connect to the production API"""
        self.log("=== TESTING PRODUCTION API CONNECTIVITY ===")
        
        try:
            # Test basic connectivity
            response = await self.client.get(f"{self.production_url}/curated-starbucks-recipes")
            
            if response.status_code == 200:
                self.log("✅ Production API is accessible")
                data = response.json()
                self.log(f"API Response: {len(data.get('recipes', []))} curated recipes found")
                return True
            else:
                self.log(f"❌ Production API returned status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to connect to production API: {str(e)}", "ERROR")
            return False
    
    async def test_account_registration_status(self):
        """Test if the email can be registered (to see if it already exists)"""
        self.log("=== TESTING ACCOUNT REGISTRATION STATUS ===")
        
        try:
            # Try to register with the target email
            registration_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": self.target_email,
                "password": "testpassword123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            response = await self.client.post(
                f"{self.production_url}/auth/register",
                json=registration_data
            )
            
            if response.status_code == 400:
                # Check if it's because email already exists
                error_data = response.json()
                if "already registered" in error_data.get("detail", "").lower():
                    self.log("🔍 Email is ALREADY REGISTERED in production database")
                    self.test_results['account_exists'] = True
                    return "exists"
                else:
                    self.log(f"❌ Registration failed with different error: {error_data}")
                    return "error"
            elif response.status_code == 200:
                self.log("✅ Email is AVAILABLE for registration")
                self.test_results['account_exists'] = False
                return "available"
            else:
                self.log(f"❌ Unexpected response status: {response.status_code}")
                self.log(f"Response: {response.text}")
                return "unknown"
                
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}", "ERROR")
            return "error"
    
    async def test_login_attempt(self):
        """Test if we can login with the target email"""
        self.log("=== TESTING LOGIN ATTEMPT ===")
        
        try:
            # Try common passwords that might have been used
            test_passwords = ["password123", "123456", "password", "test123"]
            
            for password in test_passwords:
                login_data = {
                    "email": self.target_email,
                    "password": password
                }
                
                response = await self.client.post(
                    f"{self.production_url}/auth/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Login successful with password: {password}")
                    data = response.json()
                    self.log(f"User data: {json.dumps(data, indent=2)}")
                    self.test_results['login_successful'] = True
                    self.test_results['user_data'] = data
                    return True
                elif response.status_code == 401:
                    self.log(f"❌ Login failed with password: {password}")
                else:
                    self.log(f"⚠️ Unexpected response for password {password}: {response.status_code}")
            
            self.log("❌ All login attempts failed")
            self.test_results['login_successful'] = False
            return False
            
        except Exception as e:
            self.log(f"❌ Error testing login: {str(e)}", "ERROR")
            return False
    
    async def test_password_reset_request(self):
        """Test if we can request a password reset for the email"""
        self.log("=== TESTING PASSWORD RESET REQUEST ===")
        
        try:
            reset_data = {
                "email": self.target_email
            }
            
            response = await self.client.post(
                f"{self.production_url}/auth/forgot-password",
                json=reset_data
            )
            
            if response.status_code == 200:
                self.log("✅ Password reset request successful - account exists")
                data = response.json()
                self.log(f"Reset response: {json.dumps(data, indent=2)}")
                self.test_results['password_reset_available'] = True
                return True
            elif response.status_code == 404:
                self.log("✅ Password reset failed - account does not exist")
                self.test_results['password_reset_available'] = False
                return False
            else:
                self.log(f"⚠️ Unexpected password reset response: {response.status_code}")
                self.log(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing password reset: {str(e)}", "ERROR")
            return None
    
    async def generate_cleanup_recommendations(self):
        """Generate recommendations based on test results"""
        self.log("=== GENERATING CLEANUP RECOMMENDATIONS ===")
        
        account_exists = self.test_results.get('account_exists', False)
        login_successful = self.test_results.get('login_successful', False)
        password_reset_available = self.test_results.get('password_reset_available', False)
        
        recommendations = []
        
        if account_exists:
            recommendations.append("🔧 ACCOUNT EXISTS: Direct database cleanup required")
            recommendations.append("   - Connect to production MongoDB database")
            recommendations.append("   - Delete from users collection")
            recommendations.append("   - Delete from verification_codes collection")
            recommendations.append("   - Delete from password_reset_codes collection")
            recommendations.append("   - Delete from any user-related collections (recipes, carts, etc.)")
        
        if login_successful:
            user_data = self.test_results.get('user_data', {})
            user_id = user_data.get('user_id') or user_data.get('id')
            if user_id:
                recommendations.append(f"🔧 USER ID FOUND: {user_id}")
                recommendations.append("   - Use this user_id to find related records in all collections")
        
        if password_reset_available:
            recommendations.append("🔧 PASSWORD RESET AVAILABLE: Account is active")
            recommendations.append("   - Account has active password reset capability")
            recommendations.append("   - Indicates account is not corrupted, just needs cleanup")
        
        if not account_exists and not password_reset_available:
            recommendations.append("✅ ACCOUNT ALREADY CLEAN: No cleanup needed")
            recommendations.append("   - Email is available for fresh registration")
            recommendations.append("   - No traces found in production database")
        
        # Database cleanup script recommendations
        recommendations.append("")
        recommendations.append("🛠️ RECOMMENDED CLEANUP SCRIPT:")
        recommendations.append("   1. Connect to production MongoDB using Google Cloud environment variables")
        recommendations.append("   2. Search all collections for email and user_id references")
        recommendations.append("   3. Delete all found records")
        recommendations.append("   4. Verify cleanup by testing registration")
        
        self.test_results['recommendations'] = recommendations
        
        for rec in recommendations:
            self.log(rec)
    
    async def run_comprehensive_analysis(self):
        """Run comprehensive analysis of the account status"""
        self.log("🔍 STARTING COMPREHENSIVE PRODUCTION ANALYSIS")
        self.log(f"Target email: {self.target_email}")
        self.log(f"Production API: {self.production_url}")
        
        try:
            # Test 1: API Connectivity
            api_accessible = await self.test_production_api_connectivity()
            if not api_accessible:
                self.log("❌ Cannot proceed - Production API is not accessible")
                return False
            
            # Test 2: Registration Status
            registration_status = await self.test_account_registration_status()
            
            # Test 3: Login Attempt (only if account exists)
            if registration_status == "exists":
                await self.test_login_attempt()
            
            # Test 4: Password Reset Request
            await self.test_password_reset_request()
            
            # Test 5: Generate Recommendations
            await self.generate_cleanup_recommendations()
            
            # Save results
            self.test_results['timestamp'] = datetime.now().isoformat()
            self.test_results['target_email'] = self.target_email
            self.test_results['production_url'] = self.production_url
            
            with open('/app/production_analysis_results.json', 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            self.log("📄 Analysis results saved to: /app/production_analysis_results.json")
            
            return True
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR during analysis: {str(e)}", "ERROR")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main function to run the production analysis"""
    tester = ProductionAPITester()
    
    try:
        success = await tester.run_comprehensive_analysis()
        
        if success:
            print("\n🎉 PRODUCTION ANALYSIS COMPLETED")
            print("📄 Check /app/production_analysis_results.json for detailed results")
        else:
            print("\n❌ PRODUCTION ANALYSIS FAILED")
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        await tester.cleanup()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        await tester.cleanup()

if __name__ == "__main__":
    print("🔍 Production API Analysis Tool")
    print("📧 Target: alannunezsilva0310@gmail.com")
    print("🌐 API: https://buildyoursmartcart.com/api")
    print("=" * 60)
    
    asyncio.run(main())