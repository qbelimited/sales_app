import React, { Suspense, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import AppWrapper from './AppWrapper';
import * as serviceWorkerRegistration from './services/serviceWorkerRegistration';
import 'bootstrap/dist/css/bootstrap.min.css';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext';
import { TourProvider } from './contexts/TourContext';
import Loading from './components/Loading';
import ErrorBoundary from './components/ErrorBoundary';

// Add FontAwesome icons to the library
library.add(fas);

// Find the root DOM node
const container = document.getElementById('root');
const root = createRoot(container);

// Register service worker with toast notifications
const registerServiceWorker = (showToast) => {
  serviceWorkerRegistration.register({
    onUpdate: (registration) => {
      showToast('A new update is available. The page will reload to apply it.', 'info');

      // If there's a waiting service worker, skip waiting and reload
      if (registration.waiting) {
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        registration.waiting.addEventListener('statechange', () => {
          if (registration.waiting.state === 'activated') {
            window.location.reload();
          }
        });
      }
    },
  }).catch((error) => {
    console.error('Service worker registration failed:', error);
  });
};

// Component to wrap the service worker registration logic
const AppWithServiceWorker = ({ showToast }) => {
  useEffect(() => {
    const handleLoad = () => registerServiceWorker(showToast);

    window.addEventListener('load', handleLoad);

    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('load', handleLoad);
    };
  }, [showToast]);

  return <AppWrapper />; // Render the main app
};

// Render the root component with error boundaries and context providers
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider>
          <TourProvider>
            <BrowserRouter>
              <Suspense fallback={<Loading />}>
                <AppWithServiceWorker />
              </Suspense>
            </BrowserRouter>
          </TourProvider>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
