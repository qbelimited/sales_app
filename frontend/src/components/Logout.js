import React from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';  // Import the authService

const Logout = () => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authService.logout();  // Call the logout function in authService

      // Clear tokens and user information from localStorage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userID');
      localStorage.removeItem('user');

      // Redirect the user to the login page
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <button onClick={handleLogout}>
      Logout
    </button>
  );
};

export default Logout;
