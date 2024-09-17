import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import authService from '../services/authService';

const useAuthHook = () => {
  const { state, login, logout } = useAuth();
  const { role, isAuthenticated, loading, error } = state;
  const navigate = useNavigate();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if the user is already logged in
        const loggedIn = await authService.isLoggedIn();
        if (loggedIn) {
          // If logged in, retrieve the user role from localStorage or context
          let userRole = role;
          if (!userRole) {
            userRole = JSON.parse(localStorage.getItem('userRole'));
          }

          // Determine the redirection path based on user role
          if (userRole && userRole.id) {
            const redirectPath = userRole.id === 3 ? '/manage-users' : '/sales';
            navigate(redirectPath);
          }
        } else {
          // If not logged in, redirect to login page
          navigate('/login');
        }
      } catch {
        // Handle any error by redirecting to login
        navigate('/login');
      } finally {
        setIsInitialized(true);
      }
    };

    initializeAuth();
  }, [navigate, role]);

  useEffect(() => {
    // After initialization, manage redirection based on authentication and role
    if (isInitialized) {
      if (isAuthenticated && role?.id) {
        const redirectPath = role.id === 3 ? '/manage-users' : '/sales';
        navigate(redirectPath);
      } else {
        navigate('/login');
      }
    }
  }, [isAuthenticated, role, navigate, isInitialized]);

  return {
    role,
    isLoading: loading,
    error,
    handleLogin: login,
    handleLogout: logout,
  };
};

export default useAuthHook;
