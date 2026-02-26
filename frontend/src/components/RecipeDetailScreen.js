import React, { useState, useEffect, useRef } from 'react';
import { openWalmartCart } from '../utils/externalLinks';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

function RecipeDetailScreen({ recipeId, recipeSource = 'weekly', onBack, showNotification, backDestination, triggerWalmartFetch }) {
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
  }, [recipeId]); // Keep recipeId dependency

  // If triggerWalmartFetch is set, force fetchCartOptions after mount
  useEffect(() => {
    if (triggerWalmartFetch && recipeId) {
      cartLoadedRef.current = false; // Reset so fetchCartOptions will run
      fetchCartOptions();
    }
    // Only run on mount or when triggerWalmartFetch changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        
        // NEW: Handle the enhanced data structure with multiple products per ingredient
        const walmartOption = data.cart_options?.[0]; // Get the Walmart store option
        
        if (walmartOption && walmartOption.products) {
          console.log('✅ Found Walmart products:', walmartOption.products.length);
          
          // Group products by ingredient for the new UI
          const productsByIngredient = {};
          walmartOption.products.forEach(product => {
            const ingredient = product.ingredient_match;
            if (!productsByIngredient[ingredient]) {
              productsByIngredient[ingredient] = [];
            }
            productsByIngredient[ingredient].push(product);
          });
          
          console.log('🛒 Products grouped by ingredient:', Object.keys(productsByIngredient).length, 'ingredients');
          
          // Update cart options with the enhanced structure
          setCartOptions([{
            ...walmartOption,
            productsByIngredient: productsByIngredient
          }]);
          
          // Auto-add best price items for each ingredient (first product in each group)
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

    // For each ingredient, auto-select the first product (best price/match)
    Object.entries(productsByIngredient).forEach(([ingredient, products]) => {
      if (products && products.length > 0) {
        const bestProduct = products[0]; // First product is best price from backend sorting
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

    // Remove from auto-added if user manually selects
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
      // Re-add the best price item if toggling back on
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
      // Check for new enhanced structure first
      if (option.productsByIngredient) {
        Object.keys(option.productsByIngredient).forEach(ingredient => {
          ingredients.add(ingredient);
        });
      } else if (option.products) {
        // Fallback to old structure
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
      // NEW: Check enhanced structure first (productsByIngredient)
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
        // Fallback: old structure
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
    
    // Sort by search rank, then by price (backend should already be sorted, but just in case)
    return products
      .sort((a, b) => {
        if (a.search_rank !== b.search_rank) {
          return a.search_rank - b.search_rank;
        }
        return a.price - b.price;
      })
      .slice(0, 3); // Ensure max 3 products
  };

  const getCompletionPercentage = () => {
    const totalIngredients = recipe?.ingredients?.length || 0;
    const selectedCount = Object.keys(selectedProducts).length;
    return totalIngredients > 0 ? Math.round((selectedCount / totalIngredients) * 100) : 0;
  };

  const getMissingIngredients = () => {
    const allIngredients = getUniqueIngredients();
    const selectedIngredients = Object.keys(selectedProducts);
    return allIngredients.filter(ing => !selectedIngredients.includes(ing));
  };

  const getCostIndicator = () => {
    // Cost indicator based on meal type
    // Breakfast/Snack = $ (inexpensive)
    // Lunch = $$ (moderate)
    // Dinner = $$$ (typically more expensive for a full meal)
    const mealType = recipe?.meal_type?.toLowerCase() || '';
    
    if (mealType.includes('breakfast') || mealType.includes('snack') || mealType.includes('appetizer')) {
      return '$';
    } else if (mealType.includes('lunch')) {
      return '$$';
    } else if (mealType.includes('dinner') || mealType.includes('main')) {
      return '$$$';
    } else {
      // Default based on servings if meal type unclear
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

  // ... existing loading and error states remain the same ...

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
    // ... existing error states remain the same ...
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <button
          onClick={onBack}
          className="flex items-center text-blue-700 hover:text-blue-800 font-medium mb-6"
        >
          <span className="mr-2">←</span>
          Back to Recipe History
        </button>

        {/* Recipe Header - Keep existing design */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
          {/* ... existing recipe header code ... */}
          <div className="bg-gradient-to-r from-blue-500 to-green-500 text-white p-6">
            <h1 className="text-3xl font-bold mb-2">{recipe.name}</h1>
            <p className="text-blue-100">{recipe.description}</p>
            
            <div className="flex flex-wrap gap-4 mt-4">
              <div className="bg-white bg-opacity-20 rounded px-3 py-1">
                <span className="font-medium">🍳 {recipe.cuisine_type}</span>
              </div>
              <div className="bg-white bg-opacity-20 rounded px-3 py-1">
                <span className="font-medium">🍽️ {recipe.meal_type}</span>
              </div>
              <div className="bg-white bg-opacity-20 rounded px-3 py-1">
                <span className="font-medium">⭐ {recipe.difficulty}</span>
              </div>
            </div>
          </div>

          {/* Recipe Stats */}
          <div className="p-6 border-b">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl">⏱️</div>
                <div className="font-bold">{recipe.prep_time}</div>
                <div className="text-sm text-gray-600">Prep Time</div>
              </div>
              <div className="text-center">
                <div className="text-2xl">🔥</div>
                <div className="font-bold">{recipe.cook_time}</div>
                <div className="text-sm text-gray-600">Cook Time</div>
              </div>
              <div className="text-center">
                <div className="text-2xl">👥</div>
                <div className="font-bold">{recipe.servings}</div>
                <div className="text-sm text-gray-600">Servings</div>
              </div>
              <div className="text-center">
                <div className="text-2xl">💰</div>
                <div className="font-bold">{getCostIndicator()}</div>
                <div className="text-sm text-gray-600">Est. Cost</div>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex border-b">
            {[
              { id: 'ingredients', label: 'Ingredients', icon: '🛒' },
              { id: 'instructions', label: 'Instructions', icon: '📝' },
              { id: 'nutrition', label: 'Nutrition', icon: '📊' },
              { id: 'shopping', label: 'Smart Shopping', icon: '🛍️' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-4 py-3 text-center font-medium ${
                  activeTab === tab.id
                    ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'ingredients' && (
              <div>
                <h3 className="text-xl font-bold mb-4">🛒 Ingredients ({recipe.ingredients?.length || 0})</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {recipe.ingredients?.map((ingredient, index) => (
                    <div key={index} className="flex items-center bg-gray-50 rounded p-3">
                      <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-3">
                        {index + 1}
                      </span>
                      <span>{ingredient}</span>
                    </div>
                  )) || <p className="text-gray-500">No ingredients available</p>}
                </div>
              </div>
            )}

            {activeTab === 'instructions' && (
              <div>
                <h3 className="text-xl font-bold mb-4">📝 Instructions ({recipe.instructions?.length || 0})</h3>
                <div className="space-y-4">
                  {recipe.instructions?.map((instruction, index) => (
                    <div key={index} className="flex bg-gray-50 rounded p-4">
                      <span className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold mr-4 flex-shrink-0">
                        {index + 1}
                      </span>
                      <p className="text-gray-800">{instruction}</p>
                    </div>
                  )) || <p className="text-gray-500">No instructions available</p>}
                </div>
              </div>
            )}

            {activeTab === 'nutrition' && (
              <div>
                <h3 className="text-xl font-bold mb-4">📊 Nutrition Information</h3>
                {recipe.nutrition ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(recipe.nutrition).map(([key, value]) => (
                      <div key={key} className="bg-gray-50 rounded p-4 text-center">
                        <div className="font-bold text-lg">{value}</div>
                        <div className="text-sm text-gray-600 capitalize">{key}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">Nutrition information not available</p>
                )}
                
                {recipe.cooking_tips && recipe.cooking_tips.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-bold mb-2">💡 Cooking Tips</h4>
                    <ul className="space-y-2">
                      {recipe.cooking_tips.map((tip, index) => (
                        <li key={index} className="flex items-start bg-yellow-50 rounded p-3">
                          <span className="text-yellow-500 mr-2">💡</span>
                          <span>{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'shopping' && (
              <div className="grid lg:grid-cols-10 gap-6">
                {/* Enhanced Main Shopping Area - 70% width */}
                <div className="lg:col-span-7">
                  {/* Search & Filter Bar */}
        {/* Removed search and filter section */}                  {/* Recipe completion progress removed */}

                  {/* Enhanced Product Grid by Ingredient */}
                  {isLoadingCart ? (
                    <div className="text-center py-12">
                      <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                      <p className="text-gray-600">Finding best products for your recipe...</p>
                    </div>
                  ) : (
                    <div className="space-y-8">
                      {getUniqueIngredients().map((ingredient, ingredientIndex) => {
                        const products = getProductsForIngredient(ingredient);
                        const isSelected = selectedProducts[ingredient];
                        const isAutoAdded = autoAddedItems.has(ingredient);

                        return (
                          <div key={ingredientIndex} className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                            {/* Ingredient Header */}
                            <div className={`p-4 border-b ${isSelected ? 'bg-green-50 border-green-200' : 'bg-gray-50'}`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                  <div className={`w-3 h-3 rounded-full mr-3 ${isSelected ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                                  <h4 className="text-lg font-bold text-gray-800 capitalize">{ingredient}</h4>
                                  {isAutoAdded && (
                                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                                      Auto-added
                                    </span>
                                  )}
                                </div>
                                <label className="flex items-center cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={!!isSelected}
                                    onChange={(e) => toggleItemInCart(ingredient, e.target.checked)}
                                    className="w-5 h-5 text-green-500 border-gray-300 rounded focus:ring-green-500"
                                  />
                                  <span className="ml-2 text-sm font-medium text-gray-700">
                                    {isSelected ? 'In Cart' : 'Add to Cart'}
                                  </span>
                                </label>
                              </div>
                            </div>

                            {/* Product Options (Show 3 options) */}
                            <div className="p-4">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {products.map((product, productIndex) => {
                                  const isProductSelected = isSelected && isSelected.id === product.itemId;
                                  const isPriceBest = product.is_best_price || productIndex === 0;
                                  const isBestMatch = product.search_rank === 1;

                                  return (
                                    <div
                                      key={productIndex}
                                      onClick={() => handleProductSelection(ingredient, product, productIndex)}
                                      className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all duration-200 hover:shadow-md ${
                                        isProductSelected 
                                          ? 'border-green-500 bg-green-50 shadow-md transform scale-105' 
                                          : 'border-gray-200 hover:border-blue-300'
                                      }`}
                                    >
                                      {/* Enhanced Badges */}
                                      {isPriceBest && !isProductSelected && (
                                        <div className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                                          Best Price!
                                        </div>
                                      )}
                                      
                                      {isBestMatch && !isPriceBest && !isProductSelected && (
                                        <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                                          Best Match!
                                        </div>
                                      )}

                                      {/* Selected Badge */}
                                      {isProductSelected && (
                                        <div className="absolute -top-2 -right-2 bg-green-500 text-white rounded-full p-1">
                                          <span className="text-xs">✓</span>
                                        </div>
                                      )}

                                      {/* Ranking Indicator */}
                                      <div className="absolute top-2 left-2 bg-gray-100 text-gray-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                                        #{product.search_rank || productIndex + 1}
                                      </div>

                                      {/* Product Image */}
                                      {product.image && (
                                        <div className="mb-3 mt-2">
                                          <img 
                                            src={product.image} 
                                            alt={product.name}
                                            className="w-full h-24 object-cover rounded-lg"
                                            onError={(e) => {
                                              e.target.style.display = 'none';
                                            }}
                                          />
                                        </div>
                                      )}

                                      {/* Product Details */}
                                      <div className="space-y-2">
                                        {/* Rating */}
                                        {product.rating > 0 && (
                                          <div className="flex items-center text-xs">
                                            <span className="text-yellow-500 mr-1">⭐</span>
                                            <span className="font-medium">{product.rating}</span>
                                            <span className="text-gray-500 ml-1">({product.reviewCount})</span>
                                          </div>
                                        )}

                                        {/* Brand */}
                                        <div className="text-xs text-blue-600 font-medium">
                                          {product.brand || 'Generic'}
                                        </div>

                                        {/* Product Name */}
                                        <h6 className="font-bold text-sm text-gray-800 leading-tight line-clamp-2">
                                          {product.name}
                                        </h6>

                                        {/* Price with Savings */}
                                        <div className="flex items-center justify-between">
                                          <div className="flex flex-col">
                                            <span className="text-lg font-bold text-green-600">
                                              ${product.price?.toFixed(2) || '0.00'}
                                            </span>
                                            {product.savings_amount > 0 && (
                                              <span className="text-xs text-green-600">
                                                Save ${product.savings_amount?.toFixed(2)}
                                              </span>
                                            )}
                                          </div>
                                          {product.msrp && product.msrp > product.price && (
                                            <span className="text-xs text-gray-500 line-through">
                                              ${product.msrp?.toFixed(2)}
                                            </span>
                                          )}
                                        </div>

                                        {/* Additional Info */}
                                        <div className="flex flex-wrap gap-1">
                                          {product.size && (
                                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                                              {product.size}
                                            </span>
                                          )}
                                          <span className={`text-xs px-2 py-1 rounded ${
                                            product.availability === 'InStock' 
                                              ? 'bg-green-100 text-green-700' 
                                              : 'bg-red-100 text-red-700'
                                          }`}>
                                            {product.availability || 'Available'}
                                          </span>
                                          {product.clearance && (
                                            <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                                              Clearance
                                            </span>
                                          )}
                                          {product.rollback && (
                                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                              Rollback
                                            </span>
                                          )}
                                        </div>

                                        {/* Select Button */}
                                        <button
                                          className={`w-full mt-2 py-2 px-3 rounded-lg font-medium text-sm transition-colors ${
                                            isProductSelected
                                              ? 'bg-green-500 text-white'
                                              : 'bg-blue-500 hover:bg-blue-600 text-white'
                                          }`}
                                        >
                                          {isProductSelected ? '✓ Selected' : 'Select This'}
                                        </button>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>

                              {/* Enhanced No Products Message */}
                              {products.length === 0 && (
                                <div className="text-center py-6 text-gray-500">
                                  <span className="text-2xl">🔍</span>
                                  <p className="mt-2">No products found for {ingredient}</p>
                                  <p className="text-xs mt-1">Try searching for a more generic term</p>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Enhanced Smart Shopping Sidebar - 30% width */}
                <div className="lg:col-span-3">
                  <div className="sticky top-6 space-y-6">
                    {/* Shopping Assistant Card */}
                    <div className="bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
                      {/* Header */}
                      <div className="bg-gradient-to-r from-green-500 to-blue-500 text-white p-4">
                        <h4 className="font-bold text-lg flex items-center">
                          <span className="mr-2 text-xl">🛒</span>
                          Your Walmart Cart
                        </h4>
                        <p className="text-sm text-green-100">
                          {Object.keys(selectedProducts).length} items • ${calculateSelectedTotal().toFixed(2)}
                        </p>
                      </div>

                      {/* Cart Items */}
                      <div className="p-4">
                        <div className="space-y-3 max-h-80 overflow-y-auto">
                          {Object.entries(selectedProducts).map(([ingredient, product]) => (
                            <div key={ingredient} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                              <div className="flex items-start">
                                {/* Product Image */}
                                {product.image && (
                                  <img 
                                    src={product.image} 
                                    alt={product.name}
                                    className="w-12 h-12 object-cover rounded mr-3 flex-shrink-0"
                                    onError={(e) => e.target.style.display = 'none'}
                                  />
                                )}
                                
                                {/* Product Info */}
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-gray-800 truncate">
                                    {product.name}
                                  </div>
                                  <div className="text-xs text-gray-600 flex items-center mt-1">
                                    <span className="mr-2">🥕 For: {product.ingredient}</span>
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {product.brand} • {product.size}
                                  </div>
                                  <div className="text-sm font-bold text-green-600 mt-1">
                                    ${product.price?.toFixed(2) || '0.00'}
                                  </div>
                                </div>

                                {/* Remove Button */}
                                <button
                                  onClick={() => removeProductFromCart(ingredient)}
                                  className="ml-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-full p-1 w-6 h-6 flex items-center justify-center transition-colors text-xs flex-shrink-0"
                                  title="Remove from cart"
                                >
                                  ✕
                                </button>
                              </div>
                            </div>
                          ))}

                          {Object.keys(selectedProducts).length === 0 && (
                            <div className="text-center py-8 text-gray-500">
                              <span className="text-3xl">🛒</span>
                              <p className="mt-2 text-sm">No items in cart yet</p>
                              <p className="text-xs">Items will be auto-added as they load</p>
                            </div>
                          )}
                        </div>

                        {/* Cart Summary */}
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Subtotal:</span>
                              <span className="font-medium">${calculateSelectedTotal().toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-gray-600">
                              <span>Est. Tax:</span>
                              <span>${(calculateSelectedTotal() * 0.08).toFixed(2)}</span>
                            </div>
                            <div className="border-t pt-2">
                              <div className="flex justify-between font-bold text-lg">
                                <span>Total:</span>
                                <span className="text-green-600">${(calculateSelectedTotal() * 1.08).toFixed(2)}</span>
                              </div>
                            </div>
                          </div>

                          {/* Action Buttons */}
                          <div className="mt-4 space-y-2">
                            <button
                              onClick={() => {
                                const itemIds = Object.values(selectedProducts).map(product => product.id).filter(Boolean);
                                if (itemIds.length > 0) {
                                  openWalmartCart(itemIds, { affiliate: true });
                                  showNotification(`🛒 Opening Walmart cart with ${itemIds.length} items!`, 'success');
                                } else {
                                  showNotification('Please select some items first', 'warning');
                                }
                              }}
                              disabled={Object.keys(selectedProducts).length === 0}
                              className={`w-full py-3 px-4 rounded-lg font-bold text-sm transition-colors ${
                                Object.keys(selectedProducts).length === 0
                                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                  : 'bg-green-500 hover:bg-green-600 text-white shadow-lg hover:shadow-xl'
                              }`}
                            >
                              🛒 Open in Walmart App
                            </button>
                            
                            <button
                              onClick={() => {
                                const itemIds = Object.values(selectedProducts).map(product => product.id).filter(Boolean);
                                if (itemIds.length > 0) {
                                  openWalmartCart(itemIds);
                                  showNotification('📱 Opening Walmart cart (mobile-safe link)...', 'info');
                                } else {
                                  showNotification('Please select some items first', 'warning');
                                }
                              }}
                              className="w-full py-2 px-4 rounded-lg font-medium text-sm bg-blue-500 hover:bg-blue-600 text-white transition-colors"
                            >
                              📱 Continue on Walmart.com
                            </button>
                            
                            <button
                              onClick={() => {
                                const shoppingList = Object.entries(selectedProducts)
                                  .map(([ingredient, product]) => `• ${product.name} - $${product.price?.toFixed(2)} (For: ${ingredient})`)
                                  .join('\n');
                                navigator.clipboard.writeText(`Shopping List:\n\n${shoppingList}`);
                                showNotification('📋 Shopping list copied to clipboard!', 'success');
                              }}
                              className="w-full py-2 px-4 rounded-lg font-medium text-sm bg-gray-500 hover:bg-gray-600 text-white transition-colors"
                            >
                              📋 Copy Shopping List
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Smart Suggestions */}
                    {Object.keys(selectedProducts).length > 0 && (
                      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-200">
                        <h5 className="font-bold text-sm mb-3 flex items-center">
                          <span className="mr-2">💡</span>
                          Smart Suggestions
                        </h5>
                        <div className="space-y-2 text-xs">
                          {getMissingIngredients().length > 0 && (
                            <div className="flex items-start">
                              <span className="text-orange-500 mr-2 mt-0.5">⚠️</span>
                              <span>Missing: {getMissingIngredients().slice(0, 2).join(', ')}</span>
                            </div>
                          )}
                          <div className="flex items-start">
                            <span className="text-green-500 mr-2 mt-0.5">✅</span>
                            <span>Store pickup available today</span>
                          </div>
                          <div className="flex items-start">
                            <span className="text-blue-500 mr-2 mt-0.5">🎟️</span>
                            <span>Coupons available: Save $1.50 total</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeDetailScreen;
