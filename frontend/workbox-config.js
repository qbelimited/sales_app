module.exports = {
  globDirectory: 'build/',
  globPatterns: ['**/*.{html,js,css,png,jpg,json,ico}'],
  swDest: 'build/service-worker.js',
  runtimeCaching: [
    {
      urlPattern: /^https?.*\.(?:png|jpg|jpeg|svg|gif|ico)$/,
      handler: 'CacheFirst', // Cache images and icons first
      options: {
        cacheName: 'image-cache',
        expiration: {
          maxEntries: 50,
          maxAgeSeconds: 60 * 60 * 24, // Cache images for 1 day
        },
      },
    },
    {
      urlPattern: /^https?.*\/api\/.*$/, // API requests
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 * 4, // Cache API responses for 4 hours
        },
        networkTimeoutSeconds: 30, // Timeout network request after 10 seconds
      },
    },
    {
      urlPattern: /\/offline\.html$/,
      handler: 'CacheFirst', // Cache offline page first
      options: {
        cacheName: 'offline-cache',
        expiration: {
          maxEntries: 1,
        },
      },
    },
    {
      urlPattern: /^https?.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'runtime-cache',
        expiration: {
          maxEntries: 30,
          maxAgeSeconds: 60 * 60 * 4, // 4 hours
        },
      },
    },
  ],
  skipWaiting: true,
  clientsClaim: true,
};
