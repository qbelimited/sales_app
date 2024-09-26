import React, { createContext, useContext, useMemo } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes for prop validation
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
export const useToastContext = () => useContext(ToastContext);

// Add prop validation for children
ToastProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export default ToastContext;
