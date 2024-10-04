import React, { useEffect, Suspense, useMemo, useCallback } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import HelpTour from './components/HelpTour';
import Loading from './components/Loading';
import { useAuth } from './contexts/AuthContext';
import useToasts from './hooks/useToasts';
import { useServiceWorker } from './hooks/useServiceWorker'; // Custom hook for service worker registration
import { useLocalStorage } from './hooks/useLocalStorage'; // Custom hook for localStorage interaction
import './App.css';
import authService from './services/authService';
import throttle from 'lodash.throttle'; // Import lodash.throttle

// Lazy-loaded pages
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const SalesPage = React.lazy(() => import('./pages/SalesPage'));
const SaleDetailsPage = React.lazy(() => import('./pages/SaleDetailsPage'));
const AuditTrailPage = React.lazy(() => import('./pages/AuditTrailPage'));
const SalesPerformancePage = React.lazy(() => import('./pages/SalesPerformancePage'));
const SalesTargetPage = React.lazy(() => import('./pages/SalesTargetPage'));
const QueriesPage = React.lazy(() => import('./pages/QueriesPage'));
const ReportsPage = React.lazy(() => import('./pages/ReportsPage'));
const FlaggedInvestigationsPage = React.lazy(() => import('./pages/FlaggedInvestigationsPage'));
const ManageRolesPage = React.lazy(() => import('./pages/ManageRolesPage'));
const LogsPage = React.lazy(() => import('./pages/LogsPage'));
const RetentionPolicyPage = React.lazy(() => import('./pages/RetentionPolicyPage'));
const ManageUsersPage = React.lazy(() => import('./pages/ManageUsersPage'));
const ManageSessionsPage = React.lazy(() => import('./pages/ManageSessionsPage'));
const ManageProductsPage = React.lazy(() => import('./pages/ManageProductsPage'));
const ManagePaypointsPage = React.lazy(() => import('./pages/ManagePaypointsPage'));
const ManageSalesExecutivesPage = React.lazy(() => import('./pages/ManageSalesExec'));
const ManageGenBranchesPage = React.lazy(() => import('./pages/ManageGenBranchesPage'));
const ManageSalesTargetsPage = React.lazy(() => import('./pages/ManageSalesTargetsPage'));
const ManageBanksPage = React.lazy(() => import('./pages/ManageBanksPage'));

// Define user roles
const userRoles = {
  BACK_OFFICE: 1,
  MANAGER: 2,
  ADMIN: 3,
  SALES_MANAGER: 4,
};

// Define the routes with their respective allowed roles
const appRoutes = [
  { path: '/sales', component: SalesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/sales/:saleId', component: SaleDetailsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/sales-targets', component: SalesTargetPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/sales-performance', component: SalesPerformancePage, allowedRoles: [1, 2, 3, 4] },
  { path: '/queries', component: QueriesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-sales-executives', component: ManageSalesExecutivesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-paypoints', component: ManagePaypointsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-targets', component: ManageSalesTargetsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/investigations', component: FlaggedInvestigationsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-banks', component: ManageBanksPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/reports', component: ReportsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-products', component: ManageProductsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-branches', component: ManageGenBranchesPage, allowedRoles: [1, 2, 3] },
  { path: '/audit-trail', component: AuditTrailPage, allowedRoles: [2, 3] },
  { path: '/manage-users', component: ManageUsersPage, allowedRoles: [2, 3] },
  { path: '/manage-roles', component: ManageRolesPage, allowedRoles: [3] },
  { path: '/logs', component: LogsPage, allowedRoles: [3] },
  { path: '/retention-policy', component: RetentionPolicyPage, allowedRoles: [3] },
  { path: '/manage-users-sessions', component: ManageSessionsPage, allowedRoles: [3] },
];

// Custom hook to handle login and redirection logic with throttled navigation
// Custom hook to handle login and redirection logic with throttled navigation
function useLoginRedirect(role, navigate, setShowHelpTour) {
  const throttledNavigate = useCallback(
    (path) => {
      const throttledFn = throttle(() => navigate(path), 2000); // Define throttled inside the callback
      throttledFn(); // Call the throttled function
    },
    [navigate] // Properly track navigate as a dependency
  );

  useEffect(() => {
    const checkLogin = async () => {
      const isLoggedIn = await authService.isLoggedIn();

      if (!isLoggedIn) {
        throttledNavigate('/login'); // Use throttled navigation
      } else if (role) {
        // Set a timeout to auto-hide the help tour after 2 minutes
        const timer = setTimeout(() => setShowHelpTour(false), 120000);

        // Determine redirection path
        const redirectPath = role.id === userRoles.ADMIN ? '/manage-users' : '/sales';

        // Only navigate if user is on the login page
        if (window.location.pathname === '/login') {
          throttledNavigate(redirectPath); // Use throttled navigation
        }

        // Cleanup the timer when component unmounts
        return () => clearTimeout(timer);
      }
    };

    checkLogin();
  }, [role, throttledNavigate, setShowHelpTour]);
}

// Memoized Navbar and Sidebar to prevent unnecessary re-renders
const MemoizedNavbar = React.memo(({ role, logout, showToast }) => (
  role?.id && <Navbar onLogout={logout} showToast={showToast} />
));

const MemoizedSidebar = React.memo(({ role }) => (
  role?.id && <Sidebar />
));

function App() {
  const { state, logout } = useAuth();
  const { role } = state;
  const { toasts, showToast, removeToast } = useToasts();
  const { updateServiceWorker } = useServiceWorker(showToast); // Custom hook for service worker
  const [showHelpTour, setShowHelpTour] = useLocalStorage('helpTourShown', false); // Custom hook for help tour state
  const navigate = useNavigate();

  // Handle login and redirection with throttled navigation
  useLoginRedirect(role, navigate, setShowHelpTour);

  // Memoized app routes
  const memoizedRoutes = useMemo(() => {
    return appRoutes.map((route) => (
      <Route
        key={route.path}
        path={route.path}
        element={
          <ProtectedRoute allowedRoles={route.allowedRoles} userRole={role?.id} showToast={showToast}>
            <route.component showToast={showToast} />
          </ProtectedRoute>
        }
      />
    ));
  }, [role?.id, showToast]);

  return (
    <div>
      <MemoizedNavbar role={role} logout={logout} showToast={showToast} />
      <MemoizedSidebar role={role} />
      {showHelpTour && <HelpTour />}

      <div className={`content ${role?.id ? 'withSidebar' : 'noSidebar'}`}>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/login" element={<LoginPage showToast={showToast} />} />
            {memoizedRoutes}
            <Route path="*" element={<Navigate to={role?.id ? '/sales' : '/login'} />} />
          </Routes>
        </Suspense>
      </div>

      <Toaster toasts={toasts} removeToast={removeToast} updateServiceWorker={updateServiceWorker} />
    </div>
  );
}

export default App;
