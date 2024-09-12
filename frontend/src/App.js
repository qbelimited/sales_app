import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import LoginPage from './pages/LoginPage';
import SalesPage from './pages/SalesPage';
import AuditTrailPage from './pages/AuditTrailPage';
import ManageAccessPage from './pages/ManageAccessPage';
import LogsPage from './pages/LogsPage';
import RetentionPolicyPage from './pages/RetentionPolicyPage';
import ManageUsersPage from './pages/ManageUsersPage';
import ManageProductsPage from './pages/ManageProductsPage';
import ManageBanksPage from './pages/ManageBanksPage';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import authService from './services/authService';

// Main Application Component
function App() {
  const [role, setRole] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [toasts, setToasts] = useState([]);  // Global toast state
  const [loading, setLoading] = useState(false);  // Loading state for login
  const navigate = useNavigate();

  // Fetch role name based on roleId from localStorage
  const fetchRoleName = useCallback(() => {
    try {
      const storedRoleName = localStorage.getItem('userRoleName');  // Retrieve role name from localStorage
      if (storedRoleName) {
        setRoleName(storedRoleName);
      }
    } catch (error) {
      console.error('Error fetching role name:', error);
    }
  }, []);

  // On mount, check if the user is logged in and fetch user access
  useEffect(() => {
    const savedRole = localStorage.getItem('userRoleID');
    const isLoggedIn = authService.isLoggedIn();

    if (savedRole && isLoggedIn) {
      setRole(savedRole);
      fetchRoleName();  // Ensure this function is stable
    } else {
      setRole(null);
      localStorage.removeItem('userRoleID');
      navigate('/login');  // Make sure this is not causing continuous navigation
    }
  }, [fetchRoleName, navigate]);  // Stable dependencies only

  // Function to show toast messages without duplicates
  const showToast = useCallback((variant, message, heading) => {
    const newToast = { id: Date.now(), variant, message, heading, time: new Date() };
    const isDuplicate = toasts.some(toast => toast.message === message && toast.variant === variant);

    if (!isDuplicate) {
      setToasts((prevToasts) => [...prevToasts, newToast]);
    }
  }, [toasts]);

  // Function to remove toast
  const removeToast = useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));
  }, []);

  // Handle login
  const handleLogin = useCallback(async (userRole) => {
    setRole(userRole);
    localStorage.setItem('userRoleID', userRole);
    await fetchRoleName();  // Fetch role name

    navigate(userRole === 3 ? '/manage-users' : '/sales');
  }, [fetchRoleName, navigate]);

  // Handle logout
  const handleLogout = useCallback(async () => {
    try {
      setLoading(true);
      await authService.logout();
      setRole(null);
      setRoleName('');
      showToast('success', 'Logout successful', 'Goodbye');
      navigate('/login');
    } catch (error) {
      showToast('danger', error.message || 'Logout failed', 'Error');
    } finally {
      setLoading(false);
    }
  }, [showToast, navigate]);

  // Memoized role check for ProtectedRoute
  const isAllowed = useMemo(() => (allowedRoles, userRole) => allowedRoles.includes(parseInt(userRole)), []);

  return (
    <div>
      {/* Conditionally render Navbar and Sidebar only if the user is logged in */}
      {role && <Navbar onLogout={handleLogout} roleName={roleName} />}
      {role && <Sidebar />}

      <div style={{ marginLeft: role ? '250px' : '0' }}>
        {loading ? (
          <div>Loading...</div>
        ) : (
          <Routes>
            {/* Redirect to /sales or /manage-users if logged in, otherwise show login */}
            <Route
              path="/login"
              element={
                role ? (
                  <Navigate to={role === '3' ? '/manage-users' : '/sales'} replace />
                ) : (
                  <LoginPage onLogin={handleLogin} showToast={showToast} />
                )
              }
            />
            <Route
              path="/sales"
              element={
                <ProtectedRoute allowedRoles={[1, 3, 4]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <SalesPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-trail"
              element={
                <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <AuditTrailPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-access"
              element={
                <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <ManageAccessPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/logs"
              element={
                <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <LogsPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/retention-policy"
              element={
                <ProtectedRoute allowedRoles={[3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <RetentionPolicyPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-users"
              element={
                <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <ManageUsersPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-products"
              element={
                <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <ManageProductsPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-banks"
              element={
                <ProtectedRoute allowedRoles={[2, 3]} userRole={parseInt(role)} isAllowed={isAllowed}>
                  <ManageBanksPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to={role ? "/sales" : "/login"} />} />
          </Routes>
        )}
      </div>

      {/* Global Toaster to show notifications */}
      <Toaster toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default App;
