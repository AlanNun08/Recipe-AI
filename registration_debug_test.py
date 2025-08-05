#!/usr/bin/env python3
"""
Registration Debug Test - Deep dive into registration logic
Investigating why alannunezsilva0310@gmail.com shows as "already registered" 
when no database traces exist.
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

class RegistrationDebugTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def cleanup(self):
        await self.client.aclose()
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def test_exact_backend_query(self):
        """Test the exact query used by the backend registration logic"""
        self.log("=== TESTING EXACT BACKEND REGISTRATION QUERY ===")
        
        try:
            # This is the exact logic from the backend registration endpoint:
            # email_lower = user_data.email.lower().strip()
            # existing_user = await db.users.find_one({"email": {"$regex": f"^{email_lower}$", "$options": "i"}})
            
            email_lower = TARGET_EMAIL.lower().strip()
            self.log(f"Email after processing: '{email_lower}'")
            
            # Test the exact query
            query = {"email": {"$regex": f"^{email_lower}$", "$options": "i"}}
            self.log(f"Query being executed: {query}")
            
            existing_user = await db.users.find_one(query)
            
            if existing_user:
                self.log("✅ FOUND: Backend query found existing user")
                self.log(f"  - User ID: {existing_user.get('id', 'Unknown')}")
                self.log(f"  - Email stored as: '{existing_user.get('email', 'Unknown')}'")
                self.log(f"  - Verified: {existing_user.get('is_verified', 'Unknown')}")
                self.log(f"  - Created: {existing_user.get('created_at', 'Unknown')}")
                return existing_user
            else:
                self.log("❌ NOT FOUND: Backend query found no existing user")
                
                # Let's check all users to see what's in the database
                all_users = await db.users.find({}).to_list(100)
                self.log(f"Total users in database: {len(all_users)}")
                
                # Look for similar emails
                for user in all_users:
                    user_email = user.get('email', '')
                    if 'alan' in user_email.lower() or 'nunez' in user_email.lower():
                        self.log(f"  Similar email found: '{user_email}'")
                
                return None
                
        except Exception as e:
            self.log(f"❌ Error testing backend query: {str(e)}")
            return None
    
    async def test_database_connection(self):
        """Test if we're connected to the right database"""
        self.log("=== TESTING DATABASE CONNECTION ===")
        
        try:
            # Check database name
            self.log(f"Connected to database: {db.name}")
            self.log(f"MongoDB URL: {mongo_url}")
            
            # List all collections
            collections = await db.list_collection_names()
            self.log(f"Collections in database: {collections}")
            
            # Count documents in users collection
            user_count = await db.users.count_documents({})
            self.log(f"Total users in database: {user_count}")
            
            # Show a few sample users (without sensitive data)
            sample_users = await db.users.find({}, {"email": 1, "first_name": 1, "created_at": 1}).limit(5).to_list(5)
            self.log("Sample users:")
            for user in sample_users:
                self.log(f"  - {user.get('email', 'Unknown')} ({user.get('first_name', 'Unknown')})")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing database connection: {str(e)}")
            return False
    
    async def test_registration_with_debug(self):
        """Test registration with detailed debugging"""
        self.log("=== TESTING REGISTRATION WITH DEBUG ===")
        
        try:
            # Test with the exact email
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
            self.log(f"Registration data: {json.dumps(registration_data, indent=2)}")
            
            response = await self.client.post(f"{BACKEND_URL}/auth/register", json=registration_data)
            
            self.log(f"Response status: {response.status_code}")
            self.log(f"Response headers: {dict(response.headers)}")
            self.log(f"Response text: {response.text}")
            
            # Test with slight variations
            variations = [
                TARGET_EMAIL.upper(),
                TARGET_EMAIL.lower(),
                f" {TARGET_EMAIL} ",
                TARGET_EMAIL.replace("@", " @ ").replace("  ", " ")
            ]
            
            for variation in variations:
                if variation != TARGET_EMAIL:
                    self.log(f"\nTesting variation: '{variation}'")
                    test_data = registration_data.copy()
                    test_data["email"] = variation
                    
                    var_response = await self.client.post(f"{BACKEND_URL}/auth/register", json=test_data)
                    self.log(f"  Status: {var_response.status_code}")
                    self.log(f"  Response: {var_response.text}")
            
            return response.status_code == 400 and "already registered" in response.text.lower()
            
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}")
            return False
    
    async def test_backend_logs(self):
        """Check backend logs for registration attempts"""
        self.log("=== CHECKING BACKEND LOGS ===")
        
        try:
            import subprocess
            
            # Get recent backend logs
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logs = result.stdout
                self.log("Recent backend logs:")
                
                # Look for registration-related logs
                for line in logs.split('\n'):
                    if any(keyword in line.lower() for keyword in ['register', 'alan', 'nunez', 'already', 'email']):
                        self.log(f"  {line}")
            
            # Get error logs
            result = subprocess.run(
                ["tail", "-n", "100", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                error_logs = result.stdout
                if error_logs.strip():
                    self.log("Recent error logs:")
                    for line in error_logs.split('\n'):
                        if line.strip():
                            self.log(f"  ERROR: {line}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error checking logs: {str(e)}")
            return False
    
    async def test_manual_user_creation(self):
        """Try to manually create a user with this email to see what happens"""
        self.log("=== TESTING MANUAL USER CREATION ===")
        
        try:
            # Import the User model and hash function
            sys.path.append('/app/backend')
            from server import User, hash_password
            
            # Create user object
            user = User(
                first_name="Alan",
                last_name="Nunez Silva",
                email=TARGET_EMAIL.lower().strip(),
                password_hash=hash_password("testpassword123"),
                dietary_preferences=[],
                allergies=[],
                favorite_cuisines=[],
                is_verified=False
            )
            
            self.log(f"Created user object with email: '{user.email}'")
            self.log(f"User ID: {user.id}")
            
            # Try to insert into database
            user_dict = user.dict()
            self.log("Attempting to insert user into database...")
            
            result = await db.users.insert_one(user_dict)
            
            if result.inserted_id:
                self.log(f"✅ SUCCESS: User inserted with ID: {result.inserted_id}")
                
                # Now try to find it
                found_user = await db.users.find_one({"id": user.id})
                if found_user:
                    self.log(f"✅ CONFIRMED: User found in database with email: '{found_user['email']}'")
                    
                    # Clean up
                    await db.users.delete_one({"id": user.id})
                    self.log("🗑️ Cleaned up test user")
                    
                    return True
                else:
                    self.log("❌ STRANGE: User not found after insertion")
                    return False
            else:
                self.log("❌ FAILED: User insertion failed")
                return False
                
        except Exception as e:
            self.log(f"❌ Error in manual user creation: {str(e)}")
            return False
    
    async def test_different_database_environments(self):
        """Check if we might be connected to a different database than the backend"""
        self.log("=== TESTING DATABASE ENVIRONMENT CONSISTENCY ===")
        
        try:
            # Check environment variables
            self.log(f"Our MONGO_URL: {mongo_url}")
            self.log(f"Our DB_NAME: {db_name}")
            
            # Try to create a test document and see if the backend can see it
            test_doc = {
                "test_id": "registration_debug_test",
                "email": "test@example.com",
                "created_at": datetime.utcnow(),
                "purpose": "Testing database consistency"
            }
            
            result = await db.test_collection.insert_one(test_doc)
            self.log(f"Inserted test document with ID: {result.inserted_id}")
            
            # Try to access it via API (if there's a debug endpoint)
            try:
                response = await self.client.get(f"{BACKEND_URL}/debug/test-db-connection")
                if response.status_code == 200:
                    self.log("✅ Backend can access database")
                else:
                    self.log(f"⚠️ Backend database access test returned: {response.status_code}")
            except:
                self.log("⚠️ No debug endpoint available for database test")
            
            # Clean up
            await db.test_collection.delete_one({"test_id": "registration_debug_test"})
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error testing database environment: {str(e)}")
            return False
    
    async def run_comprehensive_debug(self):
        """Run complete debugging investigation"""
        self.log("🔍 STARTING COMPREHENSIVE REGISTRATION DEBUG")
        self.log("=" * 80)
        self.log(f"TARGET EMAIL: {TARGET_EMAIL}")
        self.log("=" * 80)
        
        # Test 1: Database connection
        db_connected = await self.test_database_connection()
        
        # Test 2: Exact backend query
        backend_user = await self.test_exact_backend_query()
        
        # Test 3: Registration with debug
        registration_blocked = await self.test_registration_with_debug()
        
        # Test 4: Backend logs
        logs_checked = await self.test_backend_logs()
        
        # Test 5: Manual user creation
        manual_creation = await self.test_manual_user_creation()
        
        # Test 6: Database environment consistency
        db_consistent = await self.test_different_database_environments()
        
        # Final analysis
        self.log("=" * 80)
        self.log("🔍 DEBUG ANALYSIS")
        self.log("=" * 80)
        
        if not backend_user and registration_blocked:
            self.log("🚨 CONFIRMED BUG: Registration blocked but no user exists in database")
            self.log("🔧 POSSIBLE CAUSES:")
            self.log("  1. Backend is connected to a different database")
            self.log("  2. There's a caching layer we're not seeing")
            self.log("  3. The registration logic has a bug")
            self.log("  4. There's data in a different collection or field")
            
            if manual_creation:
                self.log("✅ Database write operations work normally")
            else:
                self.log("❌ Database write operations are failing")
        
        summary = {
            "email_investigated": TARGET_EMAIL,
            "database_connected": db_connected,
            "backend_user_found": backend_user is not None,
            "registration_blocked": registration_blocked,
            "manual_creation_works": manual_creation,
            "database_consistent": db_consistent,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log("=" * 80)
        self.log("📋 DEBUG SUMMARY")
        self.log("=" * 80)
        
        for key, value in summary.items():
            self.log(f"{key}: {value}")
        
        return summary

async def main():
    """Main debug execution"""
    tester = RegistrationDebugTester()
    
    try:
        results = await tester.run_comprehensive_debug()
        return results
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    results = asyncio.run(main())