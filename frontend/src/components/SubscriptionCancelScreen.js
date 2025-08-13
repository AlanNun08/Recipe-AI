import React from 'react';

const SubscriptionCancelScreen = ({ onClose, onRetry, showNotification }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-8 text-center">
        {/* Cancel Icon */}
        <div className="bg-gray-100 rounded-full h-16 w-16 mx-auto mb-4 flex items-center justify-center">
          <span className="text-gray-600 text-3xl">❌</span>
        </div>
        
        {/* Title */}
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Payment Cancelled</h2>
        
        {/* Message */}
        <p className="text-gray-600 mb-6">
          Your payment was cancelled. No charges were made to your account.
        </p>
        
        {/* What you're missing */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-800 mb-2">Premium Features Include:</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>🍳 30 individual recipes per month</li>
            <li>📅 3 weekly meal plans per month</li>
            <li>☕ 30 Starbucks secret drinks per month</li>
            <li>🛒 Advanced Walmart shopping integration</li>
            <li>💎 Unlimited recipe history access</li>
          </ul>
        </div>
        
        {/* Action Buttons */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={onRetry}
            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 font-medium"
          >
            Try Again
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            Continue with Free Trial
          </button>
        </div>
        
        {/* Support */}
        <div className="mt-4 text-center text-sm text-gray-500">
          Need help? Contact our support team
        </div>
      </div>
    </div>
  );
};

export default SubscriptionCancelScreen;