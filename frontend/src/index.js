import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import * as serviceWorkerRegistration from './services/serviceWorkerRegistration'; // Import service worker at the top

// Import Bootstrap CSS
import 'bootstrap/dist/css/bootstrap.min.css';

// Import FontAwesome
import { library } from '@fortawesome/fontawesome-svg-core';
import { fas } from '@fortawesome/free-solid-svg-icons';
// Import AuthProvider
import { AuthProvider } from './contexts/AuthContext';

library.add(fas);  // Add FontAwesome icons to the library

// Find the root DOM node
const container = document.getElementById('root');

// Use createRoot instead of ReactDOM.render
const root = createRoot(container);

// Wrap App inside BrowserRouter and AuthProvider
root.render(
  <AuthProvider>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </AuthProvider>
);

// Register the service worker to enable offline capabilities
serviceWorkerRegistration.register();
