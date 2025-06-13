// filepath: c:/Project/Online-evaluation/frontend/src/services/apiClient.js
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'; // 환경 변수 또는 기본값
const API_URL = `${BACKEND_URL}/api`;

const apiClient = axios.create({
  baseURL: API_URL,
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
    return Promise.reject(error);
  }
);

// 응답 인터셉터: (옵션) 에러 처리 등
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 예: 401 Unauthorized 에러 시 로그인 페이지로 리다이렉트
    if (error.response && error.response.status === 401) {
      // localStorage.removeItem('token');
      // localStorage.removeItem('user');
      // window.location.href = '/login'; 
      console.error("Unauthorized, redirecting to login might be needed.");
    }
    return Promise.reject(error);
  }
);

export default apiClient;
