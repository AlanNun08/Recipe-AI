// Service Worker for PWA functionality - PRODUCTION DOMAIN
const CACHE_NAME = 'v121-walmart-fix-deployed';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// Install event - MANUAL SHOPPING MODE SUPPORT
self.addEventListener('install', (event) => {
  // Clear all caches for manual shopping support
  event.waitUntil(
    caches.keys().then(cacheNames => {
      // Delete old caches for manual shopping support
      return Promise.all(
        cacheNames.map(cacheName => {
          // Delete cache
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      // Create manual shopping cache
      return caches.open(CACHE_NAME);
    }).then(() => {
      // Manual shopping cache created
      return self.skipWaiting();
    })
  );
});

// Activate event - IMMEDIATE CONTROL
self.addEventListener('activate', (event) => {
  console.log('🚀 CLEAN SERVICE WORKER ACTIVATING');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName !== CACHE_NAME;
        }).map(cacheName => {
          console.log('🗑️ FINAL CLEANUP:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('✅ COMPLETE CLEANUP DONE');
      return self.clients.claim();
    })
  );
});

// Fetch event - CLEAN HANDLING
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
  );
});

// Push notification event
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New notification',
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png'
  };

  event.waitUntil(
    self.registration.showNotification('AI Chef', options)
  );
});