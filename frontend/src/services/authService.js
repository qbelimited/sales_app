import api from './api';
import { toast } from 'react-toastify';

let activityTimeout = null;
let tokenExpirationTimeout = null;
const userInactivityLimit = 30 * 60 * 1000; // 30 minutes inactivity limit

const resetActivityTimeout = (logoutCallback) => {
  clearTimeout(activityTimeout);
  activityTimeout = setTimeout(() => {
    toast.warning('You have been logged out due to inactivity.');
    logoutCallback();
  }, userInactivityLimit);
};

const getUTCDateTime = () => {
  const now = new Date();

  const year = now.getUTCFullYear();
  const month = String(now.getUTCMonth() + 1).padStart(2, '0'); // Months are zero-indexed
  const day = String(now.getUTCDate()).padStart(2, '0');
  const hours = String(now.getUTCHours()).padStart(2, '0');
  const minutes = String(now.getUTCMinutes()).padStart(2, '0');
  const seconds = String(now.getUTCSeconds()).padStart(2, '0');
  const milliseconds = String(now.getUTCMilliseconds()).padStart(3, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;
};

const resetTokenExpirationTimeout = (token, refreshCallback) => {
  clearTimeout(tokenExpirationTimeout);
  const tokenExpiryTime = authService.getTokenExpirationTime(token);
  const timeLeft = tokenExpiryTime - Date.now();

  tokenExpirationTimeout = setTimeout(() => {
    if (activityTimeout) {
      refreshCallback();
    } else {
      toast.error('Session expired due to inactivity.');
      authService.logout();
    }
  }, timeLeft - 5 * 60 * 1000); // Trigger refresh 5 minutes before expiration
};

const authService = {
  login: async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials);

      if (response && response.data) {
        const { access_token, refresh_token, user } = response.data;

        if (access_token && refresh_token) {
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          localStorage.setItem('user', JSON.stringify(user));
          localStorage.setItem('userRoleID', user.role.id);
          localStorage.setItem('userRoleName', user.role.name);

          // Create a new session in the database
          await authService.createSession(user.id, access_token);

          toast.success('Login successful!');

          resetActivityTimeout(authService.logout);
          resetTokenExpirationTimeout(access_token, authService.refreshToken);

          return response.data;
        } else {
          throw new Error('Missing access or refresh token in response.');
        }
      } else {
        throw new Error('Invalid response from server.');
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
      const user = localStorage.getItem('user');
      const sessionId = localStorage.getItem('sessionId');

      if (!user) {
        authService.clearSession();
        toast.error('User data is missing. You have been logged out.');
        return;
      }

      const userId = JSON.parse(user).id;

      if (!accessToken && !refreshToken) {
        authService.clearSession();
        toast.error('You are already logged out.');
        return;
      }

      // Update the session before logging out
      if (sessionId) {
        await authService.updateSession(userId, sessionId, {
          logout_time: getUTCDateTime(),
          is_active: false
        });
      }

      // End all active sessions
      await authService.endAllActiveSessions();

      // Send a request to logout from the server
      await api.post('/auth/logout', { refresh_token: refreshToken }, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });

      toast.success('You have successfully logged out.');
      authService.clearSession();
    } catch (error) {
      console.error('Logout failed:', error);
      authService.clearSession();
      toast.error('Logout failed. Please try again.');
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
          resetTokenExpirationTimeout(access_token, authService.refreshToken);
          toast.info('Session refreshed successfully.');
          return access_token;
        } else {
          throw new Error('Missing access token in response.');
        }
      } else {
        throw new Error('Invalid response from server.');
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
      toast.info('You are already logged in.');
      return true;
    } else if (token && authService.isTokenExpired(token)) {
      try {
        await authService.refreshToken();
        return true;
      } catch (error) {
        toast.error('Session expired. Please log in again.');
        authService.logout();
      }
    } else {
      toast.warning('You are not logged in. Please log in.');
      authService.logout();
    }
  },

  checkTokenValidity: () => {
    const token = authService.getAccessToken();
    if (token && !authService.isTokenExpired(token)) {
      return true;
    }
    return false;
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

  getTokenExpirationTime: (token) => {
    try {
      const decoded = JSON.parse(atob(token.split('.')[1]));
      return decoded.exp * 1000;
    } catch (e) {
      console.error('Failed to decode token:', e);
      return null;
    }
  },

  createSession: async (userId, token) => {
    try {
      const ipAddress = await authService.getUserIPAddress();
      const loginTime = getUTCDateTime();
      const expiresAt = new Date(authService.getTokenExpirationTime(token)).toISOString();

      const sessionData = {
        user_id: userId,
        login_time: loginTime,
        expires_at: expiresAt,
        ip_address: ipAddress,
        is_active: true,
      };

      const response = await api.post(`/users/${userId}/sessions`, sessionData, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response && response.data) {
        localStorage.setItem('sessionId', response.data.id);
        toast.success('Session created successfully.');
      } else {
        throw new Error('Failed to create session.');
      }
    } catch (error) {
      console.error('Create session failed:', error);
      toast.error('Could not create session.');
    }
  },

  updateSession: async (userId, sessionId, data) => {
    try {
      const response = await api.put(`/users/${userId}/sessions/${sessionId}`, data, {
        headers: {
          'Authorization': `Bearer ${authService.getAccessToken()}`
        }
      });

      if (response && response.data) {
        toast.success('Session updated successfully.');
        return response.data;
      } else {
        throw new Error('Failed to update session.');
      }
    } catch (error) {
      console.error('Update session failed:', error);
      toast.error('Could not update session.');
    }
  },

  endAllActiveSessions: async () => {
    try {
      const userId = JSON.parse(localStorage.getItem('user')).id;
      await api.delete(`/users/${userId}/sessions`, {
        headers: {
          'Authorization': `Bearer ${authService.getAccessToken()}`,
        },
      });
      toast.success('All sessions ended successfully.');
    } catch (error) {
      console.error('End session failed:', error);
      toast.error('Could not end session.');
    }
  },

  getUserIPAddress: async () => {
    try {
      const response = await fetch('https://api.ipify.org?format=json');
      const data = await response.json();
      return data.ip || 'Unknown';
    } catch (error) {
      toast.error('Failed to fetch IP address');
      return 'Unknown';
    }
  },

  monitorUserActivity: () => {
    ['click', 'keydown', 'mousemove', 'scroll'].forEach((event) => {
      window.addEventListener(event, () => resetActivityTimeout(authService.logout));
    });

    resetActivityTimeout(authService.logout);
  },

  clearSession: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('userRoleName');
    localStorage.removeItem('userRoleId');
    localStorage.removeItem('sessionId');
    toast.info('Session cleared.');
  },
};

authService.monitorUserActivity();

export default authService;
