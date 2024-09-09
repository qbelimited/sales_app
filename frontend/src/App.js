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

// Function to get the authenticated user role from sessionStorage
const getAuthenticatedUser = () => {
  return sessionStorage.getItem('userRole');
};

// Protected Route Component to guard certain pages based on the user's role
const ProtectedRoute = ({ userRole, allowedRoles, children }) => {
  if (!userRole) {
    console.log('No user role found, redirecting to login');
    return <Navigate to="/login" />;
  }

  if (allowedRoles.includes(userRole)) {
    console.log('User has access to this route:', userRole);
    return children; // Render the protected page
  }

  console.log('User does not have access, redirecting to home');
  return <Navigate to="/home" />;
};

function App() {
  const [userRole, setUserRole] = useState(getAuthenticatedUser());

  // Monitor session storage for changes to user role
  useEffect(() => {
    const role = getAuthenticatedUser();
    if (role !== userRole) {
      setUserRole(role);
    }
  }, [userRole]);

  // Simulate login function to set the user role after login
  const handleLogin = (role) => {
    sessionStorage.setItem('userRole', role);
    setUserRole(role);
  };

  // Logout function to clear the user role from session storage and state
  const handleLogout = () => {
    sessionStorage.removeItem('userRole');  // Clear the stored user role from sessionStorage
    setUserRole(null);  // Clear the user role from state
  };

  return (
    <Router>
      {/* Conditionally render the Navbar only if the user is authenticated */}
      {userRole && <Navbar onLogout={handleLogout} />}
      <Routes>
        {/* Default route - check if the user is logged in and route accordingly */}
        <Route
          path="/"
          element={userRole ? <Navigate to="/home" /> : <Navigate to="/login" />}
        />

        {/* Login page */}
        <Route
          path="/login"
          element={userRole ? <Navigate to="/home" /> : <LoginPage onLogin={handleLogin} />}
        />

        {/* Home page - accessible by authenticated users with the correct role */}
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
