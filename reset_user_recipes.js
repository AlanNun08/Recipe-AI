// MongoDB script to reset recipe history for a user
// Usage: mongo your_database_name reset_user_recipes.js

// Configuration
const USER_ID = "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"; // Demo user ID
const DATABASE_NAME = "ai_recipe_app"; // Replace with your actual database name

print("🔄 Starting recipe history reset for user:", USER_ID);

// Switch to the database
use(DATABASE_NAME);

// Find current recipe count for the user
const currentCount = db.recipes.countDocuments({user_id: USER_ID});
print("📊 Current recipe count for user:", currentCount);

if (currentCount === 0) {
    print("✅ User has no recipes to delete");
} else {
    // Show some sample recipes before deletion
    print("📋 Sample recipes to be deleted:");
    const sampleRecipes = db.recipes.find({user_id: USER_ID}).limit(5);
    sampleRecipes.forEach(recipe => {
        print(`  • ${recipe.title || 'Unknown Title'} (ID: ${recipe.id})`);
    });
    
    // Delete all recipes for the user
    const deleteResult = db.recipes.deleteMany({user_id: USER_ID});
    print("🗑️ Deleted", deleteResult.deletedCount, "recipes");
    
    // Verify deletion
    const remainingCount = db.recipes.countDocuments({user_id: USER_ID});
    print("✅ Remaining recipe count:", remainingCount);
    
    if (remainingCount === 0) {
        print("🎉 Recipe history successfully reset for user:", USER_ID);
    } else {
        print("⚠️ Warning: Some recipes may not have been deleted");
    }
}

print("✅ Recipe history reset complete");
