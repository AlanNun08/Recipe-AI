# Weekly Recipes Structure Alignment

## Overview
Updated the weekly recipe generation system to ensure each meal in a weekly plan is created exactly like individual recipes, with all required fields for proper database storage and querying.

## Changes Made

### 1. Updated `@app.post("/weekly-recipes/generate")` Endpoint

**Key Improvements:**

#### AI Prompt Enhancement
- Updated the OpenAI prompt to request **full recipe schema** for each meal including:
  - `ingredients_clean`: Simplified ingredient names for Walmart product search
  - `instructions`: Step-by-step cooking instructions
  - `nutrition`: Complete nutrition information
  - `cooking_tips`: Expert cooking advice
  - `total_time`: Total time calculation
  - Proper time format: "X minutes" instead of "X mins"

#### Meal Processing
Each meal now includes:
```python
{
    "id": unique_meal_id,
    "user_id": user_id,
    "weekly_plan_id": plan_id,
    "day_of_week": "Monday",
    "name": "...",
    "description": "...",
    "cuisine_type": "...",
    "meal_type": "...",
    "difficulty": "...",
    "prep_time": "...",
    "cook_time": "...",
    "total_time": "...",
    "servings": family_size,
    "ingredients": [...],
    "ingredients_clean": [...],  // Key for Walmart search
    "instructions": [...],
    "nutrition": {...},
    "cooking_tips": [...],
    "estimated_cost": 0.00,
    "created_at": datetime,
    "ai_generated": true,
    "source": "weekly_plan",
    "is_weekly_meal": true
}
```

#### Database Storage
- **Each meal is saved as an individual recipe** in `recipes_collection`
- This allows weekly meals to be searched, filtered, and used exactly like regular recipes
- Weekly plan metadata is stored in `weekly_recipes_collection` with references to meal IDs
- Fallback mechanism: If `ingredients_clean` is missing, it's generated from ingredients using `clean_ingredient_for_search()`

### 2. Updated `@app.get("/weekly-recipes/current/{user_id}")` Endpoint

**Key Improvements:**

- Fetches the most recent weekly plan from `weekly_recipes_collection`
- Retrieves all individual meal recipes using the `meal_ids` array
- Returns complete meal recipes with all fields
- Response structure includes all meal details for frontend consumption

**Response Format:**
```json
{
    "has_plan": true,
    "plan": {
        "id": "plan-id",
        "user_id": "user-id",
        "week_of": "2024-XX-XX",
        "family_size": 4,
        "total_estimated_cost": 200,
        "meal_ids": ["meal-1", "meal-2", ...],
        "created_at": "2024-XX-XXTXX:XX:XX",
        "ai_generated": true,
        "meals": [
            {
                "id": "meal-1",
                "day_of_week": "Monday",
                "name": "...",
                // ... all recipe fields
            },
            // ... 6 more meals
        ]
    }
}
```

## Benefits

✅ **Database Consistency**: Weekly meals use identical schema to individual recipes
✅ **Walmart Integration**: Each meal can use Walmart product search via `ingredients_clean`
✅ **Reusability**: Weekly meals can be saved, shared, and used like regular recipes
✅ **Querying**: Weekly meals can be filtered by meal_type, cuisine_type, difficulty, etc.
✅ **Cost Estimation**: Estimated costs are available for budget tracking
✅ **Fallback Safety**: Missing `ingredients_clean` is auto-generated from ingredients

## Technical Details

### Key Fields Added to Weekly Meals
- `ingredients_clean`: Required for Walmart API product search
- `is_weekly_meal`: Boolean flag to identify meals from weekly plans
- `weekly_plan_id`: Reference back to the parent weekly plan
- `day_of_week`: Which day of the week this meal is for
- `source`: Set to "weekly_plan" to track origin

### Database Collections
- **recipes_collection**: Now contains both individual recipes AND weekly meal recipes
- **weekly_recipes_collection**: Contains weekly plan metadata with meal ID references

### API Contract
The `/weekly-recipes/generate` and `/weekly-recipes/current/{user_id}` endpoints now return complete recipe objects, allowing frontend to treat weekly meals identically to regular recipes in recipe detail screens.

## Frontend Compatibility

The frontend can now:
- Display weekly meals in `RecipeDetailScreen` using the same component as regular recipes
- Show Walmart product search for weekly meals
- Use the cost indicator feature ($, $$, $$$)
- Copy ingredients for shopping
- Share individual meals from weekly plans
- View complete nutrition information for each meal

## Testing Notes

To verify the implementation:
1. Generate a weekly plan via POST `/weekly-recipes/generate`
2. Check that each meal has `ingredients_clean` field
3. Retrieve plan via GET `/weekly-recipes/current/{user_id}`
4. Verify meals can be used with `/api/recipes/{id}/cart-options` for Walmart products
5. Confirm individual meals can be retrieved from `recipes_collection` with `is_weekly_meal: true`
