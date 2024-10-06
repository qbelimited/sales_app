// api.js
import axios from 'axios';
import authService from './authService';
import { toast } from 'react-toastify';

// Create an axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'https://api.salesapp.impactlife.com.gh/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false; // Flag to track if a token refresh is in progress
let refreshSubscribers = []; // List of subscribers waiting for token refresh
let isRedirecting = false; // Flag to prevent multiple redirects

// Notify all subscribers once the token is refreshed
const onRefreshed = (token) => {
  refreshSubscribers.forEach((cb) => cb(token)); // Call each subscriber with the new token
  refreshSubscribers = []; // Clear the subscribers list
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
      config.headers.Authorization = `Bearer ${accessToken}`; // Attach token to request headers
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiration and refresh logic
api.interceptors.response.use(
  (response) => response, // Pass through successful responses
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Mark request as retried

      // Queue requests while refreshing token
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest)); // Retry the original request with the new token
          });
        });
      }

      isRefreshing = true; // Set the refreshing flag

      try {
        const newToken = await authService.refreshToken(); // Attempt to refresh token
        isRefreshing = false; // Reset the refreshing flag
        onRefreshed(newToken); // Notify subscribers of the new token

        originalRequest.headers.Authorization = `Bearer ${newToken}`; // Set new token on original request
        return api(originalRequest); // Retry the original request
      } catch (err) {
        isRefreshing = false; // Reset the refreshing flag on error
        if (!isRedirecting) {
          isRedirecting = true; // Prevent multiple redirects
          authService.logout(); // Logout the user
          window.location.href = '/login'; // Redirect to login page
        }
        return Promise.reject(err); // Propagate error
      }
    }

    // Handle 403 Forbidden (token misuse or blacklist)
    if (error.response?.status === 403 && !isRedirecting) {
      isRedirecting = true; // Prevent multiple redirects
      authService.logout(); // Logout the user
      window.location.href = '/login'; // Redirect to login page
      return Promise.reject(error); // Propagate error
    }

    // Handle network or server errors
    if (!error.response) {
      console.error('Network or server error:', error);
      toast.error('Network error. Please check your internet connection or try again later.'); // Notify user of network error
    }

    return Promise.reject(error); // Propagate other errors
  }
);

export default api; // Export the Axios instance
