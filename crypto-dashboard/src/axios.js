import axios from 'axios';

// Create an Axios instance
const axiosInstance = axios.create({
  baseURL: 'http://localhost:5000/api', // Set the base URL for your API
  timeout: 10000, // Optional: set a timeout
});

// Add the interceptor to log error details
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    console.error('Axios Error Details:', error);
    return Promise.reject(error);
  }
);

export default axiosInstance;
