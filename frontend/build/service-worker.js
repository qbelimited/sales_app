/* eslint-disable no-restricted-globals */

const CACHE_NAME = `sales_app_v${self.__APP_VERSION__ || '1.0.0'}`; // Versioned cache
const CACHE_EXPIRATION_MS = 3 * 60 * 1000; // 3 minutes for static content
const DYNAMIC_CACHE_EXPIRATION_MS = 1 * 60 * 1000; // 1 minute for dynamic content
const CACHE_ITEM_LIMIT = 30; // Limit of 30 cached items
const FETCH_TIMEOUT = 5000; // 5 seconds timeout for network requests

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

// Install event - caching essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Failed to open cache during install:', error);
      })
  );
  self.skipWaiting(); // Activate the service worker immediately after installation
});

// Activate event - clearing old caches and notifying clients
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

  // Notify clients of updated content
  self.clients.claim().then(() => {
    self.clients.matchAll().then((clients) => {
      clients.forEach((client) => {
        client.postMessage({
          type: 'NEW_SERVICE_WORKER',
          message: 'New content available. Please refresh the page.',
        });
      });
    });
  });
});

// Helper function to add response to cache with timestamp and limit cache size
const addToCacheWithExpiration = (cache, request, response, expirationMs = CACHE_EXPIRATION_MS) => {
  const responseClone = response.clone();
  const now = Date.now();
  const headers = new Headers(responseClone.headers);
  headers.append('sw-cache-timestamp', now.toString());
  headers.append('sw-cache-expiration', expirationMs.toString());

  const responseWithHeaders = new Response(responseClone.body, {
    status: responseClone.status,
    statusText: responseClone.statusText,
    headers: headers,
  });

  return cache.put(request, responseWithHeaders)
    .then(() => enforceCacheLimit(cache))
    .catch(error => console.error('Failed to cache response:', error));
};

// Enforce cache limit by removing the oldest cache entries if limit is exceeded
const enforceCacheLimit = async (cache) => {
  const cacheKeys = await cache.keys();
  if (cacheKeys.length > CACHE_ITEM_LIMIT) {
    const cacheItems = await Promise.all(
      cacheKeys.map(async (request) => {
        const cachedResponse = await cache.match(request);
        const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
        return { request, timestamp: parseInt(timestamp, 10) || 0 };
      })
    );

    // Sort cache items by timestamp (oldest first) and remove the oldest entries
    cacheItems.sort((a, b) => a.timestamp - b.timestamp);

    const itemsToDelete = cacheItems.slice(0, cacheKeys.length - CACHE_ITEM_LIMIT);
    return Promise.all(itemsToDelete.map(item => cache.delete(item.request)))
      .then(() => {
        console.log(`Cache limit enforced, removed ${itemsToDelete.length} old items.`);
      });
  }
};

// Check if a cached response is expired based on its headers
const isCacheExpired = (cachedResponse) => {
  const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
  const expirationMs = parseInt(cachedResponse.headers.get('sw-cache-expiration'), 10);
  return (Date.now() - parseInt(timestamp, 10)) > expirationMs;
};

// Helper function to handle fetch with a timeout
const fetchWithTimeout = (request, timeout = FETCH_TIMEOUT) => {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error('Request timed out'));
    }, timeout);

    fetch(request).then((response) => {
      clearTimeout(timeoutId);
      resolve(response);
    }).catch(reject);
  });
};

// Fetch event - handling both static and dynamic content with expiration rules
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Only cache HTML, CSS, JS, and images
  const cacheableFileTypes = /\.(html|css|js|png|jpg|jpeg|svg|gif)$/i;
  if (!cacheableFileTypes.test(url.pathname)) {
    return;
  }

  // Network-first strategy for API requests or dynamic content
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/sales/')) {
    event.respondWith(
      fetchWithTimeout(event.request)
        .then((networkResponse) => {
          return caches.open(CACHE_NAME).then((cache) => {
            if (networkResponse && networkResponse.status === 200) {
              addToCacheWithExpiration(cache, event.request, networkResponse, DYNAMIC_CACHE_EXPIRATION_MS);
            }
            return networkResponse;
          });
        })
        .catch(() => caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse && !isCacheExpired(cachedResponse)) {
            return cachedResponse; // Return valid cached response
          }
          return caches.match('/offline.html'); // Fallback to offline page
        }))
    );
    return;
  }

  // For other requests (e.g., static assets), use cache-first with expiration check
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse && !isCacheExpired(cachedResponse)) {
        return cachedResponse; // Return valid cached response
      }

      return fetchWithTimeout(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              addToCacheWithExpiration(cache, event.request, networkResponse);
            });
          }
          return networkResponse;
        })
        .catch(() => caches.match('/offline.html')); // Fallback to offline page if all fails
    })
  );
});

// Function to cache specific dynamic URLs (e.g., sale details)
const cacheDynamicRoute = (saleId) => {
  const dynamicUrl = `/sales/${saleId}`;
  return caches.open(CACHE_NAME).then((cache) => {
    return fetch(dynamicUrl).then((response) => {
      if (response && response.status === 200) {
        addToCacheWithExpiration(cache, dynamicUrl, response, DYNAMIC_CACHE_EXPIRATION_MS);
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

// Notify clients when a new service worker takes over
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
