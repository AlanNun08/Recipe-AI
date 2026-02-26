export const isMobileBrowser = () => {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
  const ua = navigator.userAgent || navigator.vendor || '';
  return /android|iphone|ipad|ipod|mobile/i.test(ua) || window.innerWidth <= 768;
};

export const openExternalLink = (url, { preferSameTabOnMobile = false } = {}) => {
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

  window.location.assign(url);
  return true;
};

export const buildWalmartCartUrl = (itemIds, { affiliate = false } = {}) => {
  const ids = (itemIds || []).filter(Boolean);
  if (!ids.length) return '';
  const items = ids.join(',');
  return affiliate
    ? `https://affil.walmart.com/cart/addToCart?items=${items}`
    : `https://www.walmart.com/cart?items=${items}`;
};

export const openWalmartCart = (itemIds, options = {}) => {
  const url = buildWalmartCartUrl(itemIds, options);
  if (!url) return false;
  return openExternalLink(url, { preferSameTabOnMobile: true });
};
