import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, allowedRoles, userRole }) => {
  // If userRole is not provided or invalid, redirect to login page
  if (!userRole) {
    return <Navigate to="/login" replace />;
  }

  // Ensure userRole is an integer and check if it matches the allowed roles
  const parsedUserRole = parseInt(userRole, 10);

  // If the role is not allowed, redirect to the unauthorized page
  if (!allowedRoles.includes(parsedUserRole)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // If the user is authorized, render the child components
  return children;
};

export default ProtectedRoute;
