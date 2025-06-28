import React, { useState, useEffect } from 'react';
import './TemplateManagement.css'; 

const TemplateManagement = ({ user }) => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateDescription, setNewTemplateDescription] = useState('');
  const [newTemplateItems, setNewTemplateItems] = useState([{ text: '', score: 10 }]);
  
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';
  
  // 권한 확인
  if (!user || (user.role !== 'admin' && user.role !== 'secretary')) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">템플릿 관리</h2>
        <p className="text-gray-600">이 기능은 관리자와 간사만 사용할 수 있습니다.</p>
      </div>
    );
  }

  // 프로젝트 목록 로드
  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
        if (data.length > 0 && !selectedProject) {
          setSelectedProject(data[0].id);
        }
      }
    } catch (err) {
      console.error('프로젝트 목록 로드 실패:', err);
    }
  };
  
  // 템플릿 목록 조회
  const fetchTemplates = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (selectedProject) params.append('project_id', selectedProject);
      if (searchTerm) params.append('search', searchTerm);
      
      const response = await fetch(`${BACKEND_URL}/api/templates?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `템플릿 목록 조회 실패 (${response.status})`;
        throw new Error(errorMessage);
      }
    } catch (err) {
      const userFriendlyMessage = err.message.includes('Failed to fetch') 
        ? '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.'
        : err.message || '템플릿 목록을 불러오는 중 오류가 발생했습니다.';
      setError(userFriendlyMessage);
      console.error('템플릿 목록 조회 오류:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);
  
  useEffect(() => {
    if (projects.length > 0) {
      fetchTemplates();
    }
  }, [selectedProject, searchTerm, projects]);

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    if (!selectedProject) {
      alert('프로젝트를 선택해주세요.');
      return;
    }
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const templateData = {
        name: newTemplateName,
        description: newTemplateDescription,
        project_id: selectedProject,
        items: newTemplateItems.filter(item => item.text.trim() !== '')
      };
      
      const response = await fetch(`${BACKEND_URL}/api/templates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateData)
      });
      
      if (response.ok) {
        fetchTemplates();
        setShowCreateModal(false);
        setNewTemplateName('');
        setNewTemplateDescription('');
        setNewTemplateItems([{ text: '', score: 10 }]);
        alert('템플릿이 성공적으로 생성되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿 생성 실패');
      }
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectTemplate = (template) => {
    setSelectedTemplate(template);
    setShowPreviewModal(true);
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('정말로 이 템플릿을 삭제하시겠습니까?')) {
      return;
    }
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates/${templateId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        fetchTemplates();
        alert('템플릿이 성공적으로 삭제되었습니다.');
      } else {
        throw new Error('템플릿 삭제 실패');
      }
    } catch (err) {
      setError(err.message);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const addNewTemplateItem = () => {
    setNewTemplateItems([...newTemplateItems, { text: '', score: 10 }]);
  };
  
  const removeTemplateItem = (index) => {
    if (newTemplateItems.length > 1) {
      setNewTemplateItems(newTemplateItems.filter((_, i) => i !== index));
    }
  };
  
  const updateTemplateItem = (index, field, value) => {
    const updatedItems = [...newTemplateItems];
    updatedItems[index] = { ...updatedItems[index], [field]: value };
    setNewTemplateItems(updatedItems);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">로딩 중...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">템플릿 관리</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            + 새 템플릿 생성
          </button>
        </div>

        {/* 필터링 섹션 */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-medium mb-3">필터 및 검색</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">프로젝트</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="">전체 프로젝트</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">검색</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="템플릿 이름 또는 설명 검색..."
                className="w-full p-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800">오류가 발생했습니다</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
                <div className="mt-3">
                  <button
                    onClick={() => {
                      setError(null);
                      fetchTemplates();
                    }}
                    className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200 transition-colors"
                  >
                    다시 시도
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 템플릿 목록 */}
        {templates.length === 0 ? (
          <p className="text-gray-500 text-center py-8">등록된 템플릿이 없습니다.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleSelectTemplate(template)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      미리보기
                    </button>
                    <button
                      onClick={() => handleDeleteTemplate(template.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      삭제
                    </button>
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-3">{template.description}</p>
                <div className="text-xs text-gray-500">
                  <p>프로젝트: {template.project_name || '알 수 없음'}</p>
                  <p>항목 수: {template.items ? template.items.length : 0}개</p>
                  <p>생성일: {template.created_at ? new Date(template.created_at).toLocaleDateString() : '알 수 없음'}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 템플릿 생성 모달 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">새 템플릿 생성</h3>
            <form onSubmit={handleCreateTemplate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">템플릿 이름</label>
                <input
                  type="text"
                  value={newTemplateName}
                  onChange={(e) => setNewTemplateName(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                <textarea
                  value={newTemplateDescription}
                  onChange={(e) => setNewTemplateDescription(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  rows="3"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">프로젝트</label>
                <select
                  value={selectedProject}
                  onChange={(e) => setSelectedProject(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">프로젝트 선택</option>
                  {projects.map(project => (
                    <option key={project.id} value={project.id}>{project.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">평가 항목</label>
                  <button
                    type="button"
                    onClick={addNewTemplateItem}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    + 항목 추가
                  </button>
                </div>
                {newTemplateItems.map((item, index) => (
                  <div key={index} className="flex gap-2 mb-2">
                    <input
                      type="text"
                      value={item.text}
                      onChange={(e) => updateTemplateItem(index, 'text', e.target.value)}
                      placeholder="평가 항목 내용"
                      className="flex-1 p-2 border border-gray-300 rounded-lg"
                    />
                    <input
                      type="number"
                      value={item.score}
                      onChange={(e) => updateTemplateItem(index, 'score', parseInt(e.target.value))}
                      placeholder="점수"
                      className="w-20 p-2 border border-gray-300 rounded-lg"
                      min="1"
                      max="100"
                    />
                    {newTemplateItems.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeTemplateItem(index)}
                        className="px-3 py-2 text-red-600 hover:text-red-800"
                      >
                        삭제
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <div className="flex justify-end space-x-3 pt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewTemplateName('');
                    setNewTemplateDescription('');
                    setNewTemplateItems([{ text: '', score: 10 }]);
                  }}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {isLoading ? '생성 중...' : '생성'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 템플릿 미리보기 모달 */}
      {showPreviewModal && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">템플릿 미리보기</h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-gray-900">{selectedTemplate.name}</h4>
                <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
              </div>
              
              {selectedTemplate.items && selectedTemplate.items.length > 0 && (
                <div>
                  <h5 className="font-medium text-gray-700 mb-2">평가 항목</h5>
                  <div className="space-y-2">
                    {selectedTemplate.items.map((item, index) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm">{item.text || item}</span>
                        <span className="text-sm font-medium text-blue-600">{item.score || '10'}점</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-xs text-gray-500">
                <p>생성일: {selectedTemplate.created_at ? new Date(selectedTemplate.created_at).toLocaleDateString() : '알 수 없음'}</p>
              </div>
            </div>
            
            <div className="flex justify-end pt-6">
              <button
                onClick={() => setShowPreviewModal(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateManagement;