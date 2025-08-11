# RecipeGeneratorScreen Component Documentation

## Overview
An AI-powered recipe generation component that provides a step-by-step wizard interface for creating personalized recipes based on user preferences, dietary restrictions, and cooking requirements.

## Location
`/frontend/src/components/RecipeGeneratorScreen.js`

## Purpose
- **AI Recipe Generation**: Create personalized recipes using OpenAI GPT
- **Wizard Interface**: Multi-step guided experience for better UX
- **Customization**: Handle dietary preferences, cuisine types, difficulty levels
- **Integration**: Save generated recipes and navigate to detailed view

## Component Architecture

### State Management
```javascript
function RecipeGeneratorScreen({ user, onBack, showNotification, onViewRecipe }) {
  // Multi-step wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 5;
  
  // Form data state
  const [formData, setFormData] = useState({
    recipe_type: '',
    cuisine_type: '',
    dietary_preferences: [],
    cooking_time: '',
    servings: 4,
    difficulty: '',
    special_ingredients: '',
    meal_type: ''
  });
  
  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecipe, setGeneratedRecipe] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
}
```

## Wizard Steps

### Step 1: Recipe Type Selection
```javascript
const recipeTypes = [
  {
    id: 'cuisine',
    title: 'Cuisine Recipe',
    description: 'Traditional dishes from around the world',
    icon: '🌍',
    gradient: 'from-orange-500 to-red-500'
  },
  {
    id: 'beverages',
    title: 'Beverages',
    description: 'Refreshing drinks and smoothies',
    icon: '🥤',
    gradient: 'from-blue-500 to-teal-500'
  },
  {
    id: 'snacks',
    title: 'Snacks & Appetizers',
    description: 'Quick bites and party foods',
    icon: '🍿',
    gradient: 'from-purple-500 to-pink-500'
  },
  {
    id: 'desserts',
    title: 'Desserts',
    description: 'Sweet treats and baked goods',
    icon: '🍰',
    gradient: 'from-yellow-500 to-orange-500'
  }
];

const renderRecipeTypeStep = () => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        What type of recipe would you like?
      </h2>
      <p className="text-gray-600">Choose the category that interests you most</p>
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {recipeTypes.map(type => (
        <button
          key={type.id}
          onClick={() => {
            setFormData(prev => ({ ...prev, recipe_type: type.id }));
            setCurrentStep(2);
          }}
          className={`p-6 rounded-2xl text-white font-bold text-left transition-all duration-300 hover:scale-105 hover:shadow-lg ${
            formData.recipe_type === type.id
              ? `bg-gradient-to-r ${type.gradient} ring-4 ring-white ring-offset-4`
              : `bg-gradient-to-r ${type.gradient}`
          }`}
        >
          <div className="text-4xl mb-3">{type.icon}</div>
          <h3 className="text-xl font-bold mb-2">{type.title}</h3>
          <p className="text-white text-opacity-90">{type.description}</p>
        </button>
      ))}
    </div>
  </div>
);
```

### Step 2: Cuisine Selection
```javascript
const cuisineOptions = [
  { id: 'italian', name: 'Italian', icon: '🍝', color: 'bg-red-500' },
  { id: 'mexican', name: 'Mexican', icon: '🌮', color: 'bg-yellow-500' },
  { id: 'asian', name: 'Asian', icon: '🍜', color: 'bg-orange-500' },
  { id: 'mediterranean', name: 'Mediterranean', icon: '🫒', color: 'bg-green-500' },
  { id: 'indian', name: 'Indian', icon: '🍛', color: 'bg-purple-500' },
  { id: 'american', name: 'American', icon: '🍔', color: 'bg-blue-500' },
  { id: 'french', name: 'French', icon: '🥐', color: 'bg-indigo-500' },
  { id: 'thai', name: 'Thai', icon: '🍲', color: 'bg-pink-500' }
];

const renderCuisineStep = () => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        Choose your cuisine
      </h2>
      <p className="text-gray-600">Select the culinary style you're craving</p>
    </div>
    
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cuisineOptions.map(cuisine => (
        <button
          key={cuisine.id}
          onClick={() => setFormData(prev => ({ ...prev, cuisine_type: cuisine.id }))}
          className={`p-4 rounded-xl text-white font-bold text-center transition-all duration-300 hover:scale-105 ${
            cuisine.color
          } ${
            formData.cuisine_type === cuisine.id ? 'ring-4 ring-white ring-offset-2' : ''
          }`}
        >
          <div className="text-3xl mb-2">{cuisine.icon}</div>
          <div className="text-sm">{cuisine.name}</div>
        </button>
      ))}
    </div>
  </div>
);
```

