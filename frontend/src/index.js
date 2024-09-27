import React, { Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import AppWrapper from './AppWrapper'; // Moved AppWrapper to its own file
import * as serviceWorkerRegistration from './services/serviceWorkerRegistration';
import 'bootstrap/dist/css/bootstrap.min.css';
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
import { AuthProvider } from './contexts/AuthContext';
import { ToastProvider } from './contexts/ToastContext'; // New ToastProvider for global access
import Loading from './components/Loading';
import ErrorBoundary from './components/ErrorBoundary';

// Add FontAwesome icons to the library
library.add(fas);

// Find the root DOM node
const container = document.getElementById('root');
const root = createRoot(container);

// Lazy-load service worker registration without redundant await
const registerServiceWorker = (showToast) => {
  try {
    serviceWorkerRegistration.register({
      onUpdate: (registration) => {
        // Notify the user about the update using the Toast context
        showToast('A new update is available. The page will reload to apply it.', 'info');
        if (registration.waiting) {
          registration.waiting.postMessage({ type: 'SKIP_WAITING' });
          registration.waiting.addEventListener('statechange', (event) => {
            if (event.target.state === 'activated') {
              window.location.reload();
            }
          });
        }
      },
    });
  } catch (error) {
    console.error('Service worker registration failed:', error);
  }
};

// A functional component to wrap the service worker registration with Toast
const AppWithServiceWorker = (showToast) => {
  React.useEffect(() => {
    // Register service worker after the app has loaded
    window.addEventListener('load', () => {
      registerServiceWorker(showToast);
    });
  }, [showToast]);

  return <AppWrapper />; // Render the app normally
};

// Register service worker after the app has loaded
window.addEventListener('load', () => {
  registerServiceWorker();
});

// Render the root component with error boundaries and context providers
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <ToastProvider> {/* New ToastProvider for global toast context */}
          <BrowserRouter>
            <Suspense fallback={<Loading />}>
              <AppWithServiceWorker /> {/* Moved AppWrapper to its own file */}
            </Suspense>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
