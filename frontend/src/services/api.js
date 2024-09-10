import axios from 'axios';
import authService from './authService';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api/v1',  // Base URL
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true  // Ensure credentials (e.g., cookies) are sent with requests
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

    // Handle 401 Unauthorized - Token Expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
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

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.warn('Access forbidden: You do not have permission to access this resource.');
    }

    // Handle 404 Not Found
    if (error.response?.status === 404) {
      console.error('Error: The requested resource could not be found.');
    }

    // Handle 422 Unprocessable Entity (Validation Error)
    if (error.response?.status === 422) {
      console.warn('Validation error: Check the provided data.');
    }

    // Handle 500 Internal Server Error
    if (error.response?.status === 500) {
      console.error('Server error: Something went wrong on the server.');
    }

    return Promise.reject(error);
  }
);

export default api;
