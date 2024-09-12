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
import { AccessProvider, useAccessContext } from './context/AccessProvider';

function App() {
  const [role, setRole] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [toasts, setToasts] = useState([]);  // Global toast state
  const [loading, setLoading] = useState(false);  // Loading state for login
  const navigate = useNavigate();
  const { fetchUserAccess } = useAccessContext();  // Access context hook

  // Fetch role name based on roleId from localStorage
  const fetchRoleName = useCallback(() => {
    try {
      setLoading(true);
      const storedRoleName = localStorage.getItem('userRoleName');  // Retrieve role name from localStorage
      if (storedRoleName) {
        setRoleName(storedRoleName);
        // console.log('Role Name:', storedRoleName);  // Log role name
      }
    } catch (error) {
      console.error('Error fetching role name:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // On mount, check if the user is already logged in by checking localStorage
  useEffect(() => {
    const savedRole = localStorage.getItem('userRoleID');
    if (savedRole && authService.isLoggedIn()) { // Check if the user is logged in and token is valid
      setRole(savedRole);
      fetchRoleName(savedRole);  // Fetch role name when user logs in
      fetchUserAccess(savedRole); // Fetch access rules for the user role
    } else {
      setRole(null); // Clear role if not logged in
      localStorage.removeItem('userRoleID');  // Ensure that we clear invalid sessions
      navigate('/login');  // Redirect to login page if not logged in
    }
  }, [fetchRoleName, fetchUserAccess, navigate]);

  // Function to show toast messages without duplicates
  const showToast = useCallback((variant, message, heading) => {
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
  }, [toasts]);

  // Function to remove toast
  const removeToast = useCallback((id) => {
    setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));
  }, []);

  const handleLogin = useCallback(async (userRole) => {
    setRole(userRole);
    localStorage.setItem('userRoleID', userRole);  // Store role in localStorage after login
    await fetchRoleName(userRole);  // Fetch role name on login
    await fetchUserAccess(userRole);  // Fetch access rules on login

    // Use navigate for redirect instead of window.location.href
    navigate(userRole === 3 ? '/manage-users' : '/sales');
    // console.log('Logged in with Role:', userRole);  // Log user role
  }, [fetchRoleName, fetchUserAccess, navigate]);

  const handleLogout = useCallback(async () => {
    try {
      setLoading(true);  // Start loading during logout
      await authService.logout();  // Call the logout function to clear tokens
      setRole(null);  // Set role to null to hide Navbar and Sidebar
      setRoleName('');  // Clear the role name
      showToast('success', 'Logout successful', 'Goodbye');
      navigate('/login');  // Redirect to login page after successful logout
    } catch (error) {
      showToast('danger', error.message || 'Logout failed', 'Error');
    } finally {
      setLoading(false);  // Stop loading after logout
    }
  }, [showToast, navigate]);

  // Memoized role check for ProtectedRoute to avoid recalculating
  const isAllowed = useMemo(() => (allowedRoles, userRole) => allowedRoles.includes(parseInt(userRole)), []);

  return (
    <div>
      {role && <Navbar onLogout={handleLogout} roleName={roleName} />}
      {role && <Sidebar />}

      <div style={{ marginLeft: role ? '250px' : '0' }}>
        {loading ? (
          <div>Loading...</div>
        ) : (
          <Routes>
            <Route path="/login" element={<LoginPage onLogin={handleLogin} showToast={showToast} />} />

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

export default function RootApp() {
  return (
    <AccessProvider>
      <App />
    </AccessProvider>
  );
}
