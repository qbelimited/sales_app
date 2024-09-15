import api from './api';
import { toast } from 'react-toastify';

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);

      if (response && response.data) {
        const { access_token, refresh_token, user, expiry } = response.data;

        if (access_token && refresh_token) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          localStorage.setItem('user', JSON.stringify(user));
          localStorage.setItem('userRole', user.role.id);  // Store role in localStorage
          localStorage.setItem('expiry', Date.now() + expiry * 1000);  // Store expiry in ms

          toast.success('Login successful');
          return response.data;  // Return user data and tokens
        } else {
          throw new Error('Missing access or refresh token in response.');
        }
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Login failed:', error);
      toast.error('Login failed. Please check your credentials or try again later.');
    }
  },

  logout: async (sessionId = null, expiredSession = false) => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        toast.error('Already logged out.');
        return;
      }

      if (sessionId && user) {
        // Call API to end the specific session if sessionId exists
        await api.delete(`/users/${user.id}/sessions/${sessionId}`);
      }

      // Call API to log out if tokens exist
      await api.post('/auth/logout', {
        refresh_token: refreshToken,
      }, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
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

      if (response && response.data) {
        const { access_token, expiry } = response.data;

        if (access_token) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('expiry', Date.now() + expiry * 1000);  // Update expiry in ms
          toast.success('Session refreshed successfully');
          return access_token;
        } else {
          throw new Error('Missing access token in response.');
        }
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      authService.clearSession();
      toast.error('Session expired. Please log in again.');
    }
  },

  getAccessToken: () => {
    return localStorage.getItem('access_token') || null;
  },

  isLoggedIn: async () => {
    const token = localStorage.getItem('access_token');
    const expiry = localStorage.getItem('expiry');

    if (token && expiry && Date.now() < expiry) {
      return true;
    } else if (token && expiry && Date.now() >= expiry) {
      try {
        await authService.refreshToken();
        return true;
      } catch (error) {
        authService.logout(null, true);
      }
    } else {
      authService.logout();
      toast.error('You are not logged in. Please log in.');
    }
  },

  isTokenExpired: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));
      return decoded.exp * 1000 < Date.now();
    } catch (e) {
      console.error('Token expiration check failed:', e);
      return true;
    }
  },

  clearSession: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
    localStorage.removeItem('expiry');
  }
};

export default authService;
