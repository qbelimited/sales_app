import axios from 'axios';
import { toast } from 'react-toastify';
import authService from './authService';

// Create an axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRedirecting = false; // Prevent multiple redirects or page refreshes

// Function to handle 401 (Unauthorized) responses
const handleUnauthorizedError = async () => {
  if (!isRedirecting) {
    isRedirecting = true;
    toast.error('Session expired. Redirecting to login.');
    await authService.logout(); // Log the user out
    window.location.replace('/login'); // Redirect to login page
  }
};

// Request interceptor to add the Authorization header if the token exists
api.interceptors.request.use(
  async (config) => {
    const accessToken = authService.getAccessToken();

    // If the token is expired, log the user out
    if (!accessToken || authService.isTokenExpired(accessToken)) {
      toast.error('Session expired. Please log in again.');
      await authService.logout();
      window.location.replace('/login'); // Redirect to login page
      return Promise.reject(new Error('Session expired'));
    }

    // Add the valid token to the request
    config.headers.Authorization = `Bearer ${accessToken}`;
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    toast.error('Request error. Please try again.');
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      await handleUnauthorizedError();
    }

    // Handle 403 (Forbidden) when refresh token is invalid or expired
    if (error.response?.status === 403 && !isRedirecting) {
      console.warn('403 Forbidden: Token expired or invalid.');
      toast.error('Your session has expired. Please log in again.');
      await handleUnauthorizedError();
    }

    // Handle network or server errors
    if (!error.response) {
      console.error('Network or server error:', error);
      toast.error('Network error. Please try again later or contact support.');
      return Promise.reject(new Error('Network or server error'));
    }

    // Log the error for further debugging
    console.error('API error:', error);
    toast.error('An error occurred. Please try again later or contact support.');
    return Promise.reject(error);
  }
);

export default api;
