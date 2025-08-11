# Comprehensive Testing Guide

## Overview
This guide outlines the testing strategy, patterns, and best practices for the AI Chef application. It covers unit testing, integration testing, end-to-end testing, and automated testing workflows.

## Testing Architecture

### Testing Stack
```json
{
  "unit_testing": {
    "framework": "Jest",
    "react_testing": "@testing-library/react",
    "utilities": "@testing-library/jest-dom",
    "mocking": "Jest mocks + MSW"
  },
  "integration_testing": {
    "api_testing": "Supertest",
    "database_testing": "MongoDB Memory Server",
    "environment": "Test containers"
  },
  "e2e_testing": {
    "framework": "Playwright",
    "browser_automation": "Multi-browser support",
    "visual_testing": "Screenshot comparison"
  },
  "backend_testing": {
    "framework": "pytest",
    "api_testing": "httpx",
    "database": "MongoDB test collections"
  }
}
```

### Test File Structure
```
/tests/
├── unit/                     # Component unit tests
│   ├── components/
│   │   ├── App.test.js
│   │   ├── RecipeHistory.test.js
│   │   ├── RecipeDetail.test.js
│   │   └── RecipeGenerator.test.js
│   └── utils/               # Utility function tests
│       ├── api.test.js
│       └── helpers.test.js
├── integration/             # API integration tests
│   ├── auth.test.js
│   ├── recipes.test.js
│   ├── walmart.test.js
│   └── payments.test.js
├── e2e/                     # End-to-end user flows
│   ├── user-registration.spec.js
│   ├── recipe-generation.spec.js
│   ├── recipe-management.spec.js
│   └── subscription.spec.js
├── backend/                 # Python backend tests
│   ├── test_auth.py
│   ├── test_recipes.py
│   ├── test_walmart.py
│   └── test_payments.py
└── utils/                   # Testing utilities
    ├── test-helpers.js
    ├── mock-data.js
    └── test-setup.js
```

## Frontend Testing

### Component Testing Patterns

#### 1. Basic Component Testing
```javascript
// RecipeHistoryScreen.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import RecipeHistoryScreen from '../components/RecipeHistoryScreen';

// Mock API responses
const mockRecipes = [
  {
    id: '1',
    title: 'Test Recipe',
    description: 'Test description',
    created_at: '2025-01-01T12:00:00Z',
    category: 'regular'
  }
];

const mockProps = {
  user: { id: 'test-user-id' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  onViewRecipe: jest.fn(),
  onViewStarbucksRecipe: jest.fn()
};

// Mock fetch globally
beforeEach(() => {
  global.fetch = jest.fn();
  jest.clearAllMocks();
});

describe('RecipeHistoryScreen', () => {
  test('renders loading state initially', () => {
    render(<RecipeHistoryScreen {...mockProps} />);
    expect(screen.getByText(/Loading NEW Recipe History/)).toBeInTheDocument();
  });

  test('loads and displays recipes successfully', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ recipes: mockRecipes, total_count: 1 })
    });

    render(<RecipeHistoryScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    });

    expect(screen.getByText('📊 Total: 1 | Shown: 1')).toBeInTheDocument();
  });

  test('handles recipe filtering correctly', async () => {
    const mixedRecipes = [
      { ...mockRecipes[0], category: 'regular' },
      { id: '2', title: 'Starbucks Drink', category: 'starbucks' }
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ recipes: mixedRecipes })
    });

    render(<RecipeHistoryScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      expect(screen.getByText('Starbucks Drink')).toBeInTheDocument();
    });

    // Test regular recipes filter
    fireEvent.click(screen.getByText('Regular Recipes'));
    expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    expect(screen.queryByText('Starbucks Drink')).not.toBeInTheDocument();

    // Test Starbucks filter
    fireEvent.click(screen.getByText('Starbucks Drinks'));
    expect(screen.queryByText('Test Recipe')).not.toBeInTheDocument();
    expect(screen.getByText('Starbucks Drink')).toBeInTheDocument();
  });

  test('handles recipe deletion with confirmation', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ recipes: mockRecipes })
    });

    render(<RecipeHistoryScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    });

    // Mock confirmation dialog
    window.confirm = jest.fn(() => true);
    
    // Mock delete request
    fetch.mockResolvedValueOnce({ ok: true });

    // Click delete button
    const deleteButton = screen.getByTitle('🗑️');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockProps.showNotification).toHaveBeenCalledWith('Recipe deleted', 'success');
    });

    expect(window.confirm).toHaveBeenCalledWith('Delete this recipe?');
  });

  test('handles API errors gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    render(<RecipeHistoryScreen {...mockProps} />);

    await waitFor(() => {
      expect(mockProps.showNotification).toHaveBeenCalledWith(
        'Error loading recipes: Network error', 
        'error'
      );
    });
  });

  test('handles navigation correctly', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ recipes: mockRecipes })
    });

    render(<RecipeHistoryScreen {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Test Recipe')).toBeInTheDocument();
    });

    // Click view button
    const viewButton = screen.getByText('👀 View');
    fireEvent.click(viewButton);

    expect(mockProps.onViewRecipe).toHaveBeenCalledWith('1', 'history');
  });
});
```

