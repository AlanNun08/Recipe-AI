import React, { useState } from 'react';
import { authService } from '../services/auth';

const LoginComponent = ({ onVerificationRequired, onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const result = await authService.login({ email, password });
      
      console.log('Login result:', result); // Debug log
      
      if (result.status === 'verification_required') {
        // Password was correct but account needs verification
        console.log('Verification required, navigating to verification page');
        
        // Call callback to navigate to verification page
        if (onVerificationRequired) {
          onVerificationRequired(result);
        } else {
          // Default navigation
          window.location.href = '/verify';
        }
        
      } else if (result.status === 'success') {
        // Login successful
        console.log('Login successful:', result);
        
        if (onLoginSuccess) {
          onLoginSuccess(result);
        } else {
          // Default navigation
          alert('Login successful!');
          window.location.href = '/dashboard';
        }
      }
    } catch (error) {
      console.error('Login error:', error);
      setError('Login failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-8xl mb-6 animate-bounce">🔐</div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent mb-4">
            Welcome Back!
          </h1>
          <p className="text-lg text-gray-600">
            Sign in to your AI Chef account
          </p>
        </div>

        {/* Login Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
              <div className="flex items-center">
                <span className="text-2xl mr-3">❌</span>
                <div>
                  <h4 className="font-bold text-red-800 mb-1">Login Failed</h4>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          <form onSubmit={handleLogin} className="space-y-6">
            {/* Email Field */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                📧 Email Address
              </label>
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white text-lg"
              />
            </div>
            
            {/* Password Field */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                🔒 Password
              </label>
              <input
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-orange-500 focus:ring-2 focus:ring-orange-200 transition-all duration-200 text-gray-700 bg-white text-lg"
              />
            </div>
            
            {/* Login Button */}
            <button 
              type="submit" 
              disabled={loading}
              className={`w-full font-bold py-4 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center text-lg shadow-lg ${
                loading
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-orange-500 to-red-600 text-white hover:shadow-xl transform hover:-translate-y-1 hover:from-orange-600 hover:to-red-700'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                  Signing you in...
                </>
              ) : (
                <>
                  <span className="mr-3 text-2xl">✨</span>
                  Sign In to AI Chef
                </>
              )}
            </button>
          </form>

          {/* Additional Info */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
              <div className="flex items-start">
                <span className="text-2xl mr-3">💡</span>
                <div>
                  <h4 className="font-bold text-blue-800 mb-1">First time here?</h4>
                  <p className="text-blue-700 text-sm">
                    Create your account and start generating amazing recipes with AI Chef!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            🔒 Your data is secure and protected
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginComponent;