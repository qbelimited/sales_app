import React, { createContext, useContext, useState, useCallback } from 'react';
import authService from '../services/authService'; // Assuming you have an authService for handling API requests

// Create a context for access control
const AccessContext = createContext();

// AccessProvider component to provide the context to its children
export const AccessProvider = ({ children }) => {
  const [userAccess, setUserAccess] = useState({});

  const fetchUserAccess = useCallback(async (roleId) => {
    // Fetch access based on the role ID (role-based access control)
    try {
      const response = await authService.get(`/access/${roleId}`); // Use authService for API calls
      setUserAccess(response.data); // Assuming response contains access rules in data
    } catch (error) {
      console.error('Error fetching access rules:', error);
    }
  }, []); // useCallback to ensure fetchUserAccess is only recreated when dependencies change

  return (
    <AccessContext.Provider value={{ userAccess, fetchUserAccess }}>
      {children}
    </AccessContext.Provider>
  );
};

// Custom hook to use the access context
export const useAccessContext = () => {
  const context = useContext(AccessContext);

  if (!context) {
    throw new Error('useAccessContext must be used within an AccessProvider');
  }

  return context;
};
