// AppWrapper.js
import React from 'react';
import useToasts from './hooks/useToasts';
import { UserProvider } from './contexts/UserContext'; // Assuming UserContext exists
import App from './App';

const AppWrapper = () => {
  const { showToast } = useToasts(); // Extract the showToast function from useToasts

  return (
    <UserProvider showToast={showToast}> {/* Pass showToast down through UserProvider */}
      <App /> {/* The main app component */}
    </UserProvider>
  );
};

export default AppWrapper;
