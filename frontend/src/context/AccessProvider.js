import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import api from '../services/api';

// Create the AccessContext
const AccessContext = createContext();

// AccessProvider component to provide the context to its children
export const AccessProvider = ({ children }) => {
  const [userAccess, setUserAccess] = useState(null);  // Initially, no access is fetched
  const [loading, setLoading] = useState(false);       // Loading state for fetching access
  const [error, setError] = useState(null);            // Error state to capture any errors

  // Function to get roleId from authService
  const getRoleId = () => {
    const user = JSON.parse(localStorage.getItem('user'));
    // console.log('User from localStorage:', user);  // Log user data
    return user ? user.role.id : null;   // Return the roleId if user exists
  };

  const fetchUserAccess = useCallback(async () => {
    const roleId = getRoleId(); // Get roleId from authService or localStorage
    if (!roleId) {
      setError('No role found');
      // console.error('No role found');  // Log no role found
      return;
    }

    setLoading(true);  // Start loading before fetching access
    setError(null);    // Reset error state
    try {
      const response = await api.get(`/access/${roleId}`);
      setUserAccess(response.data); // Assuming the response contains access rules
      // console.log('Fetched access rules:', response.data);  // Log access rules
    } catch (error) {
      // console.error('Error fetching access rules:', error);
      setError('Failed to fetch access rules');
    } finally {
      setLoading(false); // Stop loading after fetching access
    }
  }, []);  // useCallback to ensure fetchUserAccess is stable

  // Memoize the context value to prevent unnecessary re-renders
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

// Custom hook to use the AccessContext
export const useAccessContext = () => {
  const context = useContext(AccessContext);

  if (!context) {
    throw new Error('useAccessContext must be used within an AccessProvider');
  }

  return context;
};
