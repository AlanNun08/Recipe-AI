import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeDetailScreen({ recipeId, onBack, showNotification }) {
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

  const calculateTotalPrice = () => {
    if (!recipe.cart_ingredients) return 0;
    return recipe.cart_ingredients.reduce((total, item) => {
      const product = item.products[0];
      return total + (product.price || 0);
    }, 0);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading recipe details...</p>
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-blue-700 hover:text-blue-800 font-medium mb-4 transition-colors"
          >
            <span className="mr-2">←</span>
            Back to Weekly Plan
          </button>
          
          <div className="text-center">
            <div className="text-8xl mb-4">🍽️</div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">{recipe.name}</h1>
            <div className="flex items-center justify-center space-x-6 text-gray-600">
              <div className="flex items-center">
                <span className="text-xl mr-2">⏱️</span>
                <span>{recipe.prep_time}</span>
              </div>
              <div className="flex items-center">
                <span className="text-xl mr-2">🔥</span>
                <span>{recipe.cook_time}</span>
              </div>
              <div className="flex items-center">
                <span className="text-xl mr-2">👥</span>
                <span>Serves {recipe.servings}</span>
              </div>
              <div className="flex items-center">
                <span className="text-xl mr-2">🏷️</span>
                <span>{recipe.cuisine}</span>
              </div>
              {recipe.calories && (
                <div className="flex items-center">
                  <span className="text-xl mr-2">🔥</span>
                  <span>{recipe.calories} cal</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Recipe Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            {recipe.description && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <span className="mr-2">📝</span>
                  About This Recipe
                </h2>
                <p className="text-gray-700 leading-relaxed text-lg">{recipe.description}</p>
              </div>
            )}

            {/* Ingredients with Buy Buttons */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span className="mr-2">🥕</span>
                Ingredients & Shopping
                <span className="ml-2 text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                  {recipe.ingredients.length} items
                </span>
              </h2>
              
              <div className="space-y-4">
                {recipe.ingredients.map((ingredient, index) => {
                  // Find the corresponding Walmart product for this ingredient
                  const cartItem = recipe.cart_ingredients?.find(item => item.ingredient === ingredient);
                  const product = cartItem?.products[0];
                  
                  return (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div className="flex items-center">
                        <div className="text-2xl mr-3">🛒</div>
                        <div>
                          <p className="font-medium text-gray-800">{ingredient}</p>
                          {product && (
                            <p className="text-sm text-gray-600">
                              {product.name} - ${product.price.toFixed(2)}
                              {product.brand && <span className="text-gray-500"> • {product.brand}</span>}
                              {product.rating > 0 && <span className="text-yellow-500"> • ⭐ {product.rating}</span>}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      {/* Buy on Walmart Button */}
                      {product && product.url && (
                        <button
                          onClick={() => window.open(product.url, '_blank')}
                          className="bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium py-2 px-4 rounded-lg hover:shadow-lg transition-all flex items-center"
                        >
                          <span className="mr-1">🛒</span>
                          Buy on Walmart
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Cooking Instructions */}
            {recipe.instructions && recipe.instructions.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <span className="mr-2">👩‍🍳</span>
                  Cooking Instructions
                </h2>
                <div className="space-y-4">
                  {recipe.instructions.map((instruction, index) => (
                    <div key={index} className="flex items-start">
                      <div className="flex-shrink-0 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold mr-4 mt-1">
                        {index + 1}
                      </div>
                      <div className="flex-grow">
                        <p className="text-gray-800 leading-relaxed">{instruction}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Shopping Summary */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                <span className="mr-2">🛍️</span>
                Shopping Summary
              </h3>
              
              {recipe.cart_ingredients && recipe.cart_ingredients.length > 0 ? (
                <div className="space-y-4">
                  {/* Shopping Summary */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-3">
                      <span className="font-medium text-gray-700">Estimated Total:</span>
                      <span className="text-xl font-bold text-green-600">
                        ${calculateTotalPrice().toFixed(2)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mb-4">
                      {recipe.cart_ingredients.length} ingredients found on Walmart
                    </div>
                    
                    {/* Shop All Button */}
                    {recipe.walmart_cart_url && (
                      <button
                        onClick={() => window.open(recipe.walmart_cart_url, '_blank')}
                        className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center mb-3"
                      >
                        <span className="mr-2">🛒</span>
                        Add All to Walmart Cart
                      </button>
                    )}
                    
                    <div className="text-xs text-gray-500 text-center">
                      Prices are estimates and may vary. You can also buy ingredients individually using the buttons above.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🏪</div>
                  <p className="text-gray-600 mb-4">Shopping options not available for this recipe.</p>
                  <p className="text-sm text-gray-500">You can still save this recipe and shop manually.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeDetailScreen;