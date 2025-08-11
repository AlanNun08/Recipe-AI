# RecipeHistoryScreen Component Documentation

## Overview
A comprehensive recipe management component that displays, filters, and manages all user-saved recipes. Features modern UI/UX with smart filtering, search capabilities, and CRUD operations.

## Location
`/frontend/src/components/RecipeHistoryScreen.js`

## Purpose
- **Recipe Display**: Show all user's saved recipes in organized cards
- **Smart Filtering**: Filter by recipe types (All, Regular, Starbucks) 
- **Recipe Management**: View details, delete recipes with confirmations
- **User Experience**: Loading states, error handling, empty state management

## Component Architecture

### State Management
```javascript
function RecipeHistoryScreen({ user, onBack, showNotification, onViewRecipe, onViewStarbucksRecipe }) {
  // Core data
  const [recipes, setRecipes] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');
  
  // Interaction state
  const [deletingIds, setDeletingIds] = useState(new Set());
}
```

## Key Features

### 1. Data Fetching & Management
```javascript
const fetchRecipes = async () => {
  if (!user?.id) {
    setError('User not found');
    setIsLoading(false);
    return;
  }

  try {
    console.log('🆕 NEW RECIPE HISTORY: Fetching recipes for user:', user.id);
    
    const response = await fetch(`${API}/api/recipes/history/${user.id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to load: ${response.status}`);
    }

    const data = await response.json();
    console.log('🆕 NEW RECIPE HISTORY: Data loaded:', data);
    
    setRecipes(data.recipes || []);
    
  } catch (error) {
    console.error('🆕 NEW RECIPE HISTORY: Error:', error);
    setError(error.message);
    showNotification(`Error loading recipes: ${error.message}`, 'error');
  } finally {
    setIsLoading(false);
  }
};
```

### 2. Smart Filtering System
```javascript
const filterOptions = [
  { id: 'all', label: 'All Recipes', icon: '🍽️' },
  { id: 'regular', label: 'Regular Recipes', icon: '🍳' },
  { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕' }
];

const filteredRecipes = recipes.filter(recipe => {
  if (selectedFilter === 'all') return true;
  if (selectedFilter === 'starbucks') return recipe.category === 'starbucks' || recipe.type === 'starbucks';
  if (selectedFilter === 'regular') return recipe.category !== 'starbucks' && recipe.type !== 'starbucks';
  return true;
});
```

### 3. Recipe Navigation
```javascript
const handleViewRecipe = (recipe) => {
  console.log('🆕 NEW RECIPE HISTORY: Viewing recipe:', recipe.title, recipe.id);
  
  if (recipe.category === 'starbucks' || recipe.type === 'starbucks') {
    onViewStarbucksRecipe?.(recipe);
  } else {
    onViewRecipe?.(recipe.id, 'history');
  }
};
```

### 4. Delete Operations with Confirmation
```javascript
const handleDelete = async (recipeId) => {
  if (!confirm('Delete this recipe?')) return;
  
  try {
    const response = await fetch(`${API}/api/recipes/${recipeId}`, { method: 'DELETE' });
    if (response.ok) {
      setRecipes(prev => prev.filter(r => r.id !== recipeId));
      showNotification('Recipe deleted', 'success');
    }
  } catch (error) {
    showNotification('Delete failed', 'error');
  }
};
```

## UI/UX Design

### Visual Design System
- **Color Scheme**: Green-to-blue gradients for distinctive branding
- **Card Layout**: Clean, modern recipe cards with hover effects
- **Typography**: Clear hierarchy with readable fonts
- **Responsive**: Mobile-first design with grid layouts

### Loading States
```javascript
if (isLoading) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-xl font-bold text-gray-800">🆕 Loading NEW Recipe History</h2>
        <p className="text-gray-600">Fetching your recipes...</p>
      </div>
    </div>
  );
}
```

### Error States
```javascript
if (error) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 text-center max-w-md">
        <h2 className="text-2xl font-bold text-red-600 mb-4">🆕 NEW Recipe History - Error</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button onClick={() => window.location.reload()} className="bg-red-500 text-white px-4 py-2 rounded mr-2">
          Retry
        </button>
        <button onClick={onBack} className="bg-gray-500 text-white px-4 py-2 rounded">
          Back
        </button>
      </div>
    </div>
  );
}
```

### Empty States
```javascript
{filteredRecipes.length === 0 ? (
  <div className="text-center py-12">
    <div className="bg-white rounded-lg shadow-lg p-8">
      <div className="text-4xl mb-4">📝</div>
      <h3 className="text-xl font-bold text-gray-800 mb-4">No Recipes Found</h3>
      <p className="text-gray-600">No recipes match your current filter.</p>
    </div>
  </div>
) : (
  // Recipe grid content
)}
```

## Recipe Card Component

### Card Structure
```javascript
<div className="bg-white rounded-lg shadow-lg overflow-hidden">
  {/* Header with recipe type and category */}
  <div className={`p-4 text-white ${isStarbucks ? 'bg-green-500' : 'bg-blue-500'}`}>
    <div className="flex items-center justify-between mb-2">
      <span className="text-2xl">{isStarbucks ? '☕' : '🍳'}</span>
      <span className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded">
        🆕 {isStarbucks ? 'Starbucks' : 'Recipe'}
      </span>
    </div>
    <h3 className="text-lg font-bold">
      {recipe.title || recipe.drink_name || recipe.name || 'Untitled'}
    </h3>
    <p className="text-xs opacity-90">
      {recipe.created_at ? new Date(recipe.created_at).toLocaleDateString() : 'Unknown date'}
    </p>
  </div>

  {/* Content with description and stats */}
  <div className="p-4">
    <p className="text-gray-600 text-sm mb-4">
      {recipe.description || 'No description available'}
    </p>
    
    {/* Recipe-specific stats or Starbucks info */}
    
    {/* Action buttons */}
    <div className="flex gap-2">
      <button onClick={() => handleViewRecipe(recipe)} className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-3 rounded text-sm">
        👀 View
      </button>
      <button onClick={() => handleDelete(recipe.id)} className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-3 rounded text-sm">
        🗑️
      </button>
    </div>
  </div>
</div>
```

## API Integration

### Required Endpoints
1. **Get Recipe History**: `GET /api/recipes/history/{user_id}`
2. **Delete Recipe**: `DELETE /api/recipes/{recipe_id}`

### Expected Data Format
```javascript
{
  "recipes": [
    {
      "id": "uuid",
      "title": "Recipe Name",
      "description": "Recipe description",
      "cuisine_type": "italian",
      "prep_time": "30 minutes",
      "cook_time": "25 minutes",
      "servings": 4,
      "difficulty": "medium",
      "created_at": "2025-01-01T12:00:00Z",
      "category": "regular", // or "starbucks"
      "type": "recipe" // or "starbucks"
    }
  ],
  "total_count": 25
}
```

## Integration with App.js

### Props Interface
```javascript
interface RecipeHistoryScreenProps {
  user: {
    id: string;
    email: string;
    // ... other user properties
  };
  onBack: () => void;
  showNotification: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;
  onViewRecipe: (recipeId: string, source: string) => void;
  onViewStarbucksRecipe?: (recipe: object) => void;
}
```

### Usage in App.js
```javascript
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
      setCurrentStarbucksRecipe(recipe);
      setCurrentScreen('starbucks-generator');
    }}
  />;
```

## Testing Strategy

### Unit Tests
```javascript
// RecipeHistoryScreen.test.js
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
        json: () => Promise.resolve({ recipes: mockRecipes })
      })
    );
    
    render(<RecipeHistoryScreen {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    });
  });
  
  test('handles recipe deletion', async () => {
    // Test deletion flow
  });
  
  test('filters recipes by type', () => {
    // Test filtering functionality
  });
});
```

### Integration Tests
- Test API endpoint integration
- Verify navigation between screens
- Check error handling flows

## Performance Optimization

### 1. Memoization
```javascript
const filteredRecipes = useMemo(() => {
  return recipes.filter(recipe => {
    // Filter logic
  });
}, [recipes, selectedFilter]);

const RecipeCard = React.memo(({ recipe, onView, onDelete }) => {
  // Recipe card implementation
});
```

### 2. Virtual Scrolling
For large recipe lists:
```javascript
import { FixedSizeGrid } from 'react-window';

const VirtualizedRecipeGrid = ({ recipes }) => (
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

### 3. Lazy Loading
```javascript
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadMoreRecipes = async () => {
  if (!hasMore) return;
  
  try {
    const response = await fetch(`${API}/api/recipes/history/${user.id}?page=${page}`);
    const data = await response.json();
    
    setRecipes(prev => [...prev, ...data.recipes]);
    setHasMore(data.has_more);
    setPage(prev => prev + 1);
  } catch (error) {
    console.error('Failed to load more recipes:', error);
  }
};
```

## Accessibility

### Screen Reader Support
```javascript
<div 
  role="grid"
  aria-label={`${recipes.length} recipes found`}
>
  {recipes.map(recipe => (
    <div 
      key={recipe.id}
      role="gridcell"
      aria-label={`Recipe: ${recipe.title}`}
    >
      {/* Recipe card content */}
    </div>
  ))}
</div>
```

### Keyboard Navigation
```javascript
const handleKeyDown = (e, recipe) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    handleViewRecipe(recipe);
  }
};

