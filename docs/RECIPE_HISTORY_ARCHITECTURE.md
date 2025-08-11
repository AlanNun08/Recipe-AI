# Recipe History Architecture & Integration Guide

## Overview
This document outlines the architecture, design patterns, and integration guidelines for the Recipe History feature in the AI Chef application.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Structure](#component-structure)
3. [API Integration](#api-integration)
4. [State Management](#state-management)
5. [Navigation Flow](#navigation-flow)
6. [Testing Strategy](#testing-strategy)
7. [Feature Integration Guidelines](#feature-integration-guidelines)
8. [Common Patterns](#common-patterns)

## Architecture Overview

### Design Principles
1. **Single Responsibility**: Each component has one clear purpose
2. **Separation of Concerns**: UI, business logic, and data fetching are separated
3. **Error Boundaries**: Graceful error handling at every level
4. **Progressive Enhancement**: Core functionality works, enhanced features are optional
5. **Accessibility First**: Screen reader friendly, keyboard navigation support

### Technology Stack
- **Frontend**: React 18 with Hooks
- **State Management**: React useState/useEffect (no external state manager needed)
- **API Communication**: Fetch API with proper error handling
- **Styling**: Tailwind CSS with component-specific classes
- **Navigation**: React Router (handled by parent App component)

## Component Structure

### File Organization
```
/frontend/src/components/
├── RecipeHistoryScreen.js      # Main component
├── RecipeHistoryCard.js        # Individual recipe card (optional)
├── RecipeHistoryFilters.js     # Filter controls (optional)
└── RecipeHistoryEmpty.js       # Empty state (optional)
```

### Component Hierarchy
```
RecipeHistoryScreen
├── Header Section
│   ├── Back Button
│   ├── Title & Description
│   └── Filter Controls
├── Recipe Grid
│   ├── Recipe Card (repeated)
│   │   ├── Recipe Image/Icon
│   │   ├── Recipe Metadata
│   │   ├── Action Buttons
│   │   └── Delete Confirmation
│   └── Empty State
└── Loading States
```

## API Integration

### Primary Endpoints
```javascript
// Get user's recipe history
GET /api/recipes/history/{user_id}
Response: {
  recipes: [
    {
      id: "uuid",
      title: "Recipe Name",
      description: "Recipe description",
      cuisine_type: "italian",
      prep_time: "30 minutes",
      cook_time: "25 minutes",
      servings: 4,
      difficulty: "medium",
      created_at: "2025-01-01T12:00:00Z",
      category: "cuisine|starbucks",
      type: "recipe|starbucks"
    }
  ],
  total_count: 25,
  page: 1,
  per_page: 20
}

// Delete a recipe
DELETE /api/recipes/{recipe_id}
Response: {
  success: true,
  message: "Recipe deleted successfully"
}
```

### API Integration Patterns

#### 1. Data Fetching with Error Handling
```javascript
const fetchRecipeHistory = async () => {
  try {
    setIsLoading(true);
    setError(null);
    
    const response = await fetch(`${API}/api/recipes/history/${user.id}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Validate response structure
    if (!data.recipes || !Array.isArray(data.recipes)) {
      throw new Error('Invalid response format');
    }
    
    setRecipes(data.recipes);
    setTotalCount(data.total_count || data.recipes.length);
    
  } catch (error) {
    console.error('Failed to fetch recipe history:', error);
    setError(error.message);
    showNotification('Failed to load recipe history', 'error');
  } finally {
    setIsLoading(false);
  }
};
```

#### 2. Optimistic Updates for Deletions
```javascript
const deleteRecipe = async (recipeId) => {
  // Optimistic update
  const originalRecipes = [...recipes];
  setRecipes(prev => prev.filter(r => r.id !== recipeId));
  
  try {
    const response = await fetch(`${API}/api/recipes/${recipeId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      throw new Error('Delete failed');
    }
    
    showNotification('Recipe deleted successfully', 'success');
    
  } catch (error) {
    // Revert optimistic update
    setRecipes(originalRecipes);
    showNotification('Failed to delete recipe', 'error');
  }
};
```

## State Management

### Component State Structure
```javascript
const RecipeHistoryScreen = ({ user, onBack, showNotification, onViewRecipe }) => {
  // Core data
  const [recipes, setRecipes] = useState([]);
  const [filteredRecipes, setFilteredRecipes] = useState([]);
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');
  
  // Interaction state
  const [deletingRecipeId, setDeletingRecipeId] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  
  // Meta data
  const [totalCount, setTotalCount] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  // ... component logic
};
```

### State Update Patterns

#### 1. Loading States
```javascript
// Loading pattern
const [loadingStates, setLoadingStates] = useState({
  initial: true,
  deleting: {},
  refreshing: false
});

// Usage
setLoadingStates(prev => ({
  ...prev,
  deleting: { ...prev.deleting, [recipeId]: true }
}));
```

#### 2. Error Handling
```javascript
// Error state management
const [errors, setErrors] = useState({
  fetch: null,
  delete: {},
  network: null
});

// Clear errors when appropriate
useEffect(() => {
  if (recipes.length > 0) {
    setErrors(prev => ({ ...prev, fetch: null }));
  }
}, [recipes]);
```

## Navigation Flow

### Integration with App.js
```javascript
// In App.js - Navigation handler
const handleViewRecipe = (recipeId, source = 'history') => {
  // Validate inputs
  if (!recipeId) {
    showNotification('❌ Recipe ID is missing', 'error');
    return;
  }
  
  // Set navigation state
  setCurrentRecipeId(recipeId);
  setCurrentRecipeSource(source);
  setCurrentScreen('recipe-detail');
};

// Recipe History Screen props
<RecipeHistoryScreen 
  user={user}
  onBack={() => setCurrentScreen('dashboard')}
  showNotification={showNotification}
  onViewRecipe={handleViewRecipe}
  onViewStarbucksRecipe={handleViewStarbucksRecipe}
/>
```

### Navigation State Management
```javascript
// Navigation context in component
const handleRecipeClick = (recipe) => {
  // Determine recipe type and source
  const recipeType = recipe.category || recipe.type;
  const source = 'history';
  
  // Route to appropriate handler
  if (recipeType === 'starbucks') {
    onViewStarbucksRecipe?.(recipe);
  } else {
    onViewRecipe?.(recipe.id, source);
  }
};
```

## Testing Strategy

### Unit Tests
```javascript
// Test data fetching
test('should fetch and display recipe history', async () => {
  const mockRecipes = [
    { id: '1', title: 'Test Recipe', created_at: '2025-01-01T12:00:00Z' }
  ];
  
  fetchMock.mockResponseOnce(JSON.stringify({ recipes: mockRecipes }));
  
  render(<RecipeHistoryScreen user={mockUser} />);
  
  await waitFor(() => {
    expect(screen.getByText('Test Recipe')).toBeInTheDocument();
  });
});

// Test error handling
test('should handle fetch errors gracefully', async () => {
  fetchMock.mockRejectOnce(new Error('Network error'));
  
  render(<RecipeHistoryScreen user={mockUser} showNotification={mockNotify} />);
  
  await waitFor(() => {
    expect(mockNotify).toHaveBeenCalledWith('Failed to load recipe history', 'error');
  });
});
```

### Integration Tests
```javascript
// Test navigation flow
test('should navigate to recipe detail when clicking view', async () => {
  const mockOnViewRecipe = jest.fn();
  const mockRecipes = [{ id: '1', title: 'Test Recipe' }];
  
  render(
    <RecipeHistoryScreen 
      user={mockUser} 
      onViewRecipe={mockOnViewRecipe}
    />
  );
  
  // Mock API response
  await waitFor(() => {
    expect(screen.getByText('Test Recipe')).toBeInTheDocument();
  });
  
  // Click view button
  fireEvent.click(screen.getByText('View Details'));
  
  expect(mockOnViewRecipe).toHaveBeenCalledWith('1', 'history');
});
```

## Feature Integration Guidelines

### 1. Adding New Recipe Types

#### Step 1: Update Backend Response
```javascript
// Add new recipe type to API response
{
  id: "uuid",
  title: "Recipe Name",
  type: "new_type", // Add new type
  category: "new_category", // Add new category
  // ... other fields
}
```

#### Step 2: Update Frontend Filtering
```javascript
// Add filter option
const filterOptions = [
  { id: 'all', label: 'All Recipes', icon: '🍽️' },
  { id: 'cuisine', label: 'Regular Recipes', icon: '🍳' },
  { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕' },
  { id: 'new_type', label: 'New Type', icon: '🆕' } // Add new filter
];

// Update filter logic
const filteredRecipes = recipes.filter(recipe => {
  if (filter === 'all') return true;
  if (filter === 'new_type') return recipe.type === 'new_type';
  return recipe.category === filter;
});
```

#### Step 3: Update Navigation Handling
```javascript
const handleViewRecipe = (recipe) => {
  if (recipe.type === 'new_type') {
    onViewNewType?.(recipe);
  } else if (recipe.type === 'starbucks') {
    onViewStarbucksRecipe?.(recipe);
  } else {
    onViewRecipe?.(recipe.id, 'history');
  }
};
```

### 2. Adding New Actions

#### Step 1: Add UI Elements
```javascript
// Add new action button
<div className="flex gap-3">
  <button onClick={() => handleViewRecipe(recipe)}>
    👀 View Details
  </button>
  <button onClick={() => handleNewAction(recipe)}>
    🆕 New Action
  </button>
  <button onClick={() => deleteRecipe(recipe.id)}>
    🗑️ Delete
  </button>
</div>
```

#### Step 2: Implement Action Handler
```javascript
const handleNewAction = async (recipe) => {
  try {
    setActionLoading(recipe.id, true);
    
    const response = await fetch(`${API}/api/recipes/${recipe.id}/new-action`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error('Action failed');
    }
    
    showNotification('Action completed successfully', 'success');
    
  } catch (error) {
    showNotification('Action failed', 'error');
  } finally {
    setActionLoading(recipe.id, false);
  }
};
```

### 3. Adding New Metadata Fields

#### Step 1: Update Recipe Card Display
```javascript
// Add new metadata to recipe card
<div className="grid grid-cols-2 gap-4 mb-6">
  <MetadataField icon="⏱️" label="Prep Time" value={recipe.prep_time} />
  <MetadataField icon="👥" label="Servings" value={recipe.servings} />
  <MetadataField icon="🆕" label="New Field" value={recipe.new_field} />
</div>
```

#### Step 2: Handle Missing Data
```javascript
const MetadataField = ({ icon, label, value }) => (
  <div className="text-center bg-gray-50 rounded-lg p-3">
    <div className="text-lg">{icon}</div>
    <div className="text-xs text-gray-600">{label}</div>
    <div className="font-bold text-sm">
      {value || 'N/A'}
    </div>
  </div>
);
```

## Common Patterns

### 1. Conditional Rendering
```javascript
// Loading state
if (isLoading) {
  return <LoadingSpinner message="Loading your recipes..." />;
}

// Error state
if (error) {
  return <ErrorMessage error={error} onRetry={fetchRecipeHistory} />;
}

// Empty state
if (recipes.length === 0) {
  return <EmptyState onCreateNew={() => setCurrentScreen('recipe-generation')} />;
}

// Success state - render recipe grid
return <RecipeGrid recipes={filteredRecipes} />;
```

### 2. Event Handling with Loading States
```javascript
const handleAction = async (id, action) => {
  try {
    setLoadingState(id, action, true);
    
    await performAction(id, action);
    
    showNotification('Action completed', 'success');
    
  } catch (error) {
    showNotification('Action failed', 'error');
  } finally {
    setLoadingState(id, action, false);
  }
};
```

### 3. Debounced Search/Filter
```javascript
const [searchTerm, setSearchTerm] = useState('');
const [debouncedSearch, setDebouncedSearch] = useState('');

useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedSearch(searchTerm);
  }, 300);
  
  return () => clearTimeout(timer);
}, [searchTerm]);

useEffect(() => {
  const filtered = recipes.filter(recipe =>
    recipe.title.toLowerCase().includes(debouncedSearch.toLowerCase())
  );
  setFilteredRecipes(filtered);
}, [recipes, debouncedSearch]);
```

## Performance Considerations

### 1. Virtualization for Large Lists
```javascript
import { FixedSizeList as List } from 'react-window';

const VirtualizedRecipeList = ({ recipes }) => (
  <List
    height={600}
    itemCount={recipes.length}
    itemSize={200}
    itemData={recipes}
  >
    {RecipeRow}
  </List>
);
```

### 2. Memoization
```javascript
const RecipeCard = React.memo(({ recipe, onView, onDelete }) => {
  return (
    <div className="recipe-card">
      {/* Recipe card content */}
    </div>
  );
});

// Memoize filtered results
const filteredRecipes = useMemo(() => {
  return recipes.filter(recipe => {
    // Filter logic
  });
}, [recipes, selectedFilter, searchTerm]);
```

### 3. Lazy Loading
```javascript
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadMoreRecipes = async () => {
  if (!hasMore) return;
  
  try {
    const response = await fetch(`${API}/api/recipes/history/${user.id}?page=${page + 1}`);
    const data = await response.json();
    
    setRecipes(prev => [...prev, ...data.recipes]);
    setPage(prev => prev + 1);
    setHasMore(data.has_more);
    
  } catch (error) {
    console.error('Failed to load more recipes:', error);
  }
};
```

## Accessibility Guidelines

### 1. Keyboard Navigation
```javascript
const handleKeyDown = (e, recipe) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    handleViewRecipe(recipe);
  }
};

return (
  <div
    role="button"
    tabIndex={0}
    onKeyDown={(e) => handleKeyDown(e, recipe)}
    onClick={() => handleViewRecipe(recipe)}
    className="recipe-card focus:ring-2 focus:ring-blue-500"
  >
    {/* Card content */}
  </div>
);
```

### 2. Screen Reader Support
```javascript
return (
  <div>
    <h1 id="recipe-history-title">Recipe History</h1>
    <div 
      role="region" 
      aria-labelledby="recipe-history-title"
      aria-live="polite"
    >
      {isLoading && (
        <div aria-label="Loading recipes">
          <LoadingSpinner />
        </div>
      )}
      
      {recipes.length > 0 && (
        <div 
          role="grid"
          aria-label={`${recipes.length} recipes found`}
        >
          {recipes.map(recipe => (
            <RecipeCard 
              key={recipe.id}
              recipe={recipe}
              role="gridcell"
            />
          ))}
        </div>
      )}
    </div>
  </div>
);
```

## Error Handling Best Practices

### 1. Granular Error States
```javascript
const [errors, setErrors] = useState({
  fetch: null,      // Failed to load initial data
  delete: {},       // Per-recipe delete errors
  network: null,    // Network connectivity issues
  permission: null  // Authorization errors
});

const handleError = (type, error, recipeId = null) => {
  setErrors(prev => ({
    ...prev,
    [type]: recipeId 
      ? { ...prev[type], [recipeId]: error.message }
      : error.message
  }));
  
  // Show appropriate notification
  showNotification(getErrorMessage(type, error), 'error');
};
```

### 2. Error Recovery
```javascript
const ErrorBoundary = ({ children, fallback, onRetry }) => {
  const [hasError, setHasError] = useState(false);
  
  useEffect(() => {
    if (hasError) {
      // Auto-retry after 5 seconds
      const timer = setTimeout(() => {
        setHasError(false);
        onRetry?.();
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [hasError, onRetry]);
  
  if (hasError) {
    return fallback;
  }
  
  return children;
};
```

This architecture guide provides a comprehensive foundation for building robust, maintainable, and scalable recipe history functionality with clear integration patterns for future enhancements.