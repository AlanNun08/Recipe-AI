import React, { useState } from 'react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

const WelcomeOnboarding = ({
  onComplete,
  onSkip,
  showLoginOption = false,
  onLoginClick,
  onRegistrationVerificationRequired,
  simpleSignupMode = true
}) => {
  const [currentStep, setCurrentStep] = useState(simpleSignupMode ? 2 : 0);
  const [showDemo, setShowDemo] = useState(false);
  const [sampleRecipe, setSampleRecipe] = useState(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationError, setRegistrationError] = useState('');
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showRegisterConfirmPassword, setShowRegisterConfirmPassword] = useState(false);
  const [userPreferences, setUserPreferences] = useState({
    quickPrefs: [],
    budget: '',
    dietaryRestrictions: [],
    cuisinePreferences: [],
    cookingSkillLevel: '',
    householdSize: 4,
    weeklyBudget: ''
  });

  const [registrationData, setRegistrationData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    agreeTerms: false,
    emailUpdates: true
  });

  const steps = [
    { id: 'hero', title: 'Welcome', component: 'hero' },
    { id: 'demo', title: 'Try It', component: 'demo' },
    { id: 'register', title: 'Sign Up', component: 'register' },
    { id: 'preferences', title: 'Personalize', component: 'preferences' }
  ];

  const quickPrefOptions = [
    { id: 'comfort', label: '🍕 Comfort Food', desc: 'Mac & cheese, burgers, pizza' },
    { id: 'healthy', label: '🥗 Healthy', desc: 'Fresh, nutritious, balanced' },
    { id: 'international', label: '🌮 International', desc: 'Global flavors & cuisines' },
    { id: 'meat', label: '🥩 Meat Lover', desc: 'Beef, chicken, pork dishes' },
    { id: 'vegetarian', label: '🌱 Vegetarian', desc: 'Plant-based goodness' },
    { id: 'quick', label: '⚡ Quick Meals', desc: '30 minutes or less' }
  ];

  const budgetOptions = [
    { value: 'budget', label: '$50', desc: 'Budget-friendly' },
    { value: 'moderate', label: '$100', desc: 'Balanced choices' },
    { value: 'premium', label: '$150', desc: 'Premium ingredients' },
    { value: 'custom', label: 'Other', desc: 'Custom amount' }
  ];

  const generateSampleRecipe = () => {
    // Simulate instant recipe generation for demo
    setSampleRecipe({
      name: "One-Pan Honey Garlic Chicken",
      time: "25 minutes",
      cost: "$12.50 for 4 people",
      ingredients: ["Chicken thighs", "Honey", "Garlic", "Vegetables"],
      image: "🍗"
    });
  };

  const handleQuickPrefToggle = (prefId) => {
    setUserPreferences(prev => ({
      ...prev,
      quickPrefs: prev.quickPrefs.includes(prefId)
        ? prev.quickPrefs.filter(id => id !== prefId)
        : [...prev.quickPrefs, prefId]
    }));
  };

  const handleRegisterAccount = async () => {
    // Validate registration data
    if (!registrationData.firstName || !registrationData.lastName || !registrationData.email || !registrationData.password || !registrationData.confirmPassword) {
      setRegistrationError('Please fill in all required fields');
      return;
    }

    if (registrationData.password.length < 8) {
      setRegistrationError('Password must be at least 8 characters');
      return;
    }

    if (registrationData.password !== registrationData.confirmPassword) {
      setRegistrationError('Passwords do not match');
      return;
    }

    setIsRegistering(true);
    setRegistrationError('');

    try {
      const email = registrationData.email.trim().toLowerCase();
      const fullName = `${registrationData.firstName} ${registrationData.lastName}`.trim();
      
      console.log('📝 Registering new user...');
      console.log('  📧 Email:', email);
      console.log('  👤 Name:', fullName);
      console.log('  🔗 API URL:', `${API}/api/auth/register`);

      const requestData = {
        email: email,
        password: registrationData.password,
        name: fullName,
        phone: '' // Optional field
      };
      
      console.log('📤 Sending registration request:', requestData);

      const response = await fetch(`${API}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('� Registration response:', data);

      if (response.ok && data.status === 'success') {
        console.log('✅ Registration successful!');
        console.log('  👤 User ID:', data.user_id);
        console.log('  📧 Email:', data.email);
        console.log('  ⏰ Trial End Date:', data.trial_end_date);
        
        // Store registration info for next step
        sessionStorage.setItem('registeredEmail', email);
        sessionStorage.setItem('registeredUserId', data.user_id);

        if (onRegistrationVerificationRequired && data.verification_required) {
          onRegistrationVerificationRequired(
            {
              ...data,
              email,
              name: fullName
            },
            {
              email,
              password: registrationData.password
            }
          );
          return;
        }

        // Fallback: complete signup directly in simplified flow
        if (simpleSignupMode) {
          if (onComplete) {
            onComplete({
              ...data,
              email,
              name: fullName
            });
          }
          return;
        }

        // Legacy flow: Move to preferences step
        setCurrentStep(3);
      } else {
        const errorMessage = data.detail || data.message || 'Registration failed. Please try again.';
        console.error('❌ Registration failed:', response.status, data);
        setRegistrationError(errorMessage);
      }
    } catch (error) {
      console.error('❌ Registration error:', error);
      console.error('  Error type:', error.name);
      console.error('  Error message:', error.message);
      setRegistrationError('Network error. Please check your connection and try again.');
    } finally {
      setIsRegistering(false);
    }
  };

  const renderHeroStep = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full text-center">
        {/* Login Option */}
        {showLoginOption && (
          <div className="mb-6">
            <button
              onClick={onLoginClick}
              className="text-blue-600 hover:text-blue-800 font-medium text-sm underline"
            >
              Already have an account? Sign in here
            </button>
          </div>
        )}

        {/* Hero Section */}
        <div className="bg-white rounded-3xl shadow-2xl p-12 mb-8">
          <div className="text-6xl mb-6">🍳</div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent mb-6">
            Turn $50 into a week of amazing meals
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            ⭐ Join 12,847 families saving money on groceries with AI-powered meal planning
          </p>

          <div className="flex flex-col md:flex-row gap-4 justify-center mb-8">
            <button
              onClick={() => setShowDemo(true)}
              className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              🎬 Watch 30-sec Demo
            </button>
            <button
              onClick={() => setCurrentStep(1)}
              className="bg-gradient-to-r from-green-500 to-teal-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              🚀 Start Free Trial
            </button>
          </div>

          <div className="text-center space-y-2">
            <p className="text-green-600 font-bold">💰 Average savings: $89/month</p>
            <p className="text-blue-600 font-bold">⏱️ Setup time: 2 minutes</p>
          </div>
        </div>

        {/* Quick Benefits */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="text-3xl mb-3">✅</div>
            <h3 className="font-bold text-lg mb-2">AI Recipes for Your Budget</h3>
            <p className="text-gray-600">Smart recipes that fit your spending plan</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="text-3xl mb-3">🛒</div>
            <h3 className="font-bold text-lg mb-2">One-Click Walmart Shopping</h3>
            <p className="text-gray-600">Auto-generated shopping lists with best prices</p>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-lg">
            <div className="text-3xl mb-3">⏰</div>
            <h3 className="font-bold text-lg mb-2">Save 3 Hours Per Week</h3>
            <p className="text-gray-600">No more meal planning stress</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderDemoStep = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          <h2 className="text-3xl font-bold text-center mb-6">
            Try it: Generate your first recipe!
          </h2>
          
          <div className="bg-gray-50 rounded-2xl p-6 mb-6">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <label className="block text-sm font-medium mb-2">💰 Budget</label>
                <select className="w-full p-2 border rounded-lg">
                  <option>$20</option>
                  <option>$30</option>
                  <option>$40</option>
                </select>
              </div>
              <div className="text-center">
                <label className="block text-sm font-medium mb-2">👨‍👩‍👧‍👦 People</label>
                <select className="w-full p-2 border rounded-lg">
                  <option>4</option>
                  <option>2</option>
                  <option>6</option>
                </select>
              </div>
              <div className="text-center">
                <label className="block text-sm font-medium mb-2">⏱️ Time</label>
                <select className="w-full p-2 border rounded-lg">
                  <option>30min</option>
                  <option>45min</option>
                  <option>60min</option>
                </select>
              </div>
            </div>

            <button
              onClick={generateSampleRecipe}
              className="w-full bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 rounded-lg font-bold text-lg hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              ✨ Generate Sample Recipe
            </button>
          </div>

          {sampleRecipe && (
            <div className="bg-green-50 border border-green-200 rounded-2xl p-6 mb-6">
              <div className="flex items-center mb-4">
                <span className="text-4xl mr-4">{sampleRecipe.image}</span>
                <div>
                  <h3 className="font-bold text-lg">{sampleRecipe.name}</h3>
                  <p className="text-green-600 font-medium">{sampleRecipe.time} • {sampleRecipe.cost}</p>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                <strong>Ingredients:</strong> {sampleRecipe.ingredients.join(', ')}
              </div>
              <div className="mt-4 p-3 bg-white rounded-lg">
                <p className="text-sm">🛒 <strong>Shopping list auto-generated!</strong></p>
                <p className="text-xs text-gray-500">Ready to add to Walmart cart with 1 click</p>
              </div>
            </div>
          )}

          <div className="text-center">
            <p className="text-lg font-medium mb-4">Like what you see? Create your free account!</p>
            <button
              onClick={() => setCurrentStep(2)}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-3 rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              🚀 Get Started Free
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderRegisterStep = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2">Create your account</h2>
            <p className="text-gray-600">Sign up to track recipes and meal plans.</p>
          </div>

          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              handleRegisterAccount();
            }}
          >
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium mb-1">👤 First Name</label>
                <input
                  type="text"
                  value={registrationData.firstName}
                  onChange={(e) => setRegistrationData({...registrationData, firstName: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">👤 Last Name</label>
                <input
                  type="text"
                  value={registrationData.lastName}
                  onChange={(e) => setRegistrationData({...registrationData, lastName: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Smith"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">📧 Email Address</label>
              <input
                type="email"
                value={registrationData.email}
                onChange={(e) => setRegistrationData({...registrationData, email: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="john.smith@email.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">🔒 Create Password</label>
              <div className="relative">
                <input
                  type={showRegisterPassword ? "text" : "password"}
                  value={registrationData.password}
                  onChange={(e) => setRegistrationData({...registrationData, password: e.target.value})}
                  className="w-full p-3 pr-16 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="••••••••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowRegisterPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:text-blue-800"
                >
                  {showRegisterPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">💪 Strong password (8+ chars, mix of letters/numbers)</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">🔒 Confirm Password</label>
              <div className="relative">
                <input
                  type={showRegisterConfirmPassword ? "text" : "password"}
                  value={registrationData.confirmPassword}
                  onChange={(e) => setRegistrationData({...registrationData, confirmPassword: e.target.value})}
                  className={`w-full p-3 pr-16 border rounded-lg focus:ring-2 focus:ring-blue-500 ${
                    registrationData.confirmPassword && registrationData.password !== registrationData.confirmPassword
                      ? 'border-red-300'
                      : 'border-gray-300'
                  }`}
                  placeholder="••••••••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowRegisterConfirmPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-blue-600 hover:text-blue-800"
                >
                  {showRegisterConfirmPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {registrationData.confirmPassword && registrationData.password !== registrationData.confirmPassword && (
                <p className="text-xs text-red-600 mt-1">Passwords do not match.</p>
              )}
            </div>

            {registrationError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-700 text-sm">⚠️ {registrationError}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={
                isRegistering ||
                (registrationData.confirmPassword && registrationData.password !== registrationData.confirmPassword)
              }
              className="w-full bg-gradient-to-r from-green-500 to-teal-500 text-white py-3 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              {isRegistering ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Creating account...
                </div>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <div className="text-center mt-6">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <button onClick={onLoginClick} className="text-blue-600 font-medium">
                Log in
              </button>
            </p>
            <p className="text-xs text-gray-500 mt-3 leading-relaxed">
              By creating an account, you agree to our{' '}
              <a href="/terms.html" target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">
                Terms of Service
              </a>{' '}
              and acknowledge our{' '}
              <a href="/privacy.html" target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">
                Privacy Policy
              </a>.
            </p>
            <div className="mt-2 text-xs">
              <a href="/security.html" target="_blank" rel="noreferrer" className="text-gray-500 hover:text-gray-700 underline">
                Security
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPreferencesStep = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-green-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2">Let's personalize your experience</h2>
            <p className="text-gray-600">Skip anytime - you can change these later</p>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-bold mb-4">🍽️ What do you like to eat?</h3>
              <div className="grid grid-cols-2 gap-3">
                {quickPrefOptions.map(option => (
                  <button
                    key={option.id}
                    onClick={() => handleQuickPrefToggle(option.id)}
                    className={`p-4 rounded-xl border-2 text-left transition-all ${
                      userPreferences.quickPrefs.includes(option.id)
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="font-medium">{option.label}</div>
                    <div className="text-xs text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-4">💰 Typical weekly grocery budget?</h3>
              <div className="grid grid-cols-4 gap-3">
                {budgetOptions.map(option => (
                  <button
                    key={option.value}
                    onClick={() => setUserPreferences({...userPreferences, budget: option.value})}
                    className={`p-3 rounded-lg border-2 text-center transition-all ${
                      userPreferences.budget === option.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-green-300'
                    }`}
                  >
                    <div className="font-bold">{option.label}</div>
                    <div className="text-xs text-gray-500">{option.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex justify-between mt-8">
            <button
              onClick={onSkip}
              className="px-6 py-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              Skip for now
            </button>
            <button
              onClick={() => onComplete(registrationData)}
              className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-3 rounded-lg font-bold hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
            >
              Save & Continue →
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Simplified signup flow renders the registration form directly.
  if (simpleSignupMode) {
    return renderRegisterStep();
  }

  // Show demo modal if requested
  if (showDemo) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-2xl p-8 max-w-md w-full">
          <h3 className="text-xl font-bold mb-4">🎬 Quick Demo</h3>
          <div className="bg-gray-100 rounded-lg p-6 mb-4 text-center">
            <div className="text-4xl mb-2">▶️</div>
            <p className="text-gray-600">30-second demo video would play here</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowDemo(false)}
              className="flex-1 py-2 border border-gray-300 rounded-lg"
            >
              Close
            </button>
            <button
              onClick={() => {
                setShowDemo(false);
                setCurrentStep(1);
              }}
              className="flex-1 bg-blue-500 text-white py-2 rounded-lg"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Render current step
  switch (currentStep) {
    case 0: return renderHeroStep();
    case 1: return renderDemoStep();
    case 2: return renderRegisterStep();
    case 3: return renderPreferencesStep();
    default: return renderHeroStep();
  }
};

export default WelcomeOnboarding;
