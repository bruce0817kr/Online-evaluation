import React, { useState, useEffect, useCallback } from 'react';

const EnhancedTemplateManagement = ({ user }) => {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 필터 및 검색 상태
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  
  // 모달 상태
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showVersionModal, setShowVersionModal] = useState(false);
  
  // 폼 상태
  const [templateForm, setTemplateForm] = useState({
    name: '',
    description: '',
    project_id: '',
    category: '',
    criteria: [],
    is_default: false,
    is_public: false
  });
  
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  // 권한 확인
  const canManageTemplates = user && ['admin', 'secretary'].includes(user.role);
  const canCreateTemplates = user && ['admin', 'secretary'].includes(user.role);

  useEffect(() => {
    loadTemplates();
    loadCategories();
    loadProjects();
  }, [selectedProject, selectedCategory, selectedStatus]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (selectedProject) params.append('project_id', selectedProject);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedStatus) params.append('status', selectedStatus);
      params.append('include_public', 'true');
      
      const response = await fetch(`${BACKEND_URL}/api/templates?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      } else {
        throw new Error('템플릿 목록을 불러올 수 없습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates/categories/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      }
    } catch (err) {
      console.error('카테고리 로드 실패:', err);
    }
  };

  const loadProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('프로젝트 로드 실패:', err);
    }
  };

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateForm)
      });

      if (response.ok) {
        await loadTemplates();
        setShowCreateModal(false);
        resetForm();
        alert('템플릿이 성공적으로 생성되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿 생성에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleUpdateTemplate = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates/${selectedTemplate.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(templateForm)
      });

      if (response.ok) {
        await loadTemplates();
        setShowEditModal(false);
        setSelectedTemplate(null);
        resetForm();
        alert('템플릿이 성공적으로 업데이트되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿 업데이트에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!confirm('정말로 이 템플릿을 삭제하시겠습니까?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates/${templateId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadTemplates();
        alert('템플릿이 삭제되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿 삭제에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleCloneTemplate = async (templateId, cloneData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates/${templateId}/clone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(cloneData)
      });

      if (response.ok) {
        await loadTemplates();
        setShowCloneModal(false);
        alert('템플릿이 성공적으로 복제되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿 복제에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const resetForm = () => {
    setTemplateForm({
      name: '',
      description: '',
      project_id: '',
      category: '',
      criteria: [],
      is_default: false,
      is_public: false
    });
  };

  const addCriterion = () => {
    const newCriterion = {
      id: '',
      name: '',
      description: '',
      max_score: 10,
      min_score: 0,
      weight: 1.0,
      bonus: false,
      category: '',
      is_required: true,
      evaluation_guide: '',
      order: templateForm.criteria.length
    };
    
    setTemplateForm(prev => ({
      ...prev,
      criteria: [...prev.criteria, newCriterion]
    }));
  };

  const updateCriterion = (index, field, value) => {
    setTemplateForm(prev => ({
      ...prev,
      criteria: prev.criteria.map((criterion, i) => 
        i === index ? { ...criterion, [field]: value } : criterion
      )
    }));
  };

  const removeCriterion = (index) => {
    setTemplateForm(prev => ({
      ...prev,
      criteria: prev.criteria.filter((_, i) => i !== index)
    }));
  };

  const moveCriterion = (index, direction) => {
    const newCriteria = [...templateForm.criteria];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (targetIndex >= 0 && targetIndex < newCriteria.length) {
      [newCriteria[index], newCriteria[targetIndex]] = [newCriteria[targetIndex], newCriteria[index]];
      
      // 순서 업데이트
      newCriteria.forEach((criterion, i) => {
        criterion.order = i;
      });
      
      setTemplateForm(prev => ({ ...prev, criteria: newCriteria }));
    }
  };

  const openEditModal = (template) => {
    setSelectedTemplate(template);
    setTemplateForm({
      name: template.name,
      description: template.description || '',
      project_id: template.project_id,
      category: template.category || '',
      criteria: template.criteria || [],
      is_default: template.is_default || false,
      is_public: template.is_public || false
    });
    setShowEditModal(true);
  };

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (template.description && template.description.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSearch;
  });

  const getStatusBadge = (status) => {
    const statusColors = {
      'draft': 'bg-gray-100 text-gray-800',
      'active': 'bg-green-100 text-green-800',
      'archived': 'bg-yellow-100 text-yellow-800'
    };
    
    return `px-2 py-1 text-xs rounded-full ${statusColors[status] || 'bg-gray-100 text-gray-800'}`;
  };

  const getCategoryColor = (category) => {
    const colors = [
      'bg-blue-100 text-blue-800',
      'bg-purple-100 text-purple-800',
      'bg-pink-100 text-pink-800',
      'bg-indigo-100 text-indigo-800',
      'bg-teal-100 text-teal-800'
    ];
    
    const hash = category ? category.split('').reduce((a, b) => a + b.charCodeAt(0), 0) : 0;
    return colors[hash % colors.length];
  };

  if (!user || !['admin', 'secretary', 'evaluator'].includes(user.role)) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">📄 템플릿 관리</h2>
        <p className="text-gray-600">이 기능은 관리자, 간사, 평가위원만 사용할 수 있습니다.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">📄 향상된 템플릿 관리</h2>
          {canCreateTemplates && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              + 새 템플릿 생성
            </button>
          )}
        </div>

        {/* 필터 및 검색 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <input
              type="text"
              placeholder="템플릿 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg"
            />
          </div>
          
          <div>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg"
            >
              <option value="">모든 프로젝트</option>
              {projects.map(project => (
                <option key={project.id} value={project.id}>{project.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg"
            >
              <option value="">모든 카테고리</option>
              {categories.map(category => (
                <option key={category.name} value={category.name}>{category.name}</option>
              ))}
            </select>
          </div>
          
          <div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg"
            >
              <option value="">모든 상태</option>
              <option value="draft">초안</option>
              <option value="active">활성</option>
              <option value="archived">아카이브</option>
            </select>
          </div>
        </div>
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center h-32">
            <div className="text-gray-500">로딩 중...</div>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredTemplates.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                조건에 맞는 템플릿이 없습니다.
              </div>
            ) : (
              filteredTemplates.map((template) => (
                <div key={template.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-medium text-lg">{template.name}</h3>
                        <span className={getStatusBadge(template.status)}>
                          {template.status === 'draft' ? '초안' : 
                           template.status === 'active' ? '활성' : '아카이브'}
                        </span>
                        {template.category && (
                          <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(template.category)}`}>
                            {template.category}
                          </span>
                        )}
                        {template.is_default && (
                          <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                            기본
                          </span>
                        )}
                        {template.is_public && (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                            공개
                          </span>
                        )}
                      </div>
                      
                      <p className="text-gray-600 text-sm mb-2">{template.description}</p>
                      
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>평가 기준: {template.criteria?.length || 0}개</span>
                        <span>버전: {template.version || 1}</span>
                        <span>사용 횟수: {template.usage_count || 0}회</span>
                        <span>생성일: {new Date(template.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setSelectedTemplate(template)}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                      >
                        상세보기
                      </button>
                      
                      <button
                        onClick={() => handleCloneTemplate(template.id, {
                          new_name: `${template.name} (복사본)`,
                          new_description: `${template.description || ''} (복사본)`
                        })}
                        className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
                      >
                        복제
                      </button>
                      
                      {canManageTemplates && (
                        <>
                          <button
                            onClick={() => openEditModal(template)}
                            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                          >
                            편집
                          </button>
                          <button
                            onClick={() => handleDeleteTemplate(template.id)}
                            className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                          >
                            삭제
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* 템플릿 생성/편집 모달 */}
        {(showCreateModal || showEditModal) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto mx-4">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium">
                  {showCreateModal ? '새 템플릿 생성' : '템플릿 편집'}
                </h3>
              </div>
              
              <form onSubmit={showCreateModal ? handleCreateTemplate : handleUpdateTemplate} className="p-6 space-y-6">
                {/* 기본 정보 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      템플릿 이름 *
                    </label>
                    <input
                      type="text"
                      value={templateForm.name}
                      onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      카테고리
                    </label>
                    <select
                      value={templateForm.category}
                      onChange={(e) => setTemplateForm(prev => ({ ...prev, category: e.target.value }))}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                    >
                      <option value="">카테고리 선택</option>
                      {categories.map(category => (
                        <option key={category.name} value={category.name}>{category.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    설명
                  </label>
                  <textarea
                    value={templateForm.description}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full p-2 border border-gray-300 rounded-lg h-20"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    프로젝트 *
                  </label>
                  <select
                    value={templateForm.project_id}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, project_id: e.target.value }))}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">프로젝트 선택</option>
                    {projects.map(project => (
                      <option key={project.id} value={project.id}>{project.name}</option>
                    ))}
                  </select>
                </div>

                {/* 평가 기준 */}
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-medium">평가 기준</h4>
                    <button
                      type="button"
                      onClick={addCriterion}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                    >
                      + 기준 추가
                    </button>
                  </div>

                  <div className="space-y-4">
                    {templateForm.criteria.map((criterion, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <h5 className="font-medium">기준 {index + 1}</h5>
                          <div className="flex items-center space-x-2">
                            <button
                              type="button"
                              onClick={() => moveCriterion(index, 'up')}
                              disabled={index === 0}
                              className="px-2 py-1 text-xs border rounded disabled:opacity-50"
                            >
                              ↑
                            </button>
                            <button
                              type="button"
                              onClick={() => moveCriterion(index, 'down')}
                              disabled={index === templateForm.criteria.length - 1}
                              className="px-2 py-1 text-xs border rounded disabled:opacity-50"
                            >
                              ↓
                            </button>
                            <button
                              type="button"
                              onClick={() => removeCriterion(index)}
                              className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                            >
                              삭제
                            </button>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              기준 이름 *
                            </label>
                            <input
                              type="text"
                              value={criterion.name}
                              onChange={(e) => updateCriterion(index, 'name', e.target.value)}
                              className="w-full p-2 border border-gray-300 rounded text-sm"
                              required
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              카테고리
                            </label>
                            <input
                              type="text"
                              value={criterion.category || ''}
                              onChange={(e) => updateCriterion(index, 'category', e.target.value)}
                              placeholder="예: 기술성, 사업성, 혁신성"
                              className="w-full p-2 border border-gray-300 rounded text-sm"
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              최대 점수 *
                            </label>
                            <input
                              type="number"
                              value={criterion.max_score}
                              onChange={(e) => updateCriterion(index, 'max_score', parseInt(e.target.value))}
                              className="w-full p-2 border border-gray-300 rounded text-sm"
                              min="1"
                              required
                            />
                          </div>

                          <div>
                            <label className="block text-xs font-medium text-gray-700 mb-1">
                              가중치
                            </label>
                            <input
                              type="number"
                              step="0.1"
                              value={criterion.weight}
                              onChange={(e) => updateCriterion(index, 'weight', parseFloat(e.target.value))}
                              className="w-full p-2 border border-gray-300 rounded text-sm"
                              min="0.1"
                            />
                          </div>
                        </div>

                        <div className="mt-3">
                          <label className="block text-xs font-medium text-gray-700 mb-1">
                            설명
                          </label>
                          <textarea
                            value={criterion.description || ''}
                            onChange={(e) => updateCriterion(index, 'description', e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded text-sm h-16"
                            placeholder="평가 기준에 대한 상세 설명"
                          />
                        </div>

                        <div className="mt-3 flex items-center space-x-4">
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={criterion.bonus}
                              onChange={(e) => updateCriterion(index, 'bonus', e.target.checked)}
                              className="mr-2"
                            />
                            가점 항목
                          </label>
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={criterion.is_required}
                              onChange={(e) => updateCriterion(index, 'is_required', e.target.checked)}
                              className="mr-2"
                            />
                            필수 항목
                          </label>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 템플릿 옵션 */}
                <div className="border-t pt-4">
                  <h4 className="text-lg font-medium mb-3">템플릿 옵션</h4>
                  <div className="flex items-center space-x-6">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={templateForm.is_default}
                        onChange={(e) => setTemplateForm(prev => ({ ...prev, is_default: e.target.checked }))}
                        className="mr-2"
                      />
                      기본 템플릿
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={templateForm.is_public}
                        onChange={(e) => setTemplateForm(prev => ({ ...prev, is_public: e.target.checked }))}
                        className="mr-2"
                      />
                      공개 템플릿
                    </label>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false);
                      setShowEditModal(false);
                      resetForm();
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    {showCreateModal ? '생성' : '저장'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* 템플릿 상세보기 모달 */}
        {selectedTemplate && !showEditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto mx-4">
              <div className="p-6 border-b">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">{selectedTemplate.name}</h3>
                  <button
                    onClick={() => setSelectedTemplate(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              <div className="p-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">기본 정보</h4>
                    <div className="bg-gray-50 p-3 rounded">
                      <p><strong>설명:</strong> {selectedTemplate.description || '설명 없음'}</p>
                      <p><strong>카테고리:</strong> {selectedTemplate.category || '미분류'}</p>
                      <p><strong>버전:</strong> {selectedTemplate.version || 1}</p>
                      <p><strong>상태:</strong> {selectedTemplate.status}</p>
                      <p><strong>생성일:</strong> {new Date(selectedTemplate.created_at).toLocaleString()}</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">평가 기준 ({selectedTemplate.criteria?.length || 0}개)</h4>
                    <div className="space-y-2">
                      {selectedTemplate.criteria?.map((criterion, index) => (
                        <div key={index} className="border border-gray-200 rounded p-3">
                          <div className="flex items-center justify-between mb-2">
                            <h5 className="font-medium">{criterion.name}</h5>
                            <div className="flex items-center space-x-2">
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                {criterion.max_score}점
                              </span>
                              {criterion.bonus && (
                                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                                  가점
                                </span>
                              )}
                              {criterion.weight !== 1.0 && (
                                <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                                  가중치 {criterion.weight}
                                </span>
                              )}
                            </div>
                          </div>
                          {criterion.description && (
                            <p className="text-sm text-gray-600">{criterion.description}</p>
                          )}
                          {criterion.category && (
                            <p className="text-xs text-gray-500 mt-1">카테고리: {criterion.category}</p>
                          )}
                        </div>
                      )) || (
                        <p className="text-gray-500">평가 기준이 없습니다.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedTemplateManagement;