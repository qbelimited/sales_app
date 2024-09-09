import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
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
import BranchManagementPage from './pages/BranchManagementPage';
import Toaster from './components/Toaster';  // Global Toaster component

function App() {
  const [role, setRole] = useState(null);
  const [toasts, setToasts] = useState([]);  // Global toast state

  // On mount, check if the user is already logged in by checking localStorage
  useEffect(() => {
    const savedRole = localStorage.getItem('userRole');
    if (savedRole) {
      setRole(savedRole);
    }
  }, []);  // This will run only once when the component mounts

  // Function to show toast messages
  const showToast = (variant, message, heading) => {
    const newToast = {
      id: Date.now(),
      variant,
      message,
      heading,
      time: new Date(),
    };
    setToasts((prevToasts) => [...prevToasts, newToast]);
  };

  // Function to remove toast
  const removeToast = (id) => {
    setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));
  };

  const handleLogin = (userRole) => {
    setRole(userRole);
    localStorage.setItem('userRole', userRole);  // Store role in localStorage after login
    showToast('success', 'Login successful', 'Welcome');
  };

  const handleLogout = () => {
    setRole(null);
    localStorage.removeItem('userRole');  // Clear userRole from localStorage on logout
    showToast('success', 'Logout successful', 'Goodbye');
  };

  return (
    <Router>
      <div>
        {/* If the user is logged in (role exists), show Navbar and Sidebar */}
        {role && <Navbar onLogout={handleLogout} />}
        {role && <Sidebar />}

        <div style={{ marginLeft: role ? '250px' : '0' }}>
          <Routes>
            {/* Public route */}
            <Route path="/login" element={<LoginPage onLogin={handleLogin} showToast={showToast} />} />

            {/* Protected routes */}
            <Route
              path="/sales"
              element={
                <ProtectedRoute allowedRoles={['user', 'admin']} userRole={role}>
                  <SalesPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-trail"
              element={
                <ProtectedRoute allowedRoles={['manager', 'admin']} userRole={role}>
                  <AuditTrailPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-access"
              element={
                <ProtectedRoute allowedRoles={['admin']} userRole={role}>
                  <ManageAccessPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/logs"
              element={
                <ProtectedRoute allowedRoles={['admin']} userRole={role}>
                  <LogsPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/retention-policy"
              element={
                <ProtectedRoute allowedRoles={['admin']} userRole={role}>
                  <RetentionPolicyPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-users"
              element={
                <ProtectedRoute allowedRoles={['manager', 'admin']} userRole={role}>
                  <ManageUsersPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-products"
              element={
                <ProtectedRoute allowedRoles={['manager', 'admin']} userRole={role}>
                  <ManageProductsPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/banks/:bankId/branches"
              element={
                <ProtectedRoute allowedRoles={['manager', 'admin']} userRole={role}>
                  <BranchManagementPage showToast={showToast} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/manage-banks"
              element={
                <ProtectedRoute allowedRoles={['manager', 'admin']} userRole={role}>
                  <ManageBanksPage showToast={showToast} />
                </ProtectedRoute>
              }
            />

            {/* Redirect any unknown paths */}
            <Route path="*" element={<Navigate to={role ? "/sales" : "/login"} />} />
          </Routes>
        </div>

        {/* Global Toaster to show notifications */}
        <Toaster toasts={toasts} removeToast={removeToast} />
      </div>
    </Router>
  );
}

export default App;
