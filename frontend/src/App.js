import React, { useEffect, Suspense, useState } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import HelpTour from './components/HelpTour';
import ErrorBoundary from './components/ErrorBoundary';
import Loading from './components/Loading';
import { useAuth } from './contexts/AuthContext'; // Use the correct hook for auth context
import useToasts from './hooks/useToasts';
import routes, { userRoles } from './routes';
import './App.css';

const LoginPage = React.lazy(() => import('./pages/LoginPage'));

function App() {
  const { state, logout } = useAuth(); // Correct hook name
  const { role } = state;
  const { toasts, showToast, removeToast } = useToasts();
  const [showHelpTour, setShowHelpTour] = useState(false);
  const navigate = useNavigate();

  // Show help tour if it's the user's first time
  useEffect(() => {
    if (!localStorage.getItem('helpTourShown')) {
      setShowHelpTour(true);
      localStorage.setItem('helpTourShown', 'true');
    }
  }, []);

  // Handle navigation after login or logout
  useEffect(() => {
    if (role?.id) {
      const redirectPath = role.id === userRoles.ADMIN ? '/manage-users' : '/sales';
      navigate(redirectPath);
    } else {
      navigate('/login');
    }
  }, [role, navigate]);

  return (
    <ErrorBoundary>
      <div>
        {/* Conditionally render Navbar and Sidebar based on user's role */}
        {role?.id && <Navbar onLogout={logout} showToast={showToast} />}
        {role?.id && <Sidebar />}
        {showHelpTour && <HelpTour />}

        <div className="content" style={{ marginLeft: role?.id ? '250px' : '0', transition: 'all 0.3s ease-in-out' }}>
          <Suspense fallback={<Loading />}>
            <Routes>
              {/* Login route */}
              <Route path="/login" element={<LoginPage showToast={showToast} />} />

              {/* Dynamically generate routes */}
              {routes.map((route, index) => (
                <Route
                  key={index}
                  path={route.path}
                  element={
                    <ProtectedRoute allowedRoles={route.allowedRoles} userRole={role?.id}>
                      <route.component showToast={showToast} />
                    </ProtectedRoute>
                  }
                />
              ))}

              {/* Fallback route */}
              <Route path="*" element={<Navigate to={role?.id ? "/sales" : "/login"} />} />
            </Routes>
          </Suspense>
        </div>

        {/* Global Toaster for notifications */}
        <Toaster toasts={toasts} removeToast={removeToast} />
      </div>
    </ErrorBoundary>
  );
}

export default App;
