import React, { useState } from 'react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

function LandingPage({ onVerificationRequired, onLoginSuccess, onSignUpClick }) {
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const normalizedEmail = email.trim().toLowerCase();
      console.log('🔐 Attempting login...');
      console.log('  📧 Email:', normalizedEmail);
      console.log('  🔗 API URL:', `${API}/api/auth/login`);

      // Call the backend login endpoint to search MongoDB
      const loginRequest = {
        email: normalizedEmail,
        password: password
      };
      
      console.log('📤 Sending login request to backend');

      const response = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginRequest),
      });

      console.log('📡 Response status:', response.status);
      const data = await response.json();
      console.log('📥 Login response:', data);

      // Handle different response cases
      if (response.status === 403 && data.status === 'verification_required') {
        console.log('⚠️ Verification required for account');
        console.log('  📧 Email:', data.email);
        if (onVerificationRequired) {
          onVerificationRequired(data);
        } else {
          setError('Account not verified. Please check your email for verification code.');
        }
        
      } else if (response.ok && data.status === 'success') {
        console.log('✅ Login successful!');
        console.log('  👤 User ID:', data.user_id);
        console.log('  📧 Email:', data.email);
        console.log('  ⏰ Subscription:', data.subscription_status);
        
        const userData = {
          user_id: data.user_id,
          email: data.email,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          verified: data.is_verified,
          subscription_status: data.subscription_status
        };

        // Store with remember me preference
        if (rememberMe) {
          localStorage.setItem('user', JSON.stringify(userData));
          localStorage.setItem('rememberMe', 'true');
          console.log('💾 User data saved to localStorage');
        } else {
          sessionStorage.setItem('user', JSON.stringify(userData));
          console.log('💾 User data saved to sessionStorage');
        }

        if (onLoginSuccess) {
          onLoginSuccess(userData);
        }
        
      } else if (response.status === 503) {
        console.error('❌ Backend service unavailable');
        setError('Authentication service is temporarily unavailable. Please try again later.');
        
      } else if (response.status === 501) {
        console.error('❌ Authentication endpoint not implemented');
        setError('Authentication system is not configured. Please contact support.');
        
      } else if (response.status === 401) {
        console.error('❌ Invalid credentials');
        setError('Invalid email or password. Please check your credentials and try again.');
        
      } else if (response.status === 500) {
        console.error('❌ Server error:', data);
        if (data.error === 'password_hash_missing') {
          setError('Account setup incomplete. Please contact support or try registering again.');
        } else {
          setError(data.detail || 'Server error. Please try again.');
        }
        
      } else {
        console.error('❌ Login failed:', response.status, data);
        setError(data.detail || data.message || 'Login failed. Please try again.');
      }
      
    } catch (error) {
      console.error('❌ Network error during login:', error);
      console.error('  Error type:', error.name);
      console.error('  Error message:', error.message);
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const testAPIConnection = async () => {
    try {
      console.log('🧪 Testing API connection...');
      const response = await fetch(`${API}/api/health`);
      const data = await response.json();
      console.log('🧪 API Health:', data);
      
      if (response.ok) {
        setError('✅ API connection successful! Try logging in again.');
      } else {
        setError('⚠️ API is responding but may have issues.');
      }
    } catch (error) {
      console.error('🧪 API test failed:', error);
      setError('❌ Cannot connect to API server.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-purple-50 to-blue-50">
      {/* Navigation Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Recipe AI
              </h1>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex gap-8">
              <button 
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-gray-700 hover:text-purple-600 font-medium transition-colors"
              >
                Features
              </button>
              <button 
                onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-gray-700 hover:text-purple-600 font-medium transition-colors"
              >
                About
              </button>
              <button 
                onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
                className="text-gray-700 hover:text-purple-600 font-medium transition-colors"
              >
                Pricing
              </button>
            </nav>

            {/* Auth Buttons */}
            <div className="flex gap-3">
              <button 
                onClick={() => setShowLoginForm(!showLoginForm)}
                className="px-4 py-2 text-purple-600 border-2 border-purple-600 rounded-lg font-semibold hover:bg-purple-600 hover:text-white transition-all"
              >
                Sign In
              </button>
              <button 
                onClick={onSignUpClick}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-semibold hover:shadow-lg hover:-translate-y-0.5 transition-all"
              >
                Sign Up
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Login Modal */}
      {showLoginForm && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => setShowLoginForm(false)}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto relative animate-in fade-in slide-in-from-bottom-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button 
              onClick={() => setShowLoginForm(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl w-8 h-8 flex items-center justify-center"
            >
              ✕
            </button>
            
            <div className="p-8 pt-10">
              {/* Welcome Message */}
              <div className="text-center mb-6">
                <div className="text-4xl mb-3">👋</div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome Back!</h2>
                <p className="text-gray-600">Ready to plan some delicious meals?</p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4 rounded">
                  <div className="flex items-start gap-2">
                    <span className="text-red-500 text-lg">⚠️</span>
                    <div className="flex-1">
                      <p className="text-red-700 text-sm">{error}</p>
                      {error.includes('Network') && (
                        <button
                          onClick={testAPIConnection}
                          className="mt-2 text-blue-600 hover:text-blue-800 text-sm underline"
                        >
                          Test API Connection
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
              
              {/* Login Form */}
              <form onSubmit={handleLogin} className="space-y-4">
                {/* Email Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    📧 Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors"
                    placeholder="email@example.com"
                  />
                </div>
                
                {/* Password Field */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    🔒 Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-colors"
                      placeholder="••••••••••••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 text-xl"
                    >
                      {showPassword ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>

                {/* Remember Me */}
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500 cursor-pointer"
                    id="rememberMe"
                  />
                  <label htmlFor="rememberMe" className="ml-2 text-sm text-gray-700 cursor-pointer">
                    ☑️ Keep me logged in
                  </label>
                </div>
                
                {/* Submit Button */}
                <button 
                  type="submit" 
                  disabled={loading}
                  className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-all duration-200 ${
                    loading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:-translate-y-1'
                  }`}
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Signing in...
                    </div>
                  ) : (
                    '🚀 Login to Dashboard'
                  )}
                </button>
              </form>

              {/* Sign Up Link */}
              <div className="text-center mt-4 text-sm text-gray-600">
                Don't have an account?{' '}
                <button
                  onClick={() => {
                    setShowLoginForm(false);
                    onSignUpClick();
                  }}
                  className="text-purple-600 hover:text-purple-800 font-medium"
                >
                  Sign up here
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900">
              Discover Amazing Recipes with AI
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              Get personalized recipe suggestions based on your dietary preferences and available ingredients
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={onSignUpClick}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-bold hover:shadow-lg hover:-translate-y-1 transition-all"
              >
                Get Started Free
              </button>
              <button 
                onClick={() => setShowLoginForm(true)}
                className="px-8 py-4 bg-white border-2 border-purple-600 text-purple-600 rounded-lg font-bold hover:bg-purple-50 transition-all"
              >
                Already have an account?
              </button>
            </div>
          </div>
          
          <div className="flex items-center justify-center">
            <div className="text-9xl animate-bounce" style={{ animationDuration: '3s' }}>
              🍽️
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">Why Choose Recipe AI?</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: '🤖', title: 'AI-Powered Suggestions', desc: 'Our advanced AI learns your preferences and suggests recipes you\'ll love' },
              { icon: '🥗', title: 'Dietary Preferences', desc: 'Support for vegan, vegetarian, keto, gluten-free, and many other dietary needs' },
              { icon: '⏱️', title: 'Quick & Easy', desc: 'Get recipes based on your available time and cooking skill level' },
              { icon: '📱', title: 'Mobile Friendly', desc: 'Access recipes anytime, anywhere on your mobile device' },
              { icon: '💚', title: 'Ingredient Matching', desc: 'Find recipes based on ingredients you already have at home' },
              { icon: '📊', title: 'Weekly Meal Plans', desc: 'Get organized weekly recipe plans to make meal prep easier' },
            ].map((feature, idx) => (
              <div 
                key={idx}
                className="p-8 bg-gray-50 rounded-xl hover:shadow-lg hover:-translate-y-2 transition-all border-2 border-transparent hover:border-purple-500"
              >
                <div className="text-5xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="bg-gradient-to-br from-gray-50 to-gray-100 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">About Recipe AI</h2>
          
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-3xl font-bold text-gray-900 mb-6">Your Personal Culinary Assistant</h3>
              <p className="text-lg text-gray-600 mb-4 leading-relaxed">
                Recipe AI is a modern cooking companion that uses artificial intelligence to understand your taste preferences, dietary restrictions, and cooking style.
              </p>
              <p className="text-lg text-gray-600 mb-6 leading-relaxed">
                Whether you're a beginner cook looking for simple recipes or an experienced chef seeking inspiration, Recipe AI adapts to your needs and provides personalized suggestions that match your lifestyle.
              </p>
              <ul className="space-y-3">
                {[
                  '✨ Personalized recipe recommendations',
                  '🎯 Smart ingredient matching',
                  '⚡ Fast and intuitive interface',
                  '🌍 Support for global cuisines',
                  '📚 Growing recipe database',
                ].map((item, idx) => (
                  <li key={idx} className="text-gray-700">{item}</li>
                ))}
              </ul>
            </div>
            
            <div className="grid grid-cols-2 gap-6">
              {[
                { num: '10K+', label: 'Recipes' },
                { num: '50K+', label: 'Active Users' },
                { num: '100%', label: 'Free Trial' },
                { num: '24/7', label: 'Support' },
              ].map((stat, idx) => (
                <div key={idx} className="bg-white p-6 rounded-xl text-center shadow-md">
                  <h4 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    {stat.num}
                  </h4>
                  <p className="text-gray-600 mt-2">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">Simple, Transparent Pricing</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Free Plan */}
            <div className="bg-gray-50 p-8 rounded-xl border-2 border-gray-200 hover:shadow-lg transition-all">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Free Trial</h3>
              <p className="text-3xl font-bold text-gray-900 mb-1">Free</p>
              <p className="text-gray-600 mb-6">50 days trial access</p>
              <ul className="space-y-3 mb-8">
                {[
                  '✓ Basic recipe suggestions',
                  '✓ Dietary preference filters',
                  '✓ Mobile access',
                  '✗ Weekly meal plans',
                  '✗ Advanced filtering',
                ].map((item, idx) => (
                  <li key={idx} className="text-gray-700">{item}</li>
                ))}
              </ul>
              <button 
                onClick={onSignUpClick}
                className="w-full py-3 px-4 border-2 border-purple-600 text-purple-600 rounded-lg font-bold hover:bg-purple-600 hover:text-white transition-all"
              >
                Start Free Trial
              </button>
            </div>

            {/* Premium Plan */}
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 p-8 rounded-xl text-white shadow-xl hover:-translate-y-2 transition-all scale-105 relative">
              <div className="absolute -top-4 left-8 bg-yellow-400 text-purple-900 px-4 py-1 rounded-full text-sm font-bold">
                Most Popular
              </div>
              <h3 className="text-2xl font-bold mb-2">Premium</h3>
              <p className="text-4xl font-bold mb-1">$9.99</p>
              <p className="text-white/80 mb-8">per month</p>
              <ul className="space-y-3 mb-8">
                {[
                  '✓ All Free features',
                  '✓ Weekly meal plans',
                  '✓ Advanced filtering',
                  '✓ Ingredient matching',
                  '✓ Priority support',
                ].map((item, idx) => (
                  <li key={idx} className="text-white/90">{item}</li>
                ))}
              </ul>
              <button 
                onClick={onSignUpClick}
                className="w-full py-3 px-4 bg-white text-purple-600 rounded-lg font-bold hover:bg-gray-100 transition-all"
              >
                Upgrade Now
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-purple-600 to-pink-600 py-20 text-white text-center">
        <div className="max-w-2xl mx-auto px-4 sm:px-6">
          <h2 className="text-4xl font-bold mb-6">Ready to Transform Your Cooking?</h2>
          <p className="text-xl mb-8 text-white/90">
            Join thousands of users discovering amazing recipes tailored to their preferences
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={onSignUpClick}
              className="px-8 py-4 bg-white text-purple-600 rounded-lg font-bold hover:shadow-lg transition-all"
            >
              Create Free Account
            </button>
            <button 
              onClick={() => setShowLoginForm(true)}
              className="px-8 py-4 bg-white/20 border-2 border-white text-white rounded-lg font-bold hover:bg-white/30 transition-all"
            >
              Sign In to Your Account
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-white font-bold text-lg mb-4">Recipe AI</h4>
              <p>Your personal AI cooking assistant</p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Quick Links</h4>
              <ul className="space-y-2">
                <li><a href="#features" className="hover:text-purple-400 transition-colors">Features</a></li>
                <li><a href="#about" className="hover:text-purple-400 transition-colors">About</a></li>
                <li><a href="#pricing" className="hover:text-purple-400 transition-colors">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li><a href="/" className="hover:text-purple-400 transition-colors">Privacy Policy</a></li>
                <li><a href="/" className="hover:text-purple-400 transition-colors">Terms of Service</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Contact</h4>
              <p>Email: support@recipeai.com</p>
              <p>Visit: buildyoursmartcart.com</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 pt-8 text-center">
            <p>&copy; 2026 Recipe AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
