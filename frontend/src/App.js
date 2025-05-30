import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

// Modal Components
const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
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

// Project Management Component
const ProjectManagement = ({ user }) => {
  const [projects, setProjects] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [evaluators, setEvaluators] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isCompanyModalOpen, setIsCompanyModalOpen] = useState(false);
  const [isEvaluatorModalOpen, setIsEvaluatorModalOpen] = useState(false);
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
  const [isAssignmentModalOpen, setIsAssignmentModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState("");
  const [newCredentials, setNewCredentials] = useState(null);

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

  return (
    <div className="space-y-6">
      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4">
        <button
          onClick={() => setIsProjectModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          프로젝트 생성
        </button>
        <button
          onClick={() => setIsCompanyModalOpen(true)}
          disabled={!selectedProject}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
        >
          기업 등록
        </button>
        <button
          onClick={() => setIsEvaluatorModalOpen(true)}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
        >
          평가위원 추가
        </button>
        <button
          onClick={() => setIsTemplateModalOpen(true)}
          disabled={!selectedProject}
          className="bg-orange-600 text-white px-4 py-2 rounded hover:bg-orange-700 disabled:opacity-50"
        >
          평가표 생성
        </button>
        <button
          onClick={() => setIsAssignmentModalOpen(true)}
          disabled={!selectedProject}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50"
        >
          평가 할당
        </button>
      </div>

      {/* Project Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">프로젝트 선택</h3>
        <select
          value={selectedProject}
          onChange={(e) => handleProjectSelect(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded"
        >
          <option value="">프로젝트를 선택하세요</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>

      {/* Companies List */}
      {selectedProject && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">참여 기업</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">기업명</th>
                  <th className="text-left py-2">사업자번호</th>
                  <th className="text-left py-2">담당자</th>
                  <th className="text-left py-2">연락처</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((company) => (
                  <tr key={company.id} className="border-b">
                    <td className="py-2">{company.name}</td>
                    <td className="py-2">{company.business_number}</td>
                    <td className="py-2">{company.contact_person}</td>
                    <td className="py-2">{company.phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Project Creation Modal */}
      <Modal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        title="프로젝트 생성"
      >
        <form onSubmit={handleProjectSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              프로젝트명
            </label>
            <input
              type="text"
              value={projectForm.name}
              onChange={(e) => setProjectForm({...projectForm, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              설명
            </label>
            <textarea
              value={projectForm.description}
              onChange={(e) => setProjectForm({...projectForm, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows={3}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              마감일
            </label>
            <input
              type="datetime-local"
              value={projectForm.deadline}
              onChange={(e) => setProjectForm({...projectForm, deadline: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsProjectModalOpen(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              생성
            </button>
          </div>
        </form>
      </Modal>

      {/* Company Creation Modal */}
      <Modal
        isOpen={isCompanyModalOpen}
        onClose={() => setIsCompanyModalOpen(false)}
        title="기업 등록"
      >
        <form onSubmit={handleCompanySubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              프로젝트
            </label>
            <select
              value={companyForm.project_id}
              onChange={(e) => setCompanyForm({...companyForm, project_id: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              기업명
            </label>
            <input
              type="text"
              value={companyForm.name}
              onChange={(e) => setCompanyForm({...companyForm, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사업자번호
            </label>
            <input
              type="text"
              value={companyForm.business_number}
              onChange={(e) => setCompanyForm({...companyForm, business_number: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              주소
            </label>
            <input
              type="text"
              value={companyForm.address}
              onChange={(e) => setCompanyForm({...companyForm, address: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              담당자
            </label>
            <input
              type="text"
              value={companyForm.contact_person}
              onChange={(e) => setCompanyForm({...companyForm, contact_person: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              전화번호
            </label>
            <input
              type="text"
              value={companyForm.phone}
              onChange={(e) => setCompanyForm({...companyForm, phone: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              이메일
            </label>
            <input
              type="email"
              value={companyForm.email}
              onChange={(e) => setCompanyForm({...companyForm, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsCompanyModalOpen(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              등록
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
          <div className="text-center space-y-4">
            <div className="text-green-600 text-lg font-semibold">평가위원이 성공적으로 생성되었습니다!</div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="space-y-2">
                <div><strong>이름:</strong> {newCredentials.name}</div>
                <div><strong>아이디:</strong> {newCredentials.login_id}</div>
                <div><strong>비밀번호:</strong> {newCredentials.password}</div>
              </div>
            </div>
            <div className="text-sm text-gray-600">
              위 정보를 평가위원에게 전달해주세요.
            </div>
            <button
              onClick={() => {
                setIsEvaluatorModalOpen(false);
                setNewCredentials(null);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              확인
            </button>
          </div>
        ) : (
          <form onSubmit={handleEvaluatorSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이름 (한글)
              </label>
              <input
                type="text"
                value={evaluatorForm.user_name}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, user_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="홍길동"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                전화번호 (하이픈 제외)
              </label>
              <input
                type="text"
                value={evaluatorForm.phone}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, phone: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="01012345678"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이메일
              </label>
              <input
                type="email"
                value={evaluatorForm.email}
                onChange={(e) => setEvaluatorForm({...evaluatorForm, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div className="text-sm text-gray-600 bg-blue-50 p-3 rounded">
              아이디와 비밀번호는 이름과 전화번호를 기반으로 자동 생성됩니다.
            </div>
            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsEvaluatorModalOpen(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
              >
                취소
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
              >
                추가
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* Template Creation Modal */}
      <Modal
        isOpen={isTemplateModalOpen}
        onClose={() => setIsTemplateModalOpen(false)}
        title="평가표 생성"
      >
        <form onSubmit={handleTemplateSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              평가표명
            </label>
            <input
              type="text"
              value={templateForm.name}
              onChange={(e) => setTemplateForm({...templateForm, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              설명
            </label>
            <textarea
              value={templateForm.description}
              onChange={(e) => setTemplateForm({...templateForm, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows={2}
            />
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-medium text-gray-700">
                평가 항목
              </label>
              <button
                type="button"
                onClick={addTemplateItem}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                + 항목 추가
              </button>
            </div>
            
            {templateForm.items.map((item, index) => (
              <div key={index} className="border border-gray-200 rounded-md p-3 mb-3">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-sm font-medium">항목 {index + 1}</span>
                  {templateForm.items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeTemplateItem(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      삭제
                    </button>
                  )}
                </div>
                
                <div className="space-y-2">
                  <input
                    type="text"
                    placeholder="항목명 (예: 기술성)"
                    value={item.name}
                    onChange={(e) => updateTemplateItem(index, 'name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    required
                  />
                  <textarea
                    placeholder="항목 설명"
                    value={item.description}
                    onChange={(e) => updateTemplateItem(index, 'description', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    rows={2}
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="number"
                      placeholder="최고점수"
                      value={item.max_score}
                      onChange={(e) => updateTemplateItem(index, 'max_score', parseInt(e.target.value))}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                      min="1"
                      required
                    />
                    <input
                      type="number"
                      placeholder="가중치"
                      value={item.weight}
                      onChange={(e) => updateTemplateItem(index, 'weight', parseFloat(e.target.value))}
                      className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                      min="0"
                      step="0.1"
                      required
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsTemplateModalOpen(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
            >
              생성
            </button>
          </div>
        </form>
      </Modal>

      {/* Assignment Modal */}
      <Modal
        isOpen={isAssignmentModalOpen}
        onClose={() => setIsAssignmentModalOpen(false)}
        title="평가 할당"
      >
        <form onSubmit={handleAssignmentSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              평가표 선택
            </label>
            <select
              value={assignmentForm.template_id}
              onChange={(e) => setAssignmentForm({...assignmentForm, template_id: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              required
            >
              <option value="">평가표를 선택하세요</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              평가위원 선택 (복수 선택 가능)
            </label>
            <div className="border border-gray-300 rounded-md p-2 max-h-32 overflow-y-auto">
              {evaluators.map((evaluator) => (
                <label key={evaluator.id} className="flex items-center space-x-2 py-1">
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
                  />
                  <span className="text-sm">{evaluator.user_name}</span>
                </label>
              ))}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              기업 선택 (복수 선택 가능)
            </label>
            <div className="border border-gray-300 rounded-md p-2 max-h-32 overflow-y-auto">
              {companies.map((company) => (
                <label key={company.id} className="flex items-center space-x-2 py-1">
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
                  />
                  <span className="text-sm">{company.name}</span>
                </label>
              ))}
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              평가 마감일 (선택사항)
            </label>
            <input
              type="datetime-local"
              value={assignmentForm.deadline}
              onChange={(e) => setAssignmentForm({...assignmentForm, deadline: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsAssignmentModalOpen(false)}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              할당
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

// File Upload Component
const FileManagement = ({ user }) => {
  const [companies, setCompanies] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);

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
    if (!selectedFile) {
      alert("파일을 선택해주세요.");
      return;
    }

    setUploading(true);
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
    } finally {
      setUploading(false);
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
                        disabled={!selectedFile || uploading}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
                      >
                        {uploading ? "업로드 중..." : "파일 업로드"}
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

// Evaluation Component
const EvaluationForm = ({ user }) => {
  const [assignments, setAssignments] = useState([]);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [evaluationData, setEvaluationData] = useState(null);
  const [scores, setScores] = useState({});
  const [saving, setSaving] = useState(false);

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

  if (selectedAssignment && evaluationData) {
    const isSubmitted = evaluationData.sheet.status === "submitted";
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <button
            onClick={() => {
              setSelectedAssignment(null);
              setEvaluationData(null);
              setScores({});
            }}
            className="text-blue-600 hover:text-blue-800"
          >
            ← 목록으로 돌아가기
          </button>
          {!isSubmitted && (
            <div className="space-x-2">
              <button
                onClick={() => saveEvaluation(false)}
                disabled={saving}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50"
              >
                {saving ? "저장 중..." : "임시저장"}
              </button>
              <button
                onClick={() => saveEvaluation(true)}
                disabled={saving}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? "제출 중..." : "최종제출"}
              </button>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">
            {evaluationData.project.name} - {evaluationData.company.name}
          </h2>
          <div className="grid grid-cols-2 gap-4 mb-6">
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
          </div>

          {evaluationData.company.files && evaluationData.company.files.length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold mb-2">제출 파일</h3>
              <div className="space-y-2">
                {evaluationData.company.files.map((file, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                    <span>📄</span>
                    <span className="text-sm">{file.split('/').pop()}</span>
                    <button className="text-blue-600 hover:text-blue-800 text-sm">
                      보기
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div>
            <h3 className="font-semibold mb-4">평가 항목</h3>
            <div className="space-y-6">
              {evaluationData.template.items.map((item) => (
                <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="mb-3">
                    <h4 className="font-medium">{item.name}</h4>
                    <p className="text-sm text-gray-600">{item.description}</p>
                    <p className="text-xs text-gray-500">
                      최고점수: {item.max_score}점, 가중치: {item.weight}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        점수
                      </label>
                      <input
                        type="number"
                        min="0"
                        max={item.max_score}
                        value={scores[item.id]?.score || ""}
                        onChange={(e) => handleScoreChange(item.id, 'score', parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        disabled={isSubmitted}
                      />
                    </div>
                    <div className="md:col-span-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        의견
                      </label>
                      <textarea
                        value={scores[item.id]?.opinion || ""}
                        onChange={(e) => handleScoreChange(item.id, 'opinion', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                        rows={3}
                        disabled={isSubmitted}
                        placeholder="평가 의견을 입력하세요..."
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
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
                      마감일: {assignment.sheet.deadline ? 
                        new Date(assignment.sheet.deadline).toLocaleDateString() : 
                        new Date(assignment.project.deadline).toLocaleDateString()
                      }
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
                      <button 
                        onClick={() => loadEvaluation(assignment)}
                        className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
                      >
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

// Admin Dashboard Component
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

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/dashboard/admin`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data.stats);
      setRecentProjects(response.data.recent_projects);
    } catch (error) {
      console.error("대시보드 데이터 조회 실패:", error);
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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">평가 진행 현황</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span>전체 평가</span>
              <span className="font-semibold">{stats.total_evaluations}</span>
            </div>
            <div className="flex justify-between">
              <span>완료된 평가</span>
              <span className="font-semibold text-green-600">{stats.completed_evaluations}</span>
            </div>
            <div className="flex justify-between">
              <span>완료율</span>
              <span className="font-semibold">{stats.completion_rate}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full" 
                style={{ width: `${stats.completion_rate}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">최근 프로젝트</h3>
          <div className="space-y-2">
            {recentProjects.map((project) => (
              <div key={project.id} className="flex justify-between items-center py-2 border-b">
                <div>
                  <div className="font-medium">{project.name}</div>
                  <div className="text-sm text-gray-500">
                    마감: {new Date(project.deadline).toLocaleDateString()}
                  </div>
                </div>
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                  진행중
                </span>
              </div>
            ))}
            {recentProjects.length === 0 && (
              <div className="text-gray-500 text-center py-4">
                프로젝트가 없습니다.
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
      case "files":
        return <FileManagement user={user} />;
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

      {/* Navigation */}
      {user.role !== "evaluator" && (
        <nav className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab("dashboard")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "dashboard"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                대시보드
              </button>
              <button
                onClick={() => setActiveTab("projects")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "projects"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                프로젝트 관리
              </button>
              <button
                onClick={() => setActiveTab("files")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "files"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                파일 관리
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