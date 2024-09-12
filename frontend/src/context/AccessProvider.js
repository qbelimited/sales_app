import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import api from '../services/api';

// Create the AccessContext
const AccessContext = createContext();

// AccessProvider component to provide the context to its children
export const AccessProvider = ({ children }) => {
  const [userAccess, setUserAccess] = useState(null);  // State for access rules
  const [loading, setLoading] = useState(false);       // Loading state for API calls
  const [error, setError] = useState(null);            // Error state for errors

  // Utility function to get roleId from localStorage
  const getRoleId = useMemo(() => {
    try {
      const user = JSON.parse(localStorage.getItem('user'));
      return user?.role?.id || null; // Safely extract roleId
    } catch (e) {
      console.error('Failed to get role from localStorage:', e);
      return null;
    }
  }, []);  // Empty dependency array to ensure this runs only once

  // Function to fetch user access rules based on roleId
  const fetchUserAccess = useCallback(async () => {
    const roleId = getRoleId;

    if (!roleId) {
      setError('User role not found. Unable to fetch access rules.');
      return; // Exit early if roleId is missing
    }

    setLoading(true);  // Set loading state to true before the request
    setError(null);    // Reset any previous errors

    try {
      const response = await api.get(`/access/${roleId}`);
      setUserAccess(response.data); // Assume response.data contains access rules
    } catch (error) {
      setError('Failed to fetch access rules. Please try again later.');
      console.error('Error fetching access rules:', error);
    } finally {
      setLoading(false); // Ensure loading state is stopped
    }
  }, [getRoleId]);  // Add getRoleId as a dependency

  // Memoize the context value to avoid unnecessary re-renders
  const contextValue = useMemo(() => ({
    userAccess,
    fetchUserAccess,
    loading,
    error,
  }), [userAccess, fetchUserAccess, loading, error]);

  return (
    <AccessContext.Provider value={contextValue}>
      {children}
    </AccessContext.Provider>
  );
};

// Custom hook to consume the AccessContext
export const useAccessContext = () => {
  const context = useContext(AccessContext);

  if (!context) {
    throw new Error('useAccessContext must be used within an AccessProvider');
  }

  return context;
};
