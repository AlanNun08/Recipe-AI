# Recipe History Integration Guide

## Quick Start

### 1. Component Integration in App.js

```javascript
import RecipeHistoryScreen from './components/RecipeHistoryScreen';

// In your switch statement
case 'all-recipes':
  return <RecipeHistoryScreen 
    user={user}
    onBack={() => setCurrentScreen('dashboard')}
    showNotification={showNotification}
    onViewRecipe={(recipeId, source = 'history') => {
      setCurrentRecipeId(recipeId);
      setCurrentRecipeSource(source);
      setCurrentScreen('recipe-detail');
    }}
    onViewStarbucksRecipe={(recipe) => {
      // Handle Starbucks recipe navigation
      setCurrentScreen('starbucks-generator');
    }}
  />;
```

### 2. Required Props

| Prop | Type | Description |
|------|------|-------------|
| `user` | Object | User object with `id` field |
| `onBack` | Function | Navigate back to dashboard |
| `showNotification` | Function | Show toast notifications |
| `onViewRecipe` | Function | Navigate to recipe detail (recipeId, source) |
| `onViewStarbucksRecipe` | Function | Navigate to Starbucks recipe (optional) |

### 3. Backend API Requirements

The component expects these endpoints:

```
GET /api/recipes/history/{user_id}
DELETE /api/recipes/{recipe_id}
```

Response format for history:
```json
{
  "recipes": [
    {
      "id": "uuid",
      "title": "Recipe Name",
      "description": "Description",
      "cuisine_type": "italian",
      "prep_time": "30 minutes",
      "cook_time": "25 minutes",
      "servings": 4,
      "difficulty": "medium",
      "created_at": "2025-01-01T12:00:00Z",
      "category": "regular",
      "type": "recipe"
    }
  ],
  "total_count": 25
}
```

## Adding New Features

### 1. Add New Recipe Type

**Step 1**: Update filter options in component:
```javascript
const filterOptions = [
  // ... existing options
  { id: 'new_type', label: 'New Type', icon: '🆕', description: 'New recipe type' }
];
```

**Step 2**: Update filtering logic:
```javascript
if (selectedFilter === 'new_type') {
  return recipe.category === 'new_type' || recipe.type === 'new_type';
}
```

**Step 3**: Update navigation handler:
```javascript
if (recipe.type === 'new_type') {
  onViewNewType?.(recipe);
} else {
  // existing logic
}
```

### 2. Add Bulk Actions

```javascript
// Add state for selected recipes
const [selectedRecipes, setSelectedRecipes] = useState(new Set());

// Add bulk action handler
const handleBulkDelete = async () => {
  const idsToDelete = Array.from(selectedRecipes);
  
  for (const id of idsToDelete) {
    await handleDeleteRecipe(id);
  }
  
  setSelectedRecipes(new Set());
};

// Add checkbox to recipe card
<input
  type="checkbox"
  checked={selectedRecipes.has(recipe.id)}
  onChange={(e) => {
    const newSelected = new Set(selectedRecipes);
    if (e.target.checked) {
      newSelected.add(recipe.id);
    } else {
      newSelected.delete(recipe.id);
    }
    setSelectedRecipes(newSelected);
  }}
/>
```

### 3. Add Recipe Categories

```javascript
// Update recipe card to show categories
const renderCategoryBadges = (recipe) => (
  <div className="flex flex-wrap gap-2 mb-2">
    {recipe.tags?.map(tag => (
      <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
        {tag}
      </span>
    ))}
  </div>
);
```

### 4. Add Export Functionality

```javascript
const handleExportRecipes = () => {
  const exportData = {
    exported_at: new Date().toISOString(),
    recipes: filteredRecipes.map(recipe => ({
      title: recipe.title,
      description: recipe.description,
      ingredients: recipe.ingredients || [],
      instructions: recipe.instructions || []
    }))
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {
    type: 'application/json'
  });
  
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `recipes-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  
  URL.revokeObjectURL(url);
};
```

## Testing

### Unit Test Example

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RecipeHistoryScreen from './RecipeHistoryScreen';

const mockProps = {
  user: { id: 'test-user-id' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  onViewRecipe: jest.fn(),
  onViewStarbucksRecipe: jest.fn()
};

describe('RecipeHistoryScreen', () => {
  test('loads and displays recipes', async () => {
    const mockRecipes = [
      { id: '1', title: 'Test Recipe', created_at: '2025-01-01T12:00:00Z' }
    ];
    
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ recipes: mockRecipes, total_count: 1 })
      })
    );
    
    render(<RecipeHistoryScreen {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    });
    
    expect(screen.getByText('1 total recipes')).toBeInTheDocument();
  });
  
  test('handles recipe view navigation', async () => {
    // ... test implementation
  });
  
  test('handles recipe deletion', async () => {
    // ... test implementation
  });
});
```

## Performance Optimization

### For Large Recipe Lists

1. **Virtual Scrolling** (if >100 recipes):
```javascript
import { FixedSizeGrid } from 'react-window';

const VirtualizedGrid = ({ recipes }) => (
  <FixedSizeGrid
    columnCount={3}
    columnWidth={350}
    height={600}
    rowCount={Math.ceil(recipes.length / 3)}
    rowHeight={250}
    itemData={recipes}
  >
    {RecipeGridItem}
  </FixedSizeGrid>
);
```

2. **Lazy Loading**:
```javascript
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadMoreRecipes = useCallback(async () => {
  if (!hasMore) return;
  
  const response = await fetch(`${API}/api/recipes/history/${user.id}?page=${page}`);
  const data = await response.json();
  
  setRecipes(prev => [...prev, ...data.recipes]);
  setHasMore(data.has_more);
  setPage(prev => prev + 1);
}, [page, hasMore, user.id]);
```

## Troubleshooting

### Common Issues

1. **"No recipes found"** despite having recipes:
   - Check API endpoint returns correct format
   - Verify user.id is passed correctly
   - Check browser network tab for failed requests

2. **Recipe cards not showing properly**:
   - Verify recipe objects have required fields (id, title, created_at)
   - Check console for rendering errors
   - Validate recipe.category/type values

3. **Delete not working**:
   - Verify DELETE endpoint exists and works
   - Check browser console for API errors
   - Ensure recipe ID is passed correctly

4. **Navigation not working**:
   - Check onViewRecipe prop is passed
   - Verify recipe.id is valid UUID
   - Check parent component navigation logic

### Debug Tips

Enable debug mode by setting localStorage:
```javascript
localStorage.setItem('recipe-history-debug', 'true');
```

This will show additional console logs for troubleshooting.

For more details, see `/docs/RECIPE_HISTORY_ARCHITECTURE.md`