import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import RecipeHistoryScreen from '../../../frontend/src/components/RecipeHistoryScreen';

// Mock data
const mockRecipes = [
  {
    id: 'recipe-1',
    title: 'Classic Margherita Pizza',
    description: 'Traditional Italian pizza',
    created_at: '2025-01-10T12:00:00Z',
    category: 'regular',
    cuisine_type: 'italian',
    prep_time: '30 minutes',
    cook_time: '15 minutes',
    servings: 4
  },
  {
    id: 'recipe-2', 
    title: 'Starbucks Caramel Frappuccino',
    description: 'Homemade version of popular drink',
    created_at: '2025-01-09T14:30:00Z',
    category: 'starbucks',
    type: 'starbucks'
  }
];

const mockProps = {
  user: { id: 'test-user-id', email: 'test@example.com' },
  onBack: jest.fn(),
  showNotification: jest.fn(),
  onViewRecipe: jest.fn(),
  onViewStarbucksRecipe: jest.fn()
};

// Global fetch mock
global.fetch = jest.fn();

describe('RecipeHistoryScreen Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Initial Rendering', () => {
    test('renders loading state initially', () => {
      render(<RecipeHistoryScreen {...mockProps} />);
      
      expect(screen.getByText(/Loading/)).toBeInTheDocument();
      expect(screen.getByText(/NEW Recipe History/)).toBeInTheDocument();
    });

    test('displays correct header and branding', () => {
      render(<RecipeHistoryScreen {...mockProps} />);
      
      expect(screen.getByText(/🆕 NEW Recipe History/)).toBeInTheDocument();
      expect(screen.getByText(/Completely rebuilt from scratch/)).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    test('successfully loads and displays recipe data', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ 
          recipes: mockRecipes, 
          total_count: 2 
        })
      });

      render(<RecipeHistoryScreen {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('Classic Margherita Pizza')).toBeInTheDocument();
        expect(screen.getByText('Starbucks Caramel Frappuccino')).toBeInTheDocument();
        expect(screen.getByText('📊 Total: 2 | Shown: 2')).toBeInTheDocument();
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/recipes/history/test-user-id')
      );
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

    test('handles empty recipe list', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ 
          recipes: [], 
          total_count: 0 
        })
      });

      render(<RecipeHistoryScreen {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText(/No recipes found/)).toBeInTheDocument();
      });
    });
  });

  describe('Recipe Filtering', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ 
          recipes: mockRecipes, 
          total_count: 2 
        })
      });

      render(<RecipeHistoryScreen {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('Classic Margherita Pizza')).toBeInTheDocument();
      });
    });

    test('filters regular recipes correctly', async () => {
      fireEvent.click(screen.getByText('Cuisine'));

      await waitFor(() => {
        expect(screen.getByText('Classic Margherita Pizza')).toBeInTheDocument();
        expect(screen.queryByText('Starbucks Caramel Frappuccino')).not.toBeInTheDocument();
      });
    });

    test('filters Starbucks recipes correctly', async () => {
      fireEvent.click(screen.getByText('Starbucks'));

      await waitFor(() => {
        expect(screen.queryByText('Classic Margherita Pizza')).not.toBeInTheDocument();
        expect(screen.getByText('Starbucks Caramel Frappuccino')).toBeInTheDocument();
      });
    });
  });

  describe('Recipe Actions', () => {
    beforeEach(async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ 
          recipes: mockRecipes, 
          total_count: 2 
        })
      });

      render(<RecipeHistoryScreen {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('Classic Margherita Pizza')).toBeInTheDocument();
      });
    });

    test('handles recipe view action correctly', async () => {
      const viewButtons = screen.getAllByText('👀 View');
      fireEvent.click(viewButtons[0]);

      expect(mockProps.onViewRecipe).toHaveBeenCalledWith('recipe-1', 'history');
    });

    test('handles recipe deletion with confirmation', async () => {
      window.confirm = jest.fn(() => true);

      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      const deleteButtons = screen.getAllByTitle('🗑️');
      fireEvent.click(deleteButtons[0]);

      expect(window.confirm).toHaveBeenCalledWith('Delete this recipe?');

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/recipes/recipe-1'),
          expect.objectContaining({ method: 'DELETE' })
        );
        expect(mockProps.showNotification).toHaveBeenCalledWith(
          'Recipe deleted',
          'success'
        );
      });
    });
  });
});

export { mockRecipes, mockProps };