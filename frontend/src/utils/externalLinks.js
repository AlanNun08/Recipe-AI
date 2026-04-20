export const isMobileBrowser = () => {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent || navigator.vendor || '';
  return /android|iphone|ipad|ipod|mobile/i.test(ua) || window.innerWidth <= 768;
};

export const openExternalLink = (url, { preferSameTabOnMobile = false, allowSameTabFallback = true } = {}) => {
  if (!url || typeof window === 'undefined') return false;

  if (preferSameTabOnMobile && isMobileBrowser()) {
    window.location.assign(url);
    return true;
  }

  try {
    const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
    if (newWindow) {
      try {
        newWindow.opener = null;
      } catch (_) {
        // noop
      }
      return true;
    }
  } catch (_) {
    // fall through to same-tab fallback
  }

  if (allowSameTabFallback) {
    window.location.assign(url);
    return true;
  }

  return false;
};

const WALMART_ITEM_ID_PATTERNS = [
  /\/ip(?:\/[^/?#]+)?\/(\d+)/i,
  /[?&]items=([\d,]+)/i,
];

export const normalizeWalmartItemId = (value) => {
  if (value == null) return '';

  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(Math.trunc(value));
  }

  const raw = String(value).trim();
  if (!raw) return '';

  if (/^\d+$/.test(raw)) {
    return raw;
  }

  for (const pattern of WALMART_ITEM_ID_PATTERNS) {
    const match = raw.match(pattern);
    if (!match) continue;

    const candidate = match[1]
      .split(',')
      .map((part) => part.trim())
      .find((part) => /^\d+$/.test(part));

    if (candidate) {
      return candidate;
    }
  }

  return '';
};

export const buildWalmartCartUrl = (itemIds, { affiliate = false } = {}) => {
  const ids = Array.from(
    new Set((itemIds || []).map(normalizeWalmartItemId).filter(Boolean))
  );
  if (!ids.length) return '';
  const items = ids.join(',');
  return affiliate
    ? `https://affil.walmart.com/cart/addToCart?items=${items}`
    : `https://www.walmart.com/cart/addToCart?items=${items}`;
};

export const openWalmartCart = (itemIds, options = {}) => {
  const url = buildWalmartCartUrl(itemIds, options);
  if (!url) return false;
  return openExternalLink(url, {
    preferSameTabOnMobile: true,
    allowSameTabFallback: true,
  });
};
