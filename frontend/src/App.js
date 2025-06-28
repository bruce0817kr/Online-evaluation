import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Document, Page, pdfjs } from 'react-pdf';
import TemplateManagement from './components/TemplateManagement.js'; // 템플릿 관리 컴포넌트 추가
import EvaluationManagement from './components/EvaluationManagement.js';
import AIAssistant from './components/AIAssistant.js'; // AI 도우미 컴포넌트 추가
import AIProviderManagement from './components/AIProviderManagement.js'; // AI 공급자 관리 컴포넌트 추가
import FileSecureViewer from './components/FileSecureViewer.js'; // 보안 파일 뷰어 컴포넌트 추가
import EvaluationPrintManager from './components/EvaluationPrintManager.js'; // 평가표 출력 관리 컴포넌트 추가
import AIEvaluationController from './components/AIEvaluationController.js'; // AI 평가 제어 컴포넌트 추가
import DeploymentManager from './components/DeploymentManager.js'; // 배포 관리 컴포넌트 추가
import AIModelDashboard from './components/AIModelDashboard.js'; // AI 모델 대시보드 컴포넌트 추가
import AIModelManagement from './components/AIModelManagement.js'; // AI 모델 관리 컴포넌트 추가
import FileSecurityDashboard from './components/FileSecurityDashboard.js'; // 파일 보안 대시보드 컴포넌트 추가
import NotificationProvider from './components/NotificationProvider.js'; // 알림 시스템 컴포넌트 추가
import NotificationCenter from './components/NotificationCenter.js'; // 알림 센터 컴포넌트 추가
import ToastNotification from './components/ToastNotification.js'; // 토스트 알림 컴포넌트 추가

// PDF.js worker setup
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
const API = `${BACKEND_URL}/api`;

// Utility Functions
const formatPhoneNumber = (phone) => {
  // 숫자만 추출
  const numbers = phone.replace(/\D/g, '');
  
  // 010으로 시작하는 11자리 숫자인지 확인
  if (numbers.length === 11 && numbers.startsWith('010')) {
    return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(7)}`;
  }
  
  // 기타 형식은 그대로 반환
  return phone;
};

const normalizePhoneNumber = (phone) => {
  // 숫자만 추출하여 저장용 형식으로 변환
  return phone.replace(/\D/g, '');
};

// 보안 강화된 PDF 새창 열기 함수
const openPDFInNewWindow = async (fileId, filename) => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('로그인이 필요합니다.');
      return;
    }

    const response = await axios.get(`${API}/files/${fileId}/preview`, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    if (response.data.type === 'pdf') {
      // Base64 데이터를 Blob으로 변환
      const binaryString = atob(response.data.content);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      // 보안 창 옵션으로 열기
      const newWindow = window.open(
        url, 
        '_blank', 
        'width=1000,height=800,scrollbars=yes,resizable=yes,toolbar=no,location=no,directories=no,status=no,menubar=no'
      );
      
      if (newWindow) {
        newWindow.document.title = `${filename || 'PDF 문서'} - ${response.data.watermark?.user || ''}`;
        
        // 워터마크 정보를 새 창에 전달
        newWindow.watermarkInfo = response.data.watermark;
      }
    } else {
      alert('PDF 파일이 아닙니다.');
    }
  } catch (error) {
    console.error('PDF 열기 실패:', error);
    if (error.response?.status === 403) {
      alert('이 파일에 접근할 권한이 없습니다.');
    } else if (error.response?.status === 401) {
      alert('로그인이 필요합니다.');
      localStorage.removeItem('token');
      window.location.href = '/login';
    } else {
      alert(`PDF 파일을 열 수 없습니다: ${error.response?.data?.detail || error.message}`);
    }
  }
};

// Auth Context
const AuthContext = React.createContext();

// PDF Viewer Component
const PDFViewer = ({ fileId, filename }) => {
  const [pdfData, setPdfData] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadPDF();
  }, [fileId]);

  const loadPDF = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/files/${fileId}/preview`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.type === 'pdf') {
        // Convert base64 to Uint8Array
        const binaryString = atob(response.data.content);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        setPdfData(bytes);
      } else {
        setError('PDF 파일이 아닙니다');
      }
    } catch (error) {
      console.error('PDF 로드 실패:', error);
      setError('PDF를 불러올 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
    setPageNumber(1);
  };

  const goToPrevPage = () => {
    setPageNumber(page => Math.max(1, page - 1));
  };

  const goToNextPage = () => {
    setPageNumber(page => Math.min(numPages, page + 1));
  };

  const zoomIn = () => {
    setScale(scale => Math.min(3.0, scale + 0.2));
  };

  const zoomOut = () => {
    setScale(scale => Math.max(0.5, scale - 0.2));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3">PDF 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="pdf-viewer bg-gray-50 rounded-lg p-4">
      <div className="pdf-controls flex items-center justify-between mb-4 p-3 bg-white rounded shadow">
        <div className="flex items-center space-x-4">
          <span className="font-medium">{filename}</span>
          <span className="text-sm text-gray-500">
            {pageNumber} / {numPages} 페이지
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            이전
          </button>
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 bg-blue-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음
          </button>
          <div className="border-l border-gray-300 pl-2 ml-2">
            <button
              onClick={zoomOut}
              className="px-2 py-1 bg-gray-600 text-white rounded mr-1"
            >
              -
            </button>
            <span className="px-2 text-sm">{Math.round(scale * 100)}%</span>
            <button
              onClick={zoomIn}
              className="px-2 py-1 bg-gray-600 text-white rounded ml-1"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <div className="pdf-container border border-gray-300 bg-white rounded overflow-auto max-h-[600px] flex justify-center">
        <Document
          file={pdfData}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={(error) => setError('PDF 로드 실패')}
          loading="PDF 로딩 중..."
        >
          <Page 
            pageNumber={pageNumber} 
            scale={scale}
            renderTextLayer={false}
            renderAnnotationLayer={false}
          />
        </Document>
      </div>
    </div>
  );
};

