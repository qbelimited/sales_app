// authService.js
import { toast } from 'react-toastify';
import api from './api';

const authService = {
  // Flag to prevent multiple login requests
  isLoggingIn: false,

  login: async (credentials) => {
    // Validate credentials
    if (!credentials.email || !credentials.password) {
      const errorMessage = 'Invalid login credentials. Email and password are required.';
      console.error(errorMessage, credentials);
      toast.error(errorMessage);
      throw new Error(errorMessage);
    }

    // Prevent multiple simultaneous login requests
    if (authService.isLoggingIn) {
      const errorMessage = 'Login request is already in progress. Please wait.';
      console.warn(errorMessage);
      toast.warn(errorMessage);
      return; // Exit if a request is already in progress
    }

    authService.isLoggingIn = true; // Set the flag to true

    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token, refresh_token, user, expiry } = response.data || {};

      // Check if login was successful by validating response
      if (response.status === 200 && access_token && refresh_token) {
        await authService.storeSession(access_token, refresh_token, user, expiry);
        await authService.invalidateExistingSession(user.id); // Invalidate old session
        await authService.fetchAndStoreUserDetails();
        toast.success('Login successful');
        return response.data; // Return user data and tokens
      } else {
        const errorMessage = 'Invalid email or password. Please try again.';
        console.error(errorMessage);
        toast.error(errorMessage);
        throw new Error(errorMessage);
      }
    } catch (error) {
      authService.handleLoginError(error); // Handle login error
      throw error; // Propagate error
    } finally {
      authService.isLoggingIn = false; // Reset the flag
    }
  },

  logout: async () => {
    try {
      const accessToken = authService.getAccessToken();
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        toast.error('Already logged out.');
        return;
      }

      // If user is logged in, perform logout
      if (user) {
        const response = await api.post('/auth/logout', { refresh_token: refreshToken }, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });

        if (response.status === 200) {
          authService.clearSession();
          toast.success('Logout successful');
        } else {
          toast.error('Logout failed. Please try again.');
        }
      }
    } catch (error) {
      authService.clearSession();

      // Handle 404 error gracefully
      if (error.response && error.response.status === 404) {
        toast.error('No active session found. You have been logged out.');
      } else {
        toast.error('Logout failed');
      }
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available/ Incorrect Credentials.');
      }

      // Validate the refresh token by attempting to refresh
      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token, expiry } = response.data || {};

      if (access_token) {
        await authService.storeSession(access_token, refreshToken, authService.getUser(), expiry);
        toast.success('Session refreshed successfully');
        return access_token;
      } else {
        throw new Error('Missing access token in response.');
      }
    } catch (error) {
      authService.handleSessionExpired(); // Handle session expiration
      throw error; // Propagate error
    }
  },

  isLoggedIn: async () => {
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
          authService.handleSessionExpired();
        }
      }
    } else {
      authService.handleSessionExpired();
    }
    return false;
  },

  getAccessToken: () => localStorage.getItem('access_token') || null,

  handleSessionExpired: () => {
    authService.clearSession();
    toast.error('Your session has expired. Please log in again.');
  },

  storeSession: (access_token, refresh_token, user, expiry) => {
    try {
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('expiry', Date.now() + expiry * 1000);
    } catch (error) {
      console.error('Failed to store session:', error);
    }
  },

  clearSession: () => {
    try {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      localStorage.removeItem('expiry');
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
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

  handleLoginError: (error) => {
    // If login fails due to wrong password, do not refresh the session
    if (error.response && error.response.status === 401) {
      toast.error('Invalid email or password. Please try again.'); // Show specific error message
    } else {
      authService.handleAuthError(error);
    }
  },

  // Function to invalidate existing sessions
  invalidateExistingSession: async (userId) => {
    const accessToken = authService.getAccessToken();

    // Check if the access token is valid before making the request
    if (!accessToken) {
      console.error('Cannot invalidate sessions: No valid access token available.');
      return;
    }

    try {
      const existingSessions = await api.get(`/users/${userId}/sessions`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      // Check if the response contains session data
      if (Array.isArray(existingSessions.data)) {
        for (const session of existingSessions.data) {
          if (session.isActive) {
            await authService.logout(session.id); // Logout from the older session
          }
        }
      } else {
        console.error('Unexpected session data structure:', existingSessions.data);
      }
    } catch (error) {
      authService.handleSessionExpired(); // Handle session expiration
      console.error('Failed to invalidate existing session:', error);
      toast.error('Could not invalidate existing session.');
    }
  },

  getUser: () => JSON.parse(localStorage.getItem('user')) || null,
};

export default authService;
