import api from './api';
import { toast } from 'react-toastify';

// Helper to get user's IP address
const getUserIpAddress = async () => {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    return data.ip || 'Unknown';
  } catch (error) {
    toast.error('Failed to fetch IP address');
    return 'Unknown';
  }
};

// Helper to get device information
const getDeviceInfo = () => {
  const userAgent = navigator.userAgent || 'Unknown';
  return {
    browser: navigator.appName || 'Unknown',
    platform: navigator.platform || 'Unknown',
    userAgent,
  };
};

// Helper to store session data in localStorage
const storeSession = ({ access_token, refresh_token, user }) => {
  try {
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('userRoleID', user.role.id);
    localStorage.setItem('userRoleName', user.role.name);
  } catch (error) {
    console.error('Failed to store session:', error);
  }
};

// Helper to clear session data from localStorage
const clearSession = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('userRoleID');
  localStorage.removeItem('userRoleName');
};

// Authentication and session management service
const authService = {
  login: async (credentials) => {
    try {
      const { data } = await api.post('/auth/login', credentials);
      const { access_token, refresh_token, user } = data || {};

      if (!access_token || !refresh_token || !user) {
        throw new Error('Login failed: Missing tokens or user data.');
      }

      // Store session and create user session
      storeSession({ access_token, refresh_token, user });

      const ipAddress = await getUserIpAddress();
      const deviceInfo = getDeviceInfo();

      // Create user session
      await api.post(`/users/${user.id}/sessions`, {
        ip_address: ipAddress,
        device_info: deviceInfo,
      }, {
        headers: { 'Authorization': `Bearer ${access_token}` },
      });

      toast.success('Login successful');
      return data;
    } catch (error) {
      toast.error(error.response?.data?.message || 'Login failed. Please check your credentials.');
      return Promise.reject(error);
    }
  },

  logout: async () => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken || !refreshToken) {
        clearSession();
        toast.error('Already logged out.');
        return;
      }

      // End user session and log out
      await api.post('/auth/logout', { refresh_token: refreshToken }, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });

      await api.delete(`/users/${user.id}/sessions`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });

      clearSession();
      toast.success('Logout successful');
    } catch (error) {
      clearSession();
      toast.error('Logout failed.');
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const { data } = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token } = data;

      if (!access_token) {
        throw new Error('Missing access token in refresh response');
      }

      localStorage.setItem('access_token', access_token);

      const user = JSON.parse(localStorage.getItem('user'));

      // Extend session expiration after refreshing the token
      await api.put(`/users/${user.id}/sessions`, {
        expires_at: new Date(Date.now() + 45 * 60 * 1000).toISOString(),
      }, {
        headers: { 'Authorization': `Bearer ${access_token}` },
      });

      return access_token;
    } catch (error) {
      clearSession();
      toast.error('Token refresh failed. Please log in again.');
      return Promise.reject(error);
    }
  },

  getAccessToken: () => localStorage.getItem('access_token'),

  isLoggedIn: async () => {
    const token = authService.getAccessToken();

    if (token && !authService.isTokenExpired(token)) {
      return true;
    }

    if (token && authService.isTokenExpired(token)) {
      try {
        await authService.refreshToken();
        return true;
      } catch (error) {
        authService.logout();
        toast.error('Session expired. Please log in again.');
        return false;
      }
    }

    authService.logout();
    toast.error('You are not logged in.');
    return false;
  },

  isTokenExpired: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));
      return decoded.exp * 1000 < Date.now();
    } catch (error) {
      return true;
    }
  },

  clearSession,
};

export default authService;
