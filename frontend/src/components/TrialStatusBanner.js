import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TrialStatusBanner = ({ user, onUpgradeClick }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
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
      <div className="relative overflow-hidden rounded-2xl shadow-lg mb-4 bg-gradient-to-r from-red-600 to-red-700">
        <div className="absolute inset-0 bg-black bg-opacity-10"></div>
        
        <div className="relative z-10 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl animate-pulse">⚠️</div>
              
              <div className="text-white">
                <div className="font-bold text-lg">Trial Expired</div>
                <div className="text-sm opacity-90">
                  Subscribe to continue using premium features
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {onUpgradeClick && (
                <button
                  onClick={onUpgradeClick}
                  className="bg-white text-red-600 px-6 py-2 rounded-xl font-bold hover:shadow-lg transition-all animate-pulse"
                >
                  🚀 Subscribe Now
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
        </div>
      </div>
    );
  }

  return null;
};

export default TrialStatusBanner;