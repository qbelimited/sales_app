import React, { useState, useEffect } from 'react';
import { useNavigate, Routes, Route, Navigate } from 'react-router-dom';

// Ensure correct imports for Navbar, Sidebar, and pages
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';
import SalesPage from '../pages/SalesPage';
import InceptedSalesPage from '../pages/InceptedSalesPage';
import FlaggedInvestigationsPage from '../pages/FlaggedInvestigationsPage';
import QueriesPage from '../pages/QueriesPage';
import ManageBanksPage from '../pages/ManageBanksPage';
import BankBranchManagementPage from '../pages/BankBranchManagementPage';
import SalesExecutiveManagementPage from '../pages/SalesExecutiveManagementPage';
import AuditTrailPage from '../pages/AuditTrailPage';
import LogsPage from '../pages/LogsPage';
import ReportsPage from '../pages/ReportsPage';
import RetentionPolicyPage from '../pages/RetentionPolicyPage';
import ManagePaypointsPage from '../pages/ManagePaypointsPage';
import ManageRolesPage from '../pages/ManageRolesPage';
import ManageUsersPage from '../pages/ManageUsersPage';
import ManageAccessPage from '../pages/ManageAccessPage';
import ManageProductsPage from '../pages/ManageProductsPage';
import ManageBranchesPage from '../pages/ManageBranchesPage';
import Toaster from './Toaster';
import authService from '../services/authService';

// Define role constants
const ROLES = {
  BACK_OFFICE: 1,
  MANAGER: 2,
  ADMIN: 3,
  SALES_MANAGER: 4,
  SUPER_ADMIN: 5,
};

function SidebarComponent() {
  const [role, setRole] = useState(null);
  const [roleName, setRoleName] = useState('');
  const [toasts, setToasts] = useState([]);
  const navigate = useNavigate();

  // Fetch role and roleName from localStorage on mount
  useEffect(() => {
    const savedRole = localStorage.getItem('userRole');
    if (savedRole && authService.isLoggedIn()) {
      setRole(parseInt(savedRole, 10));  // Ensure the role is an integer
      fetchRoleName(parseInt(savedRole, 10));
    } else {
      setRole(null);
      localStorage.removeItem('userRole');
      navigate('/login');
    }
  }, [navigate]);

  const fetchRoleName = (roleId) => {
    const roleNames = {
      [ROLES.BACK_OFFICE]: 'Back Office',
      [ROLES.MANAGER]: 'Manager',
      [ROLES.ADMIN]: 'Admin',
      [ROLES.SALES_MANAGER]: 'Sales Manager',
      [ROLES.SUPER_ADMIN]: 'Super Admin',
    };
    setRoleName(roleNames[roleId] || 'Unknown Role');
  };

  // Toast utility functions
  const showToast = (variant, message, heading) => {
    const newToast = { id: Date.now(), variant, message, heading, time: new Date() };
    const isDuplicate = toasts.some(toast => toast.message === message && toast.variant === variant);
    if (!isDuplicate) setToasts((prevToasts) => [...prevToasts, newToast]);
  };

  const removeToast = (id) => setToasts((prevToasts) => prevToasts.filter((t) => t.id !== id));

  const handleLogin = (userRole) => {
    setRole(userRole);
    localStorage.setItem('userRole', userRole);
    fetchRoleName(userRole);
    navigate(userRole === ROLES.ADMIN ? '/manage-users' : '/sales');
  };

  const handleLogout = () => {
    authService.logout()
      .then(() => {
        setRole(null);
        setRoleName('');
        showToast('success', 'Logout successful', 'Goodbye');
        navigate('/login');
      })
      .catch((error) => {
        showToast('danger', error.message || 'Logout failed', 'Error');
      });
  };

  // Define accessible routes for each role
  const accessibleRoutes = () => {
    switch (role) {
      case ROLES.ADMIN:
      case ROLES.SUPER_ADMIN:
        return (
          <>
            <Route path="/manage-users" element={<ManageUsersPage showToast={showToast} />} />
            <Route path="/manage-roles" element={<ManageRolesPage showToast={showToast} />} />
            <Route path="/manage-access" element={<ManageAccessPage showToast={showToast} />} />
            <Route path="/logs" element={<LogsPage showToast={showToast} />} />
            <Route path="/retention-policy" element={<RetentionPolicyPage showToast={showToast} />} />
          </>
        );
      case ROLES.MANAGER:
      case ROLES.SALES_MANAGER:
        return (
          <>
            <Route path="/sales" element={<SalesPage showToast={showToast} />} />
            <Route path="/incepted-sales" element={<InceptedSalesPage showToast={showToast} />} />
            <Route path="/flagged-investigations" element={<FlaggedInvestigationsPage showToast={showToast} />} />
            <Route path="/queries" element={<QueriesPage showToast={showToast} />} />
            <Route path="/audit-trail" element={<AuditTrailPage showToast={showToast} />} />
            <Route path="/reports" element={<ReportsPage showToast={showToast} />} />
          </>
        );
      case ROLES.BACK_OFFICE:
        return (
          <>
            <Route path="/dashboard" element={<DashboardPage showToast={showToast} />} />
            <Route path="/manage-banks" element={<ManageBanksPage showToast={showToast} />} />
            <Route path="/branches" element={<ManageBranchesPage showToast={showToast} />} />
            <Route path="/products" element={<ManageProductsPage showToast={showToast} />} />
            <Route path="/paypoints" element={<ManagePaypointsPage showToast={showToast} />} />
            <Route path="/sales-executive-management" element={<SalesExecutiveManagementPage showToast={showToast} />} />
            <Route path="/bank-branches/:bankId" element={<BankBranchManagementPage showToast={showToast} />} />
          </>
        );
      default:
        return <Route path="*" element={<Navigate to="/login" />} />;
    }
  };

  return (
    <div>
      {role && <Navbar onLogout={handleLogout} roleName={roleName} />}
      {role && <Sidebar />}
      <div style={{ marginLeft: role ? '250px' : '0' }}>
        <Routes>
          <Route path="/login" element={<LoginPage onLogin={handleLogin} showToast={showToast} />} />
          {accessibleRoutes()}
          <Route path="*" element={<Navigate to={role ? '/dashboard' : '/login'} />} />
        </Routes>
      </div>
      <Toaster toasts={toasts} removeToast={removeToast} />
    </div>
  );
}

export default SidebarComponent;