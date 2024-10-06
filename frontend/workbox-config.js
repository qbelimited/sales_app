module.exports = {
  globDirectory: 'build/',
  globPatterns: ['**/*.{html,js,css,png,jpg,json,ico}'],
  swDest: 'build/service-worker.js',

  runtimeCaching: [
    {
      // Cache images and icons first
      urlPattern: /^https?.*\.(?:png|jpg|jpeg|svg|gif|ico)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'image-cache',
        expiration: {
          maxEntries: 50, // Maximum number of image entries
          maxAgeSeconds: 60 * 60 * 24, // Cache images for 1 day
        },
      },
    },
    {
      // API requests with NetworkFirst strategy
      urlPattern: /^https?.*\/api\/.*$/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 100, // Maximum number of API entries
          maxAgeSeconds: 60 * 60 * 4, // Cache API responses for 4 hours
        },
        networkTimeoutSeconds: 30, // Timeout network requests after 30 seconds
      },
    },
    {
      // Cache the offline page
      urlPattern: /\/offline\.html$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'offline-cache',
        expiration: {
          maxEntries: 1, // Only keep one offline page
        },
      },
    },
    {
      // Network-first strategy for other requests
      urlPattern: /^https?.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'runtime-cache',
        expiration: {
          maxEntries: 30, // Maximum number of runtime entries
          maxAgeSeconds: 60 * 60 * 4, // Cache for 4 hours
        },
      },
    },
  ],

  skipWaiting: true, // Activate new service worker immediately
  clientsClaim: true, // Take control of all clients immediately
};
