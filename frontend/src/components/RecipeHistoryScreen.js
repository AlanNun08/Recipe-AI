import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeHistoryScreen({ user, onBack, showNotification, onViewRecipe, onViewStarbucksRecipe }) {
  const [recipes, setRecipes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const filterOptions = [
    { id: 'all', label: 'All Recipes', icon: '🍽️' },
    { id: 'cuisine', label: 'Regular Recipes', icon: '🍳' },
    { id: 'starbucks', label: 'Starbucks Drinks', icon: '☕' }
  ];

  useEffect(() => {
    loadRecipeHistory();
  }, []);

  const loadRecipeHistory = async () => {
    try {
      console.log('🔍 Loading recipe history for user:', user.id);
      
      const response = await axios.get(`${API}/api/recipes/history/${user.id}`);
      console.log('✅ Recipe history response:', response.data);
      
      // Extract recipes array from response
      const recipesData = response.data.recipes || response.data || [];
      console.log('✅ Setting recipes array:', recipesData.length, 'recipes');
      
      setRecipes(recipesData);
    } catch (error) {
      console.error('❌ Error loading recipe history:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to load recipe history';
      showNotification(`❌ ${errorMessage}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredRecipes = recipes.filter(recipe => {
    if (filter === 'all') return true;
    return recipe.category === filter;
  });

  const handleViewRecipe = (recipe) => {
    if (recipe.category === 'starbucks' || recipe.type === 'starbucks') {
      // Navigate to Starbucks generator screen for Starbucks recipes
      if (onViewStarbucksRecipe) {
        onViewStarbucksRecipe(recipe);
      } else {
        showNotification('🌟 Opening Starbucks recipe in generator...', 'info');
        // Fallback: navigate to starbucks screen
        window.location.hash = 'starbucks-generator';
      }
      return;
    }
    
    // Validate recipe ID before navigation
    if (!recipe.id) {
      console.error('❌ Recipe ID is missing or null:', recipe);
      showNotification('❌ Recipe ID is missing. Cannot open recipe details.', 'error');
      return;
    }
    
    console.log('✅ Calling onViewRecipe with ID:', recipe.id, 'source: history');
    // Use the enhanced RecipeDetailScreen for regular recipes
    onViewRecipe(recipe.id, 'history');
  };

  const deleteRecipe = async (recipeId) => {
    if (!confirm('Are you sure you want to delete this recipe?')) {
      return;
    }

    try {
      await axios.delete(`${API}/api/recipes/${recipeId}`);
      showNotification('Recipe deleted successfully', 'success');
      loadRecipeHistory(); // Reload the list
    } catch (error) {
      console.error('❌ Error deleting recipe:', error);
      showNotification('Failed to delete recipe', 'error');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-indigo-50 to-blue-50 flex items-center justify-center">
        <div className="bg-white rounded-3xl shadow-lg p-8 text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Recipe History</h2>
          <p className="text-gray-600">Fetching your saved recipes...</p>
        </div>
      </div>
    );
  }

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
              Browse and manage all your previously generated recipes
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex flex-wrap gap-4 justify-center">
            {filterOptions.map(option => (
              <button
                key={option.id}
                onClick={() => setFilter(option.id)}
                className={`flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
                  filter === option.id
                    ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span className="mr-2 text-xl">{option.icon}</span>
                {option.label}
                <span className="ml-2 bg-white bg-opacity-20 text-xs px-2 py-1 rounded-full">
                  {filteredRecipes.length}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Recipe Grid */}
        {filteredRecipes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredRecipes.map((recipe) => (
              <div key={recipe.id} className="bg-white rounded-3xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
                
                {/* Recipe Header */}
                <div className={`p-6 ${
                  recipe.category === 'cuisine' ? 'bg-gradient-to-r from-orange-500 to-red-500' :
                  recipe.category === 'snacks' ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                  recipe.category === 'beverages' ? 'bg-gradient-to-r from-blue-500 to-cyan-500' :
                  recipe.category === 'starbucks' ? 'bg-gradient-to-r from-green-500 to-teal-500' :
                  'bg-gradient-to-r from-gray-500 to-gray-600'
                } text-white`}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-3xl">{recipe.category_icon}</span>
                    <span className="text-xs bg-white bg-opacity-20 px-3 py-1 rounded-full font-medium">
                      {recipe.category_label}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold leading-tight mb-2">
                    {recipe.type === 'starbucks' ? recipe.drink_name : recipe.title}
                  </h3>
                  <p className="text-sm text-white text-opacity-90">
                    {new Date(recipe.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })}
                  </p>
                </div>

                {/* Recipe Content */}
                <div className="p-6">
                  <p className="text-gray-600 text-sm mb-6 leading-relaxed line-clamp-3">
                    {recipe.description}
                  </p>
                  
                  {/* Recipe Stats */}
                  {recipe.type !== 'starbucks' && (
                    <div className="grid grid-cols-2 gap-4 mb-6">
                      <div className="text-center bg-gray-50 rounded-lg p-3">
                        <div className="text-lg">⏱️</div>
                        <div className="text-xs text-gray-600">Prep Time</div>
                        <div className="font-bold text-sm">{recipe.prep_time || 'N/A'}</div>
                      </div>
                      <div className="text-center bg-gray-50 rounded-lg p-3">
                        <div className="text-lg">👥</div>
                        <div className="text-xs text-gray-600">Servings</div>
                        <div className="font-bold text-sm">{recipe.servings || 'N/A'}</div>
                      </div>
                    </div>
                  )}
                  
                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleViewRecipe(recipe)}
                      className="flex-1 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200 text-sm"
                    >
                      👀 View Details
                    </button>
                    <button
                      onClick={() => deleteRecipe(recipe.id)}
                      className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-4 rounded-xl transition-all duration-200 text-sm"
                      title="Delete Recipe"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <div className="bg-white rounded-3xl shadow-lg p-12 max-w-md mx-auto">
              <div className="text-8xl mb-6">📝</div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">
                {filter === 'all' ? 'No Recipes Yet' : `No ${filterOptions.find(f => f.id === filter)?.label} Found`}
              </h3>
              <p className="text-gray-600 mb-8 leading-relaxed">
                {filter === 'all' 
                  ? "You haven't created any recipes yet. Start generating some delicious recipes!"
                  : `You don't have any ${filterOptions.find(f => f.id === filter)?.label.toLowerCase()} in your history.`
                }
              </p>
              <button
                onClick={() => setFilter('all')}
                className="bg-gradient-to-r from-purple-500 to-blue-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200"
              >
                Show All Recipes
              </button>
            </div>
          </div>
        )}
        
        {/* Quick Actions */}
        {recipes.length > 0 && (
          <div className="text-center mt-12">
            <div className="bg-white rounded-2xl shadow-lg p-6 inline-block">
              <p className="text-gray-600 mb-4">Want to create more recipes?</p>
              <button
                onClick={() => {/* Navigate to recipe generator */}}
                className="bg-gradient-to-r from-orange-500 to-red-500 text-white font-bold py-3 px-6 rounded-xl hover:shadow-lg transition-all duration-200 mr-4"
              >
                🍳 Generate New Recipe
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RecipeHistoryScreen;