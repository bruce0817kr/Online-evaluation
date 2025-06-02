import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Document, Page, pdfjs } from 'react-pdf';

// PDF.js worker setup
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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

// PDF 새창 열기 함수
const openPDFInNewWindow = async (fileId, filename) => {
  try {
    const response = await axios.get(`${API}/files/${fileId}/preview`, {
      responseType: 'blob',
      // 권한 체크 제거 - 누구나 PDF 볼 수 있도록
    });
    
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    
    const newWindow = window.open(url, '_blank', 'width=1000,height=800,scrollbars=yes,resizable=yes');
    if (newWindow) {
      newWindow.document.title = filename || 'PDF 문서';
    }
  } catch (error) {
    console.error('PDF 열기 실패:', error);
    alert('PDF 파일을 열 수 없습니다.');
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
      const response = await axios.post(`${API}/auth/secretary-signup`, {
        name: formData.name,
        phone: normalizePhoneNumber(formData.phone),
        email: formData.email,
        reason: formData.reason
      });

      alert("간사 회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인이 가능합니다.");
      onSuccess();
      onClose();
    } catch (error) {
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
  const [showSecretarySignup, setShowSecretarySignup] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", credentials.username);
      formData.append("password", credentials.password);

      const response = await axios.post(`${API}/auth/token`, formData);
      const { access_token, user } = response.data;
      
      localStorage.setItem("token", access_token);
      localStorage.setItem("user", JSON.stringify(user));
      onLogin(user);
    } catch (error) {
      setError("로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.");
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
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/secretary-requests', {
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
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/secretary-requests/${requestId}/${action}`, {
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
    </div>
  );
};

// Enhanced Admin Dashboard Component
const AdminDashboard = ({ user }) => {
  const [stats, setStats] = useState({
    projects: 0,
    companies: 0,
    evaluators: 0,
    total_evaluations: 0,
    completed_evaluations: 0,
    completion_rate: 0
  });
  const [recentProjects, setRecentProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/dashboard/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data.stats);
      setRecentProjects(response.data.recent_projects);
    } catch (error) {
      console.error("대시보드 데이터 조회 실패:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">대시보드 로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Statistics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="진행 중인 프로젝트"
          value={stats.projects}
          icon="📊"
          color="blue"
        />
        <StatCard
          title="참여 기업"
          value={stats.companies}
          icon="🏢"
          color="green"
        />
        <StatCard
          title="평가위원"
          value={stats.evaluators}
          icon="👥"
          color="purple"
        />
      </div>

      {/* Evaluation Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-6">평가 진행 현황</h3>
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">전체 평가</span>
              <span className="text-2xl font-bold text-gray-900">{stats.total_evaluations}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">완료된 평가</span>
              <span className="text-2xl font-bold text-green-600">{stats.completed_evaluations}</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">완료율</span>
              <span className="text-2xl font-bold text-blue-600">{stats.completion_rate}%</span>
            </div>
            
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-500">
                <span>진행률</span>
                <span>{stats.completed_evaluations} / {stats.total_evaluations}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500" 
                  style={{ width: `${stats.completion_rate}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-6">최근 프로젝트</h3>
          <div className="space-y-4">
            {recentProjects.map((project) => (
              <div key={project.id} className="flex justify-between items-center py-3 border-b border-gray-100 last:border-b-0">
                <div>
                  <div className="font-medium text-gray-900">{project.name}</div>
                  <div className="text-sm text-gray-500">
                    마감: {new Date(project.deadline).toLocaleDateString()}
                  </div>
                </div>
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                  진행중
                </span>
              </div>
            ))}
            
            {recentProjects.length === 0 && (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">📋</div>
                <p className="text-gray-500">프로젝트가 없습니다.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-4">시스템 상태</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">데이터베이스 연결</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">파일 저장소</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span className="text-gray-600">인증 서비스</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState("dashboard");

  const renderContent = () => {
    if (user.role === "evaluator") {
      return <EvaluationForm user={user} />;
    }    switch (activeTab) {
      case "dashboard":
        return <AdminDashboard user={user} />;
      case "projects":
        return <ProjectManagement user={user} />;
      case "secretary-requests":
        return <SecretaryRequestManagement user={user} />;
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
                }`}              >
                🎯 프로젝트 관리
              </button>
              <button
                onClick={() => setActiveTab("secretary-requests")}
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  activeTab === "secretary-requests"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                👥 간사 신청 관리
              </button>
            </div>
          </div>
        </nav>
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

  useEffect(() => {
    initializeSystem();
    checkAuthStatus();
  }, []);

  const initializeSystem = async () => {
    try {
      await axios.get(`${API}/health`);
      await axios.post(`${API}/init`);
    } catch (error) {
      console.log("시스템 초기화 확인됨");
    }
  };

  const checkAuthStatus = async () => {
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");

    if (token && savedUser) {
      try {
        // Verify token is still valid
        await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(JSON.parse(savedUser));
      } catch (error) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
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
      <div className="App">
        {user ? (
          <Dashboard user={user} onLogout={handleLogout} />
        ) : (
          <Login onLogin={handleLogin} />
        )}
      </div>
    </AuthContext.Provider>
  );
}

export default App;