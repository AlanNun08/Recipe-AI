import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  loadSavedUserSettings,
  normalizeDietaryPreferencesList,
  householdSizeToNumber,
  budgetStyleToWeeklyBudget,
} from '../utils/userSettings';

const WeeklyRecipesScreen = ({ user, onBack, showNotification, onViewRecipe }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  
  const [currentPlan, setCurrentPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [trialStatus, setTrialStatus] = useState(null);
  const [showGenerator, setShowGenerator] = useState(false);
  
  // Weekly plan generation form
  const [formData, setFormData] = useState({
    family_size: 2,
    dietary_preferences: [],
    cuisines: [],
    budget: 100
  });

  const dietaryOptions = ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo', 'low-carb', 'high-protein'];
  const cuisineOptions = ['italian', 'mexican', 'chinese', 'indian', 'mediterranean', 'american', 'thai', 'japanese', 'french', 'korean'];

  // Load current week's plan and trial status on component mount
  useEffect(() => {
    loadCurrentPlan();
    loadTrialStatus();
  }, []);

  useEffect(() => {
    if (!user) return;
    const savedSettings = loadSavedUserSettings(user);
    const dietaryPrefs = normalizeDietaryPreferencesList(savedSettings.preferences?.dietaryPreferences);
    const familySize = householdSizeToNumber(savedSettings.preferences?.householdSize, 2);
    const budget = budgetStyleToWeeklyBudget(savedSettings.preferences?.budgetStyle, 100);

    setFormData((prev) => ({
      ...prev,
      family_size: prev.family_size === 2 ? familySize : prev.family_size,
      budget: prev.budget === 100 ? budget : prev.budget,
      dietary_preferences: prev.dietary_preferences.length ? prev.dietary_preferences : dietaryPrefs,
    }));
  }, [user?.id, user?.user_id]);

  const hasGenerationAccess = trialStatus ? Boolean(trialStatus.has_access) : true;

  const handleUpgradeClick = () => {
    if (typeof window.setCurrentScreen === 'function') {
      window.setCurrentScreen('settings');
      return;
    }
    showNotification('Upgrade options are available in Settings.', 'info');
  };

  const loadTrialStatus = async () => {
    try {
      const response = await axios.get(`${API}/api/user/trial-status/${user.id}`);
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to load trial status:', error);
    }
  };

  const loadCurrentPlan = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/api/weekly-recipes/current/${user.id}`);
      if (response.data.has_plan) {
        setCurrentPlan(response.data.plan);
      } else {
        setCurrentPlan(null);
      }
    } catch (error) {
      console.error('Failed to load current plan:', error);
      if (error.response?.status === 402) {
        showNotification('❌ Premium feature: Upgrade to access weekly meal plans!', 'error');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const generateWeeklyPlan = async (e) => {
    if (e?.preventDefault) {
      e.preventDefault();
    }

    if (!hasGenerationAccess) {
      showNotification('Your 7-day free trial has ended. You can still view saved plans, but new weekly plan generation requires an upgrade.', 'warning');
      return;
    }

    setIsGenerating(true);
    
    try {
      console.log('📅 Generating weekly plan with OpenAI API...');
      showNotification('📅 Creating your weekly meal plan with AI...', 'info');

      const savedSettings = loadSavedUserSettings(user);
      const savedDietaryPrefs = normalizeDietaryPreferencesList(savedSettings.preferences?.dietaryPreferences);
      const effectiveFamilySize = parseInt(formData.family_size, 10) || householdSizeToNumber(savedSettings.preferences?.householdSize, 2);
      const effectiveBudget = parseFloat(formData.budget) || budgetStyleToWeeklyBudget(savedSettings.preferences?.budgetStyle, 100);
      const effectiveDietaryPrefs = formData.dietary_preferences.length > 0 ? formData.dietary_preferences : savedDietaryPrefs;
      
      const response = await axios.post(`${API}/api/weekly-recipes/generate`, {
        user_id: user.id,
        family_size: effectiveFamilySize,
        budget: effectiveBudget,
        dietary_preferences: effectiveDietaryPrefs,
        cuisines: formData.cuisines.length > 0 ? formData.cuisines : [],
        meal_types: ['breakfast', 'lunch', 'dinner'], // Default meal types
        cooking_time_preference: 'medium'
      });

      console.log('✅ Weekly plan generated successfully:', response.data);
      setCurrentPlan(response.data);
      showNotification('🎉 Weekly meal plan generated successfully!', 'success');
      setShowGenerator(false);
      
    } catch (error) {
      console.error('❌ Error generating weekly plan:', error);
      
      if (error.response?.status === 503) {
        // OpenAI API not configured
        showNotification('❌ AI meal planning is currently unavailable. Please contact support.', 'error');
      } else if ([402, 429].includes(error.response?.status)) {
        // Usage limit error
        const errorData = error.response?.data?.detail;
        if (error.response?.data?.trial_status) {
          setTrialStatus(error.response.data.trial_status);
        }
        
        if (typeof errorData === 'object' && errorData.upgrade_required) {
          showNotification(
            `⚠️ ${errorData.message}`, 
            'warning'
          );
          return;
        }
      } else {
        const errorMessage = error.response?.data?.detail || 'Failed to generate weekly plan. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleArrayItem = (array, item, setField) => {
    const newArray = array.includes(item)
      ? array.filter(i => i !== item)
      : [...array, item];
    setField(newArray);
  };

  const formatDaysRemaining = (days) => {
    if (days <= 0) return 'Expired';
    if (days === 1) return '1 day';
    return `${days} days`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-100 via-blue-100 to-purple-100 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-bounce">📅</div>
          <div className="text-xl text-gray-600">Loading your weekly plan...</div>
          <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mt-4"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-100 via-blue-100 to-purple-100 p-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header with Trial Status */}
        <div className="bg-white rounded-3xl shadow-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={onBack}
              className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
            >
              <span className="text-2xl mr-2">←</span>
              Back to Dashboard
            </button>
            
            {/* Trial Status Badge */}
            {trialStatus && (
              <div className="flex items-center space-x-2">
                {trialStatus.trial_active ? (
                  <span className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full text-sm font-bold">
                    ✨ {formatDaysRemaining(trialStatus.trial_days_left)} left in trial
                  </span>
                ) : trialStatus.subscription_active ? (
                  <span className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full text-sm font-bold">
                    💎 Premium Active
                  </span>
                ) : (
                  <span className="px-4 py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-full text-sm font-bold">
                    ⚠️ Subscription Required
                  </span>
                )}
              </div>
            )}
          </div>
          
          <div className="text-center">
            <div className="text-5xl mb-3 animate-bounce">📅</div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Weekly Meal Planner
            </h1>
            <p className="text-gray-600 text-lg">
              AI-generated meal plans with automatic Walmart shopping
            </p>
          </div>
        </div>

        {trialStatus && !trialStatus.has_access && (
          <div className="bg-white border border-amber-200 rounded-2xl p-4 mb-6 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-semibold text-gray-900">Weekly plan generation paused (trial ended)</p>
                <p className="text-sm text-gray-600">
                  You can still view existing plans and recipe history. Upgrade anytime to generate new weekly plans.
                </p>
              </div>
              <button
                onClick={handleUpgradeClick}
                className="rounded-xl bg-amber-100 text-amber-900 px-4 py-2 font-semibold hover:bg-amber-200 transition-colors"
              >
                Upgrade
              </button>
            </div>
          </div>
        )}

        {/* Current Plan Display */}
        {currentPlan ? (
          <div className="space-y-6">
            {/* Plan Header */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">This Week's Meals</h2>
                  <p className="text-gray-600">Week of {currentPlan.week_of}</p>
                  {currentPlan.ai_generated && (
                    <div className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 rounded-full text-xs font-bold mt-2">
                      ✨ AI-Generated Plan
                    </div>
                  )}
                </div>
                <div className="flex items-center space-x-3">
                  {currentPlan.total_estimated_cost && (
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">${currentPlan.total_estimated_cost.toFixed(2)}</div>
                      <div className="text-sm text-gray-500">Total Cost</div>
                    </div>
                  )}
                  <button
                    onClick={() => hasGenerationAccess ? setShowGenerator(true) : handleUpgradeClick()}
                    className={`px-4 py-2 rounded-xl transition-all ${
                      hasGenerationAccess
                        ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white hover:shadow-lg'
                        : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    🔄 Generate New Plan
                  </button>
                </div>
              </div>
            </div>

            {/* Weekly Meals Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {currentPlan.meals && currentPlan.meals.length > 0 ? (
                currentPlan.meals.map((meal) => {
                  // Get cost indicator based on meal type
                  const getCostIndicator = (mealType, estimatedCost) => {
                    if (mealType === 'breakfast' || mealType === 'snack') return '$';
                    if (mealType === 'lunch') return '$$';
                    if (mealType === 'dinner') return '$$$';
                    if (estimatedCost < 8) return '$';
                    if (estimatedCost < 15) return '$$';
                    return '$$$';
                  };

                  const costIndicator = getCostIndicator(meal.meal_type, meal.estimated_cost);

                  return (
                    <div 
                      key={meal.id} 
                      className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 flex flex-col h-full"
                    >
                      {/* Header with Day and Meal Type */}
                      <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-white font-bold text-lg">{meal.day_of_week}</h3>
                            <span className="inline-block px-3 py-1 bg-white bg-opacity-30 text-white text-xs font-semibold rounded-full mt-1 capitalize">
                              {meal.meal_type}
                            </span>
                          </div>
                          <span className="text-3xl font-bold text-yellow-300">{costIndicator}</span>
                        </div>
                      </div>
                      
                      <div className="p-6 flex-1 flex flex-col">
                        {/* Recipe Name */}
                        <h4 className="text-xl font-bold text-gray-800 mb-1">{meal.name}</h4>
                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">{meal.description}</p>
                        
                        {/* Quick Stats */}
                        <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
                          <div className="bg-blue-50 p-3 rounded-lg text-center">
                            <div className="text-blue-600 font-bold">⏱️</div>
                            <div className="text-gray-700 font-semibold">{meal.prep_time}</div>
                            <div className="text-gray-500 text-xs">Prep</div>
                          </div>
                          <div className="bg-orange-50 p-3 rounded-lg text-center">
                            <div className="text-orange-600 font-bold">🍳</div>
                            <div className="text-gray-700 font-semibold">{meal.cook_time}</div>
                            <div className="text-gray-500 text-xs">Cook</div>
                          </div>
                          <div className="bg-green-50 p-3 rounded-lg text-center">
                            <div className="text-green-600 font-bold">👥</div>
                            <div className="text-gray-700 font-semibold">{meal.servings}</div>
                            <div className="text-gray-500 text-xs">Servings</div>
                          </div>
                          <div className="bg-purple-50 p-3 rounded-lg text-center">
                            <div className="text-purple-600 font-bold">⭐</div>
                            <div className="text-gray-700 font-semibold capitalize">{meal.difficulty}</div>
                            <div className="text-gray-500 text-xs">Level</div>
                          </div>
                        </div>

                        {/* Cuisine and Cost */}
                        <div className="flex items-center justify-between mb-4 text-sm">
                          <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full font-medium capitalize">
                            🍜 {meal.cuisine_type}
                          </span>
                          {meal.estimated_cost !== undefined && (
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                              💰 ${meal.estimated_cost.toFixed(2)}
                            </span>
                          )}
                        </div>
                        
                        {/* Ingredients Preview - with scrollable list */}
                        {meal.ingredients && meal.ingredients.length > 0 && (
                          <div className="mb-4">
                            <div className="font-semibold text-gray-700 mb-2 flex items-center text-sm">
                              <span className="mr-2">🥘</span>
                              Ingredients ({meal.ingredients.length}):
                            </div>
                            <div className="text-xs text-gray-600 max-h-16 overflow-y-auto bg-gray-50 p-2 rounded-lg">
                              {meal.ingredients.slice(0, 5).map((ing, idx) => (
                                <div key={idx} className="py-1">• {ing}</div>
                              ))}
                              {meal.ingredients.length > 5 && (
                                <div className="py-1 text-gray-500 font-semibold">+{meal.ingredients.length - 5} more</div>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Nutrition Info */}
                        {meal.nutrition && typeof meal.nutrition === 'object' && Object.keys(meal.nutrition).length > 0 && (
                          <div className="mb-4">
                            <div className="font-semibold text-gray-700 mb-2 flex items-center text-sm">
                              <span className="mr-2">�</span>
                              Nutrition per Serving:
                            </div>
                            <div className="grid grid-cols-2 gap-1 text-xs">
                              {meal.nutrition.calories && (
                                <span className="bg-yellow-50 text-yellow-700 px-2 py-1 rounded">🔥 {meal.nutrition.calories}</span>
                              )}
                              {meal.nutrition.protein && (
                                <span className="bg-red-50 text-red-700 px-2 py-1 rounded">🥩 {meal.nutrition.protein}</span>
                              )}
                              {meal.nutrition.carbs && (
                                <span className="bg-orange-50 text-orange-700 px-2 py-1 rounded">🍞 {meal.nutrition.carbs}</span>
                              )}
                              {meal.nutrition.fat && (
                                <span className="bg-green-50 text-green-700 px-2 py-1 rounded">� {meal.nutrition.fat}</span>
                              )}
                            </div>
                          </div>
                        )}
                        
                        {/* Cooking Tips */}
                        {meal.cooking_tips && meal.cooking_tips.length > 0 && (
                          <div className="mb-4">
                            <div className="font-semibold text-gray-700 mb-2 flex items-center text-sm">
                              <span className="mr-2">💡</span>
                              Chef's Tips:
                            </div>
                            <div className="text-xs text-gray-600 bg-yellow-50 p-2 rounded-lg italic">
                              "{meal.cooking_tips[0]}"
                            </div>
                          </div>
                        )}
                        
                        {/* View Recipe Button - sticky at bottom */}
                        <button
                          onClick={() => onViewRecipe(meal.id, 'weekly')}
                          className="w-full mt-auto bg-gradient-to-r from-green-500 to-blue-500 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-300"
                        >
                          <span className="flex items-center justify-center">
                            <span className="mr-2">📖</span>
                            View Recipe & Shop
                            <span className="ml-2">🛒</span>
                          </span>
                        </button>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="col-span-full text-center py-8">
                  <p className="text-gray-600">No meals in this plan</p>
                </div>
              )}
            </div>

            {/* Shopping List Summary */}
            {currentPlan.shopping_list && currentPlan.shopping_list.length > 0 && (
              <div className="bg-white rounded-2xl shadow-xl p-6">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <span className="mr-3">🛒</span>
                  Master Shopping List ({currentPlan.shopping_list.length} items)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 mb-4">
                  {currentPlan.shopping_list.slice(0, 20).map((item, index) => (
                    <span key={index} className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full font-medium">
                      {item}
                    </span>
                  ))}
                  {currentPlan.shopping_list.length > 20 && (
                    <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full font-medium">
                      +{currentPlan.shopping_list.length - 20} more
                    </span>
                  )}
                </div>
                <button
                  onClick={() => {
                    const shoppingList = `Weekly Shopping List\nWeek of ${currentPlan.week_of}\n\n${currentPlan.shopping_list.map(item => `• ${item}`).join('\n')}\n\nGenerated by BuildYourSmartCart`;
                    navigator.clipboard.writeText(shoppingList);
                    showNotification('📋 Shopping list copied to clipboard!', 'success');
                  }}
                  className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-6 py-3 rounded-xl font-bold hover:shadow-lg transition-all"
                >
                  📋 Copy Complete Shopping List
                </button>
              </div>
            )}
          </div>
        ) : (
          /* No Plan - Show Generator */
          <div className="bg-white rounded-3xl shadow-2xl p-8">
            <div className="text-center mb-8">
              <div className="text-6xl mb-4 animate-bounce">🍽️</div>
              <h2 className="text-3xl font-bold text-gray-800 mb-2">No Meal Plan Yet</h2>
              <p className="text-gray-600 text-lg">
                Generate your personalized weekly meal plan with AI!
              </p>
            </div>
            
            <button
              onClick={() => hasGenerationAccess ? setShowGenerator(true) : handleUpgradeClick()}
              className={`w-full font-bold py-4 px-8 rounded-2xl shadow-lg transition-all duration-300 text-lg ${
                hasGenerationAccess
                  ? 'bg-gradient-to-r from-green-500 via-blue-500 to-purple-500 text-white hover:shadow-xl transform hover:-translate-y-1'
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed shadow-none'
              }`}
            >
              <span className="flex items-center justify-center">
                <span className="text-2xl mr-3 animate-bounce">🤖</span>
                Generate Weekly Meal Plan
                <span className="text-2xl ml-3 animate-bounce">✨</span>
              </span>
            </button>
          </div>
        )}

        {/* Meal Plan Generator Modal */}
        {showGenerator && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Generate Weekly Meal Plan</h2>
                <button
                  onClick={() => setShowGenerator(false)}
                  className="text-gray-500 hover:text-gray-700 text-3xl"
                >
                  ×
                </button>
              </div>
              
              <form onSubmit={generateWeeklyPlan} className="space-y-6">
                {!hasGenerationAccess && (
                  <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
                    <p className="font-semibold text-amber-900">Trial ended</p>
                    <p className="text-sm text-amber-800 mt-1">
                      You can still view your saved meals and recipe history. Upgrade to generate a new weekly plan.
                    </p>
                  </div>
                )}

                {/* Family Size */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Family Size
                  </label>
                  <select
                    value={formData.family_size}
                    onChange={(e) => setFormData({...formData, family_size: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value={1}>1 person</option>
                    <option value={2}>2 people</option>
                    <option value={3}>3 people</option>
                    <option value={4}>4 people</option>
                    <option value={5}>5 people</option>
                    <option value={6}>6+ people</option>
                  </select>
                </div>

                {/* Dietary Preferences */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Dietary Preferences
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {dietaryOptions.map(option => (
                      <label key={option} className="flex items-center space-x-2 p-3 rounded-xl hover:bg-gray-50 cursor-pointer border">
                        <input
                          type="checkbox"
                          checked={formData.dietary_preferences.includes(option)}
                          onChange={() => toggleArrayItem(
                            formData.dietary_preferences, 
                            option, 
                            (newArray) => setFormData({...formData, dietary_preferences: newArray})
                          )}
                          className="rounded text-green-500"
                        />
                        <span className="text-sm capitalize">{option}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Cuisine Preferences */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Preferred Cuisines (optional)
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {cuisineOptions.map(option => (
                      <label key={option} className="flex items-center space-x-2 p-3 rounded-xl hover:bg-gray-50 cursor-pointer border">
                        <input
                          type="checkbox"
                          checked={formData.cuisines.includes(option)}
                          onChange={() => toggleArrayItem(
                            formData.cuisines, 
                            option, 
                            (newArray) => setFormData({...formData, cuisines: newArray})
                          )}
                          className="rounded text-blue-500"
                        />
                        <span className="text-sm capitalize">{option}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Budget */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Weekly Budget (optional)
                  </label>
                  <input
                    type="number"
                    placeholder="100"
                    value={formData.budget}
                    onChange={(e) => setFormData({...formData, budget: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    min="10"
                    max="500"
                    step="10"
                  />
                  <p className="text-sm text-gray-500 mt-1">
                    Estimated budget for all ingredients (leave blank for no limit)
                  </p>
                </div>

                {/* Generate Button */}
                <button
                  type="submit"
                  disabled={isGenerating || !hasGenerationAccess}
                  className="w-full bg-gradient-to-r from-green-500 via-blue-500 to-purple-500 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGenerating ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Generating Meal Plan...</span>
                    </div>
                  ) : (
                    <span className="flex items-center justify-center">
                      <span className="text-2xl mr-3">🤖</span>
                      Generate 7-Day Meal Plan
                      <span className="text-2xl ml-3">✨</span>
                    </span>
                  )}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeeklyRecipesScreen;
