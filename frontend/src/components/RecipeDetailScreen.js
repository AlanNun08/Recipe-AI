import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeDetailScreen({ recipeId, onBack, showNotification }) {
  const [recipe, setRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cartOptions, setCartOptions] = useState(null);
  const [isLoadingCart, setIsLoadingCart] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState({});
  const [cartUrl, setCartUrl] = useState('');
  const [isGeneratingCart, setIsGeneratingCart] = useState(false);

  useEffect(() => {
    if (!recipeId) {
      setIsLoading(false);
      return;
    }
    
    const loadRecipeDetail = async () => {
      setIsLoading(true);
      try {
        console.log('🔍 Loading recipe detail for ID:', recipeId);
        console.log('🔍 API URL:', `${API}/api/weekly-recipes/recipe/${recipeId}`);
        
        // Use native fetch instead of axios
        const response = await fetch(`${API}/api/weekly-recipes/recipe/${recipeId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Recipe loaded:', data);
        
        setRecipe(data);
        
        // Load cart options in the background (non-blocking) 
        setTimeout(() => {
          loadCartOptions();
        }, 500);
        
      } catch (error) {
        console.error('❌ Failed to load recipe detail:', error);
        console.error('❌ Error details:', error.message);
        showNotification('❌ Failed to load recipe details', 'error');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadRecipeDetail();
  }, [recipeId]);

  const loadCartOptions = async () => {
    setIsLoadingCart(true);
    try {
      console.log('🔍 Loading cart options for weekly recipe:', recipeId);
      
      // Use native fetch instead of axios for V2 endpoint
      const response = await fetch(`${API}/api/v2/walmart/weekly-cart-options?recipe_id=${recipeId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('✅ Cart options loaded:', data);
      
      setCartOptions(data);
      
      // Initialize selected products with first product for each ingredient
      const initialSelections = {};
      data.ingredient_matches?.forEach(ingredientMatch => {
        if (ingredientMatch.products && ingredientMatch.products.length > 0) {
          // Use 'id' field instead of 'product_id' for WalmartProductV2
          initialSelections[ingredientMatch.ingredient] = ingredientMatch.products[0];
        }
      });
      setSelectedProducts(initialSelections);
      
      console.log('✅ Selected products initialized:', initialSelections);
      showNotification('✅ Found real Walmart products!', 'success');
    } catch (error) {
      console.error('❌ Failed to load cart options:', error);
      console.log('⚠️ Will show basic ingredients instead of Walmart products');
      // Don't show error notification - just continue without cart options
      // showNotification('⚠️ Using recipe ingredients without Walmart integration', 'warning');
    } finally {
      setIsLoadingCart(false);
    }
  };

  const handleProductSelection = (ingredientName, product) => {
    setSelectedProducts(prev => ({
      ...prev,
      [ingredientName]: product
    }));
  };

  const generateCartUrl = async () => {
    setIsGeneratingCart(true);
    try {
      const products = Object.values(selectedProducts).map(product => ({
        ingredient_name: product.ingredient || 'Unknown',
        product_id: product.id, // Use 'id' field from WalmartProductV2
        name: product.name,
        price: product.price,
        quantity: 1
      }));

      console.log('🔍 Generating cart URL with products:', products);

      const response = await fetch(`${API}/api/grocery/generate-cart-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          products: products
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Cart URL generated:', data);

      setCartUrl(data.cart_url);
      showNotification(`🛒 Cart created with ${data.total_items} items! Total: $${data.total_price}`, 'success');
    } catch (error) {
      console.error('❌ Failed to generate cart URL:', error);
      console.log('Request failed with:', error.message);
      showNotification('❌ Failed to create cart URL. Please try again.', 'error');
    } finally {
      setIsGeneratingCart(false);
    }
  };

  const calculateSelectedTotal = () => {
    return Object.values(selectedProducts).reduce((total, product) => {
      return total + (product.price || 0);
    }, 0);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading recipe and Walmart products...</p>
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
            <div className="flex items-center justify-center space-x-6 text-gray-600 flex-wrap">
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

            {/* Interactive Walmart Shopping */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span className="mr-2">🛒</span>
                Smart Shopping with Real Walmart Products
                {isLoadingCart && (
                  <div className="ml-3 w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                )}
              </h2>
              
              {cartOptions?.ingredient_matches ? (
                <div className="space-y-6">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div className="flex items-center">
                      <span className="text-green-600 text-xl mr-2">✅</span>
                      <span className="text-green-800 font-medium">
                        Found {cartOptions.ingredient_matches.length} ingredients with real Walmart products!
                      </span>
                    </div>
                  </div>

                  {cartOptions.ingredient_matches.map((ingredientMatch, index) => (
                    <div key={index} className="border border-gray-200 rounded-xl p-5 bg-gray-50">
                      <div className="flex items-center mb-4">
                        <div className="text-2xl mr-3">🥕</div>
                        <h3 className="text-lg font-bold text-gray-800">{ingredientMatch.ingredient}</h3>
                        <span className="ml-auto text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                          {ingredientMatch.products.length} options available
                        </span>
                      </div>
                      
                      <div className="grid gap-3">
                        {ingredientMatch.products.map((product, productIndex) => {
                          const isSelected = selectedProducts[ingredientMatch.ingredient]?.id === product.id;
                          return (
                            <div
                              key={productIndex}
                              onClick={() => handleProductSelection(ingredientMatch.ingredient, product)}
                              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                                isSelected 
                                  ? 'border-blue-500 bg-blue-50 shadow-md' 
                                  : 'border-gray-200 bg-white hover:border-gray-300'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <h4 className="font-semibold text-gray-800 mb-1">{product.name}</h4>
                                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                                    <span className="font-medium">${product.price.toFixed(2)}</span>
                                    <span>{product.brand}</span>
                                    {product.rating && product.rating > 0 && (
                                      <div className="flex items-center">
                                        <span className="text-yellow-500">⭐</span>
                                        <span className="ml-1">{product.rating}</span>
                                      </div>
                                    )}
                                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                                      ID: {product.id}
                                    </span>
                                  </div>
                                </div>
                                <div className={`w-5 h-5 rounded-full border-2 flex-shrink-0 ${
                                  isSelected ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
                                }`}>
                                  {isSelected && (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <div className="w-2 h-2 bg-white rounded-full"></div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">📋</div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Basic Ingredients List</h3>
                  <div className="grid md:grid-cols-2 gap-4 mt-6">
                    {recipe.ingredients.map((ingredient, index) => (
                      <div key={index} className="flex items-center p-4 bg-gray-50 rounded-xl">
                        <div className="text-2xl mr-3">📝</div>
                        <span className="font-medium text-gray-800">{ingredient}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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

          {/* Right Column - Smart Shopping Cart */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                <span className="mr-2">🛍️</span>
                Smart Walmart Cart
              </h3>
              
              {cartOptions?.ingredient_matches ? (
                <div className="space-y-4">
                  {/* Selected Products Summary */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-bold text-gray-800 mb-3">Selected Products:</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {Object.entries(selectedProducts).map(([ingredient, product]) => (
                        <div key={ingredient} className="flex justify-between items-center text-sm">
                          <span className="text-gray-700 truncate flex-1 mr-2">{product.name}</span>
                          <span className="font-semibold text-green-600">${product.price.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Cart Summary */}
                  <div className="border-t pt-4">
                    <div className="flex justify-between items-center font-bold text-lg mb-4">
                      <span>Total ({Object.keys(selectedProducts).length} items):</span>
                      <span className="text-2xl text-green-600">${calculateSelectedTotal().toFixed(2)}</span>
                    </div>

                    {/* Generate Cart Button */}
                    <button
                      onClick={generateCartUrl}
                      disabled={isGeneratingCart || Object.keys(selectedProducts).length === 0}
                      className={`w-full font-bold py-4 px-4 rounded-xl transition-all duration-300 flex items-center justify-center mb-4 ${
                        isGeneratingCart || Object.keys(selectedProducts).length === 0
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-gradient-to-r from-green-500 to-green-600 text-white hover:shadow-lg transform hover:-translate-y-1'
                      }`}
                    >
                      {isGeneratingCart ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                          Creating Cart...
                        </>
                      ) : (
                        <>
                          <span className="mr-2">🛒</span>
                          Add All to Walmart Cart
                        </>
                      )}
                    </button>

                    {/* Cart URL Display */}
                    {cartUrl && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p className="text-sm font-medium text-green-800 mb-2">
                          ✅ Cart created successfully!
                        </p>
                        <button
                          onClick={() => window.open(cartUrl, '_blank')}
                          className="w-full bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 transition-colors"
                        >
                          🛒 Open Walmart Cart
                        </button>
                        <p className="text-xs text-green-700 mt-2 break-all">
                          {cartUrl}
                        </p>
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500 text-center mt-3">
                      Prices are current Walmart prices. Final prices may vary at checkout.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-4xl mb-4">🏪</div>
                  <p className="text-gray-600 mb-4">Smart shopping not available for this recipe.</p>
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