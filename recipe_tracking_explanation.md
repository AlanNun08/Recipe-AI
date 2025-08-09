# 📊 Recipe History Tracking System

## Overview
The AI Recipe + Grocery Delivery App tracks recipe history for each user through a comprehensive MongoDB-based system that stores, categorizes, and retrieves recipes across multiple collections.

## 🗄️ Database Architecture

### Primary Collections
```
buildyoursmartcart_development/
├── recipes                      # Main recipe collection
├── starbucks_recipes           # User-generated Starbucks drinks  
├── curated_starbucks_recipes   # Pre-built Starbucks recipes
└── weekly_recipes              # Weekly meal plans
```

### Recipe Data Schema
```javascript
// Main Recipe Document Structure
{
  "id": "550e8400-e29b-41d4-a716-446655440000",           // UUID primary key
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",     // User association
  "title": "Creamy Mushroom Risotto",                      // Recipe name
  "description": "Rich and creamy Arborio rice...",        // Recipe description
  "ingredients": ["1 cup Arborio rice", "2 cups broth"],   // Ingredients list
  "instructions": ["Heat oil...", "Add rice..."],          // Step-by-step instructions
  "prep_time": 15,                                         // Preparation time (minutes)
  "cook_time": 30,                                         // Cooking time (minutes) 
  "servings": 4,                                           // Number of servings
  "cuisine_type": "Italian",                               // Cuisine classification
  "dietary_tags": ["Vegetarian"],                          // Dietary restrictions
  "difficulty": "medium",                                  // easy/medium/hard
  "calories_per_serving": 420,                             // Nutritional info (optional)
  "is_healthy": false,                                     // Health classification
  "created_at": "2025-08-09T19:30:00.000Z",               // Timestamp (UTC)
  "shopping_list": ["arborio rice", "vegetable broth"]     // Walmart API ingredients
}
```

## 🔄 Recipe Creation & Storage Process

### 1. Recipe Generation
```python
# When user generates a recipe
POST /api/recipes/generate
{
  "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",
  "cuisine_type": "Italian",
  "meal_type": "dinner",
  "servings": 4,
  "difficulty": "medium",
  "dietary_preferences": ["Vegetarian"]
}

# Backend Process:
1. Generate recipe content (AI or mock data)
2. Create Recipe object with auto-generated UUID
3. Set created_at timestamp (UTC)
4. Associate with user_id
5. Insert into MongoDB recipes collection
```

### 2. Automatic Tracking Fields
```python
# Automatically added during recipe creation:
id = str(uuid.uuid4())                    # Unique identifier
created_at = datetime.utcnow()            # Timestamp
user_id = request.user_id                 # User association
```

## 📚 Recipe History Retrieval

### API Endpoint
```
GET /api/recipes/history/{user_id}
```

### Retrieval Process
```python
async def get_recipe_history(user_id: str):
    # 1. Get regular recipes for user
    recipes = await db.recipes.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    
    # 2. Get Starbucks recipes for user  
    starbucks_recipes = await db.starbucks_recipes.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    
    # 3. Categorize and merge all recipes
    # 4. Sort by created_at (newest first)
    # 5. Return paginated results (limit 100)
```

### Response Structure
```javascript
{
  "success": true,
  "recipes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Pad Thai with Shrimp", 
      "category": "cuisine",           // Auto-categorized
      "category_label": "Cuisine",     // Display label
      "category_icon": "🍝",           // UI icon
      "type": "recipe",                // recipe/starbucks
      "created_at": "2025-08-09T19:30:00.000Z",
      "user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731",
      // ... other recipe fields
    }
  ],
  "total_count": 25,
  "regular_recipes": 20,
  "starbucks_recipes": 5
}
```

## 🏷️ Automatic Categorization

### Category Logic
```python
# Smart categorization based on content analysis:

if 'snack' in cuisine_type.lower() or any(word in title.lower() for word in ['bowl', 'bite', 'snack']):
    category = 'snacks' 🍪
elif 'beverage' in cuisine_type.lower() or any(word in title.lower() for word in ['drink', 'tea']):
    category = 'beverages' 🧋  
elif recipe_type == 'starbucks':
    category = 'starbucks' ☕
else:
    category = 'cuisine' 🍝
```

## 🔍 Recipe Filtering & Search

### Frontend Filtering
```javascript
// Users can filter by category
filterOptions = [
  { id: 'all', label: 'All Recipes', icon: '🍽️' },
  { id: 'cuisine', label: 'Regular Recipes', icon: '🍳' },
  { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕' }
]

// Filter recipes client-side
const filteredRecipes = recipes.filter(recipe => {
  if (filter === 'all') return true;
  return recipe.category === filter;
});
```

## ⏱️ Timestamp Management

### UTC Storage
- All timestamps stored in UTC: `2025-08-09T19:30:00.000Z`
- Frontend converts to local time for display
- Sorting always done by UTC timestamp for consistency

### Sorting Order
```python
# Newest recipes first (descending order)
.sort("created_at", -1)
```

## 🔗 User Association

### User Linking
```python
# Every recipe linked to user via user_id field
"user_id": "f99be98f-c1d5-4ccc-a3ad-9b62e01f4731"

# Query all recipes for a user:
db.recipes.find({"user_id": user_id})
```

### Privacy & Isolation
- Users only see their own recipes
- No cross-user recipe access
- User deletion would cascade to delete all associated recipes

## 📊 Analytics Tracking

### Available Metrics
- Total recipe count per user
- Recipes by category (cuisine vs starbucks vs snacks)
- Recipe generation patterns over time
- Popular cuisines per user
- Difficulty preferences

### Usage Statistics
```javascript
{
  "total_count": 25,          // All recipes
  "regular_recipes": 20,      // Food recipes  
  "starbucks_recipes": 5,     // Drink recipes
  "categories": {
    "cuisine": 18,
    "starbucks": 5,
    "snacks": 2,
    "beverages": 0
  }
}
```

## 🗑️ Recipe Management

### Deletion
```python
# Delete single recipe
db.recipes.delete_one({"id": recipe_id, "user_id": user_id})

# Delete all user recipes (reset history)
db.recipes.delete_many({"user_id": user_id})
```

### Modification
- Recipes are immutable once created
- New versions create new recipe entries
- Original timestamps preserved

## 🔄 Data Flow Summary

```
1. User Request → Generate Recipe
2. Recipe Created → Auto-assign UUID + Timestamp + User ID  
3. Save to MongoDB → recipes collection
4. User Views History → Query by user_id, sort by created_at
5. Frontend Display → Categorize, filter, paginate
6. User Clicks Recipe → Retrieve by recipe ID
7. Show Details → Same recipe guaranteed via ID matching
```

This comprehensive tracking system ensures every user has a complete, chronological history of their recipe generations with full data integrity and privacy isolation.