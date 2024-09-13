import api from './api';
import { toast } from 'react-toastify';

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);

      // Ensure response and response.data are not undefined
      if (response && response.data) {
        const { access_token, refresh_token, user } = response.data;

        // Check if access_token and refresh_token exist before storing
        if (access_token && refresh_token) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          localStorage.setItem('user', JSON.stringify(user));
          localStorage.setItem('userRole', user.role.id);  // Store role in localStorage

          toast.success('Login successful');
          return response.data;  // Return user data and tokens
        } else {
          // Handle case where tokens are missing in the response
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

  logout: async () => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');

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

      authService.clearSession();
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
        const { access_token } = response.data;

        if (access_token) {
          localStorage.setItem('access_token', access_token);
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
      console.error('Token expiration check failed:', e);
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
