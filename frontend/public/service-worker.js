/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'sales_app_v2';
const CACHE_EXPIRATION_MS = 2 * 60 * 1000; // 2 minutes in milliseconds
const MAX_CACHE_ITEMS = 30; // Limit cache size to prevent it from growing indefinitely

const urlsToCache = [
  '/',
  '/index.html',
  '/offline.html', // Ensure offline page is included
  '/favicon.ico',
  '/manifest.json',
  '/robots.txt',
  '/logo192.png',
  '/logo512.png',
  // Static assets (Adjust paths based on your build setup)
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
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache).catch((error) => {
        console.error('Failed to cache essential assets:', error);
      });
    })
  );
  self.skipWaiting(); // Activate the service worker immediately after installation
});

// Activate event - clearing old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Deleting old cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  return self.clients.claim(); // Take control of all clients immediately
});

// Helper function to add response to cache with timestamp and limit cache size
const addToCacheWithExpiration = async (cache, request, response) => {
  // Don't cache if response status is invalid or indicates an error
  if (!response || response.status === 0 || response.status >= 400) {
    return;
  }

  const responseClone = response.clone();
  const now = Date.now();
  const headers = new Headers(responseClone.headers);
  headers.append('sw-cache-timestamp', now.toString());

  const responseWithHeaders = new Response(responseClone.body, {
    status: responseClone.status,
    statusText: responseClone.statusText,
    headers: headers
  });

  if (request.method === 'GET' && (request.url.startsWith('http://') || request.url.startsWith('https://'))) {
    await cache.put(request, responseWithHeaders);
    await limitCacheSize(cache, MAX_CACHE_ITEMS); // Ensure cache size stays within limit
  } else {
    console.warn(`Request not cached: ${request.url}. Unsupported method or scheme.`);
  }
};

// Helper function to check if a cached response has expired
const isCacheExpired = (cachedResponse) => {
  const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
  if (!timestamp) return true; // If no timestamp, consider it expired
  const age = Date.now() - parseInt(timestamp, 10);
  return age > CACHE_EXPIRATION_MS; // Check if it's older than the expiration time
};

// Fetch event - applying different strategies based on content type
self.addEventListener('fetch', (event) => {
  // Ignore requests from chrome-extension or non-GET methods
  if (event.request.url.startsWith('chrome-extension:') || event.request.method !== 'GET') {
    return;
  }

  // Offline-first strategy for essential static assets
  if (urlsToCache.includes(event.request.url)) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse && !isCacheExpired(cachedResponse)) {
          return cachedResponse;
        }
        // If cache is expired or missing, fetch from network
        return fetch(event.request).then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            addToCacheWithExpiration(cache, event.request, networkResponse);
            return networkResponse.clone();
          });
        }).catch(() => caches.match('/offline.html'));
      })
    );
    return;
  }

  // Network-first strategy for dynamic content (e.g., API calls)
  event.respondWith(
    fetch(event.request).then((networkResponse) => {
      return caches.open(CACHE_NAME).then((cache) => {
        addToCacheWithExpiration(cache, event.request, networkResponse);
        return networkResponse.clone();
      });
    }).catch(() => {
      return caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse && !isCacheExpired(cachedResponse)) {
          return cachedResponse;
        }
        return caches.match('/offline.html');
      });
    })
  );
});

// Function to cache specific dynamic URLs (e.g., sale details)
const cacheDynamicRoute = async (saleId) => {
  const dynamicUrl = `/sales/${saleId}`;
  const cache = await caches.open(CACHE_NAME);
  return fetch(dynamicUrl).then((response) => {
    if (response && response.status === 200) {
      addToCacheWithExpiration(cache, dynamicUrl, response);
    } else {
      console.warn(`Failed to cache dynamic route ${dynamicUrl}: Status ${response.status}`);
    }
  }).catch((error) => {
    console.error(`Failed to cache dynamic route ${dynamicUrl}:`, error);
  });
};

// Example of caching a sale when created or updated
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CACHE_DYNAMIC_ROUTE') {
    cacheDynamicRoute(event.data.saleId);
  }
});