#### 2. Complex Component Testing (Recipe Generator)
```javascript
// RecipeGeneratorScreen.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RecipeGeneratorScreen from '../components/RecipeGeneratorScreen';

describe('RecipeGeneratorScreen', () => {
  const mockProps = {
    user: { id: 'test-user' },
    onBack: jest.fn(),
    showNotification: jest.fn(),
    onViewRecipe: jest.fn()
  };

  test('completes full recipe generation workflow', async () => {
    render(<RecipeGeneratorScreen {...mockProps} />);

    // Step 1: Recipe Type Selection
    expect(screen.getByText('What type of recipe would you like?')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Cuisine Recipe'));

    // Step 2: Cuisine Selection
    await waitFor(() => {
      expect(screen.getByText('Choose your cuisine')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Italian'));

    // Step 3: Dietary Preferences (skip)
    await waitFor(() => {
      expect(screen.getByText('Dietary preferences')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Next'));

    // Step 4: Cooking Details
    await waitFor(() => {
      expect(screen.getByText('Cooking details')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Easy'));
    fireEvent.click(screen.getByText('Next'));

    // Step 5: Review & Generate
    await waitFor(() => {
      expect(screen.getByText('Review your recipe request')).toBeInTheDocument();
    });

    // Mock successful generation
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        id: 'recipe-123',
        name: 'Italian Pasta',
        description: 'Delicious pasta recipe',
        ingredients: ['pasta', 'tomato sauce'],
        instructions: ['Boil pasta', 'Add sauce'],
        prep_time: '15 minutes',
        cook_time: '20 minutes',
        servings: 4,
        difficulty: 'easy'
      })
    });

    fireEvent.click(screen.getByText('🍳 Generate Recipe'));

    // Verify generation
    await waitFor(() => {
      expect(screen.getByText('🎉 Your recipe is ready!')).toBeInTheDocument();
      expect(screen.getByText('Italian Pasta')).toBeInTheDocument();
    });

    expect(mockProps.showNotification).toHaveBeenCalledWith('🎉 Recipe generated successfully!', 'success');
  });

  test('validates form steps properly', () => {
    render(<RecipeGeneratorScreen {...mockProps} />);

    // Try to proceed without selection
    const nextButton = screen.queryByText('Next');
    expect(nextButton).not.toBeInTheDocument(); // Should not exist without selection

    // Select recipe type
    fireEvent.click(screen.getByText('Cuisine Recipe'));

    // Should automatically advance to step 2
    expect(screen.getByText('Choose your cuisine')).toBeInTheDocument();
  });

  test('handles generation errors', async () => {
    render(<RecipeGeneratorScreen {...mockProps} />);

    // Navigate to generation step
    fireEvent.click(screen.getByText('Cuisine Recipe'));
    await waitFor(() => fireEvent.click(screen.getByText('Italian')));
    await waitFor(() => fireEvent.click(screen.getByText('Next')));
    await waitFor(() => {
      fireEvent.click(screen.getByText('Easy'));
      fireEvent.click(screen.getByText('Next'));
    });

    await waitFor(() => {
      expect(screen.getByText('🍳 Generate Recipe')).toBeInTheDocument();
    });

    // Mock failed generation
    fetch.mockRejectedValueOnce(new Error('Generation failed'));

    fireEvent.click(screen.getByText('🍳 Generate Recipe'));

    await waitFor(() => {
      expect(mockProps.showNotification).toHaveBeenCalledWith(
        '❌ Failed to generate recipe: Generation failed', 
        'error'
      );
    });
  });
});
```

### Custom Testing Utilities
```javascript
// utils/test-helpers.js
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Custom render with providers
export const renderWithProviders = (ui, options = {}) => {
  const Wrapper = ({ children }) => (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...options });
};

// Mock API responses
export const mockApiResponse = (data, ok = true) => {
  return Promise.resolve({
    ok,
    json: () => Promise.resolve(data)
  });
};

// Mock user object
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  subscription: {
    status: 'active',
    trial_end: Date.now() + 7 * 24 * 60 * 60 * 1000
  }
};

// Mock recipes
export const mockRecipes = [
  {
    id: '1',
    title: 'Test Recipe 1',
    description: 'A test recipe',
    category: 'regular',
    created_at: '2025-01-01T12:00:00Z'
  },
  {
    id: '2',
    title: 'Test Starbucks Drink',
    description: 'A test drink',
    category: 'starbucks',
    created_at: '2025-01-02T12:00:00Z'
  }
];

// Mock props factory
export const createMockProps = (overrides = {}) => ({
  user: mockUser,
  onBack: jest.fn(),
  showNotification: jest.fn(),
  ...overrides
});
```

## Backend Testing

### Python Test Patterns

#### 1. API Endpoint Testing
```python
# test_recipes.py
import pytest
import json
from httpx import AsyncClient
from server import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com"
    }

@pytest.fixture
def mock_recipe():
    return {
        "name": "Test Recipe",
        "description": "A test recipe",
        "ingredients": ["flour", "sugar", "eggs"],
        "instructions": ["Mix ingredients", "Bake"],
        "prep_time": "15 minutes",
        "cook_time": "30 minutes",
        "servings": 4,
        "difficulty": "easy",
        "cuisine_type": "american"
    }

class TestRecipeEndpoints:
    async def test_generate_recipe_success(self, client, mock_user, mock_recipe):
        # Mock OpenAI response
        with patch('server.openai_client.chat.completions.create') as mock_openai:
            mock_openai.return_value.choices[0].message.content = json.dumps(mock_recipe)
            
            response = await client.post(
                "/api/recipes/generate",
                json={
                    "user_id": mock_user["id"],
                    "cuisine_type": "italian",
                    "difficulty": "easy",
                    "servings": 4
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Recipe"
            assert len(data["ingredients"]) == 3
            assert len(data["instructions"]) == 2

    async def test_recipe_history_success(self, client, mock_user):
        # Pre-populate database with test recipes
        await setup_test_recipes(mock_user["id"])
        
        response = await client.get(f"/api/recipes/history/{mock_user['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert len(data["recipes"]) > 0
        assert data["total_count"] > 0

    async def test_recipe_detail_success(self, client, mock_user):
        # Create test recipe
        recipe_id = await create_test_recipe(mock_user["id"])
        
        response = await client.get(f"/api/recipes/{recipe_id}/detail")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == recipe_id
        assert "ingredients" in data
        assert "instructions" in data

    async def test_recipe_detail_not_found(self, client):
        response = await client.get("/api/recipes/nonexistent-id/detail")
        assert response.status_code == 404

    async def test_delete_recipe_success(self, client, mock_user):
        # Create test recipe
        recipe_id = await create_test_recipe(mock_user["id"])
        
        response = await client.delete(f"/api/recipes/{recipe_id}")
        
        assert response.status_code == 200
        
        # Verify deletion
        detail_response = await client.get(f"/api/recipes/{recipe_id}/detail")
        assert detail_response.status_code == 404

    async def test_generate_recipe_invalid_data(self, client):
        response = await client.post(
            "/api/recipes/generate",
            json={"invalid": "data"}
        )
        
        assert response.status_code == 422  # Validation error
```

#### 2. Database Integration Testing
```python
# test_database.py
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from server import get_database

@pytest.fixture(scope="function")
async def test_db():
    # Create test database connection
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_database
    
    yield db
    
    # Cleanup after test
    await client.drop_database("test_database")
    client.close()

class TestDatabaseOperations:
    async def test_save_recipe(self, test_db):
        recipes_collection = test_db.recipes
        
        recipe_data = {
            "id": "test-recipe-id",
            "user_id": "test-user-id",
            "name": "Test Recipe",
            "ingredients": ["flour", "sugar"],
            "instructions": ["Mix", "Bake"]
        }
        
        result = await recipes_collection.insert_one(recipe_data)
        assert result.inserted_id is not None
        
        # Verify retrieval
        saved_recipe = await recipes_collection.find_one({"id": "test-recipe-id"})
        assert saved_recipe["name"] == "Test Recipe"
        assert len(saved_recipe["ingredients"]) == 2

    async def test_recipe_history_query(self, test_db):
        recipes_collection = test_db.recipes
        
        # Insert test recipes
        recipes = [
            {"id": "recipe-1", "user_id": "user-1", "name": "Recipe 1"},
            {"id": "recipe-2", "user_id": "user-1", "name": "Recipe 2"},
            {"id": "recipe-3", "user_id": "user-2", "name": "Recipe 3"}
        ]
        
        await recipes_collection.insert_many(recipes)
        
        # Query user-1 recipes
        user_recipes = await recipes_collection.find({"user_id": "user-1"}).to_list(None)
        
        assert len(user_recipes) == 2
        assert all(r["user_id"] == "user-1" for r in user_recipes)
```

#### 3. External API Testing
```python
# test_walmart_integration.py
import pytest
from unittest.mock import patch, Mock
from server import search_walmart_products_v2

class TestWalmartIntegration:
    @patch('server.walmart_api_client.search_products')
    async def test_walmart_search_success(self, mock_search):
        # Mock Walmart API response
        mock_search.return_value = {
            "items": [
                {
                    "itemId": "123456",
                    "name": "Test Product",
                    "salePrice": 2.99,
                    "mediumImage": "https://example.com/image.jpg"
                }
            ]
        }
        
        result = await search_walmart_products_v2("flour", max_results=1)
        
        assert len(result) == 1
        assert result[0]["id"] == "123456"
        assert result[0]["name"] == "Test Product"
        assert result[0]["price"] == 2.99

    @patch('server.walmart_api_client.search_products')
    async def test_walmart_search_failure(self, mock_search):
        # Mock API failure
        mock_search.side_effect = Exception("API Error")
        
        result = await search_walmart_products_v2("flour", max_results=1)
        
        assert result == []  # Should return empty list on error

    async def test_cart_options_generation(self):
        ingredients = ["2 cups flour", "1 cup sugar", "3 eggs"]
        
        with patch('server.search_walmart_products_v2') as mock_search:
            mock_search.return_value = [
                {"id": "123", "name": "Flour", "price": 2.99},
                {"id": "456", "name": "Sugar", "price": 3.99},
                {"id": "789", "name": "Eggs", "price": 1.99}
            ]
            
            result = await generate_cart_options(ingredients)
            
            assert len(result["ingredient_matches"]) == 3
            assert result["total_products"] == 3
            assert result["estimated_total"] == 8.97
```

## Integration Testing

