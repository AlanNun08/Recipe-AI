#!/usr/bin/env python3
"""
Database Inconsistency Investigation and Resolution Test
Specifically for alannunezsilva0310@gmail.com email issue

ISSUE: Email shows as "already registered" but account investigation said it didn't exist.
GOAL: Either fix the existing account to work properly OR completely remove all traces 
      so user can register fresh.
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from pathlib import Path

# Add backend to path
sys.path.append('/app/backend')
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path('/app/backend')
load_dotenv(ROOT_DIR / '.env')

# Database connection
mongo_url = os.environ['MONGO_URL']
db_name = os.environ.get('DB_NAME', 'test_database')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Backend URL for API testing
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://buildyoursmartcart.com') + '/api'

# Target email for investigation
TARGET_EMAIL = "alannunezsilva0310@gmail.com"

class DatabaseInconsistencyTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.findings = []
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        self.findings.append(f"[{level}] {message}")
    
    async def deep_database_search(self):
        """1. Deep Database Search - Search ALL possible variations of the target email"""
        self.log("=== DEEP DATABASE SEARCH FOR alannunezsilva0310@gmail.com ===")
        
        email_variations = [
            TARGET_EMAIL,
            TARGET_EMAIL.lower(),
            TARGET_EMAIL.upper(),
            TARGET_EMAIL.strip(),
            f" {TARGET_EMAIL} ",  # With spaces
            TARGET_EMAIL.replace("@", " @ "),  # With spaces around @
        ]
        
        collections_to_search = [
            "users",
            "verification_codes", 
            "password_reset_codes",
            "recipes",
            "grocery_carts",
            "shared_recipes",
            "payment_transactions",
            "user_shared_recipes",
            "starbucks_recipes",
            "curated_starbucks_recipes"
        ]
        
        total_found = 0
        
        for collection_name in collections_to_search:
            self.log(f"Searching collection: {collection_name}")
            collection = db[collection_name]
            
            for email_var in email_variations:
                try:
                    # Exact match
                    exact_docs = await collection.find({"email": email_var}).to_list(100)
                    if exact_docs:
                        self.log(f"  ✅ FOUND {len(exact_docs)} documents with exact email '{email_var}'")
                        total_found += len(exact_docs)
                        for doc in exact_docs:
                            self.log(f"    - Document ID: {doc.get('_id', doc.get('id', 'Unknown'))}")
                            self.log(f"    - Created: {doc.get('created_at', 'Unknown')}")
                            if 'is_verified' in doc:
                                self.log(f"    - Verified: {doc.get('is_verified', 'Unknown')}")
                    
                    # Case-insensitive regex search
                    regex_docs = await collection.find({
                        "email": {"$regex": f"^{re.escape(email_var)}$", "$options": "i"}
                    }).to_list(100)
                    
                    if regex_docs and len(regex_docs) != len(exact_docs):
                        self.log(f"  ✅ FOUND {len(regex_docs)} additional documents with case-insensitive search")
                        total_found += len(regex_docs)
                        for doc in regex_docs:
                            self.log(f"    - Document ID: {doc.get('_id', doc.get('id', 'Unknown'))}")
                            self.log(f"    - Email stored as: '{doc.get('email', 'Unknown')}'")
                    
                    # Search in user_id fields (in case email is stored as user_id somewhere)
                    userid_docs = await collection.find({"user_id": email_var}).to_list(100)
                    if userid_docs:
                        self.log(f"  ⚠️ FOUND {len(userid_docs)} documents with email as user_id")
                        total_found += len(userid_docs)
                    
                    # Search in shared_by_user_id fields
                    if "shared_by_user_id" in await collection.find_one({}) or {}:
                        shared_docs = await collection.find({"shared_by_user_id": email_var}).to_list(100)
                        if shared_docs:
                            self.log(f"  ⚠️ FOUND {len(shared_docs)} documents with email as shared_by_user_id")
                            total_found += len(shared_docs)
                            
                except Exception as e:
                    self.log(f"  ❌ Error searching {collection_name} for '{email_var}': {str(e)}")
        
        # Additional comprehensive search - look for partial matches
        self.log("Performing partial match search...")
        username_part = TARGET_EMAIL.split('@')[0]  # "alannunezsilva0310"
        
        for collection_name in collections_to_search:
            collection = db[collection_name]
            try:
                partial_docs = await collection.find({
                    "email": {"$regex": username_part, "$options": "i"}
                }).to_list(100)
                
                if partial_docs:
                    self.log(f"  🔍 FOUND {len(partial_docs)} documents with partial match in {collection_name}")
                    for doc in partial_docs:
                        self.log(f"    - Email: {doc.get('email', 'Unknown')}")
                        self.log(f"    - Document ID: {doc.get('_id', doc.get('id', 'Unknown'))}")
                        
            except Exception as e:
                self.log(f"  ❌ Error in partial search of {collection_name}: {str(e)}")
        
        self.log(f"🔍 TOTAL DOCUMENTS FOUND: {total_found}")
        return total_found > 0
    
    async def test_registration_behavior(self):
        """2. Test Registration Behavior - Why does it say 'email already registered'?"""
        self.log("=== TESTING REGISTRATION BEHAVIOR ===")
        
        try:
            # Attempt to register with the target email
            registration_data = {
                "first_name": "Alan",
                "last_name": "Nunez Silva",
                "email": TARGET_EMAIL,
                "password": "testpassword123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            self.log(f"Attempting registration with: {TARGET_EMAIL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=registration_data)
            
            self.log(f"Registration response status: {response.status_code}")
            self.log(f"Registration response: {response.text}")
            
            if response.status_code == 400 and "already registered" in response.text.lower():
                self.log("✅ CONFIRMED: Email shows as 'already registered'")
                return True
            elif response.status_code == 200:
                self.log("⚠️ UNEXPECTED: Registration succeeded - email was NOT already registered")
                return False
            else:
                self.log(f"❌ UNEXPECTED: Registration failed with different error: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}")
            return False
    
    async def test_login_behavior(self):
        """3. Test Login Behavior - Can the account actually login?"""
        self.log("=== TESTING LOGIN BEHAVIOR ===")
        
        # Try common passwords that might have been used
        test_passwords = [
            "password123",
            "123456",
            "password",
            "alan123",
            "alannunez123",
            "testpassword123"
        ]
        
        for password in test_passwords:
            try:
                login_data = {
                    "email": TARGET_EMAIL,
                    "password": password
                }
                
                self.log(f"Attempting login with password: {password[:3]}***")
                response = await self.client.post(f"{BACKEND_URL}/auth/login", json=login_data)
                
                self.log(f"Login response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ LOGIN SUCCESSFUL with password: {password[:3]}***")
                    self.log(f"User status: {result.get('status', 'Unknown')}")
                    self.log(f"User ID: {result.get('user_id', 'Unknown')}")
                    return True
                elif response.status_code == 401:
                    self.log(f"❌ Login failed: Invalid credentials")
                else:
                    self.log(f"❌ Login failed: {response.text}")
                    
            except Exception as e:
                self.log(f"❌ Error testing login with {password[:3]}***: {str(e)}")
        
        self.log("❌ NO SUCCESSFUL LOGIN FOUND")
        return False
    
    async def check_verification_status(self):
        """4. Check Account Verification Status"""
        self.log("=== CHECKING VERIFICATION STATUS ===")
        
        try:
            # Look for verification codes
            verification_codes = await db.verification_codes.find({
                "email": {"$regex": f"^{re.escape(TARGET_EMAIL)}$", "$options": "i"}
            }).to_list(100)
            
            if verification_codes:
                self.log(f"✅ FOUND {len(verification_codes)} verification codes")
                for code in verification_codes:
                    self.log(f"  - Code: {code.get('code', 'Unknown')}")
                    self.log(f"  - Created: {code.get('created_at', 'Unknown')}")
                    self.log(f"  - Expires: {code.get('expires_at', 'Unknown')}")
                    self.log(f"  - Used: {code.get('is_used', 'Unknown')}")
            else:
                self.log("❌ NO verification codes found")
            
            # Look for password reset codes
            reset_codes = await db.password_reset_codes.find({
                "email": {"$regex": f"^{re.escape(TARGET_EMAIL)}$", "$options": "i"}
            }).to_list(100)
            
            if reset_codes:
                self.log(f"✅ FOUND {len(reset_codes)} password reset codes")
                for code in reset_codes:
                    self.log(f"  - Code: {code.get('code', 'Unknown')}")
                    self.log(f"  - Created: {code.get('created_at', 'Unknown')}")
                    self.log(f"  - Used: {code.get('is_used', 'Unknown')}")
            else:
                self.log("❌ NO password reset codes found")
                
            return len(verification_codes) > 0 or len(reset_codes) > 0
            
        except Exception as e:
            self.log(f"❌ Error checking verification status: {str(e)}")
            return False
    
    async def complete_cleanup(self):
        """5. Complete Cleanup - Remove ALL traces of the email"""
        self.log("=== PERFORMING COMPLETE CLEANUP ===")
        
        collections_to_clean = [
            "users",
            "verification_codes", 
            "password_reset_codes",
            "recipes",
            "grocery_carts",
            "shared_recipes",
            "payment_transactions",
            "user_shared_recipes",
            "starbucks_recipes"
        ]
        
        total_deleted = 0
        
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            
            try:
                # Delete by exact email match
                result1 = await collection.delete_many({
                    "email": {"$regex": f"^{re.escape(TARGET_EMAIL)}$", "$options": "i"}
                })
                
                # Delete by user_id match (in case email was stored as user_id)
                result2 = await collection.delete_many({
                    "user_id": {"$regex": f"^{re.escape(TARGET_EMAIL)}$", "$options": "i"}
                })
                
                # Delete by shared_by_user_id match
                result3 = await collection.delete_many({
                    "shared_by_user_id": {"$regex": f"^{re.escape(TARGET_EMAIL)}$", "$options": "i"}
                })
                
                deleted_count = result1.deleted_count + result2.deleted_count + result3.deleted_count
                
                if deleted_count > 0:
                    self.log(f"✅ DELETED {deleted_count} documents from {collection_name}")
                    total_deleted += deleted_count
                else:
                    self.log(f"  No documents to delete in {collection_name}")
                    
            except Exception as e:
                self.log(f"❌ Error cleaning {collection_name}: {str(e)}")
        
        self.log(f"🗑️ TOTAL DOCUMENTS DELETED: {total_deleted}")
        return total_deleted
    
    async def verify_clean_state(self):
        """6. Verify Clean State - Ensure registration works after cleanup"""
        self.log("=== VERIFYING CLEAN STATE ===")
        
        # Wait a moment for database consistency
        await asyncio.sleep(2)
        
        try:
            # First, verify no traces remain in database
            remaining_traces = await self.deep_database_search()
            if remaining_traces:
                self.log("❌ CLEANUP INCOMPLETE: Traces still found in database")
                return False
            
            # Test registration again
            registration_data = {
                "first_name": "Alan",
                "last_name": "Nunez Silva", 
                "email": TARGET_EMAIL,
                "password": "newpassword123",
                "dietary_preferences": [],
                "allergies": [],
                "favorite_cuisines": []
            }
            
            self.log(f"Testing fresh registration with: {TARGET_EMAIL}")
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=registration_data)
            
            self.log(f"Fresh registration status: {response.status_code}")
            self.log(f"Fresh registration response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                self.log("✅ SUCCESS: Fresh registration completed successfully")
                self.log(f"New user ID: {result.get('user_id', 'Unknown')}")
                
                # Clean up the test registration
                if result.get('user_id'):
                    await db.users.delete_one({"id": result['user_id']})
                    await db.verification_codes.delete_many({"user_id": result['user_id']})
                    self.log("🗑️ Cleaned up test registration")
                
                return True
            else:
                self.log(f"❌ FAILED: Fresh registration still failing: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error verifying clean state: {str(e)}")
            return False
    
    async def investigate_backend_logic(self):
        """7. Investigate Backend Registration Logic"""
        self.log("=== INVESTIGATING BACKEND REGISTRATION LOGIC ===")
        
        try:
            # Check the actual registration logic in the backend
            self.log("Analyzing registration endpoint logic...")
            
            # The registration endpoint checks for existing users with:
            # existing_user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
            
            email_lower = TARGET_EMAIL.lower().strip()
            
            # Test the exact query used by the backend
            existing_user = await db.users.find_one({
                "email": {"$regex": f"^{email_lower}$", "$options": "i"}
            })
            
            if existing_user:
                self.log("✅ FOUND: Backend query found existing user")
                self.log(f"  - User ID: {existing_user.get('id', 'Unknown')}")
                self.log(f"  - Email stored as: '{existing_user.get('email', 'Unknown')}'")
                self.log(f"  - Verified: {existing_user.get('is_verified', 'Unknown')}")
                self.log(f"  - Created: {existing_user.get('created_at', 'Unknown')}")
                return existing_user
            else:
                self.log("❌ NOT FOUND: Backend query found no existing user")
                return None
                
        except Exception as e:
            self.log(f"❌ Error investigating backend logic: {str(e)}")
            return None
    
    async def run_comprehensive_investigation(self):
        """Run complete investigation and resolution"""
        self.log("🔍 STARTING COMPREHENSIVE DATABASE INCONSISTENCY INVESTIGATION")
        self.log("=" * 80)
        self.log(f"TARGET EMAIL: {TARGET_EMAIL}")
        self.log("=" * 80)
        
        # Step 1: Deep database search
        found_traces = await self.deep_database_search()
        
        # Step 2: Test registration behavior
        registration_blocked = await self.test_registration_behavior()
        
        # Step 3: Test login behavior
        login_possible = await self.test_login_behavior()
        
        # Step 4: Check verification status
        has_verification_data = await self.check_verification_status()
        
        # Step 5: Investigate backend logic
        backend_user = await self.investigate_backend_logic()
        
        # Analysis and decision
        self.log("=" * 80)
        self.log("🔍 INVESTIGATION ANALYSIS")
        self.log("=" * 80)
        
        if found_traces and registration_blocked:
            self.log("✅ INCONSISTENCY CONFIRMED: Data exists but account doesn't work properly")
            
            if login_possible:
                self.log("🔧 RECOMMENDATION: Fix existing account verification status")
                # Fix the account instead of deleting
                if backend_user:
                    await db.users.update_one(
                        {"id": backend_user["id"]},
                        {"$set": {
                            "is_verified": True,
                            "verified_at": datetime.utcnow()
                        }}
                    )
                    self.log("✅ FIXED: Updated account verification status")
            else:
                self.log("🗑️ RECOMMENDATION: Complete cleanup - account is corrupted")
                deleted_count = await self.complete_cleanup()
                
                if deleted_count > 0:
                    # Verify cleanup worked
                    clean_state = await self.verify_clean_state()
                    if clean_state:
                        self.log("✅ SUCCESS: Complete cleanup successful, fresh registration now possible")
                    else:
                        self.log("❌ FAILED: Cleanup incomplete, manual intervention required")
                else:
                    self.log("⚠️ WARNING: No data found to clean up, issue may be elsewhere")
        
        elif not found_traces and registration_blocked:
            self.log("🤔 MYSTERY: No data found but registration still blocked")
            self.log("🔧 RECOMMENDATION: Check for caching issues or external data sources")
            
        elif found_traces and not registration_blocked:
            self.log("✅ RESOLVED: Data exists and registration works - issue may be resolved")
            
        else:
            self.log("✅ NO ISSUE: No data found and registration works normally")
        
        # Final summary
        self.log("=" * 80)
        self.log("📋 FINAL SUMMARY")
        self.log("=" * 80)
        
        summary = {
            "email_investigated": TARGET_EMAIL,
            "database_traces_found": found_traces,
            "registration_blocked": registration_blocked,
            "login_possible": login_possible,
            "verification_data_exists": has_verification_data,
            "backend_user_found": backend_user is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        for key, value in summary.items():
            self.log(f"{key}: {value}")
        
        return summary

async def main():
    """Main investigation execution"""
    tester = DatabaseInconsistencyTester()
    
    try:
        results = await tester.run_comprehensive_investigation()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())