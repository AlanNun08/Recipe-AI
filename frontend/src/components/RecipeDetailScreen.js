import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RecipeDetailScreen = ({ recipeId, onBack, showNotification }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  const [recipe, setRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!recipeId) {
      setIsLoading(false);
      return;
    }
    loadRecipeDetail();
  }, [recipeId]);

  const loadRecipeDetail = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/api/weekly-recipes/recipe/${recipeId}`);
      setRecipe(response.data);
    } catch (error) {
      console.error('Failed to load recipe detail:', error);
      showNotification('❌ Failed to load recipe details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-100 via-blue-100 to-purple-100 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">🍳</div>
          <div className="text-xl text-gray-600">Loading recipe details...</div>
          <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mt-4"></div>
        </div>
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-100 via-orange-100 to-yellow-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 text-center">
          <div className="text-6xl mb-4">😞</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Recipe Not Found</h2>
          <p className="text-gray-600 mb-6">This recipe is no longer available or may have been removed.</p>
          <button
            onClick={onBack}
            className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-xl hover:shadow-lg transition-all"
          >
            ← Back to Weekly Plan
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-100 via-blue-100 to-purple-100 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="bg-white rounded-3xl shadow-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
            >
              <span className="text-2xl mr-2">←</span>
              Back to Weekly Plan
            </button>
            
            <div className="text-right">
              <div className="text-sm text-gray-500">Week of {recipe.week_of}</div>
              <div className="text-lg font-semibold text-purple-600">{recipe.day}</div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-5xl mb-3 animate-bounce">🍽️</div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              {recipe.name}
            </h1>
            <p className="text-gray-600 text-lg mt-2">{recipe.description}</p>
          </div>
        </div>

        {/* Recipe Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          
          {/* Recipe Info Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
              <span className="text-3xl mr-3">⏱️</span>
              Recipe Info
            </h2>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="font-medium text-gray-700">Prep Time:</span>
                <span className="text-green-600 font-semibold">{recipe.prep_time} minutes</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="font-medium text-gray-700">Cook Time:</span>
                <span className="text-green-600 font-semibold">{recipe.cook_time} minutes</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="font-medium text-gray-700">Servings:</span>
                <span className="text-green-600 font-semibold">{recipe.servings} people</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-gray-100">
                <span className="font-medium text-gray-700">Cuisine:</span>
                <span className="text-green-600 font-semibold">{recipe.cuisine_type}</span>
              </div>
              {recipe.calories_per_serving && (
                <div className="flex items-center justify-between py-2 border-b border-gray-100">
                  <span className="font-medium text-gray-700">Calories per serving:</span>
                  <span className="text-green-600 font-semibold">{recipe.calories_per_serving} cal</span>
                </div>
              )}
            </div>
            
            {/* Dietary Tags */}
            {recipe.dietary_tags && recipe.dietary_tags.length > 0 && (
              <div className="mt-4">
                <h3 className="font-semibold text-gray-700 mb-2">Dietary Info:</h3>
                <div className="flex flex-wrap gap-2">
                  {recipe.dietary_tags.map((tag, index) => (
                    <span key={index} className="px-3 py-1 bg-green-100 text-green-700 text-sm rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Ingredients Card */}
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
              <span className="text-3xl mr-3">📝</span>
              Ingredients
            </h2>
            
            <ul className="space-y-3">
              {recipe.ingredients.map((ingredient, index) => (
                <li key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-green-500 mr-3 text-lg">•</span>
                  <span className="text-gray-700">{ingredient}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Cooking Instructions */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
            <span className="text-3xl mr-3">🔪</span>
            Cooking Instructions
          </h2>
          
          <ol className="space-y-4">
            {recipe.instructions.map((instruction, index) => (
              <li key={index} className="flex">
                <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full flex items-center justify-center font-bold mr-4 mt-1">
                  {index + 1}
                </div>
                <div className="flex-1 p-3 bg-gray-50 rounded-lg">
                  <p className="text-gray-700 leading-relaxed">{instruction}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        {/* Shopping List */}
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
            <span className="text-3xl mr-3">🛒</span>
            Shopping List
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recipe.walmart_items.map((item, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center mb-3">
                  <img 
                    src={item.image_url} 
                    alt={item.name}
                    className="w-12 h-12 rounded-lg mr-3 bg-gray-100"
                  />
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-800 text-sm leading-tight">{item.name}</h3>
                    <p className="text-gray-500 text-xs">{item.estimated_price}</p>
                  </div>
                </div>
                
                <a
                  href={item.search_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white text-center py-2 px-4 rounded-lg text-sm font-medium hover:from-blue-600 hover:to-blue-700 transition-all"
                >
                  🛒 Buy on Walmart
                </a>
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center">
              <span className="text-2xl mr-3">💡</span>
              <div>
                <div className="font-semibold text-blue-800">Shopping Tip</div>
                <div className="text-blue-600 text-sm">
                  Click individual "Buy on Walmart" buttons to find each ingredient. 
                  You can add items to your cart and checkout all at once!
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecipeDetailScreen;