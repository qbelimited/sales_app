export function register(config) {
  if ('serviceWorker' in navigator) {
    return new Promise((resolve, reject) => {
      window.addEventListener('load', () => {
        const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

        navigator.serviceWorker.register(swUrl)
          .then((registration) => {
            // Check for updates to the service worker
            registration.onupdatefound = () => {
              const installingWorker = registration.installing;
              if (installingWorker) {
                installingWorker.onstatechange = () => {
                  if (installingWorker.state === 'installed') {
                    if (navigator.serviceWorker.controller) {
                      // New content available
                      config?.onUpdate?.(registration);
                    } else {
                      // Content cached for offline use
                      config?.onSuccess?.(registration);
                    }
                  }
                };
              }
            };
            resolve(registration); // Resolve the promise with the registration object
          })
          .catch((error) => {
            console.error('Service Worker registration failed:', error);
            reject(error); // Reject the promise on error
          });
      });
    });
  }
  return Promise.reject(new Error('Service Worker is not supported in this browser.'));
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    return navigator.serviceWorker.ready
      .then((registration) => registration.unregister())
      .catch((error) => {
        console.error('Service Worker unregistration failed:', error);
      });
  }
  return Promise.reject(new Error('Service Worker is not supported in this browser.'));
}
