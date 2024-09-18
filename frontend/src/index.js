// index.js
import React, { Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import * as serviceWorkerRegistration from './services/serviceWorkerRegistration';

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css';

// Import FontAwesome
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';

// Import AuthProvider and UserProvider
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext'; // Import UserProvider
import Loading from './components/Loading';
import ErrorBoundary from './components/ErrorBoundary';
import useToasts from './hooks/useToasts'; // Import useToasts for toast notifications

// Add FontAwesome icons to the library
library.add(fas);

// Find the root DOM node
const container = document.getElementById('root');

// Use createRoot instead of ReactDOM.render
const root = createRoot(container);

// Create a wrapper component to access showToast
const AppWrapper = () => {
  const { showToast } = useToasts(); // Get the showToast function from the hook

  return (
    <UserProvider showToast={showToast}> {/* Pass showToast to UserProvider */}
      <App />
    </UserProvider>
  );
};

// Wrap App inside BrowserRouter, AuthProvider, ErrorBoundary, and Suspense
root.render(
  <ErrorBoundary>
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <AppWrapper /> {/* Use the wrapper that includes UserProvider */}
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  </ErrorBoundary>
);

// Register the service worker to enable offline capabilities
const registerServiceWorker = async () => {
  try {
    await serviceWorkerRegistration.register();
  } catch (error) {
    console.error('Service worker registration failed:', error);
    // Optionally, provide user feedback here (e.g., a toast notification)
  }
};

registerServiceWorker();
