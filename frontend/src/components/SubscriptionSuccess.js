import React, { useState, useEffect } from 'react';

const SubscriptionSuccess = ({ onContinue }) => {
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Use environment variable
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

  useEffect(() => {
    // Get session_id from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      pollPaymentStatus(sessionId);
    } else {
      setError('No session ID found');
      setLoading(false);
    }
  }, []);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000; // 2 seconds

    if (attempts >= maxAttempts) {
      setError('Payment verification timed out. Please check your subscription status.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/api/subscription/checkout/status/${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Failed to check payment status');
      }

      const data = await response.json();
      
      if (data.payment_status === 'paid') {
        setPaymentStatus({
          status: 'success',
          amount: data.amount_total,
          currency: data.currency
        });
        setLoading(false);
        return;
      } else if (data.status === 'expired') {
        setError('Payment session expired. Please try again.');
        setLoading(false);
        return;
      }

      // If payment is still processing, continue polling
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      // Error checking payment status
      setError('Error verifying payment. Please check your subscription status.');
      setLoading(false);
    }
  };

  const formatAmount = (amount, currency) => {
    const formatted = (amount / 100).toFixed(2);
    return currency === 'usd' ? `$${formatted}` : `${formatted} ${currency.toUpperCase()}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto"></div>
          <h2 className="text-2xl font-bold text-gray-800 mt-6 mb-2">Processing Your Payment</h2>
          <p className="text-gray-600">Please wait while we confirm your subscription...</p>
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              🔄 Verifying payment with our secure payment processor...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-red-600 mb-4">Payment Issue</h2>
          <p className="text-gray-700 mb-6">{error}</p>
          <button
            onClick={onContinue}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Return to App
          </button>
        </div>
      </div>
    );
  }

  if (paymentStatus?.status === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-green-600 mb-2">Welcome to Premium!</h2>
          <p className="text-xl text-gray-700 mb-6">Your subscription is now active</p>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-green-800 mb-2">Payment Confirmed</h3>
            <p className="text-green-700">
              Amount: {formatAmount(paymentStatus.amount, paymentStatus.currency)}
            </p>
            <p className="text-green-600 text-sm mt-1">
              Your subscription will renew automatically each month
            </p>
          </div>

          <div className="mb-6 text-left">
            <h4 className="font-semibold text-gray-800 mb-3">🎁 You now have access to:</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Unlimited AI recipe generation
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Starbucks secret menu drinks
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Walmart grocery integration
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Recipe history & favorites
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">✓</span>
                Community features
              </li>
            </ul>
          </div>

          <button
            onClick={onContinue}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-all transform hover:scale-105"
          >
            Start Exploring Premium Features! 🚀
          </button>

          <p className="text-gray-500 text-sm mt-4">
            You can manage your subscription anytime in your account settings
          </p>
        </div>
      </div>
    );
  }

  return null;
};

export default SubscriptionSuccess;