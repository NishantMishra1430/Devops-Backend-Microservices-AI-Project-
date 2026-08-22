import axios from 'axios';

// Dynamically read from Vite environment variables with fallback
const API_BASE_URL = "";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Zero-Trust Interceptor: Automatically injects JWT if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
