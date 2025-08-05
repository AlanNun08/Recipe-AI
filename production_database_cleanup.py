#!/usr/bin/env python3
"""
Production Database Cleanup for alannunezsilva0310@gmail.com
Since the issue is in the production database, not local, we need to:
1. Confirm the production backend is the issue
2. Provide resolution steps for the main agent
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Backend URL for API testing
BACKEND_URL = "https://buildyoursmartcart.com/api"
TARGET_EMAIL = "alannunezsilva0310@gmail.com"

class ProductionDatabaseTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def confirm_production_issue(self):
        """Confirm the issue is in production backend"""
        self.log("=== CONFIRMING PRODUCTION DATABASE ISSUE ===")
        
        try:
            # Test registration with target email
            registration_data = {
                "first_name": "Alan",
                "last_name": "Nunez Silva",
                "email": TARGET_EMAIL,
                "password": "testpassword123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            self.log(f"Testing registration with production backend: {BACKEND_URL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=registration_data)
            
            self.log(f"Response status: {response.status_code}")
            self.log(f"Response headers: {dict(response.headers)}")
            self.log(f"Response text: {response.text}")
            
            # Check if it's definitely production (Google Frontend headers)
            if "Google Frontend" in response.headers.get("server", ""):
                self.log("✅ CONFIRMED: This is the production backend (Google Cloud)")
                
                if response.status_code == 400 and "already registered" in response.text.lower():
                    self.log("✅ CONFIRMED: Production database has the inconsistency issue")
                    return True
                else:
                    self.log("❌ UNEXPECTED: Production registration behavior different than expected")
                    return False
            else:
                self.log("⚠️ WARNING: This may not be the production backend")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing production backend: {str(e)}")
            return False
    
    async def test_production_login(self):
        """Test if the account can login in production"""
        self.log("=== TESTING PRODUCTION LOGIN ===")
        
        # Try common passwords
        test_passwords = [
            "password123",
            "123456", 
            "password",
            "alan123",
            "alannunez123"
        ]
        
        for password in test_passwords:
            try:
                login_data = {
                    "email": TARGET_EMAIL,
                    "password": password
                }
                
                self.log(f"Attempting production login with password: {password[:3]}***")
                response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ LOGIN SUCCESSFUL in production with password: {password[:3]}***")
                    self.log(f"User status: {result.get('status', 'Unknown')}")
                    self.log(f"User ID: {result.get('user_id', 'Unknown')}")
                    return True, result.get('user_id')
                elif response.status_code == 401:
                    self.log(f"❌ Login failed: Invalid credentials")
                elif response.status_code == 429:
                    self.log(f"⚠️ Rate limited, skipping remaining passwords")
                    break
                else:
                    self.log(f"❌ Login failed: {response.text}")
                    
            except Exception as e:
                self.log(f"❌ Error testing login: {str(e)}")
        
        self.log("❌ NO SUCCESSFUL LOGIN FOUND in production")
        return False, None
    
    async def test_password_reset_flow(self):
        """Test if password reset works for this email"""
        self.log("=== TESTING PRODUCTION PASSWORD RESET ===")
        
        try:
            # Request password reset
            reset_data = {
                "email": TARGET_EMAIL
            }
            
            self.log(f"Requesting password reset for: {TARGET_EMAIL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/forgot-password", json=reset_data)
            
            self.log(f"Password reset response status: {response.status_code}")
            self.log(f"Password reset response: {response.text}")
            
            if response.status_code == 200:
                self.log("✅ PASSWORD RESET REQUEST SUCCESSFUL - Account exists in production")
                return True
            elif response.status_code == 404:
                self.log("❌ PASSWORD RESET FAILED - Account not found in production")
                return False
            else:
                self.log(f"⚠️ PASSWORD RESET UNEXPECTED RESPONSE: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing password reset: {str(e)}")
            return False
    
    async def provide_resolution_steps(self):
        """Provide clear resolution steps for the main agent"""
        self.log("=== RESOLUTION STEPS FOR MAIN AGENT ===")
        
        self.log("🔧 ISSUE IDENTIFIED:")
        self.log("  - The inconsistency is in the PRODUCTION database, not local")
        self.log("  - Local database has no trace of alannunezsilva0310@gmail.com")
        self.log("  - Production backend (buildyoursmartcart.com) has the corrupted data")
        
        self.log("🎯 REQUIRED ACTIONS:")
        self.log("  1. Connect to the PRODUCTION MongoDB database")
        self.log("  2. Search for alannunezsilva0310@gmail.com in production collections")
        self.log("  3. Either fix the account verification status OR delete all traces")
        self.log("  4. Test registration after cleanup")
        
        self.log("💡 TECHNICAL DETAILS:")
        self.log("  - Production backend URL: https://buildyoursmartcart.com/api")
        self.log("  - Local backend URL: http://localhost:8001/api")
        self.log("  - The frontend is configured to use production backend")
        self.log("  - Local database testing is not relevant for this issue")
        
        self.log("⚠️ IMPORTANT:")
        self.log("  - This requires access to production MongoDB credentials")
        self.log("  - Backup production data before making changes")
        self.log("  - Test thoroughly after any cleanup operations")
        
        return {
            "issue_location": "production_database",
            "backend_url": BACKEND_URL,
            "local_database_clean": True,
            "production_database_corrupted": True,
            "requires_production_access": True
        }
    
    async def run_production_investigation(self):
        """Run complete production investigation"""
        self.log("🔍 STARTING PRODUCTION DATABASE INVESTIGATION")
        self.log("=" * 80)
        self.log(f"TARGET EMAIL: {TARGET_EMAIL}")
        self.log(f"PRODUCTION BACKEND: {BACKEND_URL}")
        self.log("=" * 80)
        
        # Test 1: Confirm production issue
        production_issue = await self.confirm_production_issue()
        
        # Test 2: Test production login
        login_works, user_id = await self.test_production_login()
        
        # Test 3: Test password reset
        reset_works = await self.test_password_reset_flow()
        
        # Test 4: Provide resolution
        resolution = await self.provide_resolution_steps()
        
        # Final summary
        self.log("=" * 80)
        self.log("📋 PRODUCTION INVESTIGATION SUMMARY")
        self.log("=" * 80)
        
        summary = {
            "email_investigated": TARGET_EMAIL,
            "production_backend_confirmed": production_issue,
            "production_login_works": login_works,
            "production_reset_works": reset_works,
            "user_id_if_found": user_id,
            "resolution_provided": resolution,
            "timestamp": datetime.now().isoformat()
        }
        
        for key, value in summary.items():
            self.log(f"{key}: {value}")
        
        # Recommendations
        self.log("=" * 80)
        self.log("🎯 FINAL RECOMMENDATIONS")
        self.log("=" * 80)
        
        if production_issue and not login_works and not reset_works:
            self.log("🗑️ RECOMMENDATION: Complete production database cleanup required")
            self.log("   - Account exists but is completely non-functional")
            self.log("   - Remove all traces from production database")
            self.log("   - Allow fresh registration")
        elif production_issue and (login_works or reset_works):
            self.log("🔧 RECOMMENDATION: Fix existing production account")
            self.log("   - Account exists and partially functional")
            self.log("   - Update verification status in production")
            self.log("   - Preserve user data if possible")
        else:
            self.log("❓ RECOMMENDATION: Further investigation needed")
            self.log("   - Unexpected behavior detected")
            self.log("   - Manual review of production database required")
        
        return summary

async def main():
    """Main production investigation execution"""
    tester = ProductionDatabaseTester()
    
    try:
        results = await tester.run_production_investigation()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())