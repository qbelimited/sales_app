import React, { useState, useEffect } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import SalesPage from './pages/SalesPage';
import SaleDetailsPage from './pages/SaleDetailsPage';
import AuditTrailPage from './pages/AuditTrailPage';
import ManageAccessPage from './pages/ManageAccessPage';
import LogsPage from './pages/LogsPage';
import RetentionPolicyPage from './pages/RetentionPolicyPage';
import ManageUsersPage from './pages/ManageUsersPage';
import ManageSessionsPage from './pages/ManageSessionsPage';
import ManageProductsPage from './pages/ManageProductsPage';
import ManageBanksPage from './pages/ManageBanksPage';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import authService from './services/authService';

function App() {
  const [role, setRole] = useState(null);
  const [toasts, setToasts] = useState([]);  // Global toast state
  const navigate = useNavigate();

  // On mount, check if the user is already logged in by checking localStorage
  useEffect(() => {
    const savedRole = localStorage.getItem('userRole');
    if (savedRole && authService.isLoggedIn()) { // Check if the user is logged in and token is valid
      setRole(savedRole);
    } else {
      setRole(null); // Clear role if not logged in
      localStorage.removeItem('userRole');  // Ensure that we clear invalid sessions
      navigate('/login');  // Redirect to login page if not logged in
    }
  }, [navigate]);  // This will run only once when the component mounts

  // Function to show toast messages without duplicates
  const showToast = (variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };

    // Check if a similar toast already exists (by message and variant)
    const isDuplicate = toasts.some(
      (toast) => toast.message === message && toast.variant === variant
    );

    if (!isDuplicate) {
      setToasts((prevToasts) => [...prevToasts, newToast]);
    }
  };

  // Function to remove toast
  const removeToast = (id) => {
    setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));
  };

  const handleLogin = (userRole) => {
    setRole(userRole);
    localStorage.setItem('userRole', userRole);  // Store role in localStorage after login

    // Use navigate for redirect instead of window.location.href
    navigate(userRole === 3 ? '/manage-users' : '/sales');
  };

  const handleLogout = () => {
    authService.logout()  // Call the logout function to clear tokens
      .then(() => {
        setRole(null);  // Set role to null to hide Navbar and Sidebar
        showToast('success', 'Logout successful', 'Goodbye');
        navigate('/login');  // Redirect to login page after successful logout
      })
      .catch((error) => {
        showToast('danger', error.message || 'Logout failed', 'Error');
      });
  };

  return (
    <div>
      {role && <Navbar onLogout={handleLogout} />}
      {role && <Sidebar />}

      <div style={{ marginLeft: role ? '250px' : '0' }}>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} showToast={showToast} />} />

          <Route
            path="/sales"
            element={
              <ProtectedRoute allowedRoles={[1, 3, 4]} userRole={parseInt(role)}>
                <SalesPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sales/:saleId"
            element={
              <ProtectedRoute allowedRoles={[1, 3, 4]} userRole={parseInt(role)}>
                <SaleDetailsPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/audit-trail"
            element={
              <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)}>
                <AuditTrailPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-access"
            element={
              <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)}>
                <ManageAccessPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/logs"
            element={
              <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)}>
                <LogsPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/retention-policy"
            element={
              <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)}>
                <RetentionPolicyPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-users"
            element={
              <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)}>
                <ManageUsersPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-users-sessions"
            element={
              <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)}>
                <ManageSessionsPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-products"
            element={
              <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)}>
                <ManageProductsPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manage-banks"
            element={
              <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)}>
                <ManageBanksPage showToast={showToast} />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to={role ? "/sales" : "/login"} />} />
        </Routes>
      </div>

      {/* Global Toaster to show notifications */}
      <Toaster toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default App;
