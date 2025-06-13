# 온라인 평가 시스템 프론트엔드 설계 가이드

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [기술 스택 분석](#기술-스택-분석)
3. [API 엔드포인트 및 데이터 구조](#api-엔드포인트-및-데이터-구조)
4. [프론트엔드 아키텍처](#프론트엔드-아키텍처)
5. [컴포넌트 설계](#컴포넌트-설계)
6. [상태 관리](#상태-관리)
7. [API 서비스 레이어](#api-서비스-레이어)
8. [에러 처리 및 로딩 상태](#에러-처리-및-로딩-상태)
9. [보안 고려사항](#보안-고려사항)
10. [UI/UX 가이드라인](#ui-ux-가이드라인)
11. [성능 최적화](#성능-최적화)
12. [테스트 전략](#테스트-전략)

---

## 시스템 개요

온라인 평가 시스템은 다음과 같은 핵심 기능을 제공합니다:

- **다중 역할 사용자 관리**: 관리자, 간사, 평가위원
- **평가 템플릿 관리**: 동적 평가 항목 생성 및 관리
- **프로젝트 기반 조직화**: 팀 배정 및 권한 관리
- **실시간 평가 진행**: 진행률 추적 및 분석
- **고급 분석 및 리포팅**: 대시보드 및 내보내기 기능

---

## 기술 스택 분석

### Backend
- **FastAPI** (Python 3.12+)
- **MongoDB** (NoSQL 데이터베이스)
- **Redis** (캐싱 및 세션 관리)
- **JWT** (인증 토큰)

### Frontend (현재 구현)
- **React 19** (컴포넌트 기반 UI)
- **JavaScript ES6+** (모던 JavaScript)
- **Chart.js** (데이터 시각화)
- **Tailwind CSS** (유틸리티 CSS 프레임워크)

### 개발 도구
- **Docker** (컨테이너화)
- **WebSocket** (실시간 통신)
- **File Upload/Download** (비동기 파일 처리)

---

## API 엔드포인트 및 데이터 구조

### 1. 인증 시스템

#### 로그인
```http
POST /api/auth/login
Content-Type: multipart/form-data

Request:
username: string
password: string

Response:
{
  "access_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "string",
    "login_id": "string",
    "user_name": "string",
    "email": "string",
    "phone": "string?",
    "role": "admin" | "secretary" | "evaluator",
    "created_at": "string",
    "is_active": boolean,
    "last_login": "string?"
  }
}
```

#### 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {token}

Response: UserResponse
```

#### 간사 회원가입 신청
```http
POST /api/auth/secretary-signup

Request:
{
  "name": "string",
  "phone": "string",
  "email": "string",
  "reason": "string"
}
```

### 2. 사용자 관리

#### 사용자 목록 조회
```http
GET /api/users
Authorization: Bearer {token}

Response: UserResponse[]
```

#### 사용자 생성
```http
POST /api/users
Authorization: Bearer {token}

Request:
{
  "login_id": "string",
  "password": "string",
  "user_name": "string",
  "email": "string",
  "role": "string",
  "phone": "string?"
}

Response: UserResponse
```

#### 평가위원 생성 (자동 ID/PW 생성)
```http
POST /api/evaluators
Authorization: Bearer {token}

Request:
{
  "user_name": "string",
  "phone": "string",
  "email": "string"
}

Response:
{
  ...UserResponse,
  "generated_login_id": "string",
  "generated_password": "string",
  "message": "string"
}
```

#### 평가위원 일괄 생성
```http
POST /api/evaluators/batch
Authorization: Bearer {token}

Request:
{
  "evaluators": [
    {
      "user_name": "string",
      "phone": "string", 
      "email": "string"
    }
  ]
}
```

### 3. 프로젝트 관리

#### 프로젝트 목록 조회
```http
GET /api/projects
Authorization: Bearer {token}

Response:
[
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "deadline": "string",
    "created_by": "string",
    "created_at": "string",
    "is_active": boolean,
    "total_companies": number,
    "total_evaluations": number,
    "completed_evaluations": number
  }
]
```

#### 프로젝트 생성
```http
POST /api/projects
Authorization: Bearer {token}

Request:
{
  "name": "string",
  "description": "string",
  "deadline": "string"
}

Response: Project
```

### 4. 기업 관리

#### 기업 목록 조회
```http
GET /api/companies?project_id={id}
Authorization: Bearer {token}

Response: Company[]
```

#### 기업 생성
```http
POST /api/companies
Authorization: Bearer {token}

Request:
{
  "name": "string",
  "project_id": "string",
  "description": "string?"
}

Response: Company
```

### 5. 평가 템플릿

#### 템플릿 목록 조회
```http
GET /api/templates?project_id={id}
Authorization: Bearer {token}

Response:
[
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "project_id": "string",
    "items": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "score_type": "string",
        "max_score": number,
        "weight": number
      }
    ],
    "created_by": "string",
    "created_at": "string",
    "is_active": boolean
  }
]
```

#### 템플릿 생성
```http
POST /api/templates?project_id={id}
Authorization: Bearer {token}

Request:
{
  "name": "string",
  "description": "string",
  "items": [
    {
      "title": "string",
      "description": "string",
      "score_type": "string",
      "max_score": number,
      "weight": number
    }
  ]
}

Response: EvaluationTemplate
```

### 6. 평가 배정 및 수행

#### 평가 배정
```http
POST /api/assignments
Authorization: Bearer {token}

Request:
{
  "evaluator_ids": ["string"],
  "company_ids": ["string"],
  "template_id": "string",
  "deadline": "string?"
}

Response:
{
  "message": "string",
  "count": number
}
```

#### 평가 시트 조회
```http
GET /api/evaluation/{sheet_id}
Authorization: Bearer {token}

Response:
{
  "sheet": {
    "id": "string",
    "evaluator_id": "string",
    "company_id": "string",
    "project_id": "string",
    "template_id": "string",
    "status": "draft" | "submitted",
    "scores": [],
    "total_score": number?,
    "submitted_at": "string?",
    "deadline": "string?"
  },
  "company": Company,
  "project": Project,
  "template": EvaluationTemplate
}
```

#### 평가 제출
```http
POST /api/evaluation/submit
Authorization: Bearer {token}

Request:
{
  "sheet_id": "string",
  "scores": [
    {
      "item_id": "string",
      "score": number,
      "comment": "string?"
    }
  ],
  "overall_comment": "string?"
}

Response:
{
  "message": "string",
  "total_score": number
}
```

#### 평가 임시저장
```http
POST /api/evaluation/save
Authorization: Bearer {token}

Request: EvaluationSubmission

Response:
{
  "message": "string"
}
```

### 7. 대시보드 및 분석

#### 관리자 대시보드
```http
GET /api/dashboard/admin
Authorization: Bearer {token}

Response:
{
  "stats": {
    "projects": number,
    "companies": number,
    "evaluators": number,
    "total_evaluations": number,
    "completed_evaluations": number,
    "completion_rate": number
  },
  "recent_projects": Project[]
}
```

#### 평가위원 대시보드
```http
GET /api/dashboard/evaluator
Authorization: Bearer {token}

Response:
[
  {
    "sheet": EvaluationSheet,
    "company": Company,
    "project": Project,
    "template": EvaluationTemplate
  }
]
```

#### 프로젝트 분석
```http
GET /api/analytics/project/{project_id}
Authorization: Bearer {token}

Response:
{
  "project_id": "string",
  "total_companies": number,
  "companies_evaluated": number,
  "total_evaluations": number,
  "completion_rate": number,
  "score_analytics": {
    "[template_name]": {
      "average": number,
      "min": number,
      "max": number,
      "count": number
    }
  }
}
```

### 8. 파일 관리

#### 파일 업로드
```http
POST /api/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

Request:
company_id: string
file: File

Response:
{
  "id": "string",
  "filename": "string",
  "original_filename": "string",
  "file_path": "string",
  "file_size": number,
  "file_type": "string",
  "uploaded_by": "string",
  "uploaded_at": "string",
  "company_id": "string",
  "is_processed": boolean
}
```

#### 파일 다운로드
```http
GET /api/files/{file_id}
Authorization: Bearer {token}

Response: File Stream
```

#### 파일 미리보기
```http
GET /api/files/{file_id}/preview

Response: File Content (권한 체크 없음)
```

### 9. 내보내기 기능

#### 단일 평가 내보내기
```http
GET /api/evaluations/{evaluation_id}/export?format=pdf|excel
Authorization: Bearer {token}

Response: File Stream
```

#### 일괄 내보내기
```http
POST /api/evaluations/bulk-export
Authorization: Bearer {token}

Request:
{
  "evaluation_ids": ["string"],
  "format": "pdf" | "excel",
  "options": {}
}

Response: ZIP File Stream
```

#### 내보내기 가능한 평가 목록
```http
GET /api/evaluations/export-list?project_id={id}&template_id={id}
Authorization: Bearer {token}

Response: ExportableEvaluation[]
```

### 10. 관리자 기능

#### 간사 신청 목록 조회
```http
GET /api/admin/secretary-requests
Authorization: Bearer {token}

Response: SecretaryApproval[]
```

#### 간사 신청 승인/거부
```http
POST /api/admin/secretary-requests/{request_id}/{action}
Authorization: Bearer {token}

Action: "approve" | "reject"
```

---

## 프론트엔드 아키텍처

### 디렉토리 구조
```
src/
├── components/           # 재사용 가능한 컴포넌트
│   ├── common/          # 공통 컴포넌트
│   ├── forms/           # 폼 컴포넌트
│   ├── charts/          # 차트 컴포넌트
│   └── layout/          # 레이아웃 컴포넌트
├── pages/               # 페이지 컴포넌트
│   ├── Dashboard/
│   ├── Projects/
│   ├── Evaluations/
│   ├── Analytics/
│   ├── Users/
│   └── Templates/
├── services/            # API 서비스
│   ├── api.js          # API 클라이언트
│   ├── auth.js         # 인증 서비스
│   └── websocket.js    # WebSocket 서비스
├── hooks/               # 커스텀 훅
│   ├── useApi.js       # API 호출 훅
│   ├── useAuth.js      # 인증 훅
│   └── useWebSocket.js # WebSocket 훅
├── context/             # React Context
│   ├── AuthContext.js  # 인증 컨텍스트
│   └── AppContext.js   # 앱 전역 상태
├── utils/               # 유틸리티 함수
│   ├── constants.js    # 상수 정의
│   ├── helpers.js      # 헬퍼 함수
│   └── validators.js   # 입력 검증
└── assets/             # 정적 자원
    ├── styles/         # CSS 파일
    └── images/         # 이미지 파일
```

---

## 컴포넌트 설계

### 1. 라우팅 구조
```javascript
const AppRoutes = {
  LOGIN: "/login",
  DASHBOARD: "/dashboard",
  PROJECTS: "/projects",
  PROJECT_DETAIL: "/projects/:id",
  EVALUATIONS: "/evaluations",
  EVALUATION_FORM: "/evaluations/:sheetId",
  ANALYTICS: "/analytics",
  USER_MANAGEMENT: "/users",
  TEMPLATES: "/templates",
  TEMPLATE_EDITOR: "/templates/editor",
  FILE_MANAGEMENT: "/files"
};
```

### 2. 핵심 컴포넌트

#### Dashboard Component
```javascript
// 역할별 대시보드
const Dashboard = ({ user }) => {
  const [dashboardData, setDashboardData] = useState(null);
  
  useEffect(() => {
    const fetchDashboard = async () => {
      const endpoint = user.role === 'evaluator' 
        ? '/api/dashboard/evaluator'
        : '/api/dashboard/admin';
      
      const data = await apiClient.get(endpoint);
      setDashboardData(data);
    };
    
    fetchDashboard();
  }, [user.role]);

  if (user.role === 'evaluator') {
    return <EvaluatorDashboard data={dashboardData} />;
  }
  
  return <AdminDashboard data={dashboardData} />;
};
```

#### ProjectManagement Component
```javascript
const ProjectManagement = () => {
  const [projects, setProjects] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  const { data, loading, error, execute } = useApiCall(
    () => apiClient.get('/api/projects')
  );
  
  useEffect(() => {
    execute();
  }, []);
  
  const handleCreateProject = async (projectData) => {
    await apiClient.post('/api/projects', projectData);
    execute(); // 목록 새로고침
  };
  
  return (
    <div>
      <ProjectList projects={projects} />
      {showCreateModal && (
        <ProjectCreateModal 
          onSubmit={handleCreateProject}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
};
```

#### EvaluationForm Component
```javascript
const EvaluationForm = ({ sheetId }) => {
  const [evaluationData, setEvaluationData] = useState(null);
  const [scores, setScores] = useState({});
  const [isDraft, setIsDraft] = useState(true);
  
  useEffect(() => {
    const fetchEvaluation = async () => {
      const data = await apiClient.get(`/api/evaluation/${sheetId}`);
      setEvaluationData(data);
      
      // 기존 점수 로드
      if (data.sheet.scores) {
        const scoreMap = {};
        data.sheet.scores.forEach(score => {
          scoreMap[score.item_id] = score;
        });
        setScores(scoreMap);
      }
    };
    
    fetchEvaluation();
  }, [sheetId]);
  
  const handleScoreChange = (itemId, score, comment) => {
    setScores(prev => ({
      ...prev,
      [itemId]: { item_id: itemId, score, comment }
    }));
  };
  
  const handleSave = async () => {
    const submission = {
      sheet_id: sheetId,
      scores: Object.values(scores)
    };
    
    await apiClient.post('/api/evaluation/save', submission);
    // 성공 피드백
  };
  
  const handleSubmit = async () => {
    const submission = {
      sheet_id: sheetId,
      scores: Object.values(scores)
    };
    
    await apiClient.post('/api/evaluation/submit', submission);
    setIsDraft(false);
    // 제출 완료 피드백
  };
  
  if (!evaluationData) return <LoadingSpinner />;
  
  return (
    <div className="evaluation-form">
      <EvaluationHeader 
        company={evaluationData.company}
        project={evaluationData.project}
        template={evaluationData.template}
      />
      
      <EvaluationItems 
        items={evaluationData.template.items}
        scores={scores}
        onScoreChange={handleScoreChange}
      />
      
      <EvaluationActions 
        onSave={handleSave}
        onSubmit={handleSubmit}
        isDraft={isDraft}
      />
    </div>
  );
};
```

#### AnalyticsView Component
```javascript
const AnalyticsView = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [selectedProject, setSelectedProject] = useState('');
  const [projects, setProjects] = useState([]);
  
  useEffect(() => {
    const fetchProjects = async () => {
      const data = await apiClient.get('/api/projects');
      setProjects(data);
      if (data.length > 0) {
        setSelectedProject(data[0].id);
      }
    };
    
    fetchProjects();
  }, []);
  
  useEffect(() => {
    if (selectedProject) {
      const fetchAnalytics = async () => {
        const data = await apiClient.get(`/api/analytics/project/${selectedProject}`);
        setAnalyticsData(data);
      };
      
      fetchAnalytics();
    }
  }, [selectedProject]);
  
  return (
    <div className="analytics-view">
      <ProjectSelector 
        projects={projects}
        selected={selectedProject}
        onChange={setSelectedProject}
      />
      
      {analyticsData && (
        <>
          <AnalyticsOverview data={analyticsData} />
          <ScoreAnalyticsChart data={analyticsData.score_analytics} />
          <CompletionRateChart rate={analyticsData.completion_rate} />
        </>
      )}
    </div>
  );
};
```

---

## 상태 관리

### Context API 활용
```javascript
// AuthContext.js
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    checkAuthStatus();
  }, []);
  
  const checkAuthStatus = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const userData = await apiClient.get('/api/auth/me');
        setUser(userData);
      } catch (error) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  };
  
  const login = async (credentials) => {
    const response = await apiClient.post('/api/auth/login', credentials);
    const { access_token, user } = response;
    
    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(user));
    setUser(user);
    
    return user;
  };
  
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      checkAuthStatus
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### AppContext for Global State
```javascript
// AppContext.js
const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [notifications, setNotifications] = useState([]);
  
  const addNotification = (notification) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { ...notification, id }]);
    
    // 자동 제거 (5초 후)
    setTimeout(() => {
      removeNotification(id);
    }, 5000);
  };
  
  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };
  
  return (
    <AppContext.Provider value={{
      projects,
      setProjects,
      selectedProject,
      setSelectedProject,
      notifications,
      addNotification,
      removeNotification
    }}>
      {children}
    </AppContext.Provider>
  );
};
```

---

## API 서비스 레이어

### API Client
```javascript
// services/api.js
class ApiClient {
  constructor() {
    this.baseURL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8080';
  }
  
  getHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json'
    };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: this.getHeaders(),
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response;
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }
  
  async get(endpoint) {
    return this.request(endpoint);
  }
  
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }
  
  async uploadFile(endpoint, formData) {
    const token = localStorage.getItem('token');
    
    return this.request(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
        // Content-Type은 자동으로 설정됨 (multipart/form-data)
      },
      body: formData
    });
  }
  
  async downloadFile(endpoint) {
    const response = await this.request(endpoint);
    return response.blob();
  }
}

export const apiClient = new ApiClient();
```

### Authentication Service
```javascript
// services/auth.js
export const authService = {
  async login(credentials) {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await fetch(`${apiClient.baseURL}/api/auth/login`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '로그인 실패');
    }
    
    return response.json();
  },
  
  async getMe() {
    return apiClient.get('/api/auth/me');
  },
  
  async requestSecretarySignup(data) {
    return apiClient.post('/api/auth/secretary-signup', data);
  }
};
```

---

## 에러 처리 및 로딩 상태

### Custom Hook for API Calls
```javascript
// hooks/useApi.js
export const useApiCall = (apiCall, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, dependencies);
  
  return { data, loading, error, execute };
};
```

### Error Boundary Component
```javascript
// components/common/ErrorBoundary.js
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>문제가 발생했습니다</h2>
          <p>페이지를 새로고침하거나 나중에 다시 시도해주세요.</p>
          <button onClick={() => window.location.reload()}>
            새로고침
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

### Loading Component
```javascript
// components/common/LoadingSpinner.js
const LoadingSpinner = ({ message = "로딩 중..." }) => (
  <div className="loading-spinner">
    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto"></div>
    <p className="mt-4 text-gray-600 font-medium">{message}</p>
  </div>
);
```

---

## 보안 고려사항

### 1. JWT 토큰 관리
```javascript
// utils/tokenManager.js
export const tokenManager = {
  getToken() {
    return localStorage.getItem('token');
  },
  
  setToken(token) {
    localStorage.setItem('token', token);
  },
  
  removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  
  isTokenExpired(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      return payload.exp < now;
    } catch {
      return true;
    }
  },
  
  shouldRefreshToken(token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Date.now() / 1000;
      const timeUntilExpiry = payload.exp - now;
      return timeUntilExpiry < 300; // 5분 이내 만료
    } catch {
      return false;
    }
  }
};
```

### 2. 권한 기반 라우팅
```javascript
// components/common/ProtectedRoute.js
const ProtectedRoute = ({ children, roles = [] }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  if (roles.length > 0 && !roles.includes(user.role)) {
    return (
      <div className="unauthorized">
        <h2>접근 권한이 없습니다</h2>
        <p>이 페이지에 접근할 권한이 없습니다.</p>
      </div>
    );
  }
  
  return children;
};
```

### 3. 입력 검증
```javascript
// utils/validators.js
export const validators = {
  email: (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
  },
  
  phone: (phone) => {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length >= 10 && cleaned.length <= 11;
  },
  
  password: (password) => {
    return password.length >= 6;
  },
  
  required: (value) => {
    return value && value.trim().length > 0;
  }
};
```

---

## UI/UX 가이드라인

### 1. 디자인 시스템
```javascript
// utils/constants.js
export const COLORS = {
  primary: {
    50: '#eff6ff',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8'
  },
  success: {
    500: '#10b981',
    600: '#059669'
  },
  warning: {
    500: '#f59e0b',
    600: '#d97706'
  },
  error: {
    500: '#ef4444',
    600: '#dc2626'
  }
};

export const SIZES = {
  xs: '0.75rem',
  sm: '0.875rem',
  base: '1rem',
  lg: '1.125rem',
  xl: '1.25rem',
  '2xl': '1.5rem'
};
```

### 2. 공통 컴포넌트
```javascript
// components/common/Button.js
const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'base', 
  loading = false,
  disabled = false,
  onClick,
  ...props 
}) => {
  const baseClasses = 'font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    base: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
  
  const classes = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${sizeClasses[size]}
    ${(disabled || loading) ? 'opacity-50 cursor-not-allowed' : ''}
  `.trim();
  
  return (
    <button
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? (
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          처리 중...
        </div>
      ) : children}
    </button>
  );
};
```

### 3. 반응형 레이아웃
```javascript
// components/layout/Layout.js
const Layout = ({ children }) => {
  const { user } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={user} />
      
      <div className="flex">
        <Sidebar user={user} />
        
        <main className="flex-1 p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      <NotificationContainer />
    </div>
  );
};
```

---

## 성능 최적화

### 1. 코드 분할
```javascript
// App.js
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Projects = lazy(() => import('./pages/Projects'));
const Analytics = lazy(() => import('./pages/Analytics'));

const App = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <Router>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Router>
  </Suspense>
);
```

### 2. 메모이제이션
```javascript
// components/ProjectList.js
const ProjectList = memo(({ projects, onSelect }) => {
  return (
    <div className="project-list">
      {projects.map(project => (
        <ProjectCard 
          key={project.id} 
          project={project} 
          onSelect={onSelect}
        />
      ))}
    </div>
  );
});

const ProjectCard = memo(({ project, onSelect }) => {
  const handleClick = useCallback(() => {
    onSelect(project);
  }, [project, onSelect]);
  
  return (
    <div className="project-card" onClick={handleClick}>
      <h3>{project.name}</h3>
      <p>{project.description}</p>
    </div>
  );
});
```

### 3. 가상화 (대용량 데이터)
```javascript
// components/VirtualizedList.js
import { FixedSizeList as List } from 'react-window';

const VirtualizedUserList = ({ users }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <UserCard user={users[index]} />
    </div>
  );
  
  return (
    <List
      height={600}
      itemCount={users.length}
      itemSize={80}
    >
      {Row}
    </List>
  );
};
```

---

## 테스트 전략

### 1. 단위 테스트
```javascript
// __tests__/components/Button.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../components/common/Button';

describe('Button Component', () => {
  test('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  test('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  test('shows loading state', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByText('처리 중...')).toBeInTheDocument();
  });
});
```

### 2. 통합 테스트
```javascript
// __tests__/integration/Login.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider } from '../context/AuthContext';
import Login from '../pages/Login';

const renderWithAuth = (component) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('Login Integration', () => {
  test('successful login flow', async () => {
    // Mock API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'test-token',
          user: { id: '1', name: 'Test User', role: 'admin' }
        })
      })
    );
    
    renderWithAuth(<Login />);
    
    fireEvent.change(screen.getByLabelText('아이디'), {
      target: { value: 'admin' }
    });
    fireEvent.change(screen.getByLabelText('비밀번호'), {
      target: { value: 'password' }
    });
    
    fireEvent.click(screen.getByText('로그인'));
    
    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('test-token');
    });
  });
});
```

### 3. E2E 테스트
```javascript
// cypress/integration/evaluation_flow.spec.js
describe('Evaluation Flow', () => {
  beforeEach(() => {
    // 로그인
    cy.login('evaluator01', 'evaluator123');
  });
  
  it('should complete evaluation process', () => {
    // 대시보드에서 평가 시트 선택
    cy.visit('/dashboard');
    cy.get('[data-testid="evaluation-card"]').first().click();
    
    // 평가 항목 점수 입력
    cy.get('[data-testid="score-input-1"]').select('5');
    cy.get('[data-testid="comment-1"]').type('우수한 평가입니다.');
    
    // 임시저장
    cy.get('[data-testid="save-button"]').click();
    cy.get('[data-testid="save-success"]').should('be.visible');
    
    // 최종 제출
    cy.get('[data-testid="submit-button"]').click();
    cy.get('[data-testid="submit-modal"]').should('be.visible');
    cy.get('[data-testid="confirm-submit"]').click();
    
    // 제출 완료 확인
    cy.get('[data-testid="submit-success"]').should('be.visible');
    cy.url().should('include', '/dashboard');
  });
});
```

---

## 실시간 기능 구현

### WebSocket 연결
```javascript
// hooks/useWebSocket.js
export const useWebSocket = (url) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  
  useEffect(() => {
    const token = localStorage.getItem('token');
    const wsUrl = `${url}?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setConnected(true);
      setSocket(ws);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);
    };
    
    ws.onclose = () => {
      setConnected(false);
      setSocket(null);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    return () => {
      ws.close();
    };
  }, [url]);
  
  const sendMessage = useCallback((message) => {
    if (socket && connected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, connected]);
  
  return { connected, lastMessage, sendMessage };
};
```

### 실시간 알림
```javascript
// components/NotificationSystem.js
const NotificationSystem = () => {
  const { lastMessage } = useWebSocket('ws://localhost:8080/ws');
  const { addNotification } = useContext(AppContext);
  
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'evaluation_submitted':
          addNotification({
            type: 'success',
            title: '평가 제출 완료',
            message: '평가가 성공적으로 제출되었습니다.'
          });
          break;
        case 'assignment_created':
          addNotification({
            type: 'info',
            title: '새 평가 배정',
            message: '새로운 평가가 배정되었습니다.'
          });
          break;
        case 'deadline_reminder':
          addNotification({
            type: 'warning',
            title: '마감일 알림',
            message: '평가 마감일이 임박했습니다.'
          });
          break;
      }
    }
  }, [lastMessage, addNotification]);
  
  return null; // 알림은 AppContext를 통해 표시
};
```

---

## 결론

이 가이드는 온라인 평가 시스템의 프론트엔드 개발을 위한 종합적인 설계 방향을 제시합니다. 

### 핵심 포인트

1. **타입 안전성**: TypeScript 도입을 통한 안정성 향상
2. **컴포넌트 재사용성**: 모듈화된 컴포넌트 설계
3. **성능 최적화**: 메모이제이션, 코드 분할, 가상화
4. **사용자 경험**: 로딩 상태, 에러 처리, 실시간 피드백
5. **보안**: JWT 토큰 관리, 권한 기반 접근 제어
6. **테스트**: 단위, 통합, E2E 테스트 전략

### 다음 단계

1. 기존 React 앱의 점진적 리팩토링
2. TypeScript 마이그레이션
3. 컴포넌트 라이브러리 구축
4. 성능 모니터링 도구 도입
5. 자동화된 테스트 환경 구축

이 가이드를 참고하여 확장 가능하고 유지보수가 용이한 프론트엔드 애플리케이션을 구축하시기 바랍니다.
