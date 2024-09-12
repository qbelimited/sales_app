import api from './api';
import { toast } from 'react-toastify';

// Helper to get user's IP address
const getUserIpAddress = async () => {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    return data.ip;
  } catch (error) {
    console.error('Failed to fetch IP address:', error.message || error);
    return 'Unknown';  // Fallback in case of failure
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

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);

      // Ensure response and response.data are not undefined
      if (response && response.data) {
        const { access_token, refresh_token, user } = response.data;

        // Check if access_token and refresh_token exist before storing
        if (access_token && refresh_token && user) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          localStorage.setItem('user', JSON.stringify(user));
          localStorage.setItem('userRole', user.role_id);  // Store role in localStorage

          // Fetch IP and device info
          const ipAddress = await getUserIpAddress();
          const deviceInfo = getDeviceInfo();

          // Create a session after login with IP and device info
          await api.post(`/user/${user.id}/sessions`, {
            ip_address: ipAddress,
            device_info: deviceInfo,
          }, {
            headers: {
              'Authorization': `Bearer ${access_token}`,
            },
          });

          toast.success('Login successful');
          return response.data;  // Return user data and tokens
        } else {
          // Handle case where tokens or user data are missing in the response
          toast.error('Login failed: No user found or tokens missing.');
        }
      } else {
        toast.error('Login failed: Communication to the backend lost.');
      }
    } catch (error) {
      console.error('Login failed:', error.message || error);
      toast.error('Login failed. Please check your credentials or try again later.');
    }
  },

  logout: async () => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        toast.error('Already logged out.');
        return;
      }

      await api.post('/auth/logout', {
        refresh_token: refreshToken,
      }, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      // End the session after logout
      await api.delete(`/user/${user.id}/sessions`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      authService.clearSession();
      toast.success('Logout successful');
    } catch (error) {
      console.error('Logout failed:', error.message || error);
      authService.clearSession();
      toast.error('Logout failed');
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) toast.error('No refresh token available');

      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });

      if (response && response.data) {
        const { access_token } = response.data;

        if (access_token) {
          localStorage.setItem('access_token', access_token);

          // Update session expiration after token refresh
          const user = JSON.parse(localStorage.getItem('user'));
          await api.put(`/user/${user.id}/sessions`, {
            expires_at: new Date(Date.now() + 45 * 60 * 1000).toISOString(),  // Extend session expiration by 45 minutes
          }, {
            headers: {
              'Authorization': `Bearer ${access_token}`,
            },
          });

          return access_token;
        } else {
          toast.error('Missing access token in response');
        }
      } else {
        toast.error('Invalid response from server');
      }
    } catch (error) {
      console.error('Token refresh failed:', error.message || error);
      authService.clearSession();
      toast.error('Token refresh failed. Please log in again.');
    }
  },

  getAccessToken: () => {
    return localStorage.getItem('access_token') || null;
  },

  isLoggedIn: async () => {
    const token = localStorage.getItem('access_token');

    if (token && !authService.isTokenExpired(token)) {
      return true;
    } else if (token && authService.isTokenExpired(token)) {
      try {
        await authService.refreshToken();
        return true;
      } catch (error) {
        authService.logout();
        toast.error('Session expired. Please log in again.');
      }
    } else {
      authService.logout();
      toast.error('You are not logged in. Please log in.');
    }
  },

  isTokenExpired: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));  // Decode the token payload
      return decoded.exp * 1000 < Date.now();  // Check if token is expired
    } catch (e) {
      console.error('Token expiration check failed:', e.message || e);
      return true;
    }
  },

  clearSession: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
  }
};

export default authService;
