import React, { useState } from 'react';
import { authService } from '../services/auth';

const LoginComponent = ({ onVerificationRequired, onLoginSuccess, onForgotPassword }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resetMode, setResetMode] = useState('request');
  const [resetEmail, setResetEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState('');
  const [showResetPassword, setShowResetPassword] = useState(false);
  const [showResetConfirmPassword, setShowResetConfirmPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {

      // Call the backend login endpoint
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password
        }),
      });


      const data = await response.json();

      // Handle different response cases
      if (response.status === 403 && data.status === 'verification_required') {
        if (onVerificationRequired) {
          onVerificationRequired(data);
        } else {
          setError('Account not verified. Please check your email for verification code.');
        }
        
      } else if (response.ok && data.status === 'success') {
        const fullName = [data.first_name, data.last_name].filter(Boolean).join(' ').trim();
        const userData = {
          user_id: data.user_id,
          email: data.email,
          name: data.name || fullName,
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          verified: data.verified ?? data.is_verified ?? false,
          is_verified: data.is_verified ?? data.verified ?? false,
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
      const response = await fetch('/api/health');
      const data = await response.json();
      
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

  const resetForgotPasswordState = () => {
    setShowForgotPassword(false);
    setResetMode('request');
    setResetEmail(email.trim().toLowerCase());
    setResetCode('');
    setResetPassword('');
    setResetConfirmPassword('');
    setResetMessage('');
    setError('');
    setShowResetPassword(false);
    setShowResetConfirmPassword(false);
  };

  const openForgotPassword = () => {
    setShowForgotPassword(true);
    setResetMode('request');
    setResetEmail(email.trim().toLowerCase());
    setResetCode('');
    setResetPassword('');
    setResetConfirmPassword('');
    setResetMessage('');
    setError('');
  };

  const handleSendResetCode = async (e) => {
    e.preventDefault();
    if (!resetEmail.trim()) {
      setError('Enter your email to receive a reset code.');
      return;
    }

    setResetLoading(true);
    setError('');
    setResetMessage('');

    try {
      const normalizedEmail = resetEmail.trim().toLowerCase();
      await authService.requestPasswordReset(normalizedEmail);
      setResetEmail(normalizedEmail);
      setResetMode('verify');
      setResetMessage('Reset code sent. Check your email.');
    } catch (resetError) {
      setError(resetError.message || 'Failed to send reset code.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleVerifyResetCode = async (e) => {
    e.preventDefault();
    if (resetCode.length !== 6) {
      setError('Enter the 6-digit reset code.');
      return;
    }

    setResetLoading(true);
    setError('');
    setResetMessage('');

    try {
      await authService.verifyPasswordResetCode(resetEmail, resetCode);
      setResetMode('reset');
      setResetMessage('Code verified. Enter your new password.');
    } catch (resetError) {
      setError(resetError.message || 'Failed to verify reset code.');
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (resetPassword.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (resetPassword !== resetConfirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setResetLoading(true);
    setError('');
    setResetMessage('');

    try {
      await authService.resetPassword(resetEmail, resetCode, resetPassword);
      const updatedEmail = resetEmail;
      setPassword('');
      setShowForgotPassword(false);
      setResetMode('request');
      setResetCode('');
      setResetPassword('');
      setResetConfirmPassword('');
      setResetMessage('Your password was updated. Sign in with your new password.');
      setEmail(updatedEmail);
      setResetEmail('');
      setShowResetPassword(false);
      setShowResetConfirmPassword(false);
      setError('');
    } catch (resetError) {
      setError(resetError.message || 'Failed to reset password.');
    } finally {
      setResetLoading(false);
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
      
      {showForgotPassword ? (
        <div className="space-y-4">
          <div className="text-left">
            <h3 className="text-lg font-semibold text-gray-800">Reset your password</h3>
            <p className="text-sm text-gray-600">
              {resetMode === 'request' && 'Enter your email to receive a 6-digit reset code.'}
              {resetMode === 'verify' && 'Enter the code we emailed you.'}
              {resetMode === 'reset' && 'Choose a new password for your account.'}
            </p>
          </div>

          {resetMessage && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-700">
              {resetMessage}
            </div>
          )}

          {resetMode === 'request' && (
            <form onSubmit={handleSendResetCode} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">📧 Email</label>
                <input
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  placeholder="email@example.com"
                />
              </div>
              <button
                type="submit"
                disabled={resetLoading}
                className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-all duration-200 ${
                  resetLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {resetLoading ? 'Sending code...' : 'Send Reset Code'}
              </button>
            </form>
          )}

          {resetMode === 'verify' && (
            <form onSubmit={handleVerifyResetCode} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">🔢 Reset Code</label>
                <input
                  type="text"
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  maxLength="6"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-center tracking-[0.3em] focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  placeholder="123456"
                />
              </div>
              <button
                type="submit"
                disabled={resetLoading || resetCode.length !== 6}
                className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-all duration-200 ${
                  resetLoading || resetCode.length !== 6 ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {resetLoading ? 'Verifying code...' : 'Verify Reset Code'}
              </button>
            </form>
          )}

          {resetMode === 'reset' && (
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">🔒 New Password</label>
                <div className="relative">
                  <input
                    type={showResetPassword ? 'text' : 'password'}
                    value={resetPassword}
                    onChange={(e) => setResetPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                    placeholder="At least 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowResetPassword(!showResetPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showResetPassword ? '🙈' : '👁'}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">🔒 Confirm Password</label>
                <div className="relative">
                  <input
                    type={showResetConfirmPassword ? 'text' : 'password'}
                    value={resetConfirmPassword}
                    onChange={(e) => setResetConfirmPassword(e.target.value)}
                    required
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                    placeholder="Re-enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowResetConfirmPassword(!showResetConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showResetConfirmPassword ? '🙈' : '👁'}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                disabled={resetLoading}
                className={`w-full py-3 px-4 rounded-lg font-bold text-white transition-all duration-200 ${
                  resetLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {resetLoading ? 'Updating password...' : 'Update Password'}
              </button>
            </form>
          )}

          <div className="flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => {
                setResetMode('request');
                setResetCode('');
                setResetPassword('');
                setResetConfirmPassword('');
                setResetMessage('');
                setError('');
              }}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              Start over
            </button>
            <button
              type="button"
              onClick={resetForgotPasswordState}
              className="text-gray-600 hover:text-gray-800 font-medium"
            >
              Back to login
            </button>
          </div>
        </div>
      ) : (
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
            onClick={openForgotPassword}
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
      )}

      <div className="pt-2 border-t border-gray-100 text-center text-xs text-gray-500 leading-relaxed">
        <a href="/privacy.html" target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">
          Privacy Policy
        </a>
        {' · '}
        <a href="/terms.html" target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">
          Terms of Service
        </a>
        {' · '}
        <a href="/security.html" target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">
          Security
        </a>
      </div>
    </div>
  );
};

export default LoginComponent;
