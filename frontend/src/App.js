import React, { useState, useEffect } from 'react';
import WelcomeOnboarding from './components/WelcomeOnboarding';
import LoginComponent from './components/LoginComponent';
import VerificationPage from './components/VerificationPage';
import DashboardScreen from './components/DashboardScreen';
import RecipeDetailScreen from './components/RecipeDetailScreen';
import RecipeDetailScreenMobile from './components/RecipeDetailScreenMobile';
import RecipeGeneratorScreen from './components/RecipeGeneratorScreen';
import WeeklyRecipesScreen from './components/WeeklyRecipesScreen';
import StarbucksGeneratorScreen from './components/StarbucksGeneratorScreen';
import RecipeHistoryScreen from './components/RecipeHistoryScreen';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('welcome'); // Start with welcome/onboarding
  const [user, setUser] = useState(null);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [notification, setNotification] = useState(null);
  const [verificationEmail, setVerificationEmail] = useState('');
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  // Check for existing user session on app load
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        setCurrentView('dashboard');
        console.log('🔄 Restored user session:', userData.email);
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        localStorage.removeItem('user');
      }
    }
  }, []); // Keep empty dependency array

  // Handle responsive design changes
  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Expose setCurrentView globally for dashboard navigation
  useEffect(() => {
    window.setCurrentScreen = setCurrentView;
    window.setSelectedRecipe = setSelectedRecipe;
  }, []); // Keep this cleanup as it's for globals

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleLoginSuccess = (userData) => {
    console.log('✅ Login successful, saving user data:', userData);
    
    // FIX: Ensure consistent user object structure
    const normalizedUser = {
      user_id: userData.user_id,
      id: userData.user_id, // Add both fields for compatibility
      email: userData.email,
      name: userData.name,
      verified: userData.verified,
      subscription_status: userData.subscription_status
    };
    
    setUser(normalizedUser);
    localStorage.setItem('user', JSON.stringify(normalizedUser));
    setCurrentView('dashboard');
    showNotification(`Welcome back, ${userData.name || userData.email}!`, 'success');
  };

  const handleVerificationRequired = (data) => {
    console.log('⚠️ Verification required:', data);
    setVerificationEmail(data.email);
    setCurrentView('verification');
    showNotification('Please check your email for verification code.', 'info');
  };

  const handleVerificationSuccess = (data) => {
    console.log('✅ Email verified successfully:', data);
    showNotification('Email verified! You can now log in.', 'success');
    setCurrentView('login');
    setVerificationEmail('');
  };

  const handleRegistrationComplete = (userData) => {
    console.log('✅ Registration complete, saving user data:', userData);
    
    // FIX: Ensure consistent user object structure
    const normalizedUser = {
      user_id: userData.user_id,
      id: userData.user_id, // Add both fields for compatibility
      email: userData.email,
      name: userData.name,
      verified: userData.verified || false,
      subscription_status: userData.subscription_status || 'free'
    };
    
    setUser(normalizedUser);
    localStorage.setItem('user', JSON.stringify(normalizedUser));
    setCurrentView('dashboard');
    showNotification('Welcome! Your account has been created.', 'success');
  };

  const handleLogout = () => {
    console.log('🚪 Logging out user');
    setUser(null);
    localStorage.removeItem('user');
    localStorage.removeItem('userPreferences');
    setCurrentView('welcome');
    showNotification('You have been logged out.', 'info');
  };

  const handleRecipeSelect = (recipe) => {
    setSelectedRecipe(recipe);
    setCurrentView('recipe-detail');
  };

  const handleBackFromRecipe = () => {
    setSelectedRecipe(null);
    setCurrentView('dashboard');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'welcome':
        return (
          <WelcomeOnboarding
            onComplete={handleRegistrationComplete}
            onSkip={() => setCurrentView('login')}
            showLoginOption={true}
            onLoginClick={() => setCurrentView('login')}
          />
        );

      case 'login':
        return (
          <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full">
              {/* Back to Welcome Button */}
              <button
                onClick={() => setCurrentView('welcome')}
                className="mb-4 flex items-center text-blue-600 hover:text-blue-800 font-medium"
              >
                <span className="mr-2">←</span>
                Back to Welcome
              </button>

              {/* Login Card */}
              <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
                <div className="text-center mb-6">
                  <h1 className="text-2xl font-bold text-gray-800 mb-2">Welcome Back!</h1>
                  <p className="text-gray-600">Sign in to your account</p>
                </div>

                <LoginComponent
                  onLoginSuccess={handleLoginSuccess}
                  onVerificationRequired={handleVerificationRequired}
                  onForgotPassword={() => {
                    showNotification('Password reset coming soon!', 'info');
                  }}
                />

                {/* Register Option */}
                <div className="mt-6 text-center">
                  <p className="text-gray-600">
                    Don't have an account?{' '}
                    <button
                      onClick={() => setCurrentView('welcome')}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Create one here
                    </button>
                  </p>
                </div>

                {/* Test Credentials Helper */}
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-center">
                  <p className="text-yellow-800 text-sm font-medium">🧪 Test Credentials:</p>
                  <p className="text-yellow-700 text-xs mt-1">
                    Email: fresh@test.com<br/>
                    Password: password123
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 'verification':
        return (
          <VerificationPage
            email={verificationEmail}
            onVerificationSuccess={handleVerificationSuccess}
            onBackToLogin={() => setCurrentView('login')}
          />
        );

      case 'dashboard':
        return (
          <DashboardScreen
            user={user}
            onLogout={handleLogout}
            onRecipeSelect={handleRecipeSelect}
            showNotification={showNotification}
            setCurrentScreen={setCurrentView}
          />
        );

      case 'recipe-generator':
        return (
          <RecipeGeneratorScreen
            user={user}
            onBack={() => setCurrentView('dashboard')}
            showNotification={showNotification}
            onViewRecipe={(recipeId, source, options) => {
              setSelectedRecipe({ id: recipeId, source, triggerWalmartFetch: options?.triggerWalmartFetch });
              setCurrentView('recipe-detail');
            }}
          />
        );

      case 'weekly-recipes':
        return (
          <WeeklyRecipesScreen
            user={user}
            onBack={() => setCurrentView('dashboard')}
            showNotification={showNotification}
            onViewRecipe={(recipeId, source) => {
              setSelectedRecipe({ id: recipeId, source });
              setCurrentView('recipe-detail');
            }}
          />
        );

      case 'starbucks-generator':
        return (
          <StarbucksGeneratorScreen
            user={user}
            setCurrentScreen={setCurrentView}
            showNotification={showNotification}
          />
        );

      case 'recipe-history':
        return (
          <RecipeHistoryScreen
            user={user}
            onBack={() => setCurrentView('dashboard')}
            showNotification={showNotification}
            onViewRecipe={(recipeId, source) => {
              setSelectedRecipe({ id: recipeId, source });
              setCurrentView('recipe-detail');
            }}
            onViewStarbucksRecipe={(recipe) => {
              setSelectedRecipe(recipe);
              setCurrentView('starbucks-detail');
            }}
          />
        );

      case 'recipe-detail':
        return selectedRecipe ? (
          isMobile ? (
            <RecipeDetailScreenMobile
              recipeId={selectedRecipe.id}
              recipeSource={selectedRecipe.source || "generated"}
              triggerWalmartFetch={selectedRecipe.triggerWalmartFetch}
              onBack={() => {
                // FIX: Better back navigation based on source
                if (selectedRecipe.source === 'generated') {
                  setCurrentView('recipe-generator');
                } else if (selectedRecipe.source === 'history') {
                  setCurrentView('recipe-history');
                } else if (selectedRecipe.source === 'weekly') {
                  setCurrentView('weekly-recipes');
                } else {
                  setCurrentView('dashboard');
                }
              }}
              showNotification={showNotification}
            />
          ) : (
            <RecipeDetailScreen
              recipeId={selectedRecipe.id}
              recipeSource={selectedRecipe.source || "generated"}
              triggerWalmartFetch={selectedRecipe.triggerWalmartFetch}
              onBack={() => {
                // FIX: Better back navigation based on source
                if (selectedRecipe.source === 'generated') {
                  setCurrentView('recipe-generator');
                } else if (selectedRecipe.source === 'history') {
                  setCurrentView('recipe-history');
                } else if (selectedRecipe.source === 'weekly') {
                  setCurrentView('weekly-recipes');
                } else {
                  setCurrentView('dashboard');
                }
              }}
              showNotification={showNotification}
            />
          )
        ) : (
          <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
              <div className="text-4xl mb-4">❌</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Recipe Not Found</h2>
              <p className="text-gray-600 mb-6">The recipe you're looking for could not be loaded.</p>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
              >
                ← Back to Dashboard
              </button>
            </div>
          </div>
        );

      case 'settings':
        return (
          <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
              <div className="text-4xl mb-4">⚙️</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Settings</h2>
              <p className="text-gray-600 mb-6">User settings and preferences coming soon!</p>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
              >
                ← Back to Dashboard
              </button>
            </div>
          </div>
        );

      case 'shopping-list':
        return (
          <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
              <div className="text-4xl mb-4">🛒</div>
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Shopping List</h2>
              <p className="text-gray-600 mb-6">Smart shopping list features coming soon!</p>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors"
              >
                ← Back to Dashboard
              </button>
            </div>
          </div>
        );

      default:
        return (
          <div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Page Not Found</h2>
              <button
                onClick={() => setCurrentView('welcome')}
                className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600"
              >
                Go to Welcome
              </button>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="App">
      {/* Global Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
          notification.type === 'success' ? 'bg-green-500 text-white' :
          notification.type === 'error' ? 'bg-red-500 text-white' :
          notification.type === 'warning' ? 'bg-yellow-500 text-white' :
          'bg-blue-500 text-white'
        }`}>
          <div className="flex items-center justify-between">
            <span>{notification.message}</span>
            <button
              onClick={() => setNotification(null)}
              className="ml-4 text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      {renderCurrentView()}
    </div>
  );
}

export default App;