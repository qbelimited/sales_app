import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, allowedRoles, userRole }) => {
  if (!userRole) {
    // If the user is not logged in, redirect to login
    return <Navigate to="/login" />;
  }

  if (!allowedRoles.includes(userRole)) {
    // If the user doesn't have the required role, redirect to a "Not Authorized" page
    return <Navigate to="/unauthorized" />;
  }

  return children;  // If authorized, render the child components
};

export default ProtectedRoute;
