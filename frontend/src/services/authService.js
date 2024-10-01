// authService.js
import { toast } from 'react-toastify';
import api from './api';

const authService = {
  login: async (credentials) => {
    // Validate credentials
    if (!credentials.email || !credentials.password) {
      console.error('Invalid login credentials:', credentials);
      throw new Error('Invalid login credentials. Email and password are required.');
    }

    try {
      const response = await api.post('/auth/login', credentials);

      // Check for access and refresh tokens
      const { access_token, refresh_token, user, expiry } = response.data || {};
      if (access_token && refresh_token) {
        authService.storeSession(access_token, refresh_token, user, expiry);
        authService.fetchAndStoreUserDetails();
        toast.success('Login successful');
        return response.data;  // Return user data and tokens
      } else {
        throw new Error('Missing access or refresh token in response.');
      }
    } catch (error) {
      authService.handleAuthError(error);
      throw error; // Propagate error
    }
  },

  logout: async (sessionId = null, expiredSession = false) => {
    try {
      const accessToken = authService.getAccessToken();
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        toast.error('Already logged out.');
        return;
      }

      if (sessionId && user) {
        await api.delete(`/users/${user.id}/sessions/${sessionId}`);
      }

      await api.post('/auth/logout', { refresh_token: refreshToken }, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      authService.clearSession();
      toast[expiredSession ? 'error' : 'success'](expiredSession ? 'Session expired. You have been logged out.' : 'Logout successful');
    } catch (error) {
      authService.clearSession();
      toast.error('Logout failed');
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token available.');

      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token, expiry } = response.data || {};

      if (access_token) {
        authService.storeSession(access_token, refreshToken, JSON.parse(localStorage.getItem('user')), expiry);
        toast.success('Session refreshed successfully');
        return access_token;
      } else {
        throw new Error('Missing access token in response.');
      }
    } catch (error) {
      authService.handleSessionExpired();
      throw error;
    }
  },

  isLoggedIn: async (navigate) => {
    const token = authService.getAccessToken();
    const expiry = localStorage.getItem('expiry');

    if (token && expiry) {
        const timeLeft = expiry - Date.now();
        const bufferTime = 5 * 60 * 1000; // 5 minutes buffer

        if (timeLeft > bufferTime) {
            return true; // Token is still valid
        } else {
            // Token is about to expire, refresh it
            try {
                await authService.refreshToken();
                return true; // Successfully refreshed token
            } catch (error) {
                authService.handleSessionExpired(navigate);
            }
        }
    } else {
        authService.handleSessionExpired(navigate);
    }
    return false;
  },

  getAccessToken: () => localStorage.getItem('access_token') || null,

  handleSessionExpired: (navigate) => {
    authService.clearSession();
    toast.error('Your session has expired. Please log in again.');
    // Use the passed navigate function to redirect to the login page
    navigate('/login');
  },

  storeSession: (access_token, refresh_token, user, expiry) => {
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('expiry', Date.now() + expiry * 1000);
  },

  clearSession: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('expiry');
  },

  fetchAndStoreUserDetails: async () => {
    try {
      const userAgent = navigator.userAgent;
      const ipAddress = await authService.getIpAddress();
      localStorage.setItem('userAgent', userAgent);
      localStorage.setItem('ipAddress', ipAddress);
    } catch (error) {
      console.error('Failed to fetch user details:', error);
    }
  },

  getIpAddress: async () => {
    try {
      const response = await fetch('https://api.ipify.org?format=json');
      const data = await response.json();
      return data.ip;
    } catch (error) {
      console.error('Failed to fetch IP address:', error);
      return 'Unknown IP';
    }
  },

  handleAuthError: (error) => {
    console.error('Auth error:', error);
    // Handle specific error cases if needed
    if (error.response) {
      console.error('Server error response:', error.response);
      toast.error(error.response.data?.message || 'Login failed. Please check your credentials.');
    } else if (error.request) {
      console.error('No response received:', error.request);
      toast.error('Login failed. No response from server.');
    } else {
      toast.error(`Login failed: ${error.message}`);
    }
  },
};

export default authService;
