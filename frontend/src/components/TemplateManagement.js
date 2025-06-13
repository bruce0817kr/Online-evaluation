import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '../services/apiClient.js'; // 실제 API 클라이언트 사용
import './TemplateManagement.css'; 
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'; // 드래그앤드롭을 위한 라이브러리 import

const TemplateManagement = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [userToShare, setUserToShare] = useState('');
  const [sharePermission, setSharePermission] = useState('view');
  const [newTemplateName, setNewTemplateName] = useState('');
  const [newTemplateDescription, setNewTemplateDescription] = useState('');
  const [newTemplateItems, setNewTemplateItems] = useState([{ text: '' }]); // 새 템플릿 항목

  // 미리보기 및 수정 모달 상태 추가
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null); // 수정 중인 템플릿 데이터
  const [editedTemplateName, setEditedTemplateName] = useState('');
  const [editedTemplateDescription, setEditedTemplateDescription] = useState('');
  const [editedTemplateItems, setEditedTemplateItems] = useState([{ text: '' }]);

  // TODO: 프로젝트 ID 등 필요한 컨텍스트 정보 (예: props 또는 Context API)
  const currentProjectId = 'default_project'; // 예시 프로젝트 ID

  // 필터/정렬/페이지네이션 상태 추가
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCreator, setFilterCreator] = useState('');
  const [sortOption, setSortOption] = useState('created_at_desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 10; // 페이지당 항목 수

  // 카드뷰/리스트뷰 전환 상태 추가
  const [viewMode, setViewMode] = useState('list'); // 'list' 또는 'card'

  // 기능 목록 (주석)
  // 1. 템플릿 목록 조회 (GET /api/templates)
  //    - 검색 기능 (이름, 설명 등)
  //    - 필터링 기능 (상태, 생성자 등)
  //    - 페이지네이션 (필요시)
  // 2. 새 템플릿 생성 (POST /api/templates)
  //    - 템플릿 이름, 설명, 항목(EvaluationItemCreate) 입력
  //    - 생성 후 목록 새로고침
  // 3. 템플릿 상세 조회 (GET /api/templates/{template_id})
  //    - 선택된 템플릿의 모든 정보 표시
  //    - 항목 목록 표시 및 관리 기능 (항목 추가/수정/삭제는 별도 컴포넌트 또는 모달)
  // 4. 템플릿 수정 (PUT /api/templates/{template_id})
  //    - 이름, 설명, 항목 등 수정
  //    - 수정 후 상세 정보 및 목록 새로고침
  // 5. 템플릿 삭제 (DELETE /api/templates/{template_id}) -> 실제로는 상태 변경 (archived)
  //    - 삭제 확인 절차
  //    - 삭제(아카이브) 후 목록 새로고침
  // 6. 템플릿 버전 관리
  //    - 새 버전 생성 (POST /api/templates/{template_id}/version)
  //    - 버전 히스토리 조회 (UI 요소 추가 필요)
  // 7. 템플릿 복제 (POST /api/templates/{template_id}/clone)
  //    - 복제 후 새 템플릿으로 간주, 목록에 추가
  // 8. 템플릿 공유 (POST /api/templates/{template_id}/share)
  //    - 공유할 사용자 검색/선택 기능
  //    - 공유 권한 설정 (view, edit)
  //    - 현재 공유 상태 표시 및 수정/삭제 기능
  // 9. 템플릿 상태 변경 (PATCH /api/templates/{template_id}/status)
  //    - 상태 변경 UI (예: 드롭다운, 버튼)
  //    - 상태(draft, active, archived)에 따른 UI 변화 (예: 비활성화, 아이콘 변경)
  // 10. 템플릿 미리보기 기능
  //     - 템플릿이 실제 평가에 어떻게 보일지 시각화

  // 템플릿 목록 조회 함수 수정 (필터/정렬/페이지네이션 적용)
  const fetchTemplates = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = {
        project_id: currentProjectId,
        search: searchTerm,
        status: filterStatus,
        created_by: filterCreator,
        sort: sortOption,
        page: currentPage,
        page_size: pageSize,
      };
      const response = await apiClient.get('/templates', { params });
      setTemplates(response.data.templates || response.data); // templates 배열 또는 전체
      setTotalPages(response.data.total_pages || 1);
    } catch (err) {
      setError('템플릿 목록을 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [currentProjectId, searchTerm, filterStatus, filterCreator, sortOption, currentPage]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const handleCreateTemplate = async (templateData) => {
    // TODO: templateData 구성 (이름, 설명, 항목 리스트 등)
    // const newTemplateData = { name: '새 템플릿', description: '설명', items: [], project_id: currentProjectId };
    setIsLoading(true);
    try {
      await apiClient.post('/templates', { ...templateData, project_id: currentProjectId });
      fetchTemplates(); // 목록 새로고침
      setShowCreateModal(false);
      setNewTemplateName('');
      setNewTemplateDescription('');
      setNewTemplateItems([{ text: '' }]);
    } catch (err) {
      setError('템플릿 생성 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSelectTemplate = async (templateId) => {
    setIsLoading(true);
    try {
      const response = await apiClient.get(`/templates/${templateId}`);
      setSelectedTemplate(response.data);
    } catch (err) {
      setError('템플릿 상세 정보를 불러오는 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateTemplate = async (templateId, updatedData) => {
    setIsLoading(true);
    try {
      // PUT 요청 시 items도 포함하여 전송 (실제 구현 시에는 변경된 항목만 보내거나, 전체를 보낼 수 있음)
      await apiClient.put(`/templates/${templateId}`, updatedData);
      fetchTemplates(); // 목록 새로고침
      if (selectedTemplate && selectedTemplate.id === templateId) {
        handleSelectTemplate(templateId); // 선택된 템플릿 정보도 새로고침
      }
    } catch (err) {
      setError('템플릿 수정 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (window.confirm('정말로 이 템플릿을 아카이브하시겠습니까?')) {
      setIsLoading(true);
      try {
        // 백엔드에서는 DELETE가 아닌 PATCH /status 로 archived 처리
        await apiClient.patch(`/templates/${templateId}/status`, { status: 'archived' });
        fetchTemplates(); // 목록 새로고침
        if (selectedTemplate && selectedTemplate.id === templateId) {
          setSelectedTemplate(null); // 선택된 템플릿 초기화
        }
      } catch (err) {
        setError('템플릿 아카이브 중 오류가 발생했습니다.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleCloneTemplate = async (templateId) => {
    setIsLoading(true);
    try {
      await apiClient.post(`/templates/${templateId}/clone`, {});
      fetchTemplates(); // 목록 새로고침
    } catch (err) {
      setError('템플릿 복제 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleShareTemplate = async (templateId) => {
    if (!userToShare) {
        alert('공유할 사용자 ID를 입력하세요.');
        return;
    }
    setIsLoading(true);
    try {
      await apiClient.post(`/templates/${templateId}/share`, { user_id: userToShare, permission: sharePermission });
      // 공유 후 선택된 템플릿 정보 업데이트 또는 알림
      alert('템플릿이 공유되었습니다.');
      setShowShareModal(false);
      setUserToShare('');
      // 필요시, 공유된 템플릿 정보 다시 불러오기
      if (selectedTemplate && selectedTemplate.id === templateId) {
        handleSelectTemplate(templateId);
      }
    } catch (err) {
      setError('템플릿 공유 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangeStatus = async (templateId, newStatus) => {
    setIsLoading(true);
    try {
      await apiClient.patch(`/templates/${templateId}/status`, { status: newStatus });
      fetchTemplates();
      if (selectedTemplate && selectedTemplate.id === templateId) {
        // 상태 변경 시, 선택된 템플릿의 로컬 상태도 즉시 업데이트하거나, 다시 불러옴
        // 여기서는 간단히 다시 불러오는 것으로 처리
        handleSelectTemplate(templateId);
      }
    } catch (err) {
      setError('템플릿 상태 변경 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };
  
  // TODO: 나머지 핸들러 함수들 (버전 생성 등)

  const handleCreateNewVersion = async (templateId) => {
    if (!selectedTemplate) {
      alert('버전을 생성할 템플릿이 선택되지 않았습니다.');
      return;
    }
    if (window.confirm('이 템플릿의 새 버전을 생성하시겠습니까? 현재 내용이 복사되어 새 버전으로 만들어집니다.')) {
      setIsLoading(true);
      try {
        // 현재 선택된 템플릿의 내용을 기반으로 새 버전 생성 요청
        const response = await apiClient.post(`/templates/${templateId}/version`, {
          name: `${selectedTemplate.name} (v${(selectedTemplate.version || 1) + 1})`,
          description: selectedTemplate.description,
          items: selectedTemplate.items, // 현재 항목들을 그대로 복사
          project_id: selectedTemplate.project_id || currentProjectId,
          currentVersion: selectedTemplate.version // 백엔드에서 버전 관리를 위해 현재 버전 정보 전달 (옵션)
        });
        alert('새로운 버전의 템플릿이 생성되었습니다.');
        fetchTemplates(); // 목록 새로고침
        handleSelectTemplate(response.data.id); // 새로 생성된 버전 선택
      } catch (err) {
        setError('새 버전 생성 중 오류가 발생했습니다.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  // 새 템플릿 항목 추가 핸들러
  const handleAddItemToNewTemplate = () => {
    setNewTemplateItems([...newTemplateItems, { text: '' }]);
  };

  // 새 템플릿 항목 변경 핸들러
  const handleNewTemplateItemChange = (index, value) => {
    const updatedItems = newTemplateItems.map((item, i) => 
      i === index ? { ...item, text: value } : item
    );
    setNewTemplateItems(updatedItems);
  };

  // 새 템플릿 항목 삭제 핸들러
  const handleRemoveItemFromNewTemplate = (index) => {
    const updatedItems = newTemplateItems.filter((_, i) => i !== index);
    setNewTemplateItems(updatedItems);
  };

  // 수정 모달 열기 핸들러
  const handleOpenEditModal = (template) => {
    setEditingTemplate(template);
    setEditedTemplateName(template.name);
    setEditedTemplateDescription(template.description);
    setEditedTemplateItems(template.items && template.items.length > 0 ? [...template.items] : [{ text: '' }]);
    setShowEditModal(true);
  };

  // 수정 모달 닫기 핸들러
  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setEditingTemplate(null);
    setEditedTemplateName('');
    setEditedTemplateDescription('');
    setEditedTemplateItems([{ text: '' }]);
  };

  // 수정된 템플릿 저장 핸들러
  const handleSaveEditedTemplate = async () => {
    if (!editingTemplate) return;

    const updatedData = {
      name: editedTemplateName,
      description: editedTemplateDescription,
      items: editedTemplateItems.filter(item => item.text.trim() !== ''),
      project_id: editingTemplate.project_id || currentProjectId, // 기존 project_id 유지
    };
    // version은 백엔드에서 PUT 요청 시 자동으로 증가시키거나, 필요시 명시적으로 전달
    // 여기서는 updatedData에 version을 포함하지 않고, 백엔드가 처리하도록 함

    await handleUpdateTemplate(editingTemplate.id, updatedData);
    handleCloseEditModal();
  };
  
  // 수정 템플릿 항목 변경 핸들러
  const handleEditedItemChange = (index, value) => {
    const updatedItems = editedTemplateItems.map((item, i) =>
      i === index ? { ...item, text: value } : item
    );
    setEditedTemplateItems(updatedItems);
  };

  // 수정 템플릿 항목 추가 핸들러
  const handleAddItemToEditedTemplate = () => {
    setEditedTemplateItems([...editedTemplateItems, { text: '' }]);
  };

  // 수정 템플릿 항목 삭제 핸들러
  const handleRemoveItemFromEditedTemplate = (index) => {
    const updatedItems = editedTemplateItems.filter((_, i) => i !== index);
    setEditedTemplateItems(updatedItems);
  };

  // 항목 순서 변경 핸들러
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    const reordered = Array.from(editedTemplateItems);
    const [removed] = reordered.splice(result.source.index, 1);
    reordered.splice(result.destination.index, 0, removed);
    setEditedTemplateItems(reordered);
  };

  // 미리보기 모달 열기/닫기 핸들러
  const handleOpenPreviewModal = () => {
    if (selectedTemplate) {
      setShowPreviewModal(true);
    }
  };
  const handleClosePreviewModal = () => setShowPreviewModal(false);


  if (isLoading) {
    return <div>로딩 중...</div>;
  }

  if (error) {
    return <div className="error-message">오류: {error}</div>;
  }
  return (
    <div className="template-management-container">
      <div className="header-section">
        <h1>평가 템플릿 관리</h1>
        
        {/* 도움말 및 설명 섹션 */}
        <div className="help-section" style={{ 
          backgroundColor: '#f8f9fa', 
          border: '1px solid #e9ecef', 
          borderRadius: '8px', 
          padding: '16px', 
          marginBottom: '20px' 
        }}>
          <h3 style={{ margin: '0 0 12px 0', color: '#495057', fontSize: '16px' }}>📋 템플릿 관리 사용법</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            <div>
              <h4 style={{ margin: '0 0 8px 0', color: '#6c757d', fontSize: '14px' }}>🔧 기본 기능</h4>
              <ul style={{ margin: '0', paddingLeft: '16px', fontSize: '13px', color: '#6c757d' }}>
                <li>새 템플릿 생성: 평가 항목과 기준을 정의하여 템플릿 생성</li>
                <li>템플릿 수정: 기존 템플릿의 내용과 항목 수정</li>
                <li>템플릿 복제: 기존 템플릿을 복사하여 새 템플릿 생성</li>
                <li>템플릿 공유: 다른 사용자와 템플릿 공유</li>
              </ul>
            </div>
            <div>
              <h4 style={{ margin: '0 0 8px 0', color: '#6c757d', fontSize: '14px' }}>🎯 템플릿 활용</h4>
              <ul style={{ margin: '0', paddingLeft: '16px', fontSize: '13px', color: '#6c757d' }}>
                <li>프로젝트별 평가 기준 표준화</li>
                <li>평가 항목의 일관성 유지</li>
                <li>효율적인 평가 프로세스 관리</li>
                <li>과거 평가 데이터와의 비교 분석</li>
              </ul>
            </div>
            <div>
              <h4 style={{ margin: '0 0 8px 0', color: '#6c757d', fontSize: '14px' }}>💡 사용 팁</h4>
              <ul style={{ margin: '0', paddingLeft: '16px', fontSize: '13px', color: '#6c757d' }}>
                <li>검색 기능을 활용하여 원하는 템플릿 빠르게 찾기</li>
                <li>상태별 필터로 활성/비활성 템플릿 구분</li>
                <li>카드뷰로 템플릿 미리보기 확인</li>
                <li>드래그&드롭으로 평가 항목 순서 조정</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      {/* 검색 및 생성 버튼 */}
      <div className="toolbar">
        <input 
          type="text" 
          placeholder="템플릿 검색..." 
          value={searchTerm} 
          onChange={(e) => setSearchTerm(e.target.value)} 
        />
        <button onClick={() => setShowCreateModal(true)}>새 템플릿 생성</button>
      </div>

      {/* 필터/정렬 바 */}
      <div className="filter-bar">
        <div className="filter-group">
          <label htmlFor="filterStatus">상태</label>
          <select id="filterStatus" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setCurrentPage(1); }}>
            <option value="">전체</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="filterCreator">생성자</label>
          <input id="filterCreator" type="text" value={filterCreator} onChange={e => { setFilterCreator(e.target.value); setCurrentPage(1); }} placeholder="생성자 ID" />
        </div>
        <div className="filter-group">
          <label htmlFor="sortOption">정렬</label>
          <select id="sortOption" className="sort-select" value={sortOption} onChange={e => { setSortOption(e.target.value); setCurrentPage(1); }}>
            <option value="created_at_desc">최신순</option>
            <option value="created_at_asc">오래된순</option>
            <option value="name_asc">이름 오름차순</option>
            <option value="name_desc">이름 내림차순</option>
          </select>
        </div>
        <div className="filter-group">
          <label htmlFor="viewMode">보기</label>
          <select id="viewMode" value={viewMode} onChange={e => setViewMode(e.target.value)}>
            <option value="list">리스트뷰</option>
            <option value="card">카드뷰</option>
          </select>
        </div>
        <div className="filter-group" style={{ flexGrow: 1 }}>
          <input 
            type="text" 
            placeholder="템플릿 검색..." 
            value={searchTerm} 
            onChange={e => { setSearchTerm(e.target.value); setCurrentPage(1); }}
            aria-label="템플릿 검색"
          />
        </div>
        <button onClick={() => setShowCreateModal(true)}>새 템플릿 생성</button>
      </div>

      {/* 템플릿 목록 */}
      <div className="template-list">
        <h2>템플릿 목록</h2>
        {templates.length === 0 && <p>생성된 템플릿이 없습니다.</p>}
        {viewMode === 'list' ? (
          <ul>
            {templates.map(template => (
              <li key={template.id} onClick={() => handleSelectTemplate(template.id)}>
                <strong>{template.name}</strong> (v{template.version || 1}) - 상태: {template.status || 'N/A'}
                <button onClick={(e) => { e.stopPropagation(); handleCloneTemplate(template.id); }}>복제</button>
                <button onClick={(e) => { e.stopPropagation(); setSelectedTemplate(template); setShowShareModal(true); }}>공유</button>
                <button onClick={(e) => { e.stopPropagation(); handleDeleteTemplate(template.id); }}>아카이브</button>
                <select 
                  value={template.status || 'draft'} 
                  onChange={(e) => { e.stopPropagation(); handleChangeStatus(template.id, e.target.value);}}
                  onClick={(e) => e.stopPropagation()} // 이벤트 전파 중지
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="archived">Archived</option>
                </select>
              </li>
            ))}
          </ul>
        ) : (
          <div className="card-view">
            {templates.map(template => (
              <div key={template.id} className="template-card" tabIndex={0} onClick={() => handleSelectTemplate(template.id)}>
                <div className="card-header">
                  <span className="card-title">{template.name}</span>
                  <span className={`status-badge status-${template.status}`}>{template.status}</span>
                </div>
                <div className="card-meta">
                  <span>버전: v{template.version || 1}</span>
                  <span>생성자: {template.created_by}</span>
                </div>
                <div className="card-desc">{template.description}</div>
                <div className="card-actions">
                  <button onClick={e => { e.stopPropagation(); handleCloneTemplate(template.id); }}>복제</button>
                  <button onClick={e => { e.stopPropagation(); setSelectedTemplate(template); setShowShareModal(true); }}>공유</button>
                  <button onClick={e => { e.stopPropagation(); handleDeleteTemplate(template.id); }}>아카이브</button>
                  <select
                    value={template.status || 'draft'}
                    onChange={e => { e.stopPropagation(); handleChangeStatus(template.id, e.target.value); }}
                    onClick={e => e.stopPropagation()}
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 페이지네이션 UI */}
      {totalPages > 1 && (
        <div className="pagination">
          <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1}>&laquo;</button>
          <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>&lt;</button>
          <span>{currentPage} / {totalPages}</span>
          <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>&gt;</button>
          <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}>&raquo;</button>
        </div>
      )}

      {/* 템플릿 상세 정보 */}
      {selectedTemplate && (
        <div className="template-details">
          <h2>템플릿 상세: {selectedTemplate.name}</h2>
          <p><strong>ID:</strong> {selectedTemplate.id}</p>
          <p><strong>설명:</strong> {selectedTemplate.description}</p>
          <p><strong>버전:</strong> {selectedTemplate.version}</p>
          <p><strong>상태:</strong> {selectedTemplate.status}</p>
          <p><strong>생성자:</strong> {selectedTemplate.created_by}</p>
          <p><strong>프로젝트 ID:</strong> {selectedTemplate.project_id}</p>
          
          <h4>항목 목록:</h4>
          {selectedTemplate.items && selectedTemplate.items.length > 0 ? (
            <ul>
              {selectedTemplate.items.map((item, index) => (
                <li key={item.id || index}>{item.text}</li>
              ))}
            </ul>
          ) : (
            <p>등록된 항목이 없습니다.</p>
          )}

          {/* 버전 히스토리 표시 */}
          {selectedTemplate.version_history && selectedTemplate.version_history.length > 0 && (
            <div className="version-history">
              <h4>버전 히스토리</h4>
              <ul>
                {selectedTemplate.version_history.map((ver, idx) => (
                  <li key={ver.id || idx}>
                    v{ver.version}: {ver.name} ({ver.status}) - {ver.created_at}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 공유된 사용자 목록 표시 */}
          {selectedTemplate.shared_with && selectedTemplate.shared_with.length > 0 && (
            <div className="shared-with-list">
              <h4>공유된 사용자</h4>
              <ul>
                {selectedTemplate.shared_with.map((user, idx) => (
                  <li key={user.user_id || idx}>
                    {user.user_id} ({user.permission === 'edit' ? '편집' : '보기'})
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="template-actions">
            <button onClick={() => handleOpenEditModal(selectedTemplate)}>수정</button>
            <button onClick={handleOpenPreviewModal}>미리보기</button>
            <button onClick={() => handleCreateNewVersion(selectedTemplate.id)}>새 버전 만들기</button>
          </div>
        </div>
      )}

      {/* 새 템플릿 생성 모달 */}
      {showCreateModal && (
        <div className="modal">
          <div className="modal-content">
            <h3>새 템플릿 생성</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              const name = newTemplateName;
              const description = newTemplateDescription;
              const items = newTemplateItems.filter(item => item.text.trim() !== ''); // 빈 항목 제외
              handleCreateTemplate({ name, description, items });
            }}>
              <div>
                <label htmlFor="templateName">템플릿 이름:</label>
                <input 
                  type="text" 
                  id="templateName" 
                  name="templateName" 
                  value={newTemplateName} 
                  onChange={(e) => setNewTemplateName(e.target.value)} 
                  required 
                  placeholder="예: 기본 평가 템플릿"
                  title="템플릿의 고유한 이름을 입력하세요."
                />
              </div>
              <div>
                <label htmlFor="templateDescription">설명:</label>
                <textarea 
                  id="templateDescription" 
                  name="templateDescription" 
                  value={newTemplateDescription} 
                  onChange={(e) => setNewTemplateDescription(e.target.value)}
                  placeholder="템플릿에 대한 간단한 설명을 입력하세요."
                  title="템플릿의 용도 및 내용을 설명하는 텍스트입니다."
                />
              </div>
              <h4>항목 추가:</h4>
              {newTemplateItems.map((item, index) => (
                <div key={index} className="item-input-row">
                  <input 
                    type="text" 
                    value={item.text} 
                    onChange={(e) => handleNewTemplateItemChange(index, e.target.value)} 
                    placeholder={`항목 ${index + 1}`}
                    title="평가 항목 또는 기준을 입력하세요."
                  />
                  {newTemplateItems.length > 1 && (
                    <button type="button" onClick={() => handleRemoveItemFromNewTemplate(index)}>삭제</button>
                  )}
                </div>
              ))}
              <button type="button" onClick={handleAddItemToNewTemplate}>항목 추가</button>
              
              <div className="modal-actions">
                <button type="submit">생성</button>
                <button type="button" onClick={() => {
                  setShowCreateModal(false);
                  setNewTemplateName('');
                  setNewTemplateDescription('');
                  setNewTemplateItems([{ text: '' }]);
                }}>취소</button>
              </div>
            </form>
          </div>
        </div>
      )}
      
      {/* 공유 모달 */}
      {showShareModal && selectedTemplate && (
        <div className="modal">
          <div className="modal-content">
            <h3>템플릿 공유: {selectedTemplate.name}</h3>
            <div>
              <label htmlFor="userToShare">사용자 ID:</label>
              <input 
                type="text" 
                id="userToShare" 
                value={userToShare} 
                onChange={(e) => setUserToShare(e.target.value)} 
                placeholder="공유할 사용자 ID 입력"
                title="템플릿을 공유할 사용자의 ID를 입력하세요."
              />
            </div>
            <div>
              <label htmlFor="sharePermission">권한:</label>
              <select value={sharePermission} onChange={(e) => setSharePermission(e.target.value)}>
                <option value="view">보기</option>
                <option value="edit">편집</option>
              </select>
            </div>
            <button onClick={() => handleShareTemplate(selectedTemplate.id)}>공유하기</button>
            <button type="button" onClick={() => setShowShareModal(false)}>취소</button>
          </div>
        </div>
      )}

      {/* 템플릿 미리보기 모달 */}
      {showPreviewModal && selectedTemplate && (
        <div className="modal preview-modal">
          <div className="modal-content">
            <h3>템플릿 미리보기: {selectedTemplate.name} (v{selectedTemplate.version || 1})</h3>
            <p><strong>설명:</strong> {selectedTemplate.description}</p>
            <h4>항목:</h4>
            {selectedTemplate.items && selectedTemplate.items.length > 0 ? (
              <ul className="preview-items-list">
                {selectedTemplate.items.map((item, index) => (
                  <li key={item.id || index}>
                    <span className="item-number">{index + 1}.</span> {item.text}
                    {/* 실제 평가 화면처럼 입력 필드나 선택 옵션을 보여줄 수 있음 */}
                    <div className="preview-item-response">\
                      <input type="radio" name={`preview_item_${index}`} value="1" /> 매우 미흡
                      <input type="radio" name={`preview_item_${index}`} value="2" /> 미흡
                      <input type="radio" name={`preview_item_${index}`} value="3" /> 보통
                      <input type="radio" name={`preview_item_${index}`} value="4" /> 우수
                      <input type="radio" name={`preview_item_${index}`} value="5" /> 매우 우수
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p>표시할 항목이 없습니다.</p>
            )}
            <div className="modal-actions">
              <button type="button" onClick={handleClosePreviewModal}>닫기</button>
            </div>
          </div>
        </div>
      )}

      {/* 템플릿 수정 모달 */}
      {showEditModal && editingTemplate && (
        <div className="modal edit-modal">
          <div className="modal-content">
            <h3>템플릿 수정: {editingTemplate.name}</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              handleSaveEditedTemplate();
            }}>
              <div>
                <label htmlFor="editedTemplateName">템플릿 이름:</label>
                <input
                  type="text"
                  id="editedTemplateName"
                  value={editedTemplateName}
                  onChange={(e) => setEditedTemplateName(e.target.value)}
                  required
                  placeholder="예: 수정된 평가 템플릿"
                  title="템플릿의 새로운 이름을 입력하세요."
                />
              </div>
              <div>
                <label htmlFor="editedTemplateDescription">설명:</label>
                <textarea
                  id="editedTemplateDescription"
                  value={editedTemplateDescription}
                  onChange={(e) => setEditedTemplateDescription(e.target.value)}
                  placeholder="새로운 설명을 입력하세요."
                  title="템플릿의 새로운 설명을 입력하는 곳입니다."
                />
              </div>
              <h4>항목 편집 (드래그로 순서 변경):</h4>
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="edit-items-droppable">
                  {(provided) => (
                    <div ref={provided.innerRef} {...provided.droppableProps}>
                      {editedTemplateItems.map((item, index) => (
                        <Draggable key={index} draggableId={`item-${index}`} index={index}>
                          {(provided, snapshot) => (
                            <div
                              className={`item-input-row${snapshot.isDragging ? ' dragging' : ''}`}
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                            >
                              <span style={{cursor:'grab', marginRight:6}}>☰</span>
                              <input
                                type="text"
                                value={item.text}
                                onChange={(e) => handleEditedItemChange(index, e.target.value)}
                                placeholder={`항목 ${index + 1}`}
                                title="수정할 항목의 내용을 입력하세요."
                              />
                              {editedTemplateItems.length > 1 && (
                                <button type="button" onClick={() => handleRemoveItemFromEditedTemplate(index)}>삭제</button>
                              )}
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </DragDropContext>
              <button type="button" onClick={handleAddItemToEditedTemplate}>항목 추가</button>
              <div className="modal-actions">
                <button type="submit">저장</button>
                <button type="button" onClick={handleCloseEditModal}>취소</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default TemplateManagement;
