import React, { useState, useEffect } from 'react';

const SubscriptionGate = ({ user, children, featureName = "this premium feature", onUpgrade }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Use environment variable
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

  useEffect(() => {
    if (user?.id) {
      checkSubscriptionStatus();
    }
  }, [user]);

  const checkSubscriptionStatus = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/subscription/status/${user.id}`);
      if (response.ok) {
        const status = await response.json();
        setSubscriptionStatus(status);
      }
    } catch (error) {
      // Error checking subscription status
    } finally {
      setLoading(false);
    }
  };

  const getDaysRemaining = (endDate) => {
    if (!endDate) return 0;
    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.max(0, diffDays);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  // If user has access (trial or subscription), show the content
  if (subscriptionStatus?.has_access) {
    return children;
  }

  // Show upgrade prompt
  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-8 rounded-lg border border-purple-200 text-center">
      <div className="text-6xl mb-4">🔒</div>
      <h3 className="text-2xl font-bold text-gray-800 mb-2">Premium Feature</h3>
      <p className="text-gray-600 mb-6">
        {featureName} is available with our premium subscription
      </p>

      <div className="bg-white p-6 rounded-lg shadow-sm mb-6 max-w-md mx-auto">
        <div className="text-center mb-4">
          <h4 className="text-lg font-semibold text-gray-800">Get Premium Access</h4>
          <div className="text-2xl font-bold text-purple-600 mt-2">
            $9.99<span className="text-base text-gray-500">/month</span>
          </div>
          <p className="text-purple-600 text-sm">7-week free trial included!</p>
        </div>

        <div className="text-left">
          <h5 className="font-semibold text-gray-700 mb-2">Premium includes:</h5>
          <ul className="space-y-1 text-sm text-gray-600">
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
          </ul>
        </div>
      </div>

      <button
        onClick={onUpgrade}
        className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 mr-4"
      >
        Start Free Trial 🚀
      </button>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
        <p className="text-blue-800 text-sm font-semibold">🎁 7-Week Free Trial</p>
        <p className="text-blue-700 text-xs">
          Try all premium features free for 7 weeks. No credit card required to start.
        </p>
      </div>
    </div>
  );
};

export default SubscriptionGate;