import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Starbucks Secret Menu Generator Screen with Community Features
const StarbucksGeneratorScreen = ({ showNotification, setCurrentScreen, user, API }) => {
  const [drinkType, setDrinkType] = useState('');
  const [flavorInspiration, setFlavorInspiration] = useState('');
  const [generatedDrink, setGeneratedDrink] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showCopySuccess, setShowCopySuccess] = useState(false);
  
  // New state for community features
  const [currentTab, setCurrentTab] = useState('generator'); // generator, curated, community
  const [curatedRecipes, setCuratedRecipes] = useState([]);
  const [communityRecipes, setCommunityRecipes] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [isLoadingRecipes, setIsLoadingRecipes] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareFormData, setShareFormData] = useState({
    recipe_name: '',
    description: '',
    ingredients: ['', '', ''],
    order_instructions: '',
    category: 'frappuccino',
    tags: [],
    difficulty_level: 'easy',
    image_base64: null
  });
  const [isSharing, setIsSharing] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);

  const drinkTypes = [
    { value: 'frappuccino', label: 'Frappuccino', emoji: '🥤' },
    { value: 'refresher', label: 'Refresher', emoji: '🧊' },
    { value: 'lemonade', label: 'Lemonade', emoji: '🍋' },
    { value: 'iced_matcha_latte', label: 'Iced Matcha Latte', emoji: '🍵' },
    { value: 'random', label: 'Surprise Me!', emoji: '🎲' }
  ];

  const categories = [
    { value: 'all', label: 'All Recipes', emoji: '🌟' },
    { value: 'frappuccino', label: 'Frappuccino', emoji: '🥤' },
    { value: 'refresher', label: 'Refresher', emoji: '🧊' },
    { value: 'lemonade', label: 'Lemonade', emoji: '🍋' },
    { value: 'iced_matcha_latte', label: 'Iced Matcha', emoji: '🍵' },
    { value: 'random', label: 'Other', emoji: '🎲' }
  ];

  // Load curated and community recipes
  useEffect(() => {
    if (currentTab === 'curated' || currentTab === 'community') {
      loadRecipes();
    }
  }, [currentTab, selectedCategory]);

  const loadRecipes = async () => {
    setIsLoadingRecipes(true);
    try {
      if (currentTab === 'curated') {
        const response = await axios.get(`${API}/api/curated-starbucks-recipes?category=${selectedCategory}`);
        setCuratedRecipes(response.data.recipes || []);
      } else if (currentTab === 'community') {
        const response = await axios.get(`${API}/api/shared-recipes?category=${selectedCategory}&limit=20`);
        setCommunityRecipes(response.data.recipes || []);
      }
    } catch (error) {
      console.error('Error loading recipes:', error);
      showNotification('Failed to load recipes', 'error');
    } finally {
      setIsLoadingRecipes(false);
    }
  };

  const generateDrink = async () => {
    if (!drinkType) {
      showNotification('Please select a drink type!', 'error');
      return;
    }

    setIsGenerating(true);
    
    try {
      const response = await axios.post(`${API}/api/generate-starbucks-drink`, {
        user_id: user?.id || 'demo_user',
        drink_type: drinkType,
        flavor_inspiration: flavorInspiration || null
      });

      setGeneratedDrink(response.data);
      showNotification('🎉 Your secret menu drink is ready!', 'success');
    } catch (error) {
      console.error('Error generating drink:', error);
      showNotification('Failed to generate drink. Please try again.', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const copyOrderScript = (orderScript) => {
    if (orderScript) {
      navigator.clipboard.writeText(orderScript);
      setShowCopySuccess(true);
      setTimeout(() => setShowCopySuccess(false), 2000);
      showNotification('📋 Order script copied to clipboard!', 'success');
    }
  };

  const shareDrink = (drink) => {
    const drinkName = drink.drink_name || drink.name || drink.recipe_name;
    const orderScript = drink.ordering_script || drink.order_instructions;
    const shareText = `Check out this amazing Starbucks secret menu drink: ${drinkName}! 🤩\n\nOrder it like this: "${orderScript}"\n\n#StarbucksSecretMenu #DrinkHack`;
    
    if (navigator.share) {
      navigator.share({
        title: `${drinkName} - Starbucks Secret Menu`,
        text: shareText,
        url: window.location.href
      });
    } else {
      navigator.clipboard.writeText(shareText);
      showNotification('📱 Drink details copied for sharing!', 'success');
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        showNotification('Image size should be less than 5MB', 'error');
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target.result;
        setShareFormData(prev => ({ ...prev, image_base64: base64 }));
        setImagePreview(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const shareRecipe = async () => {
    if (!user?.id) {
      showNotification('Please sign in to share recipes', 'error');
      return;
    }

    if (!shareFormData.recipe_name || !shareFormData.description) {
      showNotification('Please fill in recipe name and description', 'error');
      return;
    }

    const nonEmptyIngredients = shareFormData.ingredients.filter(ing => ing.trim());
    if (nonEmptyIngredients.length < 2) {
      showNotification('Please add at least 2 ingredients', 'error');
      return;
    }

    setIsSharing(true);
    try {
      await axios.post(`${API}/api/share-recipe?user_id=${user.id}`, {
        ...shareFormData,
        ingredients: nonEmptyIngredients,
        tags: shareFormData.tags.filter(tag => tag.trim())
      });

      showNotification('🎉 Recipe shared successfully!', 'success');
      setShowShareModal(false);
      setShareFormData({
        recipe_name: '',
        description: '',
        ingredients: ['', '', ''],
        order_instructions: '',
        category: 'frappuccino',
        tags: [],
        difficulty_level: 'easy',
        image_base64: null
      });
      setImagePreview(null);
      
      // Reload community recipes if on that tab
      if (currentTab === 'community') {
        loadRecipes();
      }
    } catch (error) {
      console.error('Error sharing recipe:', error);
      showNotification('Failed to share recipe. Please try again.', 'error');
    } finally {
      setIsSharing(false);
    }
  };

  const likeRecipe = async (recipeId) => {
    if (!user?.id) {
      showNotification('Please sign in to like recipes', 'error');
      return;
    }

    try {
      const response = await axios.post(`${API}/api/like-recipe`, {
        recipe_id: recipeId,
        user_id: user.id
      });

      // Update the recipe in the local state
      setCommunityRecipes(prev => prev.map(recipe => 
        recipe.id === recipeId 
          ? {
              ...recipe,
              likes_count: response.data.likes_count,
              liked_by_users: response.data.action === 'liked' 
                ? [...(recipe.liked_by_users || []), user.id]
                : (recipe.liked_by_users || []).filter(uid => uid !== user.id)
            }
          : recipe
      ));

      showNotification(`Recipe ${response.data.action}! ❤️`, 'success');
    } catch (error) {
      console.error('Error liking recipe:', error);
      showNotification('Failed to like recipe', 'error');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 p-4 relative overflow-hidden">
      {/* Magical Background Elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-4 h-4 bg-yellow-400 rounded-full animate-pulse"></div>
        <div className="absolute top-20 right-20 w-6 h-6 bg-pink-400 rounded-full animate-bounce"></div>
        <div className="absolute bottom-20 left-20 w-5 h-5 bg-blue-400 rounded-full animate-ping"></div>
        <div className="absolute bottom-10 right-10 w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
        <div className="absolute top-1/2 left-1/4 w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
        <div className="absolute top-1/3 right-1/3 w-4 h-4 bg-orange-400 rounded-full animate-ping"></div>
      </div>
      
      <div className="max-w-6xl mx-auto relative z-10">
        
        {/* Enhanced Header */}
        <div className="text-center mb-8">
          <div className="text-8xl mb-4 animate-bounce">☕</div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-green-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">
            ✨ Starbucks Secret Menu ✨
          </h1>
          <p className="text-xl text-gray-700 font-medium">Generate magical drinks, discover viral hacks, and share your creations!</p>
          <div className="flex justify-center mt-4 space-x-2">
            <span className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full text-sm font-bold animate-pulse">
              🌟 AI-Powered
            </span>
            <span className="px-4 py-2 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full text-sm font-bold animate-pulse">
              🚀 Viral Ready
            </span>
          </div>
        </div>

        {/* Enhanced Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-3xl shadow-2xl p-3 flex space-x-3 border-4 border-gradient-to-r from-purple-200 to-pink-200">
            <button
              onClick={() => setCurrentTab('generator')}
              className={`px-8 py-4 rounded-2xl font-bold transition-all duration-300 transform hover:scale-105 ${
                currentTab === 'generator'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="text-2xl mr-2">🎨</span>
              Generator
            </button>
            
            <button
              onClick={() => setCurrentTab('curated')}
              className={`px-8 py-4 rounded-2xl font-bold transition-all duration-300 transform hover:scale-105 ${
                currentTab === 'curated'
                  ? 'bg-gradient-to-r from-green-500 to-blue-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="text-2xl mr-2">⭐</span>
              Curated
            </button>
            
            <button
              onClick={() => setCurrentTab('community')}
              className={`px-8 py-4 rounded-2xl font-bold transition-all duration-300 transform hover:scale-105 ${
                currentTab === 'community'
                  ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="text-2xl mr-2">👥</span>
              Community
            </button>
          </div>
        </div>

        {/* AI Generator Tab */}
        {currentTab === 'generator' && (
          <>
            {/* Enhanced Generator Form */}
            <div className="bg-white rounded-3xl shadow-2xl p-10 mb-8 border-4 border-gradient-to-r from-purple-200 to-pink-200">
              <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-8 text-center">
                ✨ Create Your Magical Drink ✨
              </h2>
              
              {/* Enhanced Drink Type Selection */}
              <div className="mb-8">
                <label className="block text-lg font-bold text-gray-700 mb-4 text-center">
                  🎯 Choose Your Drink Adventure
                </label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {drinkTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setDrinkType(type.value)}
                      className={`p-6 rounded-2xl border-3 transition-all duration-300 transform hover:scale-105 hover:shadow-lg ${
                        drinkType === type.value 
                          ? 'border-purple-500 bg-gradient-to-br from-purple-100 to-pink-100 text-purple-700 shadow-lg scale-105' 
                          : 'border-gray-200 hover:border-purple-300 text-gray-700 hover:bg-gradient-to-br hover:from-purple-50 hover:to-pink-50'
                      }`}
                    >
                      <div className="text-4xl mb-2 animate-bounce">{type.emoji}</div>
                      <div className="font-bold text-sm">{type.label}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Enhanced Flavor Inspiration */}
              <div className="mb-8">
                <label className="block text-lg font-bold text-gray-700 mb-4 text-center">
                  🌟 Add Your Flavor Magic (Optional)
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={flavorInspiration}
                    onChange={(e) => setFlavorInspiration(e.target.value)}
                    placeholder='e.g., "tres leches", "ube", "mango tajin", "birthday cake", "cotton candy"'
                    className="w-full px-6 py-4 border-3 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 text-lg bg-gradient-to-r from-purple-50 to-pink-50 placeholder-purple-400 transition-all duration-300"
                  />
                  <div className="absolute right-4 top-1/2 transform -translate-y-1/2 text-2xl animate-pulse">
                    ✨
                  </div>
                </div>
                <p className="text-sm text-purple-600 mt-2 text-center font-medium">
                  🎨 Let your creativity flow! Add any flavor inspiration to make your drink unique
                </p>
              </div>

              {/* Magical Generate Button */}
              <div className="text-center">
                <button
                  onClick={generateDrink}
                  disabled={isGenerating}
                  className={`px-12 py-6 rounded-3xl font-bold text-xl transition-all duration-300 transform hover:scale-105 ${
                    isGenerating 
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 text-white shadow-2xl hover:shadow-3xl'
                  }`}
                >
                  {isGenerating ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-4 border-white mr-4"></div>
                      <span className="text-lg">🔮 Brewing Your Magical Creation...</span>
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      <span className="text-2xl mr-3 animate-bounce">🪄</span>
                      <span>Generate My Magical Drink</span>
                      <span className="text-2xl ml-3 animate-bounce">✨</span>
                    </span>
                  )}
                </button>
                
                {/* Magical sparkles around button */}
                <div className="relative mt-4">
                  <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 text-2xl animate-ping">⭐</div>
                  <div className="absolute -top-6 left-1/4 text-xl animate-bounce">💫</div>
                  <div className="absolute -top-6 right-1/4 text-xl animate-pulse">🌟</div>
                </div>
              </div>
            </div>

            {/* Generated Drink Display */}
            {generatedDrink && (
              <DrinkCard 
                drink={generatedDrink} 
                showFullDetails={true}
                onCopyOrder={() => copyOrderScript(generatedDrink.ordering_script)}
                onShare={() => shareDrink(generatedDrink)}
                onGenerateAnother={() => {
                  setGeneratedDrink(null);
                  setDrinkType('');
                  setFlavorInspiration('');
                }}
                onBackToDashboard={() => setCurrentScreen('dashboard')}
                showActionButtons={true}
              />
            )}
          </>
        )}

        {/* Curated & Community Recipes Tabs */}
        {(currentTab === 'curated' || currentTab === 'community') && (
          <>
            {/* Category Filter */}
            <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
              <div className="flex flex-wrap justify-between items-center gap-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-800">
                    {currentTab === 'curated' ? '📚 Curated Recipes' : '👥 Community Recipes'}
                  </h3>
                  <p className="text-gray-600">
                    {currentTab === 'curated' 
                      ? 'Hand-picked favorites from our team' 
                      : 'Amazing creations shared by our community'
                    }
                  </p>
                </div>
                
                {currentTab === 'community' && (
                  <button
                    onClick={() => setShowShareModal(true)}
                    className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-bold transition-all duration-200 shadow-lg hover:shadow-xl"
                  >
                    📸 Share Your Recipe
                  </button>
                )}
              </div>
              
              {/* Category Pills */}
              <div className="flex flex-wrap gap-2 mt-4">
                {categories.map((category) => (
                  <button
                    key={category.value}
                    onClick={() => setSelectedCategory(category.value)}
                    className={`px-4 py-2 rounded-full font-medium transition-all duration-200 ${
                      selectedCategory === category.value
                        ? 'bg-blue-500 text-white shadow-md'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {category.emoji} {category.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Recipes Grid */}
            {isLoadingRecipes ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading delicious recipes...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {(currentTab === 'curated' ? curatedRecipes : communityRecipes).map((recipe, index) => (
                  <RecipeCard
                    key={recipe.id || index}
                    recipe={recipe}
                    isCommunity={currentTab === 'community'}
                    onLike={currentTab === 'community' ? () => likeRecipe(recipe.id) : null}
                    isLiked={currentTab === 'community' && recipe.liked_by_users?.includes(user?.id)}
                    onCopyOrder={() => copyOrderScript(recipe.order_instructions || recipe.ordering_script)}
                    onShare={() => shareDrink(recipe)}
                    user={user}
                  />
                ))}
              </div>
            )}

            {(currentTab === 'curated' ? curatedRecipes : communityRecipes).length === 0 && !isLoadingRecipes && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">No recipes found</h3>
                <p className="text-gray-600">
                  {currentTab === 'curated' 
                    ? 'Try selecting a different category'
                    : 'Be the first to share a recipe in this category!'
                  }
                </p>
              </div>
            )}
          </>
        )}

        {/* Share Recipe Modal */}
        {showShareModal && (
          <ShareRecipeModal
            isOpen={showShareModal}
            onClose={() => setShowShareModal(false)}
            formData={shareFormData}
            setFormData={setShareFormData}
            onImageUpload={handleImageUpload}
            imagePreview={imagePreview}
            onShare={shareRecipe}
            isSharing={isSharing}
            categories={drinkTypes}
          />
        )}

        {/* Back Button */}
        <div className="text-center mt-8">
          <button
            onClick={() => setCurrentScreen('dashboard')}
            className="bg-gray-500 hover:bg-gray-600 text-white px-8 py-3 rounded-xl font-bold transition-all duration-200"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

// RecipeCard Component for displaying curated and community recipes
const RecipeCard = ({ 
  recipe, 
  isCommunity = false, 
  onLike, 
  isLiked = false, 
  onCopyOrder, 
  onShare, 
  user 
}) => {
  const recipeName = recipe.drink_name || recipe.name || recipe.recipe_name || "Secret Menu Drink";
  const description = recipe.description || recipe.vibe || "A delicious Starbucks creation";
  const orderScript = recipe.ordering_script || recipe.order_instructions || "Order instructions not available";
  const category = recipe.category || "unknown";
  const likesCount = recipe.likes_count || 0;
  const author = recipe.author || "Anonymous";
  const difficulty = recipe.difficulty_level || "medium";
  const tags = recipe.tags || [];
  
  // Get category emoji
  const getCategoryEmoji = (category) => {
    switch(category?.toLowerCase()) {
      case 'frappuccino': return '🥤';
      case 'refresher': return '🧊';
      case 'lemonade': return '🍋';
      case 'iced_matcha_latte': return '🍵';
      default: return '☕';
    }
  };
  
  // Get difficulty color
  const getDifficultyColor = (difficulty) => {
    switch(difficulty?.toLowerCase()) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const categoryEmoji = getCategoryEmoji(category);
  const difficultyColor = getDifficultyColor(difficulty);
  
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
      {/* Header */}
      <div className="text-center mb-4">
        <div className="text-4xl mb-2">{categoryEmoji}</div>
        <h3 className="text-xl font-bold text-gray-800 mb-1">{recipeName}</h3>
        <p className="text-gray-600 text-sm italic">"{description}"</p>
      </div>
      
      {/* Badges */}
      <div className="flex flex-wrap gap-2 mb-4 justify-center">
        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
          {category.charAt(0).toUpperCase() + category.slice(1)}
        </span>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${difficultyColor}`}>
          {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
        </span>
      </div>
      
      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-4 justify-center">
          {tags.slice(0, 3).map((tag, index) => (
            <span key={index} className="bg-gray-100 text-gray-700 px-2 py-1 rounded-full text-xs">
              #{tag}
            </span>
          ))}
        </div>
      )}
      
      {/* Order Script Preview */}
      <div className="mb-4">
        <div className="bg-yellow-50 p-3 rounded-lg border-l-4 border-yellow-400">
          <p className="text-gray-700 text-sm">
            {orderScript.length > 80 ? `${orderScript.substring(0, 80)}...` : orderScript}
          </p>
        </div>
      </div>
      
      {/* Community Info */}
      {isCommunity && (
        <div className="flex items-center justify-between mb-4 text-sm text-gray-600">
          <span>By {author}</span>
          <div className="flex items-center gap-4">
            <button
              onClick={onLike}
              className={`flex items-center gap-1 ${isLiked ? 'text-red-500' : 'text-gray-500'} hover:text-red-500`}
            >
              {isLiked ? '❤️' : '🤍'} {likesCount}
            </button>
          </div>
        </div>
      )}
      
      {/* Action Buttons */}
      <div className="flex gap-2 justify-center">
        <button
          onClick={onCopyOrder}
          className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        >
          📋 Copy Order
        </button>
        
        <button
          onClick={onShare}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200"
        >
          🔗 Share
        </button>
      </div>
    </div>
  );
};

// DrinkCard Component for displaying generated drinks
const DrinkCard = ({ 
  drink, 
  showFullDetails = true, 
  onCopyOrder, 
  onShare, 
  onGenerateAnother, 
  onBackToDashboard, 
  showActionButtons = true 
}) => {
  const [showFullScript, setShowFullScript] = useState(false);
  
  const drinkName = drink.drink_name || drink.name || drink.recipe_name || "Secret Menu Drink";
  const description = drink.description || drink.vibe || "A delicious Starbucks creation";
  const orderScript = drink.ordering_script || drink.order_instructions || "Order instructions not available";
  const category = drink.category || "unknown";
  const baseDrink = drink.base_drink || "";
  const modifications = drink.modifications || [];
  
  // Get category emoji
  const getCategoryEmoji = (category) => {
    switch(category?.toLowerCase()) {
      case 'frappuccino': return '🥤';
      case 'refresher': return '🧊';
      case 'lemonade': return '🍋';
      case 'iced_matcha_latte': return '🍵';
      default: return '☕';
    }
  };
  
  const categoryEmoji = getCategoryEmoji(category);
  
  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-6">
        <div className="text-6xl mb-4">{categoryEmoji}</div>
        <h2 className="text-3xl font-bold text-gray-800 mb-2">{drinkName}</h2>
        <p className="text-gray-600 text-lg italic">"{description}"</p>
        <div className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium mt-2">
          {category.charAt(0).toUpperCase() + category.slice(1)}
        </div>
      </div>
      
      {/* Ingredients */}
      {baseDrink && (
        <div className="mb-6">
          <h3 className="font-bold text-gray-800 mb-3">🥤 Base Drink</h3>
          <div className="bg-blue-50 p-3 rounded-lg">
            <span className="text-blue-800 font-medium">{baseDrink}</span>
          </div>
        </div>
      )}
      
      {modifications.length > 0 && (
        <div className="mb-6">
          <h3 className="font-bold text-gray-800 mb-3">✨ Modifications</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {modifications.map((mod, index) => (
              <div key={index} className="bg-purple-50 p-3 rounded-lg">
                <span className="text-purple-800">{mod}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Order Script */}
      <div className="mb-6">
        <h3 className="font-bold text-gray-800 mb-3">📝 How to Order</h3>
        <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-400">
          <p className="text-gray-700">
            {showFullScript ? orderScript : `${orderScript.substring(0, 120)}...`}
          </p>
          {orderScript.length > 120 && (
            <button 
              onClick={() => setShowFullScript(!showFullScript)}
              className="text-blue-600 hover:text-blue-800 text-sm mt-2"
            >
              {showFullScript ? 'Show less' : 'Show full script'}
            </button>
          )}
        </div>
      </div>
      
      {/* Action Buttons */}
      {showActionButtons && (
        <div className="flex flex-wrap gap-3 justify-center">
          <button
            onClick={onCopyOrder}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-xl font-bold transition-all duration-200 flex items-center gap-2"
          >
            📋 Copy Order
          </button>
          
          <button
            onClick={onShare}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-xl font-bold transition-all duration-200 flex items-center gap-2"
          >
            🔗 Share
          </button>
          
          {onGenerateAnother && (
            <button
              onClick={onGenerateAnother}
              className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-3 rounded-xl font-bold transition-all duration-200 flex items-center gap-2"
            >
              🎲 Generate Another
            </button>
          )}
          
          {onBackToDashboard && (
            <button
              onClick={onBackToDashboard}
              className="bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-bold transition-all duration-200 flex items-center gap-2"
            >
              🏠 Back to Dashboard
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default StarbucksGeneratorScreen;