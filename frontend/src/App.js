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

// Login Component
const Login = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", credentials.username);
      formData.append("password", credentials.password);

      const response = await axios.post(`${API}/auth/login`, formData);
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
            )}
          </button>
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
            </div>
            <div className="flex justify-between">
              <span>평가위원:</span>
              <span className="font-mono">evaluator01 / evaluator123</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Project Management Component
const ProjectManagement = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [evaluators, setEvaluators] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  
  // Modal states
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
  const [isEvaluatorModalOpen, setIsEvaluatorModalOpen] = useState(false);
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [isAssignmentModalOpen, setIsAssignmentModalOpen] = useState(false);
  const [isAnalyticsModalOpen, setIsAnalyticsModalOpen] = useState(false);
  const [isBatchEvaluatorModalOpen, setIsBatchEvaluatorModalOpen] = useState(false);
  
  const [selectedProject, setSelectedProject] = useState("");
  const [newCredentials, setNewCredentials] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});

  // Form states
  const [projectForm, setProjectForm] = useState({
    name: "",
    description: "",
    deadline: ""
  });

  const [companyForm, setCompanyForm] = useState({
    name: "",
    business_number: "",
    address: "",
    contact_person: "",
    phone: "",
    email: "",
    project_id: ""
  });

  const [evaluatorForm, setEvaluatorForm] = useState({
    user_name: "",
    phone: "",
    email: ""
  });

  const [batchEvaluatorForm, setBatchEvaluatorForm] = useState([
    { user_name: "", phone: "", email: "" }
  ]);

  const [templateForm, setTemplateForm] = useState({
    name: "",
    description: "",
    items: [{ name: "", description: "", max_score: 100, weight: 1.0 }]
  });

  const [assignmentForm, setAssignmentForm] = useState({
    evaluator_ids: [],
    company_ids: [],
    template_id: "",
    deadline: ""
  });

  useEffect(() => {
    fetchProjects();
    fetchEvaluators();
  }, []);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (error) {
      console.error("프로젝트 조회 실패:", error);
    }
  };

  const fetchCompanies = async (projectId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/companies?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompanies(response.data);
    } catch (error) {
      console.error("기업 조회 실패:", error);
    }
  };

  const fetchEvaluators = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/evaluators`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEvaluators(response.data);
    } catch (error) {
      console.error("평가위원 조회 실패:", error);
    }
  };

  const fetchTemplates = async (projectId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/templates?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplates(response.data);
    } catch (error) {
      console.error("평가표 조회 실패:", error);
    }
  };

  const fetchAnalytics = async (projectId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/analytics/project/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
      setIsAnalyticsModalOpen(true);
    } catch (error) {
      console.error("분석 데이터 조회 실패:", error);
    }
  };

  const handleProjectSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      await axios.post(`${API}/projects`, projectForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsProjectModalOpen(false);
      setProjectForm({ name: "", description: "", deadline: "" });
      fetchProjects();
      alert("프로젝트가 성공적으로 생성되었습니다.");
    } catch (error) {
      console.error("프로젝트 생성 실패:", error);
      alert("프로젝트 생성에 실패했습니다.");
    }
  };

  const handleCompanySubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      await axios.post(`${API}/companies`, companyForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsCompanyModalOpen(false);
      setCompanyForm({
        name: "",
        business_number: "",
        address: "",
        contact_person: "",
        phone: "",
        email: "",
        project_id: ""
      });
      if (selectedProject) {
        fetchCompanies(selectedProject);
      }
      alert("기업이 성공적으로 등록되었습니다.");
    } catch (error) {
      console.error("기업 등록 실패:", error);
      alert("기업 등록에 실패했습니다.");
    }
  };

  const handleEvaluatorSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(`${API}/evaluators`, evaluatorForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNewCredentials({
        name: evaluatorForm.user_name,
        login_id: response.data.generated_login_id,
        password: response.data.generated_password
      });
      
      setEvaluatorForm({ user_name: "", phone: "", email: "" });
      fetchEvaluators();
    } catch (error) {
      console.error("평가위원 생성 실패:", error);
      alert("평가위원 생성에 실패했습니다.");
    }
  };

  const handleBatchEvaluatorSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(`${API}/evaluators/batch`, batchEvaluatorForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsBatchEvaluatorModalOpen(false);
      setBatchEvaluatorForm([{ user_name: "", phone: "", email: "" }]);
      fetchEvaluators();
      
      alert(`${response.data.created_count}명의 평가위원이 생성되었습니다. 오류: ${response.data.error_count}건`);
    } catch (error) {
      console.error("일괄 평가위원 생성 실패:", error);
      alert("일괄 평가위원 생성에 실패했습니다.");
    }
  };

  const addBatchEvaluator = () => {
    setBatchEvaluatorForm([...batchEvaluatorForm, { user_name: "", phone: "", email: "" }]);
  };

  const removeBatchEvaluator = (index) => {
    const newForm = batchEvaluatorForm.filter((_, i) => i !== index);
    setBatchEvaluatorForm(newForm);
  };

  const updateBatchEvaluator = (index, field, value) => {
    const newForm = [...batchEvaluatorForm];
    newForm[index][field] = value;
    setBatchEvaluatorForm(newForm);
  };

  const handleTemplateSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      await axios.post(`${API}/templates?project_id=${selectedProject}`, templateForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsTemplateModalOpen(false);
      setTemplateForm({
        name: "",
        description: "",
        items: [{ name: "", description: "", max_score: 100, weight: 1.0 }]
      });
      fetchTemplates(selectedProject);
      alert("평가표가 성공적으로 생성되었습니다.");
    } catch (error) {
      console.error("평가표 생성 실패:", error);
      alert("평가표 생성에 실패했습니다.");
    }
  };

  const handleAssignmentSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(`${API}/assignments`, assignmentForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsAssignmentModalOpen(false);
      setAssignmentForm({
        evaluator_ids: [],
        company_ids: [],
        template_id: "",
        deadline: ""
      });
      alert(response.data.message);
    } catch (error) {
      console.error("평가 할당 실패:", error);
      alert("평가 할당에 실패했습니다.");
    }
  };

  const addTemplateItem = () => {
    setTemplateForm({
      ...templateForm,
      items: [...templateForm.items, { name: "", description: "", max_score: 100, weight: 1.0 }]
    });
  };

  const removeTemplateItem = (index) => {
    const newItems = templateForm.items.filter((_, i) => i !== index);
    setTemplateForm({ ...templateForm, items: newItems });
  };

  const updateTemplateItem = (index, field, value) => {
    const newItems = [...templateForm.items];
    newItems[index][field] = value;
    setTemplateForm({ ...templateForm, items: newItems });
  };

  const handleProjectSelect = (projectId) => {
    setSelectedProject(projectId);
    fetchCompanies(projectId);
    fetchTemplates(projectId);
  };

  const handleFileUpload = async (files, companyId) => {
    for (const file of files) {
      const formData = new FormData();
      formData.append('company_id', companyId);
      formData.append('file', file);

      try {
        setUploadProgress({ [file.name]: 0 });
        
        const token = localStorage.getItem("token");
        await axios.post(`${API}/upload`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = (progressEvent.loaded / progressEvent.total) * 100;
            setUploadProgress({ [file.name]: progress });
          }
        });

        setUploadProgress({ [file.name]: 100 });
        setTimeout(() => setUploadProgress({}), 2000);
        
        if (selectedProject) {
          fetchCompanies(selectedProject);
        }
      } catch (error) {
        console.error("파일 업로드 실패:", error);
        alert(`파일 업로드 실패: ${file.name}`);
        setUploadProgress({});
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">프로젝트 관리</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <button
            onClick={() => setIsProjectModalOpen(true)}
            className="flex flex-col items-center p-4 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <span className="text-2xl mb-2">📋</span>
            <span className="text-sm font-medium">프로젝트 생성</span>
          </button>
          
          <button
            onClick={() => setIsCompanyModalOpen(true)}
            disabled={!selectedProject}
            className="flex flex-col items-center p-4 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-2xl mb-2">🏢</span>
            <span className="text-sm font-medium">기업 등록</span>
          </button>
          
          <button
            onClick={() => setIsEvaluatorModalOpen(true)}
            className="flex flex-col items-center p-4 bg-purple-50 text-purple-600 rounded-lg hover:bg-purple-100 transition-colors"
          >
            <span className="text-2xl mb-2">👤</span>
            <span className="text-sm font-medium">평가위원 추가</span>
          </button>
          
          <button
            onClick={() => setIsBatchEvaluatorModalOpen(true)}
            className="flex flex-col items-center p-4 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors"
          >
            <span className="text-2xl mb-2">👥</span>
            <span className="text-sm font-medium">일괄 평가위원</span>
          </button>
          
          <button
            onClick={() => setIsTemplateModalOpen(true)}
            disabled={!selectedProject}
            className="flex flex-col items-center p-4 bg-orange-50 text-orange-600 rounded-lg hover:bg-orange-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-2xl mb-2">📄</span>
            <span className="text-sm font-medium">평가표 생성</span>
          </button>
          
          <button
            onClick={() => setIsAssignmentModalOpen(true)}
            disabled={!selectedProject}
            className="flex flex-col items-center p-4 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="text-2xl mb-2">📌</span>
            <span className="text-sm font-medium">평가 할당</span>
          </button>
        </div>
      </div>

      {/* Project Selection */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">프로젝트 선택</h3>
          {selectedProject && (
            <button
              onClick={() => fetchAnalytics(selectedProject)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              📊 분석 보기
            </button>
          )}
        </div>
        <select
          value={selectedProject}
          onChange={(e) => handleProjectSelect(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">프로젝트를 선택하세요</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name} (마감: {new Date(project.deadline).toLocaleDateString()})
            </option>
          ))}
        </select>
      </div>

      {/* Companies List with File Upload */}
      {selectedProject && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-4">참여 기업 및 파일 관리</h3>
          <div className="space-y-4">
            {companies.map((company) => (
              <div key={company.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-semibold text-lg">{company.name}</h4>
                    <p className="text-sm text-gray-600">
                      담당자: {company.contact_person} | 연락처: {company.phone}
                    </p>
                    <p className="text-sm text-gray-600">
                      사업자번호: {company.business_number}
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    파일 {company.files?.length || 0}개
                  </span>
                </div>
                
                {/* File Upload Zone */}
                <div className="mb-4">
                  <FileUploadZone
                    multiple={true}
                    onFileSelect={(files) => handleFileUpload(files, company.id)}
                  />
                  
                  {/* Upload Progress */}
                  {Object.entries(uploadProgress).map(([filename, progress]) => (
                    <div key={filename} className="mt-2">
                      <ProgressBar progress={progress} filename={filename} />
                    </div>
                  ))}
                </div>
                
                {/* Uploaded Files */}
                {company.files && company.files.length > 0 && (
                  <div>
                    <h5 className="font-medium mb-2">업로드된 파일</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                      {company.files.map((file, index) => (
                        <div key={index} className="flex items-center p-2 bg-gray-50 rounded border">
                          <span className="text-xl mr-2">📄</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              {file.original_filename || file.filename || file}
                            </p>
                            <p className="text-xs text-gray-500">
                              {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : ''}
                            </p>
                          </div>
                          {file.id && (
                            <button
                              onClick={() => window.open(`${API}/files/${file.id}`, '_blank')}
                              className="ml-2 px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              보기
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Modals */}
      
      {/* Project Creation Modal */}
      <Modal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        title="새 프로젝트 생성"
      >
        <form onSubmit={handleProjectSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로젝트명 *
            </label>
            <input
              type="text"
              value={projectForm.name}
              onChange={(e) => setProjectForm({...projectForm, name: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="2025년 중소기업 디지털 전환 지원사업"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로젝트 설명 *
            </label>
            <textarea
              value={projectForm.description}
              onChange={(e) => setProjectForm({...projectForm, description: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="프로젝트의 목적과 내용을 상세히 설명해주세요"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로젝트 마감일 *
            </label>
            <input
              type="datetime-local"
              value={projectForm.deadline}
              onChange={(e) => setProjectForm({...projectForm, deadline: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsProjectModalOpen(false)}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              프로젝트 생성
            </button>
          </div>
        </form>
      </Modal>

      {/* Company Registration Modal */}
      <Modal
        isOpen={isCompanyModalOpen}
        onClose={() => setIsCompanyModalOpen(false)}
        title="기업 등록"
      >
        <form onSubmit={handleCompanySubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              프로젝트 선택 *
            </label>
            <select
              value={companyForm.project_id}
              onChange={(e) => setCompanyForm({...companyForm, project_id: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">프로젝트를 선택하세요</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                기업명 *
              </label>
              <input
                type="text"
                value={companyForm.name}
                onChange={(e) => setCompanyForm({...companyForm, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="(주)혁신테크"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                사업자번호 *
              </label>
              <input
                type="text"
                value={companyForm.business_number}
                onChange={(e) => setCompanyForm({...companyForm, business_number: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="123-45-67890"
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              기업 주소 *
            </label>
            <input
              type="text"
              value={companyForm.address}
              onChange={(e) => setCompanyForm({...companyForm, address: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="서울시 강남구 테헤란로 123"
              required
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                담당자명 *
              </label>
              <input
                type="text"
                value={companyForm.contact_person}
                onChange={(e) => setCompanyForm({...companyForm, contact_person: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="김대표"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                연락처 *
              </label>
              <input
                type="text"
                value={companyForm.phone}
                onChange={(e) => setCompanyForm({...companyForm, phone: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="02-1234-5678"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일 *
              </label>
              <input
                type="email"
                value={companyForm.email}
                onChange={(e) => setCompanyForm({...companyForm, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="ceo@company.com"
                required
              />
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsCompanyModalOpen(false)}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              기업 등록
            </button>
          </div>
        </form>
      </Modal>

      {/* Evaluator Creation Modal */}
      <Modal
        isOpen={isEvaluatorModalOpen}
        onClose={() => {
          setIsEvaluatorModalOpen(false);
          setNewCredentials(null);
        }}
        title="평가위원 추가"
      >
        {newCredentials ? (
          <div className="text-center space-y-6">
            <div className="text-green-600 text-xl font-semibold flex items-center justify-center">
              <span className="text-3xl mr-3">✅</span>
              평가위원이 성공적으로 생성되었습니다!
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="space-y-3">
                <div className="flex justify-between">
                  <strong>이름:</strong>
                  <span>{newCredentials.name}</span>
                </div>
                <div className="flex justify-between">
                  <strong>아이디:</strong>
                  <span className="font-mono bg-gray-100 px-2 py-1 rounded">{newCredentials.login_id}</span>
                </div>
                <div className="flex justify-between">
                  <strong>비밀번호:</strong>
                  <span className="font-mono bg-gray-100 px-2 py-1 rounded">{newCredentials.password}</span>
                </div>
              </div>
            </div>
            <div className="text-sm text-gray-600 bg-blue-50 p-4 rounded">
              <p className="font-semibold mb-2">📋 중요 안내</p>
              <p>위 로그인 정보를 평가위원에게 안전하게 전달해주세요.</p>
              <p>보안을 위해 첫 로그인 후 비밀번호 변경을 권장합니다.</p>
            </div>
            <button
              onClick={() => {
                setIsEvaluatorModalOpen(false);
                setNewCredentials(null);
              }}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              확인
            </button>
          </div>
        ) : (
          <form onSubmit={handleEvaluatorSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                평가위원 이름 (한글) *
              </label>
              <input
                type="text"
                value={evaluatorForm.user_name}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, user_name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="홍길동"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                전화번호 (하이픈 제외) *
              </label>
              <input
                type="text"
                value={evaluatorForm.phone}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, phone: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="01012345678"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이메일 *
              </label>
              <input
                type="email"
                value={evaluatorForm.email}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="evaluator@email.com"
                required
              />
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <span className="text-blue-600 text-xl mr-3">💡</span>
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">자동 계정 생성 안내</p>
                  <p>• 아이디: 이름 + 전화번호 뒤 4자리</p>
                  <p>• 비밀번호: 전화번호 뒤 8자리</p>
                  <p>• 예시: 홍길동, 01012345678 → 아이디: 홍길동5678, 비밀번호: 12345678</p>
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setIsEvaluatorModalOpen(false)}
                className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                취소
              </button>
              <button
                type="submit"
                className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
              >
                평가위원 추가
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* Batch Evaluator Creation Modal */}
      <Modal
        isOpen={isBatchEvaluatorModalOpen}
        onClose={() => setIsBatchEvaluatorModalOpen(false)}
        title="평가위원 일괄 추가"
        size="lg"
      >
        <form onSubmit={handleBatchEvaluatorSubmit} className="space-y-6">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <span className="text-yellow-600 text-xl mr-3">⚡</span>
              <div className="text-sm text-yellow-800">
                <p className="font-semibold mb-1">일괄 추가 기능</p>
                <p>여러 명의 평가위원을 한 번에 추가할 수 있습니다. 각 평가위원의 정보를 정확히 입력해주세요.</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {batchEvaluatorForm.map((evaluator, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-medium">평가위원 #{index + 1}</h4>
                  {batchEvaluatorForm.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeBatchEvaluator(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      삭제
                    </button>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      이름 *
                    </label>
                    <input
                      type="text"
                      value={evaluator.user_name}
                      onChange={(e) => updateBatchEvaluator(index, 'user_name', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="홍길동"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      전화번호 *
                    </label>
                    <input
                      type="text"
                      value={evaluator.phone}
                      onChange={(e) => updateBatchEvaluator(index, 'phone', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="01012345678"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      이메일 *
                    </label>
                    <input
                      type="email"
                      value={evaluator.email}
                      onChange={(e) => updateBatchEvaluator(index, 'email', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="evaluator@email.com"
                      required
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center">
            <button
              type="button"
              onClick={addBatchEvaluator}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              + 평가위원 추가
            </button>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsBatchEvaluatorModalOpen(false)}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              일괄 생성 ({batchEvaluatorForm.length}명)
            </button>
          </div>
        </form>
      </Modal>

      {/* Template Creation Modal */}
      <Modal
        isOpen={isTemplateModalOpen}
        onClose={() => setIsTemplateModalOpen(false)}
        title="평가표 생성"
        size="lg"
      >
        <form onSubmit={handleTemplateSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                평가표명 *
              </label>
              <input
                type="text"
                value={templateForm.name}
                onChange={(e) => setTemplateForm({...templateForm, name: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="디지털 전환 평가표"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                평가표 설명
              </label>
              <input
                type="text"
                value={templateForm.description}
                onChange={(e) => setTemplateForm({...templateForm, description: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="평가표의 목적과 특징을 간단히 설명"
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-4">
              <label className="block text-sm font-medium text-gray-700">
                평가 항목 *
              </label>
              <button
                type="button"
                onClick={addTemplateItem}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                + 항목 추가
              </button>
            </div>
            
            <div className="space-y-4">
              {templateForm.items.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="font-medium text-gray-900">평가항목 #{index + 1}</h4>
                    {templateForm.items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTemplateItem(index)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        삭제
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        항목명 *
                      </label>
                      <input
                        type="text"
                        placeholder="예: 기술성, 시장성, 사업성"
                        value={item.name}
                        onChange={(e) => updateTemplateItem(index, 'name', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          최고점수 *
                        </label>
                        <input
                          type="number"
                          value={item.max_score}
                          onChange={(e) => updateTemplateItem(index, 'max_score', parseInt(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          min="1"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          가중치 *
                        </label>
                        <input
                          type="number"
                          value={item.weight}
                          onChange={(e) => updateTemplateItem(index, 'weight', parseFloat(e.target.value))}
                          className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          min="0"
                          step="0.1"
                          required
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      항목 설명
                    </label>
                    <textarea
                      placeholder="이 평가 항목의 세부 기준과 내용을 설명해주세요"
                      value={item.description}
                      onChange={(e) => updateTemplateItem(index, 'description', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows={2}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <span className="text-blue-600 text-xl mr-3">💡</span>
              <div className="text-sm text-blue-800">
                <p className="font-semibold mb-1">평가표 작성 가이드</p>
                <p>• 가중치가 높을수록 최종 점수에 더 큰 영향을 미칩니다</p>
                <p>• 평가 항목은 명확하고 구체적으로 작성해주세요</p>
                <p>• 최고점수는 일반적으로 100점으로 설정합니다</p>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsTemplateModalOpen(false)}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              평가표 생성
            </button>
          </div>
        </form>
      </Modal>

      {/* Assignment Modal */}
      <Modal
        isOpen={isAssignmentModalOpen}
        onClose={() => setIsAssignmentModalOpen(false)}
        title="평가 할당"
        size="lg"
      >
        <form onSubmit={handleAssignmentSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              평가표 선택 *
            </label>
            <select
              value={assignmentForm.template_id}
              onChange={(e) => setAssignmentForm({...assignmentForm, template_id: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              <option value="">평가표를 선택하세요</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name} ({template.items?.length || 0}개 항목)
                </option>
              ))}
            </select>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                평가위원 선택 * (복수 선택 가능)
              </label>
              <div className="border border-gray-300 rounded-lg p-3 max-h-40 overflow-y-auto bg-gray-50">
                {evaluators.map((evaluator) => (
                  <label key={evaluator.id} className="flex items-center space-x-3 py-2 hover:bg-white rounded px-2">
                    <input
                      type="checkbox"
                      checked={assignmentForm.evaluator_ids.includes(evaluator.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setAssignmentForm({
                            ...assignmentForm,
                            evaluator_ids: [...assignmentForm.evaluator_ids, evaluator.id]
                          });
                        } else {
                          setAssignmentForm({
                            ...assignmentForm,
                            evaluator_ids: assignmentForm.evaluator_ids.filter(id => id !== evaluator.id)
                          });
                        }
                      }}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <span className="text-sm font-medium">{evaluator.user_name}</span>
                      <span className="text-xs text-gray-500 block">{evaluator.email}</span>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                선택됨: {assignmentForm.evaluator_ids.length}명
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                기업 선택 * (복수 선택 가능)
              </label>
              <div className="border border-gray-300 rounded-lg p-3 max-h-40 overflow-y-auto bg-gray-50">
                {companies.map((company) => (
                  <label key={company.id} className="flex items-center space-x-3 py-2 hover:bg-white rounded px-2">
                    <input
                      type="checkbox"
                      checked={assignmentForm.company_ids.includes(company.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setAssignmentForm({
                            ...assignmentForm,
                            company_ids: [...assignmentForm.company_ids, company.id]
                          });
                        } else {
                          setAssignmentForm({
                            ...assignmentForm,
                            company_ids: assignmentForm.company_ids.filter(id => id !== company.id)
                          });
                        }
                      }}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <span className="text-sm font-medium">{company.name}</span>
                      <span className="text-xs text-gray-500 block">{company.business_number}</span>
                    </div>
                  </label>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                선택됨: {assignmentForm.company_ids.length}개 기업
              </p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              평가 마감일 (선택사항)
            </label>
            <input
              type="datetime-local"
              value={assignmentForm.deadline}
              onChange={(e) => setAssignmentForm({...assignmentForm, deadline: e.target.value})}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start">
              <span className="text-green-600 text-xl mr-3">📊</span>
              <div className="text-sm text-green-800">
                <p className="font-semibold mb-1">할당 예상 결과</p>
                <p>총 {assignmentForm.evaluator_ids.length * assignmentForm.company_ids.length}개의 평가가 생성됩니다.</p>
                <p>({assignmentForm.evaluator_ids.length}명 평가위원 × {assignmentForm.company_ids.length}개 기업)</p>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={() => setIsAssignmentModalOpen(false)}
              className="px-6 py-3 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              평가 할당
            </button>
          </div>
        </form>
      </Modal>

      {/* Analytics Modal */}
      <Modal
        isOpen={isAnalyticsModalOpen}
        onClose={() => setIsAnalyticsModalOpen(false)}
        title="프로젝트 분석 리포트"
        size="xl"
      >
        {analytics && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <StatCard
                title="전체 기업"
                value={analytics.total_companies}
                icon="🏢"
                color="blue"
              />
              <StatCard
                title="평가 완료"
                value={analytics.companies_evaluated}
                icon="✅"
                color="green"
              />
              <StatCard
                title="총 평가수"
                value={analytics.total_evaluations}
                icon="📊"
                color="purple"
              />
              <StatCard
                title="완료율"
                value={`${analytics.completion_rate}%`}
                icon="📈"
                color="orange"
              />
            </div>

            {Object.keys(analytics.score_analytics).length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-4">평가표별 점수 분석</h3>
                <div className="space-y-4">
                  {Object.entries(analytics.score_analytics).map(([templateName, scores]) => (
                    <div key={templateName} className="bg-gray-50 rounded-lg p-4">
                      <h4 className="font-medium mb-3">{templateName}</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{scores.average.toFixed(1)}</div>
                          <div className="text-sm text-gray-600">평균 점수</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{scores.max}</div>
                          <div className="text-sm text-gray-600">최고 점수</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-red-600">{scores.min}</div>
                          <div className="text-sm text-gray-600">최저 점수</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">{scores.count}</div>
                          <div className="text-sm text-gray-600">평가 건수</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

// Enhanced Evaluation Component for Evaluators
const EvaluationForm = ({ user }) => {
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [scores, setScores] = useState({});
  const [saving, setSaving] = useState(false);
  const [autoSaving, setAutoSaving] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);

  useEffect(() => {
    fetchAssignments();
  }, []);

  // Auto-save functionality
  useEffect(() => {
    if (selectedAssignment && Object.keys(scores).length > 0) {
      const timer = setTimeout(() => {
        autoSaveEvaluation();
      }, 5000); // Auto-save every 5 seconds

      return () => clearTimeout(timer);
    }
  }, [scores, selectedAssignment]);

  const fetchAssignments = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/dashboard/evaluator`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAssignments(response.data);
    } catch (error) {
      console.error("할당된 평가 조회 실패:", error);
    }
  };

  const loadEvaluation = async (assignment) => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/evaluation/${assignment.sheet.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSelectedAssignment(assignment);
      setEvaluationData(response.data);
      
      // Load existing scores
      const existingScores = {};
      response.data.scores.forEach(score => {
        existingScores[score.item_id] = {
          score: score.score,
          opinion: score.opinion
        };
      });
      setScores(existingScores);
    } catch (error) {
      console.error("평가 데이터 로드 실패:", error);
      alert("평가 데이터를 불러오는데 실패했습니다.");
    }
  };

  const handleScoreChange = (itemId, field, value) => {
    setScores(prev => ({
      ...prev,
      [itemId]: {
        ...prev[itemId],
        [field]: value
      }
    }));
  };

  const autoSaveEvaluation = async () => {
    if (!evaluationData || autoSaving) return;
    
    setAutoSaving(true);
    try {
      const token = localStorage.getItem("token");
      const scoresArray = evaluationData.template.items.map(item => ({
        item_id: item.id,
        score: scores[item.id]?.score || 0,
        opinion: scores[item.id]?.opinion || ""
      }));

      await axios.post(`${API}/evaluation/save`, {
        sheet_id: evaluationData.sheet.id,
        scores: scoresArray
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error) {
      console.error("자동 저장 실패:", error);
    } finally {
      setAutoSaving(false);
    }
  };

  const saveEvaluation = async (isSubmit = false) => {
    setSaving(true);
    try {
      const token = localStorage.getItem("token");
      const scoresArray = evaluationData.template.items.map(item => ({
        item_id: item.id,
        score: scores[item.id]?.score || 0,
        opinion: scores[item.id]?.opinion || ""
      }));

      const endpoint = isSubmit ? "/evaluation/submit" : "/evaluation/save";
      await axios.post(`${API}${endpoint}`, {
        sheet_id: evaluationData.sheet.id,
        scores: scoresArray
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert(isSubmit ? "평가가 성공적으로 제출되었습니다." : "평가가 임시저장되었습니다.");
      
      if (isSubmit) {
        setSelectedAssignment(null);
        setEvaluationData(null);
        setScores({});
        fetchAssignments();
      }
    } catch (error) {
      console.error("평가 저장 실패:", error);
      alert("평가 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const calculateTotalScore = () => {
    if (!evaluationData?.template?.items) return 0;
    
    let totalWeightedScore = 0;
    let totalWeight = 0;
    
    evaluationData.template.items.forEach(item => {
      const score = scores[item.id]?.score || 0;
      totalWeightedScore += score * item.weight;
      totalWeight += item.weight;
    });
    
    return totalWeight > 0 ? (totalWeightedScore / totalWeight).toFixed(1) : 0;
  };

  if (selectedAssignment && evaluationData) {
    const isSubmitted = evaluationData.sheet.status === "submitted";
    
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => {
                setSelectedAssignment(null);
                setEvaluationData(null);
                setScores({});
                setSelectedFileId(null);
              }}
              className="flex items-center text-blue-600 hover:text-blue-800 font-medium"
            >
              ← 목록으로 돌아가기
            </button>
            
            <div className="flex items-center space-x-4">
              {autoSaving && (
                <span className="text-sm text-green-600 flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600 mr-2"></div>
                  자동 저장 중...
                </span>
              )}
              
              {!isSubmitted && (
                <div className="flex space-x-3">
                  <button
                    onClick={() => saveEvaluation(false)}
                    disabled={saving}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
                  >
                    {saving ? "저장 중..." : "임시저장"}
                  </button>
                  <button
                    onClick={() => saveEvaluation(true)}
                    disabled={saving}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {saving ? "제출 중..." : "최종제출"}
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Company Information */}
            <div>
              <h2 className="text-xl font-semibold mb-4">{evaluationData.project.name}</h2>
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <strong>기업명:</strong> {evaluationData.company.name}
                </div>
                <div>
                  <strong>담당자:</strong> {evaluationData.company.contact_person}
                </div>
                <div>
                  <strong>연락처:</strong> {evaluationData.company.phone}
                </div>
                <div>
                  <strong>상태:</strong>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    isSubmitted ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {isSubmitted ? '제출 완료' : '평가 중'}
                  </span>
                </div>
                
                {/* Score Summary */}
                <div className="border-t pt-3 mt-3">
                  <div className="text-sm text-gray-600">가중 평균 점수</div>
                  <div className="text-2xl font-bold text-blue-600">{calculateTotalScore()}점</div>
                </div>
              </div>
            </div>

            {/* File Viewer */}
            <div className="lg:col-span-2">
              {evaluationData.company.files && evaluationData.company.files.length > 0 ? (
                <div>
                  <h3 className="font-semibold mb-3">제출 파일</h3>
                  
                  {/* File Tabs */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {evaluationData.company.files.map((file, index) => (
                      <button
                        key={index}
                        onClick={() => setSelectedFileId(file.id)}
                        className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                          selectedFileId === file.id
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        📄 {file.original_filename || file.filename || `파일 ${index + 1}`}
                      </button>
                    ))}
                  </div>
                  
                  {/* File Viewer */}
                  {selectedFileId ? (
                    <PDFViewer 
                      fileId={selectedFileId} 
                      filename={evaluationData.company.files.find(f => f.id === selectedFileId)?.original_filename || "파일"}
                    />
                  ) : (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
                      파일을 선택하여 미리보기를 확인하세요
                    </div>
                  )}
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center text-gray-500">
                  제출된 파일이 없습니다
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Evaluation Form */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="font-semibold mb-6 text-lg">평가 항목</h3>
          <div className="space-y-6">
            {evaluationData.template.items.map((item, index) => (
              <div key={item.id} className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="font-medium text-lg">{index + 1}. {item.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <div>최고점수: {item.max_score}점</div>
                    <div>가중치: {item.weight}</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      점수 (0-{item.max_score}점) *
                    </label>
                    <input
                      type="number"
                      min="0"
                      max={item.max_score}
                      value={scores[item.id]?.score || ""}
                      onChange={(e) => handleScoreChange(item.id, 'score', parseInt(e.target.value) || 0)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-xl font-bold"
                      disabled={isSubmitted}
                      placeholder="0"
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      평가 의견 *
                    </label>
                    <textarea
                      value={scores[item.id]?.opinion || ""}
                      onChange={(e) => handleScoreChange(item.id, 'opinion', e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows={4}
                      disabled={isSubmitted}
                      placeholder="상세한 평가 근거와 의견을 작성해주세요..."
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-6">할당된 평가 과제</h2>
        
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <StatCard
            title="진행 중"
            value={assignments.filter(a => a.sheet.status === 'draft').length}
            icon="📝"
            color="blue"
          />
          <StatCard
            title="완료"
            value={assignments.filter(a => a.sheet.status === 'submitted').length}
            icon="✅"
            color="green"
          />
          <StatCard
            title="마감 임박"
            value={assignments.filter(a => {
              const deadline = new Date(a.sheet.deadline || a.project.deadline);
              const today = new Date();
              const diffDays = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
              return diffDays <= 3 && a.sheet.status === 'draft';
            }).length}
            icon="⏰"
            color="yellow"
          />
        </div>
        
        {/* Assignment List */}
        <div className="space-y-4">
          {assignments.map((assignment) => (
            <div key={assignment.sheet.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-900">{assignment.project.name}</h3>
                  <p className="text-gray-600 mt-1">{assignment.company.name}</p>
                  <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                    <span>📅 마감: {new Date(assignment.sheet.deadline || assignment.project.deadline).toLocaleDateString()}</span>
                    <span>📋 {assignment.template.name}</span>
                    <span>📄 파일 {assignment.company.files?.length || 0}개</span>
                  </div>
                </div>
                
                <div className="text-right ml-6">
                  <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                    assignment.sheet.status === 'submitted' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {assignment.sheet.status === 'submitted' ? '제출 완료' : '평가 중'}
                  </span>
                  
                  <div className="mt-3">
                    <button 
                      onClick={() => loadEvaluation(assignment)}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      {assignment.sheet.status === 'submitted' ? '결과 보기' : '평가하기'}
                    </button>
                  </div>
                </div>
              </div>
              
              {assignment.company.files && assignment.company.files.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex flex-wrap gap-2">
                    {assignment.company.files.map((file, index) => (
                      <span key={index} className="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                        📄 {file.original_filename || file.filename || `파일 ${index + 1}`}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {assignments.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">할당된 평가 과제가 없습니다</h3>
              <p className="text-gray-500">새로운 평가 과제가 할당되면 여기에 표시됩니다.</p>
            </div>
          )}
        </div>
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
        <span className="ml-3 text-gray-600">대시보드 로딩 중...</span>
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
    }

    switch (activeTab) {
      case "dashboard":
        return <AdminDashboard user={user} />;
      case "projects":
        return <ProjectManagement user={user} />;
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
                }`}
              >
                🎯 프로젝트 관리
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