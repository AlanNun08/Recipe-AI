import React, { useState, useEffect, useRef } from 'react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

function RecipeDetailScreenMobile({ recipeId, recipeSource = 'weekly', onBack, showNotification, triggerWalmartFetch }) {
  const [recipe, setRecipe] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [cartOptions, setCartOptions] = useState([]);
  const [isLoadingCart, setIsLoadingCart] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState({});
  const [autoAddedItems, setAutoAddedItems] = useState(new Set());
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ingredients');

  // Use refs to prevent duplicate API calls
  const recipeLoadedRef = useRef(false);
  const cartLoadedRef = useRef(false);

  useEffect(() => {
    const fetchRecipe = async () => {
      if (!recipeId || recipeLoadedRef.current) return;

      try {
        setIsLoading(true);
        recipeLoadedRef.current = true;

        const response = await fetch(`${API}/api/recipes/${recipeId}/detail`);

        if (!response.ok) {
          throw new Error(`Failed to load recipe: ${response.status}`);
        }

        const data = await response.json();
        setRecipe(data);

        if (!cartLoadedRef.current) {
          fetchCartOptions();
        }

      } catch (error) {
        console.error('Error loading recipe:', error);
        setError(error.message);
        showNotification(`Error loading recipe: ${error.message}`, 'error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecipe();
  }, [recipeId]);

  useEffect(() => {
    if (triggerWalmartFetch && recipeId) {
      cartLoadedRef.current = false;
      fetchCartOptions();
    }
  }, [triggerWalmartFetch, recipeId]);

  const fetchCartOptions = async () => {
    if (!recipeId || cartLoadedRef.current) {
      console.log('🛒 Cart fetch early return: recipeId=', recipeId, 'cartLoadedRef.current=', cartLoadedRef.current);
      return;
    }

    try {
      setIsLoadingCart(true);
      cartLoadedRef.current = true;

      console.log('🛒 Loading cart options for:', recipeId);
      const response = await fetch(`${API}/api/recipes/${recipeId}/cart-options`);
      console.log('📊 Cart options response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('📦 Cart options data:', data);
        
        const walmartOption = data.cart_options?.[0];
        
        if (walmartOption && walmartOption.products) {
          console.log('✅ Found Walmart products:', walmartOption.products.length);
          
          const productsByIngredient = {};
          walmartOption.products.forEach(product => {
            const ingredient = product.ingredient_match;
            if (!productsByIngredient[ingredient]) {
              productsByIngredient[ingredient] = [];
            }
            productsByIngredient[ingredient].push(product);
          });
          
          console.log('🛒 Products grouped by ingredient:', Object.keys(productsByIngredient).length, 'ingredients');
          
          setCartOptions([{
            ...walmartOption,
            productsByIngredient: productsByIngredient
          }]);
          
          autoAddBestPriceItemsEnhanced(productsByIngredient);
        } else {
          console.warn('⚠️ No Walmart products found in response, walmartOption=', walmartOption);
          setCartOptions(data.cart_options || []);
        }
      } else {
        console.error('❌ Cart options response not ok:', response.status, response.statusText);
        const errorData = await response.text();
        console.error('❌ Error body:', errorData);
      }
    } catch (error) {
      console.error('❌ Error fetching cart options:', error);
    } finally {
      setIsLoadingCart(false);
    }
  };

  const autoAddBestPriceItemsEnhanced = (productsByIngredient) => {
    const autoSelected = {};
    const autoAdded = new Set();

    Object.entries(productsByIngredient).forEach(([ingredient, products]) => {
      if (products && products.length > 0) {
        const bestProduct = products[0];
        autoSelected[ingredient] = {
          id: bestProduct.itemId,
          name: bestProduct.name,
          price: bestProduct.price,
          brand: bestProduct.brand,
          size: bestProduct.size,
          image: bestProduct.image,
          ingredient: ingredient,
          availability: bestProduct.availability,
          rating: bestProduct.rating,
          reviewCount: bestProduct.reviewCount || 0,
          search_rank: bestProduct.search_rank || 1,
          is_best_price: bestProduct.is_best_price || true,
          isAutoAdded: true
        };
        autoAdded.add(ingredient);
      }
    });

    setSelectedProducts(autoSelected);
    setAutoAddedItems(autoAdded);
    
    if (Object.keys(autoSelected).length > 0) {
      showNotification(`🛒 Auto-added ${Object.keys(autoSelected).length} best-price items to your cart!`, 'success');
    }
  };

  const handleProductSelection = (ingredient, product, optionIndex = 0) => {
    const selectedItem = {
      id: product.itemId,
      name: product.name,
      price: product.price,
      brand: product.brand,
      size: product.size,
      image: product.image,
      ingredient: ingredient,
      availability: product.availability,
      rating: product.rating,
      reviewCount: product.reviewCount || 0,
      optionSelected: optionIndex,
      isAutoAdded: false
    };

    setSelectedProducts(prev => ({
      ...prev,
      [ingredient]: selectedItem
    }));

    setAutoAddedItems(prev => {
      const newSet = new Set(prev);
      newSet.delete(ingredient);
      return newSet;
    });

    showNotification(`✅ Selected ${product.name} for ${ingredient}`, 'success');
  };

  const removeProductFromCart = (ingredient) => {
    setSelectedProducts(prev => {
      const updated = { ...prev };
      delete updated[ingredient];
      return updated;
    });

    setAutoAddedItems(prev => {
      const newSet = new Set(prev);
      newSet.delete(ingredient);
      return newSet;
    });

    showNotification(`❌ Removed item for ${ingredient}`, 'info');
  };

  const toggleItemInCart = (ingredient, enabled) => {
    if (!enabled) {
      removeProductFromCart(ingredient);
    } else {
      const bestProduct = findBestPriceProduct(ingredient);
      if (bestProduct) {
        handleProductSelection(ingredient, bestProduct);
      }
    }
  };

  const findBestPriceProduct = (ingredient) => {
    for (const option of cartOptions) {
      if (option.products) {
        const matchingProducts = option.products.filter(p => p.ingredient_match === ingredient);
        if (matchingProducts.length > 0) {
          return matchingProducts.reduce((best, current) => 
            current.price < best.price ? current : best
          );
        }
      }
    }
    return null;
  };

  const calculateSelectedTotal = () => {
    return Object.values(selectedProducts).reduce((total, product) => {
      return total + (product.price || 0);
    }, 0);
  };

  const getUniqueIngredients = () => {
    const ingredients = new Set();
    cartOptions.forEach(option => {
      if (option.productsByIngredient) {
        Object.keys(option.productsByIngredient).forEach(ingredient => {
          ingredients.add(ingredient);
        });
      } else if (option.products) {
        option.products.forEach(product => {
          if (product.ingredient_match) {
            ingredients.add(product.ingredient_match);
          }
        });
      }
    });
    return Array.from(ingredients);
  };

  const getProductsForIngredient = (ingredient) => {
    const products = [];
    cartOptions.forEach(option => {
      if (option.productsByIngredient && option.productsByIngredient[ingredient]) {
        option.productsByIngredient[ingredient].forEach(product => {
          products.push({
            ...product, 
            storeName: option.store_name,
            search_rank: product.search_rank || 1,
            is_best_price: product.is_best_price || false
          });
        });
      } else if (option.products) {
        option.products.forEach(product => {
          if (product.ingredient_match === ingredient) {
            products.push({
              ...product, 
              storeName: option.store_name,
              search_rank: product.search_rank || 1,
              is_best_price: product.is_best_price || false
            });
          }
        });
      }
    });
    
    return products
      .sort((a, b) => {
        if (a.search_rank !== b.search_rank) {
          return a.search_rank - b.search_rank;
        }
        return a.price - b.price;
      })
      .slice(0, 3);
  };

  const getMissingIngredients = () => {
    const allIngredients = getUniqueIngredients();
    const selectedIngredients = Object.keys(selectedProducts);
    return allIngredients.filter(ing => !selectedIngredients.includes(ing));
  };

  const getCostIndicator = () => {
    const mealType = recipe?.meal_type?.toLowerCase() || '';
    
    if (mealType.includes('breakfast') || mealType.includes('snack') || mealType.includes('appetizer')) {
      return '$';
    } else if (mealType.includes('lunch')) {
      return '$$';
    } else if (mealType.includes('dinner') || mealType.includes('main')) {
      return '$$$';
    } else {
      const servings = recipe?.servings || 1;
      if (servings <= 2) {
        return '$';
      } else if (servings <= 4) {
        return '$$';
      } else {
        return '$$$';
      }
    }
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

  if (error || !recipe) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Recipe Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'Unable to load recipe details.'}</p>
          <button
            onClick={onBack}
            className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors w-full"
          >
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 pb-20">
      {/* Fixed Header */}
      <div className="sticky top-0 z-50 bg-white shadow-md">
        <div className="p-4 flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center text-blue-700 hover:text-blue-800 font-medium"
          >
            <span className="mr-2">←</span>
            Back
          </button>
          <h1 className="text-lg font-bold text-gray-800 flex-1 text-center truncate">{recipe.name}</h1>
          <div className="w-8"></div>
        </div>
      </div>

      {/* Recipe Header */}
      <div className="bg-gradient-to-r from-blue-500 to-green-500 text-white p-6">
        <h1 className="text-2xl font-bold mb-2">{recipe.name}</h1>
        <p className="text-blue-100 text-sm mb-4">{recipe.description}</p>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white bg-opacity-20 rounded p-3">
            <div className="text-2xl">⏱️</div>
            <div className="text-xs text-blue-100 mt-1">Prep</div>
            <div className="font-bold text-sm">{recipe.prep_time}</div>
          </div>
          <div className="bg-white bg-opacity-20 rounded p-3">
            <div className="text-2xl">🔥</div>
            <div className="text-xs text-blue-100 mt-1">Cook</div>
            <div className="font-bold text-sm">{recipe.cook_time}</div>
          </div>
          <div className="bg-white bg-opacity-20 rounded p-3">
            <div className="text-2xl">👥</div>
            <div className="text-xs text-blue-100 mt-1">Serves</div>
            <div className="font-bold text-sm">{recipe.servings}</div>
          </div>
          <div className="bg-white bg-opacity-20 rounded p-3">
            <div className="text-2xl">💰</div>
            <div className="text-xs text-blue-100 mt-1">Cost</div>
            <div className="font-bold text-sm">{getCostIndicator()}</div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mt-4">
          <span className="inline-block bg-white bg-opacity-20 rounded px-3 py-1 text-sm">🍳 {recipe.cuisine_type}</span>
          <span className="inline-block bg-white bg-opacity-20 rounded px-3 py-1 text-sm">🍽️ {recipe.meal_type}</span>
          <span className="inline-block bg-white bg-opacity-20 rounded px-3 py-1 text-sm">⭐ {recipe.difficulty}</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b bg-white sticky top-16 z-40">
        {[
          { id: 'ingredients', label: 'Ingredients', icon: '🛒' },
          { id: 'instructions', label: 'Steps', icon: '📝' },
          { id: 'shopping', label: 'Shop', icon: '🛍️' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-3 py-3 text-center font-medium text-sm ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'ingredients' && (
          <div>
            <h3 className="text-lg font-bold mb-4">🛒 Ingredients ({recipe.ingredients?.length || 0})</h3>
            <div className="space-y-2">
              {recipe.ingredients?.map((ingredient, index) => (
                <div key={index} className="flex items-start bg-white rounded-lg p-3 shadow">
                  <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-3 flex-shrink-0 font-bold">
                    {index + 1}
                  </span>
                  <span className="text-gray-800">{ingredient}</span>
                </div>
              )) || <p className="text-gray-500">No ingredients available</p>}
            </div>
          </div>
        )}

        {activeTab === 'instructions' && (
          <div>
            <h3 className="text-lg font-bold mb-4">📝 Instructions ({recipe.instructions?.length || 0})</h3>
            <div className="space-y-3">
              {recipe.instructions?.map((instruction, index) => (
                <div key={index} className="bg-white rounded-lg p-4 shadow">
                  <div className="flex items-start">
                    <span className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold mr-3 flex-shrink-0">
                      {index + 1}
                    </span>
                    <p className="text-gray-800 text-sm">{instruction}</p>
                  </div>
                </div>
              )) || <p className="text-gray-500">No instructions available</p>}
            </div>

            {recipe.cooking_tips && recipe.cooking_tips.length > 0 && (
              <div className="mt-6">
                <h4 className="font-bold mb-3">💡 Cooking Tips</h4>
                <div className="space-y-2">
                  {recipe.cooking_tips.map((tip, index) => (
                    <div key={index} className="bg-yellow-50 border-l-4 border-yellow-500 rounded p-3">
                      <span className="text-yellow-500 mr-2">💡</span>
                      <span className="text-sm text-gray-800">{tip}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'shopping' && (
          <div>
            <h3 className="text-lg font-bold mb-4">🛍️ Shop on Walmart</h3>

            {isLoadingCart ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-600 text-sm">Finding products...</p>
              </div>
            ) : (
              <>
                {getUniqueIngredients().map((ingredient, ingredientIndex) => {
                  const products = getProductsForIngredient(ingredient);
                  const isSelected = selectedProducts[ingredient];
                  const isAutoAdded = autoAddedItems.has(ingredient);

                  return (
                    <div key={ingredientIndex} className="mb-6 bg-white rounded-lg shadow p-4">
                      {/* Ingredient Header */}
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-2 ${isSelected ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                          <h4 className="font-bold text-gray-800 capitalize">{ingredient}</h4>
                          {isAutoAdded && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 ml-2 rounded-full">Auto-added</span>}
                        </div>
                        <input
                          type="checkbox"
                          checked={!!isSelected}
                          onChange={(e) => toggleItemInCart(ingredient, e.target.checked)}
                          className="w-5 h-5 text-green-500"
                        />
                      </div>

                      {/* Products */}
                      {products.length > 0 ? (
                        <div className="space-y-3">
                          {products.map((product, productIndex) => {
                            const isProductSelected = isSelected && isSelected.id === product.itemId;

                            return (
                              <div
                                key={productIndex}
                                onClick={() => handleProductSelection(ingredient, product, productIndex)}
                                className={`border-2 rounded-lg p-3 cursor-pointer transition-all ${
                                  isProductSelected 
                                    ? 'border-green-500 bg-green-50' 
                                    : 'border-gray-200 hover:border-blue-300'
                                }`}
                              >
                                {product.image && (
                                  <img 
                                    src={product.image} 
                                    alt={product.name}
                                    className="w-full h-20 object-cover rounded-lg mb-2"
                                    onError={(e) => { e.target.style.display = 'none'; }}
                                  />
                                )}

                                <div className="text-xs text-gray-600 font-medium mb-1">{product.brand || 'Brand'}</div>
                                <h6 className="font-bold text-sm text-gray-800 line-clamp-2 mb-2">{product.name}</h6>

                                <div className="flex justify-between items-center mb-2">
                                  <span className="text-lg font-bold text-green-600">${product.price?.toFixed(2) || '0.00'}</span>
                                  {product.rating > 0 && (
                                    <span className="text-xs text-yellow-500">⭐ {product.rating}</span>
                                  )}
                                </div>

                                <div className="flex flex-wrap gap-1 mb-2">
                                  {product.size && <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">{product.size}</span>}
                                  <span className={`text-xs px-2 py-1 rounded ${
                                    product.availability === 'InStock' 
                                      ? 'bg-green-100 text-green-700' 
                                      : 'bg-red-100 text-red-700'
                                  }`}>
                                    {product.availability || 'Available'}
                                  </span>
                                </div>

                                <button
                                  className={`w-full py-2 rounded-lg font-medium text-sm ${
                                    isProductSelected
                                      ? 'bg-green-500 text-white'
                                      : 'bg-blue-500 text-white hover:bg-blue-600'
                                  }`}
                                >
                                  {isProductSelected ? '✓ Selected' : 'Select'}
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="text-center py-4 text-gray-500">
                          <p className="text-sm">No products found for {ingredient}</p>
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Fixed Footer with Cart Summary */}
                {Object.keys(selectedProducts).length > 0 && (
                  <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg p-4">
                    <div className="max-w-md mx-auto">
                      <div className="text-center mb-3">
                        <div className="text-sm text-gray-600">{Object.keys(selectedProducts).length} items • ${calculateSelectedTotal().toFixed(2)}</div>
                      </div>
                      <button
                        onClick={() => {
                          const itemIds = Object.values(selectedProducts).map(product => product.id).filter(Boolean);
                          if (itemIds.length > 0) {
                            const cartUrl = `https://walmart.com/cart?items=${itemIds.join(',')}`;
                            window.open(cartUrl, '_blank');
                            showNotification(`🛒 Opening Walmart with ${itemIds.length} items!`, 'success');
                          }
                        }}
                        className="w-full bg-green-500 hover:bg-green-600 text-white py-3 rounded-lg font-bold"
                      >
                        🛒 Checkout on Walmart
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default RecipeDetailScreenMobile;
