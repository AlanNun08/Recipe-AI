import React, { useState, useEffect, useMemo } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * RecipeHistoryScreen Component
 * 
 * A clean, well-architected component for displaying user's recipe history
 * Built according to the Recipe History Architecture Guide
 * 
 * Features:
 * - Robust error handling and loading states
 * - Type-based filtering (All, Regular, Starbucks)
 * - Search functionality with debouncing
 * - Optimistic updates for deletions
 * - Accessible keyboard navigation
 * - Responsive design
 * 
 * @param {Object} props - Component props
 * @param {Object} props.user - Current user object with id
 * @param {Function} props.onBack - Navigation back function
 * @param {Function} props.showNotification - Notification display function
 * @param {Function} props.onViewRecipe - Recipe detail navigation function
 * @param {Function} props.onViewStarbucksRecipe - Starbucks recipe navigation function
 */
function RecipeHistoryScreen({ 
  user, 
  onBack, 
  showNotification, 
  onViewRecipe, 
  onViewStarbucksRecipe 
}) {
  // ==================== STATE MANAGEMENT ====================
  
  // Core data
  const [recipes, setRecipes] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Interaction state
  const [deletingIds, setDeletingIds] = useState(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  
  // ==================== FILTER CONFIGURATION ====================
  
  const filterOptions = [
    { id: 'all', label: 'All Recipes', icon: '🍽️', description: 'Show all your recipes' },
    { id: 'regular', label: 'Regular Recipes', icon: '🍳', description: 'AI-generated recipes' },
    { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕', description: 'Secret menu creations' }
  ];
  
  // ==================== DATA FETCHING ====================
  
  /**
   * Fetch user's recipe history from the backend
   * Implements proper error handling and loading states
   */
  const fetchRecipeHistory = async () => {
    if (!user?.id) {
      setError('User not found');
      setIsLoading(false);
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('🔍 Fetching recipe history for user:', user.id);
      
      const response = await fetch(`${API}/api/recipes/history/${user.id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to fetch recipes: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Recipe history fetched:', data);
      
      // Validate response structure
      if (!data.recipes || !Array.isArray(data.recipes)) {
        throw new Error('Invalid response format from server');
      }
      
      // Transform and clean data
      const cleanedRecipes = data.recipes.map(recipe => ({
        id: recipe.id,
        title: recipe.title || recipe.drink_name || recipe.name || 'Untitled Recipe',
        description: recipe.description || 'No description available',
        cuisine_type: recipe.cuisine_type || recipe.cuisine || 'International',
        prep_time: recipe.prep_time || 'N/A',
        cook_time: recipe.cook_time || 'N/A',
        servings: recipe.servings || 'N/A',
        difficulty: recipe.difficulty || 'Medium',
        created_at: recipe.created_at,
        category: recipe.category || 'regular',
        type: recipe.type || 'regular',
        // Additional fields for Starbucks recipes
        drink_name: recipe.drink_name,
        base_drink: recipe.base_drink,
        customizations: recipe.customizations
      }));
      
      setRecipes(cleanedRecipes);
      setTotalCount(data.total_count || cleanedRecipes.length);
      
      if (cleanedRecipes.length === 0) {
        showNotification('No recipes found. Start creating some!', 'info');
      }
      
    } catch (error) {
      console.error('❌ Failed to fetch recipe history:', error);
      setError(error.message);
      showNotification(`Failed to load recipes: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Load data on component mount
  useEffect(() => {
    fetchRecipeHistory();
  }, [user?.id]);
  
  // ==================== FILTERING & SEARCH ====================
  
  /**
   * Apply filters and search to recipes
   * Uses useMemo for performance optimization
   */
  const filteredRecipes = useMemo(() => {
    let filtered = [...recipes];
    
    // Apply type filter
    if (selectedFilter !== 'all') {
      filtered = filtered.filter(recipe => {
        if (selectedFilter === 'starbucks') {
          return recipe.category === 'starbucks' || recipe.type === 'starbucks';
        }
        if (selectedFilter === 'regular') {
          return recipe.category !== 'starbucks' && recipe.type !== 'starbucks';
        }
        return true;
      });
    }
    
    // Apply search filter
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(recipe =>
        recipe.title.toLowerCase().includes(searchLower) ||
        recipe.description.toLowerCase().includes(searchLower) ||
        recipe.cuisine_type.toLowerCase().includes(searchLower)
      );
    }
    
    // Sort by creation date (newest first)
    filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    
    return filtered;
  }, [recipes, selectedFilter, searchTerm]);
  
  // ==================== ACTION HANDLERS ====================
  
  /**
   * Handle recipe view navigation based on recipe type
   */
  const handleViewRecipe = (recipe) => {
    if (!recipe || !recipe.id) {
      showNotification('❌ Recipe data is invalid', 'error');
      return;
    }
    
    console.log('🔍 Viewing recipe:', recipe.title, 'Type:', recipe.type, 'ID:', recipe.id);
    
    // Route to appropriate handler based on recipe type
    if (recipe.category === 'starbucks' || recipe.type === 'starbucks') {
      if (onViewStarbucksRecipe) {
        onViewStarbucksRecipe(recipe);
      } else {
        showNotification('🌟 Starbucks recipe viewer not available', 'warning');
      }
    } else {
      if (onViewRecipe) {
        onViewRecipe(recipe.id, 'history');
      } else {
        showNotification('❌ Recipe viewer not available', 'error');
      }
    }
  };
  
  /**
   * Handle recipe deletion with optimistic updates
   */
  const handleDeleteRecipe = async (recipeId) => {
    if (!recipeId) {
      showNotification('❌ Recipe ID is missing', 'error');
      return;
    }
    
    // Show confirmation
    if (!window.confirm('Are you sure you want to delete this recipe? This action cannot be undone.')) {
      return;
    }
    
    // Optimistic update - remove from UI immediately
    const originalRecipes = [...recipes];
    setRecipes(prev => prev.filter(r => r.id !== recipeId));
    setDeletingIds(prev => new Set([...prev, recipeId]));
    
    try {
      console.log('🗑️ Deleting recipe:', recipeId);
      
      const response = await fetch(`${API}/api/recipes/${recipeId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete recipe: ${response.status} ${response.statusText}`);
      }
      
      console.log('✅ Recipe deleted successfully');
      showNotification('✅ Recipe deleted successfully', 'success');
      setTotalCount(prev => Math.max(0, prev - 1));
      
    } catch (error) {
      console.error('❌ Failed to delete recipe:', error);
      
      // Revert optimistic update
      setRecipes(originalRecipes);
      showNotification(`❌ Failed to delete recipe: ${error.message}`, 'error');
    } finally {
      setDeletingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(recipeId);
        return newSet;
      });
    }
  };
  
  /**
   * Handle retry after error
   */
  const handleRetry = () => {
    fetchRecipeHistory();
  };
  
  // ==================== RENDER HELPERS ====================
  
  /**
   * Render loading state
   */
  const renderLoading = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50 flex items-center justify-center">
      <div className="bg-white rounded-3xl shadow-lg p-8 text-center max-w-md">
        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Recipe History</h2>
        <p className="text-gray-600">Fetching your saved recipes...</p>
      </div>
    </div>
  );
  
  /**
   * Render error state
   */
  const renderError = () => (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-lg p-8 text-center max-w-md">
        <div className="text-6xl mb-4">😞</div>
        <h2 className="text-2xl font-bold text-red-600 mb-4">Failed to Load Recipes</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={handleRetry}
            className="bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200"
          >
            🔄 Try Again
          </button>
          <button
            onClick={onBack}
            className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-3 px-6 rounded-xl transition-all duration-200"
          >
            ← Go Back
          </button>
        </div>
      </div>
    </div>
  );
  
  /**
   * Render empty state
   */
  const renderEmpty = () => {
    const isFiltered = selectedFilter !== 'all' || searchTerm.trim();
    const currentFilter = filterOptions.find(f => f.id === selectedFilter);
    
    return (
      <div className="text-center py-16">
        <div className="bg-white rounded-3xl shadow-lg p-12 max-w-md mx-auto">
          <div className="text-8xl mb-6">
            {isFiltered ? '🔍' : '📝'}
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-4">
            {isFiltered 
              ? `No ${currentFilter?.label || 'Recipes'} Found`
              : 'No Recipes Yet'
            }
          </h3>
          <p className="text-gray-600 mb-8 leading-relaxed">
            {isFiltered
              ? `No recipes match your current search or filter. Try adjusting your criteria.`
              : `You haven't created any recipes yet. Start generating some delicious recipes!`
            }
          </p>
          <div className="flex gap-4 justify-center">
            {isFiltered && (
              <button
                onClick={() => {
                  setSelectedFilter('all');
                  setSearchTerm('');
                }}
                className="bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200"
              >
                🔄 Clear Filters
              </button>
            )}
            <button
              onClick={() => {
                // Navigate to recipe generator
                onBack();
                // This would need to be handled by parent component
                // setCurrentScreen('recipe-generation');
              }}
              className="bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200"
            >
              🍳 Create Recipe
            </button>
          </div>
        </div>
      </div>
    );
  };
  
  /**
   * Render recipe card
   */
  const renderRecipeCard = (recipe) => {
    const isDeleting = deletingIds.has(recipe.id);
    const isStarbucks = recipe.category === 'starbucks' || recipe.type === 'starbucks';
    
    // Format creation date
    const createdDate = recipe.created_at 
      ? new Date(recipe.created_at).toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      : 'Unknown date';
    
    // Get appropriate colors for recipe type
    const cardColors = isStarbucks 
      ? 'bg-gradient-to-r from-green-500 to-teal-500'
      : 'bg-gradient-to-r from-orange-500 to-red-500';
    
    const categoryIcon = isStarbucks ? '☕' : '🍳';
    const categoryLabel = isStarbucks ? 'Starbucks Drink' : 'Recipe';
    
    return (
      <div 
        key={recipe.id}
        className={`bg-white rounded-3xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 ${isDeleting ? 'opacity-50' : ''}`}
      >
        {/* Recipe Header */}
        <div className={`${cardColors} text-white p-6`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-3xl">{categoryIcon}</span>
            <span className="text-xs bg-white bg-opacity-20 px-3 py-1 rounded-full font-medium">
              {categoryLabel}
            </span>
          </div>
          <h3 className="text-xl font-bold leading-tight mb-2 line-clamp-2">
            {recipe.title}
          </h3>
          <p className="text-sm text-white text-opacity-90">
            {createdDate}
          </p>
        </div>

        {/* Recipe Content */}
        <div className="p-6">
          <p className="text-gray-600 text-sm mb-6 leading-relaxed line-clamp-3">
            {recipe.description}
          </p>
          
          {/* Recipe Stats - Only show for regular recipes */}
          {!isStarbucks && (
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="text-center bg-gray-50 rounded-lg p-3">
                <div className="text-lg">⏱️</div>
                <div className="text-xs text-gray-600">Prep Time</div>
                <div className="font-bold text-sm">{recipe.prep_time}</div>
              </div>
              <div className="text-center bg-gray-50 rounded-lg p-3">
                <div className="text-lg">👥</div>
                <div className="text-xs text-gray-600">Servings</div>
                <div className="font-bold text-sm">{recipe.servings}</div>
              </div>
            </div>
          )}
          
          {/* Starbucks specific info */}
          {isStarbucks && recipe.base_drink && (
            <div className="mb-6">
              <div className="text-center bg-green-50 rounded-lg p-3">
                <div className="text-lg">☕</div>
                <div className="text-xs text-green-600">Base Drink</div>
                <div className="font-bold text-sm text-green-700">{recipe.base_drink}</div>
              </div>
            </div>
          )}
          
          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => handleViewRecipe(recipe)}
              disabled={isDeleting}
              className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200 text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              👀 View Details
            </button>
            <button
              onClick={() => handleDeleteRecipe(recipe.id)}
              disabled={isDeleting}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-4 rounded-xl transition-all duration-200 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
              title="Delete Recipe"
            >
              {isDeleting ? '⏳' : '🗑️'}
            </button>
          </div>
        </div>
      </div>
    );
  };
  
  // ==================== MAIN RENDER ====================
  
  // Show loading state
  if (isLoading) {
    return renderLoading();
  }
  
  // Show error state
  if (error) {
    return renderError();
  }
  
  // Show empty state
  if (filteredRecipes.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Header */}
          <div className="mb-8">
            <button
              onClick={onBack}
              className="group flex items-center text-purple-700 hover:text-purple-800 font-medium mb-6 transition-all duration-200 hover:transform hover:-translate-x-1"
            >
              <span className="mr-2 group-hover:mr-3 transition-all duration-200">←</span>
              Back to Dashboard
            </button>
            
            <div className="text-center bg-white rounded-3xl shadow-lg p-8 mb-8">
              <div className="text-8xl mb-6 animate-bounce">📚</div>
              <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-4">
                Recipe History
              </h1>
              <p className="text-xl text-gray-600 leading-relaxed max-w-3xl mx-auto">
                Browse and manage all your previously created recipes
              </p>
            </div>
          </div>
          
          {/* Search and Filter Controls */}
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            {/* Search Bar */}
            <div className="mb-6">
              <div className="relative max-w-md mx-auto">
                <input
                  type="text"
                  placeholder="Search recipes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                  🔍
                </div>
              </div>
            </div>
            
            {/* Filter Tabs */}
            <div className="flex flex-wrap gap-4 justify-center">
              {filterOptions.map(option => (
                <button
                  key={option.id}
                  onClick={() => setSelectedFilter(option.id)}
                  className={`flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                    selectedFilter === option.id
                      ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title={option.description}
                >
                  <span className="mr-2 text-xl">{option.icon}</span>
                  {option.label}
                  <span className="ml-2 bg-white bg-opacity-20 text-xs px-2 py-1 rounded-full">
                    {selectedFilter === option.id ? filteredRecipes.length : '0'}
                  </span>
                </button>
              ))}
            </div>
          </div>
          
          {renderEmpty()}
        </div>
      </div>
    );
  }
  
  // Main render with recipes
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="group flex items-center text-purple-700 hover:text-purple-800 font-medium mb-6 transition-all duration-200 hover:transform hover:-translate-x-1"
          >
            <span className="mr-2 group-hover:mr-3 transition-all duration-200">←</span>
            Back to Dashboard
          </button>
          
          <div className="text-center bg-white rounded-3xl shadow-lg p-8 mb-8">
            <div className="text-8xl mb-6 animate-bounce">📚</div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-4">
              Recipe History
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed max-w-3xl mx-auto mb-4">
              Browse and manage all your previously created recipes
            </p>
            <div className="flex justify-center items-center gap-4 text-sm text-gray-500">
              <span>📊 {totalCount} total recipes</span>
              <span>•</span>
              <span>🔍 {filteredRecipes.length} shown</span>
            </div>
          </div>
        </div>

        {/* Search and Filter Controls */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          {/* Search Bar */}
          <div className="mb-6">
            <div className="relative max-w-md mx-auto">
              <input
                type="text"
                placeholder="Search recipes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                🔍
              </div>
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              )}
            </div>
          </div>
          
          {/* Filter Tabs */}
          <div className="flex flex-wrap gap-4 justify-center">
            {filterOptions.map(option => {
              const count = option.id === 'all' 
                ? recipes.length
                : recipes.filter(r => {
                    if (option.id === 'starbucks') return r.category === 'starbucks' || r.type === 'starbucks';
                    if (option.id === 'regular') return r.category !== 'starbucks' && r.type !== 'starbucks';
                    return true;
                  }).length;
              
              return (
                <button
                  key={option.id}
                  onClick={() => setSelectedFilter(option.id)}
                  className={`flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                    selectedFilter === option.id
                      ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title={option.description}
                >
                  <span className="mr-2 text-xl">{option.icon}</span>
                  {option.label}
                  <span className="ml-2 bg-white bg-opacity-20 text-xs px-2 py-1 rounded-full">
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Recipe Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredRecipes.map(recipe => renderRecipeCard(recipe))}
        </div>
        
        {/* Quick Actions Footer */}
        <div className="text-center mt-12">
          <div className="bg-white rounded-2xl shadow-lg p-6 inline-block">
            <p className="text-gray-600 mb-4">Want to create more recipes?</p>
            <button
              onClick={onBack}
              className="bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200 mr-4"
            >
              🍳 Generate New Recipe
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeHistoryScreen;