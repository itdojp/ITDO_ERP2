import axios, { AxiosInstance } from 'axios';

const BASE_URL = process.env.API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token if available
apiClient.interceptors.request.use(
  (config) => {
    const token = globalThis.testAuthToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Retry logic for flaky tests
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config;
    
    // Retry on network errors
    if (!config || !config.retry) {
      config.retry = 0;
    }
    
    if (config.retry < 3 && (error.code === 'ECONNABORTED' || !error.response)) {
      config.retry++;
      await new Promise(resolve => setTimeout(resolve, 1000 * config.retry));
      return apiClient(config);
    }
    
    return Promise.reject(error);
  }
);

// Helper to set auth token for tests
export function setTestAuthToken(token: string) {
  globalThis.testAuthToken = token;
}

// Helper to clear auth token
export function clearTestAuthToken() {
  delete globalThis.testAuthToken;
}