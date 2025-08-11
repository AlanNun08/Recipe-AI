# Testing Execution Guide

## Overview
This guide provides comprehensive instructions for running tests, interpreting results, and maintaining the testing infrastructure for the AI Recipe + Grocery Delivery App.

## Test Infrastructure Summary

### Testing Stack
- **Frontend**: Jest + React Testing Library + Playwright
- **Backend**: pytest + httpx + pytest-asyncio
- **Integration**: MSW (Mock Service Worker)
- **E2E**: Playwright with multi-browser support
- **Performance**: Artillery.js
- **Security**: Trivy + npm audit + safety

## Quick Test Commands

### Frontend Testing
```bash
# Navigate to frontend directory
cd frontend

# Run all unit tests
yarn test

# Run tests with coverage
yarn test --coverage

# Run tests in CI mode (single run)
yarn test --ci --coverage --watchAll=false

# Run tests for specific component
yarn test RecipeHistoryScreen.test.js

# Run tests in watch mode
yarn test --watch

# Update snapshots
yarn test --updateSnapshot
```

### Backend Testing
```bash
# Navigate to backend directory
cd backend

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=server

# Run specific test file
pytest tests/test_recipe_endpoints.py

# Run specific test method
pytest tests/test_recipe_endpoints.py::TestRecipeGeneration::test_generate_recipe_success

# Run tests with coverage report in HTML
pytest --cov=server --cov-report=html

# Run only unit tests (marked with @pytest.mark.unit)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run with maximum failures before stopping
pytest --maxfail=3
```

### End-to-End Testing
```bash
# From root directory

# Install Playwright browsers (first time only)
npx playwright install --with-deps

# Run all E2E tests
npx playwright test

# Run tests in headed mode (with browser UI)
npx playwright test --headed

# Run specific test file
npx playwright test tests/e2e/recipe-management.spec.js

# Run tests on specific browser
npx playwright test --project=chromium

# Run tests with debug mode
npx playwright test --debug

# Generate test report
npx playwright show-report
```

### Performance Testing
```bash
# From root directory

# Install Artillery globally
npm install -g artillery@latest

# Run load tests
artillery run tests/performance/load-test.yml

# Run stress tests
artillery run tests/performance/stress-test.yml

# Run with custom output
artillery run tests/performance/load-test.yml --output performance-results.json
```

## Continuous Integration

### GitHub Actions Workflow
The CI pipeline automatically runs:
1. **Frontend Tests**: Unit tests with coverage on Node 18 & 20
2. **Backend Tests**: API tests with coverage on Python 3.9, 3.10 & 3.11
3. **E2E Tests**: Full application workflow tests
4. **Security Tests**: Vulnerability scanning
5. **Performance Tests**: Load and stress testing
6. **Build & Package**: Deployment artifact creation

### Manual CI Trigger
```bash
# Trigger specific test type via GitHub UI or API
gh workflow run comprehensive-testing.yml --ref main -f test_type=frontend
gh workflow run comprehensive-testing.yml --ref main -f test_type=backend
gh workflow run comprehensive-testing.yml --ref main -f test_type=e2e
gh workflow run comprehensive-testing.yml --ref main -f test_type=all
```

## Test Configuration

### Jest Configuration (Frontend)
```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  collectCoverageFrom: [
    'frontend/src/**/*.{js,jsx}',
    '!frontend/src/index.js',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75
    }
  }
};
```

### Pytest Configuration (Backend)
```ini
# pytest.ini
[tool:pytest]
testpaths = tests/backend
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --verbose
    --cov=server
    --cov-report=html
    --cov-fail-under=75
```

### Playwright Configuration (E2E)
```javascript
// playwright.config.js
module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html'], ['junit', { outputFile: 'results.xml' }]],
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ]
});
```

## Test Development Guidelines

### Writing Frontend Tests

#### Component Test Structure
```javascript
// tests/frontend/unit/components/NewComponent.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NewComponent from '../../../frontend/src/components/NewComponent';
import { createMockProps } from '../../utils/testHelpers';

describe('NewComponent', () => {
  const defaultProps = createMockProps();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  describe('Rendering', () => {
    test('renders without crashing', () => {
      render(<NewComponent {...defaultProps} />);
      expect(screen.getByText('Expected Text')).toBeInTheDocument();
    });
    
    test('displays loading state correctly', () => {
      render(<NewComponent {...defaultProps} isLoading={true} />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });
  
  describe('User Interactions', () => {
    test('handles button click correctly', async () => {
      const mockOnClick = jest.fn();
      render(<NewComponent {...defaultProps} onClick={mockOnClick} />);
      
      fireEvent.click(screen.getByRole('button'));
      
      await waitFor(() => {
        expect(mockOnClick).toHaveBeenCalledTimes(1);
      });
    });
  });
  
  describe('API Integration', () => {
    test('fetches data successfully', async () => {
      const mockData = { items: [{ id: 1, name: 'Test' }] };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData)
      });
      
      render(<NewComponent {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Test')).toBeInTheDocument();
      });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/endpoint')
      );
    });
  });
});
```

### Writing Backend Tests

#### API Endpoint Test Structure
```python
# tests/backend/test_new_endpoints.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

class TestNewEndpoints:
    """Test suite for new API endpoints."""
    
    async def test_endpoint_success(self, test_client: AsyncClient, mock_user_data):
        """Test successful endpoint operation."""
        with patch('server.collection.find_one') as mock_find:
            mock_find.return_value = mock_user_data
            
            response = await test_client.post("/api/new-endpoint", json={
                "user_id": mock_user_data["id"],
                "data": "test data"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    async def test_endpoint_validation_error(self, test_client: AsyncClient):
        """Test endpoint with invalid data."""
        response = await test_client.post("/api/new-endpoint", json={
            "invalid": "data"
        })
        
        assert response.status_code == 422  # Validation error
    
    async def test_endpoint_not_found(self, test_client: AsyncClient):
        """Test endpoint with non-existent resource."""
        with patch('server.collection.find_one', return_value=None):
            response = await test_client.get("/api/new-endpoint/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
```

### Writing E2E Tests

#### E2E Test Structure
```javascript
// tests/e2e/new-feature.spec.js
import { test, expect } from '@playwright/test';

test.describe('New Feature E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test user session
    await page.addInitScript(() => {
      localStorage.setItem('ai_chef_user', JSON.stringify({
        id: 'test-user-id',
        email: 'test@example.com',
        loginTime: Date.now(),
        sessionExpiry: Date.now() + 7 * 24 * 60 * 60 * 1000
      }));
    });
    
    await page.goto('/');
  });
  
  test('complete feature workflow', async ({ page }) => {
    // Navigate to feature
    await page.click('button:has-text("New Feature")');
    await expect(page.locator('h1')).toContainText('New Feature');
    
    // Interact with feature
    await page.fill('input[name="input"]', 'test value');
    await page.click('button:has-text("Submit")');
    
    // Verify results
    await expect(page.locator('.result')).toBeVisible();
    await expect(page.locator('.success-message')).toContainText('Success');
  });
  
  test('handles errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/new-endpoint', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Server error' })
      });
    });
    
    await page.click('button:has-text("New Feature")');
    await page.fill('input[name="input"]', 'test value');
    await page.click('button:has-text("Submit")');
    
    // Should show error message
    await expect(page.locator('.error-message')).toBeVisible();
    await expect(page.locator('.error-message')).toContainText('Error');
  });
});
```

## Test Data Management

### Mock Data Creation
```javascript
// tests/utils/mockData.js
export const createMockUser = (overrides = {}) => ({
  id: 'test-user-id',
  email: 'test@example.com',
  subscription: { status: 'active' },
  created_at: new Date().toISOString(),
  ...overrides
});

export const createMockRecipe = (overrides = {}) => ({
  id: 'test-recipe-id',
  name: 'Test Recipe',
  ingredients: ['ingredient1', 'ingredient2'],
  instructions: ['step1', 'step2'],
  created_at: new Date().toISOString(),
  ...overrides
});
```

### Database Test Utilities
```python
# tests/backend/utils.py
async def create_test_user(db, user_data: dict) -> str:
    """Create a test user in database."""
    result = await db.users.insert_one(user_data)
    return user_data["id"]

async def cleanup_test_data(db, collections: list = None):
    """Clean up test data after tests."""
    collections = collections or ["users", "recipes", "weekly_recipes"]
    for collection in collections:
        await db[collection].delete_many({"test_data": True})
```

