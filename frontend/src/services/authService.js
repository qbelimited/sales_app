import api from './api';

const authService = {
  login: async (credentials, showToast) => {
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

          // Store user agent and IP address in localStorage for audit logging
          const userAgent = navigator.userAgent;
          const ipAddress = await authService.getIpAddress();
          localStorage.setItem('userAgent', userAgent);
          localStorage.setItem('ipAddress', ipAddress);

          showToast('success', 'Login successful');
          return response.data;  // Return user data and tokens
        } else {
          throw new Error('Missing access or refresh token in response.');
        }
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Login failed:', error);
      showToast('danger', 'Login failed. Please check your credentials or try again later.');
    }
  },

  logout: async (sessionId = null, expiredSession = false, showToast) => {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      const user = JSON.parse(localStorage.getItem('user'));

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        showToast('danger', 'Already logged out.');
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
        showToast('danger', 'Session expired. You have been logged out.');
      } else {
        showToast('success', 'Logout successful');
      }
    } catch (error) {
      console.error('Logout failed:', error);
      authService.clearSession();
      showToast('danger', 'Logout failed');
    }
  },

  refreshToken: async (showToast) => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token available.');

      const response = await api.post('/auth/refresh', { refresh_token: refreshToken });

      if (response && response.data) {
        const { access_token, expiry } = response.data;

        if (access_token) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('expiry', Date.now() + expiry * 1000);  // Update expiry in ms
          showToast('success', 'Session refreshed successfully');
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
      showToast('danger', 'Session expired. Please log in again.');
    }
  },

  getAccessToken: () => {
    return localStorage.getItem('access_token') || null;
  },

  isLoggedIn: async (showToast) => {
    const token = localStorage.getItem('access_token');
    const expiry = localStorage.getItem('expiry');

    if (token && expiry && Date.now() < expiry) {
      return true;
    } else if (token && expiry && Date.now() >= expiry) {
      try {
        await authService.refreshToken(showToast);
        return true;
      } catch (error) {
        authService.logout(null, true, showToast);
      }
    } else {
      authService.logout(null, true, showToast);
      showToast('danger', 'You are not logged in. Please log in.');
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
    localStorage.removeItem('userAgent');
    localStorage.removeItem('ipAddress');
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
