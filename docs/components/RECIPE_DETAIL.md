# RecipeDetailScreen Component Documentation

## Overview
A comprehensive recipe viewing component that displays complete recipe information, manages Walmart shopping integration, and provides cart functionality for ingredient purchases.

## Location
`/frontend/src/components/RecipeDetailScreen.js`

## Purpose
- **Recipe Display**: Show complete recipe details with ingredients and instructions
- **Walmart Integration**: Real-time product search and cart creation
- **Shopping Cart Management**: Select/deselect ingredients, manage product choices
- **User Experience**: Loading states, error handling, responsive design

## Component Architecture

### State Management
```javascript
function RecipeDetailScreen({ recipeId, recipeSource, user, onBack, showNotification }) {
  // Core recipe data
  const [recipe, setRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Cart and product management
  const [cartOptions, setCartOptions] = useState(null);
  const [selectedProducts, setSelectedProducts] = useState({});
  const [excludedIngredients, setExcludedIngredients] = useState(new Set());
  const [isLoadingCart, setIsLoadingCart] = useState(false);
}
```

## Key Features

### 1. Smart Recipe Loading
```javascript
useEffect(() => {
  if (!recipeId) {
    console.log('❌ No recipeId provided');
    setIsLoading(false);
    return;
  }
  
  const loadRecipeDetail = async () => {
    try {
      console.log('🔍 Loading recipe ID:', recipeId, 'from source:', recipeSource);
      setIsLoading(true);
      
      // Determine the correct API endpoint based on source
      let apiUrl;
      if (recipeSource === 'weekly') {
        apiUrl = `${API}/api/weekly-recipes/recipe/${recipeId}`;
      } else {
        // For 'history' and 'generated' sources, use the detail endpoint
        apiUrl = `${API}/api/recipes/${recipeId}/detail`;
      }
      
      console.log('🔍 Making API call to:', apiUrl);
      
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📡 API Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ Recipe data received:', {
        id: data.id,
        name: data.name || data.title,
        hasIngredients: !!data.ingredients,
        hasInstructions: !!data.instructions
      });
      
      setRecipe(data);
      setIsLoading(false);
      
      // Load cart options after recipe loads
      setTimeout(() => {
        loadCartOptionsForRecipe(recipeId);
      }, 1000);
      
    } catch (error) {
      console.error('❌ Recipe loading failed:', error);
      showNotification(`❌ Failed to load recipe: ${error.message}`, 'error');
      setRecipe(null);
      setIsLoading(false);
    }
  };
  
  loadRecipeDetail();
}, [recipeId, recipeSource, showNotification]);
```

### 2. Walmart Cart Integration
```javascript
const loadCartOptionsForRecipe = async (currentRecipeId) => {
  setIsLoadingCart(true);
  
  try {
    console.log('🔍 Loading cart options for recipe:', currentRecipeId);
    
    // Try weekly endpoint first, fallback to regular
    let cartData = null;
    let apiUrl = `${API}/api/v2/walmart/weekly-cart-options?recipe_id=${currentRecipeId}`;
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000); // 25 second timeout
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      // Fallback to regular endpoint
      console.log('⚠️ Weekly cart endpoint failed, trying regular cart endpoint');
      
      const fallbackUrl = `${API}/api/recipes/${currentRecipeId}/cart-options`;
      const fallbackResponse = await fetch(fallbackUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!fallbackResponse.ok) {
        throw new Error(`Both cart endpoints failed`);
      }
      
      cartData = await fallbackResponse.json();
    } else {
      cartData = await response.json();
    }
    
    // Set cart options and initialize product selections
    setCartOptions(cartData);
    
    if (cartData?.ingredient_matches) {
      const initialSelections = {};
      cartData.ingredient_matches.forEach(ingredientMatch => {
        if (ingredientMatch.products && ingredientMatch.products.length > 0) {
          initialSelections[ingredientMatch.ingredient] = ingredientMatch.products[0];
        }
      });
      setSelectedProducts(initialSelections);
      
      showNotification(`✅ Found ${cartData.total_products || cartData.ingredient_matches.length} real Walmart products!`, 'success');
    }
    
  } catch (error) {
    console.error('❌ Failed to load cart options:', error);
    if (error.name === 'AbortError') {
      showNotification('⚠️ Walmart product search is taking longer than expected. Recipe still available!', 'warning');
    } else {
      showNotification('⚠️ Could not load Walmart products. Recipe details available.', 'warning');  
    }
  } finally {
    setIsLoadingCart(false);
  }
};
```

