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
    console.log('🔍 useEffect triggered with recipeId:', recipeId);
    
    if (!recipeId) {
      console.log('⚠️ No recipeId provided, setting loading to false');
      setIsLoading(false);
      return;
    }
    
    const loadRecipeDetail = async () => {
      console.log('🔍 Starting loadRecipeDetail...');
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
        console.log('✅ Recipe loaded successfully:', data);
        
        console.log('🔍 About to set recipe data and disable loading...');
        setRecipe(data);
        setIsLoading(false);
        console.log('✅ Recipe state set and loading disabled');
        
        // Load cart options in the background (non-blocking) 
        console.log('🔍 Starting cart options loading in 2 seconds...');
        setTimeout(() => {
          loadCartOptions(recipeId);
        }, 2000);
        
      } catch (error) {
        console.error('❌ Failed to load recipe detail:', error);
        showNotification('❌ Failed to load recipe details', 'error');
        setIsLoading(false);
      }
    };
    
    loadRecipeDetail();
  }, [recipeId]);

  const loadCartOptions = async (currentRecipeId) => {
    console.log('🔍 Starting loadCartOptions for recipe:', currentRecipeId);
    setIsLoadingCart(true);
    
    try {
      console.log('🔍 Loading cart options for weekly recipe:', currentRecipeId);
      console.log('🔍 API URL:', `${API}/api/v2/walmart/weekly-cart-options?recipe_id=${currentRecipeId}`);
      console.log('⏰ This may take 8-10 seconds - fetching real Walmart products...');
      
      // Add longer timeout for slow Walmart API (backend takes ~8 seconds)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 25000); // 25 second timeout
      
      // Use native fetch instead of axios for V2 endpoint
      const response = await fetch(`${API}/api/v2/walmart/weekly-cart-options?recipe_id=${currentRecipeId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      console.log('📥 Cart options response status:', response.status);
      console.log('📥 Cart options response ok:', response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log('❌ Cart options error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('✅ Cart options loaded successfully:', data);
      console.log(`📊 Found ${data.total_products} total products across ${data.ingredient_matches?.length} ingredients`);
      
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
      showNotification(`✅ Found ${data.total_products} real Walmart products!`, 'success');
      
    } catch (error) {
      console.error('❌ Failed to load cart options:', error);
      console.error('❌ Error name:', error.name);
      console.error('❌ Error message:', error.message);
      if (error.name === 'AbortError') {
        console.log('⚠️ Request timed out after 25 seconds');
        showNotification('⚠️ Walmart product search is taking longer than expected. Showing basic ingredients.', 'warning');
      } else {
        console.log('⚠️ Error loading Walmart products, showing basic ingredients instead');
        showNotification('⚠️ Could not load Walmart products. Showing basic ingredients.', 'warning');  
      }
    } finally {
      setIsLoadingCart(false);
    }
  };

  // Remove the external loadCartOptions function since it's now inline
  
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
        id: product.id, // Use 'id' field from WalmartProductV2 (correct field name)
        product_id: product.id, // Keep for backward compatibility 
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
        const errorText = await response.text();
        console.error('❌ Cart URL generation failed:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Cart URL generated:', data);

      if (data.success && data.cart_url) {
        setCartUrl(data.cart_url);
        showNotification(`🛒 Cart created with ${data.total_items || data.product_count} items! Total: $${data.total_price}`, 'success');
      } else {
        throw new Error('Cart URL generation failed');
      }
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Enhanced Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="group flex items-center text-blue-700 hover:text-blue-800 font-medium mb-6 transition-all duration-200 hover:transform hover:-translate-x-1"
          >
            <span className="mr-2 group-hover:mr-3 transition-all duration-200">←</span>
            Back to Weekly Plan
          </button>
          
          <div className="text-center bg-white rounded-3xl shadow-lg p-8 mb-8">
            <div className="text-8xl mb-6 animate-bounce">🍽️</div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
              {recipe.name}
            </h1>
            {recipe.description && (
              <p className="text-xl text-gray-600 leading-relaxed max-w-3xl mx-auto mb-6">
                {recipe.description}
              </p>
            )}
            
            {/* Enhanced Recipe Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 max-w-4xl mx-auto">
              <div className="bg-gradient-to-br from-orange-100 to-orange-200 rounded-2xl p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="text-3xl mb-2">⏱️</div>
                <div className="text-sm text-gray-600 font-medium">Prep Time</div>
                <div className="font-bold text-gray-800">{recipe.prep_time}</div>
              </div>
              <div className="bg-gradient-to-br from-red-100 to-red-200 rounded-2xl p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="text-3xl mb-2">🔥</div>
                <div className="text-sm text-gray-600 font-medium">Cook Time</div>
                <div className="font-bold text-gray-800">{recipe.cook_time}</div>
              </div>
              <div className="bg-gradient-to-br from-green-100 to-green-200 rounded-2xl p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="text-3xl mb-2">👥</div>
                <div className="text-sm text-gray-600 font-medium">Servings</div>
                <div className="font-bold text-gray-800">{recipe.servings}</div>
              </div>
              <div className="bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                <div className="text-3xl mb-2">🏷️</div>
                <div className="text-sm text-gray-600 font-medium">Cuisine</div>
                <div className="font-bold text-gray-800">{recipe.cuisine}</div>
              </div>
              {recipe.calories && (
                <div className="bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-2xl p-4 text-center shadow-sm hover:shadow-md transition-shadow">
                  <div className="text-3xl mb-2">⚡</div>
                  <div className="text-sm text-gray-600 font-medium">Calories</div>
                  <div className="font-bold text-gray-800">{recipe.calories}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left Column - Recipe Details */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Enhanced Walmart Shopping Section */}
            <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent flex items-center">
                  <span className="mr-3 text-4xl">🛒</span>
                  Smart Walmart Shopping
                </h2>
                {isLoadingCart && (
                  <div className="flex items-center bg-blue-50 rounded-full px-4 py-2">
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-3"></div>
                    <span className="text-sm text-blue-700 font-medium">Finding best prices...</span>
                  </div>
                )}
              </div>
              
              {cartOptions?.ingredient_matches ? (
                <div className="space-y-8">
                  <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6">
                    <div className="flex items-center">
                      <div className="bg-green-500 rounded-full p-2 mr-4">
                        <span className="text-white text-2xl">✨</span>
                      </div>
                      <div>
                        <div className="font-bold text-green-800 text-lg">
                          Found {cartOptions.ingredient_matches.length} ingredients with real Walmart products!
                        </div>
                        <div className="text-green-700 text-sm">
                          {cartOptions.total_products} products available • Real-time pricing
                        </div>
                      </div>
                    </div>
                  </div>

                  {cartOptions.ingredient_matches.map((ingredientMatch, index) => (
                    <div key={index} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-3xl p-8 border border-gray-200 shadow-sm hover:shadow-md transition-all duration-300">
                      <div className="flex items-center mb-6">
                        <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-full p-3 mr-4">
                          <span className="text-white text-2xl">🥕</span>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-2xl font-bold text-gray-800 mb-1">{ingredientMatch.ingredient}</h3>
                          <div className="flex items-center space-x-2">
                            <span className="bg-blue-100 text-blue-700 text-sm font-medium px-3 py-1 rounded-full">
                              {ingredientMatch.products.length} options
                            </span>
                            <span className="bg-green-100 text-green-700 text-sm font-medium px-3 py-1 rounded-full">
                              Best price: ${Math.min(...ingredientMatch.products.map(p => p.price)).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="grid gap-4">
                        {ingredientMatch.products.map((product, productIndex) => {
                          const isSelected = selectedProducts[ingredientMatch.ingredient]?.id === product.id;
                          const isLowestPrice = product.price === Math.min(...ingredientMatch.products.map(p => p.price));
                          
                          return (
                            <div
                              key={productIndex}
                              onClick={() => handleProductSelection(ingredientMatch.ingredient, product)}
                              className={`relative p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 transform hover:scale-[1.02] ${
                                isSelected 
                                  ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-blue-100 shadow-lg' 
                                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-md'
                              }`}
                            >
                              {isLowestPrice && !isSelected && (
                                <div className="absolute -top-2 -right-2 bg-gradient-to-r from-orange-400 to-red-400 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg">
                                  Best Price!
                                </div>
                              )}
                              
                              <div className="flex items-center justify-between">
                                <div className="flex-1 mr-4">
                                  <h4 className="font-bold text-gray-800 mb-2 text-lg leading-tight">{product.name}</h4>
                                  <div className="flex items-center flex-wrap gap-3 text-sm">
                                    <span className="bg-gradient-to-r from-green-500 to-green-600 text-white font-bold px-3 py-1 rounded-full text-lg">
                                      ${product.price.toFixed(2)}
                                    </span>
                                    <span className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full font-medium">
                                      {product.brand}
                                    </span>
                                    {product.rating && product.rating > 0 && (
                                      <div className="flex items-center bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full">
                                        <span className="text-yellow-500 mr-1">⭐</span>
                                        <span className="font-medium">{product.rating}</span>
                                      </div>
                                    )}
                                    <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded font-mono">
                                      ID: {product.id}
                                    </span>
                                  </div>
                                </div>
                                
                                <div className={`w-8 h-8 rounded-full border-2 flex-shrink-0 transition-all duration-300 ${
                                  isSelected 
                                    ? 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-500 shadow-lg' 
                                    : 'border-gray-300 hover:border-gray-400'
                                }`}>
                                  {isSelected && (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <span className="text-white text-lg">✓</span>
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
                <div className="text-center py-12">
                  <div className="text-6xl mb-6">📋</div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-4">Basic Ingredients List</h3>
                  <p className="text-gray-600 mb-8 max-w-md mx-auto">
                    Smart shopping not available for this recipe. Here's the basic ingredient list:
                  </p>
                  <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl p-6 text-left max-w-2xl mx-auto">
                    <div className="grid gap-3">
                      {recipe.ingredients?.map((ingredient, index) => (
                        <div key={index} className="flex items-center p-3 bg-white rounded-lg border border-gray-200">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                            <span className="text-blue-600 font-bold text-sm">{index + 1}</span>
                          </div>
                          <span className="text-gray-800 font-medium">{ingredient}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Enhanced Instructions Section */}
            {recipe.instructions && recipe.instructions.length > 0 && (
              <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-8 flex items-center">
                  <span className="mr-3 text-4xl">👩‍🍳</span>
                  Cooking Instructions
                </h2>
                <div className="space-y-6">
                  {recipe.instructions.map((instruction, index) => (
                    <div key={index} className="group flex items-start hover:bg-gray-50 rounded-2xl p-6 transition-colors duration-200">
                      <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-2xl flex items-center justify-center font-bold mr-6 mt-1 shadow-lg group-hover:scale-110 transition-transform duration-200">
                        {index + 1}
                      </div>
                      <div className="flex-grow">
                        <p className="text-gray-800 leading-relaxed text-lg font-medium">{instruction}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Enhanced Right Column - Smart Shopping Cart */}
          <div className="space-y-8">
            <div className="bg-white rounded-3xl shadow-xl p-8 sticky top-6 border border-gray-100">
              <div className="text-center mb-6">
                <h3 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-2 flex items-center justify-center">
                  <span className="mr-3 text-4xl">🛍️</span>
                  Smart Walmart Cart
                </h3>
                <p className="text-gray-600 text-sm">Real-time pricing • One-click shopping</p>
              </div>
              
              {cartOptions?.ingredient_matches ? (
                <div className="space-y-6">
                  {/* Enhanced Selected Products Summary */}
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
                    <div className="flex items-center mb-4">
                      <div className="bg-blue-500 rounded-full p-2 mr-3">
                        <span className="text-white text-lg">🛒</span>
                      </div>
                      <h4 className="font-bold text-gray-800 text-lg">Selected Products</h4>
                    </div>
                    <div className="space-y-3 max-h-48 overflow-y-auto">
                      {Object.entries(selectedProducts).map(([ingredient, product]) => (
                        <div key={ingredient} className="flex justify-between items-center bg-white rounded-lg p-3 shadow-sm">
                          <div className="flex-1 mr-3">
                            <div className="font-medium text-gray-800 text-sm leading-tight mb-1">{product.name}</div>
                            <div className="text-xs text-gray-500">{product.brand}</div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold text-green-600 text-lg">${product.price.toFixed(2)}</div>
                            {product.rating && (
                              <div className="text-xs text-yellow-600">⭐ {product.rating}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Enhanced Cart Summary */}
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-100">
                    <div className="text-center mb-6">
                      <div className="text-sm text-gray-600 mb-2">Cart Total</div>
                      <div className="text-4xl font-bold text-green-600 mb-2">${calculateSelectedTotal().toFixed(2)}</div>
                      <div className="text-sm text-gray-600">
                        {Object.keys(selectedProducts).length} items • Ready for checkout
                      </div>
                    </div>

                    {/* Enhanced Generate Cart Button */}
                    <button
                      onClick={generateCartUrl}
                      disabled={isGeneratingCart || Object.keys(selectedProducts).length === 0}
                      className={`w-full font-bold py-4 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center mb-4 text-lg shadow-lg ${
                        isGeneratingCart || Object.keys(selectedProducts).length === 0
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
                          : 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-xl transform hover:-translate-y-1 hover:from-green-600 hover:to-emerald-700'
                      }`}
                    >
                      {isGeneratingCart ? (
                        <>
                          <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                          Creating Your Cart...
                        </>
                      ) : (
                        <>
                          <span className="mr-3 text-2xl">🚀</span>
                          Add All to Walmart Cart
                        </>
                      )}
                    </button>

                    {/* Enhanced Cart URL Display */}
                    {cartUrl && (
                      <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-2xl p-6 shadow-lg">
                        <div className="text-center mb-4">
                          <div className="text-3xl mb-2">🎉</div>
                          <div className="font-bold text-xl mb-2">Cart Ready!</div>
                          <p className="text-green-100 text-sm">Your Walmart cart has been created with all selected items</p>
                        </div>
                        <button
                          onClick={() => window.open(cartUrl, '_blank')}
                          className="w-full bg-white text-green-600 font-bold py-4 px-6 rounded-xl hover:bg-green-50 transition-all duration-300 flex items-center justify-center text-lg shadow-md hover:shadow-lg"
                        >
                          <span className="mr-3 text-2xl">🛒</span>
                          Open Walmart Cart
                        </button>
                        <div className="mt-4 p-3 bg-green-600 bg-opacity-20 rounded-lg">
                          <p className="text-xs text-green-100 break-all font-mono leading-relaxed">
                            {cartUrl}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    <div className="text-center mt-4">
                      <div className="text-xs text-gray-500 leading-relaxed">
                        💡 Prices are current Walmart prices<br/>
                        Final prices may vary at checkout
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-6">🏪</div>
                  <h4 className="text-xl font-bold text-gray-800 mb-4">Smart Shopping Unavailable</h4>
                  <p className="text-gray-600 mb-6 leading-relaxed">
                    Smart shopping with real Walmart products isn't available for this recipe yet.
                  </p>
                  <p className="text-sm text-gray-500">
                    You can still save this recipe and shop manually using the ingredient list above.
                  </p>
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