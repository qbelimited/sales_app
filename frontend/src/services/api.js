import axios from 'axios';
import authService from './authService';

// Create an Axios instance with a base URL
const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api/v1',  // Adjust this to your actual base URL
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to prevent multiple refresh attempts at the same time
let isRefreshing = false;
let refreshSubscribers = [];

// Function to add subscribers that will retry requests after the token is refreshed
function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

// Function to call all the subscribers once the token is refreshed
function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

// Request interceptor to add the access token to headers
api.interceptors.request.use(
  (config) => {
    const access_token = authService.getAccessToken();
    if (access_token) {
      config.headers.Authorization = `Bearer ${access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,  // If the response is successful, return it
  async (error) => {
    const originalRequest = error.config;

    // Check if the error is 401 Unauthorized and the request has not been retried
    if (error.response.status === 401 && !originalRequest._retry) {
      // Set the _retry flag on the original request to prevent infinite retry loop
      originalRequest._retry = true;

      // If the refresh process is already ongoing, wait for it to complete
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token) => {
            // Update the original request with the new token and retry it
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      // Set refreshing flag to true to avoid concurrent refresh attempts
      isRefreshing = true;

      try {
        // Attempt to refresh the access token
        const newAccessToken = await authService.refreshToken();
        isRefreshing = false;

        // Call all the subscribers waiting for the token refresh
        onRefreshed(newAccessToken);

        // Update the Authorization header with the new access token and retry the request
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, log the user out or handle the error accordingly
        isRefreshing = false;
        console.error('Refresh token failed:', refreshError);
        authService.logout();
        window.location.href = '/login';  // Redirect to login page
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);  // Reject the error if it's not 401 or refresh fails
  }
);

export default api;
