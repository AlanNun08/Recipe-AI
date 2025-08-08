import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeDetailScreen({ recipeId, onBack, showNotification }) {
  const [recipe, setRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cartOptions, setCartOptions] = useState(null);
  const [selectedProducts, setSelectedProducts] = useState({});
  const [cartItems, setCartItems] = useState([]);
  const [finalWalmartUrl, setFinalWalmartUrl] = useState('');
  const [loadingCart, setLoadingCart] = useState(false);

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
      
      // Check if this recipe should use V2 cart system
      if (response.data.use_v2_cart && response.data.v2_cart_endpoint) {
        await loadCartOptions(response.data.v2_cart_endpoint);
      }
    } catch (error) {
      console.error('Failed to load recipe detail:', error);
      showNotification('❌ Failed to load recipe details', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCartOptions = async (cartEndpoint) => {
    setLoadingCart(true);
    try {
      // Extract recipe ID from current recipe or endpoint
      const response = await axios.post(`${API}${cartEndpoint}`);
      setCartOptions(response.data);
      
      // Initialize default selections (first product for each ingredient)
      const defaultSelections = {};
      const defaultCartItems = [];
      
      response.data.ingredient_matches.forEach(match => {
        if (match.products && match.products.length > 0) {
          const firstProduct = match.products[0];
          defaultSelections[match.ingredient] = firstProduct.id;
          defaultCartItems.push({
            ingredient: match.ingredient,
            product: firstProduct,
            quantity: 1
          });
        }
      });
      
      setSelectedProducts(defaultSelections);
      setCartItems(defaultCartItems);
      generateCartUrl(defaultCartItems);
      
    } catch (error) {
      console.error('Failed to load cart options:', error);
      showNotification('❌ Failed to load shopping options', 'error');
    } finally {
      setLoadingCart(false);
    }
  };

  const handleProductSelection = (ingredient, productId) => {
    const match = cartOptions.ingredient_matches.find(m => m.ingredient === ingredient);
    const selectedProduct = match.products.find(p => p.id === productId);
    
    if (!selectedProduct) return;
    
    // Update selections
    const newSelections = {
      ...selectedProducts,
      [ingredient]: productId
    };
    setSelectedProducts(newSelections);
    
    // Update cart items
    const newCartItems = cartItems.map(item => {
      if (item.ingredient === ingredient) {
        return {
          ...item,
          product: selectedProduct
        };
      }
      return item;
    }).filter(item => newSelections[item.ingredient]); // Remove unselected items
    
    // Add new item if ingredient wasn't in cart before
    if (!cartItems.some(item => item.ingredient === ingredient)) {
      newCartItems.push({
        ingredient,
        product: selectedProduct,
        quantity: 1
      });
    }
    
    setCartItems(newCartItems);
    generateCartUrl(newCartItems);
  };

  const handleIngredientToggle = (ingredient, include) => {
    if (include) {
      // Add ingredient back to cart with first available product
      const match = cartOptions.ingredient_matches.find(m => m.ingredient === ingredient);
      if (match && match.products.length > 0) {
        const firstProduct = match.products[0];
        const newSelections = {
          ...selectedProducts,
          [ingredient]: firstProduct.id
        };
        setSelectedProducts(newSelections);
        
        const newCartItems = [...cartItems, {
          ingredient,
          product: firstProduct,
          quantity: 1
        }];
        setCartItems(newCartItems);
        generateCartUrl(newCartItems);
      }
    } else {
      // Remove ingredient from cart
      const newSelections = { ...selectedProducts };
      delete newSelections[ingredient];
      setSelectedProducts(newSelections);
      
      const newCartItems = cartItems.filter(item => item.ingredient !== ingredient);
      setCartItems(newCartItems);
      generateCartUrl(newCartItems);
    }
  };

  const generateCartUrl = async (items) => {
    try {
      const selectedProductsData = items.map(item => ({
        id: item.product.id,
        name: item.product.name,
        price: item.product.price,
        quantity: item.quantity
      }));
      
      const response = await axios.post(`${API}/api/v2/walmart/generate-cart-url`, {
        selected_products: selectedProductsData
      });
      
      setFinalWalmartUrl(response.data.cart_url);
    } catch (error) {
      console.error('Failed to generate cart URL:', error);
    }
  };

  const calculateTotal = () => {
    return cartItems.reduce((total, item) => total + (item.product.price * item.quantity), 0);
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

            {/* Ingredients */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                <span className="mr-2">🥕</span>
                Ingredients
                <span className="ml-2 text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-full">
                  {recipe.ingredients.length} items
                </span>
              </h2>
              
              <div className="grid md:grid-cols-2 gap-4">
                {recipe.ingredients.map((ingredient, index) => (
                  <div key={index} className="flex items-center p-4 bg-gray-50 rounded-xl">
                    <div className="text-2xl mr-3">🛒</div>
                    <div>
                      <p className="font-medium text-gray-800">{ingredient}</p>
                    </div>
                  </div>
                ))}
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

          {/* Right Column - V2 Shopping Cart */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                <span className="mr-2">🛍️</span>
                Smart Shopping Cart
              </h3>
              
              {loadingCart ? (
                <div className="text-center py-8">
                  <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600">Finding best products...</p>
                </div>
              ) : cartOptions && cartOptions.ingredient_matches.length > 0 ? (
                <div className="space-y-4">
                  {/* Ingredient Selection */}
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {cartOptions.ingredient_matches.map((match, index) => {
                      const isSelected = selectedProducts[match.ingredient];
                      const selectedProduct = isSelected ? match.products.find(p => p.id === isSelected) : null;
                      
                      return (
                        <div key={index} className="border rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={!!isSelected}
                                onChange={(e) => handleIngredientToggle(match.ingredient, e.target.checked)}
                                className="mr-2"
                              />
                              <span className="font-medium text-gray-800 text-sm">{match.ingredient}</span>
                            </div>
                            <span className="text-xs text-gray-500">{match.products.length} options</span>
                          </div>
                          
                          {isSelected && (
                            <select
                              value={selectedProducts[match.ingredient] || ''}
                              onChange={(e) => handleProductSelection(match.ingredient, e.target.value)}
                              className="w-full text-xs border rounded px-2 py-1 bg-white"
                            >
                              {match.products.map(product => (
                                <option key={product.id} value={product.id}>
                                  {product.name} - ${product.price}
                                </option>
                              ))}
                            </select>
                          )}
                          
                          {selectedProduct && (
                            <div className="mt-2 text-xs text-gray-600">
                              Selected: ${selectedProduct.price} • {selectedProduct.brand}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Cart Summary */}
                  <div className="border-t pt-4">
                    <div className="flex justify-between items-center font-bold text-lg mb-3">
                      <span>Total ({cartItems.length} items):</span>
                      <span className="text-green-600">${calculateTotal().toFixed(2)}</span>
                    </div>

                    {/* Shop Button */}
                    {finalWalmartUrl && cartItems.length > 0 && (
                      <button
                        onClick={() => window.open(finalWalmartUrl, '_blank')}
                        className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center"
                      >
                        <span className="mr-2">🛒</span>
                        Shop Selected Items on Walmart
                      </button>
                    )}
                    
                    {cartItems.length === 0 && (
                      <div className="text-center py-4 text-gray-500">
                        Select ingredients to add them to your cart
                      </div>
                    )}
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