import { test, expect } from '@playwright/test';

test.describe('Recipe Management E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test user session
    await page.addInitScript(() => {
      const mockUser = {
        id: 'test-user-id',
        email: 'demo@test.com',
        loginTime: Date.now(),
        sessionExpiry: Date.now() + (7 * 24 * 60 * 60 * 1000)
      };
      localStorage.setItem('ai_chef_user', JSON.stringify(mockUser));
    });

    await page.goto('/');
  });

  test('complete recipe history workflow', async ({ page }) => {
    // Should automatically navigate to dashboard with stored session
    await expect(page.locator('text=Dashboard')).toBeVisible({ timeout: 10000 });

    // Navigate to Recipe History
    await page.click('button:has-text("Recipe History")');

    // Verify Recipe History screen loads
    await expect(page.locator('text=NEW Recipe History')).toBeVisible({ timeout: 10000 });

    // Check for recipe cards (if any exist)
    const recipeCards = await page.locator('.recipe-card').count();
    if (recipeCards > 0) {
      // Test recipe detail navigation
      await page.click('.recipe-card >> button:has-text("👀 View")');

      // Should navigate to recipe detail
      await expect(page.locator('[data-testid="recipe-detail"]')).toBeVisible({ timeout: 10000 });

      // Test navigation back
      await page.click('button:has-text("← Back")');

      // Should return to recipe history
      await expect(page.locator('text=NEW Recipe History')).toBeVisible();
    }
  });

  test('recipe generation workflow', async ({ page }) => {
    // Navigate to recipe generator
    await page.click('button:has-text("Generate AI Recipe")');

    // Verify generator screen loads
    await expect(page.locator('text=What type of recipe')).toBeVisible();

    // Select recipe type
    await page.click('button:has-text("Cuisine Recipe")');

    // Select cuisine
    await page.click('button:has-text("Italian")');

    // Skip dietary preferences
    await page.click('button:has-text("Next")');

    // Set cooking details
    await page.click('button:has-text("Easy")');
    await page.click('button:has-text("Next")');

    // Generate recipe
    await page.click('button:has-text("🍳 Generate Recipe")');

    // Wait for generation to complete (may take time with mock data)
    await expect(page.locator('text=Your recipe is ready')).toBeVisible({ timeout: 30000 });
  });

  test('weekly meal planner workflow', async ({ page }) => {
    // Navigate to weekly meal planner
    await page.click('button:has-text("Weekly Meal Planner")');

    // Verify weekly recipes screen loads
    await expect(page.locator('text=Weekly Recipes')).toBeVisible({ timeout: 10000 });

    // Check for meal cards
    const mealCards = await page.locator('.meal-card').count();
    if (mealCards > 0) {
      // Click view full recipe on first meal
      await page.click('.meal-card >> button:has-text("View Full Recipe")');

      // Should navigate to recipe detail
      await expect(page.locator('h1')).toBeVisible({ timeout: 10000 });

      // Test navigation back
      await page.click('button:has-text("← Back")');

      // Should return to weekly recipes
      await expect(page.locator('text=Weekly Recipes')).toBeVisible();
    }
  });

  test('handles network errors gracefully', async ({ page }) => {
    // Intercept API calls to simulate network errors
    await page.route('**/api/recipes/**', route => {
      route.abort('failed');
    });

    // Navigate to recipe history
    await page.click('button:has-text("Recipe History")');

    // Should show error state
    await expect(page.locator('text=Error loading')).toBeVisible({ timeout: 10000 });
  });

  test('responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });

    // Test navigation on mobile
    await page.click('button:has-text("Recipe History")');

    // Verify mobile layout
    await expect(page.locator('text=NEW Recipe History')).toBeVisible();

    // Test touch interactions
    const recipeCards = await page.locator('.recipe-card').count();
    if (recipeCards > 0) {
      // Tap on recipe card
      await page.tap('.recipe-card');
    }
  });
});