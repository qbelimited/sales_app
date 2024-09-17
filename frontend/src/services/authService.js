// authService.js
import { toast } from 'react-toastify';
import api from './api';

const authService = {
  login: async (credentials) => {

    // Ensure the credentials object contains both email and password
    if (!credentials.email || !credentials.password) {
      console.error('Invalid login credentials:', credentials);
      throw new Error('Invalid login credentials. Email and password are required.');
    }

    try {
      const response = await api.post('/auth/login', credentials);

      if (response?.data) {
        const { access_token, refresh_token, user, expiry } = response.data;

        if (access_token && refresh_token) {
          authService.storeSession(access_token, refresh_token, user, expiry);

          // Fetch IP and User Agent without blocking the login process
          authService.fetchAndStoreUserDetails();

          toast.success('Login successful');
          return response.data;  // Return user data and tokens
        } else {
          console.error('Missing access or refresh token in response.');
          throw new Error('Missing access or refresh token in response.');
        }
      } else {
        console.error('Invalid response from server.');
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      // Log the entire error object for more details
      console.error('Login failed:', error);
      if (error.response) {
        // Server responded with a status code outside of the 2xx range
        console.error('Server error response:', error.response);
        if (error.response.data && error.response.data.message) {
          toast.error(`Login failed: ${error.response.data.message}`);
        } else {
          toast.error('Login failed. Please check your credentials or try again later.');
        }
      } else if (error.request) {
        // Request was made but no response received
        console.error('No response received:', error.request);
        toast.error('Login failed. No response from server.');
      } else {
        // Something else caused the error
        toast.error(`Login failed: ${error.message}`);
      }
      throw error; // Ensure the error is propagated
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
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });

      authService.clearSession();

      if (expiredSession) {
        toast.error('Session expired. You have been logged out.');
      } else {
        toast.success('Logout successful');
      }
    } catch (error) {
      console.error('Logout failed:', error);
      authService.clearSession();
      toast.error('Logout failed');
    }
  },

  refreshToken: async () => {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token available.');

        const response = await api.post('/auth/refresh', { refresh_token: refreshToken });

        if (response?.data) {
            const { access_token, expiry } = response.data;

            if (access_token) {
                // Store the new access token and update the expiry
                authService.storeSession(access_token, refreshToken, JSON.parse(localStorage.getItem('user')), expiry);
                toast.success('Session refreshed successfully');
                return access_token;
            } else {
                console.error('Missing access token in response.');
                throw new Error('Missing access token in response.');
            }
        } else {
            console.error('Invalid response from server.');
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
        authService.handleSessionExpired();
        throw error;
    }
  },

  isLoggedIn: async () => {
    const token = authService.getAccessToken();
    const expiry = localStorage.getItem('expiry');

    if (token && expiry) {
      if (Date.now() < expiry) {
        return true;
      } else {
        try {
          await authService.refreshToken();
          return true;
        } catch (error) {
          authService.handleSessionExpired();
        }
      }
    } else {
      authService.handleSessionExpired();
    }
    return false;
  },

  getAccessToken: () => {
    return localStorage.getItem('access_token') || null;
  },

  handleSessionExpired: () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
        authService.logout(null, true);
    }
    toast.error('You are not logged in. Please log in.');
  },

  storeSession: (access_token, refresh_token, user, expiry) => {
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('userRole', JSON.stringify(user.role));
    localStorage.setItem('userRoleID', JSON.stringify(user.role.id));
    localStorage.setItem('expiry', Date.now() + expiry * 1000);
  },

  clearSession: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userRoleID');
    localStorage.removeItem('expiry');
    localStorage.removeItem('userAgent');
    localStorage.removeItem('ipAddress');
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
};

export default authService;