### 3. Ingredient Management
```javascript
const handleIngredientToggle = (ingredient) => {
  setExcludedIngredients(prev => {
    const newSet = new Set(prev);
    if (newSet.has(ingredient)) {
      newSet.delete(ingredient);
    } else {
      newSet.add(ingredient);
    }
    return newSet;
  });
};

const handleSelectAll = () => {
  setExcludedIngredients(new Set());
};

const handleDeselectAll = () => {
  const allIngredients = cartOptions?.ingredient_matches?.map(match => match.ingredient) || [];
  setExcludedIngredients(new Set(allIngredients));
};
```

### 4. Product Selection & Cart Management
```javascript
const handleProductRemove = (ingredient) => {
  setSelectedProducts(prev => {
    const updated = { ...prev };
    delete updated[ingredient];
    return updated;
  });
  
  // Also exclude the ingredient
  setExcludedIngredients(prev => new Set([...prev, ingredient]));
};

const calculateCartTotal = () => {
  return Object.entries(selectedProducts)
    .filter(([ingredient]) => !excludedIngredients.has(ingredient))
    .reduce((total, [, product]) => total + (parseFloat(product.price) || 0), 0);
};

const generateWalmartCartUrl = () => {
  const includedProducts = Object.entries(selectedProducts)
    .filter(([ingredient]) => !excludedIngredients.has(ingredient))
    .map(([, product]) => product.id);
  
  if (includedProducts.length === 0) return null;
  
  return `https://www.walmart.com/cart?items=${includedProducts.join(',')}`;
};
```

## UI/UX Components

### Recipe Display
```javascript
const RecipeContent = () => (
  <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
    {/* Recipe Header */}
    <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-8">
      <h1 className="text-4xl font-bold mb-4">{recipe.name || recipe.title}</h1>
      <p className="text-orange-100 text-lg leading-relaxed">{recipe.description}</p>
    </div>

    {/* Recipe Metadata */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-gray-50">
      <MetadataItem icon="⏱️" label="Prep Time" value={recipe.prep_time} />
      <MetadataItem icon="🍳" label="Cook Time" value={recipe.cook_time} />
      <MetadataItem icon="👥" label="Servings" value={recipe.servings} />
      <MetadataItem icon="📊" label="Difficulty" value={recipe.difficulty} />
    </div>

    {/* Ingredients Section */}
    <div className="p-8">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center">
        🛒 Ingredients & Shopping
      </h2>
      
      {/* Ingredient management controls */}
      <div className="flex gap-4 mb-6">
        <button 
          onClick={handleSelectAll}
          className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded-lg"
        >
          ✅ Select All
        </button>
        <button 
          onClick={handleDeselectAll}
          className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg"
        >
          ❌ Deselect All
        </button>
      </div>
      
      {/* Ingredient list with checkboxes */}
      <div className="space-y-3">
        {(recipe.ingredients || []).map((ingredient, index) => (
          <IngredientItem
            key={index}
            ingredient={ingredient}
            isExcluded={excludedIngredients.has(ingredient)}
            onToggle={() => handleIngredientToggle(ingredient)}
            products={cartOptions?.ingredient_matches?.find(m => m.ingredient === ingredient)?.products}
          />
        ))}
      </div>
    </div>

    {/* Instructions Section */}
    <div className="p-8 bg-gray-50">
      <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center">
        📝 Instructions
      </h2>
      <div className="space-y-4">
        {(recipe.instructions || []).map((instruction, index) => (
          <InstructionStep key={index} step={index + 1} instruction={instruction} />
        ))}
      </div>
    </div>
  </div>
);
```

### Shopping Cart Summary
```javascript
const CartSummary = () => {
  const cartTotal = calculateCartTotal();
  const selectedCount = Object.keys(selectedProducts).length - excludedIngredients.size;
  
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
        🛒 Shopping Cart
      </h3>
      
      <div className="space-y-4">
        {Object.entries(selectedProducts)
          .filter(([ingredient]) => !excludedIngredients.has(ingredient))
          .map(([ingredient, product]) => (
            <CartItem
              key={ingredient}
              ingredient={ingredient}
              product={product}
              onRemove={() => handleProductRemove(ingredient)}
            />
          ))}
      </div>
      
      <div className="border-t pt-4 mt-4">
        <div className="flex justify-between items-center mb-4">
          <span className="text-lg font-semibold">Total: ${cartTotal.toFixed(2)}</span>
          <span className="text-sm text-gray-600">{selectedCount} items</span>
        </div>
        
        <button
          onClick={() => window.open(generateWalmartCartUrl(), '_blank')}
          disabled={selectedCount === 0}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-xl disabled:opacity-50"
        >
          🛒 Shop on Walmart (${cartTotal.toFixed(2)})
        </button>
      </div>
    </div>
  );
};
```

## Component Integration

### Props Interface
```javascript
interface RecipeDetailScreenProps {
  recipeId: string;
  recipeSource: 'weekly' | 'history' | 'generated';
  user: {
    id: string;
    email: string;
  };
  onBack: () => void;
  showNotification: (message: string, type: string) => void;
}
```

### Usage in App.js
```javascript
case 'recipe-detail':
  return <RecipeDetailScreen
    key={`${currentRecipeId}-${currentRecipeSource}`} // Force re-render on recipe change
    recipeId={currentRecipeId}
    recipeSource={currentRecipeSource}
    user={user}
    onBack={() => setCurrentScreen(getBackScreen())}
    showNotification={showNotification}
  />;
```

## API Integration

### Required Endpoints
1. **Recipe Detail**: `GET /api/recipes/{recipe_id}/detail`
2. **Weekly Recipe**: `GET /api/weekly-recipes/recipe/{recipe_id}`
3. **Cart Options**: `POST /api/v2/walmart/weekly-cart-options?recipe_id={recipe_id}`
4. **Cart Fallback**: `POST /api/recipes/{recipe_id}/cart-options`

### Expected Data Formats

#### Recipe Data
```javascript
{
  "id": "uuid",
  "name": "Recipe Name",
  "title": "Recipe Title",
  "description": "Recipe description",
  "prep_time": "30 minutes",
  "cook_time": "25 minutes",
  "servings": 4,
  "difficulty": "medium",
  "cuisine_type": "italian",
  "ingredients": [
    "2 cups flour",
    "1 cup sugar",
    "3 eggs"
  ],
  "instructions": [
    "Preheat oven to 350°F",
    "Mix ingredients",
    "Bake for 30 minutes"
  ]
}
```

#### Cart Options Data
```javascript
{
  "ingredient_matches": [
    {
      "ingredient": "2 cups flour",
      "products": [
        {
          "id": "walmart_product_id",
          "name": "All-Purpose Flour, 5 lb",
          "price": "2.98",
          "image": "https://walmart.com/image.jpg"
        }
      ]
    }
  ],
  "total_products": 15,
  "estimated_total": 45.67
}
```

## Error Handling

### Loading States
```javascript
if (isLoading) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 flex items-center justify-center">
      <div className="bg-white rounded-3xl shadow-2xl p-8 text-center">
        <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Recipe</h2>
        <p className="text-gray-600">Fetching delicious details...</p>
      </div>
    </div>
  );
}
```

### Error States
```javascript
if (!recipe) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl p-8 text-center max-w-md">
        <div className="text-6xl mb-4">😞</div>
        <h2 className="text-2xl font-bold text-red-600 mb-4">Recipe Not Found</h2>
        <p className="text-gray-600 mb-6">
          This recipe is no longer available or may have been removed.
        </p>
        <button
          onClick={onBack}
          className="bg-gradient-to-r from-red-500 to-orange-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200"
        >
          ← Go Back
        </button>
      </div>
    </div>
  );
}
```

## Performance Optimization

### 1. Component Memoization
```javascript
const IngredientItem = React.memo(({ ingredient, isExcluded, onToggle, products }) => {
  return (
    <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50">
      <input
        type="checkbox"
        checked={!isExcluded}
        onChange={onToggle}
        className="w-5 h-5 text-green-600"
      />
      <span className={`flex-1 ${isExcluded ? 'line-through text-gray-400' : ''}`}>
        {ingredient}
      </span>
      {products && products.length > 0 && (
        <span className="text-sm text-green-600">${products[0].price}</span>
      )}
    </div>
  );
});

const InstructionStep = React.memo(({ step, instruction }) => (
  <div className="flex items-start space-x-4 p-4 bg-white rounded-lg shadow-sm">
    <div className="flex-shrink-0 w-8 h-8 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold">
      {step}
    </div>
    <p className="text-gray-700 leading-relaxed">{instruction}</p>
  </div>
));
```

### 2. Debounced Cart Updates
```javascript
const [debouncedCartTotal, setDebouncedCartTotal] = useState(0);

useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedCartTotal(calculateCartTotal());
  }, 300);
  
  return () => clearTimeout(timer);
}, [selectedProducts, excludedIngredients]);
```

### 3. Lazy Loading for Large Ingredient Lists
```javascript
const [visibleIngredients, setVisibleIngredients] = useState(20);

const loadMoreIngredients = () => {
  setVisibleIngredients(prev => prev + 20);
};

// Render only visible ingredients
const displayIngredients = (recipe.ingredients || []).slice(0, visibleIngredients);
```

## Testing Strategy

### Unit Tests
```javascript
// RecipeDetailScreen.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RecipeDetailScreen from './RecipeDetailScreen';

const mockProps = {
  recipeId: 'test-recipe-id',
  recipeSource: 'history',
  user: { id: 'test-user-id' },
  onBack: jest.fn(),
  showNotification: jest.fn()
};

