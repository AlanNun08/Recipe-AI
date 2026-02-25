import React, { useState, useEffect } from 'react';

const DashboardScreen = ({ 
  user, 
  userPreferences, 
  onLogout, 
  showNotification, 
  setCurrentScreen 
}) => {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

  useEffect(() => {
    loadDashboardData();
  }, [user]);

  const loadDashboardData = async () => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    try {
      // Load user stats and recent activity
      const response = await fetch(`${API}/api/user/dashboard/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      // Continue without stats if API fails
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      id: 'recipe-generator',
      title: '🍳 Generate Recipe',
      description: 'Create AI-powered recipes with Walmart shopping',
      gradient: 'from-orange-500 to-red-600',
      action: () => setCurrentScreen('recipe-generator')
    },
    {
      id: 'weekly-planner',
      title: '📅 Weekly Planner', 
      description: 'Plan your entire week with AI meal planning',
      gradient: 'from-green-500 to-blue-600',
      action: () => setCurrentScreen('weekly-recipes')
    },
    {
      id: 'starbucks-generator',
      title: '☕ Starbucks Drinks',
      description: 'Generate secret menu drinks with ordering scripts',
      gradient: 'from-green-600 to-green-700',
      action: () => setCurrentScreen('starbucks-generator')
    },
    {
      id: 'recipe-history',
      title: '📚 Recipe History',
      description: 'Browse your saved recipes and favorites',
      gradient: 'from-purple-500 to-pink-600',
      action: () => setCurrentScreen('recipe-history')
    },
    {
      id: 'tutorial',
      title: '📖 How to Use',
      description: 'Learn all features with interactive tutorials',
      gradient: 'from-blue-500 to-indigo-600',
      action: () => setCurrentScreen('tutorial')
    },
    {
      id: 'settings',
      title: '⚙️ Settings',
      description: 'Manage your account and preferences',
      gradient: 'from-gray-500 to-gray-600',
      action: () => setCurrentScreen('settings')
    }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-100 to-pink-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto mb-4"></div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">🔄 Loading your dashboard...</h2>
          <p className="text-gray-600">Getting everything ready for you!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-blue-100 to-pink-100 p-4">
      <div className="max-w-7xl mx-auto">
        
        {/* Header with Welcome Message */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8 text-center">
          <div className="text-8xl mb-4 animate-bounce">🤖</div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent mb-4">
            Welcome to BuildYourSmartCart!
          </h1>
          <p className="text-xl text-gray-600 mb-4">
            Your AI-powered recipe and grocery companion
          </p>
          {user && (
            <div className="bg-gradient-to-r from-green-100 to-blue-100 rounded-2xl p-4 mb-6 inline-block">
              <p className="text-lg font-semibold text-gray-800">
                👋 Hello, <span className="text-purple-600">{user.email}</span>!
              </p>
              <p className="text-gray-600">Ready to cook something amazing?</p>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-2xl shadow-xl p-6 text-center hover:shadow-2xl transition-shadow duration-300">
              <div className="text-4xl mb-3">🍳</div>
              <h3 className="text-2xl font-bold text-orange-600 mb-2">
                {dashboardStats.total_recipes || 0}
              </h3>
              <p className="text-gray-600 font-medium">Recipes Generated</p>
            </div>
            
            <div className="bg-white rounded-2xl shadow-xl p-6 text-center hover:shadow-2xl transition-shadow duration-300">
              <div className="text-4xl mb-3">☕</div>
              <h3 className="text-2xl font-bold text-green-600 mb-2">
                {dashboardStats.total_starbucks || 0}
              </h3>
              <p className="text-gray-600 font-medium">Starbucks Drinks</p>
            </div>
            
            <div className="bg-white rounded-2xl shadow-xl p-6 text-center hover:shadow-2xl transition-shadow duration-300">
              <div className="text-4xl mb-3">🛒</div>
              <h3 className="text-2xl font-bold text-blue-600 mb-2">
                {dashboardStats.total_shopping_lists || 0}
              </h3>
              <p className="text-gray-600 font-medium">Shopping Lists</p>
            </div>
            
            <div className="bg-white rounded-2xl shadow-xl p-6 text-center hover:shadow-2xl transition-shadow duration-300">
              <div className="text-4xl mb-3">⭐</div>
              <h3 className="text-2xl font-bold text-purple-600 mb-2">
                {user?.subscription?.status === 'trialing' ? 'Trial' : 'Premium'}
              </h3>
              <p className="text-gray-600 font-medium">Account Status</p>
            </div>
          </div>
        )}

        {/* Preferences Card */}
        {userPreferences && (
          <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8">
            <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
              <span className="text-3xl mr-3">🎯</span>
              Your Preferences
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {userPreferences.dietaryRestrictions?.length > 0 && (
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-2xl p-4">
                  <div className="text-2xl mb-2">🥗</div>
                  <div className="text-sm text-gray-600 mb-1">Dietary</div>
                  <div className="font-semibold text-gray-800">{userPreferences.dietaryRestrictions.join(', ')}</div>
                </div>
              )}
              {userPreferences.cuisinePreferences?.length > 0 && (
                <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-2xl p-4">
                  <div className="text-2xl mb-2">🍽️</div>
                  <div className="text-sm text-gray-600 mb-1">Cuisines</div>
                  <div className="font-semibold text-gray-800">{userPreferences.cuisinePreferences.join(', ')}</div>
                </div>
              )}
              {userPreferences.cookingSkillLevel && (
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-2xl p-4">
                  <div className="text-2xl mb-2">👨‍🍳</div>
                  <div className="text-sm text-gray-600 mb-1">Skill Level</div>
                  <div className="font-semibold text-gray-800">{userPreferences.cookingSkillLevel}</div>
                </div>
              )}
              {userPreferences.householdSize && (
                <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-2xl p-4">
                  <div className="text-2xl mb-2">🏠</div>
                  <div className="text-sm text-gray-600 mb-1">Household</div>
                  <div className="font-semibold text-gray-800">{userPreferences.householdSize} people</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Main Actions Grid */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8">
          <div className="text-center mb-8">
            <h3 className="text-3xl font-bold text-gray-800 mb-4 flex items-center justify-center">
              <span className="text-4xl mr-3 animate-bounce">🚀</span>
              What would you like to do today?
            </h3>
            <p className="text-gray-600 text-lg">Choose from our AI-powered features</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {quickActions.map((action) => (
              <button
                key={action.id}
                onClick={action.action}
                className={`group relative overflow-hidden bg-gradient-to-br ${action.gradient} rounded-3xl p-8 text-white shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300 text-left`}
              >
                {/* Background Pattern */}
                <div className="absolute inset-0 opacity-10">
                  <div className="absolute top-4 right-4 text-6xl">✨</div>
                  <div className="absolute bottom-4 left-4 text-4xl">🌟</div>
                </div>
                
                {/* Content */}
                <div className="relative z-10">
                  <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                    {action.title.split(' ')[0]}
                  </div>
                  <h4 className="text-xl font-bold mb-3 leading-tight">
                    {action.title.substring(action.title.indexOf(' ') + 1)}
                  </h4>
                  <p className="text-white/90 text-sm leading-relaxed mb-4">
                    {action.description}
                  </p>
                  <div className="flex items-center text-white/80 group-hover:text-white transition-colors duration-300">
                    <span className="text-sm font-medium mr-2">Get Started</span>
                    <span className="group-hover:translate-x-1 transition-transform duration-300">→</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer with Logout */}
        <div className="text-center">
          <div className="bg-white rounded-3xl shadow-2xl p-6 inline-block">
            <button 
              onClick={onLogout}
              className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-8 py-4 rounded-2xl font-bold text-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-300 flex items-center"
            >
              <span className="text-2xl mr-3">🚪</span>
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardScreen;
