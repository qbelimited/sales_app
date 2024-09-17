import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'; // Correct import

const useAuthHook = () => {
  const { state, login, logout } = useAuth(); // Use useAuth here
  const { role, isAuthenticated, loading, error } = state;
  const navigate = useNavigate();

  useEffect(() => {
    // Navigate to the appropriate path after login or logout
    if (isAuthenticated && role?.id) {
      const redirectPath = role.id === 3 ? '/manage-users' : '/sales';
      navigate(redirectPath);
    } else {
      navigate('/login');
    }
  }, [isAuthenticated, role, navigate]);

  return {
    role,
    isLoading: loading,
    error,
    handleLogin: login,
    handleLogout: logout,
  };
};

export default useAuthHook; // Export as useAuthHook to avoid name conflict
