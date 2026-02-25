import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeGeneratorScreen({ user, onBack, showNotification, onViewRecipe }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    cuisine: '',
    dietary_restrictions: '',
    prep_time: '',
    difficulty: '',
    ingredients: '',
    meal_type: '',
    servings: '4'
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecipe, setGeneratedRecipe] = useState(null);
  const [trialStatus, setTrialStatus] = useState(null);

  const cuisineOptions = [
    { value: 'Italian', emoji: '🍝', desc: 'Pasta, pizza, risotto' },
    { value: 'Mexican', emoji: '🌮', desc: 'Tacos, burritos, salsa' },
    { value: 'Chinese', emoji: '🥢', desc: 'Stir-fry, dumplings, rice' },
    { value: 'Indian', emoji: '🍛', desc: 'Curry, biryani, naan' },
    { value: 'French', emoji: '🥖', desc: 'Elegant, sophisticated' },
    { value: 'Thai', emoji: '🌶️', desc: 'Spicy, aromatic, fresh' },
    { value: 'Japanese', emoji: '🍜', desc: 'Sushi, ramen, tempura' },
    { value: 'Mediterranean', emoji: '🫒', desc: 'Healthy, olive oil, herbs' },
    { value: 'American', emoji: '🍔', desc: 'Comfort food, BBQ' },
    { value: 'Korean', emoji: '🥘', desc: 'Kimchi, bulgogi, spicy' },
    { value: 'Greek', emoji: '🧄', desc: 'Feta, olives, fresh' },
    { value: 'Spanish', emoji: '🥘', desc: 'Paella, tapas, gazpacho' }
  ];

  const difficultyOptions = [
    { value: 'easy', label: 'Easy', icon: '😊', desc: 'Quick & simple', time: '15-30 min', color: 'green' },
    { value: 'medium', label: 'Medium', icon: '🤔', desc: 'Some skills needed', time: '30-60 min', color: 'yellow' },
    { value: 'hard', label: 'Hard', icon: '👨‍🍳', desc: 'Advanced techniques', time: '60+ min', color: 'red' }
  ];

  const mealTypeOptions = [
    { value: 'breakfast', label: 'Breakfast', icon: '🌅', desc: 'Start your day right', time: 'Morning' },
    { value: 'lunch', label: 'Lunch', icon: '🥪', desc: 'Midday fuel', time: 'Afternoon' },
    { value: 'dinner', label: 'Dinner', icon: '🍽️', desc: 'Evening feast', time: 'Evening' },
    { value: 'snack', label: 'Snack', icon: '🍿', desc: 'Quick bite', time: 'Anytime' },
    { value: 'dessert', label: 'Dessert', icon: '🍰', desc: 'Sweet treat', time: 'After meals' },
    { value: 'appetizer', label: 'Appetizer', icon: '🥗', desc: 'Start the meal', time: 'Before dinner' }
  ];

  const prepTimeOptions = [
    { value: '15 minutes', label: '15 min', icon: '⚡', desc: 'Super quick' },
    { value: '30 minutes', label: '30 min', icon: '⏰', desc: 'Quick & easy' },
    { value: '45 minutes', label: '45 min', icon: '⏱️', desc: 'Standard time' },
    { value: '1 hour', label: '1 hour', icon: '🕐', desc: 'Worth the wait' },
    { value: '1+ hours', label: '1+ hours', icon: '⏳', desc: 'Slow & steady' }
  ];

  const servingsOptions = [
    { value: 1, label: '1 person', icon: '👤', desc: 'Just for me' },
    { value: 2, label: '2 people', icon: '👫', desc: 'Couple meal' },
    { value: 4, label: '4 people', icon: '👨‍👩‍👧‍👦', desc: 'Family meal' },
    { value: 6, label: '6 people', icon: '👥', desc: 'Small group' },
    { value: 8, label: '8 people', icon: '🎉', desc: 'Party size' },
    { value: 12, label: '12+ people', icon: '🎊', desc: 'Large gathering' }
  ];

  const popularDietaryRestrictions = [
    { value: 'Vegetarian', icon: '🥬', color: 'green' },
    { value: 'Vegan', icon: '🌱', color: 'green' },
    { value: 'Gluten-free', icon: '🚫', color: 'blue' },
    { value: 'Keto', icon: '🥑', color: 'purple' },
    { value: 'Paleo', icon: '🦴', color: 'orange' },
    { value: 'Low-carb', icon: '📉', color: 'red' },
    { value: 'Dairy-free', icon: '🚫', color: 'yellow' },
    { value: 'Nut-free', icon: '🥜', color: 'red' }
  ];

  const totalSteps = 4;

  useEffect(() => {
    const userId = user?.id || user?.user_id;
    if (userId) {
      loadTrialStatus(userId);
    }
  }, [user]);

  const loadTrialStatus = async (userId) => {
    try {
      const response = await axios.get(`${API}/api/user/trial-status/${userId}`);
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to load trial status:', error);
    }
  };

  const hasGenerationAccess = trialStatus ? Boolean(trialStatus.has_access) : true;

  const handleUpgradeClick = () => {
    if (typeof window.setCurrentScreen === 'function') {
      window.setCurrentScreen('settings');
      return;
    }
    showNotification('Upgrade options are available in Settings.', 'info');
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSelection = (fieldName, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleDietaryRestrictionToggle = (restriction) => {
    const current = formData.dietary_restrictions;
    const restrictions = current ? current.split(', ').filter(r => r) : [];
    
    if (restrictions.includes(restriction)) {
      // Remove restriction
      const updated = restrictions.filter(r => r !== restriction);
      setFormData(prev => ({
        ...prev,
        dietary_restrictions: updated.join(', ')
      }));
    } else {
      // Add restriction
      restrictions.push(restriction);
      setFormData(prev => ({
        ...prev,
        dietary_restrictions: restrictions.join(', ')
      }));
    }
  };

  const nextStep = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1: return formData.cuisine && formData.meal_type;
      case 2: return formData.difficulty;
      case 3: return true; // Optional step
      case 4: return true; // Review step
      default: return false;
    }
  };

  const generateRecipe = async () => {
    if (!hasGenerationAccess) {
      showNotification('Your 7-day free trial has ended. You can still view history, but recipe generation requires an upgrade.', 'warning');
      return;
    }

    if (!formData.cuisine || !formData.meal_type || !formData.difficulty) {
      showNotification('Please complete the required fields!', 'error');
      return;
    }

    setIsGenerating(true);
    
    try {
      console.log('🤖 Generating recipe with OpenAI API...');
      console.log('👤 Current user:', user);
      showNotification('🤖 Generating your recipe with AI...', 'info');
      
      // Send properly formatted request to backend - FIX: Use correct user_id
      const requestData = {
        user_id: user?.user_id || user?.id || 'demo_user', // FIX: Use the correct user ID field
        cuisine_type: formData.cuisine,
        meal_type: formData.meal_type,
        difficulty: formData.difficulty,
        servings: parseInt(formData.servings) || 4,
        prep_time_max: formData.prep_time ? parseInt(formData.prep_time.split(' ')[0]) : null,
        dietary_preferences: formData.dietary_restrictions ? 
          formData.dietary_restrictions.split(',').map(d => d.trim()).filter(d => d) : [],
        ingredients_on_hand: formData.ingredients ? 
          formData.ingredients.split(',').map(i => i.trim()).filter(i => i) : []
      };

      console.log('📤 Sending request to API:', requestData);
      console.log('📤 Request payload keys:', Object.keys(requestData));
      console.log('📤 Request validation:', {
        has_user_id: !!requestData.user_id,
        has_cuisine_type: !!requestData.cuisine_type,
        has_meal_type: !!requestData.meal_type,
        has_difficulty: !!requestData.difficulty,
        has_servings: !!requestData.servings
      });

      const startTime = Date.now();
      console.log(`⏱️ Request started at: ${new Date().toISOString()}`);
      
      const response = await axios.post(`${API}/api/recipes/generate`, requestData);
      
      const elapsedTime = Date.now() - startTime;
      console.log(`✅ Response received after ${elapsedTime}ms`);
      console.log('📥 Received response from API:', response.data);
      console.log('📥 Response status:', response.status);
      console.log('📥 Response headers:', response.headers);
      console.log('📥 Response validation:', {
        has_name: !!response.data.name,
        has_ingredients: !!response.data.ingredients,
        has_instructions: !!response.data.instructions,
        has_id: !!response.data.id,
        ingredients_count: response.data.ingredients?.length || 0,
        instructions_count: response.data.instructions?.length || 0
      });
      
      // Validate the response has required data
      if (!response.data.name || !response.data.ingredients || !response.data.instructions) {
        throw new Error('Invalid recipe data received from API');
      }

      // Store the generated recipe
      setGeneratedRecipe(response.data);
      showNotification('🎉 Recipe generated successfully with AI!', 'success');
      
      // Auto-navigate to detail screen to fetch cart options immediately
      console.log('📱 Auto-navigating to recipe detail to fetch Walmart items...');
      if (onViewRecipe) {
        // Pass a callback to trigger Walmart fetch after navigation
        onViewRecipe(response.data.id, 'generated', {
          triggerWalmartFetch: true
        });
      } else {
        // Fallback: show results step if onViewRecipe not available
        setCurrentStep(5);
      }

    } catch (error) {
      console.error('❌ Error generating recipe:', error);
      console.error('❌ Error stack trace:', error.stack);
      
      // Log request and response details
      if (error.request) {
        console.error('❌ Request details:', {
          method: error.request.method,
          url: error.request.url,
          status: error.request.status,
          statusText: error.request.statusText,
          readyState: error.request.readyState
        });
      }
      
      if (error.response) {
        console.error('❌ Response details:', {
          status: error.response.status,
          statusText: error.response.statusText,
          headers: error.response.headers,
          data: error.response.data,
          config: error.response.config
        });
      }
      
      if (error.response?.status === 503) {
        showNotification('❌ AI recipe generation is currently unavailable. Please contact support.', 'error');
      } else if (error.response?.status === 500) {
        // NEW: Handle 500 errors specifically
        const errorDetail = error.response?.data?.detail || 'Internal server error';
        console.error('🔥 Server error details:', errorDetail);
        showNotification(`❌ Server error: ${errorDetail}`, 'error');
      } else if ([402, 429].includes(error.response?.status)) {
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
        const errorMessage = error.response?.data?.detail || 'Failed to generate recipe. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const viewRecipeDetail = () => {
    if (generatedRecipe && onViewRecipe) {
      console.log('👀 Viewing recipe detail:', generatedRecipe.id);
      // FIX: Ensure we navigate to recipe detail properly
      onViewRecipe(generatedRecipe.id, 'generated');
    } else {
      console.error('❌ No generated recipe or onViewRecipe callback missing');
      showNotification('❌ Cannot view recipe details', 'error');
    }
  };

  const resetForm = () => {
    setFormData({
      cuisine: '',
      dietary_restrictions: '',
      prep_time: '',
      difficulty: '',
      ingredients: '',
      meal_type: '',
      servings: '4'
    });
    setGeneratedRecipe(null);
    setCurrentStep(1);
  };

  const ProgressBar = () => (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div key={i} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
              i + 1 <= currentStep 
                ? 'bg-orange-500 text-white' 
                : 'bg-gray-200 text-gray-400'
            }`}>
              {i + 1}
            </div>
            {i < totalSteps - 1 && (
              <div className={`w-12 h-1 mx-2 transition-all duration-300 ${
                i + 1 < currentStep ? 'bg-orange-500' : 'bg-gray-200'
              }`} />
            )}
          </div>
        ))}
      </div>
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-700">
          Step {currentStep} of {totalSteps}
        </h3>
      </div>
    </div>
  );

  const StepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">What are you craving?</h2>
              <p className="text-gray-600 text-lg">Choose your cuisine and meal type</p>
            </div>

            {/* Cuisine Selection */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-6 text-center">
                🌍 Choose Your Cuisine
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {cuisineOptions.map(cuisine => (
                  <button
                    key={cuisine.value}
                    type="button"
                    onClick={() => handleSelection('cuisine', cuisine.value)}
                    className={`p-4 rounded-xl border-2 transition-all duration-200 text-center hover:scale-105 ${
                      formData.cuisine === cuisine.value
                        ? 'border-orange-500 bg-orange-50 text-orange-700 shadow-lg'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-orange-300 hover:shadow-md'
                    }`}
                  >
                    <div className="text-3xl mb-2">{cuisine.emoji}</div>
                    <div className="font-bold text-sm">{cuisine.value}</div>
                    <div className="text-xs text-gray-500 mt-1">{cuisine.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Meal Type Selection */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-6 text-center">
                🍽️ What type of meal?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {mealTypeOptions.map(type => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => handleSelection('meal_type', type.value)}
                    className={`p-6 rounded-xl border-2 transition-all duration-200 text-center hover:scale-105 ${
                      formData.meal_type === type.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700 shadow-lg'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-blue-300 hover:shadow-md'
                    }`}
                  >
                    <div className="text-4xl mb-2">{type.icon}</div>
                    <div className="font-bold">{type.label}</div>
                    <div className="text-sm text-gray-500 mt-1">{type.desc}</div>
                    <div className="text-xs text-gray-400 mt-1">{type.time}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">How challenging?</h2>
              <p className="text-gray-600 text-lg">Pick your cooking difficulty level</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {difficultyOptions.map(diff => (
                <button
                  key={diff.value}
                  type="button"
                  onClick={() => handleSelection('difficulty', diff.value)}
                  className={`p-8 rounded-2xl border-2 transition-all duration-200 text-center hover:scale-105 ${
                    formData.difficulty === diff.value
                      ? 'border-green-500 bg-green-50 text-green-700 shadow-xl'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-green-300 hover:shadow-lg'
                  }`}
                >
                  <div className="text-6xl mb-4">{diff.icon}</div>
                  <div className="text-2xl font-bold mb-2">{diff.label}</div>
                  <div className="text-gray-600 mb-2">{diff.desc}</div>
                  <div className="text-sm text-gray-500">{diff.time}</div>
                </button>
              ))}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Customize your recipe</h2>
              <p className="text-gray-600 text-lg">These are optional but help personalize your recipe</p>
            </div>

            {/* Servings */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                👥 How many servings?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 max-w-4xl mx-auto">
                {servingsOptions.map(serving => (
                  <button
                    key={serving.value}
                    type="button"
                    onClick={() => handleSelection('servings', serving.value.toString())}
                    className={`p-4 rounded-xl border-2 transition-all duration-200 text-center hover:scale-105 ${
                      formData.servings === serving.value.toString()
                        ? 'border-purple-500 bg-purple-50 text-purple-700 shadow-lg'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-purple-300 hover:shadow-md'
                    }`}
                  >
                    <div className="text-2xl mb-2">{serving.icon}</div>
                    <div className="font-bold text-sm">{serving.label}</div>
                    <div className="text-xs text-gray-500 mt-1">{serving.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Prep Time */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                ⏱️ Maximum prep time?
              </label>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 max-w-4xl mx-auto">
                {prepTimeOptions.map(time => (
                  <button
                    key={time.value}
                    type="button"
                    onClick={() => handleSelection('prep_time', time.value)}
                    className={`p-4 rounded-xl border-2 transition-all duration-200 text-center hover:scale-105 ${
                      formData.prep_time === time.value
                        ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-lg'
                        : 'border-gray-200 bg-white text-gray-600 hover:border-indigo-300 hover:shadow-md'
                    }`}
                  >
                    <div className="text-2xl mb-2">{time.icon}</div>
                    <div className="font-bold">{time.label}</div>
                    <div className="text-xs text-gray-500 mt-1">{time.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Dietary Restrictions */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                🥗 Any dietary restrictions?
              </label>
              <div className="flex flex-wrap justify-center gap-3 max-w-4xl mx-auto mb-4">
                {popularDietaryRestrictions.map(restriction => (
                  <button
                    key={restriction.value}
                    type="button"
                    onClick={() => handleDietaryRestrictionToggle(restriction.value)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 flex items-center space-x-2 hover:scale-105 ${
                      formData.dietary_restrictions.includes(restriction.value)
                        ? 'bg-green-100 text-green-700 border-2 border-green-300 shadow-md'
                        : 'bg-gray-100 text-gray-600 border-2 border-gray-200 hover:border-green-300'
                    }`}
                  >
                    <span>{restriction.icon}</span>
                    <span>{restriction.value}</span>
                  </button>
                ))}
              </div>
              <div className="max-w-lg mx-auto">
                <input
                  type="text"
                  name="dietary_restrictions"
                  value={formData.dietary_restrictions}
                  onChange={handleInputChange}
                  placeholder="Or type custom dietary restrictions..."
                  className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white text-center"
                />
              </div>
            </div>

            {/* Specific Ingredients */}
            <div>
              <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                🥘 Got specific ingredients to use?
              </label>
              <div className="max-w-lg mx-auto">
                <textarea
                  name="ingredients"
                  value={formData.ingredients}
                  onChange={handleInputChange}
                  placeholder="e.g., chicken, tomatoes, basil, mushrooms... (optional)"
                  rows="3"
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white resize-none text-center"
                />
                <p className="text-sm text-gray-500 mt-2 text-center">
                  💡 Leave blank for surprise ingredients based on your cuisine choice
                </p>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">Ready to cook?</h2>
              <p className="text-gray-600 text-lg">Review your choices and generate your recipe</p>
            </div>

            <div className="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-lg max-w-2xl mx-auto">
              <div className="space-y-6">
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="font-semibold text-gray-700">Cuisine:</span>
                  <span className="text-orange-600 font-bold">{formData.cuisine || 'Not selected'}</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="font-semibold text-gray-700">Meal Type:</span>
                  <span className="text-blue-600 font-bold">{formData.meal_type || 'Not selected'}</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="font-semibold text-gray-700">Difficulty:</span>
                  <span className="text-green-600 font-bold capitalize">{formData.difficulty || 'Not selected'}</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-gray-100">
                  <span className="font-semibold text-gray-700">Servings:</span>
                  <span className="text-purple-600 font-bold">{formData.servings} people</span>
                </div>
                {formData.prep_time && (
                  <div className="flex items-center justify-between py-3 border-b border-gray-100">
                    <span className="font-semibold text-gray-700">Max Prep Time:</span>
                    <span className="text-indigo-600 font-bold">{formData.prep_time}</span>
                  </div>
                )}
                {formData.dietary_restrictions && (
                  <div className="flex items-center justify-between py-3 border-b border-gray-100">
                    <span className="font-semibold text-gray-700">Dietary:</span>
                    <span className="text-green-600 font-bold">{formData.dietary_restrictions}</span>
                  </div>
                )}
                {formData.ingredients && (
                  <div className="py-3">
                    <span className="font-semibold text-gray-700 block mb-2">Specific Ingredients:</span>
                    <span className="text-gray-600">{formData.ingredients}</span>
                  </div>
                )}
              </div>

              <button
                onClick={generateRecipe}
                disabled={isGenerating || !formData.cuisine || !formData.meal_type || !formData.difficulty || !hasGenerationAccess}
                className={`w-full font-bold py-5 px-6 rounded-2xl mt-8 transition-all duration-300 flex items-center justify-center text-lg shadow-lg ${
                  isGenerating || !formData.cuisine || !formData.meal_type || !formData.difficulty || !hasGenerationAccess
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-orange-500 to-red-600 text-white hover:shadow-xl transform hover:-translate-y-1 hover:from-orange-600 hover:to-red-700'
                }`}
              >
                {isGenerating ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                    Creating Your Perfect Recipe...
                  </>
                ) : (
                  <>
                    <span className="mr-3 text-2xl">✨</span>
                    Generate My Recipe
                  </>
                )}
              </button>

              {!hasGenerationAccess && (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-left">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold text-amber-900">Your free trial has ended</p>
                      <p className="text-sm text-amber-800 mt-1">
                        You can still access your recipe history and saved recipes. Upgrade when you are ready to keep generating new AI recipes.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={handleUpgradeClick}
                      className="shrink-0 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-amber-900 border border-amber-300 hover:bg-amber-100 transition-colors"
                    >
                      Upgrade
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-800 mb-4">🎉 Recipe Ready!</h2>
              <p className="text-gray-600 text-lg">Your personalized recipe has been generated</p>
              {generatedRecipe?.ai_generated && (
                <div className="inline-block bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-full text-sm font-bold mt-2">
                  ✨ AI-Generated Recipe
                </div>
              )}
            </div>

            {generatedRecipe && (
              <div className="bg-white rounded-2xl p-8 border-2 border-gray-100 shadow-lg max-w-4xl mx-auto">
                {/* Recipe Header */}
                <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-6 border border-green-200 mb-6">
                  <h3 className="text-3xl font-bold text-gray-800 mb-4 text-center">
                    {generatedRecipe.name}
                  </h3>
                  <p className="text-gray-600 leading-relaxed mb-6 text-center text-lg">
                    {generatedRecipe.description}
                  </p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-3xl mb-2">⏱️</div>
                      <div className="text-xs text-gray-500">Prep Time</div>
                      <div className="font-bold text-gray-800">
                        {generatedRecipe.prep_time || 'N/A'}
                      </div>
                    </div>
                    <div className="text-center bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-3xl mb-2">🔥</div>
                      <div className="text-xs text-gray-500">Cook Time</div>
                      <div className="font-bold text-gray-800">
                        {generatedRecipe.cook_time || 'N/A'}
                      </div>
                    </div>
                    <div className="text-center bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-3xl mb-2">👥</div>
                      <div className="text-xs text-gray-500">Servings</div>
                      <div className="font-bold text-gray-800">
                        {generatedRecipe.servings}
                      </div>
                    </div>
                    <div className="text-center bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-3xl mb-2">🏷️</div>
                      <div className="text-xs text-gray-500">Cuisine</div>
                      <div className="font-bold text-gray-800">
                        {generatedRecipe.cuisine_type}
                      </div>
                    </div>
                  </div>

                  {/* Nutrition Info - Only show if exists */}
                  {generatedRecipe.nutrition && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                      <div className="text-center bg-yellow-50 rounded-xl p-3 shadow-sm">
                        <div className="text-2xl mb-1">🔥</div>
                        <div className="text-xs text-gray-500">Calories</div>
                        <div className="font-bold text-gray-800">{generatedRecipe.nutrition.calories}</div>
                      </div>
                      <div className="text-center bg-red-50 rounded-xl p-3 shadow-sm">
                        <div className="text-2xl mb-1">🥩</div>
                        <div className="text-xs text-gray-500">Protein</div>
                        <div className="font-bold text-gray-800">{generatedRecipe.nutrition.protein}</div>
                      </div>
                      <div className="text-center bg-orange-50 rounded-xl p-3 shadow-sm">
                        <div className="text-2xl mb-1">🍞</div>
                        <div className="text-xs text-gray-500">Carbs</div>
                        <div className="font-bold text-gray-800">{generatedRecipe.nutrition.carbs}</div>
                      </div>
                      <div className="text-center bg-green-50 rounded-xl p-3 shadow-sm">
                        <div className="text-2xl mb-1">🥑</div>
                        <div className="text-xs text-gray-500">Fat</div>
                        <div className="font-bold text-gray-800">{generatedRecipe.nutrition.fat}</div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Recipe Details Display - Show REAL data */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Real Ingredients */}
                  <div className="bg-amber-50 rounded-2xl p-6 border border-amber-200">
                    <h4 className="font-bold text-gray-800 mb-4 flex items-center text-lg">
                      <span className="mr-2 text-2xl">🥘</span>
                      Ingredients ({generatedRecipe.ingredients?.length || 0})
                    </h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {generatedRecipe.ingredients?.map((ingredient, index) => (
                        <div key={index} className="flex items-start text-sm text-gray-700 bg-white rounded-lg p-3 shadow-sm">
                          <span className="w-2 h-2 bg-amber-500 rounded-full mr-3 mt-2 flex-shrink-0"></span>
                          <span className="leading-relaxed font-medium">{ingredient}</span>
                        </div>
                      )) || (
                        <div className="text-center py-8">
                          <div className="text-4xl mb-4">🤔</div>
                          <p className="text-gray-600">No ingredients available</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Real Instructions */}
                  <div className="bg-blue-50 rounded-2xl p-6 border border-blue-200">
                    <h4 className="font-bold text-gray-800 mb-4 flex items-center text-lg">
                      <span className="mr-2 text-2xl">📋</span>
                      Instructions ({generatedRecipe.instructions?.length || 0} steps)
                    </h4>
                    <div className="space-y-3 max-h-48 overflow-y-auto">
                      {generatedRecipe.instructions?.map((instruction, index) => (
                        <div key={index} className="flex items-start text-sm text-gray-700 bg-white rounded-lg p-3 shadow-sm">
                          <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5 flex-shrink-0">
                            {index + 1}
                          </span>
                          <span className="leading-relaxed font-medium">{instruction}</span>
                        </div>
                      )) || (
                        <div className="text-center py-8">
                          <div className="text-4xl mb-4">🤔</div>
                          <p className="text-gray-600">No instructions available</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Cooking Tips - Only show if exists */}
                {generatedRecipe.cooking_tips && generatedRecipe.cooking_tips.length > 0 && (
                  <div className="bg-purple-50 rounded-2xl p-6 border border-purple-200 mt-6">
                    <h4 className="font-bold text-gray-800 mb-4 flex items-center text-lg">
                      <span className="mr-2 text-2xl">💡</span>
                      Cooking Tips
                    </h4>
                    <div className="space-y-2">
                      {generatedRecipe.cooking_tips.map((tip, index) => (
                        <div key={index} className="flex items-start text-sm text-gray-700 bg-white rounded-lg p-3 shadow-sm">
                          <span className="text-purple-500 mr-2 text-lg">💡</span>
                          <span className="leading-relaxed font-medium">{tip}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recipe Summary */}
                <div className="bg-gray-50 rounded-2xl p-6 border border-gray-200 mt-6">
                  <h4 className="font-bold text-gray-800 mb-4 flex items-center text-lg">
                    <span className="mr-2 text-2xl">📊</span>
                    Recipe Summary
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    {generatedRecipe.estimated_cost && (
                      <div className="bg-white rounded-xl p-4 shadow-sm">
                        <div className="text-2xl mb-2">💰</div>
                        <div className="text-sm text-gray-600">Estimated Cost</div>
                        <div className="font-bold text-green-600">${generatedRecipe.estimated_cost.toFixed(2)}</div>
                      </div>
                    )}
                    <div className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-2xl mb-2">⭐</div>
                      <div className="text-sm text-gray-600">Difficulty</div>
                      <div className="font-bold text-purple-600 capitalize">{generatedRecipe.difficulty}</div>
                    </div>
                    <div className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-2xl mb-2">⏱️</div>
                      <div className="text-sm text-gray-600">Total Time</div>
                      <div className="font-bold text-blue-600">{generatedRecipe.total_time || 'N/A'}</div>
                    </div>
                    <div className="bg-white rounded-xl p-4 shadow-sm">
                      <div className="text-2xl mb-2">🎯</div>
                      <div className="text-sm text-gray-600">Meal Type</div>
                      <div className="font-bold text-orange-600 capitalize">{generatedRecipe.meal_type}</div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
                  <button
                    onClick={viewRecipeDetail}
                    className="bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold py-4 px-6 rounded-2xl hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
                  >
                    <span className="mr-3 text-2xl">👀</span>
                    View Full Recipe with Walmart Shopping
                  </button>

                  <button
                    onClick={resetForm}
                    className="bg-gradient-to-r from-gray-500 to-gray-600 text-white font-bold py-4 px-6 rounded-2xl hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
                  >
                    <span className="mr-3 text-2xl">🔄</span>
                    Generate Another Recipe
                  </button>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  const NavigationButtons = () => (
    <div className="flex justify-between mt-8">
      <button
        onClick={prevStep}
        disabled={currentStep === 1}
        className={`flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
          currentStep === 1
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
            : 'bg-gray-500 text-white hover:bg-gray-600 hover:shadow-md'
        }`}
      >
        <span className="mr-2">←</span>
        Previous
      </button>

      {currentStep < 4 && (
        <button
          onClick={nextStep}
          disabled={!canProceed()}
          className={`flex items-center px-6 py-3 rounded-xl font-medium transition-all duration-200 ${
            canProceed()
              ? 'bg-orange-500 text-white hover:bg-orange-600 hover:shadow-md'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          Next
          <span className="ml-2">→</span>
        </button>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={onBack}
            className="group flex items-center text-orange-700 hover:text-orange-800 font-medium mb-6 transition-all duration-200 hover:transform hover:-translate-x-1"
          >
            <span className="mr-2 group-hover:mr-3 transition-all duration-200">←</span>
            Back to Dashboard
          </button>
          
          <div className="text-center bg-white rounded-3xl shadow-lg p-8 mb-8">
            <div className="text-8xl mb-6 animate-bounce">🍳</div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-4">
              AI Recipe Generator
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed max-w-3xl mx-auto">
              Create personalized recipes with AI and get instant Walmart shopping lists
            </p>
          </div>

          {trialStatus && !trialStatus.has_access && (
            <div className="bg-white border border-amber-200 rounded-2xl p-4 shadow-sm">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-semibold text-gray-900">Generation is paused (trial ended)</p>
                  <p className="text-sm text-gray-600">
                    You still have access to recipe history. Upgrade anytime to resume generating recipes.
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
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
          {currentStep <= 4 && <ProgressBar />}
          <StepContent />
          {currentStep <= 4 && <NavigationButtons />}
        </div>
      </div>
    </div>
  );
}

export default RecipeGeneratorScreen;
