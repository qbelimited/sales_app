import axios from 'axios';
import authService from './authService';  // Assumes authService manages tokens and logout

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api/v1',  // Base API URL
  headers: {
    'Content-Type': 'application/json',
  }
});

// Token refresh flag and subscribers for handling token refresh requests
let isRefreshing = false;
let refreshSubscribers = [];

// Add subscriber to retry failed requests after token is refreshed
const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

// Notify all subscribers with the new token
const onRefreshed = (token) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

// Request interceptor to add Authorization header if token is available
api.interceptors.request.use(
  (config) => {
    const accessToken = authService.getAccessToken();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors (e.g., token expiration, 401 Unauthorized)
api.interceptors.response.use(
  (response) => response,  // Return the response directly if successful
  async (error) => {
    const originalRequest = error.config;

    // If 401 (Unauthorized) and request has not been retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Check if another refresh token request is already in progress
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      isRefreshing = true;
      try {
        // Attempt to refresh the access token
        const newAccessToken = await authService.refreshToken();
        isRefreshing = false;

        // Notify all subscribers with the new token and retry the original request
        onRefreshed(newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (err) {
        isRefreshing = false;
        authService.logout();
        window.location.href = '/login';  // Redirect to login on token refresh failure
        return Promise.reject(err);
      }
    }

    // Handle other errors based on status codes
    if (error.response?.status === 403) {
      console.warn('Forbidden: You do not have access to this resource.');
    }
    if (error.response?.status === 404) {
      console.error('Resource not found.');
    }
    if (error.response?.status === 500) {
      console.error('Internal server error.');
    }

    return Promise.reject(error);  // Forward the error to the calling code
  }
);

export default api;
