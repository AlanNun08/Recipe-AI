import React, { useState } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

function RecipeGeneratorScreen({ user, onBack, showNotification, onViewRecipe }) {
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
  const [showAdvanced, setShowAdvanced] = useState(false);

  const cuisineOptions = [
    'Italian', 'Mexican', 'Chinese', 'Indian', 'French', 'Thai', 'Japanese',
    'Mediterranean', 'American', 'Korean', 'Greek', 'Spanish', 'Vietnamese', 'Lebanese'
  ];

  const difficultyOptions = [
    { value: 'easy', label: 'Easy', icon: '😊', desc: 'Quick & simple recipes' },
    { value: 'medium', label: 'Medium', icon: '🤔', desc: 'Some cooking skills needed' },
    { value: 'hard', label: 'Hard', icon: '👨‍🍳', desc: 'Advanced techniques required' }
  ];

  const mealTypeOptions = [
    { value: 'breakfast', label: 'Breakfast', icon: '🌅' },
    { value: 'lunch', label: 'Lunch', icon: '🥪' },
    { value: 'dinner', label: 'Dinner', icon: '🍽️' },
    { value: 'snack', label: 'Snack', icon: '🍿' },
    { value: 'dessert', label: 'Dessert', icon: '🍰' },
    { value: 'appetizer', label: 'Appetizer', icon: '🥗' }
  ];

  const prepTimeOptions = [
    '15 minutes', '30 minutes', '45 minutes', '1 hour', '1+ hours'
  ];

  const servingsOptions = [1, 2, 3, 4, 5, 6, 8, 10, 12];

  const popularDietaryRestrictions = [
    'Vegetarian', 'Vegan', 'Gluten-free', 'Keto', 'Paleo', 'Low-carb', 'Dairy-free', 'Nut-free'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleDietaryRestrictionClick = (restriction) => {
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

  const generateRecipe = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setGeneratedRecipe(null);

    try {
      const response = await axios.post(`${API}/api/recipes/generate`, {
        user_id: user.id,
        cuisine: formData.cuisine,
        meal_type: formData.meal_type,
        difficulty: formData.difficulty,
        prep_time: formData.prep_time,
        dietary_restrictions: formData.dietary_restrictions || '',
        ingredients: formData.ingredients || '',
        servings: parseInt(formData.servings) || 4
      });

      setGeneratedRecipe(response.data);
      showNotification('🎉 Recipe generated successfully!', 'success');

    } catch (error) {
      console.error('❌ Error generating recipe:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to generate recipe. Please try again.';
      showNotification(`❌ ${errorMessage}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const viewRecipeDetail = () => {
    if (generatedRecipe && onViewRecipe) {
      onViewRecipe(generatedRecipe.id, 'generated');
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
    setShowAdvanced(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
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
        </div>

        <div className="grid xl:grid-cols-3 gap-8">
          {/* Left Column - Recipe Generation Form */}
          <div className="xl:col-span-2">
            <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent flex items-center">
                  <span className="mr-3 text-4xl">⚙️</span>
                  Recipe Preferences
                </h2>
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all duration-200 flex items-center"
                >
                  <span className="mr-2">🔄</span>
                  Reset Form
                </button>
              </div>

              <form onSubmit={generateRecipe} className="space-y-6">
                {/* Essential Fields */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Cuisine Type */}
                  <div>
                    <label className="block text-lg font-bold text-gray-700 mb-3">
                      🌍 Cuisine Type *
                    </label>
                    <select
                      name="cuisine"
                      value={formData.cuisine}
                      onChange={handleInputChange}
                      required
                      className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50"
                    >
                      <option value="">Select a cuisine...</option>
                      {cuisineOptions.map(cuisine => (
                        <option key={cuisine} value={cuisine}>{cuisine}</option>
                      ))}
                    </select>
                  </div>

                  {/* Meal Type */}
                  <div>
                    <label className="block text-lg font-bold text-gray-700 mb-3">
                      🍽️ Meal Type *
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {mealTypeOptions.map(type => (
                        <button
                          key={type.value}
                          type="button"
                          onClick={() => setFormData(prev => ({ ...prev, meal_type: type.value }))}
                          className={`p-3 rounded-xl border-2 transition-all duration-200 flex flex-col items-center text-sm font-medium ${
                            formData.meal_type === type.value
                              ? 'border-orange-500 bg-orange-50 text-orange-700'
                              : 'border-gray-200 bg-gray-50 text-gray-600 hover:border-orange-300'
                          }`}
                        >
                          <span className="text-lg mb-1">{type.icon}</span>
                          {type.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Difficulty Level */}
                <div>
                  <label className="block text-lg font-bold text-gray-700 mb-3">
                    📊 Difficulty Level *
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    {difficultyOptions.map(diff => (
                      <button
                        key={diff.value}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, difficulty: diff.value }))}
                        className={`p-4 rounded-xl border-2 transition-all duration-200 text-center ${
                          formData.difficulty === diff.value
                            ? 'border-orange-500 bg-orange-50 text-orange-700'
                            : 'border-gray-200 bg-gray-50 text-gray-600 hover:border-orange-300'
                        }`}
                      >
                        <div className="text-2xl mb-2">{diff.icon}</div>
                        <div className="font-bold">{diff.label}</div>
                        <div className="text-xs text-gray-500 mt-1">{diff.desc}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Advanced Options Toggle */}
                <div className="border-t border-gray-200 pt-6">
                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex items-center text-orange-600 hover:text-orange-700 font-medium mb-4 transition-all duration-200"
                  >
                    <span className={`mr-2 transition-transform duration-200 ${showAdvanced ? 'rotate-90' : ''}`}>▶</span>
                    Advanced Options
                  </button>

                  {showAdvanced && (
                    <div className="space-y-6 bg-gray-50 rounded-xl p-6">
                      {/* Prep Time and Servings */}
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-lg font-bold text-gray-700 mb-3">
                            ⏱️ Maximum Prep Time
                          </label>
                          <select
                            name="prep_time"
                            value={formData.prep_time}
                            onChange={handleInputChange}
                            className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white"
                          >
                            <option value="">Any time</option>
                            {prepTimeOptions.map(time => (
                              <option key={time} value={time}>{time}</option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-lg font-bold text-gray-700 mb-3">
                            👥 Number of Servings
                          </label>
                          <select
                            name="servings"
                            value={formData.servings}
                            onChange={handleInputChange}
                            className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white"
                          >
                            {servingsOptions.map(num => (
                              <option key={num} value={num}>{num} serving{num > 1 ? 's' : ''}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      {/* Dietary Restrictions */}
                      <div>
                        <label className="block text-lg font-bold text-gray-700 mb-3">
                          🥗 Dietary Restrictions
                        </label>
                        <div className="flex flex-wrap gap-2 mb-4">
                          {popularDietaryRestrictions.map(restriction => (
                            <button
                              key={restriction}
                              type="button"
                              onClick={() => handleDietaryRestrictionClick(restriction)}
                              className={`px-3 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                                formData.dietary_restrictions.includes(restriction)
                                  ? 'bg-green-100 text-green-700 border-2 border-green-300'
                                  : 'bg-gray-100 text-gray-600 border-2 border-gray-200 hover:border-green-300'
                              }`}
                            >
                              {restriction}
                            </button>
                          ))}
                        </div>
                        <input
                          type="text"
                          name="dietary_restrictions"
                          value={formData.dietary_restrictions}
                          onChange={handleInputChange}
                          placeholder="Custom dietary restrictions (comma separated)"
                          className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white"
                        />
                      </div>

                      {/* Specific Ingredients */}
                      <div>
                        <label className="block text-lg font-bold text-gray-700 mb-3">
                          🥘 Specific Ingredients to Include
                        </label>
                        <textarea
                          name="ingredients"
                          value={formData.ingredients}
                          onChange={handleInputChange}
                          placeholder="e.g., chicken, tomatoes, basil, mushrooms... (comma separated)"
                          rows="3"
                          className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white resize-none"
                        />
                        <p className="text-sm text-gray-500 mt-2">
                          💡 Leave blank for surprise ingredients, or specify what you have on hand
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Generate Button */}
                <button
                  type="submit"
                  disabled={isGenerating || !formData.cuisine || !formData.meal_type || !formData.difficulty}
                  className={`w-full font-bold py-5 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center text-lg shadow-lg ${
                    isGenerating || !formData.cuisine || !formData.meal_type || !formData.difficulty
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
              </form>
            </div>
          </div>

          {/* Right Column - Generated Recipe Preview */}
          <div className="xl:col-span-1">
            <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100 sticky top-6">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-8 flex items-center">
                <span className="mr-3 text-4xl">🎉</span>
                Generated Recipe
              </h2>

              {generatedRecipe ? (
                <div className="space-y-6">
                  {/* Recipe Header */}
                  <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-6 border border-green-200">
                    <h3 className="text-2xl font-bold text-gray-800 mb-3 leading-tight">
                      {generatedRecipe.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed mb-4">
                      {generatedRecipe.description}
                    </p>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center bg-white rounded-xl p-3">
                        <div className="text-2xl mb-1">⏱️</div>
                        <div className="text-xs text-gray-500">Prep Time</div>
                        <div className="font-bold text-gray-800">
                          {generatedRecipe.prep_time ? `${generatedRecipe.prep_time} min` : 'N/A'}
                        </div>
                      </div>
                      <div className="text-center bg-white rounded-xl p-3">
                        <div className="text-2xl mb-1">👥</div>
                        <div className="text-xs text-gray-500">Servings</div>
                        <div className="font-bold text-gray-800">
                          {generatedRecipe.servings || formData.servings || '4'}
                        </div>
                      </div>
                    </div>

                    {generatedRecipe.cook_time && (
                      <div className="mt-4 text-center bg-white rounded-xl p-3">
                        <div className="text-2xl mb-1">🔥</div>
                        <div className="text-xs text-gray-500">Cook Time</div>
                        <div className="font-bold text-gray-800">
                          {generatedRecipe.cook_time} min
                        </div>
                      </div>
                    )}

                    {generatedRecipe.calories_per_serving && (
                      <div className="mt-4 text-center bg-white rounded-xl p-3">
                        <div className="text-2xl mb-1">🔥</div>
                        <div className="text-xs text-gray-500">Calories per Serving</div>
                        <div className="font-bold text-gray-800">
                          {generatedRecipe.calories_per_serving}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Ingredients Preview */}
                  {generatedRecipe.ingredients && (
                    <div className="bg-amber-50 rounded-2xl p-6 border border-amber-200">
                      <h4 className="font-bold text-gray-800 mb-4 flex items-center">
                        <span className="mr-2">🥘</span>
                        Ingredients ({generatedRecipe.ingredients.length})
                      </h4>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {generatedRecipe.ingredients.slice(0, 8).map((ingredient, index) => (
                          <div key={index} className="flex items-start text-sm text-gray-700">
                            <span className="w-2 h-2 bg-amber-500 rounded-full mr-3 mt-2 flex-shrink-0"></span>
                            <span className="leading-relaxed">{ingredient}</span>
                          </div>
                        ))}
                        {generatedRecipe.ingredients.length > 8 && (
                          <div className="text-sm text-gray-500 italic pl-5">
                            +{generatedRecipe.ingredients.length - 8} more ingredients...
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Instructions Preview */}
                  {generatedRecipe.instructions && (
                    <div className="bg-blue-50 rounded-2xl p-6 border border-blue-200">
                      <h4 className="font-bold text-gray-800 mb-4 flex items-center">
                        <span className="mr-2">📋</span>
                        Instructions ({generatedRecipe.instructions.length} steps)
                      </h4>
                      <div className="space-y-3 max-h-40 overflow-y-auto">
                        {generatedRecipe.instructions.slice(0, 4).map((instruction, index) => (
                          <div key={index} className="flex items-start text-sm text-gray-700">
                            <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5 flex-shrink-0">
                              {index + 1}
                            </span>
                            <span className="leading-relaxed">{instruction}</span>
                          </div>
                        ))}
                        {generatedRecipe.instructions.length > 4 && (
                          <div className="text-sm text-gray-500 italic pl-9">
                            +{generatedRecipe.instructions.length - 4} more steps...
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Shopping List Preview */}
                  {generatedRecipe.shopping_list && (
                    <div className="bg-purple-50 rounded-2xl p-6 border border-purple-200">
                      <h4 className="font-bold text-gray-800 mb-4 flex items-center">
                        <span className="mr-2">🛒</span>
                        Shopping List ({generatedRecipe.shopping_list.length} items)
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {generatedRecipe.shopping_list.slice(0, 10).map((item, index) => (
                          <span key={index} className="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full font-medium">
                            {item}
                          </span>
                        ))}
                        {generatedRecipe.shopping_list.length > 10 && (
                          <span className="px-3 py-1 bg-gray-100 text-gray-500 text-sm rounded-full">
                            +{generatedRecipe.shopping_list.length - 10} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    <button
                      onClick={viewRecipeDetail}
                      className="w-full bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold py-4 px-6 rounded-2xl hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
                    >
                      <span className="mr-3 text-2xl">👀</span>
                      View Full Recipe with Walmart Shopping
                    </button>

                    <button
                      onClick={() => setGeneratedRecipe(null)}
                      className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-3 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center"
                    >
                      <span className="mr-2 text-lg">🔄</span>
                      Generate New Recipe
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-6 opacity-50">🍳</div>
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Ready to Create?</h3>
                  <p className="text-gray-600 leading-relaxed mb-6">
                    Fill out the form to generate your personalized recipe with AI.
                  </p>
                  
                  {/* Progress Indicator */}
                  <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-6 border border-orange-200">
                    <div className="text-orange-600 font-medium text-sm mb-4">
                      💡 Recipe Generation Progress
                    </div>
                    <div className="space-y-2">
                      <div className={`flex items-center text-sm ${formData.cuisine ? 'text-green-600' : 'text-gray-400'}`}>
                        <span className="mr-2">{formData.cuisine ? '✅' : '⭕'}</span>
                        Cuisine selected
                      </div>
                      <div className={`flex items-center text-sm ${formData.meal_type ? 'text-green-600' : 'text-gray-400'}`}>
                        <span className="mr-2">{formData.meal_type ? '✅' : '⭕'}</span>
                        Meal type chosen
                      </div>
                      <div className={`flex items-center text-sm ${formData.difficulty ? 'text-green-600' : 'text-gray-400'}`}>
                        <span className="mr-2">{formData.difficulty ? '✅' : '⭕'}</span>
                        Difficulty set
                      </div>
                    </div>
                    {formData.cuisine && formData.meal_type && formData.difficulty && (
                      <div className="mt-4 text-green-600 font-medium text-sm">
                        🎉 Ready to generate! Click the button below.
                      </div>
                    )}
                  </div>

                  <div className="mt-6 bg-blue-50 rounded-2xl p-6 border border-blue-200">
                    <div className="text-blue-600 font-medium text-sm">
                      ✨ Your generated recipe will include step-by-step instructions and a complete Walmart shopping list with real products and pricing!
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RecipeGeneratorScreen;