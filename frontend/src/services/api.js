import axios from 'axios';
import authService from './authService';
import { toast } from 'react-toastify';

// Create an axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers = [];
let isRedirecting = false; // Prevent multiple redirects or page refreshes

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

    // If the error is a 401 (Unauthorized) and the request has not been retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // If a token refresh is already in progress, queue this request until the token is refreshed
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
        // Refresh the token
        const newToken = await authService.refreshToken();
        isRefreshing = false;

        // Notify all queued requests with the new token
        onRefreshed(newToken);

        // Update the Authorization header with the new token
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (err) {
        isRefreshing = false;
        if (!isRedirecting) {
          isRedirecting = true; // Set the redirect flag
          authService.logout(); // Log the user out
          window.location.href = '/login'; // Redirect to login page
        }
        return Promise.reject(err);
      }
    }

    // Handle case where refresh token is invalid or expired (403 Forbidden)
    if (error.response?.status === 403 && !isRedirecting) {
      isRedirecting = true; // Prevent multiple refreshes or redirects
      authService.logout(); // Log the user out
      window.location.href = '/login'; // Redirect to login page
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