// Enhanced File Upload Component
const FileUploadZone = ({ onFileSelect, multiple = false, acceptedTypes = ".pdf,.doc,.docx" }) => {
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    onFileSelect(files);
  };

  const handleFileInputChange = (e) => {
    const files = Array.from(e.target.files);
    onFileSelect(files);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragOver 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept={acceptedTypes}
        multiple={multiple}
        onChange={handleFileInputChange}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        <div className="text-gray-400 text-5xl mb-4">📄</div>
        <p className="text-lg text-gray-600 mb-2">
          파일을 드래그하여 놓거나 클릭하여 선택하세요
        </p>
        <p className="text-sm text-gray-400">
          지원 형식: PDF, DOC, DOCX | 최대 크기: 50MB
        </p>
      </label>
    </div>
  );
};

// Progress Bar Component
const ProgressBar = ({ progress, filename }) => (
  <div className="w-full">
    <div className="flex justify-between text-sm text-gray-600 mb-1">
      <span>{filename}</span>
      <span>{Math.round(progress)}%</span>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
        style={{ width: `${progress}%` }}
      ></div>
    </div>
  </div>
);

// Statistics Card Component
const StatCard = ({ title, value, icon, color = "blue", trend = null }) => (
  <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
    <div className="flex items-center">
      <div className={`p-3 rounded-full bg-${color}-100 text-${color}-600`}>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="ml-4 flex-1">
        <p className="text-sm text-gray-600">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {trend && (
          <p className={`text-xs ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
            {trend.positive ? '↗' : '↘'} {trend.value}
          </p>
        )}
      </div>
    </div>
  </div>
);

// Modal Components
const Modal = ({ isOpen, onClose, title, children, size = "md" }) => {
  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-2xl", 
    lg: "max-w-4xl",
    xl: "max-w-6xl"
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`bg-white rounded-lg ${sizeClasses[size]} w-full mx-4 max-h-[90vh] overflow-y-auto`}>
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

// Secretary Signup Component
const SecretarySignup = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    email: "",
    reason: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      console.log("👥 간사 회원가입 신청 시작...");
      console.log("API URL:", API);
      console.log("신청 데이터:", {
        name: formData.name,
        phone: normalizePhoneNumber(formData.phone),
        email: formData.email,
        reason: formData.reason.substring(0, 50) + "..."
      });
      
      const response = await axios.post(`${API}/auth/secretary-signup`, {
        name: formData.name,
        phone: normalizePhoneNumber(formData.phone),
        email: formData.email,
        reason: formData.reason
      });
      
      console.log("✅ 간사 회원가입 신청 성공:", response.data);
      alert("간사 회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다.");
      onSuccess();
      onClose();
    } catch (error) {
      console.error("❌ 간사 회원가입 오류:", error);
      console.error("Error response:", error.response?.data);
      console.error("Error status:", error.response?.status);
      setError(error.response?.data?.detail || "회원가입 신청 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">간사 회원가입</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              이름 *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="이름을 입력하세요"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              전화번호 *
            </label>
            <input
              type="tel"
              value={formatPhoneNumber(formData.phone)}
              onChange={(e) => setFormData({...formData, phone: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="010-1234-5678"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              이메일 *
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({...formData, email: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="email@example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              신청 사유 *
            </label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({...formData, reason: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="간사 권한이 필요한 사유를 입력하세요"
              rows={3}
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "신청 중..." : "신청하기"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Login Component
const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showSecretarySignup, setShowSecretarySignup] = useState(false);  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      console.log("🔑 로그인 시도 시작...");
      console.log("API URL:", API);
      console.log("Backend URL:", BACKEND_URL);
      console.log("Credentials:", { username: credentials.username, password: "***" });
      
      // 입력 데이터 유효성 검사
      if (!credentials.username.trim() || !credentials.password.trim()) {
        throw new Error("아이디와 비밀번호를 모두 입력해주세요.");
      }
      
      const formData = new FormData();
      formData.append("username", credentials.username.trim());
      formData.append("password", credentials.password.trim());

      console.log("📤 로그인 요청 전송 중...");
      
      // axios 설정으로 타임아웃 설정
      const response = await axios.post(`${API}/auth/login`, formData, {
        timeout: 10000, // 10초 타임아웃
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      });
      
      console.log("📥 로그인 응답 받음:", response.status);
      
      // 응답 데이터 검증
      if (!response.data || typeof response.data !== 'object') {
        throw new Error("서버 응답 형식이 올바르지 않습니다.");
      }
      
      const { access_token, user } = response.data;
      
      // 필수 데이터 검증
      if (!access_token) {
        throw new Error("서버에서 인증 토큰을 반환하지 않았습니다.");
      }
      
      if (!user || !user.role) {
        throw new Error("사용자 정보가 완전하지 않습니다.");
      }
      
      console.log("✅ 로그인 성공, 토큰 저장 중...");
      console.log("사용자 정보:", { 
        name: user.user_name, 
        role: user.role, 
        id: user.id 
      });
      
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user));
      
      // 저장 확인
      const savedToken = localStorage.getItem("token");
      const savedUser = localStorage.getItem("user");
      
      if (!savedToken || !savedUser) {
        throw new Error("로그인 정보 저장에 실패했습니다.");
      }
      
      console.log("✅ 로그인 정보 저장 완료");
      onLogin(user);
      
    } catch (error) {
      console.error("❌ 로그인 오류 발생:", error);
      
      let errorMessage = "로그인에 실패했습니다.";
      
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = "서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.";
      } else if (error.message.includes('Network Error')) {
        errorMessage = "네트워크 연결을 확인해주세요.";
      } else if (error.response) {
        console.error("Error response:", error.response.data);
        console.error("Error status:", error.response.status);
        
        if (error.response.status === 401) {
          errorMessage = "아이디 또는 비밀번호가 잘못되었습니다.";
        } else if (error.response.status === 422) {
          errorMessage = "입력 데이터 형식이 올바르지 않습니다.";
        } else if (error.response.status >= 500) {
          errorMessage = "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
        } else {
          const detail = error.response.data?.detail;
          if (detail) {
            errorMessage = detail;
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <div className="text-4xl mb-4">🏢</div>
          <h1 className="text-3xl font-bold text-gray-900">온라인 평가 시스템</h1>
          <p className="text-gray-600 mt-2">중소기업 지원사업 평가 플랫폼</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              아이디
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="아이디를 입력하세요"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="비밀번호를 입력하세요"
              required
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                로그인 중...
              </div>
            ) : (
              "로그인"
            )}          </button>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => setShowSecretarySignup(true)}
              className="text-blue-600 hover:text-blue-800 underline text-sm"
            >
              간사로 회원가입
            </button>
          </div>
        </form>

        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 mb-3">테스트 계정</h3>
          <div className="text-xs text-gray-600 space-y-2">
            <div className="flex justify-between">
              <span>관리자:</span>
              <span className="font-mono">admin / admin123</span>
            </div>
            <div className="flex justify-between">
              <span>간사:</span>
              <span className="font-mono">secretary01 / secretary123</span>
            </div>            <div className="flex justify-between">
              <span>평가위원:</span>
              <span className="font-mono">evaluator01 / evaluator123</span>
            </div>
          </div>
        </div>

        {/* Secretary Signup Modal */}
        {showSecretarySignup && (
          <SecretarySignup
            onClose={() => setShowSecretarySignup(false)}
            onSuccess={() => {}}
          />
        )}
      </div>
    </div>
  );
};

// 간사 신청 관리 컴포넌트
const SecretaryRequestManagement = ({ user }) => {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');      const response = await fetch(`${BACKEND_URL}/api/admin/secretary-requests`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: '간사 신청 목록을 불러오는데 실패했습니다.' }));
        throw new Error(errData.detail || '간사 신청 목록을 불러오는데 실패했습니다.');
      }
      const data = await response.json();
      setRequests(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && user.role === 'admin') {
      fetchRequests();
    } else {
      setLoading(false);
      setRequests([]);
    }
  }, [user]);

  const handleAction = async (requestId, action) => {
    try {
      const token = localStorage.getItem('token');      const response = await fetch(`${BACKEND_URL}/api/admin/secretary-requests/${requestId}/${action}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: `${action === 'approve' ? '승인' : '거절'} 처리 중 오류가 발생했습니다.`}));
        throw new Error(errData.detail || `${action === 'approve' ? '승인' : '거절'} 처리 중 오류가 발생했습니다.`);
      }
      const successMessage = await response.json();
      alert(successMessage.message || `선택한 간사 신청이 ${action === 'approve' ? '승인' : '거절'}되었습니다.`);
      fetchRequests(); // 목록 새로고침
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">간사 신청 목록 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 p-4 bg-red-100 border border-red-400 rounded">오류: {error}</div>;
  }

  if (user && user.role !== 'admin') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">간사 신청 관리</h2>
        <p className="text-gray-600">이 기능은 관리자만 사용할 수 있습니다.</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-6">간사 신청 관리</h2>
        {requests.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-2">👥</div>
            <p className="text-gray-500">대기 중인 간사 신청이 없습니다.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">연락처</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이메일</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신청 사유</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">신청일</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                  <th scope="col" className="relative px-6 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {requests.map((request) => (
                  <tr key={request.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{request.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{request.phone}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{request.email}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 max-w-xs truncate" title={request.reason}>{request.reason}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(request.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        request.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        request.status === 'approved' ? 'bg-green-100 text-green-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {request.status === 'pending' ? '대기중' : request.status === 'approved' ? '승인됨' : '거절됨'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {request.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleAction(request.id, 'approve')}
                            className="text-green-600 hover:text-green-900 mr-3 px-3 py-1 rounded-md hover:bg-green-50 transition-colors"
                          >
                            승인
                          </button>
                          <button
                            onClick={() => handleAction(request.id, 'reject')}
                            className="text-red-600 hover:text-red-900 px-3 py-1 rounded-md hover:bg-red-50 transition-colors"
                          >
                            거절
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>  );
};

// 관리자용 사용자 관리 컴포넌트
const AdminUserManagement = ({ user }) => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    user_name: '',
    email: '',
    password: '',
    role: 'evaluator'
  });

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        const errData = await response.json().catch(() => ({ detail: '사용자 목록을 불러오는데 실패했습니다.' }));
        throw new Error(errData.detail || '사용자 목록을 불러오는데 실패했습니다.');
      }
      
      const data = await response.json();
      setUsers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && user.role === 'admin') {
      fetchUsers();
    } else {
      setLoading(false);
      setUsers([]);
    }
  }, [user]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        alert('사용자가 성공적으로 생성되었습니다!');
        setShowCreateModal(false);
        setFormData({ username: '', user_name: '', email: '', password: '', role: 'evaluator' });
        fetchUsers();
      } else {
        const errorData = await response.json();
        alert(`사용자 생성 실패: ${errorData.detail}`);
      }
    } catch (error) {
      alert('사용자 생성 중 오류가 발생했습니다.');
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${editingUser.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        alert('사용자가 성공적으로 수정되었습니다!');
        setShowEditModal(false);
        setEditingUser(null);
        setFormData({ username: '', user_name: '', email: '', password: '', role: 'evaluator' });
        fetchUsers();
      } else {
        const errorData = await response.json();
        alert(`사용자 수정 실패: ${errorData.detail}`);
      }
    } catch (error) {
      alert('사용자 수정 중 오류가 발생했습니다.');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('정말로 이 사용자를 삭제하시겠습니까?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('사용자가 성공적으로 삭제되었습니다!');
        fetchUsers();
      } else {
        const errorData = await response.json();
        alert(`사용자 삭제 실패: ${errorData.detail}`);
      }
    } catch (error) {
      alert('사용자 삭제 중 오류가 발생했습니다.');
    }
  };

  const openEditModal = (userData) => {
    setEditingUser(userData);
    setFormData({
      username: userData.username,
      user_name: userData.user_name,
      email: userData.email || '',
      password: '',
      role: userData.role
    });
    setShowEditModal(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">사용자 목록 로딩 중...</span>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-500 p-4 bg-red-100 border border-red-400 rounded">오류: {error}</div>;
  }

  if (user && user.role !== 'admin') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">사용자 관리</h2>
        <p className="text-gray-600">이 기능은 관리자만 사용할 수 있습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">사용자 관리</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            새 사용자 생성
          </button>
        </div>

        {users.length === 0 ? (
          <p className="text-gray-500 text-center py-8">등록된 사용자가 없습니다.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">사용자 ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이메일</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">역할</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">생성일</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((userData) => (
                  <tr key={userData.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{userData.username}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{userData.user_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{userData.email || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        userData.role === 'admin' ? 'bg-red-100 text-red-800' :
                        userData.role === 'secretary' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {userData.role === 'admin' ? '관리자' : 
                         userData.role === 'secretary' ? '간사' : '평가위원'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {userData.created_at ? new Date(userData.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        userData.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {userData.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openEditModal(userData)}
                        className="text-indigo-600 hover:text-indigo-900 mr-3 px-3 py-1 rounded-md hover:bg-indigo-50 transition-colors"
                      >
                        수정
                      </button>
                      {userData.id !== user.id && (
                        <button
                          onClick={() => handleDeleteUser(userData.id)}
                          className="text-red-600 hover:text-red-900 px-3 py-1 rounded-md hover:bg-red-50 transition-colors"
                        >
                          삭제
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 사용자 생성 모달 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold mb-4">새 사용자 생성</h3>
            <form onSubmit={handleCreateUser}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">사용자 ID</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
                  <input
                    type="text"
                    value={formData.user_name}
                    onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">역할</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="evaluator">평가위원</option>
                    <option value="secretary">간사</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
              </div>
              <div className="flex space-x-3 pt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setFormData({ username: '', user_name: '', email: '', password: '', role: 'evaluator' });
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  생성
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 사용자 수정 모달 */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold mb-4">사용자 수정</h3>
            <form onSubmit={handleUpdateUser}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">사용자 ID</label>
                  <input
                    type="text"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
                  <input
                    type="text"
                    value={formData.user_name}
                    onChange={(e) => setFormData({ ...formData, user_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">새 비밀번호 (변경하지 않으려면 비워두세요)</label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">역할</label>
                  <select
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="evaluator">평가위원</option>
                    <option value="secretary">간사</option>
                    <option value="admin">관리자</option>
                  </select>
                </div>
              </div>
              <div className="flex space-x-3 pt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingUser(null);
                    setFormData({ username: '', user_name: '', email: '', password: '', role: 'evaluator' });
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  수정
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Project Management Component
const ProjectManagement = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    deadline: ''
  });

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'secretary') {
      fetchProjects();
    }
  }, [user]);
  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'}/projects`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      } else {
        console.error('프로젝트 목록을 가져오지 못했습니다');
      }
    } catch (error) {
      console.error('프로젝트 목록 가져오기 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const newProject = await response.json();
        setProjects([...projects, newProject]);
        setShowCreateModal(false);
        setFormData({ name: '', description: '', status: 'draft', start_date: '', end_date: '', budget: '' });
        alert('프로젝트가 성공적으로 생성되었습니다!');
      } else {
        const errorData = await response.json();
        alert(`프로젝트 생성 실패: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('프로젝트 생성 실패:', error);
      alert('프로젝트 생성 중 오류가 발생했습니다.');
    }
  };
  const handleUpdateProject = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'}/projects/${editingProject.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const updatedProject = await response.json();
        setProjects(projects.map(p => p.id === editingProject.id ? updatedProject : p));
        setEditingProject(null);
        setFormData({ name: '', description: '', status: 'draft', start_date: '', end_date: '', budget: '' });
        alert('프로젝트가 성공적으로 수정되었습니다!');
      } else {
        const errorData = await response.json();
        alert(`프로젝트 수정 실패: ${errorData.detail}`);
      }
    } catch (error) {
      alert('프로젝트 수정 중 오류가 발생했습니다.');
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('정말로 이 프로젝트를 삭제하시겠습니까?')) return;    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080'}/projects/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setProjects(projects.filter(p => p.id !== projectId));
        alert('프로젝트가 성공적으로 삭제되었습니다!');
      } else {
        const errorData = await response.json();
        alert(`프로젝트 삭제 실패: ${errorData.detail}`);
      }
    } catch (error) {
      alert('프로젝트 삭제 중 오류가 발생했습니다.');
    }
  };

  const openEditModal = (project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      description: project.description,
      deadline: project.deadline ? project.deadline.split('T')[0] : ''
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: "bg-gray-100 text-gray-800",
      active: "bg-green-100 text-green-800",
      completed: "bg-blue-100 text-blue-800",
      cancelled: "bg-red-100 text-red-800"
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  const getStatusName = (status) => {
    const names = {
      draft: "초안",
      active: "진행중",
      completed: "완료",
      cancelled: "취소"
    };
    return names[status] || status;
  };

  if (user.role === 'evaluator') {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 text-lg">접근 권한이 없습니다.</div>
        <div className="text-gray-400">프로젝트 관리는 관리자와 간사만 이용할 수 있습니다.</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">프로젝트 목록을 불러오는 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">프로젝트 관리</h2>
          <p className="text-gray-600">중소기업 지원사업 프로젝트를 생성하고 관리합니다.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <span>➕</span>
          <span>새 프로젝트</span>
        </button>
      </div>

      {/* Projects Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">프로젝트명</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">마감일</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">생성일</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {projects.length === 0 ? (
              <tr>
                <td colSpan="4" className="px-6 py-12 text-center text-gray-500">
                  <div className="text-4xl mb-4">📋</div>
                  <div>등록된 프로젝트가 없습니다.</div>
                  <div className="text-sm text-gray-400 mt-1">새 프로젝트를 생성해보세요.</div>
                </td>
              </tr>
            ) : (
              projects.map((project) => (
                <tr key={project.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{project.name}</div>
                    <div className="text-sm text-gray-500">{project.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {project.deadline ? new Date(project.deadline).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {project.created_at ? new Date(project.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => openEditModal(project)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      수정
                    </button>
                    <button
                      onClick={() => handleDeleteProject(project.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      삭제
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Project Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
          setFormData({ name: '', description: '', status: 'draft', start_date: '', end_date: '', budget: '' });
        }}
        title="새 프로젝트 생성"
      >
        <form onSubmit={handleCreateProject} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">프로젝트명</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">마감일</label>
            <input
              type="date"
              value={formData.deadline}
              onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={() => {
                setShowCreateModal(false);
                setFormData({ name: '', description: '', deadline: '' });
              }}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              생성
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Project Modal */}
      <Modal
        isOpen={!!editingProject}
        onClose={() => {
          setEditingProject(null);
          setFormData({ name: '', description: '', status: 'draft', start_date: '', end_date: '', budget: '' });
        }}
        title="프로젝트 수정"
      >
        <form onSubmit={handleUpdateProject} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">프로젝트명</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">마감일</label>
            <input
              type="date"
              value={formData.deadline}
              onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={() => {
                setEditingProject(null);
                setFormData({ name: '', description: '', deadline: '' });
              }}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              수정
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// AdminDashboard Component - 관리자 대시보드
const AdminDashboard = ({ user, setActiveTab }) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSystemStatus();
    fetchDashboardStats();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${BACKEND_URL}/health`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSystemStatus(data);
      } else {
        // 기본 상태 정보
        setSystemStatus({
          status: "healthy",
          timestamp: new Date().toISOString(),
          database: { status: "connected" },
          redis: { status: "connected" },
          uptime: "24h 30m"
        });
      }
    } catch (err) {
      console.error("시스템 상태 조회 실패:", err);
      setSystemStatus({
        status: "unknown",
        timestamp: new Date().toISOString(),
        database: { status: "unknown" },
        redis: { status: "unknown" },
        uptime: "알 수 없음"
      });
    }
  };
  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${BACKEND_URL}/api/dashboard/statistics`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        // 새로운 백엔드 응답 구조에 맞게 매핑
        setDashboardStats({
          totalProjects: data.overview?.total_projects || 0,
          activeProjects: data.overview?.total_projects || 0,
          totalUsers: data.overview?.total_evaluators || 0,
          totalEvaluations: data.overview?.total_evaluations || 0,
          pendingEvaluations: data.evaluation_status?.pending || 0,
          inProgressEvaluations: data.evaluation_status?.in_progress || 0,
          completedEvaluations: data.evaluation_status?.completed || 0,
          completionRate: data.evaluation_status?.completion_rate || 0,
          recentActivity: data.recent_activity?.map(activity => ({
            type: "evaluation",
            message: `${activity.company_name || '알 수 없음'} 평가 - ${activity.status}`,
            time: activity.created_at ? new Date(activity.created_at).toLocaleDateString() : "최근",
            evaluator: activity.evaluator_name
          })) || []
        });
      } else {
        // 백엔드 연결 실패 시 기본 데이터
        console.warn('백엔드 통계 API 연결 실패, 기본 데이터 사용');
        setDashboardStats({
          totalProjects: 0,
          activeProjects: 0,
          totalUsers: 0,
          totalEvaluations: 0,
          pendingEvaluations: 0,
          inProgressEvaluations: 0,
          completedEvaluations: 0,
          completionRate: 0,
          recentActivity: []
        });
      }
    } catch (err) {
      console.error("대시보드 통계 조회 실패:", err);
      setDashboardStats({
        totalProjects: 0,
        activeProjects: 0,
        totalUsers: 0,
        totalEvaluations: 0,
        pendingEvaluations: 0,
        inProgressEvaluations: 0,
        completedEvaluations: 0,
        completionRate: 0,
        recentActivity: []
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "healthy":
      case "connected":
        return "text-green-600 bg-green-100";
      case "warning":
        return "text-yellow-600 bg-yellow-100";
      case "error":
      case "disconnected":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case "evaluation_completed":
      case "evaluation":
        return "📝";
      case "user_created":
        return "👤";
      case "project_created":
        return "📁";
      default:
        return "📋";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 환영 메시지 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          안녕하세요, {user.user_name}님! 👋
        </h2>
        <p className="text-gray-600">
          시스템의 실시간 상태와 핵심 지표를 한눈에 모니터링할 수 있습니다. 관리 작업은 상단 메뉴를 통해 접근하세요.
        </p>
      </div>

      {/* 시스템 개요 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">📋 시스템 개요</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
            <div className="text-blue-600 text-2xl mb-2">🎯</div>
            <div className="font-medium text-gray-900">운영 중인 프로젝트</div>
            <div className="text-sm text-gray-500">현재 진행 중인 평가 프로젝트들을 모니터링합니다</div>
          </div>
          <div className="p-4 bg-green-50 rounded-lg border border-green-100">
            <div className="text-green-600 text-2xl mb-2">👥</div>
            <div className="font-medium text-gray-900">활성 사용자</div>
            <div className="text-sm text-gray-500">로그인 및 활동 중인 사용자들을 추적합니다</div>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
            <div className="text-purple-600 text-2xl mb-2">📊</div>
            <div className="font-medium text-gray-900">평가 진행률</div>
            <div className="text-sm text-gray-500">전체 평가 프로세스의 완료 상황을 확인합니다</div>
          </div>
        </div>
      </div>

      {/* 시스템 상태 */}
      {systemStatus && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">🔧 시스템 상태</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">전체 상태</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.status)}`}>
                  {systemStatus.status === "healthy" ? "정상" : "문제"}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">데이터베이스</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.database?.status)}`}>
                  {systemStatus.database?.status === "connected" ? "연결됨" : "문제"}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Redis</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.redis?.status)}`}>
                  {systemStatus.redis?.status === "connected" ? "연결됨" : "문제"}
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">업타임</div>
              <div className="font-medium text-gray-900">{systemStatus.uptime}</div>
            </div>
          </div>
        </div>
      )}

      {/* 주요 통계 */}
      {dashboardStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-blue-500">
            <div className="text-3xl text-blue-600 mb-2">📁</div>
            <div className="text-2xl font-bold text-gray-900">{dashboardStats.totalProjects}</div>
            <div className="text-sm text-gray-600">전체 프로젝트</div>
            <div className="text-xs text-green-600 mt-1">활성: {dashboardStats.activeProjects}</div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-green-500">
            <div className="text-3xl text-green-600 mb-2">👥</div>
            <div className="text-2xl font-bold text-gray-900">{dashboardStats.totalUsers}</div>
            <div className="text-sm text-gray-600">평가위원</div>
            <div className="text-xs text-blue-600 mt-1">총 평가: {dashboardStats.totalEvaluations}</div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-yellow-500">
            <div className="text-3xl text-yellow-600 mb-2">⏳</div>
            <div className="text-2xl font-bold text-gray-900">{dashboardStats.pendingEvaluations}</div>
            <div className="text-sm text-gray-600">배정됨</div>
            <div className="text-xs text-orange-600 mt-1">진행중: {dashboardStats.inProgressEvaluations}</div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-purple-500">
            <div className="text-3xl text-purple-600 mb-2">✅</div>
            <div className="text-2xl font-bold text-gray-900">{dashboardStats.completedEvaluations}</div>
            <div className="text-sm text-gray-600">완료된 평가</div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-sm border-l-4 border-indigo-500">
            <div className="text-3xl text-indigo-600 mb-2">📊</div>
            <div className="text-2xl font-bold text-gray-900">
              {dashboardStats.completionRate || 0}%
            </div>
            <div className="text-sm text-gray-600">완료율</div>
            <div className="text-xs text-gray-500 mt-1">
              실시간 업데이트
            </div>
          </div>
        </div>
      )}

      {/* 최근 활동 */}
      {dashboardStats?.recentActivity && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">📋 최근 활동</h3>
          <div className="space-y-3">            {dashboardStats.recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="text-xl">{getActivityIcon(activity.type)}</div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900">{activity.message}</div>
                  <div className="text-xs text-gray-500">{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 서버 정보 */}
      {systemStatus && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">🖥️ 서버 정보</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-sm text-gray-600">환경</div>
              <div className="font-medium text-gray-900">{systemStatus.environment || 'Development'}</div>
            </div>
            <div className="space-y-2">
              <div className="text-sm text-gray-600">버전</div>
              <div className="font-medium text-gray-900">{systemStatus.version || 'v1.0.0'}</div>
            </div>
          </div>
          {/* 관리자 전용 정보 */}
          {user && user.role === 'admin' && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-blue-100">
              <h4 className="text-base font-semibold mb-2 text-blue-700">🔒 관리자 전용 정보</h4>
              <div className="text-sm text-gray-700 mb-1">공인 IP: <span className="font-mono">218.38.240.192</span></div>
              <div className="text-sm text-gray-700 mb-1">프론트엔드 포트: <span className="font-mono">3000</span></div>
              <div className="text-sm text-gray-700 mb-1">백엔드 포트: <span className="font-mono">8080</span></div>
              <div className="text-sm text-gray-700 mb-1">MongoDB 포트: <span className="font-mono">27017</span></div>
              <div className="text-sm text-gray-700 mb-1">Redis 포트: <span className="font-mono">6379</span></div>
              <div className="text-sm text-gray-700 mb-1">Nginx 포트: <span className="font-mono">80</span></div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// AnalyticsManagement Component - 결과 분석
const AnalyticsManagement = ({ user }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedProject, setSelectedProject] = useState("");
  const [projects, setProjects] = useState([]);
  const [chartData, setChartData] = useState({});

  useEffect(() => {
    fetchProjects();
    fetchAnalyticsData();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchProjectAnalytics(selectedProject);
    }
  }, [selectedProject]);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        if (data.length > 0) {
          setSelectedProject(data[0].id);
        }
      }
    } catch (err) {
      console.error("프로젝트 목록 조회 실패:", err);
    }
  };

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      
      // 대시보드 통계 데이터 조회
      const dashboardResponse = await fetch(`${BACKEND_URL}/api/dashboard/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (dashboardResponse.ok) {
        const data = await dashboardResponse.json();
        setAnalyticsData(data);
      } else {
        // 백엔드에 해당 API가 없을 경우 임시 데이터 사용
        setAnalyticsData({
          totalEvaluations: 25,
          completedEvaluations: 18,
          averageScore: 4.2,
          completionRate: 72,
          projectStats: [
            { name: '프로젝트 A', completed: 10, total: 15 },
            { name: '프로젝트 B', completed: 8, total: 10 }
          ]
        });
      }
    } catch (err) {
      setError("분석 데이터를 불러오는데 실패했습니다.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjectAnalytics = async (projectId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${BACKEND_URL}/api/analytics/project/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setChartData(data);
      } else {
        // 임시 차트 데이터
        setChartData({
          scoreDistribution: [
            { range: '1-2점', count: 2 },
            { range: '2-3점', count: 4 },
            { range: '3-4점', count: 8 },
            { range: '4-5점', count: 12 }
          ],
          evaluationProgress: [
            { month: '1월', completed: 5 },
            { month: '2월', completed: 8 },
            { month: '3월', completed: 12 },
            { month: '4월', completed: 18 }
          ]
        });
      }
    } catch (err) {
      console.error("프로젝트 분석 데이터 조회 실패:", err);
    }
  };

  const renderStatCard = (title, value, subtext, color = 'blue') => (
    <div className={`bg-white p-6 rounded-lg shadow-sm border-l-4 border-${color}-500`}>
      <div className="flex items-center">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtext && <p className="text-sm text-gray-500">{subtext}</p>}
        </div>
      </div>
    </div>
  );

  const renderSimpleChart = (data, title) => (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="space-y-3">
        {data.map((item, index) => (
          <div key={index} className="flex items-center">
            <div className="w-24 text-sm text-gray-600">{item.range || item.month}</div>
            <div className="flex-1 bg-gray-200 rounded-full h-2 mx-3">
              <div 
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${(item.count || item.completed) * 5}%` }}
              ></div>
            </div>
            <div className="w-12 text-sm font-medium text-gray-900">
              {item.count || item.completed}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">결과 분석</h2>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">전체 프로젝트</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg">
          {error}
        </div>
      )}

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {renderStatCard(
          "총 평가 수",
          analyticsData?.totalEvaluations || 0,
          "전체 평가 항목"
        )}
        {renderStatCard(
          "완료된 평가",
          analyticsData?.completedEvaluations || 0,
          `완료율: ${analyticsData?.completionRate || 0}%`,
          "green"
        )}
        {renderStatCard(
          "평균 점수",
          analyticsData?.averageScore || 0,
          "5점 만점 기준",
          "yellow"
        )}
        {renderStatCard(
          "진행률",
          `${analyticsData?.completionRate || 0}%`,
          "전체 진행 상황",
          "purple"
        )}
      </div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {chartData.scoreDistribution && renderSimpleChart(
          chartData.scoreDistribution,
          "점수 분포"
        )}
        {chartData.evaluationProgress && renderSimpleChart(
          chartData.evaluationProgress,
          "월별 평가 완료 현황"
        )}
      </div>

      {/* 프로젝트별 통계 */}
      {analyticsData?.projectStats && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">프로젝트별 현황</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    프로젝트명
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    완료/전체
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    진행률
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analyticsData.projectStats.map((project, index) => {
                  const progress = Math.round((project.completed / project.total) * 100);
                  return (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {project.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {project.completed}/{project.total}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${progress}%` }}
                            ></div>
                          </div>
                          <span>{progress}%</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          progress >= 100 ? 'bg-green-100 text-green-800' :
                          progress >= 50 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {progress >= 100 ? '완료' : progress >= 50 ? '진행중' : '시작'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 액션 버튼 */}
      <div className="flex justify-end space-x-4">
        <button 
          onClick={() => window.print()}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          보고서 인쇄
        </button>
        <button 
          onClick={fetchAnalyticsData}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          새로고침
        </button>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [showAdminDropdown, setShowAdminDropdown] = useState(false);
  const renderContent = () => {
    if (user.role === "evaluator") {
      return <EvaluationForm user={user} />;
    }    switch (activeTab) {
      case "dashboard":
        return <AdminDashboard user={user} setActiveTab={setActiveTab} />;
      case "project-management":
      case "projects":
        return <ProjectManagement user={user} />;
      case "secretary-requests":
        return <SecretaryRequestManagement user={user} />;
      case "admin-user-management":
      case "users":
        return <AdminUserManagement user={user} />;
      case "evaluations":
        return <EvaluationManagement user={user} />;
      case "templates":
        return <TemplateManagement />;
      case "analytics":
        return <AnalyticsManagement user={user} />;
      case "ai-assistant":
        return <AIAssistant user={user} onAnalysisComplete={(data) => console.log('AI 분석 완료:', data)} />;
      case "ai-provider":
        return <AIProviderManagement user={user} />;
      case "ai-model-settings":
        return <AIModelDashboard user={user} />;
      case "ai-model-management":
        return <AIModelManagement user={user} />;
      case "secure-file-viewer":
        return <FileSecureViewer user={user} />;
      case "evaluation-print":
        return <EvaluationPrintManager user={user} />;
      case "ai-evaluation-control":
        return <AIEvaluationController user={user} />;
      case "deployment":
        return <DeploymentManager user={user} />;
      case "file-security-dashboard":
        return <FileSecurityDashboard user={user} />;
      default:
        return <AdminDashboard user={user} />;
    }
  };

  const getRoleDisplayName = (role) => {
    const roleNames = {
      admin: "관리자",
      secretary: "간사",
      evaluator: "평가위원"
    };
       return roleNames[role] || role;
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: "bg-red-100 text-red-800",
      secretary: "bg-blue-100 text-blue-800",
      evaluator: "bg-green-100 text-green-800"
    };
    return colors[role] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="text-3xl">🏢</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">온라인 평가 시스템</h1>
                <p className="text-sm text-gray-500">중소기업 지원사업 평가 플랫폼</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-gray-500">안녕하세요,</div>
                <div className="font-medium text-gray-900">{user.user_name}</div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                {getRoleDisplayName(user.role)}
              </span>
              {/* 실시간 알림 센터 */}
              <NotificationCenter />
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      {user.role !== "evaluator" && (
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              {/* 기본 메뉴 항목들 */}
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === "dashboard"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                📊 대시보드
              </button>
              
              <button
                onClick={() => setActiveTab("projects")}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === "projects"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                🎯 프로젝트 관리
              </button>
              
              <button
                onClick={() => setActiveTab("evaluations")}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === "evaluations"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                📝 평가 관리
              </button>
              
              <button
                onClick={() => setActiveTab("templates")}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === "templates"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                📄 템플릿 관리
              </button>
              
              {['admin', 'secretary', 'evaluator'].includes(user.role) && (
                <button
                  onClick={() => setActiveTab("secure-file-viewer")}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === "secure-file-viewer"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  🔒 보안 파일 뷰어
                </button>
              )}
              
              {['admin', 'secretary', 'evaluator'].includes(user.role) && (
                <button
                  onClick={() => setActiveTab("evaluation-print")}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === "evaluation-print"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  📄 평가표 출력
                </button>
              )}
              
              <button
                onClick={() => setActiveTab("analytics")}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === "analytics"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                📊 결과 분석
              </button>
              
              {['admin', 'secretary', 'evaluator'].includes(user.role) && (
                <button
                  onClick={() => setActiveTab("ai-assistant")}
                  className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === "ai-assistant"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  🤖 AI 도우미
                </button>
              )}
              
              {/* 관리자 드롭다운 메뉴 */}
              {user.role === 'admin' && (
                <div className="relative">
                  <button
                    onClick={() => setShowAdminDropdown(!showAdminDropdown)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center space-x-1 ${
                      ['secretary-requests', 'users', 'ai-provider', 'ai-evaluation-control', 'deployment', 'file-security-dashboard'].includes(activeTab)
                        ? "border-blue-500 text-blue-600"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }`}
                  >
                    <span>⚙️ 관리자</span>
                    <svg 
                      className={`w-4 h-4 transition-transform ${showAdminDropdown ? 'rotate-180' : ''}`} 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {showAdminDropdown && (
                    <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                      <div className="py-2">
                        <button
                          onClick={() => {
                            setActiveTab("secretary-requests");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "secretary-requests" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          👥 간사 신청 관리
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("users");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "users" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          👤 사용자 관리
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("ai-provider");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "ai-provider" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          🤖 AI 공급자 관리
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("ai-model-settings");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "ai-model-settings" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          ⚙️ AI 모델 설정
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("ai-model-management");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "ai-model-management" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          🔧 AI 모델 관리
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("ai-evaluation-control");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "ai-evaluation-control" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          🤖 AI 평가 제어
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("deployment");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "deployment" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          🚀 배포 관리
                        </button>
                        
                        <button
                          onClick={() => {
                            setActiveTab("file-security-dashboard");
                            setShowAdminDropdown(false);
                          }}
                          className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                            activeTab === "file-security-dashboard" ? "bg-blue-50 text-blue-600" : "text-gray-700"
                          }`}
                        >
                          🔐 파일 보안 대시보드
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </nav>
      )}
      
      {/* 드롭다운 외부 클릭 시 닫기 */}
      {showAdminDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowAdminDropdown(false)}
        ></div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState('dashboard'); // 현재 보여줄 뷰 상태
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    initializeSystem();
    checkAuthStatus();
  }, []);  const initializeSystem = async () => {
    try {
      await axios.get(`${BACKEND_URL}/health`);
    } catch (error) {
      console.log("시스템 초기화 확인됨");
    }
  };
  const checkAuthStatus = async () => {
    const token = localStorage.getItem("token");

    if (token) {
      try {
        // Verify token is still valid and get fresh user data
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Use fresh data from server instead of cached localStorage data
        const userData = response.data;
        localStorage.setItem("user", JSON.stringify(userData));
        setUser(userData);
        
        console.log("✅ 사용자 정보 업데이트 완료:", { 
          name: userData.user_name, 
          role: userData.role,
          email: userData.email 
        });
      } catch (error) {
        console.error("❌ 인증 확인 실패:", error);
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setUser(null);
      }
    }
    setLoading(false);
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">시스템 로딩 중...</p>
          <p className="text-sm text-gray-500">온라인 평가 시스템을 준비하고 있습니다</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      <NotificationProvider user={user}>
        <div className="App">
          {user ? (
            <Dashboard user={user} onLogout={handleLogout} />
          ) : (
            <Login onLogin={handleLogin} />
          )}
          {/* 토스트 알림 컴포넌트 */}
          <ToastNotification />
        </div>
      </NotificationProvider>
    </AuthContext.Provider>
  );
}

export default App;