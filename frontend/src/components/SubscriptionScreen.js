import React, { useState, useEffect } from 'react';

const SubscriptionScreen = ({ user, onClose, onSubscriptionUpdate }) => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingPayment, setProcessingPayment] = useState(false);
  const [processingSubscriptionAction, setProcessingSubscriptionAction] = useState(false);
  const [error, setError] = useState('');

  // Use environment variable
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';

  useEffect(() => {
    if (user?.id) {
      fetchSubscriptionStatus();
    }
  }, [user]);

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${backendUrl}/api/subscription/status/${user.id}`);
      if (response.ok) {
        const status = await response.json();
        setSubscriptionStatus(status);
      }
    } catch (error) {
      // Error fetching subscription status
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async () => {
    try {
      setProcessingPayment(true);
      setError('');

      const checkoutRequest = {
        user_id: user.id,
        user_email: user.email,
        origin_url: window.location.origin
      };

      const response = await fetch(`${backendUrl}/api/subscription/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(checkoutRequest)
      });

      if (response.ok) {
        const { url } = await response.json();
        // Redirect to Stripe checkout
        window.location.href = url;
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to create checkout session');
      }
    } catch (error) {
      // Error creating subscription
      setError('Failed to start subscription process');
    } finally {
      setProcessingPayment(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!window.confirm('Cancel your subscription at the end of the current billing period?')) {
      return;
    }

    try {
      setProcessingSubscriptionAction(true);
      setError('');

      const response = await fetch(`${backendUrl}/api/subscription/cancel/${user.id}`, {
        method: 'POST'
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to cancel subscription');
        return;
      }

      await fetchSubscriptionStatus();
      if (onSubscriptionUpdate) {
        onSubscriptionUpdate(data);
      }
    } catch (e) {
      setError('Failed to cancel subscription');
    } finally {
      setProcessingSubscriptionAction(false);
    }
  };

  const handleReactivateSubscription = async () => {
    try {
      setProcessingSubscriptionAction(true);
      setError('');

      const response = await fetch(`${backendUrl}/api/subscription/reactivate/${user.id}`, {
        method: 'POST'
      });

      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to reactivate subscription');
        return;
      }

      await fetchSubscriptionStatus();
      if (onSubscriptionUpdate) {
        onSubscriptionUpdate(data);
      }
    } catch (e) {
      setError('Failed to reactivate subscription');
    } finally {
      setProcessingSubscriptionAction(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
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
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading subscription information...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">Subscription Management</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* Current Status */}
          {subscriptionStatus && (
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-lg font-semibold mb-3">Current Status</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Access Status</p>
                  <p className={`font-semibold ${subscriptionStatus.has_access ? 'text-green-600' : 'text-red-600'}`}>
                    {subscriptionStatus.has_access ? '✅ Active' : '❌ Expired'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Subscription Type</p>
                  <p className="font-semibold capitalize">
                    {subscriptionStatus.subscription_status}
                  </p>
                </div>
              </div>

              {/* Trial Information */}
              {subscriptionStatus.trial_active && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-blue-800 font-semibold">🎉 Free Trial Active</p>
                  <p className="text-blue-700 text-sm">
                    {getDaysRemaining(subscriptionStatus.trial_end_date)} days remaining
                  </p>
                  <p className="text-blue-600 text-xs">
                    Trial expires: {formatDate(subscriptionStatus.trial_end_date)}
                  </p>
                </div>
              )}

              {/* Subscription Information */}
              {subscriptionStatus.subscription_active && (
                <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-green-800 font-semibold">💎 Premium Subscription Active</p>
                  <p className="text-green-700 text-sm">
                    Next billing: {formatDate(subscriptionStatus.next_billing_date)}
                  </p>
                  <p className="text-green-600 text-xs">
                    Renews: {formatDate(subscriptionStatus.subscription_end_date)}
                  </p>
                  {subscriptionStatus.cancel_at_period_end && (
                    <p className="text-amber-700 text-xs mt-2">
                      Cancellation scheduled. Access remains active until period end.
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Subscription Plans */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">Premium Subscription</h3>
            
            <div className="border border-purple-200 rounded-lg p-6 relative">
              <div className="absolute -top-3 left-6 bg-purple-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                MOST POPULAR
              </div>
              
              <div className="text-center mb-4">
                <h4 className="text-xl font-bold text-gray-800">Monthly Plan</h4>
                <div className="text-3xl font-bold text-purple-600 mt-2">
                  $9.99<span className="text-lg text-gray-500">/month</span>
                </div>
                <p className="text-gray-600 text-sm mt-1">After 7-day free trial</p>
              </div>

              <div className="mb-6">
                <h5 className="font-semibold text-gray-800 mb-2">Premium Features:</h5>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Unlimited AI recipe generation
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Starbucks secret menu drink generator
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Walmart grocery cart integration
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Recipe history and favorites
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Community recipe sharing
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Advanced dietary preferences
                  </li>
                </ul>
              </div>

              {/* Action Button */}
              {subscriptionStatus && !subscriptionStatus.subscription_active ? (
                <button
                  onClick={handleSubscribe}
                  disabled={processingPayment}
                  className={`w-full py-3 px-4 rounded-lg font-semibold text-white transition-colors ${
                    processingPayment
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-purple-600 hover:bg-purple-700'
                  }`}
                >
                  {processingPayment ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </span>
                  ) : subscriptionStatus.trial_active ? (
                    'Subscribe Now - Trial Will Continue'
                  ) : (
                    'Start Your Subscription'
                  )}
                </button>
              ) : (
                <div className="space-y-3">
                  <div className="text-center py-1 text-green-600 font-semibold">
                    ✅ You have an active subscription
                  </div>

                  {subscriptionStatus && (
                    <div className="flex flex-col sm:flex-row gap-3">
                      {subscriptionStatus.cancel_at_period_end ? (
                        <button
                          onClick={handleReactivateSubscription}
                          disabled={processingSubscriptionAction}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
                            processingSubscriptionAction
                              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                              : 'bg-green-100 text-green-800 hover:bg-green-200'
                          }`}
                        >
                          {processingSubscriptionAction ? 'Processing...' : 'Reactivate Subscription'}
                        </button>
                      ) : (
                        <button
                          onClick={handleCancelSubscription}
                          disabled={processingSubscriptionAction}
                          className={`flex-1 py-3 px-4 rounded-lg font-semibold transition-colors ${
                            processingSubscriptionAction
                              ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                              : 'bg-red-100 text-red-800 hover:bg-red-200'
                          }`}
                        >
                          {processingSubscriptionAction ? 'Processing...' : 'Cancel at Period End'}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Free Trial Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2">🎁 7-Day Free Trial</h4>
            <p className="text-blue-700 text-sm">
              New users get full access to all premium features for 7 days completely free. 
              No credit card required to start your trial. You can subscribe anytime during or after your trial.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionScreen;
