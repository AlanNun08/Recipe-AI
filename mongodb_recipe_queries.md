# 🗄️ MongoDB Recipe Tracking Queries

## Core Recipe Tracking Queries

### 1. Save New Recipe
```javascript
// When user generates a recipe
db.recipes.insertOne({
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731", 
  "title": "Pad Thai with Shrimp",
  "description": "Classic Thai stir-fried noodles...",
  "ingredients": ["8 oz rice noodles", "1 lb shrimp"],
  "instructions": ["Soak noodles in warm water", "Heat oil in wok"],
  "prep_time": 20,
  "cook_time": 15,
  "servings": 4,
  "cuisine_type": "Asian", 
  "dietary_tags": [],
  "difficulty": "medium",
  "calories_per_serving": 380,
  "is_healthy": false,
  "created_at": ISODate("2025-08-09T19:30:00.000Z"),
  "shopping_list": ["rice noodles", "shrimp", "fish sauce"]
})
```

### 2. Get User Recipe History
```javascript
// Get all recipes for a user, sorted by newest first
db.recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
}).sort({
  "created_at": -1
}).limit(100)
```

### 3. Get Specific Recipe by ID
```javascript
// Get exact recipe for detail view
db.recipes.findOne({
  "id": "550e8400-e29b-41d4-a716-446655440000"
})
```

### 4. Get Recipe Statistics
```javascript
// Count total recipes for user
db.recipes.countDocuments({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
})

// Count by cuisine type
db.recipes.aggregate([
  {"$match": {"user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"}},
  {"$group": {"_id": "$cuisine_type", "count": {"$sum": 1}}},
  {"$sort": {"count": -1}}
])
```

### 5. Delete Recipe History
```javascript
// Delete single recipe
db.recipes.deleteOne({
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
})

// Delete all recipes for user (reset history)
db.recipes.deleteMany({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
})
```

## Advanced Tracking Queries

### 6. Filter Recipes by Category
```javascript
// Get only food recipes (exclude beverages/snacks)
db.recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",
  "cuisine_type": {"$not": {"$regex": "beverage|snack", "$options": "i"}}
}).sort({"created_at": -1})
```

### 7. Search Recipes by Text
```javascript
// Search recipe titles and descriptions
db.recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",
  "$or": [
    {"title": {"$regex": "chicken", "$options": "i"}},
    {"description": {"$regex": "chicken", "$options": "i"}}
  ]
}).sort({"created_at": -1})
```

### 8. Get Recipes by Date Range
```javascript
// Get recipes from last 30 days
var thirtyDaysAgo = new Date();
thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

db.recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",
  "created_at": {"$gte": thirtyDaysAgo}
}).sort({"created_at": -1})
```

### 9. Get Recipe Analytics
```javascript
// User's recipe generation patterns
db.recipes.aggregate([
  {"$match": {"user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"}},
  {"$group": {
    "_id": {
      "year": {"$year": "$created_at"},
      "month": {"$month": "$created_at"},
      "day": {"$dayOfMonth": "$created_at"}
    },
    "recipes_per_day": {"$sum": 1}
  }},
  {"$sort": {"_id": 1}}
])
```

### 10. Multi-Collection Recipe History
```javascript
// Combined query for all recipe types (used by backend)
// Regular recipes
var regularRecipes = db.recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
}).sort({"created_at": -1}).toArray();

// Starbucks recipes  
var starbucksRecipes = db.starbucks_recipes.find({
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"
}).sort({"created_at": -1}).toArray();

// Combine and sort in application layer
```

## Index Optimization

### Recommended Indexes
```javascript
// Primary index for user recipe queries
db.recipes.createIndex({"user_id": 1, "created_at": -1})

// Index for recipe ID lookups
db.recipes.createIndex({"id": 1})

// Index for text search
db.recipes.createIndex({
  "title": "text",
  "description": "text",
  "cuisine_type": "text"
})

// Index for category filtering
db.recipes.createIndex({"user_id": 1, "cuisine_type": 1})
```

## Query Performance Notes

### Efficient Patterns ✅
- Query by user_id first (high selectivity)
- Use compound indexes (user_id + created_at)
- Sort by indexed fields
- Limit results to prevent large result sets

### Avoid These Patterns ❌
- Full table scans without user_id filter
- Sorting by non-indexed fields
- Complex regex without proper indexes
- Unlimited result sets

## Example Usage in Backend Code

```python
# Python/FastAPI implementation
async def get_recipe_history(user_id: str):
    # Efficient query using indexes
    recipes = await db.recipes.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "recipes": recipes,
        "total_count": len(recipes)
    }
```

This query structure ensures efficient, scalable recipe tracking for any number of users and recipes.