import api from './api';

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token, refresh_token, user } = response.data;

      // Store tokens and user information in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('userRole', user.role_id);  // Store role in localStorage

      return response.data;  // Return user data and tokens
    } catch (error) {
      console.error('Login failed:', error);
      const errorMessage = error.response?.data?.message || 'Login failed';
      throw new Error(errorMessage);
    }
  },

  logout: async () => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');

      if (!accessToken) throw new Error('No access token available for logout.');
      if (!refreshToken) throw new Error('No refresh token available for logout.');

      // Send both the access token and refresh token to the logout endpoint
      await api.post('/auth/logout', {
        refresh_token: refreshToken,  // Include the refresh token in the request body
      }, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      // Clear tokens and user data from localStorage
      authService.clearSession();
    } catch (error) {
      console.error('Logout failed:', error);
      const errorMessage = error.response?.data?.message || 'Logout failed';
      throw new Error(errorMessage);
    }
  },

  refreshToken: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token available.');

      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
      const { access_token } = response.data;

      // Update access token in localStorage
      localStorage.setItem('access_token', access_token);

      return access_token;  // Return the new access token
    } catch (error) {
      console.error('Token refresh failed:', error);

      // If the refresh token fails, logout the user and clear session
      authService.clearSession();

      const errorMessage = error.response?.data?.message || 'Token refresh failed';
      throw new Error(errorMessage);
    }
  },

  getAccessToken: () => {
    return localStorage.getItem('access_token') || null;
  },

  isLoggedIn: () => {
    const token = localStorage.getItem('access_token');
    return !!token && !authService.isTokenExpired(token);  // Check if logged in and token is not expired
  },

  isTokenExpired: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));  // Decode the token payload
      return decoded.exp * 1000 < Date.now();  // Check if token is expired
    } catch (e) {
      console.error('Token expiration check failed:', e);
      return true;  // Return true if token cannot be decoded or checked
    }
  },

  clearSession: () => {
    // Clear tokens and user data from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userID');
  }
};

export default authService;
