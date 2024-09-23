// api.js
import axios from 'axios';
import authService from './authService';
import { toast } from 'react-toastify';

// Create an axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://api.salesapp.impactlife.com.gh/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers = [];
let isRedirecting = false;

// Notify all subscribers once the token is refreshed
const onRefreshed = (token) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

// Add a subscriber to retry requests after token refresh
const subscribeTokenRefresh = (cb) => {
  refreshSubscribers.push(cb);
};

// Request interceptor to add the Authorization header if the token exists
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

// Response interceptor to handle token expiration and refresh logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Queue requests while refreshing token
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
        const newToken = await authService.refreshToken();
        isRefreshing = false;
        onRefreshed(newToken);

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (err) {
        isRefreshing = false;
        if (!isRedirecting) {
          isRedirecting = true;
          authService.logout();
          window.location.href = '/login';
        }
        return Promise.reject(err);
      }
    }

    // Handle 403 Forbidden (token misuse or blacklist)
    if (error.response?.status === 403 && !isRedirecting) {
      isRedirecting = true;
      authService.logout();
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Handle network or server errors
    if (!error.response) {
      console.error('Network or server error:', error);
      toast.error('Network error. Please check your internet connection or try again later.');
    }

    return Promise.reject(error);
  }
);

export default api;
