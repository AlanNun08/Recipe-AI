#!/usr/bin/env python3
"""
PRODUCTION DATABASE CLEANUP SCRIPT
FOR DEPLOYMENT IN GOOGLE CLOUD ENVIRONMENT

This script must be run in the production environment where it has access to:
- MONGO_URL (production MongoDB connection string)
- DB_NAME=buildyoursmartcart_production

TARGET: Complete cleanup of alannunezsilva0310@gmail.com account
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any
import json
import httpx

class ProductionAccountCleaner:
    def __init__(self):
        self.client = None
        self.db = None
        self.target_email = "alannunezsilva0310@gmail.com"
        self.production_api = "https://buildyoursmartcart.com/api"
        self.cleanup_results = {
            'target_email': self.target_email,
            'cleanup_steps': [],
            'collections_cleaned': {},
            'verification_tests': {}
        }
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        self.cleanup_results['cleanup_steps'].append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
    
    async def connect_to_production_database(self):
        """Connect to production MongoDB using Google Cloud environment variables"""
        self.log("=== CONNECTING TO PRODUCTION DATABASE ===")
        
        try:
            # Get production environment variables
            mongo_url = os.environ.get('MONGO_URL')
            db_name = os.environ.get('DB_NAME', 'buildyoursmartcart_production')
            
            if not mongo_url:
                self.log("❌ MONGO_URL not found in environment variables", "ERROR")
                self.log("This script must be run in Google Cloud environment with production credentials", "ERROR")
                return False
            
            self.log(f"Database name: {db_name}")
            self.log(f"MongoDB URL: {mongo_url[:50]}..." if len(mongo_url) > 50 else f"MongoDB URL: {mongo_url}")
            
            # Connect to production database
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            
            # Test connection
            await self.db.command("ping")
            self.log("✅ Successfully connected to production database", "SUCCESS")
            
            # Get database info
            collections = await self.db.list_collection_names()
            self.log(f"Available collections ({len(collections)}): {collections}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to connect to production database: {str(e)}", "ERROR")
            return False
    
    async def find_user_account(self):
        """Find the user account and get user_id for comprehensive cleanup"""
        self.log("=== FINDING USER ACCOUNT ===")
        
        try:
            users_collection = self.db["users"]
            
            # Search for user with case-insensitive email
            user = await users_collection.find_one({
                "email": {"$regex": f"^{self.target_email}$", "$options": "i"}
            })
            
            if user:
                user_id = user.get('id')
                self.log(f"✅ Found user account:")
                self.log(f"   User ID: {user_id}")
                self.log(f"   Email: {user.get('email')}")
                self.log(f"   Name: {user.get('first_name')} {user.get('last_name')}")
                self.log(f"   Verified: {user.get('is_verified')}")
                self.log(f"   Created: {user.get('created_at')}")
                
                self.cleanup_results['user_found'] = True
                self.cleanup_results['user_id'] = user_id
                self.cleanup_results['user_data'] = {
                    'id': user_id,
                    'email': user.get('email'),
                    'first_name': user.get('first_name'),
                    'last_name': user.get('last_name'),
                    'is_verified': user.get('is_verified'),
                    'created_at': str(user.get('created_at'))
                }
                
                return user_id
            else:
                self.log("❌ User account not found in users collection")
                self.cleanup_results['user_found'] = False
                return None
                
        except Exception as e:
            self.log(f"❌ Error finding user account: {str(e)}", "ERROR")
            return None
    
    async def comprehensive_account_search(self, user_id: str = None):
        """Search for account data in all collections"""
        self.log("=== COMPREHENSIVE ACCOUNT SEARCH ===")
        
        try:
            collections = await self.db.list_collection_names()
            found_data = {}
            
            for collection_name in collections:
                self.log(f"Searching collection: {collection_name}")
                collection = self.db[collection_name]
                
                # Define search queries for different collections
                search_queries = []
                
                # Email-based searches
                search_queries.extend([
                    {"email": self.target_email},
                    {"email": {"$regex": f"^{self.target_email}$", "$options": "i"}},
                    {"user_email": self.target_email},
                    {"shared_by_user_email": self.target_email}
                ])
                
                # User ID-based searches (if we have user_id)
                if user_id:
                    search_queries.extend([
                        {"user_id": user_id},
                        {"shared_by_user_id": user_id},
                        {"id": user_id}
                    ])
                
                collection_records = []
                for query in search_queries:
                    try:
                        records = await collection.find(query).to_list(100)
                        for record in records:
                            # Convert ObjectId to string for JSON serialization
                            if '_id' in record:
                                record['_id'] = str(record['_id'])
                            # Avoid duplicates
                            if record not in collection_records:
                                collection_records.append(record)
                    except Exception:
                        # Some queries might not work for all collections
                        continue
                
                if collection_records:
                    found_data[collection_name] = collection_records
                    self.log(f"🔍 Found {len(collection_records)} records in {collection_name}")
                else:
                    self.log(f"✅ No records in {collection_name}")
            
            self.cleanup_results['found_data'] = found_data
            
            if found_data:
                total_records = sum(len(records) for records in found_data.values())
                self.log(f"🚨 TOTAL RECORDS FOUND: {total_records} across {len(found_data)} collections")
            else:
                self.log("✅ No account data found in any collection")
            
            return found_data
            
        except Exception as e:
            self.log(f"❌ Error during comprehensive search: {str(e)}", "ERROR")
            return {}
    
    async def delete_account_data(self, found_data: Dict):
        """Delete all account data from all collections"""
        self.log("=== DELETING ACCOUNT DATA ===")
        
        if not found_data:
            self.log("✅ No data to delete")
            return True
        
        deletion_summary = {}
        total_deleted = 0
        
        try:
            for collection_name, records in found_data.items():
                self.log(f"Deleting from {collection_name}...")
                collection = self.db[collection_name]
                
                deleted_count = 0
                for record in records:
                    try:
                        # Convert string _id back to ObjectId for deletion
                        from bson import ObjectId
                        record_id = ObjectId(record['_id']) if isinstance(record['_id'], str) else record['_id']
                        
                        result = await collection.delete_one({"_id": record_id})
                        if result.deleted_count > 0:
                            deleted_count += 1
                            self.log(f"  ✅ Deleted record: {record['_id']}")
                        else:
                            self.log(f"  ⚠️ Record not found: {record['_id']}")
                    except Exception as e:
                        self.log(f"  ❌ Error deleting {record['_id']}: {str(e)}", "ERROR")
                
                deletion_summary[collection_name] = {
                    'found': len(records),
                    'deleted': deleted_count
                }
                total_deleted += deleted_count
                
                self.log(f"✅ {collection_name}: {deleted_count}/{len(records)} records deleted")
            
            self.cleanup_results['collections_cleaned'] = deletion_summary
            self.cleanup_results['total_records_deleted'] = total_deleted
            
            self.log(f"🎉 DELETION COMPLETE: {total_deleted} total records deleted")
            return True
            
        except Exception as e:
            self.log(f"❌ Error during deletion: {str(e)}", "ERROR")
            return False
    
    async def verify_cleanup_success(self):
        """Verify that the account has been completely removed"""
        self.log("=== VERIFYING CLEANUP SUCCESS ===")
        
        try:
            # Re-search for any remaining data
            remaining_data = await self.comprehensive_account_search()
            
            if not remaining_data:
                self.log("✅ VERIFICATION SUCCESSFUL: No account data remains")
                self.cleanup_results['verification_tests']['database_clean'] = True
                return True
            else:
                self.log("❌ VERIFICATION FAILED: Some data still remains", "ERROR")
                self.cleanup_results['verification_tests']['database_clean'] = False
                self.cleanup_results['remaining_data'] = remaining_data
                return False
                
        except Exception as e:
            self.log(f"❌ Error during verification: {str(e)}", "ERROR")
            return False
    
    async def test_registration_availability(self):
        """Test that the email is now available for registration"""
        self.log("=== TESTING REGISTRATION AVAILABILITY ===")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                registration_data = {
                    "first_name": "Test",
                    "last_name": "User",
                    "email": self.target_email,
                    "password": "testpassword123",
                    "dietary_preferences": [],
                    "allergies": [],
                    "favorite_cuisines": []
                }
                
                response = await client.post(
                    f"{self.production_api}/auth/register",
                    json=registration_data
                )
                
                if response.status_code == 200:
                    self.log("✅ REGISTRATION TEST PASSED: Email is available for registration")
                    self.cleanup_results['verification_tests']['registration_available'] = True
                    
                    # Clean up the test registration
                    response_data = response.json()
                    test_user_id = response_data.get('user_id')
                    if test_user_id:
                        self.log("🧹 Cleaning up test registration...")
                        await self.db.users.delete_one({"id": test_user_id})
                        await self.db.verification_codes.delete_many({"user_id": test_user_id})
                        self.log("✅ Test registration cleaned up")
                    
                    return True
                elif response.status_code == 400:
                    error_data = response.json()
                    if "already registered" in error_data.get("detail", "").lower():
                        self.log("❌ REGISTRATION TEST FAILED: Email still registered", "ERROR")
                        self.cleanup_results['verification_tests']['registration_available'] = False
                        return False
                    else:
                        self.log(f"⚠️ Registration failed with different error: {error_data}")
                        return None
                else:
                    self.log(f"⚠️ Unexpected registration response: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}", "ERROR")
            return None
    
    async def run_complete_cleanup(self):
        """Execute the complete cleanup process"""
        self.log("🚀 STARTING COMPLETE PRODUCTION ACCOUNT CLEANUP")
        self.log(f"Target: {self.target_email}")
        self.log(f"Environment: Google Cloud Production")
        
        try:
            # Step 1: Connect to production database
            if not await self.connect_to_production_database():
                return False
            
            # Step 2: Find user account and get user_id
            user_id = await self.find_user_account()
            
            # Step 3: Comprehensive search for all account data
            found_data = await self.comprehensive_account_search(user_id)
            
            # Step 4: Delete all account data
            deletion_success = await self.delete_account_data(found_data)
            
            # Step 5: Verify cleanup success
            verification_success = await self.verify_cleanup_success()
            
            # Step 6: Test registration availability
            registration_available = await self.test_registration_availability()
            
            # Final assessment
            overall_success = (
                deletion_success and 
                verification_success and 
                registration_available
            )
            
            self.cleanup_results['overall_success'] = overall_success
            self.cleanup_results['completed_at'] = datetime.now().isoformat()
            
            # Final summary
            self.log("=== FINAL CLEANUP SUMMARY ===")
            self.log(f"Database Connection: ✅")
            self.log(f"Account Search: ✅")
            self.log(f"Data Deletion: {'✅' if deletion_success else '❌'}")
            self.log(f"Cleanup Verification: {'✅' if verification_success else '❌'}")
            self.log(f"Registration Available: {'✅' if registration_available else '❌'}")
            
            if overall_success:
                self.log("🎉 COMPLETE CLEANUP SUCCESSFUL", "SUCCESS")
                self.log(f"✅ {self.target_email} completely removed from production")
                self.log("✅ Email is now available for fresh registration")
            else:
                self.log("❌ CLEANUP INCOMPLETE", "ERROR")
                self.log("❌ Manual intervention may be required")
            
            # Save detailed results
            with open('/tmp/production_cleanup_results.json', 'w') as f:
                json.dump(self.cleanup_results, f, indent=2, default=str)
            
            self.log("📄 Results saved to: /tmp/production_cleanup_results.json")
            
            return overall_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {str(e)}", "ERROR")
            return False
        finally:
            if self.client:
                self.client.close()

async def main():
    """Main execution function"""
    cleaner = ProductionAccountCleaner()
    
    try:
        success = await cleaner.run_complete_cleanup()
        
        if success:
            print("\n🎉 PRODUCTION CLEANUP COMPLETED SUCCESSFULLY")
            print("✅ alannunezsilva0310@gmail.com has been completely removed")
            print("✅ Email is now available for fresh registration")
            print("✅ All verification issues should be resolved")
            sys.exit(0)
        else:
            print("\n❌ PRODUCTION CLEANUP FAILED")
            print("❌ Check logs and results file for details")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔧 PRODUCTION DATABASE CLEANUP TOOL")
    print("📧 Target: alannunezsilva0310@gmail.com")
    print("🗄️ Database: buildyoursmartcart_production")
    print("🌐 Environment: Google Cloud Production")
    print("=" * 70)
    print("⚠️  This script must be run in the production environment")
    print("⚠️  with access to production MongoDB credentials")
    print("=" * 70)
    
    asyncio.run(main())