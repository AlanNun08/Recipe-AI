#!/usr/bin/env python3
"""
Production Database Cleanup Script
Connect to PRODUCTION database using Google Cloud environment variables
to completely clean up alannunezsilva0310@gmail.com account.

PRODUCTION DATABASE CONNECTION:
- Use MONGO_URL from Google Cloud environment (not local .env)
- Use DB_NAME=buildyoursmartcart_production 
- This is the actual production database where the corrupted account exists
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any
import json

class ProductionDatabaseCleaner:
    def __init__(self):
        self.client = None
        self.db = None
        self.target_email = "alannunezsilva0310@gmail.com"
        self.cleanup_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    async def connect_to_production_database(self):
        """Connect to the PRODUCTION database using Google Cloud environment variables"""
        self.log("=== CONNECTING TO PRODUCTION DATABASE ===")
        
        try:
            # Get production MongoDB URL from Google Cloud environment
            # This should be the actual production connection string, not local .env
            mongo_url = os.environ.get('MONGO_URL')
            if not mongo_url:
                self.log("ERROR: MONGO_URL not found in environment variables", "ERROR")
                return False
            
            # Use production database name
            db_name = "buildyoursmartcart_production"
            
            self.log(f"Connecting to production database: {db_name}")
            self.log(f"MongoDB URL: {mongo_url[:50]}..." if len(mongo_url) > 50 else f"MongoDB URL: {mongo_url}")
            
            # Connect to production database
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[db_name]
            
            # Test connection
            await self.db.command("ping")
            self.log("✅ Successfully connected to PRODUCTION database", "SUCCESS")
            
            # Get database info
            collections = await self.db.list_collection_names()
            self.log(f"Available collections: {collections}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to connect to production database: {str(e)}", "ERROR")
            return False
    
    async def search_account_in_all_collections(self):
        """Search for alannunezsilva0310@gmail.com in all collections"""
        self.log("=== SEARCHING FOR ACCOUNT IN ALL COLLECTIONS ===")
        
        try:
            collections = await self.db.list_collection_names()
            found_records = {}
            
            for collection_name in collections:
                self.log(f"Searching in collection: {collection_name}")
                collection = self.db[collection_name]
                
                # Search for email in various possible fields
                search_queries = [
                    {"email": self.target_email},
                    {"email": {"$regex": f"^{self.target_email}$", "$options": "i"}},
                    {"user_email": self.target_email},
                    {"shared_by_user_email": self.target_email}
                ]
                
                collection_records = []
                for query in search_queries:
                    try:
                        records = await collection.find(query).to_list(100)
                        for record in records:
                            # Convert ObjectId to string for JSON serialization
                            if '_id' in record:
                                record['_id'] = str(record['_id'])
                            collection_records.append(record)
                    except Exception as e:
                        # Some queries might not work for all collections
                        continue
                
                if collection_records:
                    found_records[collection_name] = collection_records
                    self.log(f"🔍 Found {len(collection_records)} records in {collection_name}")
                    
                    # Log details of found records
                    for i, record in enumerate(collection_records):
                        self.log(f"  Record {i+1}: {json.dumps(record, default=str, indent=2)}")
                else:
                    self.log(f"✅ No records found in {collection_name}")
            
            self.cleanup_results['found_records'] = found_records
            
            if found_records:
                self.log(f"🚨 TOTAL COLLECTIONS WITH DATA: {len(found_records)}")
                total_records = sum(len(records) for records in found_records.values())
                self.log(f"🚨 TOTAL RECORDS FOUND: {total_records}")
            else:
                self.log("✅ No records found for this email in any collection")
            
            return found_records
            
        except Exception as e:
            self.log(f"❌ Error searching collections: {str(e)}", "ERROR")
            return {}
    
    async def delete_all_account_data(self, found_records: Dict):
        """Delete ALL traces of the email from all collections"""
        self.log("=== DELETING ALL ACCOUNT DATA ===")
        
        if not found_records:
            self.log("✅ No data to delete - account already clean")
            return True
        
        deletion_results = {}
        
        try:
            for collection_name, records in found_records.items():
                self.log(f"Deleting from collection: {collection_name}")
                collection = self.db[collection_name]
                
                # Delete records by their _id
                deleted_count = 0
                for record in records:
                    try:
                        # Convert string _id back to ObjectId for deletion
                        from bson import ObjectId
                        record_id = ObjectId(record['_id']) if isinstance(record['_id'], str) else record['_id']
                        
                        result = await collection.delete_one({"_id": record_id})
                        if result.deleted_count > 0:
                            deleted_count += 1
                            self.log(f"  ✅ Deleted record with _id: {record['_id']}")
                        else:
                            self.log(f"  ⚠️ Record not found for deletion: {record['_id']}")
                    except Exception as e:
                        self.log(f"  ❌ Error deleting record {record['_id']}: {str(e)}", "ERROR")
                
                deletion_results[collection_name] = {
                    'found': len(records),
                    'deleted': deleted_count
                }
                
                self.log(f"✅ Deleted {deleted_count}/{len(records)} records from {collection_name}")
            
            self.cleanup_results['deletion_results'] = deletion_results
            
            # Summary
            total_found = sum(result['found'] for result in deletion_results.values())
            total_deleted = sum(result['deleted'] for result in deletion_results.values())
            
            self.log(f"🎉 DELETION SUMMARY: {total_deleted}/{total_found} records deleted")
            
            return total_deleted == total_found
            
        except Exception as e:
            self.log(f"❌ Error during deletion: {str(e)}", "ERROR")
            return False
    
    async def verify_clean_state(self):
        """Verify that no documents remain for this email"""
        self.log("=== VERIFYING CLEAN STATE ===")
        
        try:
            # Re-search all collections to confirm cleanup
            remaining_records = await self.search_account_in_all_collections()
            
            if not remaining_records:
                self.log("✅ VERIFICATION SUCCESSFUL: No traces of email found in database")
                self.cleanup_results['verification_status'] = 'clean'
                return True
            else:
                self.log("❌ VERIFICATION FAILED: Some records still remain", "ERROR")
                self.cleanup_results['verification_status'] = 'dirty'
                self.cleanup_results['remaining_records'] = remaining_records
                return False
                
        except Exception as e:
            self.log(f"❌ Error during verification: {str(e)}", "ERROR")
            return False
    
    async def test_registration_capability(self):
        """Test that the email is now available for fresh registration"""
        self.log("=== TESTING REGISTRATION CAPABILITY ===")
        
        try:
            # Check if user exists in users collection
            users_collection = self.db["users"]
            existing_user = await users_collection.find_one({
                "email": {"$regex": f"^{self.target_email}$", "$options": "i"}
            })
            
            if existing_user:
                self.log("❌ Registration test FAILED: User still exists in database", "ERROR")
                self.cleanup_results['registration_ready'] = False
                return False
            else:
                self.log("✅ Registration test PASSED: Email is available for registration")
                self.cleanup_results['registration_ready'] = True
                return True
                
        except Exception as e:
            self.log(f"❌ Error testing registration: {str(e)}", "ERROR")
            return False
    
    async def run_complete_cleanup(self):
        """Run the complete cleanup process"""
        self.log("🚀 STARTING PRODUCTION DATABASE CLEANUP")
        self.log(f"Target email: {self.target_email}")
        self.log(f"Production database: buildyoursmartcart_production")
        
        try:
            # Step 1: Connect to production database
            if not await self.connect_to_production_database():
                return False
            
            # Step 2: Search for account in all collections
            found_records = await self.search_account_in_all_collections()
            
            # Step 3: Delete all account data
            deletion_success = await self.delete_all_account_data(found_records)
            
            # Step 4: Verify clean state
            verification_success = await self.verify_clean_state()
            
            # Step 5: Test registration capability
            registration_ready = await self.test_registration_capability()
            
            # Final summary
            self.log("=== FINAL CLEANUP SUMMARY ===")
            self.log(f"Database Connection: ✅ Success")
            self.log(f"Account Search: ✅ Complete")
            self.log(f"Data Deletion: {'✅ Success' if deletion_success else '❌ Failed'}")
            self.log(f"Clean State Verification: {'✅ Success' if verification_success else '❌ Failed'}")
            self.log(f"Registration Ready: {'✅ Yes' if registration_ready else '❌ No'}")
            
            overall_success = deletion_success and verification_success and registration_ready
            
            if overall_success:
                self.log("🎉 COMPLETE CLEANUP SUCCESSFUL", "SUCCESS")
                self.log(f"✅ {self.target_email} is now completely removed from production database")
                self.log("✅ Email is available for fresh registration")
            else:
                self.log("❌ CLEANUP INCOMPLETE - Manual intervention may be required", "ERROR")
            
            # Save detailed results
            self.cleanup_results['overall_success'] = overall_success
            self.cleanup_results['timestamp'] = datetime.now().isoformat()
            
            # Write results to file
            with open('/app/production_cleanup_results.json', 'w') as f:
                json.dump(self.cleanup_results, f, indent=2, default=str)
            
            self.log("📄 Detailed results saved to: /app/production_cleanup_results.json")
            
            return overall_success
            
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR during cleanup: {str(e)}", "ERROR")
            return False
        finally:
            if self.client:
                self.client.close()

async def main():
    """Main function to run the production cleanup"""
    cleaner = ProductionDatabaseCleaner()
    
    try:
        success = await cleaner.run_complete_cleanup()
        
        if success:
            print("\n🎉 PRODUCTION CLEANUP COMPLETED SUCCESSFULLY")
            print("✅ alannunezsilva0310@gmail.com has been completely removed")
            print("✅ Email is now available for fresh registration")
            sys.exit(0)
        else:
            print("\n❌ PRODUCTION CLEANUP FAILED")
            print("❌ Manual intervention may be required")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔧 Production Database Cleanup Tool")
    print("📧 Target: alannunezsilva0310@gmail.com")
    print("🗄️ Database: buildyoursmartcart_production")
    print("=" * 60)
    
    asyncio.run(main())