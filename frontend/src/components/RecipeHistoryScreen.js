import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeHistoryScreen({ user, onBack, showNotification, onViewRecipe, onViewStarbucksRecipe }) {
  const [recipes, setRecipes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState('all');

  const filterOptions = [
    { id: 'all', label: 'All Recipes', icon: '🍽️' },
    { id: 'regular', label: 'Regular Recipes', icon: '🍳' },
    { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕' }
  ];

  useEffect(() => {
    const fetchRecipes = async () => {
      if (!user?.id) {
        setError('User not found');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API}/api/recipes/history/${user.id}`);
        
        if (!response.ok) {
          throw new Error(`Failed to load: ${response.status}`);
        }

        const data = await response.json();
        setRecipes(data.recipes || []);
        
      } catch (error) {
        setError(error.message);
        showNotification(`Error loading recipes: ${error.message}`, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecipes();
  }, [user?.id]);

  const filteredRecipes = recipes.filter(recipe => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'starbucks') return recipe.category === 'starbucks' || recipe.type === 'starbucks';
    if (selectedFilter === 'regular') return recipe.category !== 'starbucks' && recipe.type !== 'starbucks';
    return true;
  });

  const handleViewRecipe = (recipe) => {
    if (recipe.category === 'starbucks' || recipe.type === 'starbucks') {
      onViewStarbucksRecipe?.(recipe);
    } else {
      onViewRecipe?.(recipe.id, 'history');
    }
  };

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

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">🆕 NEW Recipe History - Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="bg-red-500 text-white px-4 py-2 rounded mr-2"
          >
            Retry
          </button>
          <button 
            onClick={onBack}
            className="bg-gray-500 text-white px-4 py-2 rounded"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <button
          onClick={onBack}
          className="flex items-center text-green-700 hover:text-green-800 font-medium mb-6"
        >
          <span className="mr-2">←</span>
          Back to Dashboard
        </button>
        
        <div className="text-center bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="text-6xl mb-4">🆕</div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-4">
            NEW Recipe History
          </h1>
          <p className="text-lg text-gray-600 mb-4">
            Completely rebuilt from scratch with clean architecture!
          </p>
          <div className="text-sm text-green-600 font-medium">
            📊 Total: {recipes.length} | Shown: {filteredRecipes.length}
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex flex-wrap gap-4 justify-center">
            {filterOptions.map(option => (
              <button
                key={option.id}
                onClick={() => setSelectedFilter(option.id)}
                className={`flex items-center px-4 py-2 rounded-lg font-medium ${
                  selectedFilter === option.id
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="mr-2">{option.icon}</span>
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Recipe Grid */}
        {filteredRecipes.length === 0 ? (
          <div className="text-center py-12">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <div className="text-4xl mb-4">📝</div>
              <h3 className="text-xl font-bold text-gray-800 mb-4">No Recipes Found</h3>
              <p className="text-gray-600">No recipes match your current filter.</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRecipes.map((recipe) => {
              const isStarbucks = recipe.category === 'starbucks' || recipe.type === 'starbucks';
              
              return (
                <div key={recipe.id} className="bg-white rounded-lg shadow-lg overflow-hidden">
                  {/* Header */}
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

                  {/* Content */}
                  <div className="p-4">
                    <p className="text-gray-600 text-sm mb-4">
                      {recipe.description || 'No description available'}
                    </p>
                    
                    {/* Stats */}
                    {!isStarbucks && (
                      <div className="grid grid-cols-2 gap-2 mb-4">
                        <div className="text-center bg-gray-50 rounded p-2">
                          <div className="text-lg">⏱️</div>
                          <div className="text-xs text-gray-600">Prep</div>
                          <div className="font-bold text-xs">{recipe.prep_time || 'N/A'}</div>
                        </div>
                        <div className="text-center bg-gray-50 rounded p-2">
                          <div className="text-lg">👥</div>
                          <div className="text-xs text-gray-600">Serves</div>
                          <div className="font-bold text-xs">{recipe.servings || 'N/A'}</div>
                        </div>
                      </div>
                    )}
                    
                    {/* Actions */}
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewRecipe(recipe)}
                        className="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-3 rounded text-sm"
                      >
                        👀 View
                      </button>
                      <button
                        onClick={() => handleDelete(recipe.id)}
                        className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-3 rounded text-sm"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default RecipeHistoryScreen;