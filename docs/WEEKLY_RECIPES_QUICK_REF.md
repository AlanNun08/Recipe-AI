# 🚀 Weekly Recipes - Quick Reference Guide

## How It Works

### User Journey
1. User navigates to "Weekly Recipes" screen
2. User clicks "Generate Weekly Meal Plan"
3. User selects preferences (family size, dietary, cuisines, budget)
4. AI generates 7-day meal plan with complete recipes
5. Each meal displays in a beautiful card with:
   - Quick stats (prep time, cook time, servings, difficulty)
   - Full ingredients list
   - Nutrition information
   - Chef's tips
   - Estimated cost
6. User can click "View Recipe & Shop" to:
   - See full recipe details
   - Browse Walmart products
   - Add items to cart
   - Generate shopping list

---

## Key Files

| File | Purpose | Key Functions |
|------|---------|---|
| `backend/server.py` | API endpoints | `generate_weekly_plan()`, `get_current_weekly_plan()` |
| `frontend/WeeklyRecipesScreen.js` | Main view | Meal card rendering, meal display logic |
| `frontend/RecipeDetailScreen.js` | Detail view | Full recipe & Walmart products |
| `frontend/App.js` | Routing | Navigation between screens |

---

## API Endpoints

### Generate Plan
```
POST /api/weekly-recipes/generate
Body: { user_id, family_size, budget, dietary_preferences, cuisines, meal_types, cooking_time_preference }
Returns: Weekly plan with 7 complete meal objects
```

### Get Current Plan
```
GET /api/weekly-recipes/current/{user_id}
Returns: Current weekly plan with all meals
```

### View Individual Recipe
```
GET /api/recipes/{recipe_id}/detail
Returns: Full recipe details (works for weekly meals too!)
```

### Walmart Products
```
GET /api/recipes/{recipe_id}/cart-options
Returns: Walmart products for all ingredients
Works for weekly meals because they have ingredients_clean!
```

---

## Database Collections

### recipes_collection
Contains ALL recipes:
- Individual user-generated recipes
- AI-generated recipes
- **Weekly meal recipes** (marked with `is_weekly_meal: true`)

Query to find weekly meals:
```javascript
db.recipes_collection.find({ is_weekly_meal: true, user_id: "xxx" })
```

### weekly_recipes_collection
Contains plan metadata:
- Plan ID, user ID, week info
- Array of meal IDs (references to recipes_collection)
- Total cost, family size, timestamps

---

## UI Layout Breakdown

### Card Sections (Top to Bottom)
1. **Header** (Purple-Pink Gradient)
   - Day of week | Meal type | Cost indicator

2. **Quick Stats** (2x2 Grid)
   - Prep time | Cook time
   - Servings | Difficulty

3. **Recipe Info**
   - Name, description
   - Cuisine badge, cost

4. **Ingredients**
   - First 5 items shown
   - Scrollable list

5. **Nutrition**
   - Calories, protein, carbs, fat
   - Color-coded badges

6. **Tips**
   - First chef's tip in callout box

7. **Button**
   - "View Recipe & Shop" (Green-Blue Gradient)

---

## Responsive Breakpoints

```css
/* Mobile (default) */
.grid-cols-1        /* 1 column */

/* Tablet */
md:grid-cols-2      /* 2 columns at 768px+ */

/* Desktop */
lg:grid-cols-3      /* 3 columns at 1024px+ */
```

---

## Styling Reference

### Colors
```javascript
// Headers
from-purple-500 to-pink-500

// Buttons
from-green-500 to-blue-500

// Stats
- Prep: blue-50/blue-700
- Cook: orange-50/orange-700
- Servings: green-50/green-700
- Difficulty: purple-50/purple-700

// Badges
- Cuisine: indigo-100/indigo-700
- Cost: green-100/green-700
- Nutrition: yellow/red/orange/green-50
```

---

## Common Tasks

### Adding New Meal Field to Display
1. Edit `WeeklyRecipesScreen.js` card rendering
2. Add new JSX section with proper styling
3. Use emoji + text label for consistency
4. Add null check: `meal.field && ...`

