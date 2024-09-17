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
// Import AuthProvider
import { AuthProvider } from './contexts/AuthContext';
import Loading from './components/Loading';
import ErrorBoundary from './components/ErrorBoundary';

// Add FontAwesome icons to the library
library.add(fas);

// Find the root DOM node
const container = document.getElementById('root');

// Use createRoot instead of ReactDOM.render
const root = createRoot(container);

// Wrap App inside BrowserRouter, AuthProvider, ErrorBoundary, and Suspense
root.render(
  <ErrorBoundary>
    <AuthProvider>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <App />
        </Suspense>
      </BrowserRouter>
    </AuthProvider>
  </ErrorBoundary>
);

// Register the service worker to enable offline capabilities
serviceWorkerRegistration.register();
