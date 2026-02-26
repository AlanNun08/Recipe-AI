import React, { useState } from 'react';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

const LoginComponent = ({ onVerificationRequired, onLoginSuccess, onForgotPassword }) => {
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
      console.log('🔐 Attempting login for:', email);
      console.log('🔗 API URL:', `${API}/api/auth/login`);

      // Call the backend login endpoint
      const response = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        }),
      });

      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));

      const data = await response.json();
      console.log('📥 Login response:', data);

      // Handle different response cases
      if (response.status === 403 && data.status === 'verification_required') {
        console.log('⚠️ Verification required');
        if (onVerificationRequired) {
          onVerificationRequired(data);
        } else {
          setError('Account not verified. Please check your email for verification code.');
        }
        
      } else if (response.ok && data.status === 'success') {
        console.log('✅ Login successful:', data);
        
        const userData = {
          user_id: data.user_id,
          email: data.email,
          name: data.name,
          verified: data.verified,
          subscription_status: data.subscription_status,
          rememberMe
        };

        if (onLoginSuccess) {
          onLoginSuccess(userData);
        }
        
      } else if (response.status === 503) {
        // Backend not available
        console.error('❌ Backend service unavailable');
        setError('Authentication service is temporarily unavailable. Please try again later.');
        
      } else if (response.status === 501) {
        // Not implemented
        console.error('❌ Authentication endpoint not implemented');
        setError('Authentication system is not configured. Please contact support.');
        
      } else if (response.status === 401) {
        // Invalid credentials
        console.error('❌ Invalid credentials');
        setError('Invalid email or password. Please check your credentials.');
        
      } else if (response.status === 500) {
        // Server error
        console.error('❌ Server error:', data);
        if (data.error === 'password_hash_missing') {
          setError('Account setup incomplete. Please contact support or try registering again.');
        } else {
          setError(data.detail || 'Server error. Please try again.');
        }
        
      } else {
        // Other error
        console.error('❌ Login failed:', response.status, data);
        setError(data.detail || data.message || 'Login failed. Please try again.');
      }
      
    } catch (error) {
      console.error('❌ Network error during login:', error);
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
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="text-center">
        <div className="text-4xl mb-3">👋</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Welcome Back!</h2>
        <p className="text-gray-600">Ready to plan some delicious meals?</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-red-500 mr-2">⚠️</span>
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
      
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📧 Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
            placeholder="email@example.com"
          />
        </div>
        
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
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              placeholder="••••••••••••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
            >
              {showPassword ? '🙈' : '👁'}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="flex items-center text-sm">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mr-2"
            />
            <span className="text-gray-700">Keep me logged in</span>
          </label>
          <button
            type="button"
            onClick={onForgotPassword}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            🔗 Forgot password?
          </button>
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-all duration-200 ${
            loading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:shadow-lg transform hover:-translate-y-1'
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
    </div>
  );
};

export default LoginComponent;
