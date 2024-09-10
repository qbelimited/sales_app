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

// Response interceptor for handling token expiration and other errors
api.interceptors.response.use(
  (response) => response,  // Return the response directly if no error
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 errors by trying to refresh the token
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
        authService.logout();
        window.location.href = '/login'; // Redirect to login page
        return Promise.reject(refreshError);
      }
    }

    // Optional: Handle other common HTTP errors here (e.g., 403, 500)
    if (error.response?.status === 403) {
      console.warn('Access forbidden');
      // Optionally, trigger an action like redirecting to a forbidden page
    }

    if (error.response?.status === 500) {
      console.error('Server error');
      // Notify users about server issues
    }

    return Promise.reject(error);
  }
);

export default api;
