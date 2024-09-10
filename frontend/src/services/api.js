import axios from 'axios';
import authService from './authService';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api/v1', // Dynamic base URL
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers = [];

// Add subscribers to retry failed requests after token refresh
function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// Request interceptor to add token to headers
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

// Response interceptor for handling token expiration, refresh, and other errors
api.interceptors.response.use(
  (response) => response,  // Return the response directly if no error
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors by trying to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        // Add to queue if a token refresh is already in progress
        return new Promise((resolve) => {
          subscribeTokenRefresh((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      isRefreshing = true;
      try {
        const newAccessToken = await authService.refreshToken();
        isRefreshing = false;

        // Notify subscribers with the new token
        onRefreshed(newAccessToken);

        // Retry the original request with the new token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        console.error('Token refresh failed:', refreshError);

        // Log the user out and redirect to the login page
        authService.logout();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle 403 Forbidden error
    if (error.response?.status === 403) {
      console.warn('Access forbidden: You do not have permission to access this resource.');
      // Optionally, redirect the user to a "403 Forbidden" page or show a modal
    }

    // Handle 404 Not Found error
    if (error.response?.status === 404) {
      console.error('Error: The requested resource could not be found.');
      // Optionally, redirect the user to a "404 Not Found" page
    }

    // Handle 422 Validation Error (Unprocessable Entity)
    if (error.response?.status === 422) {
      console.warn('Validation error: Check the provided data.');
      // Optionally, you could surface the validation error messages to the user
    }

    // Handle 500 Server Error
    if (error.response?.status === 500) {
      console.error('Server error: Something went wrong on the server.');
      // Optionally, show a global toast notification about the server error
    }

    return Promise.reject(error);
  }
);

export default api;
