#!/usr/bin/env python3
"""
Reset User Recipe History - MongoDB Script
Safely deletes all recipes for a specific user from MongoDB
"""

import os
import pymongo
import logging
from datetime import datetime

class RecipeHistoryResetter:
    def __init__(self):
        # Get MongoDB URL from environment
        self.mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/ai_recipe_app')
        self.client = None
        self.db = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def connect_to_database(self):
        """Connect to MongoDB database"""
        try:
            self.client = pymongo.MongoClient(self.mongo_url)
            # Extract database name from connection string or use default
            if '/' in self.mongo_url:
                db_name = self.mongo_url.split('/')[-1].split('?')[0]
            else:
                db_name = 'ai_recipe_app'
            
            self.db = self.client[db_name]
            
            # Test connection
            self.client.admin.command('ping')
            self.logger.info(f"✅ Connected to MongoDB database: {db_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
            return False
    
    def get_user_recipe_count(self, user_id):
        """Get current recipe count for user"""
        try:
            collections_to_check = [
                ('recipes', 'user_id'),
                ('starbucks_recipes', 'user_id'),
                ('curated_starbucks_recipes', 'user_id'),
                ('weekly_plans', 'user_id')
            ]
            
            total_count = 0
            counts = {}
            
            for collection_name, field_name in collections_to_check:
                if collection_name in self.db.list_collection_names():
                    count = self.db[collection_name].count_documents({field_name: user_id})
                    counts[collection_name] = count
                    total_count += count
                else:
                    counts[collection_name] = 0
            
            return total_count, counts
            
        except Exception as e:
            self.logger.error(f"❌ Error getting recipe count: {str(e)}")
            return 0, {}
    
    def preview_user_recipes(self, user_id, limit=5):
        """Preview recipes before deletion"""
        try:
            self.logger.info(f"📋 Preview of recipes for user {user_id[:8]}...")
            
            # Check main recipes collection
            recipes = list(self.db.recipes.find({'user_id': user_id}).limit(limit))
            
            if recipes:
                self.logger.info(f"Sample recipes to be deleted:")
                for i, recipe in enumerate(recipes, 1):
                    title = recipe.get('title', 'Unknown Title')
                    recipe_id = recipe.get('id', recipe.get('_id', 'Unknown ID'))
                    cuisine = recipe.get('cuisine_type', 'Unknown')
                    self.logger.info(f"  {i}. {title} ({cuisine}) - ID: {str(recipe_id)[:8]}...")
            else:
                self.logger.info("  No recipes found in main collection")
            
            return len(recipes)
            
        except Exception as e:
            self.logger.error(f"❌ Error previewing recipes: {str(e)}")
            return 0
    
    def reset_user_recipes(self, user_id, confirm=False):
        """Reset all recipes for a user"""
        try:
            if not confirm:
                self.logger.warning("⚠️  This operation will permanently delete all recipes for the user!")
                self.logger.warning("⚠️  Set confirm=True to proceed with deletion")
                return False
            
            self.logger.info(f"🔄 Starting recipe history reset for user: {user_id}")
            
            # Get current counts
            total_count, counts = self.get_user_recipe_count(user_id)
            
            if total_count == 0:
                self.logger.info("✅ User has no recipes to delete")
                return True
            
            self.logger.info(f"📊 Current recipe counts: {counts}")
            self.logger.info(f"📊 Total recipes to delete: {total_count}")
            
            # Preview recipes
            self.preview_user_recipes(user_id)
            
            # Delete from all collections
            collections_to_clean = [
                ('recipes', 'user_id'),
                ('starbucks_recipes', 'user_id'),
                ('curated_starbucks_recipes', 'user_id'),
                ('weekly_plans', 'user_id')
            ]
            
            total_deleted = 0
            deletion_results = {}
            
            for collection_name, field_name in collections_to_clean:
                if collection_name in self.db.list_collection_names():
                    result = self.db[collection_name].delete_many({field_name: user_id})
                    deletion_results[collection_name] = result.deleted_count
                    total_deleted += result.deleted_count
                    
                    if result.deleted_count > 0:
                        self.logger.info(f"🗑️  Deleted {result.deleted_count} items from {collection_name}")
                else:
                    deletion_results[collection_name] = 0
            
            # Verify deletion
            remaining_count, remaining_counts = self.get_user_recipe_count(user_id)
            
            self.logger.info(f"📊 Deletion summary:")
            self.logger.info(f"   Total deleted: {total_deleted}")
            self.logger.info(f"   Remaining items: {remaining_count}")
            
            if remaining_count == 0:
                self.logger.info(f"🎉 Recipe history successfully reset for user: {user_id}")
                return True
            else:
                self.logger.warning(f"⚠️  Warning: {remaining_count} items still remain")
                self.logger.info(f"Remaining counts: {remaining_counts}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error resetting recipe history: {str(e)}")
            return False
    
    def close_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.logger.info("✅ Database connection closed")

def main():
    # Configuration
    DEMO_USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
    
    print("🔄 MongoDB Recipe History Reset Tool")
    print("=" * 50)
    
    resetter = RecipeHistoryResetter()
    
    try:
        # Connect to database
        if not resetter.connect_to_database():
            return False
        
        # Get current status
        total_count, counts = resetter.get_user_recipe_count(DEMO_USER_ID)
        print(f"📊 Current recipe count for demo user: {total_count}")
        
        if total_count == 0:
            print("✅ Demo user already has no recipes")
            return True
        
        # Preview recipes
        resetter.preview_user_recipes(DEMO_USER_ID)
        
        # Ask for confirmation
        print("\n⚠️  This will permanently delete all recipes for the demo user!")
        response = input("Type 'DELETE' to confirm: ")
        
        if response.strip() == 'DELETE':
            # Perform reset
            success = resetter.reset_user_recipes(DEMO_USER_ID, confirm=True)
            return success
        else:
            print("❌ Operation cancelled")
            return False
            
    finally:
        resetter.close_connection()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Recipe history reset completed successfully!")
    else:
        print("\n❌ Recipe history reset failed!")
        exit(1)