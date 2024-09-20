import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import useToasts from '../hooks/useToasts'; // Import useToasts hook

const ProtectedRoute = ({ children, allowedRoles, userRole }) => {
  const location = useLocation();
  const { showToast } = useToasts(); // Initialize useToasts

  // Check if userRole is defined and valid
  if (!userRole || !allowedRoles.includes(userRole)) {
    showToast('danger', 'Unauthorized access', 'Access Denied');
    return <Navigate to="/login" state={{ from: location }} />;
  }

  // Return children if the user has access
  return children || null; // Return null if no children are passed
};

export default ProtectedRoute;