### Changing Card Layout
1. Modify grid in `WeeklyRecipesScreen.js`:
   ```jsx
   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
   ```
2. Change breakpoint classes as needed
3. Test on mobile/tablet/desktop

### Modifying AI Prompt for Meals
1. Edit `backend/server.py` line ~1100
2. Update the `prompt = f"""..."""` string
3. Specify exact JSON structure you want
4. Test by generating a plan

### Fixing Missing Data
1. Check API response structure first
2. Add optional field handling:
   ```jsx
   {meal.field && <div>{meal.field}</div>}
   ```
3. Or add fallback text:
   ```jsx
   {meal.field || 'Not available'}
   ```

---

## Troubleshooting

### Cards Not Showing
- Check: Are meals in plan? `currentPlan.meals?.length > 0`
- Check: Backend returning meal data?
- Check: Console for errors

### Missing Information
- Check: `ingredients_clean` present? (needed for Walmart)
- Check: Nutrition object structure correct?
- Check: Optional fields properly handled with `&&`

### Styling Issues
- Check: Tailwind CSS classes correct?
- Check: Responsive breakpoints working?
- Check: Color classes spelled correctly (no typos)?

### Walmart Products Not Found
- Check: `ingredients_clean` field exists?
- Check: Clean ingredient names searchable?
- Check: Backend properly generating fallback?

---

## Performance Tips

### Optimize Card Rendering
- Use keys: `key={meal.id}`
- Lazy load images if added
- Memoize child components if needed

### Database Optimization
- Index `user_id` in both collections
- Index `weekly_plan_id` in recipes_collection
- Compound index: `(user_id, is_weekly_meal)` for filtering

### API Optimization
- Cache weekly plans for 1 hour
- Batch meal fetches in backend
- Limit meal_ids array in response if needed

---

## Testing Checklist

- [ ] Plan generates successfully
- [ ] 7 meals appear in cards
- [ ] All quick stats visible
- [ ] Ingredients list shows (first 5)
- [ ] Nutrition grid displays
- [ ] Chef's tips showing
- [ ] Cost indicators correct
- [ ] "View Recipe & Shop" navigates
- [ ] Walmart products load
- [ ] Back button returns to plan
- [ ] Mobile responsive (test at 375px)
- [ ] Tablet responsive (test at 768px)
- [ ] Desktop responsive (test at 1024px)
- [ ] No console errors
- [ ] Loading states working
- [ ] Error states handled
- [ ] Empty state displays if no meals

---

## Documentation References

- `WEEKLY_RECIPES_FIX.md` - Backend details
- `WEEKLY_RECIPES_VIEW_UPDATE.md` - Frontend details
- `WEEKLY_RECIPES_COMPLETE.md` - Full summary
- `WEEKLY_RECIPES_UI_SPECS.md` - Visual specs
- `IMPLEMENTATION_VERIFICATION.md` - Verification details

---

## Future Enhancements

1. **Meal Swapping** - Replace meals with similar recipes
2. **Plan Sharing** - Share plans with family
3. **Favorites** - Save favorite weekly plans
4. **Customization** - Edit individual meals in plan
5. **Prep Guides** - Step-by-step weekly prep instructions
6. **Batch Cooking** - Identify recipes that share ingredients

---

## Support Commands

```bash
# Backend logs
tail -f backend.log | grep "Weekly plan"

# Frontend console (in browser DevTools)
console.log(currentPlan)     // Check data structure
console.log(meal)            // Check individual meal

# Database query (for checking data)
db.recipes_collection.find({ is_weekly_meal: true }).limit(1)
db.weekly_recipes_collection.find({}).limit(1)
```

---

## Quick Deploy Checklist

- [ ] Backend changes deployed
- [ ] Frontend changes built and deployed
- [ ] Test weekly plan generation
- [ ] Verify card display
- [ ] Check Walmart product search works
- [ ] Test back navigation
- [ ] Verify mobile responsive
- [ ] Check error states
- [ ] Monitor logs for errors
- [ ] Get user feedback

---

**Last Updated**: December 18, 2025  
**Status**: ✅ Production Ready
