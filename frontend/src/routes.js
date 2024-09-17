// routes.js
import React from 'react';

// Define the lazy-loaded components and their respective allowed roles
const routes = [
  {
    path: '/sales',
    component: React.lazy(() => import('./pages/SalesPage')),
    allowedRoles: [1, 2, 3, 4], // Use the userRoles constants for better readability
  },
  {
    path: '/sales/:saleId',
    component: React.lazy(() => import('./pages/SaleDetailsPage')),
    allowedRoles: [1, 2, 3, 4],
  },
  {
    path: '/audit-trail',
    component: React.lazy(() => import('./pages/AuditTrailPage')),
    allowedRoles: [2, 3],
  },
  {
    path: '/manage-access',
    component: React.lazy(() => import('./pages/ManageAccessPage')),
    allowedRoles: [3],
  },
  {
    path: '/manage-roles',
    component: React.lazy(() => import('./pages/ManageRolesPage')),
    allowedRoles: [3],
  },
  {
    path: '/logs',
    component: React.lazy(() => import('./pages/LogsPage')),
    allowedRoles: [3],
  },
  {
    path: '/retention-policy',
    component: React.lazy(() => import('./pages/RetentionPolicyPage')),
    allowedRoles: [3],
  },
  {
    path: '/manage-users',
    component: React.lazy(() => import('./pages/ManageUsersPage')),
    allowedRoles: [2, 3],
  },
  {
    path: '/manage-users-sessions',
    component: React.lazy(() => import('./pages/ManageSessionsPage')),
    allowedRoles: [3],
  },
  {
    path: '/manage-products',
    component: React.lazy(() => import('./pages/ManageProductsPage')),
    allowedRoles: [1, 2, 3],
  },
  {
    path: '/manage-banks',
    component: React.lazy(() => import('./pages/ManageBanksPage')),
    allowedRoles: [1, 2, 3],
  },
];

export const userRoles = {
  BACK_OFFICE: 1,
  MANAGER: 2,
  ADMIN: 3,
  SALES_MANAGER: 4,
};

export default routes;
