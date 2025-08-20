import React, { useState } from 'react';
import { authService } from '../services/auth';

const WelcomeOnboarding = ({ onComplete, onSkip }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [userPreferences, setUserPreferences] = useState({
    dietaryRestrictions: [],
    cuisinePreferences: [],
    cookingSkillLevel: '',
    householdSize: 1,
    weeklyBudget: '',
    favoriteIngredients: []
  });

  const steps = [
    {
      title: "Welcome to BuildYourSmartCart! 🛒",
      description: "Let's personalize your AI chef experience",
      component: "welcome"
    },
    {
      title: "Dietary Preferences 🥗",
      description: "Tell us about your dietary needs",
      component: "dietary"
    },
    {
      title: "Cuisine Preferences 🍽️",
      description: "What flavors do you love?",
      component: "cuisine"
    },
    {
      title: "Cooking Experience 👨‍🍳",
      description: "How comfortable are you in the kitchen?",
      component: "skill"
    },
    {
      title: "Household Setup 🏠",
      description: "Help us plan the right portions",
      component: "household"
    }
  ];

  const dietaryOptions = [
    'Vegetarian', 'Vegan', 'Gluten-Free', 'Keto', 'Paleo', 
    'Low-Carb', 'Dairy-Free', 'Nut-Free', 'Low-Sodium'
  ];

  const cuisineOptions = [
    'Italian', 'Mexican', 'Asian', 'Mediterranean', 'American',
    'Indian', 'Thai', 'French', 'Japanese', 'Middle Eastern'
  ];

  const skillLevels = [
    { value: 'beginner', label: 'Beginner - Simple recipes please!' },
    { value: 'intermediate', label: 'Intermediate - I can handle some complexity' },
    { value: 'advanced', label: 'Advanced - Bring on the challenge!' }
  ];

  const budgetRanges = [
    { value: 'budget', label: '$50-100/week - Budget-friendly' },
    { value: 'moderate', label: '$100-200/week - Moderate' },
    { value: 'premium', label: '$200+/week - Premium ingredients' }
  ];

  const handleDietaryChange = (option) => {
    const current = userPreferences.dietaryRestrictions;
    const updated = current.includes(option)
      ? current.filter(item => item !== option)
      : [...current, option];
    
    setUserPreferences({
      ...userPreferences,
      dietaryRestrictions: updated
    });
  };

  const handleCuisineChange = (option) => {
    const current = userPreferences.cuisinePreferences;
    const updated = current.includes(option)
      ? current.filter(item => item !== option)
      : [...current, option];
    
    setUserPreferences({
      ...userPreferences,
      cuisinePreferences: updated
    });
  };

  const savePreferences = async () => {
    try {
      // Save preferences to backend
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (user.id) {
        // Call API to save preferences
        const response = await fetch('/api/user/preferences', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            user_id: user.id,
            preferences: userPreferences
          }),
        });

        if (response.ok) {
          console.log('Preferences saved successfully');
        }
      }
      
      // Store preferences locally as backup
      localStorage.setItem('userPreferences', JSON.stringify(userPreferences));
      
      if (onComplete) {
        onComplete(userPreferences);
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      // Still continue even if save fails
      if (onComplete) {
        onComplete(userPreferences);
      }
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      savePreferences();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const renderStepContent = () => {
    const step = steps[currentStep];
    
    switch (step.component) {
      case 'welcome':
        return (
          <div className="text-center">
            <div className="text-6xl mb-6">🤖👨‍🍳</div>
            <h2 className="text-2xl font-bold mb-4">Meet Your AI Chef!</h2>
            <p className="text-gray-600 mb-6">
              I'll help you discover amazing recipes, plan your weekly meals, 
              and create smart shopping lists that fit your lifestyle.
            </p>
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-blue-700">
                ✨ This quick setup will personalize your experience in just 2 minutes!
              </p>
            </div>
          </div>
        );

      case 'dietary':
        return (
          <div>
            <h3 className="text-xl font-bold mb-4">Select your dietary preferences:</h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              {dietaryOptions.map(option => (
                <button
                  key={option}
                  onClick={() => handleDietaryChange(option)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    userPreferences.dietaryRestrictions.includes(option)
                      ? 'border-green-500 bg-green-50 text-green-700'
                      : 'border-gray-200 hover:border-green-300'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-500">Select all that apply</p>
          </div>
        );

      case 'cuisine':
        return (
          <div>
            <h3 className="text-xl font-bold mb-4">What cuisines do you enjoy?</h3>
            <div className="grid grid-cols-2 gap-3 mb-4">
              {cuisineOptions.map(option => (
                <button
                  key={option}
                  onClick={() => handleCuisineChange(option)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    userPreferences.cuisinePreferences.includes(option)
                      ? 'border-orange-500 bg-orange-50 text-orange-700'
                      : 'border-gray-200 hover:border-orange-300'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
            <p className="text-sm text-gray-500">Choose your favorites</p>
          </div>
        );

      case 'skill':
        return (
          <div>
            <h3 className="text-xl font-bold mb-4">What's your cooking skill level?</h3>
            <div className="space-y-3">
              {skillLevels.map(skill => (
                <button
                  key={skill.value}
                  onClick={() => setUserPreferences({
                    ...userPreferences,
                    cookingSkillLevel: skill.value
                  })}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    userPreferences.cookingSkillLevel === skill.value
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                >
                  {skill.label}
                </button>
              ))}
            </div>
          </div>
        );

      case 'household':
        return (
          <div>
            <h3 className="text-xl font-bold mb-6">Household Details</h3>
            
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                How many people are you cooking for?
              </label>
              <select
                value={userPreferences.householdSize}
                onChange={(e) => setUserPreferences({
                  ...userPreferences,
                  householdSize: parseInt(e.target.value)
                })}
                className="w-full p-3 border border-gray-300 rounded-lg"
              >
                {[1,2,3,4,5,6,7,8].map(num => (
                  <option key={num} value={num}>
                    {num} {num === 1 ? 'person' : 'people'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Weekly grocery budget:
              </label>
              <div className="space-y-2">
                {budgetRanges.map(budget => (
                  <button
                    key={budget.value}
                    onClick={() => setUserPreferences({
                      ...userPreferences,
                      weeklyBudget: budget.value
                    })}
                    className={`w-full p-3 rounded-lg border-2 text-left transition-all ${
                      userPreferences.weeklyBudget === budget.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                  >
                    {budget.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-2">
              {steps[currentStep].title}
            </h1>
            <p className="text-gray-600">
              {steps[currentStep].description}
            </p>
          </div>

          <div className="mb-8">
            {renderStepContent()}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center">
            <div>
              {currentStep > 0 && (
                <button
                  onClick={prevStep}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  ← Previous
                </button>
              )}
            </div>

            <div className="flex space-x-3">
              {onSkip && (
                <button
                  onClick={onSkip}
                  className="px-6 py-2 text-gray-500 hover:text-gray-700 transition-colors"
                >
                  Skip Setup
                </button>
              )}
              
              <button
                onClick={nextStep}
                className="px-8 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200"
              >
                {currentStep === steps.length - 1 ? 'Complete Setup 🎉' : 'Next →'}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            🔒 Your preferences are private and secure
          </p>
        </div>
      </div>
    </div>
  );
};

export default WelcomeOnboarding;