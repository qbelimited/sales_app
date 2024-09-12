import api from './api';
import { toast } from 'react-toastify';

// Helper to get user's IP address
const getUserIpAddress = async () => {
  try {
    const response = await fetch('https://api.ipify.org?format=json');
    const data = await response.json();
    // console.log('IP Address:', data.ip);  // Log IP Address
    return data.ip;
  } catch (error) {
    toast.error('Failed to fetch IP address');
    // console.error('Failed to fetch IP address:', error.message || error);
    return 'Unknown';  // Fallback in case of failure
  }
};

// Helper to get device information
const getDeviceInfo = () => {
  const userAgent = navigator.userAgent || 'Unknown';
  const deviceInfo = {
    browser: navigator.appName || 'Unknown',
    platform: navigator.platform || 'Unknown',
    userAgent,
  };
  // console.log('Device Info:', deviceInfo);  // Log Device Info
  return deviceInfo;
};

// Helper to store tokens and user data in localStorage
const storeSession = (access_token, refresh_token, user) => {
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  localStorage.setItem('user', JSON.stringify(user));
  localStorage.setItem('userRoleID', user.role.id);
  localStorage.setItem('userRoleName', user.role.name);
  // console.log('Stored Session:', { access_token, refresh_token, user });  // Log stored session data
  // console.log('User Role:', user.role);
  // console.log('User Role ID:', user.role.id);
  // console.log('User Role name:', user.role.name);
};

// Helper to clear tokens and user data from localStorage
const clearSession = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  localStorage.removeItem('userRoleID');
  localStorage.removeItem('userRoleName');
  // console.log('Session cleared');  // Log session cleared
};

// authService for authentication and session management
const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);

      if (response && response.data) {
        const { access_token, refresh_token, user } = response.data;

        if (access_token && refresh_token && user) {
          // Store session
          storeSession(access_token, refresh_token, user);

          // Fetch IP and device info
          const ipAddress = await getUserIpAddress();
          const deviceInfo = getDeviceInfo();

          // Create a session after login
          await api.post(`/users/${user.id}/sessions`, {
            ip_address: ipAddress,
            device_info: deviceInfo,
          }, {
            headers: {
              'Authorization': `Bearer ${access_token}`,
            },
          });

          toast.success('Login successful');
          return response.data;
        } else {
          toast.error('Login failed: Missing tokens or user data.');
          // console.error('Login failed: Missing tokens or user data.');
        }
      } else {
        toast.error('Login failed: Server response is invalid.');
        // console.error('Login failed: Server response is invalid.');
      }
    } catch (error) {
      // console.error('Login failed:', error.message || error);
      toast.error('Login failed. Please check your credentials or try again later.');
    }
  },

  logout: async () => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        clearSession();
        toast.error('Already logged out.');
        // console.log('Already logged out');
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
      await api.delete(`/users/${user.id}/sessions`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      clearSession();
      toast.success('Logout successful');
      // console.log('Logout successful');
    } catch (error) {
      // console.error('Logout failed:', error.message || error);
      clearSession();
      toast.error('Logout failed');
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        toast.error('No refresh token available');
        // console.log('No refresh token available');
        return;
      }

      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });

      if (response && response.data) {
        const { access_token } = response.data;

        if (access_token) {
          localStorage.setItem('access_token', access_token);

          // Update session expiration after token refresh
          const user = JSON.parse(localStorage.getItem('user'));
          await api.put(`/users/${user.id}/sessions`, {
            expires_at: new Date(Date.now() + 45 * 60 * 1000).toISOString(),  // Extend session expiration by 45 minutes
          }, {
            headers: {
              'Authorization': `Bearer ${access_token}`,
            },
          });

          // console.log('Token refreshed successfully:', access_token);  // Log token refresh
          return access_token;
        } else {
          toast.error('Missing access token in refresh response');
          // console.error('Missing access token in refresh response');
        }
      } else {
        toast.error('Invalid response from server during token refresh');
        // console.error('Invalid response from server during token refresh');
      }
    } catch (error) {
      // console.error('Token refresh failed:', error.message || error);
      clearSession();
      toast.error('Token refresh failed. Please log in again.');
    }
  },

  getAccessToken: () => {
    const token = localStorage.getItem('access_token');
    // console.log('Access Token:', token);  // Log access token
    return token || null;
  },

  isLoggedIn: async () => {
    const token = localStorage.getItem('access_token');
    // console.log('Checking if logged in with token:', token);  // Log token check

    if (token && !authService.isTokenExpired(token)) {
      return true;
    } else if (token && authService.isTokenExpired(token)) {
      try {
        await authService.refreshToken();
        return true;
      } catch (error) {
        authService.logout();
        toast.error('Session expired. Please log in again.');
        // console.error('Session expired. Please log in again.');
      }
    } else {
      authService.logout();
      toast.error('You are not logged in. Please log in.');
      // console.log('You are not logged in.');
    }
  },

  isTokenExpired: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));  // Decode the token payload
      const isExpired = decoded.exp * 1000 < Date.now();
      // console.log('Token expiration check:', isExpired);  // Log token expiration check
      return isExpired;
    } catch (e) {
      // console.error('Token expiration check failed:', e.message || e);
      return true;
    }
  },

  clearSession,  // Export clearSession for usage in other parts of the app
};

export default authService;
