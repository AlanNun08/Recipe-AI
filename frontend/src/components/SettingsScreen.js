import React, { useState, useEffect } from 'react';

const SettingsScreen = ({ user, backendUrl, onClose, onLogout, showNotification }) => {
  const [loading, setLoading] = useState(true);
  const [settingsData, setSettingsData] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    dietary_preferences: []
  });
  const [processing, setProcessing] = useState(false);

  const dietaryOptions = [
    'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 
    'paleo', 'low-carb', 'mediterranean', 'pescatarian', 'nut-free'
  ];

  useEffect(() => {
    if (user?.id) {
      fetchSettings();
    }
  }, [user]);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/user/settings/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setSettingsData(data);
        setProfileData({
          first_name: data.profile.first_name || '',
          last_name: data.profile.last_name || '',
          dietary_preferences: data.profile.dietary_preferences || []
        });
      } else {
        showNotification('Failed to load settings', 'error');
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
      showNotification('Error loading settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const updateProfile = async () => {
    setProcessing(true);
    try {
      const response = await fetch(`${backendUrl}/api/user/profile/${user.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        const result = await response.json();
        showNotification('Profile updated successfully!', 'success');
        setEditMode(false);
        await fetchSettings(); // Refresh settings
      } else {
        const error = await response.json();
        showNotification(error.detail || 'Failed to update profile', 'error');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      showNotification('Error updating profile', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const cancelSubscription = async () => {
    if (!window.confirm('Are you sure you want to cancel your subscription? Your access will continue until the next billing date.')) {
      return;
    }

    setProcessing(true);
    try {
      const response = await fetch(`${backendUrl}/api/subscription/cancel/${user.id}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        showNotification(result.message, 'success');
        await fetchSettings(); // Refresh settings to show cancellation
      } else {
        const error = await response.json();
        showNotification(error.detail || 'Failed to cancel subscription', 'error');
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      showNotification('Error cancelling subscription', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const reactivateSubscription = async () => {
    setProcessing(true);
    try {
      const response = await fetch(`${backendUrl}/api/subscription/reactivate/${user.id}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        showNotification(result.message, 'success');
        await fetchSettings(); // Refresh settings
      } else {
        const error = await response.json();
        showNotification(error.detail || 'Failed to reactivate subscription', 'error');
      }
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      showNotification('Error reactivating subscription', 'error');
    } finally {
      setProcessing(false);
    }
  };

  const handleDietaryChange = (option) => {
    setProfileData(prev => ({
      ...prev,
      dietary_preferences: prev.dietary_preferences.includes(option)
        ? prev.dietary_preferences.filter(pref => pref !== option)
        : [...prev.dietary_preferences, option]
    }));
  };

  const getUsageBarColor = (current, limit) => {
    const percentage = (current / limit) * 100;
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const redirectToUpgrade = () => {
    showNotification('Redirecting to upgrade your plan...', 'info');
    onClose();
    // This would typically navigate to subscription screen
    // For now, we'll just show a message
    setTimeout(() => {
      showNotification('Contact support to upgrade your subscription', 'info');
    }, 1000);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading settings...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!settingsData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <p className="text-red-600">Failed to load settings</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b p-6 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">⚙️ Settings</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-8">
          {/* Profile Section */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">👤 Profile</h3>
              <button
                onClick={() => editMode ? updateProfile() : setEditMode(true)}
                disabled={processing}
                className={`px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                  processing 
                    ? 'bg-gray-400 cursor-not-allowed' 
                    : editMode 
                      ? 'bg-green-600 hover:bg-green-700' 
                      : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {processing ? 'Saving...' : editMode ? 'Save Changes' : 'Edit Profile'}
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                {editMode ? (
                  <input
                    type="text"
                    value={profileData.first_name}
                    onChange={(e) => setProfileData(prev => ({ ...prev, first_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-800 py-2">{settingsData.profile.first_name || 'Not set'}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                {editMode ? (
                  <input
                    type="text"
                    value={profileData.last_name}
                    onChange={(e) => setProfileData(prev => ({ ...prev, last_name: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-800 py-2">{settingsData.profile.last_name || 'Not set'}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p className="text-gray-800 py-2">{settingsData.profile.email}</p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Preferences</label>
                {editMode ? (
                  <div className="flex flex-wrap gap-2">
                    {dietaryOptions.map(option => (
                      <button
                        key={option}
                        onClick={() => handleDietaryChange(option)}
                        className={`px-3 py-1 rounded-full text-sm transition-colors ${
                          profileData.dietary_preferences.includes(option)
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {settingsData.profile.dietary_preferences.length > 0 ? (
                      settingsData.profile.dietary_preferences.map(pref => (
                        <span key={pref} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                          {pref}
                        </span>
                      ))
                    ) : (
                      <span className="text-gray-500">None selected</span>
                    )}
                  </div>
                )}
              </div>

              {editMode && (
                <div className="md:col-span-2">
                  <button
                    onClick={() => setEditMode(false)}
                    className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 mr-2"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Subscription Section */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">💳 Subscription</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Status:</span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  settingsData.subscription.subscription_status === 'active' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {settingsData.subscription.subscription_status === 'active' ? '✅ Active' : '🆓 Trial'}
                </span>
              </div>

              {settingsData.subscription.trial_active && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-700">Trial ends:</span>
                  <span className="text-gray-800">
                    {new Date(settingsData.subscription.trial_end_date).toLocaleDateString()}
                  </span>
                </div>
              )}

              {settingsData.subscription.subscription_active && (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-700">Next billing:</span>
                    <span className="text-gray-800">
                      {new Date(settingsData.subscription.next_billing_date).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="mt-4">
                    {settingsData.subscription.cancel_at_period_end ? (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-yellow-800 mb-2">⚠️ Subscription will be cancelled at end of billing period</p>
                        <button
                          onClick={reactivateSubscription}
                          disabled={processing}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                        >
                          {processing ? 'Processing...' : 'Reactivate Subscription'}
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={cancelSubscription}
                        disabled={processing}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
                      >
                        {processing ? 'Processing...' : 'Cancel Subscription'}
                      </button>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Usage Section */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold text-gray-800">📊 Usage This Month</h3>
              {settingsData.subscription.subscription_status === 'trial' && (
                <button
                  onClick={redirectToUpgrade}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 font-medium"
                >
                  Upgrade Plan
                </button>
              )}
            </div>

            <div className="space-y-4">
              {/* Weekly Recipes */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700">🗓️ Weekly Recipe Plans</span>
                  <span className="text-sm text-gray-600">
                    {settingsData.usage.weekly_recipes.current} / {settingsData.usage.weekly_recipes.limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(
                      settingsData.usage.weekly_recipes.current, 
                      settingsData.usage.weekly_recipes.limit
                    )}`}
                    style={{ 
                      width: `${Math.min(100, (settingsData.usage.weekly_recipes.current / settingsData.usage.weekly_recipes.limit) * 100)}%` 
                    }}
                  ></div>
                </div>
              </div>

              {/* Individual Recipes */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700">🍳 Individual Recipes</span>
                  <span className="text-sm text-gray-600">
                    {settingsData.usage.individual_recipes.current} / {settingsData.usage.individual_recipes.limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(
                      settingsData.usage.individual_recipes.current, 
                      settingsData.usage.individual_recipes.limit
                    )}`}
                    style={{ 
                      width: `${Math.min(100, (settingsData.usage.individual_recipes.current / settingsData.usage.individual_recipes.limit) * 100)}%` 
                    }}
                  ></div>
                </div>
              </div>

              {/* Starbucks Drinks */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-700">☕ Starbucks Drinks</span>
                  <span className="text-sm text-gray-600">
                    {settingsData.usage.starbucks_drinks.current} / {settingsData.usage.starbucks_drinks.limit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageBarColor(
                      settingsData.usage.starbucks_drinks.current, 
                      settingsData.usage.starbucks_drinks.limit
                    )}`}
                    style={{ 
                      width: `${Math.min(100, (settingsData.usage.starbucks_drinks.current / settingsData.usage.starbucks_drinks.limit) * 100)}%` 
                    }}
                  ></div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  💡 Usage resets monthly. {settingsData.subscription.subscription_status === 'trial' 
                    ? 'Upgrade to get higher limits!' 
                    : 'Thank you for being a premium subscriber!'}
                </p>
              </div>
            </div>
          </div>

          {/* Account Actions */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">🔒 Account</h3>
            <button
              onClick={onLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsScreen;