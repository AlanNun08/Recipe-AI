import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

const TRIAL_LIMIT_FALLBACK = {
  individual_recipes: 50,
  weekly_plans: 5,
  starbucks_drinks: 10,
};

const GENERATION_ROWS = [
  { key: 'individual_recipes', label: 'Individual Recipes', icon: '🍳' },
  { key: 'weekly_plans', label: 'Weekly Meal Plans', icon: '🗓️' },
  { key: 'starbucks_drinks', label: 'Starbucks Drinks', icon: '☕' },
];

const TrialWelcomeScreen = ({ user, onContinue, showNotification }) => {
  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  const userId = user?.id || user?.user_id || '';
  const hasStoredSession = Boolean(localStorage.getItem('user') || sessionStorage.getItem('user'));
  const [trialStatus, setTrialStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const notifyRef = useRef(showNotification);

  useEffect(() => {
    notifyRef.current = showNotification;
  }, [showNotification]);

  useEffect(() => {
    if (!userId) {
      if (!hasStoredSession) {
        setLoading(false);
      }
      return;
    }

    let isMounted = true;

    const loadTrialStatus = async () => {
      try {
        const response = await axios.get(`${API}/api/user/trial-status/${userId}`);
        if (isMounted) {
          setTrialStatus(response.data);
        }
      } catch (error) {
        console.error('Failed to load post-verification trial status:', error);
        if (isMounted) {
          setTrialStatus(null);
        }
        notifyRef.current?.('We could not load your live trial counters, so default trial limits are shown.', 'warning');
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadTrialStatus();

    return () => {
      isMounted = false;
    };
  }, [API, hasStoredSession, userId]);

  const getTrialDaysLeft = () => {
    const value = trialStatus?.trial_days_left;
    if (typeof value === 'number' && Number.isFinite(value)) {
      return Math.max(0, value);
    }
    return 7;
  };

  const getUsageData = (key) => trialStatus?.usage_limits?.usage?.[key] || null;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-sky-50 to-amber-50 flex items-center justify-center p-4">
        <div className="rounded-3xl bg-white px-10 py-12 text-center shadow-2xl">
          <div className="mx-auto mb-5 h-12 w-12 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          <h2 className="text-2xl font-bold text-slate-900">Setting up your free trial</h2>
          <p className="mt-2 text-slate-600">Loading your generation limits...</p>
        </div>
      </div>
    );
  }

  if (!userId && !hasStoredSession) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-sky-50 to-amber-50 flex items-center justify-center p-4">
        <div className="max-w-md rounded-3xl bg-white p-8 text-center shadow-2xl">
          <div className="mb-4 text-6xl">🔐</div>
          <h2 className="text-2xl font-bold text-slate-900">Sign in to continue</h2>
          <p className="mt-2 text-slate-600">Your trial overview is available after your account session is active.</p>
          <button
            type="button"
            onClick={onContinue}
            className="mt-6 w-full rounded-2xl bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-800"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.18),_transparent_38%),linear-gradient(135deg,_#ecfeff_0%,_#eff6ff_45%,_#fff7ed_100%)] p-4">
      <div className="mx-auto max-w-5xl py-8 md:py-12">
        <div className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.14)] backdrop-blur">
          <div className="border-b border-emerald-100 bg-gradient-to-r from-emerald-500 via-sky-500 to-amber-400 px-6 py-10 text-white md:px-10">
            <div className="text-5xl md:text-6xl">🎉</div>
            <h1 className="mt-4 text-3xl font-black tracking-tight md:text-5xl">Your Free Trial Is Ready</h1>
            <p className="mt-3 max-w-2xl text-base text-white/90 md:text-lg">
              Your account is verified. Here’s what you can generate during the free trial before you need to subscribe.
            </p>
            <div className="mt-6 inline-flex rounded-full bg-white/20 px-4 py-2 text-sm font-semibold">
              {trialStatus?.trial_active === false
                ? 'Trial currently inactive'
                : `${getTrialDaysLeft()} days left in your 7-day trial`}
            </div>
          </div>

          <div className="px-6 py-8 md:px-10">
            <div className="grid gap-4 md:grid-cols-3">
              {GENERATION_ROWS.map((row) => {
                const usage = getUsageData(row.key);
                const total = usage?.trial_limit ?? TRIAL_LIMIT_FALLBACK[row.key];
                const remaining = usage?.trial_remaining ?? total;
                const used = usage?.used ?? 0;

                return (
                  <div key={row.key} className="rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
                    <div className="text-4xl">{row.icon}</div>
                    <h2 className="mt-3 text-xl font-bold text-slate-900">{row.label}</h2>
                    <div className="mt-4 text-4xl font-black text-slate-900">{total}</div>
                    <div className="text-sm font-medium text-slate-500">free generations included</div>
                    <div className="mt-4 flex items-center justify-between rounded-2xl bg-white px-4 py-3 text-sm">
                      <span className="text-slate-600">Remaining</span>
                      <span className="font-bold text-emerald-700">{remaining}</span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-sm text-slate-500">
                      <span>Used so far</span>
                      <span>{used}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 rounded-3xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900">
              Your usage is tracked separately for individual recipes, weekly plans, and Starbucks drinks. You can check the live remaining counts again anytime in Settings.
            </div>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={onContinue}
                className="rounded-2xl bg-slate-900 px-6 py-3 font-semibold text-white hover:bg-slate-800"
              >
                Continue to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrialWelcomeScreen;
