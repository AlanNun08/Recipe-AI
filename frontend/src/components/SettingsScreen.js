import React, { useEffect, useMemo, useState } from 'react';

const DEFAULT_SETTINGS = {
  general: {
    defaultStartPage: 'dashboard',
    units: 'us',
    reducedMotion: false,
  },
  notifications: {
    weeklyMealReminder: true,
    trialEndingReminder: true,
    billingEmails: true,
    productUpdates: false,
  },
  preferences: {
    householdSize: '2',
    budgetStyle: 'balanced',
    dietaryPreferences: [],
  },
};

const DIETARY_OPTIONS = [
  'vegetarian',
  'vegan',
  'gluten-free',
  'dairy-free',
  'keto',
  'paleo',
  'low-carb',
  'mediterranean',
  'pescatarian',
  'nut-free',
];

const SettingsSection = ({ title, subtitle, children }) => (
  <section className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 md:p-6">
    <div className="mb-4">
      <h2 className="text-lg md:text-xl font-semibold text-gray-900">{title}</h2>
      {subtitle ? <p className="text-sm text-gray-600 mt-1">{subtitle}</p> : null}
    </div>
    {children}
  </section>
);

const ToggleRow = ({ label, description, checked, onChange, disabled }) => (
  <label className={`flex items-start justify-between gap-4 py-3 ${disabled ? 'opacity-60' : ''}`}>
    <div>
      <div className="text-sm font-medium text-gray-800">{label}</div>
      {description ? <div className="text-xs text-gray-500 mt-1">{description}</div> : null}
    </div>
    <button
      type="button"
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-blue-600' : 'bg-gray-300'
      }`}
      aria-pressed={checked}
      aria-label={label}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-5' : 'translate-x-1'
        }`}
      />
    </button>
  </label>
);

const SettingsScreen = ({ user, onBack, onLogout, showNotification }) => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [processingBilling, setProcessingBilling] = useState(false);
  const [processingSubscriptionAction, setProcessingSubscriptionAction] = useState(false);
  const [processingSecurityAction, setProcessingSecurityAction] = useState(false);
  const [error, setError] = useState('');
  const [passwordResetFlow, setPasswordResetFlow] = useState({
    open: false,
    step: 'request', // request -> verify -> reset -> done
    email: user?.email || '',
    code: '',
    newPassword: '',
    confirmPassword: '',
    message: '',
  });

  const settingsStorageKey = user?.id ? `userSettings:${user.id}` : 'userSettings:anonymous';

  useEffect(() => {
    if (!user?.id) {
      setLoading(false);
      return;
    }

    loadLocalSettings();
    fetchSubscriptionStatus();
  }, [user?.id]);

  useEffect(() => {
    setPasswordResetFlow((prev) => ({
      ...prev,
      email: prev.email || user?.email || '',
    }));
  }, [user?.email]);

  const loadLocalSettings = () => {
    try {
      const stored = localStorage.getItem(settingsStorageKey);
      if (!stored) {
        setSettings(DEFAULT_SETTINGS);
        return;
      }

      const parsed = JSON.parse(stored);
      setSettings({
        general: { ...DEFAULT_SETTINGS.general, ...(parsed.general || {}) },
        notifications: { ...DEFAULT_SETTINGS.notifications, ...(parsed.notifications || {}) },
        preferences: { ...DEFAULT_SETTINGS.preferences, ...(parsed.preferences || {}) },
      });
    } catch (e) {
      setSettings(DEFAULT_SETTINGS);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await fetch(`${backendUrl}/api/subscription/status/${user.id}`);
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to load subscription status');
        return;
      }
      setSubscriptionStatus(data);
    } catch (e) {
      setError('Failed to load subscription status');
    } finally {
      setLoading(false);
    }
  };

  const saveLocalSettings = async () => {
    try {
      setSaving(true);
      localStorage.setItem(settingsStorageKey, JSON.stringify(settings));
      showNotification('Settings saved', 'success');
    } catch (e) {
      showNotification('Failed to save settings', 'error');
    } finally {
      setSaving(false);
    }
  };

  const updateSettings = (section, patch) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        ...patch,
      },
    }));
  };

  const toggleDietaryPreference = (value) => {
    setSettings((prev) => {
      const current = prev.preferences.dietaryPreferences || [];
      const next = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];

      return {
        ...prev,
        preferences: {
          ...prev.preferences,
          dietaryPreferences: next,
        },
      };
    });
  };

  const formatDate = (dateValue) => {
    if (!dateValue) return 'Unknown';
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) return 'Unknown';
    return date.toLocaleDateString();
  };

  const getDaysRemaining = (dateValue) => {
    if (!dateValue) return 0;
    const end = new Date(dateValue);
    if (Number.isNaN(end.getTime())) return 0;
    const diff = end.getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
  };

  const getTrialDaysLeftDisplay = () => {
    const apiDaysLeft = subscriptionStatus?.trial_days_left;
    if (typeof apiDaysLeft === 'number' && Number.isFinite(apiDaysLeft)) {
      return Math.max(0, apiDaysLeft);
    }
    return getDaysRemaining(subscriptionStatus?.trial_end_date);
  };

  const accountName = useMemo(() => {
    if (user?.name) return user.name;
    const first = user?.first_name || '';
    const last = user?.last_name || '';
    return `${first} ${last}`.trim() || 'Not set';
  }, [user]);

  const isVerified = useMemo(() => {
    if (typeof subscriptionStatus?.is_verified === 'boolean') return subscriptionStatus.is_verified;
    if (typeof subscriptionStatus?.verified === 'boolean') return subscriptionStatus.verified;
    return Boolean(user?.verified);
  }, [subscriptionStatus, user]);

  const generationUsageRows = useMemo(() => {
    const usage = subscriptionStatus?.usage_limits?.usage || {};
    return [
      { key: 'individual_recipes', label: 'Individual Recipes', icon: '🍳', data: usage.individual_recipes },
      { key: 'weekly_plans', label: 'Weekly Plans', icon: '🗓️', data: usage.weekly_plans },
      { key: 'starbucks_drinks', label: 'Starbucks Drinks', icon: '☕', data: usage.starbucks_drinks },
    ];
  }, [subscriptionStatus]);

  const accountStatusDisplay = useMemo(() => {
    if (!subscriptionStatus) {
      return { label: 'Loading', detail: 'Checking access', tone: 'bg-gray-100 text-gray-700' };
    }

    if (subscriptionStatus.subscription_active) {
      if (subscriptionStatus.cancel_at_period_end) {
        return {
          label: 'Premium (Ending)',
          detail: `Cancels ${formatDate(subscriptionStatus.subscription_end_date || subscriptionStatus.next_billing_date)}`,
          tone: 'bg-amber-100 text-amber-800',
        };
      }

      return {
        label: 'Premium',
        detail: 'Monthly plan active',
        tone: 'bg-green-100 text-green-800',
      };
    }

    if (subscriptionStatus.trial_active) {
        return {
          label: 'Trial',
          detail: `${getTrialDaysLeftDisplay()} days left`,
          tone: 'bg-blue-100 text-blue-800',
        };
    }

    if (subscriptionStatus.subscription_status === 'past_due') {
      return {
        label: 'Payment Due',
        detail: 'Update payment method to restore access',
        tone: 'bg-red-100 text-red-800',
      };
    }

    return {
      label: 'Trial Ended',
      detail: 'History is still available. Upgrade to generate recipes again.',
      tone: 'bg-orange-100 text-orange-800',
    };
  }, [subscriptionStatus]);

  const quickSummary = useMemo(() => {
    if (!subscriptionStatus) {
      return {
        planLabel: 'Loading',
        accessLabel: 'Checking',
        periodLabel: 'N/A',
        periodValue: 'Loading',
      };
    }

    if (subscriptionStatus.subscription_active) {
      return {
        planLabel: subscriptionStatus.cancel_at_period_end ? 'Premium (Ending)' : 'Premium Monthly',
        accessLabel: 'Full Access',
        periodLabel: subscriptionStatus.cancel_at_period_end ? 'Ends On' : 'Next Billing',
        periodValue: formatDate(subscriptionStatus.subscription_end_date || subscriptionStatus.next_billing_date),
      };
    }

    if (subscriptionStatus.subscription_status === 'past_due') {
      return {
        planLabel: 'Payment Due',
        accessLabel: subscriptionStatus.has_access ? 'Limited Access' : 'History Only',
        periodLabel: 'Action',
        periodValue: 'Update payment method',
      };
    }

    if (subscriptionStatus.trial_active) {
      return {
        planLabel: '7-Day Trial',
        accessLabel: 'Trial Access',
        periodLabel: 'Trial Ends',
        periodValue: formatDate(subscriptionStatus.trial_end_date),
      };
    }

    return {
      planLabel: 'Trial Ended',
      accessLabel: 'History Only',
      periodLabel: 'Upgrade',
      periodValue: 'Subscribe to restore generation',
    };
  }, [subscriptionStatus]);

  const handleSubscribe = async () => {
    if (!user?.id) return;
    try {
      setProcessingBilling(true);
      setError('');
      const response = await fetch(`${backendUrl}/api/subscription/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          user_email: user.email,
          origin_url: window.location.origin,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to start subscription checkout');
        return;
      }
      window.location.href = data.url;
    } catch (e) {
      setError('Failed to start subscription checkout');
    } finally {
      setProcessingBilling(false);
    }
  };

  const handleOpenBillingPortal = async () => {
    if (!user?.id) return;
    try {
      setProcessingBilling(true);
      setError('');
      const response = await fetch(`${backendUrl}/api/subscription/create-billing-portal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          origin_url: window.location.origin,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to open billing portal');
        return;
      }
      window.location.href = data.url;
    } catch (e) {
      setError('Failed to open billing portal');
    } finally {
      setProcessingBilling(false);
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
        method: 'POST',
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to cancel subscription');
        return;
      }
      showNotification(data.message || 'Subscription will cancel at period end', 'success');
      await fetchSubscriptionStatus();
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
        method: 'POST',
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to reactivate subscription');
        return;
      }
      showNotification(data.message || 'Subscription reactivated', 'success');
      await fetchSubscriptionStatus();
    } catch (e) {
      setError('Failed to reactivate subscription');
    } finally {
      setProcessingSubscriptionAction(false);
    }
  };

  const updatePasswordResetFlow = (patch) => {
    setPasswordResetFlow((prev) => ({ ...prev, ...patch }));
  };

  const handleSendPasswordResetCode = async () => {
    try {
      setProcessingSecurityAction(true);
      setError('');
      const normalizedEmail = (passwordResetFlow.email || '').trim().toLowerCase();
      if (!normalizedEmail) {
        setError('Enter your account email to receive a reset code');
        return;
      }

      const response = await fetch(`${backendUrl}/api/auth/request-password-reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: normalizedEmail }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to send reset code');
        return;
      }
      updatePasswordResetFlow({
        step: 'verify',
        email: normalizedEmail,
        message: 'Reset code sent. Check your email and enter the code below.',
      });
      showNotification('Password reset code sent to your email', 'success');
    } catch (e) {
      setError('Failed to send reset code');
    } finally {
      setProcessingSecurityAction(false);
    }
  };

  const handleVerifyPasswordResetCode = async () => {
    try {
      setProcessingSecurityAction(true);
      setError('');
      const email = (passwordResetFlow.email || '').trim().toLowerCase();
      const code = (passwordResetFlow.code || '').trim();
      if (!email || !code) {
        setError('Enter your account email and the code from your email');
        return;
      }

      const response = await fetch(`${backendUrl}/api/auth/verify-password-reset-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, verification_code: code }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to verify reset code');
        return;
      }

      updatePasswordResetFlow({
        step: 'reset',
        message: 'Code verified. Enter your new password below.',
      });
      showNotification('Reset code verified', 'success');
    } catch (e) {
      setError('Failed to verify reset code');
    } finally {
      setProcessingSecurityAction(false);
    }
  };

  const handleResetPassword = async () => {
    try {
      setProcessingSecurityAction(true);
      setError('');
      const email = (passwordResetFlow.email || '').trim().toLowerCase();
      const code = (passwordResetFlow.code || '').trim();
      const newPassword = passwordResetFlow.newPassword || '';
      const confirmPassword = passwordResetFlow.confirmPassword || '';

      if (!email || !code) {
        setError('Missing email or reset code');
        return;
      }
      if (newPassword.length < 8) {
        setError('New password must be at least 8 characters');
        return;
      }
      if (newPassword !== confirmPassword) {
        setError('New passwords do not match');
        return;
      }

      const response = await fetch(`${backendUrl}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          verification_code: code,
          new_password: newPassword,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        setError(data.detail || 'Failed to update password');
        return;
      }

      updatePasswordResetFlow({
        step: 'done',
        newPassword: '',
        confirmPassword: '',
        message: 'Password updated successfully.',
      });
      showNotification('Password changed successfully', 'success');
    } catch (e) {
      setError('Failed to update password');
    } finally {
      setProcessingSecurityAction(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 text-center max-w-md w-full">
          <h1 className="text-xl font-semibold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600 mb-4">Log in to manage account settings.</p>
          <button
            onClick={onBack}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="max-w-5xl mx-auto px-4 py-6 md:py-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-600 mt-1">
              Manage your account, subscription, billing, notifications, and preferences.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={onBack}
              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Back to Dashboard
            </button>
            <button
              onClick={saveLocalSettings}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>

        {error ? (
          <div className="mb-6 rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">
            {error}
          </div>
        ) : null}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <SettingsSection title="Account Info" subtitle="Profile and account status">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Name</div>
                  <div className="text-sm font-medium text-gray-900 mt-1">{accountName}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Email</div>
                  <div className="text-sm font-medium text-gray-900 mt-1 break-all">{user.email || 'Unknown'}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Joined</div>
                  <div className="text-sm font-medium text-gray-900 mt-1">
                    {formatDate(user.created_at || subscriptionStatus?.trial_start_date)}
                  </div>
                </div>
                <div className="md:col-span-2">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Account Status</div>
                  <div className="flex flex-wrap items-center gap-3 mt-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${accountStatusDisplay.tone}`}>
                      {accountStatusDisplay.label}
                    </span>
                    <span className="text-sm text-gray-600">{accountStatusDisplay.detail}</span>
                  </div>
                </div>
              </div>
            </SettingsSection>

            <SettingsSection title="Subscription & Billing" subtitle="Trial, plan, and access management">
              {loading ? (
                <div className="text-sm text-gray-600">Loading subscription status...</div>
              ) : (
                <div className="space-y-4">
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <div className="text-gray-500">Access</div>
                        <div className={`font-semibold mt-1 ${subscriptionStatus?.has_access ? 'text-green-700' : 'text-red-700'}`}>
                          {subscriptionStatus?.has_access ? 'Active' : 'Limited'}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-500">Plan</div>
                        <div className="font-semibold mt-1 text-gray-900 capitalize">
                          {subscriptionStatus?.subscription_active
                            ? 'Premium Monthly'
                            : subscriptionStatus?.trial_active
                              ? '7-day Trial'
                              : subscriptionStatus?.subscription_status || 'Free'}
                        </div>
                      </div>
                      <div>
                        <div className="text-gray-500">Trial Ends</div>
                        <div className="font-medium mt-1 text-gray-900">{formatDate(subscriptionStatus?.trial_end_date)}</div>
                      </div>
                      <div>
                        <div className="text-gray-500">Next Billing</div>
                        <div className="font-medium mt-1 text-gray-900">{formatDate(subscriptionStatus?.next_billing_date)}</div>
                      </div>
                    </div>
                    {subscriptionStatus?.trial_active ? (
                      <div className="mt-3 text-sm text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                        Trial active: {getTrialDaysLeftDisplay()} day(s) remaining.
                      </div>
                    ) : null}
                    {!subscriptionStatus?.has_access ? (
                      <div className="mt-3 text-sm text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                        Your trial has ended. You can still view recipe history, but generation is locked until you subscribe.
                      </div>
                    ) : null}
                    {subscriptionStatus?.cancel_at_period_end ? (
                      <div className="mt-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                        Cancellation scheduled. Access remains active until {formatDate(subscriptionStatus.subscription_end_date || subscriptionStatus.next_billing_date)}.
                      </div>
                    ) : null}
                  </div>

                  <div className="rounded-xl border border-gray-200 bg-white p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-sm font-semibold text-gray-900">Generation Usage</div>
                      <div className="text-xs text-gray-500">
                        {subscriptionStatus?.subscription_active
                          ? 'Premium tracking'
                          : subscriptionStatus?.trial_active
                            ? 'Trial limits'
                            : 'Usage history'}
                      </div>
                    </div>
                    <div className="space-y-3">
                      {generationUsageRows.map((row) => (
                        <div key={row.key} className="flex items-center justify-between gap-3 text-sm">
                          <div className="text-gray-700">
                            <span className="mr-2">{row.icon}</span>
                            {row.label}
                          </div>
                          <div className="text-right">
                            <div className="font-medium text-gray-900">
                              Used: {row.data?.used ?? 0}
                            </div>
                            {subscriptionStatus?.trial_active ? (
                              <div className="text-xs text-blue-700">
                                Remaining: {row.data?.trial_remaining ?? 0} / {row.data?.trial_limit ?? 0}
                              </div>
                            ) : subscriptionStatus?.subscription_active ? (
                              <div className="text-xs text-green-700">Included with plan</div>
                            ) : (
                              <div className="text-xs text-gray-500">Trial ended</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {!subscriptionStatus?.subscription_active ? (
                      <button
                        onClick={handleSubscribe}
                        disabled={processingBilling}
                        className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
                      >
                        {processingBilling ? 'Opening Checkout...' : 'Subscribe to Premium'}
                      </button>
                    ) : null}

                    {subscriptionStatus?.subscription_active && !subscriptionStatus?.cancel_at_period_end ? (
                      <button
                        onClick={handleCancelSubscription}
                        disabled={processingSubscriptionAction}
                        className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:bg-red-400"
                      >
                        {processingSubscriptionAction ? 'Processing...' : 'Cancel at Period End'}
                      </button>
                    ) : null}

                    {subscriptionStatus?.subscription_active && subscriptionStatus?.cancel_at_period_end ? (
                      <button
                        onClick={handleReactivateSubscription}
                        disabled={processingSubscriptionAction}
                        className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400"
                      >
                        {processingSubscriptionAction ? 'Processing...' : 'Reactivate Subscription'}
                      </button>
                    ) : null}
                  </div>
                </div>
              )}
            </SettingsSection>

            <SettingsSection title="Payment Methods" subtitle="Securely managed in Stripe Billing Portal">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="text-sm text-gray-600">
                  Update your card, billing details, and view invoices in Stripe.
                </div>
                <button
                  onClick={handleOpenBillingPortal}
                  disabled={processingBilling || !subscriptionStatus?.stripe_configured}
                  className="px-4 py-2 rounded-lg border border-blue-300 text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                >
                  {processingBilling ? 'Opening...' : 'Manage Payment Methods'}
                </button>
              </div>
              {!subscriptionStatus?.stripe_configured ? (
                <p className="text-xs text-amber-700 mt-3">
                  Stripe is not configured on the server yet. Add your Stripe environment variables to enable billing management.
                </p>
              ) : null}
            </SettingsSection>

            <SettingsSection title="Notifications" subtitle="Choose which emails and reminders you receive">
              <div className="divide-y divide-gray-100">
                <ToggleRow
                  label="Weekly meal reminders"
                  description="Helpful reminders to build next week’s meal plan."
                  checked={settings.notifications.weeklyMealReminder}
                  onChange={(value) => updateSettings('notifications', { weeklyMealReminder: value })}
                />
                <ToggleRow
                  label="Trial ending reminders"
                  description="Gentle reminders before your free trial expires."
                  checked={settings.notifications.trialEndingReminder}
                  onChange={(value) => updateSettings('notifications', { trialEndingReminder: value })}
                />
                <ToggleRow
                  label="Billing receipts and renewal emails"
                  description="Payment confirmations and subscription billing notices."
                  checked={settings.notifications.billingEmails}
                  onChange={(value) => updateSettings('notifications', { billingEmails: value })}
                />
                <ToggleRow
                  label="Product updates"
                  description="Occasional feature announcements and improvements."
                  checked={settings.notifications.productUpdates}
                  onChange={(value) => updateSettings('notifications', { productUpdates: value })}
                />
              </div>
            </SettingsSection>

            <SettingsSection title="Preferences" subtitle="Default behavior for recipes and planning">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Default Start Page</label>
                  <select
                    value={settings.general.defaultStartPage}
                    onChange={(e) => updateSettings('general', { defaultStartPage: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="dashboard">Dashboard</option>
                    <option value="recipe-generator">Recipe Generator</option>
                    <option value="weekly-recipes">Weekly Planner</option>
                    <option value="recipe-history">Recipe History</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Measurement Units</label>
                  <select
                    value={settings.general.units}
                    onChange={(e) => updateSettings('general', { units: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="us">US (cups, oz, lb)</option>
                    <option value="metric">Metric (g, kg, ml)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Household Size</label>
                  <select
                    value={settings.preferences.householdSize}
                    onChange={(e) => updateSettings('preferences', { householdSize: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="1">1 person</option>
                    <option value="2">2 people</option>
                    <option value="3-4">3-4 people</option>
                    <option value="5+">5+ people</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Budget Style</label>
                  <select
                    value={settings.preferences.budgetStyle}
                    onChange={(e) => updateSettings('preferences', { budgetStyle: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  >
                    <option value="budget">Budget-first</option>
                    <option value="balanced">Balanced</option>
                    <option value="premium">Premium ingredients</option>
                  </select>
                </div>
              </div>

              <div className="mt-4">
                <div className="text-sm font-medium text-gray-700 mb-2">Dietary Preferences</div>
                <div className="flex flex-wrap gap-2">
                  {DIETARY_OPTIONS.map((option) => {
                    const selected = settings.preferences.dietaryPreferences.includes(option);
                    return (
                      <button
                        key={option}
                        type="button"
                        onClick={() => toggleDietaryPreference(option)}
                        className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                          selected
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        {option}
                      </button>
                    );
                  })}
                </div>
              </div>
            </SettingsSection>

            <SettingsSection title="Security" subtitle="Password and account session controls">
              <div className="space-y-4">
                <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <div className="flex items-center justify-between gap-3 mb-3">
                    <div>
                      <div className="text-sm font-medium text-gray-800">Change Password</div>
                      <div className="text-xs text-gray-600 mt-1">
                        Send a code to your account email, verify it, then set a new password.
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        updatePasswordResetFlow({
                          open: !passwordResetFlow.open,
                          step: passwordResetFlow.open ? 'request' : passwordResetFlow.step,
                          message: '',
                          email: passwordResetFlow.email || user?.email || '',
                        })
                      }
                      className="px-4 py-2 rounded-lg border border-blue-300 text-blue-700 hover:bg-blue-50"
                    >
                      {passwordResetFlow.open ? 'Close' : 'Change Password'}
                    </button>
                  </div>

                  {passwordResetFlow.open ? (
                    <div className="space-y-3 border-t border-gray-200 pt-3">
                      {passwordResetFlow.message ? (
                        <div className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                          {passwordResetFlow.message}
                        </div>
                      ) : null}

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Account Email</label>
                        <input
                          type="email"
                          value={passwordResetFlow.email}
                          onChange={(e) => updatePasswordResetFlow({ email: e.target.value })}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                          placeholder="you@example.com"
                        />
                      </div>

                      {passwordResetFlow.step !== 'request' ? (
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Reset Code</label>
                          <input
                            type="text"
                            value={passwordResetFlow.code}
                            onChange={(e) => updatePasswordResetFlow({ code: e.target.value })}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm tracking-widest"
                            placeholder="123456"
                            maxLength={6}
                          />
                        </div>
                      ) : null}

                      {passwordResetFlow.step === 'reset' ? (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                            <input
                              type="password"
                              value={passwordResetFlow.newPassword}
                              onChange={(e) => updatePasswordResetFlow({ newPassword: e.target.value })}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                              placeholder="At least 8 characters"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                            <input
                              type="password"
                              value={passwordResetFlow.confirmPassword}
                              onChange={(e) => updatePasswordResetFlow({ confirmPassword: e.target.value })}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                              placeholder="Retype new password"
                            />
                          </div>
                        </>
                      ) : null}

                      {passwordResetFlow.step === 'done' ? (
                        <div className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                          Password changed successfully. Use your new password next time you log in.
                        </div>
                      ) : null}

                      <div className="flex flex-wrap gap-2">
                        {passwordResetFlow.step === 'request' ? (
                          <button
                            type="button"
                            onClick={handleSendPasswordResetCode}
                            disabled={processingSecurityAction}
                            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
                          >
                            {processingSecurityAction ? 'Sending...' : 'Send Code'}
                          </button>
                        ) : null}

                        {passwordResetFlow.step === 'verify' ? (
                          <>
                            <button
                              type="button"
                              onClick={handleVerifyPasswordResetCode}
                              disabled={processingSecurityAction}
                              className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400"
                            >
                              {processingSecurityAction ? 'Verifying...' : 'Verify Code'}
                            </button>
                            <button
                              type="button"
                              onClick={handleSendPasswordResetCode}
                              disabled={processingSecurityAction}
                              className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                            >
                              Resend Code
                            </button>
                          </>
                        ) : null}

                        {passwordResetFlow.step === 'reset' ? (
                          <button
                            type="button"
                            onClick={handleResetPassword}
                            disabled={processingSecurityAction}
                            className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:bg-green-400"
                          >
                            {processingSecurityAction ? 'Updating...' : 'Update Password'}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={onLogout}
                    className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
                  >
                    Log Out
                  </button>
                </div>
              </div>
            </SettingsSection>
          </div>

          <div className="space-y-6">
            <SettingsSection title="Quick Summary">
              <div className="space-y-3 text-sm">
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">Plan</span>
                  <span className="font-medium text-gray-900">
                    {quickSummary.planLabel}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">{quickSummary.periodLabel}</span>
                  <span className="font-medium text-gray-900 text-right">
                    {quickSummary.periodValue}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">Trial Days Left</span>
                  <span className="font-medium text-gray-900">
                    {subscriptionStatus?.trial_active ? getTrialDaysLeftDisplay() : 0}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">Access</span>
                  <span className={`font-medium ${subscriptionStatus?.has_access ? 'text-green-700' : 'text-orange-700'}`}>
                    {quickSummary.accessLabel}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">Verified</span>
                  <span className={`font-medium ${isVerified ? 'text-green-700' : 'text-amber-700'}`}>
                    {isVerified ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between gap-3">
                  <span className="text-gray-600">Free Trial Recipe Uses Left</span>
                  <span className="font-medium text-gray-900">
                    {subscriptionStatus?.trial_active
                      ? (subscriptionStatus?.usage_limits?.usage?.individual_recipes?.trial_remaining ?? 0)
                      : 0}
                  </span>
                </div>
              </div>
            </SettingsSection>

            <SettingsSection title="What You Can Do">
              <ul className="space-y-2 text-sm text-gray-600">
                <li>View recipe history even after your trial ends.</li>
                <li>Upgrade to restore recipe and weekly plan generation.</li>
                <li>Manage cards and invoices securely through Stripe.</li>
                <li>Control reminders and basic app preferences here.</li>
              </ul>
            </SettingsSection>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsScreen;
