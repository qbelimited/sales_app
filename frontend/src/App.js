import React, { useEffect, Suspense, useMemo, useState } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import HelpTour from './components/HelpTour';
import Loading from './components/Loading';
import { useAuth } from './contexts/AuthContext';
import useToasts from './hooks/useToasts';
import { useServiceWorker } from './hooks/useServiceWorker';
import { useLocalStorage } from './hooks/useLocalStorage';
import './App.css';
import authService from './services/authService';
import api from './services/api';
import throttle from 'lodash.throttle';
import TourService from './services/tourService';
import { ToastProvider } from './contexts/ToastContext';
import NotificationService from './services/notificationService';
import { useNotification } from './hooks/useNotification';

// Lazy-loaded pages
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const SalesPage = React.lazy(() => import('./pages/SalesPage'));
const SaleDetailsPage = React.lazy(() => import('./pages/SaleDetailsPage'));
const AuditTrailPage = React.lazy(() => import('./pages/AuditTrailPage'));
const SalesPerformancePage = React.lazy(() => import('./pages/SalesPerformancePage'));
const InceptionsPage = React.lazy(() => import('./pages/InceptedSalesPage'));
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
const ManageBanksPage = React.lazy(() => import('./pages/ManageBanksPage'));
const HelpPage = React.lazy(() => import('./pages/HelpPage'));
const HelpStepsPage = React.lazy(() => import('./pages/HelpStepsPage'));
const NotFoundPage = React.lazy(() => import('./pages/NotFoundPage'));

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
  { path: '/inceptions', component: InceptionsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/queries', component: QueriesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-sales-executives', component: ManageSalesExecutivesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-paypoints', component: ManagePaypointsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/investigations', component: FlaggedInvestigationsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-banks', component: ManageBanksPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/help-center', component: HelpPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/help/steps', component: HelpStepsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/reports', component: ReportsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-products', component: ManageProductsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-branches', component: ManageGenBranchesPage, allowedRoles: [1, 2, 3] },
  { path: '/audit-trail', component: AuditTrailPage, allowedRoles: [2, 3] },
  { path: '/manage-users', component: ManageUsersPage, allowedRoles: [2, 3] },
  { path: '/manage-roles', component: ManageRolesPage, allowedRoles: [3] },
  { path: '/logs', component: LogsPage, allowedRoles: [3] },
  { path: '/retention-policy', component: RetentionPolicyPage, allowedRoles: [3] },
  { path: '/manage-users-sessions', component: ManageSessionsPage, allowedRoles: [3] },
  { path: '/not-found', component: NotFoundPage },
];

function useLoginRedirect(role, navigate, setShowHelpTour, setTourStarted, handleTourError, handleApiError) {
  const throttledNavigate = useMemo(() => throttle((path) => navigate(path), 2000), [navigate]);

  useEffect(() => {
    const checkLogin = async () => {
      try {
        const isLoggedIn = await authService.isLoggedIn();
        if (!isLoggedIn) {
          throttledNavigate('/login');
        } else if (role && role.id) {
          const redirectPath = role.id === userRoles.ADMIN ? '/manage-users' : '/sales';
          if (window.location.pathname === '/login') {
            throttledNavigate(redirectPath);
          }

          try {
            const user = authService.getUser();
            if (!user || !user.id) {
              throw new Error('User ID not found');
            }
            const tour = await TourService.getTourStatus(user.id);
            if (tour && !tour.completed) {
              setTourStarted(true);
              setShowHelpTour(true);
            } else {
              setShowHelpTour(false);
            }
          } catch (error) {
            if (error.response?.status === 404) {
              setTourStarted(true);
              setShowHelpTour(true);
            } else {
              console.error('Error fetching tour status:', error);
              handleTourError(error);
            }
          }
        }
      } catch (error) {
        console.error('Failed to check login status:', error);
        handleApiError(error, 'Failed to check login status');
      }
    };

    checkLogin();

    return () => {
      // Cleanup logic (optional)
    };
  }, [role, throttledNavigate, setTourStarted, setShowHelpTour, handleTourError, handleApiError]);
}

// Memoized Navbar and Sidebar to prevent unnecessary re-renders
const MemoizedNavbar = React.memo(({ role, logout, showToast, setShowHelpTour }) => (
  role?.id && <Navbar onLogout={logout} showToast={showToast} setShowHelpTour={setShowHelpTour} />
));

const MemoizedSidebar = React.memo(({ role }) => (
  role?.id && <Sidebar />
));

function App() {
  const { state, logout } = useAuth();
  const { role } = state;
  const { toasts, showToast, removeToast } = useToasts();
  const { updateServiceWorker } = useServiceWorker(showToast);
  const [showHelpTour, setShowHelpTour] = useLocalStorage('helpTourShown', false);
  const [tourStarted, setTourStarted] = useState(false);
  const navigate = useNavigate();
  const { handleTourError, handleApiError } = useNotification();

  // Handle login and redirection with throttled navigation
  useLoginRedirect(role, navigate, setShowHelpTour, setTourStarted, handleTourError, handleApiError);

  // Auto-hide Help Tour after 2 minutes if not clicked
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!showHelpTour) {
        setShowHelpTour(true); // Mark the Help Tour as shown
      }
    }, 120000); // 2 minutes

    return () => clearTimeout(timer);
  }, [showHelpTour, setShowHelpTour]);

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
    <ToastProvider>
      <div>
        <MemoizedNavbar role={role} logout={logout} showToast={showToast} setShowHelpTour={setShowHelpTour} />
        <MemoizedSidebar role={role} />
        {showHelpTour && tourStarted && <HelpTour setShowHelpTour={setShowHelpTour} />}

        <div className={`content ${role?.id ? 'withSidebar' : 'noSidebar'}`}>
          <Suspense fallback={<Loading message="Loading, please wait..." />}>
            <Routes>
              <Route path="/login" element={<LoginPage showToast={showToast} />} />
              {memoizedRoutes}
              <Route path="*" element={<Navigate to={role?.id ? '/sales' : '/login'} />} />
            </Routes>
          </Suspense>
        </div>

        <Toaster toasts={toasts} removeToast={removeToast} updateServiceWorker={updateServiceWorker} />
      </div>
    </ToastProvider>
  );
}

export default App;