<div
  tabIndex={0}
  onKeyDown={(e) => handleKeyDown(e, recipe)}
  className="focus:ring-2 focus:ring-green-500"
>
  {/* Card content */}
</div>
```

## Common Issues & Solutions

### Issue: Recipes not loading
**Solution**: Check user authentication and API endpoint availability
```javascript
useEffect(() => {
  if (!user?.id) {
    setError('User not authenticated');
    setIsLoading(false);
    return;
  }
  fetchRecipes();
}, [user?.id]);
```

### Issue: Delete operations failing
**Solution**: Add proper error handling and user feedback
```javascript
const handleDelete = async (recipeId) => {
  try {
    setDeletingIds(prev => new Set([...prev, recipeId]));
    const response = await fetch(`${API}/api/recipes/${recipeId}`, { method: 'DELETE' });
    
    if (!response.ok) {
      throw new Error(`Delete failed: ${response.status}`);
    }
    
    // Success handling
  } catch (error) {
    showNotification(`Failed to delete recipe: ${error.message}`, 'error');
  } finally {
    setDeletingIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(recipeId);
      return newSet;
    });
  }
};
```

### Issue: Filter counts incorrect
**Solution**: Calculate counts dynamically
```javascript
const getFilterCount = (filterId) => {
  if (filterId === 'all') return recipes.length;
  if (filterId === 'starbucks') return recipes.filter(r => r.category === 'starbucks' || r.type === 'starbucks').length;
  if (filterId === 'regular') return recipes.filter(r => r.category !== 'starbucks' && r.type !== 'starbucks').length;
  return 0;
};
```

## Future Enhancements

### Potential Features
1. **Search Functionality**: Recipe search by name, ingredients, cuisine
2. **Sorting Options**: Sort by date, name, cuisine, difficulty
3. **Bulk Operations**: Select multiple recipes for batch delete
4. **Recipe Categories**: Custom user-defined categories
5. **Export Options**: Export recipes to PDF, email, or file
6. **Recipe Sharing**: Share recipes with other users

### Implementation Patterns
```javascript
// Search functionality
const [searchTerm, setSearchTerm] = useState('');
const searchedRecipes = filteredRecipes.filter(recipe =>
  recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
  recipe.description.toLowerCase().includes(searchTerm.toLowerCase())
);

// Bulk operations
const [selectedRecipes, setSelectedRecipes] = useState(new Set());
const handleBulkDelete = async () => {
  for (const recipeId of selectedRecipes) {
    await handleDelete(recipeId);
  }
  setSelectedRecipes(new Set());
};
```

---

**Last Updated**: January 2025
**Component Version**: 2.0.0