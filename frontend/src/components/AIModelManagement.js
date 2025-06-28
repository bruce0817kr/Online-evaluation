import React, { useState, useEffect } from 'react';
import './AIModelManagement.css';

const AIModelManagement = ({ user }) => {
  const [models, setModels] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [activeTab, setActiveTab] = useState('manage'); // manage, templates, test

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  // 새 모델 생성 폼 상태
  const [newModel, setNewModel] = useState({
    model_id: '',
    provider: 'openai',
    model_name: '',
    display_name: '',
    api_endpoint: '',
    parameters: {},
    cost_per_token: 0.0,
    max_tokens: 4096,
    context_window: 4096,
    capabilities: [],
    quality_score: 0.5,
    speed_score: 0.5,
    cost_score: 0.5,
    reliability_score: 0.5,
    is_default: false
  });

  const [testResults, setTestResults] = useState(null);
  const [testingModel, setTestingModel] = useState(null);

  useEffect(() => {
    loadModels();
    loadTemplates();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/available?include_inactive=true`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const modelsData = await response.json();
        setModels(modelsData);
      } else {
        throw new Error('모델 목록 로드 실패');
      }
    } catch (err) {
      setError('모델 목록을 불러오는데 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/templates/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const templatesData = await response.json();
        setTemplates(templatesData.templates || []);
      }
    } catch (err) {
      console.error('템플릿 로드 실패:', err);
    }
  };

  const handleCreateModel = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // capabilities를 배열로 변환
      const capabilitiesArray = typeof newModel.capabilities === 'string' 
        ? newModel.capabilities.split(',').map(c => c.trim()).filter(c => c)
        : newModel.capabilities;

      const modelData = {
        ...newModel,
        capabilities: capabilitiesArray,
        parameters: typeof newModel.parameters === 'string' 
          ? JSON.parse(newModel.parameters || '{}')
          : newModel.parameters
      };

      const response = await fetch(`${BACKEND_URL}/api/ai-models/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(modelData)
      });

      if (response.ok) {
        const createdModel = await response.json();
        setModels(prev => [...prev, createdModel.model]);
        setShowCreateModal(false);
        resetNewModel();
        setError(null);
        alert('모델이 성공적으로 생성되었습니다!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '모델 생성 실패');
      }
    } catch (err) {
      setError('모델 생성에 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateModel = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const updateData = {
        display_name: editingModel.display_name,
        api_endpoint: editingModel.api_endpoint,
        parameters: typeof editingModel.parameters === 'string' 
          ? JSON.parse(editingModel.parameters || '{}')
          : editingModel.parameters,
        cost_per_token: editingModel.cost_per_token,
        max_tokens: editingModel.max_tokens,
        context_window: editingModel.context_window,
        capabilities: typeof editingModel.capabilities === 'string' 
          ? editingModel.capabilities.split(',').map(c => c.trim()).filter(c => c)
          : editingModel.capabilities,
        quality_score: editingModel.quality_score,
        speed_score: editingModel.speed_score,
        cost_score: editingModel.cost_score,
        reliability_score: editingModel.reliability_score,
        is_default: editingModel.is_default
      };

      const response = await fetch(`${BACKEND_URL}/api/ai-models/${editingModel.model_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        const updatedModel = await response.json();
        setModels(prev => prev.map(m => 
          m.model_id === editingModel.model_id ? updatedModel.model : m
        ));
        setShowEditModal(false);
        setEditingModel(null);
        setError(null);
        alert('모델이 성공적으로 업데이트되었습니다!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '모델 업데이트 실패');
      }
    } catch (err) {
      setError('모델 업데이트에 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteModel = async (modelId) => {
    if (!window.confirm('정말로 이 모델을 삭제하시겠습니까?')) {
      return;
    }

    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/${modelId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setModels(prev => prev.filter(m => m.model_id !== modelId));
        setError(null);
        alert('모델이 성공적으로 삭제되었습니다!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '모델 삭제 실패');
      }
    } catch (err) {
      setError('모델 삭제에 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFromTemplate = async (templateName) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/templates/${templateName}/create`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const createdModel = await response.json();
        setModels(prev => [...prev, createdModel.model]);
        setError(null);
        alert(`${templateName} 템플릿으로 모델이 생성되었습니다!`);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '템플릿으로부터 모델 생성 실패');
      }
    } catch (err) {
      setError('템플릿으로부터 모델 생성에 실패했습니다: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (modelId) => {
    try {
      setTestingModel(modelId);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/${modelId}/test-connection`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        setTestResults(prev => ({
          ...prev,
          [modelId]: result
        }));
      } else {
        const errorData = await response.json();
        setTestResults(prev => ({
          ...prev,
          [modelId]: { success: false, error: errorData.detail || '연결 테스트 실패' }
        }));
      }
    } catch (err) {
      setTestResults(prev => ({
        ...prev,
        [modelId]: { success: false, error: err.message }
      }));
    } finally {
      setTestingModel(null);
    }
  };

  const resetNewModel = () => {
    setNewModel({
      model_id: '',
      provider: 'openai',
      model_name: '',
      display_name: '',
      api_endpoint: '',
      parameters: {},
      cost_per_token: 0.0,
      max_tokens: 4096,
      context_window: 4096,
      capabilities: [],
      quality_score: 0.5,
      speed_score: 0.5,
      cost_score: 0.5,
      reliability_score: 0.5,
      is_default: false
    });
  };

  const openEditModal = (model) => {
    setEditingModel({
      ...model,
      capabilities: Array.isArray(model.capabilities) 
        ? model.capabilities.join(', ') 
        : model.capabilities,
      parameters: JSON.stringify(model.parameters || {}, null, 2)
    });
    setShowEditModal(true);
  };

  const getProviderIcon = (provider) => {
    const icons = {
      'openai': '🤖',
      'anthropic': '🧠',
      'google': '🔍',
      'cohere': '🌐',
      'novita': '⚡',
      'local': '💻'
    };
    return icons[provider] || '🤖';
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': '#28a745',
      'inactive': '#6c757d',
      'maintenance': '#ffc107',
      'error': '#dc3545'
    };
    return colors[status] || '#6c757d';
  };

  if (!['admin', 'secretary'].includes(user.role)) {
    return (
      <div className="ai-model-management">
        <div className="access-denied">
          <h2>🚫 접근 권한 없음</h2>
          <p>AI 모델 관리 기능은 관리자와 간사만 사용할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-model-management">
      <div className="management-header">
        <h2>🤖 AI 모델 관리</h2>
        <p>AI 모델을 생성, 수정, 삭제하고 연결을 테스트하세요</p>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="close-error">✕</button>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'manage' ? 'active' : ''}`}
          onClick={() => setActiveTab('manage')}
        >
          🔧 모델 관리
        </button>
        <button
          className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          📋 템플릿
        </button>
        <button
          className={`tab-btn ${activeTab === 'test' ? 'active' : ''}`}
          onClick={() => setActiveTab('test')}
        >
          🧪 연결 테스트
        </button>
      </div>

      <div className="tab-content">
        {/* 모델 관리 탭 */}
        {activeTab === 'manage' && (
          <div className="manage-tab">
            <div className="actions-bar">
              <button 
                className="create-model-btn"
                onClick={() => setShowCreateModal(true)}
              >
                ➕ 새 모델 생성
              </button>
              <button 
                className="refresh-btn"
                onClick={loadModels}
                disabled={loading}
              >
                🔄 새로고침
              </button>
            </div>

            <div className="models-grid">
              {models.map((model) => (
                <div key={model.model_id} className="model-management-card">
                  <div className="model-header">
                    <div className={`model-icon ${model.provider}`}>
                      {getProviderIcon(model.provider)}
                    </div>
                    <div className="model-info">
                      <h4>{model.display_name}</h4>
                      <p>{model.provider.toUpperCase()} - {model.model_name}</p>
                    </div>
                    <div 
                      className="model-status"
                      style={{ backgroundColor: getStatusColor(model.status) }}
                    >
                      {model.status}
                    </div>
                  </div>

                  <div className="model-details">
                    <p><strong>토큰당 비용:</strong> ${model.cost_per_token}</p>
                    <p><strong>최대 토큰:</strong> {model.max_tokens.toLocaleString()}</p>
                    <p><strong>컨텍스트 윈도우:</strong> {model.context_window.toLocaleString()}</p>
                    <p><strong>기능:</strong> {Array.isArray(model.capabilities) ? model.capabilities.join(', ') : model.capabilities}</p>
                  </div>

                  <div className="model-scores">
                    <div className="score">
                      <span>품질: {(model.quality_score * 100).toFixed(0)}%</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill quality"
                          style={{ width: `${model.quality_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="score">
                      <span>속도: {(model.speed_score * 100).toFixed(0)}%</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill speed"
                          style={{ width: `${model.speed_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="score">
                      <span>비용: {(model.cost_score * 100).toFixed(0)}%</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill cost"
                          style={{ width: `${model.cost_score * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  <div className="model-actions">
                    <button 
                      className="edit-btn"
                      onClick={() => openEditModal(model)}
                    >
                      ✏️ 수정
                    </button>
                    <button 
                      className="delete-btn"
                      onClick={() => handleDeleteModel(model.model_id)}
                      disabled={model.is_default}
                    >
                      🗑️ 삭제
                    </button>
                  </div>

                  {model.is_default && (
                    <div className="default-badge">기본 모델</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 템플릿 탭 */}
        {activeTab === 'templates' && (
          <div className="templates-tab">
            <h3>📋 모델 템플릿</h3>
            <p>사전 정의된 템플릿으로 빠르게 모델을 생성하세요</p>
            
            <div className="templates-grid">
              {templates.map((template) => (
                <div key={template.name} className="template-card">
                  <div className="template-header">
                    <h4>{template.name}</h4>
                    <div className={`provider-badge ${template.provider}`}>
                      {getProviderIcon(template.provider)} {template.provider.toUpperCase()}
                    </div>
                  </div>
                  
                  <div className="template-description">
                    <p>{template.description}</p>
                  </div>
                  
                  <div className="template-features">
                    <strong>포함된 기능:</strong>
                    <ul>
                      {template.capabilities.map((capability, index) => (
                        <li key={index}>{capability}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <button 
                    className="create-from-template-btn"
                    onClick={() => handleCreateFromTemplate(template.name)}
                    disabled={loading}
                  >
                    🚀 템플릿으로 생성
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 연결 테스트 탭 */}
        {activeTab === 'test' && (
          <div className="test-tab">
            <h3>🧪 모델 연결 테스트</h3>
            <p>각 AI 모델의 연결 상태를 확인하세요</p>
            
            <div className="test-grid">
              {models.filter(m => m.status === 'active').map((model) => (
                <div key={model.model_id} className="test-card">
                  <div className="test-header">
                    <div className={`model-icon ${model.provider}`}>
                      {getProviderIcon(model.provider)}
                    </div>
                    <div className="test-info">
                      <h4>{model.display_name}</h4>
                      <p>{model.provider.toUpperCase()}</p>
                    </div>
                  </div>
                  
                  <button 
                    className="test-connection-btn"
                    onClick={() => handleTestConnection(model.model_id)}
                    disabled={testingModel === model.model_id}
                  >
                    {testingModel === model.model_id ? '🔄 테스트 중...' : '🔗 연결 테스트'}
                  </button>
                  
                  {testResults && testResults[model.model_id] && (
                    <div className={`test-result ${testResults[model.model_id].is_healthy ? 'success' : 'error'}`}>
                      {testResults[model.model_id].is_healthy ? (
                        <div>
                          <span className="success-icon">✅</span>
                          <div className="test-summary">
                            <span>연결 성공</span>
                            <div className="test-metrics">
                              <small>건강도: {(testResults[model.model_id].health_score * 100).toFixed(0)}%</small>
                              <small>평균 응답: {testResults[model.model_id].avg_response_time?.toFixed(2)}초</small>
                              <small>성공/전체: {testResults[model.model_id].successful_tests}/{testResults[model.model_id].total_tests}</small>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div>
                          <span className="error-icon">❌</span>
                          <div className="test-summary">
                            <span>연결 불안정</span>
                            <div className="test-metrics">
                              <small>건강도: {(testResults[model.model_id].health_score * 100).toFixed(0)}%</small>
                              <small>성공/전체: {testResults[model.model_id].successful_tests}/{testResults[model.model_id].total_tests}</small>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 새 모델 생성 모달 */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>➕ 새 AI 모델 생성</h3>
              <button 
                className="close-modal"
                onClick={() => {
                  setShowCreateModal(false);
                  resetNewModel();
                }}
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleCreateModel} className="model-form">
              <div className="form-grid">
                <div className="form-field">
                  <label>모델 ID *</label>
                  <input 
                    type="text"
                    value={newModel.model_id}
                    onChange={(e) => setNewModel(prev => ({...prev, model_id: e.target.value}))}
                    pattern="^[a-z0-9-]+$"
                    title="소문자, 숫자, 하이픈만 사용 가능"
                    required
                  />
                </div>
                
                <div className="form-field">
                  <label>제공업체 *</label>
                  <select 
                    value={newModel.provider}
                    onChange={(e) => setNewModel(prev => ({...prev, provider: e.target.value}))}
                    required
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google</option>
                    <option value="cohere">Cohere</option>
                    <option value="novita">Novita AI</option>
                    <option value="local">Local</option>
                  </select>
                </div>
                
                <div className="form-field">
                  <label>모델명 *</label>
                  <input 
                    type="text"
                    value={newModel.model_name}
                    onChange={(e) => setNewModel(prev => ({...prev, model_name: e.target.value}))}
                    placeholder="예: gpt-4, claude-3-opus"
                    required
                  />
                </div>
                
                <div className="form-field">
                  <label>표시명 *</label>
                  <input 
                    type="text"
                    value={newModel.display_name}
                    onChange={(e) => setNewModel(prev => ({...prev, display_name: e.target.value}))}
                    placeholder="예: GPT-4 (OpenAI)"
                    required
                  />
                </div>
                
                <div className="form-field">
                  <label>API 엔드포인트</label>
                  <input 
                    type="url"
                    value={newModel.api_endpoint}
                    onChange={(e) => setNewModel(prev => ({...prev, api_endpoint: e.target.value}))}
                    placeholder="커스텀 API 엔드포인트"
                  />
                </div>
                
                <div className="form-field">
                  <label>토큰당 비용</label>
                  <input 
                    type="number"
                    step="0.000001"
                    value={newModel.cost_per_token}
                    onChange={(e) => setNewModel(prev => ({...prev, cost_per_token: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>최대 토큰</label>
                  <input 
                    type="number"
                    value={newModel.max_tokens}
                    onChange={(e) => setNewModel(prev => ({...prev, max_tokens: parseInt(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>컨텍스트 윈도우</label>
                  <input 
                    type="number"
                    value={newModel.context_window}
                    onChange={(e) => setNewModel(prev => ({...prev, context_window: parseInt(e.target.value)}))}
                  />
                </div>
              </div>
              
              <div className="form-field full-width">
                <label>기능 목록 (쉼표로 구분)</label>
                <input 
                  type="text"
                  value={Array.isArray(newModel.capabilities) ? newModel.capabilities.join(', ') : newModel.capabilities}
                  onChange={(e) => setNewModel(prev => ({...prev, capabilities: e.target.value}))}
                  placeholder="예: text-generation, analysis, coding"
                />
              </div>
              
              <div className="score-fields">
                <div className="form-field">
                  <label>품질 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={newModel.quality_score}
                    onChange={(e) => setNewModel(prev => ({...prev, quality_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>속도 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={newModel.speed_score}
                    onChange={(e) => setNewModel(prev => ({...prev, speed_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>비용 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={newModel.cost_score}
                    onChange={(e) => setNewModel(prev => ({...prev, cost_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>안정성 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={newModel.reliability_score}
                    onChange={(e) => setNewModel(prev => ({...prev, reliability_score: parseFloat(e.target.value)}))}
                  />
                </div>
              </div>
              
              <div className="form-field checkbox-field">
                <label>
                  <input 
                    type="checkbox"
                    checked={newModel.is_default}
                    onChange={(e) => setNewModel(prev => ({...prev, is_default: e.target.checked}))}
                  />
                  기본 모델로 설정
                </label>
              </div>
              
              <div className="form-actions">
                <button 
                  type="button"
                  className="cancel-btn"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetNewModel();
                  }}
                >
                  취소
                </button>
                <button 
                  type="submit"
                  className="create-btn"
                  disabled={loading}
                >
                  {loading ? '생성 중...' : '모델 생성'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 모델 편집 모달 */}
      {showEditModal && editingModel && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3>✏️ 모델 편집: {editingModel.display_name}</h3>
              <button 
                className="close-modal"
                onClick={() => {
                  setShowEditModal(false);
                  setEditingModel(null);
                }}
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleUpdateModel} className="model-form">
              <div className="form-grid">
                <div className="form-field">
                  <label>표시명</label>
                  <input 
                    type="text"
                    value={editingModel.display_name}
                    onChange={(e) => setEditingModel(prev => ({...prev, display_name: e.target.value}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>API 엔드포인트</label>
                  <input 
                    type="url"
                    value={editingModel.api_endpoint || ''}
                    onChange={(e) => setEditingModel(prev => ({...prev, api_endpoint: e.target.value}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>토큰당 비용</label>
                  <input 
                    type="number"
                    step="0.000001"
                    value={editingModel.cost_per_token}
                    onChange={(e) => setEditingModel(prev => ({...prev, cost_per_token: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>최대 토큰</label>
                  <input 
                    type="number"
                    value={editingModel.max_tokens}
                    onChange={(e) => setEditingModel(prev => ({...prev, max_tokens: parseInt(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>컨텍스트 윈도우</label>
                  <input 
                    type="number"
                    value={editingModel.context_window}
                    onChange={(e) => setEditingModel(prev => ({...prev, context_window: parseInt(e.target.value)}))}
                  />
                </div>
              </div>
              
              <div className="form-field full-width">
                <label>기능 목록 (쉼표로 구분)</label>
                <input 
                  type="text"
                  value={editingModel.capabilities}
                  onChange={(e) => setEditingModel(prev => ({...prev, capabilities: e.target.value}))}
                />
              </div>
              
              <div className="score-fields">
                <div className="form-field">
                  <label>품질 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={editingModel.quality_score}
                    onChange={(e) => setEditingModel(prev => ({...prev, quality_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>속도 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={editingModel.speed_score}
                    onChange={(e) => setEditingModel(prev => ({...prev, speed_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>비용 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={editingModel.cost_score}
                    onChange={(e) => setEditingModel(prev => ({...prev, cost_score: parseFloat(e.target.value)}))}
                  />
                </div>
                
                <div className="form-field">
                  <label>안정성 점수 (0-1)</label>
                  <input 
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={editingModel.reliability_score}
                    onChange={(e) => setEditingModel(prev => ({...prev, reliability_score: parseFloat(e.target.value)}))}
                  />
                </div>
              </div>
              
              <div className="form-field checkbox-field">
                <label>
                  <input 
                    type="checkbox"
                    checked={editingModel.is_default}
                    onChange={(e) => setEditingModel(prev => ({...prev, is_default: e.target.checked}))}
                  />
                  기본 모델로 설정
                </label>
              </div>
              
              <div className="form-actions">
                <button 
                  type="button"
                  className="cancel-btn"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingModel(null);
                  }}
                >
                  취소
                </button>
                <button 
                  type="submit"
                  className="update-btn"
                  disabled={loading}
                >
                  {loading ? '업데이트 중...' : '모델 업데이트'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIModelManagement;