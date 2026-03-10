import axios from 'axios';

// Create API client for FastAPI backend
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // Crucial for signed cookies to work
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If not authenticated, we can redirect or trigger an event
    if (error.response?.status === 401) {
      // Small delay to prevent redirect loops when verifying auth state
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
