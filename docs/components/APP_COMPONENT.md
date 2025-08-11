# App.js Component Documentation

## Overview
The main application component that handles routing, authentication, global state management, and navigation between different screens. Acts as the central hub for the entire application.

## Location
`/frontend/src/App.js`

## Purpose
- **Central Router**: Manages navigation between all application screens
- **Authentication Handler**: Login/logout, session persistence, trial management
- **Global State Manager**: User state, current screen, notifications
- **Service Integration**: Connects all components with shared services

## Component Architecture

### State Management
```javascript
const App = () => {
  // Authentication & User Management
  const [user, setUser] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  
  // Navigation & Screen Management
  const [currentScreen, setCurrentScreen] = useState('landing');
  const [currentRecipeId, setCurrentRecipeId] = useState(null);
  const [currentRecipeSource, setCurrentRecipeSource] = useState('weekly');
  
  // Starbucks Recipe State
  const [currentStarbucksRecipe, setCurrentStarbucksRecipe] = useState(null);
  
  // Notification System
  const [notification, setNotification] = useState(null);
  
  // Weekly Recipes State
  const [weeklyRecipes, setWeeklyRecipes] = useState([]);
  const [weeklyRecipesLoading, setWeeklyRecipesLoading] = useState(false);
}
```

### Screen Navigation System
The app uses a simple but effective screen-based routing system:

```javascript
const renderScreen = () => {
  switch (currentScreen) {
    case 'landing': return <LandingScreen />;
    case 'dashboard': return <DashboardScreen />;
    case 'generate-recipe': return <RecipeGeneratorScreen />;
    case 'all-recipes': return <RecipeHistoryScreen />;
    case 'recipe-detail': return <RecipeDetailScreen />;
    case 'weekly-recipes': return <WeeklyRecipesScreen />;
    case 'starbucks-generator': return <StarbucksGeneratorScreen />;
    case 'subscription': return <SubscriptionScreen />;
    case 'welcome-onboarding': return <WelcomeOnboarding />;
    case 'tutorial': return <TutorialScreen />;
    default: return <LandingScreen />;
  }
};
```

## Key Features

### 1. Authentication System
- **Session Persistence**: 7-day auto-login using localStorage
- **Trial Management**: Automatic trial expiration handling
- **Security**: JWT token validation and refresh

```javascript
const login = (userData) => {
  const userSession = {
    ...userData,
    loginTime: Date.now(),
    sessionExpiry: Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days
  };
  setUser(userSession);
  localStorage.setItem('ai_chef_user', JSON.stringify(userSession));
};
```

### 2. Navigation Management
- **Deep Linking**: Direct navigation to specific recipes/screens
- **State Preservation**: Maintains context between screen switches
- **Back Navigation**: Proper back button handling

```javascript
const handleViewRecipe = (recipeId, source = 'weekly') => {
  setCurrentRecipeId(recipeId);
  setCurrentRecipeSource(source);
  setCurrentScreen('recipe-detail');
};
```

### 3. Notification System
- **Global Notifications**: Success, error, warning, info messages
- **Auto-dismiss**: 4-second automatic dismissal
- **User-friendly Messages**: Clear, actionable feedback

```javascript
const showNotification = useCallback((message, type = 'success') => {
  setNotification({ message, type });
  setTimeout(() => setNotification(null), 4000);
}, []);
```

## Integration with Components

### Standard Props Pattern
All screens receive these standard props:

```javascript
<ComponentScreen 
  user={user}
  onBack={() => setCurrentScreen('dashboard')}
  showNotification={showNotification}
  // Component-specific props
/>
```

### Recipe-related Components
Recipe components receive additional navigation handlers:

```javascript
<RecipeHistoryScreen 
  user={user}
  onBack={() => setCurrentScreen('dashboard')}
  showNotification={showNotification}
  onViewRecipe={handleViewRecipe}
  onViewStarbucksRecipe={(recipe) => {
    setCurrentStarbucksRecipe(recipe);
    setCurrentScreen('starbucks-generator');
  }}
/>
```

## Adding New Screens

### 1. Create Component
```javascript
// /frontend/src/components/NewScreen.js
import React from 'react';

function NewScreen({ user, onBack, showNotification }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Screen content */}
      <button onClick={onBack}>Back</button>
    </div>
  );
}

export default NewScreen;
```

### 2. Add Import to App.js
```javascript
import NewScreen from './components/NewScreen';
```

### 3. Add Case to Switch Statement
```javascript
case 'new-screen':
  return <NewScreen 
    user={user}
    onBack={() => setCurrentScreen('dashboard')}
    showNotification={showNotification}
  />;
```

### 4. Add Navigation Trigger
```javascript
// In dashboard or other components
<button onClick={() => setCurrentScreen('new-screen')}>
  Open New Screen
</button>
```

## Protected Routes
Screens that require authentication are automatically handled:

```javascript
useEffect(() => {
  // Redirect to landing if user not authenticated
  const protectedScreens = ['dashboard', 'generate-recipe', 'all-recipes', 'recipe-detail'];
  if (!user && protectedScreens.includes(currentScreen)) {
    const savedUser = localStorage.getItem('ai_chef_user');
    if (!savedUser) {
      setCurrentScreen('landing');
    }
  }
}, [user, currentScreen]);
```

## Error Handling

### Loading States
- Authentication loading during session restoration
- Component-specific loading states
- Graceful fallbacks for missing data

### Error Boundaries
```javascript
// Built-in error handling for navigation
const handleNavigationError = (error) => {
  console.error('Navigation error:', error);
  showNotification('Navigation failed. Please try again.', 'error');
  setCurrentScreen('dashboard'); // Safe fallback
};
```

## Performance Considerations

### 1. Component Lazy Loading
Consider implementing lazy loading for large components:

```javascript
const RecipeDetailScreen = React.lazy(() => import('./components/RecipeDetailScreen'));

// In render
<Suspense fallback={<LoadingSpinner />}>
  <RecipeDetailScreen {...props} />
</Suspense>
```

### 2. State Optimization
- Use `useCallback` for stable function references
- Implement `useMemo` for expensive calculations
- Consider state management libraries for complex state

## Security Considerations

### 1. Session Management
- Automatic session expiration
- Secure token storage
- Logout on security events

### 2. API Integration
- All API calls use environment variables
- Error handling prevents information leakage
- Input validation at component level

## Testing Strategy

### Unit Tests
```javascript
// App.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';

test('renders landing screen by default', () => {
  render(<App />);
  expect(screen.getByText('Welcome')).toBeInTheDocument();
});

test('navigates to dashboard after login', async () => {
  render(<App />);
  // Simulate login
  // Assert dashboard is shown
});
```

### Integration Tests
- Test navigation flow between screens
- Verify authentication state persistence
- Check notification system functionality

## Common Patterns

### 1. Screen Navigation
```javascript
// Always use setCurrentScreen for navigation
const handleNavigateToRecipes = () => {
  setCurrentScreen('all-recipes');
};
```

### 2. State Updates
```javascript
// Update user state properly
const updateUserPreferences = (preferences) => {
  const updatedUser = { ...user, preferences };
  setUser(updatedUser);
  localStorage.setItem('ai_chef_user', JSON.stringify(updatedUser));
};
```

### 3. Error Handling
```javascript
// Standard error handling pattern
try {
  await apiCall();
  showNotification('Success!', 'success');
} catch (error) {
  console.error('Operation failed:', error);
  showNotification('Operation failed. Please try again.', 'error');
}
```

## Troubleshooting

### Common Issues

**Screen not rendering**
- Verify case in switch statement matches exactly
- Check component import statement
- Ensure component exports default

**Navigation not working**
- Check `setCurrentScreen` calls use correct screen names
- Verify protected route logic for authenticated screens
- Check for JavaScript errors in browser console

**State not persisting**
- Verify localStorage operations are correct
- Check session expiry logic
- Ensure state updates use spread operators for immutability

## Future Enhancements

### Potential Improvements
1. **React Router**: Migrate to React Router for better URL support
2. **Context API**: Move global state to React Context
3. **Error Boundaries**: Implement proper error boundaries
4. **Analytics**: Add page view tracking
5. **Performance**: Implement code splitting and lazy loading

### Migration Considerations
- Maintain backward compatibility during transitions
- Update all navigation calls consistently
- Test thoroughly across all user flows

---

**Last Updated**: January 2025
**Component Version**: 2.0.0