import React, { useEffect, Suspense, useState } from 'react';
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import ProtectedRoute from './components/ProtectedRoute';
import Toaster from './components/Toaster';
import HelpTour from './components/HelpTour';
import Loading from './components/Loading';
import { useAuth } from './contexts/AuthContext';
import useToasts from './hooks/useToasts';
import * as serviceWorkerRegistration from './services/serviceWorkerRegistration';
import './App.css';

// Lazy-loaded pages
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const SalesPage = React.lazy(() => import('./pages/SalesPage'));
const SaleDetailsPage = React.lazy(() => import('./pages/SaleDetailsPage'));
const AuditTrailPage = React.lazy(() => import('./pages/AuditTrailPage'));
const SalesPerformancePage = React.lazy(() => import('./pages/SalesPerformancePage'));
const QueriesPage = React.lazy(() => import('./pages/QueriesPage'));
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
  { path: '/sales-performance', component: SalesPerformancePage, allowedRoles: [1, 2, 3, 4] },
  { path: '/queries', component: QueriesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-sales-executives', component: ManageSalesExecutivesPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-paypoints', component: ManagePaypointsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-targets', component: ManageSalesTargetsPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/manage-banks', component: ManageBanksPage, allowedRoles: [1, 2, 3, 4] },
  { path: '/investigations', component: FlaggedInvestigationsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-products', component: ManageProductsPage, allowedRoles: [1, 2, 3] },
  { path: '/manage-branches', component: ManageGenBranchesPage, allowedRoles: [1, 2, 3] },
  { path: '/audit-trail', component: AuditTrailPage, allowedRoles: [2, 3] },
  { path: '/manage-users', component: ManageUsersPage, allowedRoles: [2, 3] },
  { path: '/manage-roles', component: ManageRolesPage, allowedRoles: [3] },
  { path: '/logs', component: LogsPage, allowedRoles: [3] },
  { path: '/retention-policy', component: RetentionPolicyPage, allowedRoles: [3] },
  { path: '/manage-users-sessions', component: ManageSessionsPage, allowedRoles: [3] },
];

function App() {
  const { state, logout } = useAuth();
  const { role } = state;
  const { toasts, showToast, removeToast } = useToasts();
  const [showHelpTour, setShowHelpTour] = useState(false);
  const [waitingServiceWorker, setWaitingServiceWorker] = useState(null);
  const navigate = useNavigate();

  // Show help tour if it's the user's first time
  useEffect(() => {
    if (!localStorage.getItem('helpTourShown')) {
      setShowHelpTour(true);
      localStorage.setItem('helpTourShown', 'true');
    }
  }, []);

  // Handle navigation based on user role
  useEffect(() => {
    const redirectUser = () => {
      if (role) {
        const redirectPath = role.id === userRoles.ADMIN ? '/manage-users' : '/sales';
        // Only navigate if the user is on the login page
        if (window.location.pathname === '/login') {
          navigate(redirectPath);
        }
      }
    };
    redirectUser();
  }, [role, navigate]);

  // Register service worker and listen for updates
  useEffect(() => {
    const registerServiceWorker = async () => {
      try {
        await serviceWorkerRegistration.register({
          onUpdate: (registration) => {
            showToast('update', 'A new version is available. Click here to update.', 'Update Available');
            setWaitingServiceWorker(registration.waiting);
          },
        });
      } catch (error) {
        console.error('Service worker registration failed:', error);
      }
    };

    registerServiceWorker();
  }, [showToast]);

  // Handle service worker update
  const updateServiceWorker = () => {
    if (waitingServiceWorker) {
      waitingServiceWorker.postMessage({ type: 'SKIP_WAITING' });
      waitingServiceWorker.addEventListener('statechange', (event) => {
        if (event.target.state === 'activated') {
          window.location.reload();
        }
      });
    }
  };

  return (
    <div>
      {role?.id && <Navbar onLogout={logout} showToast={showToast} />}
      {role?.id && <Sidebar />}
      {showHelpTour && <HelpTour />}

      <div className="content" style={{ marginLeft: role?.id ? '250px' : '0', transition: 'all 0.3s ease-in-out' }}>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/login" element={<LoginPage showToast={showToast} />} />
            {appRoutes.map((route) => (
              <Route
                key={route.path}
                path={route.path}
                element={
                  <ProtectedRoute allowedRoles={route.allowedRoles} userRole={role?.id} showToast={showToast}>
                    <route.component showToast={showToast} />
                  </ProtectedRoute>
                }
              />
            ))}
            <Route path="*" element={<Navigate to={role?.id ? "/sales" : "/login"} />} />
          </Routes>
        </Suspense>
      </div>

      <Toaster
        toasts={toasts}
        removeToast={removeToast}
        updateServiceWorker={updateServiceWorker}
      />
    </div>
  );
}

export default App;