## Coverage Analysis

### Understanding Coverage Reports

#### Frontend Coverage
```bash
# Generate detailed HTML coverage report
cd frontend
yarn test --coverage

# View coverage report
open coverage/lcov-report/index.html
```

#### Backend Coverage
```bash
# Generate HTML coverage report
cd backend
pytest --cov=server --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Coverage Goals
- **Statements**: 80%+
- **Branches**: 75%+
- **Functions**: 80%+
- **Lines**: 80%+

### Improving Coverage
1. **Identify uncovered code**: Use coverage reports to find untested areas
2. **Add unit tests**: Focus on business logic and edge cases
3. **Integration tests**: Cover API endpoints and data flows
4. **E2E tests**: Cover complete user workflows

## Debugging Tests

### Frontend Test Debugging
```bash
# Run tests with verbose output
yarn test --verbose

# Run single test file in debug mode
yarn test RecipeHistoryScreen.test.js --no-cache --watchAll=false

# Debug with Node.js debugger
node --inspect-brk node_modules/.bin/jest --runInBand --no-cache RecipeHistoryScreen.test.js
```

### Backend Test Debugging
```bash
# Run tests with pdb debugger
pytest --pdb tests/test_recipe_endpoints.py

# Run specific test with verbose output
pytest -v -s tests/test_recipe_endpoints.py::test_generate_recipe_success

# Debug with logging
pytest --log-cli-level=DEBUG tests/test_recipe_endpoints.py
```

### E2E Test Debugging
```bash
# Run in headed mode (see browser)
npx playwright test --headed

# Run with debug mode (step through)
npx playwright test --debug

# Run with trace viewer
npx playwright test --trace on
npx playwright show-trace trace.zip
```

## Troubleshooting Common Issues

### Frontend Test Issues

#### Problem: Tests timeout
**Solution**: Increase timeout or use `waitFor` properly
```javascript
// Increase timeout
test('async operation', async () => {
  // ... test code
}, 10000); // 10 second timeout

// Use waitFor correctly
await waitFor(() => {
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
}, { timeout: 5000 });
```

#### Problem: Component not rendering
**Solution**: Check props and mock dependencies
```javascript
// Mock all required props
const mockProps = {
  user: { id: 'test-user' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  // ... other required props
};
```

### Backend Test Issues

#### Problem: Database connection errors
**Solution**: Ensure MongoDB is running or use test database
```python
# Use test database fixture
@pytest.fixture
async def test_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_database
    yield db
    await client.drop_database("test_database")
```

#### Problem: Async test failures
**Solution**: Use proper async/await patterns
```python
# Correct async test
async def test_async_operation(test_client):
    response = await test_client.get("/api/endpoint")
    assert response.status_code == 200
```

### E2E Test Issues

#### Problem: Element not found
**Solution**: Use proper selectors and waits
```javascript
// Wait for element to be visible
await expect(page.locator('selector')).toBeVisible({ timeout: 10000 });

// Use more specific selectors
await page.locator('[data-testid="submit-button"]').click();
```

#### Problem: Test flakiness
**Solution**: Add proper waits and stabilize selectors
```javascript
// Wait for network requests to complete
await page.waitForLoadState('networkidle');

// Wait for specific conditions
await page.waitForFunction(() => window.dataLoaded === true);
```

## Best Practices

### Test Organization
1. **Group related tests**: Use `describe` blocks for logical grouping
2. **Clear test names**: Describe the expected behavior
3. **Setup/teardown**: Use `beforeEach`/`afterEach` for test isolation
4. **Mock external dependencies**: Focus on unit being tested

### Test Writing
1. **AAA Pattern**: Arrange, Act, Assert
2. **Single responsibility**: Test one thing per test
3. **Edge cases**: Test boundary conditions and error scenarios
4. **Readable assertions**: Use descriptive assertion messages

### Test Maintenance
1. **Regular updates**: Update tests when code changes
2. **Remove obsolete tests**: Clean up tests for removed features
3. **Refactor duplicated code**: Create reusable test utilities
4. **Monitor coverage**: Maintain minimum coverage thresholds

This comprehensive testing execution guide provides everything needed to effectively run, debug, and maintain the testing infrastructure for the AI Recipe + Grocery Delivery App.