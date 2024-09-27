// hooks/useServiceWorker.js
import { useEffect, useRef } from 'react';
import * as serviceWorkerRegistration from '../services/serviceWorkerRegistration';

export const useServiceWorker = (showToast) => {
  const waitingServiceWorker = useRef(null);

  // Register service worker and listen for updates
  useEffect(() => {
    const registerServiceWorker = () => {
      try {
        serviceWorkerRegistration.register({
          onUpdate: (registration) => {
            showToast('update', 'A new version is available. Click here to update.', 'Update Available');
            waitingServiceWorker.current = registration.waiting;
          },
        });
      } catch (error) {
        console.error('Service worker registration failed:', error);
      }
    };

    registerServiceWorker();
  }, [showToast]);

  // Function to handle service worker update
  const updateServiceWorker = () => {
    if (waitingServiceWorker.current) {
      waitingServiceWorker.current.postMessage({ type: 'SKIP_WAITING' });
      waitingServiceWorker.current.addEventListener('statechange', (event) => {
        if (event.target.state === 'activated') {
          window.location.reload();
        }
      });
    }
  };

  return { updateServiceWorker };
};