### Step 3: Dietary Preferences
```javascript
const dietaryOptions = [
  { id: 'vegetarian', name: 'Vegetarian', icon: '🥬', description: 'No meat or fish' },
  { id: 'vegan', name: 'Vegan', icon: '🌱', description: 'No animal products' },
  { id: 'gluten-free', name: 'Gluten-Free', icon: '🌾', description: 'No gluten-containing ingredients' },
  { id: 'dairy-free', name: 'Dairy-Free', icon: '🥛', description: 'No dairy products' },
  { id: 'keto', name: 'Keto', icon: '🥑', description: 'Low-carb, high-fat' },
  { id: 'paleo', name: 'Paleo', icon: '🦴', description: 'Whole foods only' },
  { id: 'low-sodium', name: 'Low Sodium', icon: '🧂', description: 'Reduced salt content' },
  { id: 'nut-free', name: 'Nut-Free', icon: '🥜', description: 'No nuts or nut products' }
];

const handleDietaryToggle = (dietaryId) => {
  setFormData(prev => ({
    ...prev,
    dietary_preferences: prev.dietary_preferences.includes(dietaryId)
      ? prev.dietary_preferences.filter(d => d !== dietaryId)
      : [...prev.dietary_preferences, dietaryId]
  }));
};

const renderDietaryStep = () => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        Dietary preferences
      </h2>
      <p className="text-gray-600">Select any dietary restrictions or preferences (optional)</p>
    </div>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {dietaryOptions.map(dietary => (
        <label
          key={dietary.id}
          className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 hover:shadow-md ${
            formData.dietary_preferences.includes(dietary.id)
              ? 'border-green-500 bg-green-50'
              : 'border-gray-200 bg-white hover:border-green-300'
          }`}
        >
          <input
            type="checkbox"
            checked={formData.dietary_preferences.includes(dietary.id)}
            onChange={() => handleDietaryToggle(dietary.id)}
            className="sr-only"
          />
          <div className="flex items-center space-x-4">
            <div className="text-2xl">{dietary.icon}</div>
            <div>
              <div className="font-bold text-gray-800">{dietary.name}</div>
              <div className="text-sm text-gray-600">{dietary.description}</div>
            </div>
            {formData.dietary_preferences.includes(dietary.id) && (
              <div className="ml-auto text-green-500">✓</div>
            )}
          </div>
        </label>
      ))}
    </div>
  </div>
);
```

### Step 4: Cooking Details
```javascript
const difficultyLevels = [
  {
    id: 'easy',
    name: 'Easy',
    description: '15-30 minutes, basic skills',
    icon: '😊',
    color: 'bg-green-500',
    time: '15-30 min'
  },
  {
    id: 'medium',
    name: 'Medium',
    description: '30-60 minutes, some experience',
    icon: '🤔',
    color: 'bg-yellow-500',
    time: '30-60 min'
  },
  {
    id: 'hard',
    name: 'Hard',
    description: '60+ minutes, advanced skills',
    icon: '😤',
    color: 'bg-red-500',
    time: '60+ min'
  }
];

const renderCookingDetailsStep = () => (
  <div className="space-y-8">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        Cooking details
      </h2>
      <p className="text-gray-600">Tell us about your cooking preferences</p>
    </div>
    
    {/* Difficulty Selection */}
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-800">Difficulty Level</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {difficultyLevels.map(level => (
          <button
            key={level.id}
            onClick={() => setFormData(prev => ({ ...prev, difficulty: level.id }))}
            className={`p-4 rounded-xl text-white font-bold text-center transition-all duration-300 hover:scale-105 ${
              level.color
            } ${
              formData.difficulty === level.id ? 'ring-4 ring-white ring-offset-2' : ''
            }`}
          >
            <div className="text-3xl mb-2">{level.icon}</div>
            <div className="text-lg mb-1">{level.name}</div>
            <div className="text-sm opacity-90">{level.time}</div>
            <div className="text-xs opacity-75 mt-1">{level.description}</div>
          </button>
        ))}
      </div>
    </div>
    
    {/* Servings Selection */}
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-800">Number of Servings</h3>
      <div className="flex items-center justify-center space-x-4">
        <button
          onClick={() => setFormData(prev => ({ ...prev, servings: Math.max(1, prev.servings - 1) }))}
          className="w-12 h-12 bg-gray-200 hover:bg-gray-300 rounded-full flex items-center justify-center font-bold text-xl"
        >
          -
        </button>
        <div className="text-3xl font-bold text-gray-800 px-4">
          {formData.servings}
        </div>
        <button
          onClick={() => setFormData(prev => ({ ...prev, servings: Math.min(12, prev.servings + 1) }))}
          className="w-12 h-12 bg-gray-200 hover:bg-gray-300 rounded-full flex items-center justify-center font-bold text-xl"
        >
          +
        </button>
      </div>
      <p className="text-center text-gray-600">
        {formData.servings === 1 ? '1 person' : `${formData.servings} people`}
      </p>
    </div>
    
    {/* Special Ingredients */}
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-gray-800">Special Ingredients (Optional)</h3>
      <textarea
        value={formData.special_ingredients}
        onChange={(e) => setFormData(prev => ({ ...prev, special_ingredients: e.target.value }))}
        placeholder="Any specific ingredients you want to include or avoid..."
        className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none resize-none"
        rows="3"
      />
    </div>
  </div>
);
```

### Step 5: Review & Generate
```javascript
const renderReviewStep = () => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        Review your recipe request
      </h2>
      <p className="text-gray-600">Make sure everything looks good before generating</p>
    </div>
    
    <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
      <ReviewItem label="Recipe Type" value={getRecipeTypeName(formData.recipe_type)} />
      <ReviewItem label="Cuisine" value={getCuisineName(formData.cuisine_type)} />
      <ReviewItem label="Dietary Preferences" value={formData.dietary_preferences.length > 0 ? formData.dietary_preferences.join(', ') : 'None'} />
      <ReviewItem label="Difficulty" value={getDifficultyName(formData.difficulty)} />
      <ReviewItem label="Servings" value={`${formData.servings} ${formData.servings === 1 ? 'person' : 'people'}`} />
      {formData.special_ingredients && (
        <ReviewItem label="Special Ingredients" value={formData.special_ingredients} />
      )}
    </div>
    
    <div className="flex gap-4">
      <button
        onClick={() => setCurrentStep(currentStep - 1)}
        className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-4 px-6 rounded-xl"
      >
        ← Back
      </button>
      <button
        onClick={generateRecipe}
        disabled={isGenerating}
        className="flex-1 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white font-bold py-4 px-6 rounded-xl disabled:opacity-50"
      >
        {isGenerating ? (
          <div className="flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
            Generating...
          </div>
        ) : (
          '🍳 Generate Recipe'
        )}
      </button>
    </div>
  </div>
);
```

## Recipe Generation

### API Integration
```javascript
const generateRecipe = async () => {
  if (!user?.id) {
    showNotification('Please log in to generate recipes', 'error');
    return;
  }

  setIsGenerating(true);

  try {
    console.log('🍳 Generating recipe with data:', formData);

    const response = await fetch(`${API}/api/recipes/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: user.id,
        ...formData
      }),
    });

    if (!response.ok) {
      throw new Error(`Generation failed: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Recipe generated successfully:', data);

    setGeneratedRecipe(data);
    showNotification('🎉 Recipe generated successfully!', 'success');

  } catch (error) {
    console.error('❌ Recipe generation failed:', error);
    showNotification(`❌ Failed to generate recipe: ${error.message}`, 'error');
  } finally {
    setIsGenerating(false);
  }
};
```

### Recipe Display
```javascript
const renderGeneratedRecipe = () => (
  <div className="space-y-6">
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-4">
        🎉 Your recipe is ready!
      </h2>
      <p className="text-gray-600">Here's your personalized recipe</p>
    </div>
    
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Recipe Header */}
      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-6">
        <h3 className="text-2xl font-bold mb-2">{generatedRecipe.name}</h3>
        <p className="text-green-100">{generatedRecipe.description}</p>
      </div>
      
      {/* Recipe Details */}
      <div className="p-6 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailCard icon="⏱️" label="Prep Time" value={generatedRecipe.prep_time} />
          <DetailCard icon="🍳" label="Cook Time" value={generatedRecipe.cook_time} />
          <DetailCard icon="👥" label="Servings" value={generatedRecipe.servings} />
          <DetailCard icon="📊" label="Difficulty" value={generatedRecipe.difficulty} />
        </div>
        
        {/* Ingredients Preview */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-3">Ingredients ({generatedRecipe.ingredients?.length || 0})</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {(generatedRecipe.ingredients || []).slice(0, 6).map((ingredient, index) => (
              <div key={index} className="flex items-center space-x-2 text-gray-700">
                <span className="text-green-500">•</span>
                <span className="text-sm">{ingredient}</span>
              </div>
            ))}
            {generatedRecipe.ingredients?.length > 6 && (
              <div className="text-gray-500 text-sm">+ {generatedRecipe.ingredients.length - 6} more...</div>
            )}
          </div>
        </div>
        
        {/* Instructions Preview */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-3">Instructions ({generatedRecipe.instructions?.length || 0} steps)</h4>
          <div className="space-y-2">
            {(generatedRecipe.instructions || []).slice(0, 3).map((instruction, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-green-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                  {index + 1}
                </div>
                <p className="text-sm text-gray-700">{instruction}</p>
              </div>
            ))}
            {generatedRecipe.instructions?.length > 3 && (
              <div className="text-gray-500 text-sm ml-9">+ {generatedRecipe.instructions.length - 3} more steps...</div>
            )}
          </div>
        </div>
      </div>
    </div>
    
    {/* Action Buttons */}
    <div className="flex gap-4">
      <button
        onClick={() => {
          setCurrentStep(1);
          setGeneratedRecipe(null);
          setFormData({
            recipe_type: '',
            cuisine_type: '',
            dietary_preferences: [],
            cooking_time: '',
            servings: 4,
            difficulty: '',
            special_ingredients: '',
            meal_type: ''
          });
        }}
        className="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-bold py-4 px-6 rounded-xl"
      >
        🔄 Generate Another
      </button>
      <button
        onClick={saveRecipe}
        disabled={isSaving}
        className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-4 px-6 rounded-xl disabled:opacity-50"
      >
        {isSaving ? 'Saving...' : '💾 Save Recipe'}
      </button>
      <button
        onClick={() => onViewRecipe(generatedRecipe.id, 'generated')}
        className="flex-1 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white font-bold py-4 px-6 rounded-xl"
      >
        👀 View Full Recipe
      </button>
    </div>
  </div>
);
```

## Recipe Management

### Save Recipe
```javascript
const saveRecipe = async () => {
  if (!generatedRecipe || !user?.id) {
    showNotification('Unable to save recipe', 'error');
    return;
  }

  setIsSaving(true);

  try {
    const response = await fetch(`${API}/api/recipes/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: user.id,
        recipe: generatedRecipe
      }),
    });

    if (!response.ok) {
      throw new Error(`Save failed: ${response.status}`);
    }

    showNotification('✅ Recipe saved to your collection!', 'success');

  } catch (error) {
    console.error('❌ Failed to save recipe:', error);
    showNotification(`❌ Failed to save recipe: ${error.message}`, 'error');
  } finally {
    setIsSaving(false);
  }
};
```

## Component Integration

### Props Interface
```javascript
interface RecipeGeneratorScreenProps {
  user: {
    id: string;
    email: string;
  };
  onBack: () => void;
  showNotification: (message: string, type: string) => void;
  onViewRecipe: (recipeId: string, source: string) => void;
}
```

### Usage in App.js
```javascript
case 'generate-recipe':
  return <RecipeGeneratorScreen 
    user={user}
    onBack={() => setCurrentScreen('dashboard')}
    showNotification={showNotification}
    onViewRecipe={(recipeId, source = 'generated') => {
      setCurrentRecipeId(recipeId);
      setCurrentRecipeSource(source);
      setCurrentScreen('recipe-detail');
    }}
  />;
```

## Error Handling & Loading States

### Form Validation
```javascript
const validateStep = (step) => {
  switch (step) {
    case 1:
      return formData.recipe_type !== '';
    case 2:
      return formData.cuisine_type !== '';
    case 3:
      return true; // Dietary preferences are optional
    case 4:
      return formData.difficulty !== '' && formData.servings > 0;
    case 5:
      return true; // Review step
    default:
      return false;
  }
};

const handleNext = () => {
  if (!validateStep(currentStep)) {
    showNotification('Please complete all required fields', 'warning');
    return;
  }
  
  if (currentStep < totalSteps) {
    setCurrentStep(currentStep + 1);
  }
};
```

### Loading States
```javascript
const LoadingSpinner = ({ message }) => (
  <div className="flex flex-col items-center justify-center py-12">
    <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mb-4"></div>
    <p className="text-gray-600 text-lg">{message}</p>
  </div>
);
```

## Testing Strategy

### Unit Tests
```javascript
// RecipeGeneratorScreen.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RecipeGeneratorScreen from './RecipeGeneratorScreen';

const mockProps = {
  user: { id: 'test-user-id' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  onViewRecipe: jest.fn()
};

describe('RecipeGeneratorScreen', () => {
  test('renders step 1 initially', () => {
    render(<RecipeGeneratorScreen {...mockProps} />);
    expect(screen.getByText('What type of recipe would you like?')).toBeInTheDocument();
  });

  test('advances to next step on selection', async () => {
    render(<RecipeGeneratorScreen {...mockProps} />);
    
    fireEvent.click(screen.getByText('Cuisine Recipe'));
    
    await waitFor(() => {
      expect(screen.getByText('Choose your cuisine')).toBeInTheDocument();
    });
  });

  test('generates recipe with form data', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ 
          id: 'recipe-123',
          name: 'Test Recipe',
          ingredients: ['flour', 'sugar'],
          instructions: ['Mix', 'Bake']
        })
      })
    );

    render(<RecipeGeneratorScreen {...mockProps} />);
    
    // Navigate through steps and generate recipe
    // Assert recipe is displayed
  });
});
```

## Performance Optimization

### Form State Optimization
```javascript
const useFormState = (initialState) => {
  const [state, setState] = useState(initialState);
  
  const updateField = useCallback((field, value) => {
    setState(prev => ({ ...prev, [field]: value }));
  }, []);
  
  const resetForm = useCallback(() => {
    setState(initialState);
  }, [initialState]);
  
  return [state, updateField, resetForm];
};
```

### Step Memoization
```javascript
const StepContent = React.memo(({ step, formData, onUpdateField }) => {
  switch (step) {
    case 1: return <RecipeTypeStep formData={formData} onUpdate={onUpdateField} />;
    case 2: return <CuisineStep formData={formData} onUpdate={onUpdateField} />;
    // ... other steps
    default: return null;
  }
});
```

## Accessibility

### Screen Reader Support
```javascript
<div role="main" aria-labelledby="wizard-title">
  <h1 id="wizard-title">Recipe Generator</h1>
  
  <div role="progressbar" 
       aria-valuemin="1" 
       aria-valuemax={totalSteps} 
       aria-valuenow={currentStep}
       aria-label={`Step ${currentStep} of ${totalSteps}`}>
    <div className="progress-bar">
      <div style={{ width: `${(currentStep / totalSteps) * 100}%` }} />
    </div>
  </div>
  
  <fieldset>
    <legend>Step {currentStep}: {getStepTitle(currentStep)}</legend>
    {/* Step content */}
  </fieldset>
</div>
```

### Keyboard Navigation
```javascript
useEffect(() => {
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft' && currentStep > 1) {
      setCurrentStep(prev => prev - 1);
    } else if (e.key === 'ArrowRight' && currentStep < totalSteps && validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    }
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [currentStep, totalSteps]);
```

## Common Issues & Solutions

### Issue: Form data not persisting between steps
**Solution**: Implement proper state management
```javascript
const persistFormData = useCallback(() => {
  localStorage.setItem('recipe_generator_form', JSON.stringify(formData));
}, [formData]);

useEffect(() => {
  const savedData = localStorage.getItem('recipe_generator_form');
  if (savedData) {
    setFormData(JSON.parse(savedData));
  }
}, []);

useEffect(() => {
  if (formData.recipe_type) { // Only persist if form has been started
    persistFormData();
  }
}, [formData, persistFormData]);
```

### Issue: Recipe generation timeout
**Solution**: Implement proper timeout and retry logic
```javascript
const generateWithRetry = async (maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const response = await fetch(endpoint, {
        ...options,
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response;
      
    } catch (error) {
      if (attempt === maxRetries) throw error;
      showNotification(`Attempt ${attempt} failed, retrying...`, 'warning');
      await new Promise(resolve => setTimeout(resolve, 2000 * attempt)); // Exponential backoff
    }
  }
};
```

## Future Enhancements

### Potential Features
1. **Recipe Templates**: Pre-filled forms for common recipes
2. **Ingredient Suggestions**: Auto-complete for ingredient inputs
3. **Recipe Variations**: Generate multiple versions of the same recipe
4. **Nutritional Information**: Display calories and nutritional data
5. **Recipe Sharing**: Share generation settings with other users

### Implementation Patterns
```javascript
// Recipe templates
const recipeTemplates = {
  'quick-dinner': {
    recipe_type: 'cuisine',
    difficulty: 'easy',
    cooking_time: '30 minutes',
    meal_type: 'dinner'
  },
  'healthy-lunch': {
    recipe_type: 'cuisine',
    dietary_preferences: ['low-sodium'],
    difficulty: 'easy',
    meal_type: 'lunch'
  }
};

const applyTemplate = (templateId) => {
  const template = recipeTemplates[templateId];
  if (template) {
    setFormData(prev => ({ ...prev, ...template }));
  }
};
```

---

**Last Updated**: January 2025
**Component Version**: 2.0.0