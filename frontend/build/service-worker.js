/* eslint-disable no-restricted-globals */

const CACHE_NAME = 'sales_app_v1';
const CACHE_EXPIRATION_MS = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
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

// Install event - caching essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return Promise.all(
          urlsToCache.map(url => {
            return cache.add(url).catch((error) => {
              console.error(`Failed to cache ${url}:`, error);
            });
          })
        );
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

// Helper function to add response to cache with timestamp
const addToCacheWithExpiration = (cache, request, response) => {
  const responseClone = response.clone();
  const now = Date.now();
  const headers = new Headers(responseClone.headers);
  headers.append('sw-cache-timestamp', now.toString());
  const responseWithHeaders = new Response(responseClone.body, {
    status: responseClone.status,
    statusText: responseClone.statusText,
    headers: headers
  });

  // Only cache GET requests with HTTP or HTTPS scheme
  if (request.method === 'GET' && (request.url.startsWith('http://') || request.url.startsWith('https://'))) {
    cache.put(request, responseWithHeaders).catch(error => {
      console.error('Failed to cache response:', error);
    });
  } else {
    console.warn(`Request not cached: ${request.url}. Unsupported method or scheme.`);
  }
};

// Fetch event - offline-first strategy with stale-while-revalidate and cache expiration
self.addEventListener('fetch', (event) => {
  // Ignore requests from chrome-extension or non-GET methods
  if (event.request.url.startsWith('chrome-extension:') || event.request.method !== 'GET') {
    return;
  }

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            addToCacheWithExpiration(cache, event.request, networkResponse);
          }
          return networkResponse;
        }).catch(() => {
          // If network fetch fails, serve offline page for navigation requests
          if (event.request.mode === 'navigate') {
            return cache.match('/offline.html');
          }
        });

        // Serve cached response if it exists and is not expired
        if (cachedResponse) {
          const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
          if (timestamp && (Date.now() - parseInt(timestamp, 10)) < CACHE_EXPIRATION_MS) {
            return cachedResponse; // Return valid cached response
          } else {
            // Cache is expired, remove it
            cache.delete(event.request);
          }
        }
        // Serve network response or offline page if cache expired or not found
        return fetchPromise;
      });
    })
  );
});

// Function to cache specific dynamic URLs (e.g., sale details)
const cacheDynamicRoute = (saleId) => {
  const dynamicUrl = `/sales/${saleId}`;
  return caches.open(CACHE_NAME).then((cache) => {
    return fetch(dynamicUrl).then((response) => {
      if (response && response.status === 200) {
        addToCacheWithExpiration(cache, dynamicUrl, response);
      } else {
        console.warn(`Failed to cache dynamic route ${dynamicUrl}: Status ${response.status}`);
      }
    }).catch((error) => {
      console.error(`Failed to cache dynamic route ${dynamicUrl}:`, error);
    });
  });
};

// Example of caching a sale when created or updated
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'CACHE_DYNAMIC_ROUTE') {
    cacheDynamicRoute(event.data.saleId);
  }
});
