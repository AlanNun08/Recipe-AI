import React, { useState, useEffect } from 'react';
import axios from 'axios';

const WeeklyRecipesScreen = ({ user, onBack, showNotification, onViewRecipe }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
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
    e.preventDefault();
    setIsGenerating(true);
    
    try {
      const requestData = {
        user_id: user.id,
        family_size: parseInt(formData.family_size),
        dietary_preferences: formData.dietary_preferences,
        cuisines: formData.cuisines,
        budget: formData.budget ? parseFloat(formData.budget) : null
      };

      const response = await axios.post(`${API}/api/weekly-recipes/generate`, requestData);
      setCurrentPlan(response.data);
      setShowGenerator(false);
      showNotification('🎉 Your weekly meal plan is ready!', 'success');
    } catch (error) {
      console.error('Failed to generate weekly plan:', error);
      
      // Check if it's a usage limit error (status 429)
      if (error.response?.status === 429) {
        const errorData = error.response.data.detail;
        
        if (typeof errorData === 'object' && errorData.upgrade_required) {
          // Show usage limit reached message and redirect to upgrade
          showNotification(
            `⚠️ ${errorData.message} Redirecting to upgrade...`, 
            'warning'
          );
          
          // Redirect to subscription screen after a short delay
          setTimeout(() => {
            if (onBack) {
              onBack(); // Go back to dashboard first
              setTimeout(() => {
                showNotification('💎 Upgrade to get more weekly recipe plans!', 'info');
              }, 500);
            }
          }, 2000);
          
          return;
        }
      }
      
      if (error.response?.status === 402) {
        showNotification('❌ Premium feature: Upgrade to access weekly meal plans!', 'error');
      } else {
        const errorMessage = error.response?.data?.detail || 'Failed to generate meal plan. Please try again.';
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

        {/* Current Plan Display */}
        {currentPlan ? (
          <div className="space-y-6">
            {/* Plan Header */}
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-800">This Week's Meals</h2>
                  <p className="text-gray-600">Week of {currentPlan.week_of}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setShowGenerator(true)}
                    className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-4 py-2 rounded-xl hover:shadow-lg transition-all"
                  >
                    🔄 Generate New Plan
                  </button>
                </div>
              </div>
            </div>

            {/* Weekly Meals Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {currentPlan.meals?.map((meal, index) => (
                <div key={index} className="bg-white rounded-2xl shadow-xl overflow-hidden hover:shadow-2xl transition-all duration-300">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4">
                    <h3 className="text-white font-bold text-lg">{meal.day}</h3>
                  </div>
                  
                  <div className="p-6">
                    <h4 className="text-xl font-bold text-gray-800 mb-2">{meal.name}</h4>
                    <p className="text-gray-600 text-sm mb-4">{meal.description}</p>
                    
                    {/* Meal Details */}
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="mr-2">⏱️</span>
                        Prep: {meal.prep_time}min | Cook: {meal.cook_time}min
                      </div>
                      <div className="flex items-center text-sm text-gray-500">
                        <span className="mr-2">👥</span>
                        Serves {meal.servings} | {meal.cuisine_type}
                      </div>
                      {meal.calories_per_serving && (
                        <div className="flex items-center text-sm text-gray-500">
                          <span className="mr-2">🔥</span>
                          {meal.calories_per_serving} calories/serving
                        </div>
                      )}
                    </div>
                    
                    {/* Dietary Tags */}
                    {meal.dietary_tags && meal.dietary_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-4">
                        {meal.dietary_tags.map((tag, tagIndex) => (
                          <span key={tagIndex} className="px-2 py-1 bg-green-100 text-green-600 text-xs rounded-full">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {/* Ingredients Preview */}
                    <div className="mb-4">
                      <div className="font-semibold text-gray-700 mb-2">Ingredients:</div>
                      <div className="text-sm text-gray-600">
                        {meal.ingredients?.slice(0, 3).join(', ')}
                        {meal.ingredients?.length > 3 && `... +${meal.ingredients.length - 3} more`}
                      </div>
                    </div>
                    
                    {/* Instructions Preview */}
                    <div className="mb-4">
                      <div className="font-semibold text-gray-700 mb-2">Instructions:</div>
                      <div className="text-sm text-gray-600">
                        {meal.instructions?.[0] || 'Cooking instructions included'}
                        {meal.instructions?.length > 1 && ` (+${meal.instructions.length - 1} more steps)`}
                      </div>
                    </div>
                    
                    {/* View Recipe Button */}
                    <button
                      onClick={() => onViewRecipe(meal.id)}
                      className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-bold py-3 px-4 rounded-xl hover:shadow-lg transform hover:-translate-y-1 transition-all duration-300"
                    >
                      <span className="flex items-center justify-center">
                        <span className="mr-2">📖</span>
                        View Full Recipe
                        <span className="ml-2">🛒</span>
                      </span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
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
              onClick={() => setShowGenerator(true)}
              className="w-full bg-gradient-to-r from-green-500 via-blue-500 to-purple-500 text-white font-bold py-4 px-8 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 text-lg"
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
                  disabled={isGenerating}
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