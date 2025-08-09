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
    meal_type: ''
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecipe, setGeneratedRecipe] = useState(null);

  const cuisineOptions = [
    'Italian', 'Mexican', 'Chinese', 'Indian', 'French', 'Thai', 'Japanese',
    'Mediterranean', 'American', 'Korean', 'Greek', 'Spanish'
  ];

  const difficultyOptions = [
    'Easy', 'Medium', 'Hard'
  ];

  const mealTypeOptions = [
    'Breakfast', 'Lunch', 'Dinner', 'Snack', 'Dessert', 'Appetizer'
  ];

  const prepTimeOptions = [
    '15 minutes', '30 minutes', '45 minutes', '1 hour', '1+ hours'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const generateRecipe = async (e) => {
    e.preventDefault();
    setIsGenerating(true);

    try {
      console.log('🍳 Generating recipe with data:', formData);

      const response = await axios.post(`${API}/api/recipes/generate`, {
        user_id: user.id,
        ...formData,
        dietary_restrictions: formData.dietary_restrictions || 'None',
        ingredients: formData.ingredients || 'Surprise me!'
      });

      console.log('✅ Recipe generated:', response.data);
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
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - Recipe Generation Form */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-8 flex items-center">
              <span className="mr-3 text-4xl">⚙️</span>
              Recipe Preferences
            </h2>

            <form onSubmit={generateRecipe} className="space-y-6">
              {/* Cuisine Type */}
              <div>
                <label className="block text-lg font-bold text-gray-700 mb-3">
                  🌍 Cuisine Type
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
                  🍽️ Meal Type
                </label>
                <select
                  name="meal_type"
                  value={formData.meal_type}
                  onChange={handleInputChange}
                  required
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50"
                >
                  <option value="">Select meal type...</option>
                  {mealTypeOptions.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-lg font-bold text-gray-700 mb-3">
                  📊 Difficulty Level
                </label>
                <select
                  name="difficulty"
                  value={formData.difficulty}
                  onChange={handleInputChange}
                  required
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50"
                >
                  <option value="">Select difficulty...</option>
                  {difficultyOptions.map(diff => (
                    <option key={diff} value={diff}>{diff}</option>
                  ))}
                </select>
              </div>

              {/* Prep Time */}
              <div>
                <label className="block text-lg font-bold text-gray-700 mb-3">
                  ⏱️ Preparation Time
                </label>
                <select
                  name="prep_time"
                  value={formData.prep_time}
                  onChange={handleInputChange}
                  required
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50"
                >
                  <option value="">Select prep time...</option>
                  {prepTimeOptions.map(time => (
                    <option key={time} value={time}>{time}</option>
                  ))}
                </select>
              </div>

              {/* Dietary Restrictions */}
              <div>
                <label className="block text-lg font-bold text-gray-700 mb-3">
                  🥗 Dietary Restrictions (Optional)
                </label>
                <input
                  type="text"
                  name="dietary_restrictions"
                  value={formData.dietary_restrictions}
                  onChange={handleInputChange}
                  placeholder="e.g., Vegetarian, Vegan, Gluten-free, Keto..."
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50"
                />
              </div>

              {/* Specific Ingredients */}
              <div>
                <label className="block text-lg font-bold text-gray-700 mb-3">
                  🥘 Specific Ingredients (Optional)
                </label>
                <textarea
                  name="ingredients"
                  value={formData.ingredients}
                  onChange={handleInputChange}
                  placeholder="e.g., chicken, tomatoes, basil... or leave blank for surprise ingredients!"
                  rows="3"
                  className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-gray-50 resize-none"
                />
              </div>

              {/* Generate Button */}
              <button
                type="submit"
                disabled={isGenerating}
                className={`w-full font-bold py-4 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center text-lg shadow-lg ${
                  isGenerating
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
                    : 'bg-gradient-to-r from-orange-500 to-red-600 text-white hover:shadow-xl transform hover:-translate-y-1 hover:from-orange-600 hover:to-red-700'
                }`}
              >
                {isGenerating ? (
                  <>
                    <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                    Creating Your Recipe...
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

          {/* Right Column - Generated Recipe Preview */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-8 flex items-center">
              <span className="mr-3 text-4xl">🎉</span>
              Generated Recipe
            </h2>

            {generatedRecipe ? (
              <div className="space-y-6">
                {/* Recipe Header */}
                <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-6 border border-green-200">
                  <h3 className="text-2xl font-bold text-gray-800 mb-3">{generatedRecipe.title}</h3>
                  <p className="text-gray-600 leading-relaxed mb-4">{generatedRecipe.description}</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl mb-1">⏱️</div>
                      <div className="text-sm text-gray-600">Prep Time</div>
                      <div className="font-bold">{generatedRecipe.prep_time || 'N/A'}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl mb-1">👥</div>
                      <div className="text-sm text-gray-600">Servings</div>
                      <div className="font-bold">{generatedRecipe.servings || 'N/A'}</div>
                    </div>
                  </div>
                </div>

                {/* Ingredients Preview */}
                {generatedRecipe.ingredients && (
                  <div className="bg-gray-50 rounded-2xl p-6">
                    <h4 className="font-bold text-gray-800 mb-4 flex items-center">
                      <span className="mr-2">🥘</span>
                      Ingredients ({generatedRecipe.ingredients.length})
                    </h4>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {generatedRecipe.ingredients.slice(0, 5).map((ingredient, index) => (
                        <div key={index} className="flex items-center text-sm text-gray-700">
                          <span className="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                          {ingredient}
                        </div>
                      ))}
                      {generatedRecipe.ingredients.length > 5 && (
                        <div className="text-sm text-gray-500 italic">
                          +{generatedRecipe.ingredients.length - 5} more ingredients...
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* View Full Recipe Button */}
                <button
                  onClick={viewRecipeDetail}
                  className="w-full bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold py-4 px-6 rounded-2xl hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
                >
                  <span className="mr-3 text-2xl">👀</span>
                  View Full Recipe with Walmart Shopping
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-6">🍳</div>
                <h3 className="text-xl font-bold text-gray-800 mb-4">Ready to Create?</h3>
                <p className="text-gray-600 leading-relaxed mb-6">
                  Fill out the form on the left to generate your personalized recipe with AI.
                </p>
                <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-6 border border-orange-200">
                  <div className="text-orange-600 font-medium text-sm">
                    💡 Your generated recipe will include step-by-step instructions and a complete Walmart shopping list with real products and pricing!
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

export default RecipeGeneratorScreen;