### Full User Flow Testing
```javascript
// e2e/recipe-generation-flow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Recipe Generation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test user
    await page.goto('/');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForSelector('[data-testid="dashboard"]');
  });

  test('complete recipe generation workflow', async ({ page }) => {
    // Navigate to recipe generator
    await page.click('button:has-text("Generate Recipe")');
    await page.waitForSelector('[data-testid="recipe-generator"]');

    // Step 1: Select recipe type
    await page.click('button:has-text("Cuisine Recipe")');

    // Step 2: Select cuisine
    await page.click('button:has-text("Italian")');

    // Step 3: Skip dietary preferences
    await page.click('button:has-text("Next")');

    // Step 4: Set cooking details
    await page.click('button:has-text("Easy")');
    
    // Adjust servings
    await page.click('button:has-text("+")');
    await expect(page.locator('text=5')).toBeVisible();
    
    await page.click('button:has-text("Next")');

    // Step 5: Generate recipe
    await page.click('button:has-text("🍳 Generate Recipe")');

    // Wait for generation to complete
    await page.waitForSelector('text=🎉 Your recipe is ready!', { timeout: 30000 });

    // Verify recipe is displayed
    await expect(page.locator('[data-testid="generated-recipe"]')).toBeVisible();
    
    // Test save functionality
    await page.click('button:has-text("💾 Save Recipe")');
    await page.waitForSelector('text=Recipe saved to your collection!');

    // Test view full recipe
    await page.click('button:has-text("👀 View Full Recipe")');
    await page.waitForSelector('[data-testid="recipe-detail"]');

    // Verify recipe detail page
    await expect(page.locator('h1')).toContainText(''); // Recipe name should be present
    await expect(page.locator('text=Ingredients')).toBeVisible();
    await expect(page.locator('text=Instructions')).toBeVisible();
  });

  test('handles generation errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('/api/recipes/generate', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Generation failed' })
      });
    });

    // Navigate through steps
    await page.click('button:has-text("Generate Recipe")');
    await page.click('button:has-text("Cuisine Recipe")');
    await page.click('button:has-text("Italian")');
    await page.click('button:has-text("Next")');
    await page.click('button:has-text("Easy")');
    await page.click('button:has-text("Next")');

    // Attempt generation
    await page.click('button:has-text("🍳 Generate Recipe")');

    // Should show error message
    await page.waitForSelector('text=Failed to generate recipe');
    
    // Should still be on generator page
    await expect(page.locator('[data-testid="recipe-generator"]')).toBeVisible();
  });

  test('recipe history integration', async ({ page }) => {
    // Generate and save a recipe first
    await page.click('button:has-text("Generate Recipe")');
    await page.click('button:has-text("Cuisine Recipe")');
    await page.click('button:has-text("Italian")');
    await page.click('button:has-text("Next")');
    await page.click('button:has-text("Easy")');
    await page.click('button:has-text("Next")');
    await page.click('button:has-text("🍳 Generate Recipe")');
    
    await page.waitForSelector('text=🎉 Your recipe is ready!', { timeout: 30000 });
    await page.click('button:has-text("💾 Save Recipe")');
    await page.waitForSelector('text=Recipe saved to your collection!');

    // Navigate to recipe history
    await page.click('button:has-text("Back")'); // Go back to dashboard
    await page.click('button:has-text("Recipe History")');
    await page.waitForSelector('[data-testid="recipe-history"]');

    // Verify saved recipe appears
    await expect(page.locator('.recipe-card').first()).toBeVisible();

    // Test viewing recipe from history
    await page.click('.recipe-card button:has-text("👀 View")');
    await page.waitForSelector('[data-testid="recipe-detail"]');
  });
});
```

### API Integration Tests
```javascript
// integration/api-integration.test.js
import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';

describe('API Integration Tests', () => {
  let testServer;
  let testUser;

  beforeAll(async () => {
    // Start test server
    testServer = await startTestServer();
    
    // Create test user
    testUser = await createTestUser();
  });

  afterAll(async () => {
    // Cleanup
    await cleanupTestData();
    await testServer.close();
  });

  test('recipe generation end-to-end', async () => {
    const generationData = {
      user_id: testUser.id,
      recipe_type: 'cuisine',
      cuisine_type: 'italian',
      difficulty: 'easy',
      servings: 4
    };

    // Generate recipe
    const generateResponse = await fetch(`${API_BASE}/api/recipes/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(generationData)
    });

    expect(generateResponse.ok).toBe(true);
    const recipe = await generateResponse.json();
    expect(recipe.id).toBeDefined();
    expect(recipe.name).toBeDefined();

    // Retrieve recipe detail
    const detailResponse = await fetch(`${API_BASE}/api/recipes/${recipe.id}/detail`);
    expect(detailResponse.ok).toBe(true);
    const detailData = await detailResponse.json();
    expect(detailData.id).toBe(recipe.id);

    // Check recipe appears in history
    const historyResponse = await fetch(`${API_BASE}/api/recipes/history/${testUser.id}`);
    expect(historyResponse.ok).toBe(true);
    const historyData = await historyResponse.json();
    expect(historyData.recipes.some(r => r.id === recipe.id)).toBe(true);

    // Delete recipe
    const deleteResponse = await fetch(`${API_BASE}/api/recipes/${recipe.id}`, {
      method: 'DELETE'
    });
    expect(deleteResponse.ok).toBe(true);

    // Verify deletion
    const deletedDetailResponse = await fetch(`${API_BASE}/api/recipes/${recipe.id}/detail`);
    expect(deletedDetailResponse.status).toBe(404);
  });

  test('walmart cart integration', async () => {
    // Create test recipe
    const recipe = await createTestRecipe(testUser.id);

    // Get cart options
    const cartResponse = await fetch(
      `${API_BASE}/api/v2/walmart/weekly-cart-options?recipe_id=${recipe.id}`,
      { method: 'POST' }
    );

    expect(cartResponse.ok).toBe(true);
    const cartData = await cartResponse.json();
    expect(cartData.ingredient_matches).toBeDefined();
    expect(Array.isArray(cartData.ingredient_matches)).toBe(true);
  });

  test('subscription flow integration', async () => {
    // Test trial user creation
    const trialUser = await createTrialUser();
    expect(trialUser.subscription.status).toBe('trialing');

    // Test subscription upgrade
    const upgradeResponse = await fetch(`${API_BASE}/api/subscription/upgrade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: trialUser.id,
        payment_method_id: 'pm_test_card'
      })
    });

    expect(upgradeResponse.ok).toBe(true);
    const upgradeData = await upgradeResponse.json();
    expect(upgradeData.subscription.status).toBe('active');
  });
});
```

## Test Configuration

### Jest Configuration
```javascript
// jest.config.js
export default {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/utils/test-setup.js'],
  moduleNameMapping: {
    '\\.(css|less|scss)$': 'identity-obj-proxy',
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/index.js',
    '!src/reportWebVitals.js',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.{js,jsx}',
    '<rootDir>/tests/integration/**/*.test.{js,jsx}'
  ]
};
```

### Playwright Configuration
```javascript
// playwright.config.js
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] }
    }
  ],
  webServer: {
    command: 'yarn start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI
  }
});
```

### Python Test Configuration
```python
# pytest.ini
[tool:pytest]
testpaths = tests/backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=server
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70

# conftest.py
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from server import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_client():
    """Create test client."""
    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def test_db():
    """Create test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_db
    yield db
    await client.drop_database("test_db")
    client.close()
```

## Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'yarn'
          cache-dependency-path: frontend/yarn.lock
      
      - name: Install dependencies
        run: cd frontend && yarn install
      
      - name: Run unit tests
        run: cd frontend && yarn test --coverage --watchAll=false
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: frontend/coverage/lcov.info

  backend-tests:
    runs-on: ubuntu-latest
    services:
      mongodb:
        image: mongo:5.0
        ports:
          - 27017:27017
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run backend tests
        env:
          MONGO_URL: mongodb://localhost:27017/test_db
          OPENAI_API_KEY: test_key
        run: cd backend && pytest --cov=server --cov-report=xml
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'yarn'
      
      - name: Install dependencies
        run: yarn install
      
      - name: Install Playwright browsers
        run: npx playwright install --with-deps
      
      - name: Start application
        run: |
          cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8001 &
          cd frontend && yarn start &
        env:
          MONGO_URL: mongodb://localhost:27017/test_db
          REACT_APP_BACKEND_URL: http://localhost:8001
      
      - name: Run Playwright tests
        run: npx playwright test
      
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## Test Data Management

### Mock Data Factory
```javascript
// utils/mock-data.js
export const createMockRecipe = (overrides = {}) => ({
  id: `recipe-${Date.now()}`,
  name: 'Test Recipe',
  description: 'A delicious test recipe',
  ingredients: ['ingredient 1', 'ingredient 2'],
  instructions: ['step 1', 'step 2'],
  prep_time: '15 minutes',
  cook_time: '30 minutes',
  servings: 4,
  difficulty: 'easy',
  cuisine_type: 'american',
  created_at: new Date().toISOString(),
  category: 'regular',
  ...overrides
});

export const createMockUser = (overrides = {}) => ({
  id: `user-${Date.now()}`,
  email: 'test@example.com',
  subscription: {
    status: 'active',
    trial_end: Date.now() + 7 * 24 * 60 * 60 * 1000
  },
  created_at: new Date().toISOString(),
  ...overrides
});

export const createMockCartOptions = (ingredients = []) => ({
  ingredient_matches: ingredients.map((ingredient, index) => ({
    ingredient,
    products: [
      {
        id: `product-${index}`,
        name: `Test Product for ${ingredient}`,
        price: (Math.random() * 10 + 1).toFixed(2),
        image: 'https://example.com/image.jpg'
      }
    ]
  })),
  total_products: ingredients.length,
  estimated_total: (ingredients.length * 5).toFixed(2)
});
```

## Performance Testing

### Load Testing with Artillery
```yaml
# artillery-config.yml
config:
  target: 'http://localhost:8001'
  phases:
    - duration: 60
      arrivalRate: 10
  payload:
    path: './test-data.csv'
    fields:
      - user_id

scenarios:
  - name: "Recipe Generation"
    weight: 50
    flow:
      - post:
          url: "/api/recipes/generate"
          json:
            user_id: "{{ user_id }}"
            cuisine_type: "italian"
            difficulty: "easy"
            servings: 4
      
  - name: "Recipe History"
    weight: 30
    flow:
      - get:
          url: "/api/recipes/history/{{ user_id }}"
      
  - name: "Recipe Detail"
    weight: 20
    flow:
      - get:
          url: "/api/recipes/history/{{ user_id }}"
      - get:
          url: "/api/recipes/{{ $randomString() }}/detail"
```

## Testing Best Practices

### 1. Test Organization
- Group related tests using `describe` blocks
- Use descriptive test names that explain the expected behavior
- Follow the AAA pattern (Arrange, Act, Assert)
- Keep tests focused and independent

### 2. Mock Strategy
- Mock external APIs and services
- Use real database for integration tests
- Mock heavy computations and time-dependent operations
- Keep mocks close to the real implementation

### 3. Test Coverage
- Aim for 70-80% code coverage
- Focus on testing critical business logic
- Don't chase 100% coverage at the expense of test quality
- Use coverage reports to identify untested code paths

### 4. Performance Testing
- Test loading states and error conditions
- Verify component performance with large datasets
- Test API response times under load
- Monitor memory usage in long-running tests

### 5. Accessibility Testing
- Test keyboard navigation
- Verify screen reader compatibility
- Check color contrast ratios
- Test with assistive technologies

## Troubleshooting Common Issues

### 1. Test Flakiness
```javascript
// Use waitFor for async operations
await waitFor(() => {
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
}, { timeout: 5000 });

// Mock timers for time-dependent tests
beforeEach(() => {
  jest.useFakeTimers();
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});
```

### 2. Memory Leaks
```javascript
// Clean up event listeners
afterEach(() => {
  cleanup();
  jest.clearAllMocks();
  jest.clearAllTimers();
});
```

### 3. Network Issues
```javascript
// Retry failed network requests
const fetchWithRetry = async (url, options, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fetch(url, options);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

---

**Last Updated**: January 2025
**Version**: 2.0.0