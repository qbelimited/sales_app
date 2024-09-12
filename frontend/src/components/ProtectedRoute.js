import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, allowedRoles, userRole }) => {
  // Check if the user is logged in by validating userRole
  if (!userRole) {
    // If the user is not logged in, redirect to login page
    return <Navigate to="/login" replace />;
  }

  // Ensure userRole is an integer and check if it matches the allowed roles
  const parsedUserRole = parseInt(userRole, 10);

  if (!allowedRoles.includes(parsedUserRole)) {
    // If the user doesn't have the required role, redirect to an unauthorized page
    return <Navigate to="/unauthorized" replace />;
  }

  // If the user is authorized, render the child components
  return children;
};

export default ProtectedRoute;
