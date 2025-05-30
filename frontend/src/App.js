import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

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
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">온라인 평가 시스템</h1>
          <p className="text-gray-600 mt-2">로그인하여 시작하세요</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              아이디
            </label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <h3 className="text-sm font-medium text-gray-700 mb-2">테스트 계정:</h3>
          <div className="text-xs text-gray-600 space-y-1">
            <div>관리자: admin / admin123</div>
            <div>간사: secretary01 / secretary123</div>
            <div>평가위원: evaluator01 / evaluator123</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Components
const AdminDashboard = ({ user }) => {
  const [stats, setStats] = useState({ projects: 0, companies: 0, evaluators: 0 });
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
      setStats(prev => ({ ...prev, projects: response.data.length }));
    } catch (error) {
      console.error("프로젝트 조회 실패:", error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              📊
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">진행 중인 과제</p>
              <p className="text-2xl font-bold">{stats.projects}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              🏢
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">참여 기업</p>
              <p className="text-2xl font-bold">{stats.companies}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              👥
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">평가위원</p>
              <p className="text-2xl font-bold">{stats.evaluators}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">프로젝트 관리</h2>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">과제명</th>
                  <th className="text-left py-2">마감일</th>
                  <th className="text-left py-2">상태</th>
                  <th className="text-left py-2">작업</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((project) => (
                  <tr key={project.id} className="border-b">
                    <td className="py-2">{project.name}</td>
                    <td className="py-2">{new Date(project.deadline).toLocaleDateString()}</td>
                    <td className="py-2">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                        진행중
                      </span>
                    </td>
                    <td className="py-2">
                      <button className="text-blue-600 hover:text-blue-800 text-sm">
                        관리
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const SecretaryDashboard = ({ user }) => {
  const [companies, setCompanies] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadCompanyId, setUploadCompanyId] = useState("");

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/companies`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompanies(response.data);
    } catch (error) {
      console.error("기업 조회 실패:", error);
    }
  };

  const handleFileUpload = async (companyId) => {
    if (!selectedFile) return;

    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append("company_id", companyId);
      formData.append("file", selectedFile);

      await axios.post(`${API}/upload`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      alert("파일이 성공적으로 업로드되었습니다.");
      setSelectedFile(null);
      fetchCompanies();
    } catch (error) {
      console.error("파일 업로드 실패:", error);
      alert("파일 업로드에 실패했습니다.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">파일 업로드</h2>
        </div>
        <div className="p-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <input
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-gray-400 text-4xl mb-2">📄</div>
              <p className="text-gray-600">
                {selectedFile ? selectedFile.name : "파일을 선택하거나 드래그하세요"}
              </p>
              <p className="text-sm text-gray-400">PDF, DOC, DOCX 파일만 지원</p>
            </label>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">참여 기업 관리</h2>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">기업명</th>
                  <th className="text-left py-2">담당자</th>
                  <th className="text-left py-2">연락처</th>
                  <th className="text-left py-2">파일 수</th>
                  <th className="text-left py-2">작업</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id} className="border-b">
                    <td className="py-2">{company.name}</td>
                    <td className="py-2">{company.contact_person}</td>
                    <td className="py-2">{company.phone}</td>
                    <td className="py-2">{company.files?.length || 0}</td>
                    <td className="py-2">
                      <button
                        onClick={() => handleFileUpload(company.id)}
                        disabled={!selectedFile}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                      >
                        파일 업로드
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const EvaluatorDashboard = ({ user }) => {
  const [assignments, setAssignments] = useState([]);

  useEffect(() => {
    fetchAssignments();
  }, []);

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

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">오늘의 평가 작업</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {assignments.filter(a => a.sheet.status === 'draft').length}
              </div>
              <div className="text-sm text-gray-600">진행 중</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {assignments.filter(a => a.sheet.status === 'submitted').length}
              </div>
              <div className="text-sm text-gray-600">완료</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {assignments.filter(a => {
                  const deadline = new Date(a.project.deadline);
                  const today = new Date();
                  const diffDays = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
                  return diffDays <= 3 && a.sheet.status === 'draft';
                }).length}
              </div>
              <div className="text-sm text-gray-600">마감 임박</div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">할당된 평가 과제</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {assignments.map((assignment) => (
              <div key={assignment.sheet.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-semibold text-lg">{assignment.project.name}</h3>
                    <p className="text-gray-600">{assignment.company.name}</p>
                    <p className="text-sm text-gray-500">
                      마감일: {new Date(assignment.project.deadline).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      assignment.sheet.status === 'submitted' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {assignment.sheet.status === 'submitted' ? '제출 완료' : '평가 중'}
                    </span>
                    <div className="mt-2">
                      <button className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">
                        {assignment.sheet.status === 'submitted' ? '결과 보기' : '평가하기'}
                      </button>
                    </div>
                  </div>
                </div>
                
                {assignment.company.files && assignment.company.files.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">제출 파일:</p>
                    <div className="flex flex-wrap gap-2">
                      {assignment.company.files.map((file, index) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 bg-gray-100 rounded text-xs">
                          📄 {file.split('/').pop()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {assignments.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                할당된 평가 과제가 없습니다.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
const Dashboard = ({ user, onLogout }) => {
  const renderDashboard = () => {
    switch (user.role) {
      case "admin":
        return <AdminDashboard user={user} />;
      case "secretary":
        return <SecretaryDashboard user={user} />;
      case "evaluator":
        return <EvaluatorDashboard user={user} />;
      default:
        return <div>알 수 없는 권한입니다.</div>;
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

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">온라인 평가 시스템</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm">
                <span className="text-gray-600">안녕하세요, </span>
                <span className="font-medium">{user.user_name}</span>
                <span className="text-gray-600"> ({getRoleDisplayName(user.role)})</span>
              </div>
              <button
                onClick={onLogout}
                className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700"
              >
                로그아웃
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {renderDashboard()}
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
      await axios.post(`${API}/init`);
    } catch (error) {
      console.log("시스템 이미 초기화됨");
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
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
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