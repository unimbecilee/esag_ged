import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercepteur pour injecter le token dynamiquement
api.interceptors.request.use(config => {
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer les erreurs globales
api.interceptors.response.use(
  response => {
    console.log('API Response success:', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('API Response error:', 
      error.response?.status || 'No status', 
      error.response?.config?.url || 'No URL',
      error.message
    );
    
    if (error.response?.status === 401) {
      console.warn('Unauthorized access detected, clearing token');
      localStorage.removeItem('token');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export default api;