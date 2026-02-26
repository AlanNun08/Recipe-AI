const DEFAULT_SETTINGS = {
  general: {
    units: 'us',
  },
  preferences: {
    householdSize: '2',
    budgetStyle: 'balanced',
    dietaryPreferences: [],
  },
};

export function getUserSettingsStorageKey(user) {
  const userId = user?.id || user?.user_id;
  return userId ? `userSettings:${userId}` : 'userSettings:anonymous';
}

export function loadSavedUserSettings(user) {
  try {
    const raw = localStorage.getItem(getUserSettingsStorageKey(user));
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw);
    return {
      general: { ...DEFAULT_SETTINGS.general, ...(parsed.general || {}) },
      preferences: { ...DEFAULT_SETTINGS.preferences, ...(parsed.preferences || {}) },
      notifications: parsed.notifications || {},
    };
  } catch (e) {
    return DEFAULT_SETTINGS;
  }
}

export function normalizeDietaryPreferencesList(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean);
}

export function householdSizeToNumber(value, fallback = 2) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  const text = String(value || '').trim();
  if (!text) return fallback;
  if (text === '5+') return 5;
  if (text === '3-4') return 4;
  const parsed = parseInt(text, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function budgetStyleToWeeklyBudget(style, fallback = 100) {
  switch ((style || '').toLowerCase()) {
    case 'budget':
      return 50;
    case 'premium':
      return 150;
    case 'balanced':
      return 100;
    default:
      return fallback;
  }
}

export function buildStarbucksPreferenceHint(settings) {
  const dietary = normalizeDietaryPreferencesList(settings?.preferences?.dietaryPreferences);
  const budgetStyle = String(settings?.preferences?.budgetStyle || '').trim();
  const hints = [];

  if (dietary.length) {
    hints.push(`${dietary.join(', ')} friendly`);
  }
  if (budgetStyle) {
    hints.push(`${budgetStyle} budget style`);
  }

  return hints.join(', ');
}
