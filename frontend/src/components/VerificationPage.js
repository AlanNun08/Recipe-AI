import React, { useState, useEffect } from 'react';
import { authService } from '../services/auth';

const VerificationPage = ({ onVerificationSuccess, onBackToLogin }) => {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verificationData, setVerificationData] = useState(null);

  useEffect(() => {
    // Get pending verification data from localStorage
    const pendingData = authService.getPendingVerification();
    if (pendingData) {
      setVerificationData(pendingData);
    } else {
      // No pending verification, redirect back to login
      setError('No pending verification found. Please login again.');
    }
  }, []);

  const handleVerification = async (e) => {
    e.preventDefault();
    
    if (!verificationData) {
      setError('No verification data found. Please login again.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await authService.verifyEmailAndLogin(
        verificationData.user_id, 
        verificationCode
      );
      
      console.log('Verification successful:', result);
      
      // Clear verification data
      authService.clearPendingVerification();
      
      // Call success callback
      if (onVerificationSuccess) {
        onVerificationSuccess(result);
      } else {
        alert('Account verified successfully! You are now logged in.');
        // Default redirect or action
        window.location.href = '/dashboard';
      }
      
    } catch (error) {
      console.error('Verification error:', error);
      setError('Verification failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!verificationData) {
      setError('No verification data found. Please login again.');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      await authService.resendCode(verificationData.email);
      alert('New verification code sent to your email!');
    } catch (error) {
      console.error('Resend error:', error);
      setError('Failed to resend code: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    authService.clearPendingVerification();
    if (onBackToLogin) {
      onBackToLogin();
    } else {
      // Default back to login
      window.location.href = '/login';
    }
  };

  if (!verificationData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="text-8xl mb-6">❌</div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent mb-4">
              Verification Error
            </h1>
            <p className="text-lg text-gray-600">
              No pending verification found
            </p>
          </div>

          {/* Error Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 text-center">
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
              <h4 className="font-bold text-red-800 mb-2">Oops! Something went wrong</h4>
              <p className="text-red-700">
                No pending verification found. Please login again to receive a new verification code.
              </p>
            </div>
            
            <button 
              onClick={handleBackToLogin}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold py-4 px-6 rounded-2xl hover:shadow-xl transform hover:-translate-y-1 transition-all duration-300 flex items-center justify-center text-lg"
            >
              <span className="mr-3 text-2xl">🔙</span>
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-8xl mb-6 animate-bounce">📧</div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-4">
            Check Your Email
          </h1>
          <p className="text-lg text-gray-600">
            Enter the verification code to continue
          </p>
        </div>

        {/* Verification Form Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          {/* Email Info */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 mb-6 border border-blue-200">
            <div className="flex items-center mb-3">
              <span className="text-2xl mr-3">✉️</span>
              <h3 className="font-bold text-gray-800">Verification Code Sent!</h3>
            </div>
            <p className="text-gray-700 mb-2">
              We sent a 6-digit verification code to:
            </p>
            <p className="font-bold text-blue-700 text-lg">
              {verificationData.email}
            </p>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
              <div className="flex items-center">
                <span className="text-2xl mr-3">⚠️</span>
                <div>
                  <h4 className="font-bold text-red-800 mb-1">Verification Failed</h4>
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
              </div>
            </div>
          )}
          
          <form onSubmit={handleVerification} className="space-y-6">
            {/* Verification Code Field */}
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-2">
                🔢 Verification Code
              </label>
              <input
                type="text"
                placeholder="000000"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength="6"
                required
                className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 text-gray-700 bg-white text-2xl text-center tracking-widest font-mono"
              />
              <p className="text-sm text-gray-500 mt-2 text-center">
                💡 Enter the 6-digit code from your email
              </p>
            </div>
            
            {/* Verify Button */}
            <button 
              type="submit" 
              disabled={loading || verificationCode.length !== 6}
              className={`w-full font-bold py-4 px-6 rounded-2xl transition-all duration-300 flex items-center justify-center text-lg shadow-lg ${
                loading || verificationCode.length !== 6
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed shadow-none'
                  : 'bg-gradient-to-r from-green-500 to-blue-600 text-white hover:shadow-xl transform hover:-translate-y-1 hover:from-green-600 hover:to-blue-700'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin mr-3"></div>
                  Verifying...
                </>
              ) : (
                <>
                  <span className="mr-3 text-2xl">✅</span>
                  Verify My Account
                </>
              )}
            </button>
          </form>
          
          {/* Action Buttons */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="text-center mb-4">
              <p className="text-sm text-gray-600">
                Didn't receive the code?
              </p>
            </div>
            
            <div className="grid grid-cols-1 gap-3">
              <button 
                onClick={handleResendCode}
                disabled={loading}
                className={`font-medium py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center ${
                  loading 
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed' 
                    : 'bg-blue-100 text-blue-700 hover:bg-blue-200 border border-blue-300'
                }`}
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-blue-700 border-t-transparent rounded-full animate-spin mr-2"></div>
                    Sending...
                  </>
                ) : (
                  <>
                    <span className="mr-2 text-lg">📤</span>
                    Resend Code
                  </>
                )}
              </button>
              
              <button 
                onClick={handleBackToLogin}
                disabled={loading}
                className={`font-medium py-3 px-4 rounded-xl transition-all duration-200 flex items-center justify-center ${
                  loading 
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                }`}
              >
                <span className="mr-2 text-lg">🔙</span>
                Back to Login
              </button>
            </div>
          </div>

          {/* Help Text */}
          <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <div className="flex items-start">
              <span className="text-xl mr-3">💡</span>
              <div>
                <h4 className="font-bold text-yellow-800 mb-1">Pro Tips</h4>
                <ul className="text-yellow-700 text-sm space-y-1">
                  <li>• Check your spam/junk folder</li>
                  <li>• Code expires in 24 hours</li>
                  <li>• Make sure you entered the correct email</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-gray-500 text-sm">
            🔒 Your account security is our priority
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerificationPage;