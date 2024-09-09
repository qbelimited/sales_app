import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SalesPage from './pages/SalesPage';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage';
import NotFoundPage from './pages/NotFoundPage';
// import SalesExecutivePage from './pages/SalesExecutivePage'; // Uncomment if this page exists
// import ReportsPage from './pages/ReportsPage'; // Uncomment if this page exists
import Navbar from './components/Navbar';

const getAuthenticatedUser = () => {
  return sessionStorage.getItem('userRole');
};

// Protected Route Component
const ProtectedRoute = ({ userRole, allowedRoles, children }) => {
  if (!userRole) {
    return <Navigate to="/login" />;
  }
  if (allowedRoles.includes(userRole)) {
    return children;
  }
  return <Navigate to="/home" />;
};

function App() {
  const [userRole, setUserRole] = useState(getAuthenticatedUser());

  // Monitor session storage for changes
  useEffect(() => {
    const role = getAuthenticatedUser();
    if (role !== userRole) {
      setUserRole(role);
    }
  }, [userRole]);

  // Simulate login function - sets the user role after login
  const handleLogin = (role) => {
    sessionStorage.setItem('userRole', role);
    setUserRole(role);
  };

  // Logout function
  const handleLogout = () => {
    sessionStorage.removeItem('userRole');
    setUserRole(null);
  };

  return (
    <Router>
      {/* Conditionally render the Navbar only if the user is authenticated */}
      {userRole && <Navbar onLogout={handleLogout} />}
      <Routes>
        {/* Default route - Redirect to home or login based on authentication */}
        <Route
          path="/"
          element={userRole ? <Navigate to="/home" /> : <Navigate to="/login" />}
        />

        {/* Login page */}
        <Route
          path="/login"
          element={userRole ? <Navigate to="/" /> : <LoginPage onLogin={handleLogin} />}
        />

        {/* Home page for authenticated users */}
        <Route
          path="/home"
          element={
            <ProtectedRoute userRole={userRole} allowedRoles={['sales_manager', 'admin']}>
              <HomePage />
            </ProtectedRoute>
          }
        />

        {/* Sales page for Sales Managers */}
        <Route
          path="/sales"
          element={
            <ProtectedRoute userRole={userRole} allowedRoles={['sales_manager']}>
              <SalesPage />
            </ProtectedRoute>
          }
        />

        {/* Admin page - only accessible to admin */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute userRole={userRole} allowedRoles={['admin']}>
              <AdminPage />
            </ProtectedRoute>
          }
        />

        {/* Sales Executives Page - Only accessible to sales managers */}
        <Route
          path="/sales-executives"
          element={
            <ProtectedRoute userRole={userRole} allowedRoles={['sales_manager']}>
              {/* Uncomment if the page exists: <SalesExecutivePage /> */}
            </ProtectedRoute>
          }
        />

        {/* Reports Page - For both sales managers and admin */}
        <Route
          path="/reports"
          element={
            <ProtectedRoute userRole={userRole} allowedRoles={['sales_manager', 'admin']}>
              {/* Uncomment if the page exists: <ReportsPage /> */}
            </ProtectedRoute>
          }
        />

        {/* Not Found page */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Router>
  );
}

export default App;
