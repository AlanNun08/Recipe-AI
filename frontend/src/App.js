import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import StarbucksGeneratorScreen from './components/StarbucksGeneratorScreen';
import WelcomeOnboarding from './components/WelcomeOnboarding';
import TutorialScreen from './components/TutorialScreen';
import SubscriptionScreen from './components/SubscriptionScreen';
import SubscriptionSuccess from './components/SubscriptionSuccess';
import SubscriptionGate from './components/SubscriptionGate';

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
  const [pendingResetEmail, setPendingResetEmail] = useState(null);
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  
  // Subscription states
  const [showSubscriptionScreen, setShowSubscriptionScreen] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);

  // Load user session from localStorage on app start - PRODUCTION FIX
  useEffect(() => {
    const loadUserSession = () => {
      try {
        const savedUser = localStorage.getItem('ai_chef_user');
        if (savedUser) {
          const userData = JSON.parse(savedUser);
          // Restore user session
          setUser(userData);
          // Only set to dashboard if we're on landing page or if currentScreen is a protected route
          if (currentScreen === 'landing' || !['landing', 'register', 'verify-email', 'login', 'forgot-password', 'reset-password'].includes(currentScreen)) {
            // Set screen to dashboard
            setCurrentScreen('dashboard');
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

  // Clear user session from localStorage
  const clearUserSession = () => {
    try {
      localStorage.removeItem('ai_chef_user');
      // Session cleared
    } catch (error) {
      // Failed to clear session
    }
  };

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

  // Notification system
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
        console.error('Registration failed:', error);
        const errorMessage = error.response?.data?.detail || 'Registration failed. Please try again.';
        showNotification(`❌ ${errorMessage}`, 'error');
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

        setUser(response.data.user);
        setCurrentScreen('dashboard');
        showNotification('🎉 Email verified successfully! Welcome to AI Chef!', 'success');
        
      } catch (error) {
        console.error('Verification failed:', error);
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
        console.error('Resend failed:', error);
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
          setUser(response.data.user);
          setCurrentScreen('dashboard');
          
          // Mark user as onboarded to skip tutorial for returning users
          localStorage.setItem(`user_${response.data.user.id}_onboarded`, 'true');
          
          showNotification(`🎉 Welcome back, ${response.data.user.first_name}!`, 'success');
        }
        
      } catch (error) {
        console.error('Login failed:', error);
        const errorMessage = error.response?.data?.detail || 'Login failed. Please check your credentials.';
        showNotification(`❌ ${errorMessage}`, 'error');
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

  // Enhanced Dashboard Screen Component
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
          <button
            onClick={() => setCurrentScreen('generate-recipe')}
            className="w-full bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg relative overflow-hidden"
          >
            <span className="relative z-10 flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">🍳</span>
              Generate AI Recipe
              <span className="text-2xl ml-3 animate-bounce">✨</span>
            </span>
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
          
          <button
            onClick={() => setCurrentScreen('all-recipes')}
            className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white font-bold py-6 px-8 rounded-3xl shadow-2xl hover:shadow-3xl transform hover:-translate-y-2 transition-all duration-300 text-lg"
          >
            <span className="flex items-center justify-center">
              <span className="text-2xl mr-3 animate-bounce">📜</span>
              Recipe History
              <span className="text-2xl ml-3 animate-pulse">🏆</span>
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
              <span className="text-3xl mr-4 animate-bounce">🤖</span>
              <span className="text-gray-700 font-medium">Generate personalized recipes with AI</span>
            </div>
            <div className="flex items-center p-4 bg-white rounded-2xl shadow-lg">
              <span className="text-3xl mr-4 animate-pulse">🛒</span>
              <span className="text-gray-700 font-medium">Instant Walmart grocery delivery</span>
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
            setUser(null);
            clearUserSession(); // Clear localStorage
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
        console.error('Password reset request failed:', error);
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
        console.error('Password reset failed:', error);
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
        console.error('Recipe generation failed:', error);
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
  const RecipeDetailScreen = ({ recipe, showBackButton = false }) => {
    const [productOptions, setProductOptions] = useState({}); // Store all product options per ingredient
    const [selectedProducts, setSelectedProducts] = useState({}); // Store user selections
    const [cartItems, setCartItems] = useState([]);
    const [finalWalmartUrl, setFinalWalmartUrl] = useState(null);
    const [loadingCart, setLoadingCart] = useState(false);

    // Auto-generate product options when recipe loads using real Walmart API
    useEffect(() => {
      if (recipe?.id && (recipe?.shopping_list?.length > 0 || recipe?.ingredients?.length > 0)) {
        setLoadingCart(true);
        
        // Call the backend API to get real Walmart product options
        axios.post(`${API}/api/grocery/cart-options`, {}, {
          params: {
            recipe_id: recipe.id,
            user_id: user?.id || 'demo_user'
          }
        })
        .then(response => {
          console.log('✅ Cart options response:', response.data);
          
          // Handle the case where no products are found
          if (response.data && response.data.status === 'no_products_found') {
            console.log('⚠️ No Walmart products found for this recipe');
            setProductOptions({});
            setSelectedProducts({});
            setCartItems([]);
            setFinalWalmartUrl('');
            return; // Exit early
          }
          
          console.log('🛒 Cart options response:', response.data);
          
          // Check for correct backend format: response.data.ingredient_options
          if (response.data && response.data.ingredient_options) {
            // Store all product options per ingredient - CORRECT BACKEND FORMAT
            const options = {};
            const defaultSelections = {};
            const newCartItems = [];
            
            // Process correct format: ingredient_options array with options sub-arrays
            response.data.ingredient_options.forEach((ingredientOption, index) => {
              const ingredientName = ingredientOption.ingredient_name || ingredientOption.original_ingredient;
              
              // Backend uses 'options' field (not 'products')
              if (ingredientOption.options && ingredientOption.options.length > 0) {
                // Store all options for this ingredient
                options[ingredientName] = ingredientOption.options;
                
                // Default to first option
                const firstProduct = ingredientOption.options[0];
                defaultSelections[ingredientName] = firstProduct.product_id;
                
                // Add to cart with first product
                newCartItems.push({
                  name: firstProduct.name || ingredientName,
                  price: parseFloat(firstProduct.price) || 2.99,
                  quantity: 1,
                  product_id: firstProduct.product_id,
                  ingredient_name: ingredientName
                });
              }
            });
            
            setProductOptions(options);
            setSelectedProducts(defaultSelections);
            setCartItems(newCartItems);
            
            // Generate affiliate URL with default selections
            // Generate Walmart URL with correct format using SELECTED items only
            const walmartItems = [];
            const finalQuantities = {};
            
            // Count quantities for SELECTED products only (from cartItems)
            newCartItems.forEach(item => {
              if (item.product_id) {
                const quantity = (typeof item.quantity === 'number' && item.quantity > 0) ? item.quantity : 1;
                const qty = finalQuantities[item.product_id] || 0;
                finalQuantities[item.product_id] = qty + quantity;
              }
            });
            
            // Format for Walmart URL: productId or productId_quantity
            Object.entries(finalQuantities).forEach(([productId, quantity]) => {
              if (productId) {
                if (quantity === 1) {
                  walmartItems.push(productId);
                } else {
                  walmartItems.push(`${productId}_${Math.floor(quantity)}`);
                }
              }
            });
            
            if (walmartItems.length > 0) {
              setFinalWalmartUrl(`https://affil.walmart.com/cart/addToCart?items=${walmartItems.join(',')}`);
              console.log('✅ Walmart URL generated with SELECTED items only:', walmartItems.length, 'items');
            } else {
              console.warn('⚠️ No selected items for Walmart URL generation');
              setFinalWalmartUrl('');
            };
            
            console.log('✅ Product options loaded:', Object.keys(options).length, 'ingredients');
          } else {
            // No valid API response - check for different formats
            console.log('⚠️ API Response Debug:', response.data);
            if (response.data && response.data.ingredients) {
              console.log('⚠️ Found ingredients format (old), expected ingredient_options format');
            } else {
              console.log('⚠️ Invalid API response - only real Walmart products are used');
            }
          }
        })
        .catch(error => {
          console.error('❌ Error fetching cart options:', error);
          console.log('ℹ️ No cart generated - only real Walmart products are used');
        })
        .finally(() => {
          setLoadingCart(false);
        });
      }
    }, [recipe, user]);

    // Handle product selection change
    const handleProductSelection = (ingredientName, productId) => {
      const selectedProduct = productOptions[ingredientName]?.find(p => p.product_id === productId);
      if (!selectedProduct) return;

      // Update selected products
      const newSelections = { ...selectedProducts, [ingredientName]: productId };
      setSelectedProducts(newSelections);

      // Update cart items with new selection
      const updatedCartItems = cartItems.map(item => {
        if (item.ingredient_name === ingredientName) {
          return {
            ...item,
            name: selectedProduct.name,
            price: parseFloat(selectedProduct.price),
            product_id: selectedProduct.product_id
          };
        }
        return item;
      });

      setCartItems(updatedCartItems);

      // Regenerate affiliate URL
      // Generate Walmart URL with correct format: items=ID1,ID2_quantity,ID3
      const walmartItems = [];
      const finalQuantities = {};
      
      // Count quantities for each product
      updatedCartItems.forEach(item => {
        if (item.product_id) {
          const quantity = (typeof item.quantity === 'number' && item.quantity > 0) ? item.quantity : 1;
          const qty = finalQuantities[item.product_id] || 0;
          finalQuantities[item.product_id] = qty + quantity;
        }
      });
      
      // Format for Walmart URL: productId or productId_quantity
      Object.entries(finalQuantities).forEach(([productId, quantity]) => {
        if (productId) {
          if (quantity === 1) {
            walmartItems.push(productId);
          } else {
            walmartItems.push(`${productId}_${Math.floor(quantity)}`);
          }
        }
      });
      
      if (walmartItems.length > 0) {
        setFinalWalmartUrl(`https://affil.walmart.com/cart/addToCart?items=${walmartItems.join(',')}`);
      } else {
        setFinalWalmartUrl('');
      };

      console.log('✅ Product selection updated for', ingredientName, ':', selectedProduct.name);
    };

    // Update quantity and regenerate URL
    const updateQuantity = (index, newQuantity) => {
      if (newQuantity < 1) return;
      const updatedItems = cartItems.map((item, i) => 
        i === index ? { ...item, quantity: newQuantity } : item
      );
      setCartItems(updatedItems);
      
      // Generate Walmart URL with correct format: items=ID1,ID2_quantity,ID3
      const walmartItems = [];
      const finalQuantities = {};
      
      // Count quantities for each product
      updatedItems.forEach(item => {
        if (item.product_id) {
          const quantity = (typeof item.quantity === 'number' && item.quantity > 0) ? item.quantity : 1;
          const qty = finalQuantities[item.product_id] || 0;
          finalQuantities[item.product_id] = qty + quantity;
        }
      });
      
      // Format for Walmart URL: productId or productId_quantity
      Object.entries(finalQuantities).forEach(([productId, quantity]) => {
        if (productId) {
          if (quantity === 1) {
            walmartItems.push(productId);
          } else {
            walmartItems.push(`${productId}_${Math.floor(quantity)}`);
          }
        }
      });
      
      if (walmartItems.length > 0) {
        setFinalWalmartUrl(`https://affil.walmart.com/cart/addToCart?items=${walmartItems.join(',')}`);
      } else {
        setFinalWalmartUrl('');
      }
    };

    // Remove item and regenerate URL
    const removeItem = (index) => {
      const updatedItems = cartItems.filter((_, i) => i !== index);
      setCartItems(updatedItems);
      
      // Generate Walmart URL with correct format: items=ID1,ID2_quantity,ID3
      const walmartItems = [];
      const finalQuantities = {};
      
      // Count quantities for each product
      updatedItems.forEach(item => {
        if (item.product_id) {
          const quantity = (typeof item.quantity === 'number' && item.quantity > 0) ? item.quantity : 1;
          const qty = finalQuantities[item.product_id] || 0;
          finalQuantities[item.product_id] = qty + quantity;
        }
      });
      
      // Format for Walmart URL: productId or productId_quantity
      Object.entries(finalQuantities).forEach(([productId, quantity]) => {
        if (productId) {
          if (quantity === 1) {
            walmartItems.push(productId);
          } else {
            walmartItems.push(`${productId}_${Math.floor(quantity)}`);
          }
        }
      });
      
      if (walmartItems.length > 0) {
        setFinalWalmartUrl(`https://affil.walmart.com/cart/addToCart?items=${walmartItems.join(',')}`);
      } else {
        setFinalWalmartUrl('');
      }
    };

    // Calculate total price
    const calculateTotal = () => {
      return cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
    };

    // Copy URL to clipboard
    const copyUrlToClipboard = async () => {
      try {
        await navigator.clipboard.writeText(finalWalmartUrl);
        showNotification('🎉 Walmart link copied! Open new tab and paste to shop. Your selections are saved - you can continue making changes.', 'success');
      } catch (err) {
        showNotification('❌ Failed to copy. Please copy manually from the text box above.', 'error');
      }
    };

    // Special layout for Starbucks recipes
    if (recipe?.drink_name || recipe?.base_drink || recipe?.ordering_script) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 p-4">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              {showBackButton && (
                <button
                  onClick={() => setCurrentScreen('dashboard')}
                  className="mb-4 flex items-center space-x-2 text-green-600 hover:text-green-700 font-medium"
                >
                  <span>←</span>
                  <span>Back to Dashboard</span>
                </button>
              )}
              
              <div className="text-center">
                <div className="text-6xl mb-4">☕</div>
                <h1 className="text-4xl font-bold text-gray-800 mb-2">{recipe.drink_name}</h1>
                <p className="text-lg text-gray-600">{recipe.description}</p>
              </div>
            </div>

            {/* Starbucks Recipe Card */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              
              {/* Base Drink Section */}
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <span className="mr-2">☕</span>
                  Base Drink
                </h3>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-lg font-medium text-gray-800">{recipe.base_drink}</p>
                </div>
              </div>

              {/* Modifications Section */}
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <span className="mr-2">🎨</span>
                  Modifications
                </h3>
                <div className="space-y-3">
                  {recipe.modifications?.map((modification, index) => (
                    <div key={index} className="flex items-start p-4 bg-gray-50 rounded-lg">
                      <span className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4 mt-0.5">
                        {index + 1}
                      </span>
                      <p className="text-gray-800 leading-relaxed">{modification}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Ordering Script Section */}
              <div className="mb-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                  <span className="mr-2">💬</span>
                  How to Order
                </h3>
                <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-lg">
                  <p className="text-lg text-gray-800 italic">"{recipe.ordering_script}"</p>
                </div>
              </div>

              {/* Pro Tips Section */}
              {recipe.pro_tips && recipe.pro_tips.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                    <span className="mr-2">💡</span>
                    Pro Tips
                  </h3>
                  <div className="space-y-3">
                    {recipe.pro_tips.map((tip, index) => (
                      <div key={index} className="flex items-start p-4 bg-blue-50 rounded-lg">
                        <span className="text-blue-500 mr-3 mt-1">•</span>
                        <p className="text-gray-800">{tip}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Why Amazing Section */}
              {recipe.why_amazing && (
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                    <span className="mr-2">🔥</span>
                    Why This Drink is Amazing
                  </h3>
                  <div className="bg-purple-50 rounded-lg p-6">
                    <p className="text-gray-800 leading-relaxed">{recipe.why_amazing}</p>
                  </div>
                </div>
              )}

              {/* Share Section */}
              <div className="text-center">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Share this Starbucks hack!</h3>
                <p className="text-gray-600 mb-4">Spread the word about this amazing drink creation</p>
                <div className="flex justify-center space-x-4">
                  <button 
                    onClick={() => {
                      const text = `Try this amazing Starbucks hack: ${recipe.drink_name}! Order: ${recipe.ordering_script}`;
                      navigator.clipboard.writeText(text);
                      showNotification('📱 Recipe copied to clipboard!', 'success');
                    }}
                    className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    📱 Copy Recipe
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (!recipe) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-20">
              <div className="text-6xl mb-4">🍳</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">No Recipe Found</h2>
              <p className="text-gray-600">Please generate a recipe first to see the details.</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 p-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            {showBackButton && (
              <button
                onClick={() => setCurrentScreen('dashboard')}
                className="mb-6 flex items-center space-x-2 text-blue-600 hover:text-blue-700 font-medium transition-all duration-200 hover:translate-x-1"
              >
                <svg className="w-5 h-5 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                <span>Back to Dashboard</span>
              </button>
            )}
            
            <div className="bg-white rounded-3xl shadow-2xl p-8 text-center transform hover:scale-105 transition-all duration-300 border border-gray-100">
              <div className="text-6xl mb-4 animate-bounce">🍳</div>
              <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-gray-800 to-gray-600 bg-clip-text text-transparent mb-4">
                {recipe.title || 'Delicious Recipe'}
              </h1>
              <p className="text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
                {recipe.description || 'A wonderful recipe created just for you with real Walmart shopping integration!'}
              </p>
              
              {/* Recipe Tags */}
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {recipe.category && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {recipe.category.charAt(0).toUpperCase() + recipe.category.slice(1)}
                  </span>
                )}
                {recipe.dietary_preferences && recipe.dietary_preferences.map((pref, index) => (
                  <span key={index} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                    {pref}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Enhanced Walmart Shopping Section - Now at Top */}
          <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-purple-800 rounded-3xl shadow-2xl p-8 text-white mb-8 transform hover:scale-105 transition-all duration-300">
            <div className="text-center mb-8">
              <div className="w-24 h-24 bg-gradient-to-br from-white to-gray-100 rounded-full flex items-center justify-center mx-auto mb-6 transform hover:scale-110 transition-all duration-300 shadow-lg">
                <span className="text-blue-600 text-4xl font-bold">W</span>
              </div>
              <h2 className="text-3xl font-bold mb-4">🛒 One-Click Walmart Shopping</h2>
              <p className="text-xl text-blue-100 font-medium mb-4">Real products • Real prices • Real delivery</p>
              <div className="flex items-center justify-center">
                <span className="w-3 h-3 bg-green-400 rounded-full animate-pulse mr-3"></span>
                <span className="text-lg font-medium">Live inventory check</span>
              </div>
            </div>

            {loadingCart ? (
              <div className="text-center py-16">
                <div className="w-20 h-20 border-4 border-white border-t-transparent rounded-full animate-spin mx-auto mb-8"></div>
                <p className="text-2xl font-bold mb-4">🔍 Finding Perfect Products...</p>
                <p className="text-lg text-blue-100 mb-6">Searching Walmart's inventory for your ingredients</p>
                <div className="flex justify-center space-x-2">
                  <div className="w-3 h-3 bg-white rounded-full animate-bounce"></div>
                  <div className="w-3 h-3 bg-white rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-3 h-3 bg-white rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                {Object.entries(productOptions).map(([ingredientName, ingredientOptions], index) => {
                  const selectedProductId = selectedProducts[ingredientName];
                  const selectedProduct = ingredientOptions.find(p => p.product_id === selectedProductId) || ingredientOptions[0];
                  
                  return (
                    <div key={index} className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20 hover:bg-white/20 transition-all duration-300">
                      {/* Ingredient Header */}
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="font-bold text-white flex items-center">
                          <span className="w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center text-white text-sm font-bold mr-3">
                            {index + 1}
                          </span>
                          {ingredientName}
                        </h4>
                        <span className="text-xs text-blue-200 bg-white/20 px-3 py-1 rounded-full font-medium">
                          {ingredientOptions.length} options
                        </span>
                      </div>
                      
                      {/* Selected Product Display */}
                      {selectedProduct && (
                        <div className="bg-white/20 rounded-xl p-4 mb-4 border border-white/30">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h5 className="font-semibold text-white text-sm leading-tight mb-2">
                                {selectedProduct.name}
                              </h5>
                              <p className="text-2xl font-bold text-yellow-300 mb-2">
                                ${parseFloat(selectedProduct.price).toFixed(2)}
                              </p>
                              <div className="flex items-center text-sm text-blue-200">
                                <span className="w-3 h-3 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                                <span className="font-medium">In Stock</span>
                              </div>
                            </div>
                            {selectedProduct.image_url && (
                              <img 
                                src={selectedProduct.image_url} 
                                alt={selectedProduct.name}
                                className="w-16 h-16 object-cover rounded-xl ml-4 border-2 border-white/30 shadow-md hover:scale-105 transition-transform"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                }}
                              />
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Product Selection Dropdown */}
                      {ingredientOptions.length > 1 && (
                        <select 
                          value={selectedProductId || ingredientOptions[0]?.product_id || ''} 
                          onChange={(e) => handleProductSelection(ingredientName, e.target.value)}
                          className="w-full p-3 border-0 rounded-xl text-sm bg-white/20 backdrop-blur-sm text-white focus:ring-2 focus:ring-yellow-400 focus:bg-white/30 hover:bg-white/30 transition-all duration-200 font-medium"
                        >
                          {ingredientOptions.map((product, productIndex) => (
                            <option key={productIndex} value={product.product_id} className="text-gray-800">
                              {product.name} - ${parseFloat(product.price).toFixed(2)}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Enhanced Shopping Cart Summary */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <h4 className="text-2xl font-bold mb-6 flex items-center justify-center">
                <span className="mr-3 text-3xl">🛍️</span>
                <span>Your Cart</span>
              </h4>
              
              <div className="space-y-3 mb-6">
                {cartItems.length > 0 ? (
                  cartItems.map((item, index) => (
                    <div key={index} className="flex justify-between items-center py-3 px-4 bg-white/10 rounded-xl backdrop-blur-sm border border-white/20">
                      <span className="text-sm font-medium truncate flex-1 mr-3">{item.name}</span>
                      <span className="text-xl font-bold text-yellow-300">${parseFloat(item.price).toFixed(2)}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-white/80">
                    <div className="text-4xl mb-4">🛍️</div>
                    <p className="text-lg font-medium">Select ingredients to start shopping</p>
                  </div>
                )}
              </div>
              
              <div className="border-t border-white/20 pt-6 mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-2xl font-bold">Total:</span>
                  <span className="text-3xl font-bold text-yellow-300">${calculateTotal().toFixed(2)}</span>
                </div>
                <p className="text-sm text-blue-200">{cartItems.length} items • Ready for delivery</p>
              </div>
              
              <button
                onClick={copyUrlToClipboard}
                disabled={cartItems.length === 0}
                className={`w-full py-6 rounded-2xl font-bold text-xl transition-all duration-300 transform ${
                  cartItems.length > 0
                    ? 'bg-white text-blue-600 hover:bg-yellow-50 shadow-2xl hover:shadow-3xl hover:scale-105 hover:text-blue-700'
                    : 'bg-white/20 text-white/50 cursor-not-allowed'
                }`}
              >
                {cartItems.length > 0 ? (
                  <>
                    <div className="flex items-center justify-center">
                      <span className="mr-3 text-2xl">🛒</span>
                      <span>Shop at Walmart Now</span>
                      <span className="ml-3 text-2xl">✨</span>
                    </div>
                    <div className="text-sm font-normal mt-2 opacity-80">One-click checkout • Same-day delivery</div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center justify-center">
                      <span className="mr-2 text-2xl">🛍️</span>
                      <span>Select Products First</span>
                    </div>
                    <div className="text-sm font-normal mt-1 opacity-60">Choose your ingredients above</div>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Left Column - Recipe Instructions */}
            <div className="space-y-8">
              
              {/* Recipe Quick Stats */}
              <div className="bg-white rounded-3xl shadow-xl p-8 transform hover:shadow-2xl transition-all duration-300 border border-gray-100">
                <h2 className="text-2xl font-bold text-gray-800 mb-8 flex items-center">
                  <span className="mr-4 text-3xl">📊</span>
                  <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Recipe Overview</span>
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="text-center p-6 bg-gradient-to-br from-orange-100 to-orange-200 rounded-2xl transform hover:scale-105 transition-all duration-300 hover:shadow-lg">
                    <div className="text-4xl mb-3 animate-pulse">⏱️</div>
                    <div className="text-sm text-gray-600 font-medium mb-1">Prep Time</div>
                    <div className="text-2xl font-bold text-orange-800">{recipe.prep_time || '30'}</div>
                    <div className="text-sm text-orange-600 font-medium">minutes</div>
                  </div>
                  <div className="text-center p-6 bg-gradient-to-br from-blue-100 to-blue-200 rounded-2xl transform hover:scale-105 transition-all duration-300 hover:shadow-lg">
                    <div className="text-4xl mb-3 animate-pulse">🍽️</div>
                    <div className="text-sm text-gray-600 font-medium mb-1">Servings</div>
                    <div className="text-2xl font-bold text-blue-800">{recipe.servings || '4'}</div>
                    <div className="text-sm text-blue-600 font-medium">people</div>
                  </div>
                  <div className="text-center p-6 bg-gradient-to-br from-green-100 to-green-200 rounded-2xl transform hover:scale-105 transition-all duration-300 hover:shadow-lg">
                    <div className="text-4xl mb-3 animate-pulse">🔥</div>
                    <div className="text-sm text-gray-600 font-medium mb-1">Difficulty</div>
                    <div className="text-2xl font-bold text-green-800">{recipe.difficulty || 'Medium'}</div>
                    <div className="text-sm text-green-600 font-medium">level</div>
                  </div>
                  <div className="text-center p-6 bg-gradient-to-br from-purple-100 to-purple-200 rounded-2xl transform hover:scale-105 transition-all duration-300 hover:shadow-lg">
                    <div className="text-4xl mb-3 animate-pulse">💰</div>
                    <div className="text-sm text-gray-600 font-medium mb-1">Est. Cost</div>
                    <div className="text-2xl font-bold text-purple-800">${calculateTotal().toFixed(2)}</div>
                    <div className="text-sm text-purple-600 font-medium">total</div>
                  </div>
                </div>
              </div>

              {/* Ingredients List */}
              <div className="bg-white rounded-3xl shadow-xl p-8 transform hover:shadow-2xl transition-all duration-300 border border-gray-100">
                <h3 className="text-2xl font-bold text-gray-800 mb-8 flex items-center">
                  <span className="mr-4 text-3xl">🥘</span>
                  <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">Ingredients</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(recipe.ingredients || []).map((ingredient, index) => (
                    <div key={index} className="flex items-center p-4 bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl hover:from-slate-100 hover:to-blue-100 transition-all duration-200 group">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm mr-4 flex-shrink-0 group-hover:scale-110 transition-transform">
                        {index + 1}
                      </div>
                      <span className="text-gray-700 font-medium flex-1">{ingredient}</span>
                      <div className="w-2 h-2 bg-green-400 rounded-full opacity-60 group-hover:opacity-100 transition-opacity"></div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cooking Instructions */}
              <div className="bg-white rounded-3xl shadow-xl p-8 transform hover:shadow-2xl transition-all duration-300 border border-gray-100">
                <h3 className="text-2xl font-bold text-gray-800 mb-8 flex items-center">
                  <span className="mr-4 text-3xl">👨‍🍳</span>
                  <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Cooking Instructions</span>
                </h3>
                <div className="space-y-6">
                  {(recipe.instructions || []).map((instruction, index) => (
                    <div key={index} className="flex items-start p-6 bg-gradient-to-r from-slate-50 to-indigo-50 rounded-2xl hover:from-slate-100 hover:to-indigo-100 transition-all duration-300 group">
                      <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-lg mr-6 flex-shrink-0 group-hover:scale-110 transition-transform">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-700 leading-relaxed font-medium text-lg">{instruction}</p>
                        <div className="mt-3 h-1 bg-gradient-to-r from-green-400 to-blue-500 rounded-full transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500"></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column - Recipe Tips & Extras */}
            <div className="space-y-8">
              
              {/* Recipe Tips */}
              <div className="bg-white rounded-3xl shadow-xl p-8 transform hover:shadow-2xl transition-all duration-300 border border-gray-100">
                <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <span className="mr-4 text-3xl">💡</span>
                  <span className="bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">Pro Tips</span>
                </h3>
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-yellow-50 to-orange-50 rounded-2xl border-l-4 border-yellow-500">
                    <h4 className="font-bold text-gray-800 mb-2">🔥 Cooking Tip</h4>
                    <p className="text-gray-700">Let ingredients come to room temperature before cooking for better flavor and texture.</p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-2xl border-l-4 border-green-500">
                    <h4 className="font-bold text-gray-800 mb-2">🛒 Shopping Tip</h4>
                    <p className="text-gray-700">Buy ingredients in bulk to save money and reduce packaging waste.</p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl border-l-4 border-purple-500">
                    <h4 className="font-bold text-gray-800 mb-2">⏰ Time Saver</h4>
                    <p className="text-gray-700">Prep ingredients the night before for faster cooking the next day.</p>
                  </div>
                </div>
              </div>

              {/* Nutritional Benefits */}
              <div className="bg-white rounded-3xl shadow-xl p-8 transform hover:shadow-2xl transition-all duration-300 border border-gray-100">
                <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                  <span className="mr-4 text-3xl">🌟</span>
                  <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">Recipe Benefits</span>
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-2xl">
                    <span className="text-3xl mr-4">🥗</span>
                    <div>
                      <h4 className="font-bold text-gray-800">Nutritious</h4>
                      <p className="text-sm text-gray-600">Balanced ingredients for optimal health</p>
                    </div>
                  </div>
                  <div className="flex items-center p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-2xl">
                    <span className="text-3xl mr-4">💰</span>
                    <div>
                      <h4 className="font-bold text-gray-800">Budget-Friendly</h4>
                      <p className="text-sm text-gray-600">Affordable ingredients that don't compromise on taste</p>
                    </div>
                  </div>
                  <div className="flex items-center p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-2xl">
                    <span className="text-3xl mr-4">👨‍🍳</span>
                    <div>
                      <h4 className="font-bold text-gray-800">Easy to Make</h4>
                      <p className="text-sm text-gray-600">Simple steps that anyone can follow</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Save Recipe Action */}
              <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl shadow-2xl p-8 text-white text-center transform hover:scale-105 transition-all duration-300">
                <div className="text-5xl mb-4 animate-bounce">💾</div>
                <h3 className="text-2xl font-bold mb-4">Save This Recipe!</h3>
                <p className="text-lg mb-6">Never lose this amazing recipe again</p>
                <button className="bg-white text-purple-600 font-bold py-3 px-8 rounded-2xl hover:bg-gray-100 transition-colors transform hover:scale-105">
                  <span className="flex items-center justify-center">
                    <span className="mr-2">❤️</span>
                    Add to Favorites
                  </span>
                </button>
              </div>

            </div>
          </div>
        </div>
      </div>
    );
  };

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
        console.error('Error fetching recipes:', error);
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
          console.error('Error deleting recipe:', error);
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
        console.log('🔄 No saved session found, redirecting to landing from:', currentScreen);
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
        console.log('⏳ User session exists in localStorage, waiting for restoration...');
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
      case 'recipe-detail':
        return <RecipeDetailScreen recipe={window.currentRecipe} showBackButton={true} />;
      case 'starbucks-generator':
        return <StarbucksGeneratorScreen 
          showNotification={showNotification}
          setCurrentScreen={setCurrentScreen}
          user={user}
          API={API}
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