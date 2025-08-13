import React, { useState, useEffect } from 'react';

const SubscriptionSuccessScreen = ({ onClose, showNotification, backendUrl }) => {
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const [sessionId, setSessionId] = useState('');
  const [attempts, setAttempts] = useState(0);

  // Get session ID from URL parameters
  const getUrlParameter = (name) => {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(window.location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
  };

  // Poll payment status
  const pollPaymentStatus = async (sessionId, attemptCount = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000; // 2 seconds

    if (attemptCount >= maxAttempts) {
      setPaymentStatus('timeout');
      showNotification('Payment status check timed out. Please check your email for confirmation.', 'warning');
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/subscription/checkout/status/${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Failed to check payment status');
      }

      const data = await response.json();
      
      if (data.payment_status === 'paid') {
        setPaymentStatus('success');
        showNotification('🎉 Payment successful! Your subscription is now active!', 'success');
        return;
      } else if (data.status === 'expired') {
        setPaymentStatus('expired');
        showNotification('Payment session expired. Please try again.', 'error');
        return;
      }

      // If payment is still pending, continue polling
      setPaymentStatus('processing');
      setAttempts(attemptCount + 1);
      setTimeout(() => pollPaymentStatus(sessionId, attemptCount + 1), pollInterval);
      
    } catch (error) {
      console.error('Error checking payment status:', error);
      setPaymentStatus('error');
      showNotification('Error checking payment status. Please try again.', 'error');
    }
  };

  useEffect(() => {
    const sessionId = getUrlParameter('session_id');
    if (sessionId) {
      setSessionId(sessionId);
      pollPaymentStatus(sessionId);
    } else {
      setPaymentStatus('error');
      showNotification('No session ID found in URL', 'error');
    }
  }, []);

  const renderStatusContent = () => {
    switch (paymentStatus) {
      case 'checking':
        return (
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Initializing Payment Check...</h2>
            <p className="text-gray-600">Setting up payment verification...</p>
          </div>
        );

      case 'processing':
        return (
          <div className="text-center">
            <div className="animate-pulse">
              <div className="bg-gradient-to-r from-blue-400 to-purple-400 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
                <span className="text-white text-2xl">💳</span>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Processing Payment...</h2>
            <p className="text-gray-600 mb-4">
              Verifying your payment with Stripe... (Attempt {attempts + 1}/10)
            </p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, ((attempts + 1) / 10) * 100)}%` }}
              ></div>
            </div>
          </div>
        );

      case 'success':
        return (
          <div className="text-center">
            <div className="bg-green-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-green-600 text-3xl">✅</span>
            </div>
            <h2 className="text-2xl font-bold text-green-800 mb-2">Payment Successful!</h2>
            <p className="text-gray-600 mb-4">
              🎉 Your subscription is now active! Welcome to premium features.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <h3 className="font-semibold text-green-800 mb-2">What's Next:</h3>
              <ul className="text-sm text-green-700 space-y-1">
                <li>✅ Generate unlimited recipes</li>
                <li>✅ Create weekly meal plans</li>
                <li>✅ Access Starbucks secret menu</li>
                <li>✅ Premium Walmart shopping integration</li>
              </ul>
            </div>
          </div>
        );

      case 'expired':
        return (
          <div className="text-center">
            <div className="bg-yellow-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-yellow-600 text-3xl">⏰</span>
            </div>
            <h2 className="text-2xl font-bold text-yellow-800 mb-2">Session Expired</h2>
            <p className="text-gray-600 mb-4">
              Your payment session has expired. Please try subscribing again.
            </p>
          </div>
        );

      case 'timeout':
        return (
          <div className="text-center">
            <div className="bg-orange-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-orange-600 text-3xl">⚠️</span>
            </div>
            <h2 className="text-2xl font-bold text-orange-800 mb-2">Verification Timeout</h2>
            <p className="text-gray-600 mb-4">
              We couldn't verify your payment status. Please check your email for confirmation or contact support.
            </p>
          </div>
        );

      case 'error':
      default:
        return (
          <div className="text-center">
            <div className="bg-red-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
              <span className="text-red-600 text-3xl">❌</span>
            </div>
            <h2 className="text-2xl font-bold text-red-800 mb-2">Verification Error</h2>
            <p className="text-gray-600 mb-4">
              There was an error checking your payment status. Please try again or contact support.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-8">
        {renderStatusContent()}
        
        <div className="mt-6 flex justify-center space-x-4">
          {paymentStatus === 'success' && (
            <button
              onClick={onClose}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              Start Using Premium Features
            </button>
          )}
          
          {['expired', 'timeout', 'error'].includes(paymentStatus) && (
            <>
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Try Again
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                Go Back
              </button>
            </>
          )}
          
          {paymentStatus === 'processing' && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Continue in Background
            </button>
          )}
        </div>

        {sessionId && (
          <div className="mt-4 text-center text-xs text-gray-500">
            Session ID: {sessionId.substring(0, 20)}...
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionSuccessScreen;