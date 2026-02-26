import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TrialStatusBanner = ({ user, onUpgradeClick }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  
  const [trialStatus, setTrialStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    if (user?.id) {
      loadTrialStatus();
    }
  }, [user]);

  const loadTrialStatus = async () => {
    try {
      const response = await axios.get(`${API}/api/user/trial-status/${user.id}`);
      setTrialStatus(response.data);
    } catch (error) {
      console.error('Failed to load trial status:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDaysRemaining = (days) => {
    if (days <= 0) return 'expired';
    if (days === 1) return '1 day';
    return `${days} days`;
  };

  const getProgressPercentage = (daysLeft) => {
    const totalDays = 7; // 7-day trial
    const daysUsed = totalDays - daysLeft;
    return Math.min(100, Math.max(0, (daysUsed / totalDays) * 100));
  };

  if (isLoading || !trialStatus || isDismissed) {
    return null;
  }

  // Don't show banner for users with active subscription
  if (trialStatus.subscription_active) {
    return null;
  }

  // Show different banners based on trial status
  if (trialStatus.trial_active && trialStatus.trial_days_left > 0) {
    // Trial active - show days remaining
    const daysLeft = trialStatus.trial_days_left;
    const isUrgent = daysLeft <= 2;
    
    return (
      <div className={`relative overflow-hidden rounded-2xl shadow-lg mb-4 ${
        isUrgent 
          ? 'bg-gradient-to-r from-red-500 to-orange-500' 
          : 'bg-gradient-to-r from-blue-500 to-purple-500'
      }`}>
        <div className="absolute inset-0 bg-black bg-opacity-10"></div>
        
        <div className="relative z-10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl animate-bounce">
                {isUrgent ? '⏰' : '✨'}
              </div>
              
              <div className="text-white">
                <div className="font-bold text-lg">
                  {isUrgent ? '🚨 Trial Ending Soon!' : '🎉 Free Trial Active'}
                </div>
                <div className="text-sm opacity-90">
                  {formatDaysRemaining(daysLeft)} left in your free trial
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {onUpgradeClick && (
                <button
                  onClick={onUpgradeClick}
                  className="bg-white text-gray-800 px-4 py-2 rounded-xl font-bold hover:shadow-lg transition-all text-sm"
                >
                  💎 Upgrade Now
                </button>
              )}
              
              <button
                onClick={() => setIsDismissed(true)}
                className="text-white hover:text-gray-200 text-xl opacity-70 hover:opacity-100"
              >
                ×
              </button>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-3">
            <div className="bg-white bg-opacity-20 rounded-full h-2">
              <div 
                className="bg-white rounded-full h-2 transition-all duration-300"
                style={{ width: `${getProgressPercentage(daysLeft)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!trialStatus.has_access) {
    // Trial expired - show upgrade prompt
    return (
      <div className="relative overflow-hidden rounded-2xl shadow-lg mb-4 border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
        <div className="relative z-10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl">⏳</div>
              
              <div className="text-gray-900">
                <div className="font-bold text-lg">Your free trial has ended</div>
                <div className="text-sm text-gray-700">
                  You can still view saved recipes and history. Upgrade to continue generating new AI recipes and meal plans.
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {onUpgradeClick && (
                <button
                  onClick={onUpgradeClick}
                  className="bg-white text-amber-900 px-5 py-2 rounded-xl font-bold hover:shadow-lg transition-all border border-amber-300"
                >
                  View Plans
                </button>
              )}
              
              <button
                onClick={() => setIsDismissed(true)}
                className="text-gray-500 hover:text-gray-700 text-xl opacity-70 hover:opacity-100"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default TrialStatusBanner;
