/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'sales_app_v2';
const OFFLINE_CACHE = 'offline-cache';
const CACHE_EXPIRATION_MS = 2 * 60 * 1000; // 2 minutes
const MAX_CACHE_ITEMS = 30;

const urlsToCache = [
  '/',
  '/index.html',
  '/offline.html',
  '/favicon.ico',
  '/manifest.json',
  '/robots.txt',
  '/logo192.png',
  '/logo512.png',
  '/static/css/main.css',
  '/static/js/bundle.js',
];

// Helper to limit cache size
const limitCacheSize = async (cache, maxItems) => {
  const keys = await cache.keys();
  if (keys.length > maxItems) {
    await cache.delete(keys[0]); // Delete the oldest entry
    limitCacheSize(cache, maxItems); // Recursively check again
  }
};

// Install event - caching essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
      .catch((error) => console.error('Failed to cache essential assets:', error))
  );
  self.skipWaiting(); // Activate the service worker immediately after installation
});

// Activate event - clearing old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME && cache !== OFFLINE_CACHE) {
            console.log('Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Take control of all clients immediately
});

// Add response to cache with timestamp
const addToCacheWithExpiration = async (cache, request, response) => {
  if (!response || response.status < 200 || response.status > 599) {
    console.warn(`Invalid response status ${response?.status} for request ${request.url}. Not caching.`);
    return; // Exit if the response is invalid
  }

  const now = Date.now();
  const responseClone = response.clone();
  const headers = new Headers(responseClone.headers);
  headers.append('sw-cache-timestamp', now.toString());

  const responseWithHeaders = new Response(responseClone.body, {
    status: responseClone.status,
    statusText: responseClone.statusText,
    headers: headers,
  });

  if (request.method === 'GET') {
    await cache.put(request, responseWithHeaders);
    await limitCacheSize(cache, MAX_CACHE_ITEMS); // Limit cache size
  } else {
    console.warn(`Request not cached: ${request.url}. Unsupported method or scheme.`);
  }
};

// Check if cached response has expired
const isCacheExpired = (cachedResponse) => {
  const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
  if (!timestamp) return true;
  return Date.now() - parseInt(timestamp, 10) > CACHE_EXPIRATION_MS;
};

// Fetch event - Offline-first for static assets, network-first for dynamic content
self.addEventListener('fetch', (event) => {
  if (event.request.url.startsWith('chrome-extension:') || event.request.method !== 'GET') {
    return; // Ignore unsupported requests
  }

  // Serve cached static assets
  if (urlsToCache.includes(event.request.url)) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse && !isCacheExpired(cachedResponse)) {
          return cachedResponse; // Return cached response if valid
        }
        return fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse && networkResponse.status >= 200 && networkResponse.status <= 599) {
              return caches.open(CACHE_NAME).then((cache) => {
                addToCacheWithExpiration(cache, event.request, networkResponse);
                return networkResponse.clone();
              });
            } else {
              console.warn(`Failed network request: ${networkResponse.status}`);
              return networkResponse; // Return the network response even if it failed
            }
          })
          .catch(() => caches.match('/offline.html')); // Serve offline.html if network fails
      })
    );
    return;
  }

  // Handle dynamic requests
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (!networkResponse || networkResponse.status === 0) {
          throw new Error('Network response was not valid.');
        }
        return caches.open(CACHE_NAME).then((cache) => {
          addToCacheWithExpiration(cache, event.request, networkResponse);
          return networkResponse.clone();
        });
      })
      .catch((error) => {
        console.error('Fetch error:', error);
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse && !isCacheExpired(cachedResponse)) {
            return cachedResponse; // Return valid cached response
          }
          return caches.match('/offline.html'); // Fallback to offline page
        });
      })
  );
});

// Dynamic route caching for sales
const cacheDynamicRoute = async (saleId) => {
  const dynamicUrl = `/sales/${saleId}`;
  const cache = await caches.open(CACHE_NAME);
  return fetch(dynamicUrl)
    .then((response) => {
      if (response && response.status === 200) {
        addToCacheWithExpiration(cache, dynamicUrl, response);
      } else {
        console.warn(`Failed to cache dynamic route ${dynamicUrl}: Status ${response.status}`);
      }
    })
    .catch((error) => {
      console.error(`Failed to cache dynamic route ${dynamicUrl}:`, error);
    });
};

// Message listener for dynamic caching
self.addEventListener('message', (event) => {
  if (event.data?.type === 'CACHE_DYNAMIC_ROUTE') {
    cacheDynamicRoute(event.data.saleId);
  }
});
