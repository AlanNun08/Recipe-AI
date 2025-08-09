import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import StarbucksGeneratorScreen from './components/StarbucksGeneratorScreen';
import WelcomeOnboarding from './components/WelcomeOnboarding';
import TutorialScreen from './components/TutorialScreen';
import SubscriptionScreen from './components/SubscriptionScreen';
import SubscriptionSuccess from './components/SubscriptionSuccess';
import SubscriptionGate from './components/SubscriptionGate';
import WeeklyRecipesScreen from './components/WeeklyRecipesScreen';
import TrialStatusBanner from './components/TrialStatusBanner';
import RecipeDetailScreen from './components/RecipeDetailScreen';
import RecipeGeneratorScreen from './components/RecipeGeneratorScreen';
import RecipeHistoryScreen from './components/RecipeHistoryScreen';

function App() {
  // BUILDYOURSMARTCART - PRODUCTION VERSION
  
  // API Configuration - Debug version
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Environment variables configured

  // Simple cache clearing (no excessive logging) - ONLY CLEAR CACHES, NOT AUTH DATA
  useEffect(() => {
    const clearCaches = async () => {
      try {
        // Clear service worker caches
        if ('caches' in window) {
          const cacheNames = await caches.keys();
          await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
          );
        }
        
        // DON'T clear auth storage on app load - let user stay logged in
        // localStorage.removeItem('authToken');
        // localStorage.removeItem('userSession');
        // localStorage.removeItem('user_auth_data');
        
      } catch (error) {
        // Silent error handling
      }
    };
    
    // Clear caches once on app load
    clearCaches();
  }, []);

  const [currentScreen, setCurrentScreen] = useState('landing');
  const [user, setUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [userRecipes, setUserRecipes] = useState([]);
  const [loadingRecipes, setLoadingRecipes] = useState(false);
  const [generatingRecipe, setGeneratingRecipe] = useState(false);
  const [notification, setNotification] = useState(null);
  const [pendingVerificationEmail, setPendingVerificationEmail] = useState(null);
  const [currentRecipeId, setCurrentRecipeId] = useState(null); // NEW: For recipe detail view
  const [currentRecipeSource, setCurrentRecipeSource] = useState('weekly'); // NEW: Track recipe source
  const [pendingResetEmail, setPendingResetEmail] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  
  // Subscription states
  const [showSubscriptionScreen, setShowSubscriptionScreen] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);

  // Enhanced user session management functions
  const clearUserSession = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('userSession');
    localStorage.removeItem('authToken');
    localStorage.removeItem('ai_chef_user'); // Keep compatibility with existing code
  };

  const setUserWithSession = (userData) => {
    if (userData) {
      // Save to both new and legacy localStorage keys for compatibility
      const userDataToSave = {
        ...userData,
        lastLoginTime: Date.now(),
        sessionExpiry: Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days
      };
      
      localStorage.setItem('user', JSON.stringify(userDataToSave));
      localStorage.setItem('ai_chef_user', JSON.stringify(userDataToSave)); // Legacy compatibility
      localStorage.setItem('userSession', JSON.stringify({
        userId: userData.id,
        email: userData.email,
        first_name: userData.first_name,
        is_verified: userData.is_verified,
        loginTime: Date.now(),
        sessionExpiry: Date.now() + (7 * 24 * 60 * 60 * 1000) // 7 days
      }));
      setUser(userDataToSave);
      
      // Auto-redirect to dashboard for verified users
      if (userData.is_verified && (currentScreen === 'landing' || currentScreen === 'login' || currentScreen === 'register')) {
        setCurrentScreen('dashboard');
      }
    } else {
      // Clear session
      clearUserSession();
      setUser(null);
    }
  };

  const loadUserSession = () => {
    try {
      const savedUser = localStorage.getItem('ai_chef_user');
      if (savedUser) {
        const userData = JSON.parse(savedUser);
        
        // Check if session is expired (7 days)
        const sessionExpiry = userData.sessionExpiry || (userData.lastLoginTime + (7 * 24 * 60 * 60 * 1000));
        if (Date.now() > sessionExpiry) {
          // Session expired, clear it
          clearUserSession();
          setIsLoadingAuth(false);
          return;
        }
        
        // Restore user session
        setUser(userData);
        // Only set to dashboard if we're on landing page or if currentScreen is a protected route
        if (currentScreen === 'landing' || !['landing', 'register', 'verify-email', 'login', 'forgot-password', 'reset-password'].includes(currentScreen)) {
          // Set screen to dashboard only if user is verified
          if (userData.is_verified) {
            setCurrentScreen('dashboard');
          } else {
            // User is not verified, send them to verify email screen
            setPendingVerificationEmail(userData.email);
            setCurrentScreen('verify-email');
          }
        }
      } else {
        // No saved session found
      }
    } catch (error) {
      // Failed to restore session
      localStorage.removeItem('ai_chef_user');
    } finally {
      setIsLoadingAuth(false);
    }
  };

  // Load user session from localStorage on app start - PRODUCTION FIX
  useEffect(() => {
    // Load user session after a short delay to ensure cache clearing is done
    const timer = setTimeout(loadUserSession, 100);
    return () => clearTimeout(timer);
  }, []); // Only run once on mount

  // Monitor user state changes and save to localStorage
  useEffect(() => {
    if (user) {
      try {
        localStorage.setItem('ai_chef_user', JSON.stringify(user));
        // User session saved
      } catch (error) {
        // Failed to save session
      }
    }
  }, [user]); // Save whenever user changes

  // Check for subscription success URL parameters
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId && currentScreen !== 'subscription-success') {
      setCurrentScreen('subscription-success');
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Check if user has completed onboarding
  const checkOnboardingStatus = () => {
    if (user?.id) {
      const isOnboarded = localStorage.getItem(`user_${user.id}_onboarded`);
      return isOnboarded === 'true';
    }
    return false;
  };

  // Show onboarding for new users
  useEffect(() => {
    if (user && !checkOnboardingStatus() && currentScreen === 'dashboard') {
      setCurrentScreen('welcome-onboarding');
    }
  }, [user, currentScreen]);

  // Debug logging for user state changes
  // Debug user state changes (for development only)
  useEffect(() => {
    if (user) {
      // User logged in successfully
    }
  }, [user, currentScreen]);

  // Test backend connectivity
  const testBackendConnection = async () => {
    try {
      const response = await axios.get(`${API}/api/health`, { timeout: 5000 });
      return response.status === 200;
    } catch (error) {
      return false;
    }
  };

  // Check backend connection on app load
  useEffect(() => {
    const checkConnection = async () => {
      const isConnected = await testBackendConnection();
      if (!isConnected) {
        showNotification('⚠️ Unable to connect to backend services. Some features may not work properly.', 'error');
      }
    };
    
    checkConnection();
  }, []);

  // Enhanced notification function with better error categorization
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // Landing Screen Component
  const LandingScreen = () => {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-orange-100 p-4 relative overflow-hidden">
        {/* Magical Background Elements */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-6 h-6 bg-yellow-400 rounded-full animate-pulse"></div>
          <div className="absolute top-20 right-20 w-8 h-8 bg-pink-400 rounded-full animate-bounce"></div>
          <div className="absolute bottom-20 left-20 w-7 h-7 bg-blue-400 rounded-full animate-ping"></div>
          <div className="absolute bottom-10 right-10 w-5 h-5 bg-purple-400 rounded-full animate-pulse"></div>
          <div className="absolute top-1/2 left-1/4 w-4 h-4 bg-green-400 rounded-full animate-bounce"></div>
          <div className="absolute top-1/3 right-1/3 w-6 h-6 bg-orange-400 rounded-full animate-ping"></div>
          <div className="absolute top-2/3 left-1/3 w-3 h-3 bg-red-400 rounded-full animate-pulse"></div>
        </div>
        
        <div className="max-w-6xl mx-auto relative z-10">
          
          {/* Enhanced Hero Section */}
          <div className="text-center py-20">
            <div className="mb-12">
              <div className="text-9xl mb-6 animate-bounce">👨‍🍳</div>
              <h1 className="text-6xl md:text-7xl font-bold mb-6">
                Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-pink-600 to-orange-600 animate-pulse">AI Chef</span>
              </h1>
              <p className="text-2xl md:text-3xl text-gray-700 mb-8 max-w-4xl mx-auto font-medium">
                ✨ Your magical cooking assistant that creates custom recipes, generates viral Starbucks drinks, and builds automatic shopping lists! 🌟
              </p>
              
              {/* Magic badges */}
              <div className="flex flex-wrap justify-center gap-4 mb-8">
                <span className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full font-bold text-lg shadow-lg animate-pulse">
                  🤖 AI-Powered
                </span>
                <span className="px-6 py-3 bg-gradient-to-r from-blue-500 to-green-500 text-white rounded-full font-bold text-lg shadow-lg animate-pulse">
                  🛒 Real Shopping
                </span>
                <span className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full font-bold text-lg shadow-lg animate-pulse">
                  🚀 Viral Ready
                </span>
              </div>
            </div>

            {/* Enhanced Feature Highlights */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
              <div className="bg-white rounded-3xl shadow-2xl p-10 transform hover:scale-105 transition-all duration-300 border-4 border-gradient-to-r from-purple-200 to-pink-200 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50 to-pink-50 opacity-50"></div>
                <div className="relative z-10">
                  <div className="text-6xl mb-6 animate-bounce">🍳</div>
                  <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-4">AI Recipe Generator</h3>
                  <p className="text-gray-700 text-lg">Create personalized recipes with automatic Walmart shopping lists</p>
                </div>
              </div>
              
              <div className="bg-white rounded-3xl shadow-2xl p-10 transform hover:scale-105 transition-all duration-300 border-4 border-gradient-to-r from-green-200 to-blue-200 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-green-50 to-blue-50 opacity-50"></div>
                <div className="relative z-10">
                  <div className="text-6xl mb-6 animate-bounce">☕</div>
                  <h3 className="text-2xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent mb-4">Starbucks Secret Menu</h3>
                  <p className="text-gray-700 text-lg">Generate viral TikTok drink hacks with drive-thru ordering scripts</p>
                </div>
              </div>
              
              <div className="bg-white rounded-3xl shadow-2xl p-10 transform hover:scale-105 transition-all duration-300 border-4 border-gradient-to-r from-orange-200 to-red-200 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-orange-50 to-red-50 opacity-50"></div>
                <div className="relative z-10">
                  <div className="text-6xl mb-6 animate-bounce">🛒</div>
                  <h3 className="text-2xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-4">Smart Shopping</h3>
                  <p className="text-gray-700 text-lg">One-click Walmart integration for all your ingredients</p>
                </div>
              </div>
            </div>

            {/* Enhanced CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
              <button
                onClick={() => setCurrentScreen('register')}
                className="bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 text-white font-bold py-6 px-12 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-xl relative overflow-hidden"
              >
                <span className="relative z-10 flex items-center">
                  <span className="text-2xl mr-3 animate-bounce">🚀</span>
                  Start Cooking for Free
                  <span className="text-2xl ml-3 animate-bounce">✨</span>
                </span>
              </button>
              <button
                onClick={() => setCurrentScreen('login')}
                className="bg-gradient-to-r from-gray-600 to-gray-800 hover:from-gray-700 hover:to-gray-900 text-white font-bold py-6 px-12 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-xl"
              >
                <span className="flex items-center">
                  <span className="text-2xl mr-3">🔑</span>
                  Sign In
                </span>
              </button>
            </div>
          </div>

          {/* Enhanced How It Works */}
          <div className="bg-white rounded-3xl shadow-2xl p-12 md:p-16 mb-16 border-4 border-gradient-to-r from-purple-200 to-pink-200">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent text-center mb-16">
              ✨ How AI Chef Works ✨
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
              
              {/* Enhanced Recipe Flow */}
              <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-8 border-2 border-orange-200">
                <h3 className="text-3xl font-bold text-orange-600 mb-8 flex items-center">
                  <span className="mr-4 text-4xl animate-bounce">🍳</span>
                  Recipe Magic
                </h3>
                <div className="space-y-6">
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">1</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">Choose Your Style</h4>
                      <p className="text-gray-600">Pick from Cuisine, Snacks, or Beverages</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">2</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">AI Creates Your Recipe</h4>
                      <p className="text-gray-600">Personalized with your preferences and dietary needs</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">3</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">Shop with One Click</h4>
                      <p className="text-gray-600">Automatic Walmart cart with all ingredients</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Enhanced Starbucks Flow */}
              <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-8 border-2 border-green-200">
                <h3 className="text-3xl font-bold text-green-600 mb-8 flex items-center">
                  <span className="mr-4 text-4xl animate-bounce">☕</span>
                  Starbucks Hacks
                </h3>
                <div className="space-y-6">
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">1</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">Pick Your Vibe</h4>
                      <p className="text-gray-600">Frappuccino, Refresher, Lemonade, or Surprise Me!</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">2</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">Get Your Secret Drink</h4>
                      <p className="text-gray-600">Unique creations with viral potential</p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <span className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full flex items-center justify-center text-lg font-bold mr-6 mt-1 animate-pulse">3</span>
                    <div>
                      <h4 className="font-bold text-gray-800 text-lg">Order Like a Pro</h4>
                      <p className="text-gray-600">Perfect drive-thru script ready to use</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Enhanced Social Proof */}
          <div className="text-center bg-gradient-to-r from-purple-100 to-pink-100 rounded-3xl p-16 border-4 border-gradient-to-r from-purple-200 to-pink-200">
            <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-12">
              🌟 Join the AI Chef Community 🌟
            </h2>
            <div className="flex flex-wrap justify-center gap-6 text-4xl mb-12">
              <span className="animate-bounce">🍕</span>
              <span className="animate-pulse">🥗</span>
              <span className="animate-bounce">🍜</span>
              <span className="animate-pulse">🧋</span>
              <span className="animate-bounce">☕</span>
              <span className="animate-pulse">🍰</span>
              <span className="animate-bounce">🍱</span>
              <span className="animate-pulse">🥙</span>
            </div>
            <p className="text-2xl text-gray-700 mb-8 font-medium">
              Ready to transform your cooking and coffee game? Let's get started! 🚀✨
            </p>
            <div className="flex justify-center gap-4 mt-8">
              <span className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-full font-bold text-lg shadow-lg animate-pulse">
                🎯 AI-Powered Recipes
              </span>
              <span className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-full font-bold text-lg shadow-lg animate-pulse">
                🛒 Smart Shopping
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Enhanced Registration Screen Component
  const RegisterScreen = () => {
    const [formData, setFormData] = useState({
      first_name: '',
      last_name: '',
      email: '',
      password: '',
      confirmPassword: '',
      dietary_preferences: [],
      allergies: [],
      favorite_cuisines: []
    });
    const [isCreating, setIsCreating] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const dietaryOptions = ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'];
    const allergyOptions = ['nuts', 'shellfish', 'eggs', 'dairy', 'soy', 'wheat'];
    const cuisineOptions = ['italian', 'mexican', 'chinese', 'indian', 'mediterranean', 'american'];

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      // Validation
      if (!formData.first_name || !formData.last_name || !formData.email || !formData.password) {
        showNotification('❌ Please fill in all required fields', 'error');
        return;
      }

      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(formData.email)) {
        showNotification('❌ Please enter a valid email address', 'error');
        return;
      }

      // Password validation
      if (formData.password.length < 6) {
        showNotification('❌ Password must be at least 6 characters', 'error');
        return;
      }

      if (formData.password !== formData.confirmPassword) {
        showNotification('❌ Passwords do not match', 'error');
        return;
      }

      setIsCreating(true);
      try {
        const registrationData = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          password: formData.password,
          dietary_preferences: formData.dietary_preferences,
          allergies: formData.allergies,
          favorite_cuisines: formData.favorite_cuisines
        };

        const response = await axios.post(`${API}/api/auth/register`, registrationData);
        
        setPendingVerificationEmail(formData.email);
        setCurrentScreen('verify-email');
        showNotification('✅ Registration successful! Check your email for verification code', 'success');
        
      } catch (error) {
        // Enhanced error handling for registration
        if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
          showNotification('❌ Unable to connect to server. Please check your internet connection and try again.', 'error');
        } else if (error.response?.status === 404) {
          showNotification('❌ Service temporarily unavailable. Please try again later.', 'error');
        } else if (error.response?.status === 400) {
          const errorMessage = error.response?.data?.detail || 'Registration failed. Please check your information.';
          showNotification(`❌ ${errorMessage}`, 'error');
        } else {
          const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
          showNotification(`❌ ${errorMessage}`, 'error');
        }
      } finally {
        setIsCreating(false);
      }
    };

    const toggleArrayItem = (array, item, setField) => {
      const newArray = array.includes(item)
        ? array.filter(i => i !== item)
        : [...array, item];
      setField(newArray);
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">👨‍🍳</div>
            <h2 className="text-2xl font-bold text-gray-800">Create Your Account</h2>
            <p className="text-gray-600">Join AI Chef today!</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                <input
                  type="text"
                  placeholder="John"
                  value={formData.first_name}
                  onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                <input
                  type="text"
                  placeholder="Doe"
                  value={formData.last_name}
                  onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Address *</label>
              <input
                type="email"
                placeholder="john.doe@example.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                required
              />
            </div>

            {/* Password Fields */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password *</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="At least 6 characters"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password *</label>
              <input
                type="password"
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm"
                required
              />
            </div>

            {/* Dietary Preferences */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Preferences</label>
              <div className="grid grid-cols-2 gap-1">
                {dietaryOptions.map(option => (
                  <label key={option} className="flex items-center space-x-2 p-1 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.dietary_preferences.includes(option)}
                      onChange={() => toggleArrayItem(formData.dietary_preferences, option, 
                        (newArray) => setFormData({...formData, dietary_preferences: newArray}))}
                      className="rounded text-green-500"
                    />
                    <span className="text-xs capitalize">{option}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Allergies */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Allergies</label>
              <div className="grid grid-cols-2 gap-1">
                {allergyOptions.map(option => (
                  <label key={option} className="flex items-center space-x-2 p-1 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.allergies.includes(option)}
                      onChange={() => toggleArrayItem(formData.allergies, option, 
                        (newArray) => setFormData({...formData, allergies: newArray}))}
                      className="rounded text-red-500"
                    />
                    <span className="text-xs capitalize">{option}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Favorite Cuisines */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Favorite Cuisines</label>
              <div className="grid grid-cols-2 gap-1">
                {cuisineOptions.map(option => (
                  <label key={option} className="flex items-center space-x-2 p-1 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.favorite_cuisines.includes(option)}
                      onChange={() => toggleArrayItem(formData.favorite_cuisines, option, 
                        (newArray) => setFormData({...formData, favorite_cuisines: newArray}))}
                      className="rounded text-blue-500"
                    />
                    <span className="text-xs capitalize">{option}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isCreating}
              className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold py-3 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {isCreating ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Creating Account...</span>
                </div>
              ) : (
                '✨ Create Account'
              )}
            </button>
          </form>

          <button
            onClick={() => setCurrentScreen('landing')}
            className="w-full mt-4 text-gray-600 hover:text-gray-800 transition-colors text-sm"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  };

  // Email Verification Screen Component
  const EmailVerificationScreen = () => {
    const [verificationCode, setVerificationCode] = useState('');
    const [isVerifying, setIsVerifying] = useState(false);
    const [isResending, setIsResending] = useState(false);
    const [timeRemaining, setTimeRemaining] = useState(300); // 5 minutes in seconds

    // Countdown timer
    useEffect(() => {
      if (timeRemaining > 0) {
        const timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000);
        return () => clearTimeout(timer);
      }
    }, [timeRemaining]);

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleVerify = async (e) => {
      e.preventDefault();
      
      if (!verificationCode || verificationCode.length !== 6) {
        showNotification('❌ Please enter a 6-digit verification code', 'error');
        return;
      }

      setIsVerifying(true);
      try {
        const response = await axios.post(`${API}/api/auth/verify`, {
          email: pendingVerificationEmail,
          code: verificationCode
        });

        // Set user state with verified status
        const verifiedUser = {
          ...response.data.user,
          is_verified: true  // Ensure verification status is set
        };
        
        setUser(verifiedUser);
        
        // Clear verification email state
        setPendingVerificationEmail(null);
        
        // Explicitly save to localStorage to ensure persistence
        try {
          localStorage.setItem('ai_chef_user', JSON.stringify(verifiedUser));
        } catch (storageError) {
          // Handle localStorage errors gracefully
        }
        
        setCurrentScreen('dashboard');
        showNotification('🎉 Email verified successfully! Welcome to AI Chef!', 'success');
        
      } catch (error) {
        // Verification failed
        const errorMessage = error.response?.data?.detail || 'Verification failed. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
      } finally {
        setIsVerifying(false);
      }
    };

    const handleResendCode = async () => {
      setIsResending(true);
      try {
        await axios.post(`${API}/api/auth/resend-code`, {
          email: pendingVerificationEmail
        });

        setTimeRemaining(300); // Reset timer
        setVerificationCode(''); // Clear current code
        showNotification('📧 New verification code sent!', 'success');
        
      } catch (error) {
        // Resend failed
        const errorMessage = error.response?.data?.detail || 'Failed to resend code. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
      } finally {
        setIsResending(false);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">📧</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Check Your Email</h2>
            <p className="text-gray-600 text-sm">
              We sent a 6-digit verification code to<br/>
              <strong>{pendingVerificationEmail}</strong>
            </p>
          </div>

          <form onSubmit={handleVerify} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3 text-center">
                Enter Verification Code
              </label>
              <input
                type="text"
                placeholder="123456"
                value={verificationCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setVerificationCode(value);
                }}
                className="w-full px-4 py-4 text-center text-2xl font-mono border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent tracking-widest"
                maxLength={6}
                autoComplete="one-time-code"
                autoFocus
              />
              <div className="text-center mt-3">
                {timeRemaining > 0 ? (
                  <p className="text-sm text-gray-500">
                    Code expires in: <span className="font-mono text-red-500">{formatTime(timeRemaining)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-red-500">Code has expired</p>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={isVerifying || verificationCode.length !== 6}
              className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {isVerifying ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Verifying...</span>
                </div>
              ) : (
                '✅ Verify Email'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 mb-3">Didn't receive the code?</p>
            <button
              onClick={handleResendCode}
              disabled={isResending || timeRemaining > 240} // Allow resend after 1 minute
              className="text-blue-600 hover:text-blue-800 font-medium text-sm underline disabled:text-gray-400 disabled:no-underline"
            >
              {isResending ? (
                <span className="flex items-center justify-center space-x-1">
                  <div className="w-3 h-3 border border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Sending...</span>
                </span>
              ) : timeRemaining > 240 ? (
                `Resend available in ${formatTime(timeRemaining - 240)}`
              ) : (
                '📤 Resend Code'
              )}
            </button>
          </div>

          <button
            onClick={() => {
              setCurrentScreen('register');
              setPendingVerificationEmail(null);
            }}
            className="w-full mt-6 text-gray-600 hover:text-gray-800 transition-colors text-sm"
          >
            ← Back to Registration
          </button>
        </div>
      </div>
    );
  };

  // Enhanced Login Screen Component
  const LoginScreen = () => {
    const [formData, setFormData] = useState({
      email: '',
      password: ''
    });
    const [isLoggingIn, setIsLoggingIn] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!formData.email || !formData.password) {
        showNotification('❌ Please enter both email and password', 'error');
        return;
      }

      setIsLoggingIn(true);
      try {
        const response = await axios.post(`${API}/api/auth/login`, formData);
        
        // Check if user is unverified
        if (response.data.status === 'unverified' && response.data.needs_verification) {
          setPendingVerificationEmail(response.data.email);
          setCurrentScreen('verify-email');
          showNotification('📧 Please verify your email to continue', 'error');
          return;
        }
        
        // Successful login
        if (response.data.status === 'success') {
          setUserWithSession(response.data.user);  // Use enhanced session management
          setCurrentScreen('dashboard');
          
          // Mark user as onboarded to skip tutorial for returning users
          localStorage.setItem(`user_${response.data.user.id}_onboarded`, 'true');
          
          showNotification(`🎉 Welcome back, ${response.data.user.first_name}!`, 'success');
        }
        
      } catch (error) {
        // Enhanced error handling for connectivity issues
        if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
          showNotification('❌ Unable to connect to server. Please check your internet connection and try again.', 'error');
        } else if (error.response?.status === 404) {
          showNotification('❌ Service temporarily unavailable. Please try again later.', 'error');
        } else if (error.response?.status === 401) {
          showNotification('❌ Invalid email or password. Please check your credentials.', 'error');
        } else {
          const errorMessage = error.response?.data?.detail || 'Login failed. Please check your credentials and try again.';
          showNotification(`❌ ${errorMessage}`, 'error');
        }
      } finally {
        setIsLoggingIn(false);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">👨‍🍳</div>
            <h2 className="text-2xl font-bold text-gray-800">Welcome Back</h2>
            <p className="text-gray-600">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
              <input
                type="email"
                placeholder="john.doe@example.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {isLoggingIn ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Signing In...</span>
                </div>
              ) : (
                '🔑 Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center space-y-3">
            <button
              onClick={() => setCurrentScreen('forgot-password')}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium underline"
            >
              🔒 Forgot your password?
            </button>
            
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <button
                onClick={() => setCurrentScreen('register')}
                className="text-blue-600 hover:text-blue-800 font-medium underline"
              >
                Sign up here
              </button>
            </p>
          </div>

          <button
            onClick={() => setCurrentScreen('landing')}
            className="w-full mt-4 text-gray-600 hover:text-gray-800 transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  };

  // Enhanced Dashboard Screen Component with improved navigation
  const DashboardScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-blue-100 p-4 relative overflow-hidden">
      {/* Magical Background Elements */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-4 h-4 bg-yellow-400 rounded-full animate-pulse"></div>
        <div className="absolute top-20 right-20 w-6 h-6 bg-pink-400 rounded-full animate-bounce"></div>
        <div className="absolute bottom-20 left-20 w-5 h-5 bg-blue-400 rounded-full animate-ping"></div>
        <div className="absolute bottom-10 right-10 w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
        <div className="absolute top-1/2 left-1/4 w-2 h-2 bg-green-400 rounded-full animate-bounce"></div>
      </div>
      
      <div className="max-w-md mx-auto relative z-10">
        {/* Trial Status Banner */}
        <TrialStatusBanner 
          user={user} 
          onUpgradeClick={() => setShowSubscriptionScreen(true)}
        />
        
        {/* Welcome Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8 border-4 border-gradient-to-r from-purple-200 to-pink-200">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4 animate-bounce">👨‍🍳</div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Hi, Welcome back, {user?.first_name}!
            </h2>
            <p className="text-lg text-gray-600 mt-2">Ready to cook something amazing?</p>
            {user?.is_verified && (
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold bg-gradient-to-r from-green-500 to-green-600 text-white mt-4 shadow-lg">
                <span className="mr-2">✅</span>
                Verified Chef
              </span>
            )}
          </div>
        </div>
        
        {/* Enhanced Action Buttons */}
        <div className="space-y-4 mb-8">
          {/* FEATURED: Weekly Recipe Planner Button */}
          <button
            onClick={() => setCurrentScreen('weekly-recipes')}
            className="w-full bg-gradient-to-r from-green-500 via-teal-500 to-blue-500 hover:from-green-600 hover:via-teal-600 hover:to-blue-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">📅</span>
              Weekly Meal Planner
              <span className="text-2xl ml-3 animate-pulse">🛒</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-blue-400 opacity-20 animate-pulse"></div>
          </button>
          
          <button
            onClick={() => setCurrentScreen('recipe-generation')}
            className="w-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">🍳</span>
              Generate AI Recipe
              <span className="text-2xl ml-3 animate-bounce">✨</span>
            </span>
          </button>
          
          <button
            onClick={() => setCurrentScreen('recipe-history')}
            className="w-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">📚</span>
              Recipe History
              <span className="text-2xl ml-3 animate-pulse">📖</span>
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-400 to-pink-400 opacity-20 animate-pulse"></div>
          </button>
          
          <button
            onClick={() => setCurrentScreen('starbucks-generator')}
            className="w-full bg-gradient-to-r from-green-500 via-blue-500 to-purple-500 hover:from-green-600 hover:via-blue-600 hover:to-purple-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg"
          >
            <span className="flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">☕</span>
              Starbucks Secret Menu
              <span className="text-2xl ml-3 animate-pulse">🌟</span>
            </span>
          </button>
          
          <button
            onClick={() => setCurrentScreen('tutorial')}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg"
          >
            <span className="flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">📖</span>
              How to Use AI Chef
              <span className="text-2xl ml-3 animate-pulse">💡</span>
            </span>
          </button>
        </div>
        
        {/* Enhanced Quick Stats */}
        <div className="bg-gradient-to-r from-purple-100 via-pink-100 to-blue-100 rounded-3xl p-8 mb-8 border-4 border-gradient-to-r from-purple-200 to-pink-200">
          <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-6 text-center">
            🌟 Welcome to AI Chef! 🌟
          </h3>
          <div className="space-y-4">
            <div className="flex items-center p-4 bg-white rounded-2xl shadow-lg">
              <span className="text-3xl mr-4 animate-bounce">📅</span>
              <span className="text-gray-700 font-medium">Weekly meal plans with shopping lists</span>
            </div>
            <div className="flex items-center p-4 bg-white rounded-2xl shadow-lg">
              <span className="text-3xl mr-4 animate-bounce">🤖</span>
              <span className="text-gray-700 font-medium">Generate personalized recipes with AI</span>
            </div>
            <div className="flex items-center p-4 bg-white rounded-2xl shadow-lg">
              <span className="text-3xl mr-4 animate-pulse">🛒</span>
              <span className="text-gray-700 font-medium">Individual ingredient Walmart shopping</span>
            </div>
            <div className="flex items-center p-4 bg-white rounded-2xl shadow-lg">
              <span className="text-3xl mr-4 animate-bounce">💚</span>
              <span className="text-gray-700 font-medium">Healthy & budget-friendly options</span>
            </div>
          </div>
        </div>
        
        {/* Enhanced Logout Button */}
        <button
          onClick={() => {
            setUserWithSession(null); // Use enhanced session clearing
            setPendingVerificationEmail(null);
            setCurrentScreen('landing');
            showNotification('👋 Signed out successfully', 'success');
          }}
          className="w-full bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white font-bold py-4 px-8 rounded-3xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300"
        >
          <span className="flex items-center justify-center">
            <span className="text-xl mr-2">🚪</span>
            Sign Out
          </span>
        </button>
      </div>
    </div>
  );

  // Forgot Password Screen Component
  const ForgotPasswordScreen = () => {
    const [email, setEmail] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!email) {
        showNotification('❌ Please enter your email address', 'error');
        return;
      }

      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showNotification('❌ Please enter a valid email address', 'error');
        return;
      }

      setIsSubmitting(true);
      try {
        await axios.post(`${API}/api/auth/forgot-password`, { email });
        
        setPendingResetEmail(email);
        setCurrentScreen('reset-password');
        showNotification('📧 Password reset code sent! Check your email', 'success');
        
      } catch (error) {
        // Password reset request failed
        // Don't show specific error for security - always show success message
        setPendingResetEmail(email);
        setCurrentScreen('reset-password');
        showNotification('📧 If an account exists, a reset code has been sent', 'success');
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">🔒</div>
            <h2 className="text-2xl font-bold text-gray-800">Forgot Password?</h2>
            <p className="text-gray-600">No worries! We'll send you a reset code</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
              <input
                type="email"
                placeholder="Enter your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white font-semibold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Sending Reset Code...</span>
                </div>
              ) : (
                '📧 Send Reset Code'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Remember your password?{' '}
              <button
                onClick={() => setCurrentScreen('login')}
                className="text-blue-600 hover:text-blue-800 font-medium underline"
              >
                Sign in here
              </button>
            </p>
          </div>

          <button
            onClick={() => setCurrentScreen('landing')}
            className="w-full mt-4 text-gray-600 hover:text-gray-800 transition-colors"
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  };

  // Reset Password Screen Component
  const ResetPasswordScreen = () => {
    const [formData, setFormData] = useState({
      resetCode: '',
      newPassword: '',
      confirmPassword: ''
    });
    const [isResetting, setIsResetting] = useState(false);
    const [showPasswords, setShowPasswords] = useState(false);
    const [timeRemaining, setTimeRemaining] = useState(600); // 10 minutes

    // Countdown timer
    useEffect(() => {
      if (timeRemaining > 0) {
        const timer = setTimeout(() => setTimeRemaining(timeRemaining - 1), 1000);
        return () => clearTimeout(timer);
      }
    }, [timeRemaining]);

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!formData.resetCode || !formData.newPassword || !formData.confirmPassword) {
        showNotification('❌ Please fill in all fields', 'error');
        return;
      }

      if (formData.resetCode.length !== 6) {
        showNotification('❌ Please enter a 6-digit reset code', 'error');
        return;
      }

      if (formData.newPassword.length < 6) {
        showNotification('❌ Password must be at least 6 characters', 'error');
        return;
      }

      if (formData.newPassword !== formData.confirmPassword) {
        showNotification('❌ Passwords do not match', 'error');
        return;
      }

      setIsResetting(true);
      try {
        await axios.post(`${API}/api/auth/reset-password`, {
          email: pendingResetEmail,
          reset_code: formData.resetCode,
          new_password: formData.newPassword
        });
        
        setCurrentScreen('login');
        showNotification('✅ Password reset successful! Please login with your new password', 'success');
        
      } catch (error) {
        // Password reset failed
        const errorMessage = error.response?.data?.detail || 'Password reset failed. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
      } finally {
        setIsResetting(false);
      }
    };

    const handleResendCode = async () => {
      try {
        await axios.post(`${API}/api/auth/forgot-password`, { email: pendingResetEmail });
        setTimeRemaining(600); // Reset timer
        setFormData({...formData, resetCode: ''}); // Clear current code
        showNotification('📧 New reset code sent!', 'success');
      } catch (error) {
        showNotification('📧 If an account exists, a new reset code has been sent', 'success');
      }
    };

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="text-4xl mb-2">🔑</div>
            <h2 className="text-2xl font-bold text-gray-800">Reset Password</h2>
            <p className="text-gray-600 text-sm">
              Enter the 6-digit code sent to<br/>
              <strong>{pendingResetEmail}</strong>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 text-center">
                Reset Code
              </label>
              <input
                type="text"
                placeholder="123456"
                value={formData.resetCode}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                  setFormData({...formData, resetCode: value});
                }}
                className="w-full px-4 py-3 text-center text-xl font-mono border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent tracking-widest"
                maxLength={6}
                autoComplete="one-time-code"
              />
              <div className="text-center mt-2">
                {timeRemaining > 0 ? (
                  <p className="text-sm text-gray-500">
                    Code expires in: <span className="font-mono text-red-500">{formatTime(timeRemaining)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-red-500">Code has expired</p>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
              <div className="relative">
                <input
                  type={showPasswords ? "text" : "password"}
                  placeholder="Enter new password (min 6 characters)"
                  value={formData.newPassword}
                  onChange={(e) => setFormData({...formData, newPassword: e.target.value})}
                  className="w-full px-4 py-3 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPasswords(!showPasswords)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPasswords ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
              <input
                type={showPasswords ? "text" : "password"}
                placeholder="Confirm your new password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isResetting || formData.resetCode.length !== 6}
              className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white font-semibold py-4 px-6 rounded-2xl shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
            >
              {isResetting ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Resetting Password...</span>
                </div>
              ) : (
                '🔑 Reset Password'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 mb-3">Didn't receive the code?</p>
            <button
              onClick={handleResendCode}
              disabled={timeRemaining > 540} // Allow resend after 1 minute
              className="text-blue-600 hover:text-blue-800 font-medium text-sm underline disabled:text-gray-400 disabled:no-underline"
            >
              {timeRemaining > 540 ? (
                `Resend available in ${formatTime(timeRemaining - 540)}`
              ) : (
                '📤 Resend Reset Code'
              )}
            </button>
          </div>

          <button
            onClick={() => {
              setCurrentScreen('login');
              setPendingResetEmail(null);
            }}
            className="w-full mt-6 text-gray-600 hover:text-gray-800 transition-colors text-sm"
          >
            ← Back to Login
          </button>
        </div>
      </div>
    );
  };

  // Recipe Generation Screen Component
  const RecipeGenerationScreen = () => {
    const [formData, setFormData] = useState({
      recipe_type: '', // 'cuisine', 'snack', or 'beverage'
      cuisine_type: '',
      snack_type: '',
      beverage_type: '',
      dietary_preferences: [],
      ingredients_on_hand: '',
      prep_time_max: '',
      servings: 4,
      difficulty: 'medium',
      is_healthy: false,
      max_calories_per_serving: 400,
      is_budget_friendly: false,
      max_budget: 20
    });
    const [isGenerating, setIsGenerating] = useState(false);

    const cuisineOptions = ['italian', 'mexican', 'chinese', 'indian', 'mediterranean', 'american', 'thai', 'japanese', 'french', 'korean'];
    const snackOptions = ['acai bowls', 'fruit lemon slices chili', 'frozen yogurt berry bites'];
    const beverageOptions = ['boba tea', 'thai tea', 'special lemonades'];
    const dietaryOptions = ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'];
    const difficultyOptions = ['easy', 'medium', 'hard'];

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      // Validate that a recipe type and specific type are selected
      if (!formData.recipe_type) {
        showNotification('❌ Please select a recipe category (Cuisine, Snack, or Beverage)', 'error');
        return;
      }

      let selectedType = '';
      if (formData.recipe_type === 'cuisine' && !formData.cuisine_type) {
        showNotification('❌ Please select a cuisine type', 'error');
        return;
      } else if (formData.recipe_type === 'snack' && !formData.snack_type) {
        showNotification('❌ Please select a snack type', 'error');
        return;
      } else if (formData.recipe_type === 'beverage' && !formData.beverage_type) {
        showNotification('❌ Please select a beverage type', 'error');
        return;
      }

      // Determine the final type for the API
      if (formData.recipe_type === 'cuisine') {
        selectedType = formData.cuisine_type;
      } else if (formData.recipe_type === 'snack') {
        selectedType = formData.snack_type;
      } else if (formData.recipe_type === 'beverage') {
        selectedType = formData.beverage_type;
      }

      setIsGenerating(true);
      try {
        const requestData = {
          user_id: user.id,
          recipe_category: formData.recipe_type, // 'cuisine', 'snack', or 'beverage'
          cuisine_type: selectedType,
          dietary_preferences: formData.dietary_preferences,
          ingredients_on_hand: formData.ingredients_on_hand ? formData.ingredients_on_hand.split(',').map(i => i.trim()) : [],
          prep_time_max: formData.prep_time_max ? parseInt(formData.prep_time_max) : null,
          servings: formData.servings,
          difficulty: formData.difficulty,
          is_healthy: formData.is_healthy,
          max_calories_per_serving: formData.is_healthy ? formData.max_calories_per_serving : null,
          is_budget_friendly: formData.is_budget_friendly,
          max_budget: formData.is_budget_friendly ? formData.max_budget : null
        };

        const response = await axios.post(`${API}/api/recipes/generate`, requestData);
        
        // Store recipe and navigate to detail
        window.currentRecipe = response.data;
        setCurrentScreen('recipe-detail');
        showNotification('🎉 Recipe generated successfully!', 'success');
        
      } catch (error) {
        // Recipe generation failed
        const errorMessage = error.response?.data?.detail || 'Failed to generate recipe. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
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

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-100 via-pink-100 to-orange-100 p-4 relative overflow-hidden">
        {/* Magical Background Elements */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-5 h-5 bg-yellow-400 rounded-full animate-pulse"></div>
          <div className="absolute top-20 right-20 w-7 h-7 bg-pink-400 rounded-full animate-bounce"></div>
          <div className="absolute bottom-20 left-20 w-6 h-6 bg-blue-400 rounded-full animate-ping"></div>
          <div className="absolute bottom-10 right-10 w-4 h-4 bg-purple-400 rounded-full animate-pulse"></div>
          <div className="absolute top-1/2 left-1/4 w-3 h-3 bg-green-400 rounded-full animate-bounce"></div>
          <div className="absolute top-1/3 right-1/3 w-5 h-5 bg-orange-400 rounded-full animate-ping"></div>
        </div>
        
        <div className="max-w-2xl mx-auto relative z-10">
          {/* Enhanced Header Card */}
          <div className="bg-white rounded-3xl shadow-2xl p-8 mb-8 border-4 border-gradient-to-r from-purple-200 to-pink-200">
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={() => setCurrentScreen('dashboard')}
                className="flex items-center space-x-2 text-purple-600 hover:text-purple-700 font-bold transition-all duration-200 hover:scale-105"
              >
                <span className="text-2xl">←</span>
                <span>Back</span>
              </button>
              <div className="text-center flex-1">
                <div className="text-6xl mb-2 animate-bounce">🤖</div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Generate AI Recipe
                </h2>
                <p className="text-gray-600 text-lg font-medium">Create a personalized recipe just for you</p>
              </div>
            </div>
          </div>

          {/* Enhanced Form Card */}
          <div className="bg-white rounded-3xl shadow-2xl p-8 border-4 border-gradient-to-r from-purple-200 to-pink-200">
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Enhanced Recipe Category Selection */}
              <div>
                <label className="block text-2xl font-bold text-gray-700 mb-6 text-center">
                  🎯 Choose Your Recipe Adventure
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Enhanced Cuisine Card */}
                  <div 
                    className={`border-4 rounded-3xl p-6 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                      formData.recipe_type === 'cuisine' 
                        ? 'border-purple-500 bg-gradient-to-br from-purple-100 to-pink-100 shadow-lg scale-105' 
                        : 'border-gray-200 hover:border-purple-300 bg-white hover:shadow-lg'
                    }`}
                    onClick={() => setFormData({...formData, recipe_type: 'cuisine', snack_type: '', beverage_type: ''})}
                  >
                    <div className="text-center">
                      <div className="text-5xl mb-4 animate-bounce">🍝</div>
                      <h3 className="font-bold text-gray-800 text-lg">Cuisine</h3>
                      <p className="text-sm text-gray-600">Traditional dishes from around the world</p>
                    </div>
                  </div>

                  {/* Enhanced Snacks Card */}
                  <div 
                    className={`border-4 rounded-3xl p-6 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                      formData.recipe_type === 'snack' 
                        ? 'border-green-500 bg-gradient-to-br from-green-100 to-blue-100 shadow-lg scale-105' 
                        : 'border-gray-200 hover:border-green-300 bg-white hover:shadow-lg'
                    }`}
                    onClick={() => setFormData({...formData, recipe_type: 'snack', cuisine_type: '', beverage_type: ''})}
                  >
                    <div className="text-center">
                      <div className="text-5xl mb-4 animate-bounce">🍪</div>
                      <h3 className="font-bold text-gray-800 text-lg">Snacks</h3>
                      <p className="text-sm text-gray-600">Healthy bowls, treats, and bite-sized delights</p>
                    </div>
                  </div>

                  {/* Enhanced Beverages Card */}
                  <div 
                    className={`border-4 rounded-3xl p-6 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
                      formData.recipe_type === 'beverage' 
                        ? 'border-orange-500 bg-gradient-to-br from-orange-100 to-red-100 shadow-lg scale-105' 
                        : 'border-gray-200 hover:border-orange-300 bg-white hover:shadow-lg'
                    }`}
                    onClick={() => setFormData({...formData, recipe_type: 'beverage', cuisine_type: '', snack_type: ''})}
                  >
                    <div className="text-center">
                      <div className="text-5xl mb-4 animate-bounce">🧋</div>
                      <h3 className="font-bold text-gray-800 text-lg">Beverages</h3>
                      <p className="text-sm text-gray-600">Boba, tea, and specialty drinks</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Specific Type Selection */}
              {formData.recipe_type === 'cuisine' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Cuisine Type *</label>
                  <select
                    value={formData.cuisine_type}
                    onChange={(e) => setFormData({...formData, cuisine_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select cuisine...</option>
                    {cuisineOptions.map(cuisine => (
                      <option key={cuisine} value={cuisine}>
                        {cuisine.charAt(0).toUpperCase() + cuisine.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {formData.recipe_type === 'snack' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Snack Type *</label>
                  <select
                    value={formData.snack_type}
                    onChange={(e) => setFormData({...formData, snack_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                  >
                    <option value="">Select snack type...</option>
                    {snackOptions.map(snack => (
                      <option key={snack} value={snack}>
                        {snack.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {formData.recipe_type === 'beverage' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Beverage Type *</label>
                  <select
                    value={formData.beverage_type}
                    onChange={(e) => setFormData({...formData, beverage_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    required
                    data-testid="beverage-type-select"
                  >
                    <option value="">Select beverage type...</option>
                    {beverageOptions.map(beverage => (
                      <option key={beverage} value={beverage}>
                        {beverage.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Enhanced Dietary Preferences */}
              <div>
                <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                  🥗 Dietary Preferences (Optional)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {dietaryOptions.map(option => (
                    <label key={option} className="flex items-center space-x-3 p-4 rounded-2xl hover:bg-gray-50 cursor-pointer border-2 border-gray-200 hover:border-green-300 transition-all duration-300">
                      <input
                        type="checkbox"
                        checked={formData.dietary_preferences.includes(option)}
                        onChange={() => toggleArrayItem(formData.dietary_preferences, option, 
                          (newArray) => setFormData({...formData, dietary_preferences: newArray}))}
                        className="w-5 h-5 rounded text-green-500 focus:ring-green-400"
                      />
                      <span className="text-lg font-medium capitalize">{option}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Enhanced Healthy Mode Toggle */}
              <div className="bg-gradient-to-r from-green-100 to-blue-100 p-6 rounded-3xl border-3 border-green-200">
                <label className="flex items-center space-x-4 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_healthy}
                    onChange={(e) => setFormData({...formData, is_healthy: e.target.checked})}
                    className="w-6 h-6 rounded-xl text-green-500 focus:ring-4 focus:ring-green-300"
                  />
                  <div>
                    <div className="flex items-center">
                      <span className="text-3xl mr-2">🌱</span>
                      <span className="text-xl font-bold text-green-800">Healthy Mode</span>
                    </div>
                    <p className="text-green-600 font-medium">Limit calories per serving for healthier meals</p>
                  </div>
                </label>
                {formData.is_healthy && (
                  <div className="mt-4">
                    <label className="block text-lg font-bold text-green-700 mb-2">Max Calories per Serving</label>
                    <input
                      type="number"
                      value={formData.max_calories_per_serving}
                      onChange={(e) => setFormData({...formData, max_calories_per_serving: parseInt(e.target.value)})}
                      className="w-full px-4 py-3 border-3 border-green-300 rounded-2xl focus:ring-4 focus:ring-green-400 focus:border-green-500 text-center text-lg font-medium bg-white"
                      min="200"
                      max="800"
                      placeholder="400"
                    />
                  </div>
                )}
              </div>

              {/* Budget Mode Toggle */}
              <div className="bg-blue-50 p-4 rounded-xl">
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.is_budget_friendly}
                    onChange={(e) => setFormData({...formData, is_budget_friendly: e.target.checked})}
                    className="rounded text-blue-500"
                  />
                  <div>
                    <span className="font-medium text-blue-800">💰 Budget Mode</span>
                    <p className="text-sm text-blue-600">Set maximum budget</p>
                  </div>
                </label>
                {formData.is_budget_friendly && (
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-blue-700 mb-1">Max Budget ($)</label>
                    <input
                      type="number"
                      value={formData.max_budget}
                      onChange={(e) => setFormData({...formData, max_budget: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      min="5"
                      max="100"
                      placeholder="20"
                    />
                  </div>
                )}
              </div>

              {/* Enhanced Servings and Difficulty */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                    🍽️ Servings
                  </label>
                  <input
                    type="number"
                    value={formData.servings}
                    onChange={(e) => setFormData({...formData, servings: parseInt(e.target.value)})}
                    className="w-full px-4 py-3 border-3 border-gray-200 rounded-2xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 text-center text-lg font-medium bg-gradient-to-r from-gray-50 to-blue-50"
                    min="1"
                    max="12"
                  />
                </div>
                <div>
                  <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                    🔥 Difficulty
                  </label>
                  <select
                    value={formData.difficulty}
                    onChange={(e) => setFormData({...formData, difficulty: e.target.value})}
                    className="w-full px-4 py-3 border-3 border-gray-200 rounded-2xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 text-center text-lg font-medium bg-gradient-to-r from-gray-50 to-blue-50"
                    data-testid="difficulty-select"
                  >
                    {difficultyOptions.map(difficulty => (
                      <option key={difficulty} value={difficulty}>
                        {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Enhanced Optional Fields */}
              <div className="space-y-6">
                <div>
                  <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                    🥘 Ingredients on Hand (Optional)
                  </label>
                  <input
                    type="text"
                    value={formData.ingredients_on_hand}
                    onChange={(e) => setFormData({...formData, ingredients_on_hand: e.target.value})}
                    className="w-full px-4 py-3 border-3 border-gray-200 rounded-2xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 text-lg bg-gradient-to-r from-gray-50 to-blue-50"
                    placeholder="chicken, rice, onions (comma separated)"
                  />
                </div>

                <div>
                  <label className="block text-xl font-bold text-gray-700 mb-4 text-center">
                    ⏰ Max Prep Time (Optional)
                  </label>
                  <input
                    type="number"
                    value={formData.prep_time_max}
                    onChange={(e) => setFormData({...formData, prep_time_max: e.target.value})}
                    className="w-full px-4 py-3 border-3 border-gray-200 rounded-2xl focus:ring-4 focus:ring-purple-300 focus:border-purple-500 text-center text-lg font-medium bg-gradient-to-r from-gray-50 to-blue-50"
                    placeholder="30 minutes"
                  />
                </div>
              </div>

              {/* Enhanced Submit Button */}
              <button
                type="submit"
                disabled={isGenerating}
                className={`w-full py-6 rounded-3xl font-bold text-xl transition-all duration-300 transform hover:scale-105 ${
                  isGenerating 
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 text-white shadow-2xl hover:shadow-3xl'
                }`}
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-4 border-white mr-4"></div>
                    <span className="text-lg">🤖 AI is cooking up your recipe...</span>
                  </span>
                ) : (
                  <span className="flex items-center justify-center">
                    <span className="text-2xl mr-3 animate-bounce">🪄</span>
                    <span>Generate My Perfect Recipe</span>
                    <span className="text-2xl ml-3 animate-bounce">✨</span>
                  </span>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  };

  // Recipe Detail Screen Component - COMPLETELY NEW DESIGN


  // Recipe History Screen Component with Categories
  const RecipeHistoryScreen = () => {
    const [recipes, setRecipes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeCategory, setActiveCategory] = useState('all');
    const [stats, setStats] = useState({
      total_count: 0,
      regular_recipes: 0,
      starbucks_recipes: 0
    });

    const categories = [
      { id: 'all', label: 'All', icon: '📝', color: 'bg-gray-500' },
      { id: 'cuisine', label: 'Cuisine', icon: '🍝', color: 'bg-orange-500' },
      { id: 'snacks', label: 'Snacks', icon: '🍪', color: 'bg-purple-500' },
      { id: 'beverages', label: 'Beverages', icon: '🧋', color: 'bg-blue-500' },
      { id: 'starbucks', label: 'Starbucks', icon: '☕', color: 'bg-green-500' }
    ];

    useEffect(() => {
      fetchRecipes();
    }, []);

    const fetchRecipes = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API}/api/recipes/history/${user?.id || 'demo_user'}`);
        
        if (response.data.success) {
          setRecipes(response.data.recipes);
          setStats({
            total_count: response.data.total_count,
            regular_recipes: response.data.regular_recipes,
            starbucks_recipes: response.data.starbucks_recipes
          });
        } else {
          setRecipes([]);
        }
      } catch (error) {
        // Error fetching recipes
        showNotification('❌ Failed to load recipe history', 'error');
        setRecipes([]);
      } finally {
        setLoading(false);
      }
    };

    const filteredRecipes = activeCategory === 'all' 
      ? recipes 
      : recipes.filter(recipe => recipe.category === activeCategory);

    const getCategoryCount = (categoryId) => {
      if (categoryId === 'all') return recipes.length;
      return recipes.filter(recipe => recipe.category === categoryId).length;
    };

    const viewRecipe = (recipe) => {
      if (recipe.type === 'starbucks') {
        // For Starbucks recipes, show them in the existing Starbucks detail view
        window.currentRecipe = recipe;
        setCurrentScreen('recipe-detail');
      } else {
        // For regular recipes, show them in the regular recipe detail view  
        window.currentRecipe = recipe;
        setCurrentScreen('recipe-detail');
      }
    };

    const deleteRecipe = async (recipeId, recipeType) => {
      if (window.confirm('Are you sure you want to delete this recipe?')) {
        try {
          const endpoint = recipeType === 'starbucks' ? 'starbucks-recipes' : 'recipes';
          await axios.delete(`${API}/api/${endpoint}/${recipeId}`);
          showNotification('✅ Recipe deleted successfully', 'success');
          fetchRecipes(); // Refresh the list
        } catch (error) {
          // Error deleting recipe
          showNotification('❌ Failed to delete recipe', 'error');
        }
      }
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    if (loading) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
          <div className="max-w-6xl mx-auto">
            <div className="text-center py-20">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Your Recipe History</h2>
              <p className="text-gray-600">Fetching all your amazing creations...</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 p-4">
        <div className="max-w-6xl mx-auto">
          
          {/* Header */}
          <div className="text-center mb-8">
            <button
              onClick={() => setCurrentScreen('dashboard')}
              className="mb-4 inline-flex items-center text-gray-600 hover:text-gray-800 font-medium"
            >
              <span className="mr-2">←</span>
              Back to Dashboard
            </button>
            <div className="text-6xl mb-4">📖</div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">Recipe History</h1>
            <p className="text-lg text-gray-600">
              All your culinary creations in one place
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="text-3xl mb-2">📝</div>
              <div className="text-2xl font-bold text-gray-800">{stats.total_count}</div>
              <div className="text-sm text-gray-600">Total Recipes</div>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="text-3xl mb-2">🍳</div>
              <div className="text-2xl font-bold text-orange-600">{stats.regular_recipes}</div>
              <div className="text-sm text-gray-600">Food Recipes</div>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="text-3xl mb-2">☕</div>
              <div className="text-2xl font-bold text-green-600">{stats.starbucks_recipes}</div>
              <div className="text-sm text-gray-600">Starbucks Drinks</div>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 text-center">
              <div className="text-3xl mb-2">🏆</div>
              <div className="text-2xl font-bold text-purple-600">{filteredRecipes.length}</div>
              <div className="text-sm text-gray-600">Showing Now</div>
            </div>
          </div>

          {/* Category Filters */}
          <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Filter by Category</h3>
            <div className="flex flex-wrap gap-3">
              {categories.map(category => (
                <button
                  key={category.id}
                  onClick={() => setActiveCategory(category.id)}
                  className={`flex items-center px-4 py-2 rounded-xl font-medium transition-all duration-200 ${
                    activeCategory === category.id 
                      ? `${category.color} text-white shadow-lg` 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-2">{category.icon}</span>
                  <span>{category.label}</span>
                  <span className="ml-2 text-sm opacity-80">({getCategoryCount(category.id)})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Recipe Grid */}
          {filteredRecipes.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-8xl mb-4">🍽️</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                {activeCategory === 'all' ? 'No Recipes Yet' : `No ${categories.find(c => c.id === activeCategory)?.label} Recipes`}
              </h2>
              <p className="text-gray-600 mb-6">
                {activeCategory === 'all' 
                  ? "Start creating some delicious recipes and viral Starbucks drinks!" 
                  : `Try creating some ${categories.find(c => c.id === activeCategory)?.label.toLowerCase()} recipes!`}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => setCurrentScreen('recipe-generation')}
                  className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-6 rounded-xl transition-all duration-200"
                >
                  🍳 Generate Recipe
                </button>
                <button
                  onClick={() => setCurrentScreen('starbucks-generator')}
                  className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-xl transition-all duration-200"
                >
                  ☕ Create Starbucks Drink
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRecipes.map((recipe) => (
                <div key={recipe.id} className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
                  
                  {/* Recipe Header */}
                  <div className={`p-4 ${
                    recipe.category === 'cuisine' ? 'bg-gradient-to-r from-orange-500 to-red-500' :
                    recipe.category === 'snacks' ? 'bg-gradient-to-r from-purple-500 to-pink-500' :
                    recipe.category === 'beverages' ? 'bg-gradient-to-r from-blue-500 to-cyan-500' :
                    recipe.category === 'starbucks' ? 'bg-gradient-to-r from-green-500 to-teal-500' :
                    'bg-gradient-to-r from-gray-500 to-gray-600'
                  } text-white`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-2xl">{recipe.category_icon}</span>
                      <span className="text-xs opacity-80">{recipe.category_label}</span>
                    </div>
                    <h3 className="text-lg font-bold line-clamp-2">
                      {recipe.type === 'starbucks' ? recipe.drink_name : recipe.title}
                    </h3>
                  </div>

                  {/* Recipe Content */}
                  <div className="p-4">
                    <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                      {recipe.description}
                    </p>
                    
                    {recipe.type === 'starbucks' ? (
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">🎯</span>
                          <span>Base: {recipe.base_drink}</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">🎨</span>
                          <span>{recipe.modifications?.length || 0} modifications</span>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">⏱️</span>
                          <span>{recipe.prep_time + recipe.cook_time} min total</span>
                        </div>
                        <div className="flex items-center text-gray-600">
                          <span className="mr-2">🍽️</span>
                          <span>{recipe.servings} servings</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-500">
                          {formatDate(recipe.created_at)}
                        </span>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => viewRecipe(recipe)}
                            className="bg-blue-500 hover:bg-blue-600 text-white text-xs px-3 py-1 rounded-lg transition-colors"
                          >
                            View
                          </button>
                          <button
                            onClick={() => deleteRecipe(recipe.id, recipe.type)}
                            className="bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1 rounded-lg transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  // For now, let me add a placeholder for other screens
  const OtherScreen = ({ screenName }) => (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">{screenName}</h1>
        <p className="text-gray-600 mb-4">This screen is being updated...</p>
        <button
          onClick={() => setCurrentScreen('dashboard')}
          className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );

  // Handle automatic screen navigation with useEffect to prevent render loops
  useEffect(() => {
    // If user is logged in and on landing, redirect to dashboard
    if (user && currentScreen === 'landing') {
      setCurrentScreen('dashboard');
    }
    
    // If user is not logged in and on protected screen, redirect to landing
    const protectedScreens = ['dashboard', 'generate-recipe', 'all-recipes', 'recipe-detail', 'starbucks-generator', 'welcome-onboarding', 'tutorial'];
    if (!user && protectedScreens.includes(currentScreen)) {
      const savedUser = localStorage.getItem('ai_chef_user');
      if (!savedUser) {
        // No saved session, redirecting to landing
        setCurrentScreen('landing');
      }
    }
  }, [user, currentScreen]);

  // Main render function
  const renderScreen = () => {
    // Show loading screen while checking authentication
    if (isLoadingAuth) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">👨‍🍳</div>
            <div className="w-8 h-8 border-3 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-gray-600">Loading AI Chef...</p>
          </div>
        </div>
      );
    }
    
    // Show loading if waiting for session restoration
    const protectedScreens = ['dashboard', 'generate-recipe', 'all-recipes', 'recipe-detail', 'starbucks-generator', 'welcome-onboarding', 'tutorial'];
    if (!user && protectedScreens.includes(currentScreen)) {
      const savedUser = localStorage.getItem('ai_chef_user');
      if (savedUser) {
        // User session exists, waiting for restoration
        return (
          <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">👨‍🍳</div>
              <div className="w-8 h-8 border-3 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-gray-600">Restoring your session...</p>
            </div>
          </div>
        );
      }
    }
    
    switch (currentScreen) {
      case 'landing':
        return <LandingScreen />;
      case 'register':
        return <RegisterScreen />;
      case 'verify-email':
        return <EmailVerificationScreen />;
      case 'login':
        return <LoginScreen />;
      case 'forgot-password':
        return <ForgotPasswordScreen />;
      case 'reset-password':
        return <ResetPasswordScreen />;
      case 'dashboard':
        return <DashboardScreen />;
      case 'generate-recipe':
        return <RecipeGenerationScreen />;
      case 'all-recipes':
        return <RecipeHistoryScreen />;
      case 'starbucks-generator':
        return <StarbucksGeneratorScreen 
          showNotification={showNotification}
          setCurrentScreen={setCurrentScreen}
          user={user}
          API={API}
        />;
      case 'weekly-recipes':
        return <WeeklyRecipesScreen 
          user={user}
          onBack={() => setCurrentScreen('dashboard')}
          showNotification={showNotification}
          onViewRecipe={(recipeId, source = 'weekly') => {
            console.log('onViewRecipe called with recipeId:', recipeId, 'source:', source);
            if (!recipeId) {
              showNotification('❌ Recipe ID is missing', 'error');
              return;
            }
            console.log('Setting currentRecipeId to:', recipeId);
            console.log('Setting currentRecipeSource to:', source);
            setCurrentRecipeId(recipeId);
            setCurrentRecipeSource(source);
            console.log('Setting currentScreen to recipe-detail');
            setCurrentScreen('recipe-detail');
          }}
        />;
      case 'recipe-detail':
        console.log('Rendering RecipeDetailScreen with currentRecipeId:', currentRecipeId, 'source:', currentRecipeSource);
        return <RecipeDetailScreen 
          key={`${currentRecipeId}-${currentRecipeSource}`} // Force re-render when recipe ID or source changes
          recipeId={currentRecipeId}
          recipeSource={currentRecipeSource}
          onBack={() => {
            // Navigate back to appropriate screen based on source
            if (currentRecipeSource === 'generated') {
              setCurrentScreen('recipe-generation');
            } else if (currentRecipeSource === 'history') {
              setCurrentScreen('recipe-history');
            } else {
              setCurrentScreen('weekly-recipes');
            }
          }}
          showNotification={showNotification}
        />;
      case 'welcome-onboarding':
        return <WelcomeOnboarding 
          user={user}
          setCurrentScreen={setCurrentScreen}
          showNotification={showNotification}
        />;
      case 'tutorial':
        return <TutorialScreen 
          setCurrentScreen={setCurrentScreen}
          showNotification={showNotification}
        />;
      case 'subscription-success':
        return <SubscriptionSuccess 
          onContinue={() => setCurrentScreen('dashboard')}
        />;
      case 'recipe-generation':
        return <RecipeGeneratorScreen
          user={user}
          onBack={() => setCurrentScreen('dashboard')}
          showNotification={showNotification}
          onViewRecipe={(recipeId, source = 'generated') => {
            console.log('onViewRecipe called from generator with recipeId:', recipeId, 'source:', source);
            setCurrentRecipeId(recipeId);
            setCurrentRecipeSource(source);
            setCurrentScreen('recipe-detail');
          }}
        />;
      case 'recipe-history':
        return <RecipeHistoryScreen
          user={user}
          onBack={() => setCurrentScreen('dashboard')}
          showNotification={showNotification}
          onViewRecipe={(recipeId, source = 'history') => {
            if (!recipeId) {
              console.error('❌ Recipe ID is null or undefined in App.js');
              showNotification('❌ Recipe ID is missing', 'error');
              return;
            }
            
            setCurrentRecipeId(recipeId);
            setCurrentRecipeSource(source);
            setCurrentScreen('recipe-detail');
          }}
          onViewStarbucksRecipe={(recipe) => {
            console.log('onViewStarbucksRecipe called with recipe:', recipe);
            // Navigate to Starbucks generator screen for Starbucks recipes
            setCurrentScreen('starbucks-generator');
            showNotification('🌟 Opening Starbucks recipe generator', 'info');
          }}
        />;
      default:
        return <LandingScreen />;
    }
  };

  return (
    <div className="relative">
      {renderScreen()}
      
      {/* Subscription Screen Modal */}
      {showSubscriptionScreen && (
        <SubscriptionScreen 
          user={user}
          onClose={() => setShowSubscriptionScreen(false)}
          onSubscriptionUpdate={(status) => {
            setSubscriptionStatus(status);
            setShowSubscriptionScreen(false);
            showNotification({ message: 'Subscription updated successfully!', type: 'success' });
          }}
        />
      )}
      
      {/* Global Notification */}
      {notification && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-2xl shadow-lg text-white font-medium max-w-sm text-center ${
          notification.type === 'success' ? 'bg-green-500' : 'bg-red-500'
        }`}>
          {notification.message}
        </div>
      )}
    </div>
  );
}

export default App;