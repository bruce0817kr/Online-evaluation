// filepath: c:/Project/Online-evaluation/frontend/src/services/apiClient.js
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019'; // 환경 변수 또는 기본값 (포트매니저 호환)
const API_URL = `${BACKEND_URL}/api`;

// Error notification function (can be replaced with your notification system)
const showNotification = (message, type = 'error') => {
  // Simple console logging for now - can be replaced with toast notification
  if (type === 'error') {
    console.error('API Error:', message);
    // Optionally show user-friendly message using your notification system
  }
};

// User-friendly error messages
const getErrorMessage = (error) => {
  if (error.response) {
    const status = error.response.status;
    const data = error.response.data;
    
    switch (status) {
      case 400:
        return data?.detail || '잘못된 요청입니다.';
      case 401:
        return '로그인이 필요합니다.';
      case 403:
        return '권한이 없습니다.';
      case 404:
        return '요청한 리소스를 찾을 수 없습니다.';
      case 409:
        return '이미 존재하는 데이터입니다.';
      case 413:
        return '파일 크기가 너무 큽니다.';
      case 415:
        return '지원하지 않는 파일 형식입니다.';
      case 422:
        return '입력 데이터가 올바르지 않습니다.';
      case 429:
        return '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
      case 500:
        return '서버 오류가 발생했습니다.';
      case 502:
      case 503:
      case 504:
        return '서버에 일시적인 문제가 있습니다. 잠시 후 다시 시도해주세요.';
      default:
        return data?.detail || `오류가 발생했습니다 (${status})`;
    }
  } else if (error.request) {
    return '네트워크 연결을 확인해주세요.';
  } else {
    return '알 수 없는 오류가 발생했습니다.';
  }
};

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // Increased timeout for file uploads
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 모든 요청에 토큰 추가
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 향상된 에러 처리
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const errorMessage = getErrorMessage(error);
    
    if (error.response) {
      const status = error.response.status;
      
      switch (status) {
        case 401:
          // Handle unauthorized access
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          showNotification('로그인 세션이 만료되었습니다. 다시 로그인해주세요.');
          // Redirect to login page if not already there
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
          break;
        case 403:
          showNotification('이 작업을 수행할 권한이 없습니다.');
          break;
        case 404:
          console.error('API endpoint not found:', error.config?.url);
          break;
        case 429:
          showNotification('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.');
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          showNotification('서버에 문제가 있습니다. 관리자에게 문의해주세요.');
          break;
        default:
          // Don't show notification for other errors - let components handle them
          break;
      }
    } else if (error.request) {
      showNotification('네트워크 연결을 확인해주세요.');
    }
    
    // Add user-friendly error message to error object
    error.userMessage = errorMessage;
    
    return Promise.reject(error);
  }
);

// Retry function for failed requests
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  let lastError;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      // Don't retry for client errors (4xx)
      if (error.response && error.response.status >= 400 && error.response.status < 500) {
        throw error;
      }
      
      // Wait before retrying
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }
  
  throw lastError;
};

// Enhanced API client with error handling utilities
export const api = {
  client: apiClient,
  getErrorMessage,
  retryRequest,
  
  // Utility methods for common operations
  async get(url, config = {}) {
    try {
      const response = await apiClient.get(url, config);
      return response.data;
    } catch (error) {
      console.error(`GET ${url} failed:`, error.userMessage || error.message);
      throw error;
    }
  },
  
  async post(url, data, config = {}) {
    try {
      const response = await apiClient.post(url, data, config);
      return response.data;
    } catch (error) {
      console.error(`POST ${url} failed:`, error.userMessage || error.message);
      throw error;
    }
  },
  
  async put(url, data, config = {}) {
    try {
      const response = await apiClient.put(url, data, config);
      return response.data;
    } catch (error) {
      console.error(`PUT ${url} failed:`, error.userMessage || error.message);
      throw error;
    }
  },
  
  async delete(url, config = {}) {
    try {
      const response = await apiClient.delete(url, config);
      return response.data;
    } catch (error) {
      console.error(`DELETE ${url} failed:`, error.userMessage || error.message);
      throw error;
    }
  }
};

export default apiClient;
