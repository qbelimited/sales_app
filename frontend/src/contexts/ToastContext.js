import React, { createContext, useContext, useMemo } from 'react';
import PropTypes from 'prop-types'; // For prop validation
import useToasts from '../hooks/useToasts';

// Create the ToastContext
const ToastContext = createContext();

// Create the ToastProvider to wrap your app and provide toast functions
export const ToastProvider = ({ children }) => {
  const { showToast, toasts, removeToast } = useToasts();

  // Memoize the context value to avoid unnecessary re-renders
  const contextValue = useMemo(
    () => ({ showToast, toasts, removeToast }),
    [showToast, toasts, removeToast]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
    </ToastContext.Provider>
  );
};

// Custom hook to use the ToastContext
export const useToastContext = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToastContext must be used within a ToastProvider');
  }
  return context;
};

// Add prop validation for children
ToastProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ToastContext;