describe('RecipeDetailScreen', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  test('loads recipe data successfully', async () => {
    const mockRecipe = {
      id: 'test-recipe-id',
      name: 'Test Recipe',
      ingredients: ['flour', 'sugar'],
      instructions: ['Mix ingredients', 'Bake']
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockRecipe)
    });

    render(<RecipeDetailScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      expect(screen.getByText('flour')).toBeInTheDocument();
      expect(screen.getByText('Mix ingredients')).toBeInTheDocument();
    });
  });

  test('handles ingredient selection', async () => {
    // Test ingredient checkbox functionality
  });

  test('calculates cart total correctly', () => {
    // Test cart calculation logic
  });

  test('handles Walmart cart integration', async () => {
    // Test cart URL generation and product selection
  });
});
```

### Integration Tests
- Test API endpoint responses
- Verify cart integration flow
- Check error handling scenarios

## Accessibility

### Screen Reader Support
```javascript
<div role="main" aria-labelledby="recipe-title">
  <h1 id="recipe-title">{recipe.name}</h1>
  
  <section aria-label="Ingredients">
    <h2>Ingredients</h2>
    <ul role="list">
      {ingredients.map((ingredient, index) => (
        <li key={index} role="listitem">
          <label>
            <input
              type="checkbox"
              aria-describedby={`ingredient-${index}-desc`}
            />
            <span id={`ingredient-${index}-desc`}>{ingredient}</span>
          </label>
        </li>
      ))}
    </ul>
  </section>
</div>
```

### Keyboard Navigation
```javascript
const handleKeyDown = (e, action) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    action();
  }
};

<button
  onKeyDown={(e) => handleKeyDown(e, () => handleIngredientToggle(ingredient))}
  className="focus:ring-2 focus:ring-orange-500"
>
  {ingredient}
</button>
```

## Common Issues & Solutions

### Issue: Recipe not loading
**Solution**: Check recipe ID and source parameters
```javascript
useEffect(() => {
  if (!recipeId) {
    console.error('Recipe ID is required');
    setIsLoading(false);
    return;
  }
  
  if (!['weekly', 'history', 'generated'].includes(recipeSource)) {
    console.warn('Invalid recipe source, defaulting to history');
    // Handle gracefully
  }
}, [recipeId, recipeSource]);
```

### Issue: Cart integration failing
**Solution**: Implement robust fallback mechanism
```javascript
const loadCartOptions = async () => {
  try {
    // Try primary endpoint
    let response = await fetch(primaryEndpoint);
    
    if (!response.ok) {
      // Fallback to secondary endpoint
      response = await fetch(fallbackEndpoint);
    }
    
    if (!response.ok) {
      throw new Error('All cart endpoints failed');
    }
    
    // Process successful response
  } catch (error) {
    // Graceful degradation
    showNotification('Cart features temporarily unavailable', 'warning');
  }
};
```

### Issue: Performance issues with large recipes
**Solution**: Implement virtual scrolling and lazy loading
```javascript
const useVirtualizedList = (items, itemHeight = 60) => {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 });
  
  const handleScroll = useCallback((e) => {
    const scrollTop = e.target.scrollTop;
    const start = Math.floor(scrollTop / itemHeight);
    const end = start + Math.ceil(window.innerHeight / itemHeight);
    
    setVisibleRange({ start, end });
  }, [itemHeight]);
  
  return { visibleItems: items.slice(visibleRange.start, visibleRange.end), handleScroll };
};
```

## Future Enhancements

### Potential Features
1. **Recipe Scaling**: Adjust ingredient quantities for different serving sizes
2. **Nutrition Information**: Display calorie and nutrition data
3. **Recipe Notes**: Allow users to add personal notes and modifications
4. **Print View**: Optimized layout for printing recipes
5. **Recipe Rating**: Allow users to rate and review recipes
6. **Alternative Ingredients**: Suggest ingredient substitutions

### Implementation Patterns
```javascript
// Recipe scaling
const scaleIngredients = (ingredients, originalServings, newServings) => {
  const scale = newServings / originalServings;
  return ingredients.map(ingredient => {
    // Parse and scale numeric values in ingredient strings
    return ingredient.replace(/(\d+(?:\.\d+)?)/g, (match) => {
      return (parseFloat(match) * scale).toString();
    });
  });
};

// Recipe rating
const [userRating, setUserRating] = useState(0);
const submitRating = async (rating) => {
  try {
    await fetch(`${API}/api/recipes/${recipeId}/rate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating })
    });
    setUserRating(rating);
    showNotification('Rating submitted!', 'success');
  } catch (error) {
    showNotification('Failed to submit rating', 'error');
  }
};
```

---

**Last Updated**: January 2025
**Component Version**: 2.0.0