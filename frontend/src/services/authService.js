import api from './api';

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token, refresh_token, user } = response.data;

      // Store tokens and user information in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));  // Store user data

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
      if (!accessToken) throw new Error('No access token available for logout.');

      await api.post('/auth/logout', {}, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      // Clear tokens and user data from localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userID');
    } catch (error) {
      console.error('Logout failed:', error);
      throw new Error(error.response?.data?.message || 'Logout failed');
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
      const errorMessage = error.response?.data?.message || 'Token refresh failed';
      throw new Error(errorMessage);
    }
  },

  getAccessToken: () => {
    const token = localStorage.getItem('access_token');
    return token ? token : null;  // Return the token or null if it doesn't exist
  },

  isLoggedIn: () => !!localStorage.getItem('access_token'),  // Check if logged in by checking if access_token exists
};

export default authService;
