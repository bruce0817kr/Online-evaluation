import React, { useState, useEffect } from 'react';

const AIProviderManagement = ({ user }) => {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingProvider, setEditingProvider] = useState(null);
  const [testingProvider, setTestingProvider] = useState(null);
  const [serviceStatus, setServiceStatus] = useState(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  // 새 공급자 추가 폼 상태
  const [newProvider, setNewProvider] = useState({
    provider_name: 'openai',
    display_name: '',
    api_key: '',
    api_endpoint: '',
    model: 'gpt-4',
    is_active: true,
    priority: 1,
    max_tokens: 4096,
    temperature: 0.3
  });

  // 권한 확인
  if (!user || user.role !== 'admin') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">🔧 AI 공급자 관리</h2>
        <p className="text-gray-600">이 기능은 관리자만 사용할 수 있습니다.</p>
      </div>
    );
  }

  useEffect(() => {
    loadProviders();
    loadServiceStatus();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('인증 토큰이 없습니다. 다시 로그인해주세요.');
      }

      const response = await fetch(`${BACKEND_URL}/api/admin/ai/providers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProviders(Array.isArray(data) ? data : []);
      } else if (response.status === 401) {
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (response.status === 403) {
        throw new Error('AI 공급자 관리 권한이 없습니다.');
      } else if (response.status === 404) {
        console.warn('AI 공급자 API 엔드포인트를 찾을 수 없습니다.');
        setProviders([]);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `공급자 목록을 불러올 수 없습니다 (${response.status})`);
      }
    } catch (err) {
      console.error('AI 공급자 목록 로드 오류:', err);
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setError('네트워크 연결을 확인해주세요.');
      } else {
        setError(err.message);
      }
      setProviders([]);
    } finally {
      setLoading(false);
    }
  };

  const loadServiceStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/ai/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setServiceStatus(data);
      }
    } catch (err) {
      console.error('서비스 상태 조회 실패:', err);
    }
  };

  const handleAddProvider = async (e) => {
    e.preventDefault();
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/ai/providers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newProvider)
      });

      if (response.ok) {
        await loadProviders();
        await loadServiceStatus();
        setShowAddForm(false);
        setNewProvider({
          provider_name: 'openai',
          display_name: '',
          api_key: '',
          api_endpoint: '',
          model: 'gpt-4',
          is_active: true,
          priority: 1,
          max_tokens: 4096,
          temperature: 0.3
        });
        alert('AI 공급자가 성공적으로 추가되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '공급자 추가에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleUpdateProvider = async (providerId, updateData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/ai/providers/${providerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        await loadProviders();
        await loadServiceStatus();
        setEditingProvider(null);
        alert('공급자 설정이 업데이트되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '업데이트에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleDeleteProvider = async (providerId) => {
    if (!confirm('정말로 이 AI 공급자를 삭제하시겠습니까?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/ai/providers/${providerId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await loadProviders();
        await loadServiceStatus();
        alert('AI 공급자가 삭제되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '삭제에 실패했습니다');
      }
    } catch (err) {
      alert(`오류: ${err.message}`);
    }
  };

  const handleTestProvider = async (providerId) => {
    try {
      setTestingProvider(providerId);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/admin/ai/providers/${providerId}/test`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          alert(`✅ 연결 테스트 성공: ${result.message}`);
        } else {
          alert(`❌ 연결 테스트 실패: ${result.message}`);
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '테스트에 실패했습니다');
      }
    } catch (err) {
      alert(`테스트 오류: ${err.message}`);
    } finally {
      setTestingProvider(null);
    }
  };

  const getProviderDisplayName = (providerName) => {
    const displayNames = {
      'openai': 'OpenAI',
      'anthropic': 'Anthropic (Claude)',
      'google': 'Google (Gemini)',
      'groq': 'Groq'
    };
    return displayNames[providerName] || providerName;
  };

  const getProviderIcon = (providerName) => {
    const icons = {
      'openai': '🤖',
      'anthropic': '🧠',
      'google': '🔍',
      'groq': '⚡'
    };
    return icons[providerName] || '🔧';
  };

  const [availableModels, setAvailableModels] = useState({});
  const [loadingModels, setLoadingModels] = useState({});

  const getAvailableModels = (providerName) => {
    // 캐시된 모델이 있으면 반환
    if (availableModels[providerName]) {
      return availableModels[providerName];
    }
    
    // 기본 모델 반환 (동적 로딩 전까지)
    const defaultModels = {
      'openai': [
        { value: 'gpt-4', label: 'GPT-4' },
        { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
      ],
      'anthropic': [
        { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' },
        { value: 'claude-3-sonnet-20240229', label: 'Claude 3 Sonnet' },
        { value: 'claude-3-haiku-20240307', label: 'Claude 3 Haiku' }
      ],
      'google': [
        { value: 'gemini-pro', label: 'Gemini Pro' },
        { value: 'gemini-pro-vision', label: 'Gemini Pro Vision' }
      ],
      'groq': [
        { value: 'llama3-70b-8192', label: 'Llama 3 70B' },
        { value: 'llama3-8b-8192', label: 'Llama 3 8B' }
      ]
    };
    return defaultModels[providerName] || [{ value: 'default', label: 'Default Model' }];
  };

  const loadDynamicModels = async (providerName, apiKey = null) => {
    try {
      setLoadingModels(prev => ({ ...prev, [providerName]: true }));
      
      const token = localStorage.getItem('token');
      let url = `${BACKEND_URL}/api/admin/ai/providers/${providerName}/models`;
      
      // API 키가 제공된 경우 쿼리 파라미터로 추가
      if (apiKey) {
        url += `?api_key=${encodeURIComponent(apiKey)}`;
      }
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const models = data.models.map(model => ({
          value: model.value,
          label: model.label,
          description: model.description
        }));
        
        setAvailableModels(prev => ({
          ...prev,
          [providerName]: models
        }));
        
        console.log(`✅ ${providerName} 모델 목록 동적 로드 완료 (${data.source}):`, models);
        return models;
      } else {
        console.warn(`⚠️ ${providerName} 모델 목록 로드 실패, 기본 목록 사용`);
        return getAvailableModels(providerName);
      }
    } catch (err) {
      console.error(`❌ ${providerName} 모델 로드 오류:`, err);
      return getAvailableModels(providerName);
    } finally {
      setLoadingModels(prev => ({ ...prev, [providerName]: false }));
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-500">로딩 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">🔧 AI 공급자 관리</h2>
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            + 공급자 추가
          </button>
        </div>

        {/* 서비스 상태 카드 */}
        {serviceStatus && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{serviceStatus.total_providers}</div>
              <div className="text-sm text-blue-700">총 공급자</div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{serviceStatus.active_providers}</div>
              <div className="text-sm text-green-700">활성 공급자</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {serviceStatus.default_provider || 'None'}
              </div>
              <div className="text-sm text-purple-700">기본 공급자</div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {new Date(serviceStatus.last_updated).toLocaleTimeString()}
              </div>
              <div className="text-sm text-gray-700">마지막 업데이트</div>
            </div>
          </div>
        )}
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* 공급자 추가 폼 */}
        {showAddForm && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-medium mb-4">새 AI 공급자 추가</h3>
            <form onSubmit={handleAddProvider} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    공급자 유형
                  </label>
                  <select
                    value={newProvider.provider_name}
                    onChange={async (e) => {
                      const providerName = e.target.value;
                      const defaultModel = getAvailableModels(providerName)[0]?.value || 'default';
                      setNewProvider(prev => ({
                        ...prev,
                        provider_name: providerName,
                        display_name: getProviderDisplayName(providerName),
                        model: defaultModel
                      }));
                      
                      // 공급자 변경 시 모델 목록 미리 로드
                      await loadDynamicModels(providerName);
                    }}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="google">Google (Gemini)</option>
                    <option value="groq">Groq</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    표시 이름
                  </label>
                  <input
                    type="text"
                    value={newProvider.display_name}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, display_name: e.target.value }))}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    모델 선택
                  </label>
                  <button
                    type="button"
                    onClick={() => loadDynamicModels(newProvider.provider_name, newProvider.api_key)}
                    disabled={loadingModels[newProvider.provider_name]}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                    title="최신 모델 목록 불러오기"
                  >
                    {loadingModels[newProvider.provider_name] ? '로딩...' : '🔄 새로고침'}
                  </button>
                </div>
                <select
                  value={newProvider.model}
                  onChange={(e) => setNewProvider(prev => ({ ...prev, model: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  required
                >
                  {getAvailableModels(newProvider.provider_name).map(model => (
                    <option key={model.value} value={model.value} title={model.description}>
                      {model.label}
                    </option>
                  ))}
                </select>
                {loadingModels[newProvider.provider_name] && (
                  <div className="text-xs text-gray-500 mt-1">
                    최신 모델 목록을 불러오는 중...
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API 키
                </label>
                <input
                  type="password"
                  value={newProvider.api_key}
                  onChange={(e) => setNewProvider(prev => ({ ...prev, api_key: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="API 키를 입력하세요"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    우선순위
                  </label>
                  <input
                    type="number"
                    value={newProvider.priority}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    최대 토큰
                  </label>
                  <input
                    type="number"
                    value={newProvider.max_tokens}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={newProvider.temperature}
                    onChange={(e) => setNewProvider(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="isActive"
                  checked={newProvider.is_active}
                  onChange={(e) => setNewProvider(prev => ({ ...prev, is_active: e.target.checked }))}
                  className="mr-2"
                />
                <label htmlFor="isActive" className="text-sm text-gray-700">
                  활성화
                </label>
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 bg-gray-500 text-white border border-gray-500 rounded-lg hover:bg-gray-600"
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  추가
                </button>
              </div>
            </form>
          </div>
        )}

        {/* 공급자 목록 */}
        <div className="space-y-4">
          {providers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              설정된 AI 공급자가 없습니다.
            </div>
          ) : (
            providers.map((provider) => (
              <div key={provider.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getProviderIcon(provider.provider_name)}</span>
                    <div>
                      <h3 className="font-medium">{provider.display_name}</h3>
                      <p className="text-sm text-gray-600">
                        {provider.provider_name} • 우선순위: {provider.priority}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      provider.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {provider.is_active ? '활성' : '비활성'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleTestProvider(provider.id)}
                      disabled={testingProvider === provider.id}
                      className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
                    >
                      {testingProvider === provider.id ? '테스트 중...' : '연결 테스트'}
                    </button>
                    <button
                      onClick={() => setEditingProvider(provider)}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      편집
                    </button>
                    <button
                      onClick={() => handleDeleteProvider(provider.id)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      삭제
                    </button>
                  </div>
                </div>

                <div className="mt-2 text-sm text-gray-600">
                  모델: {provider.model || 'N/A'} • 최대 토큰: {provider.max_tokens} • Temperature: {provider.temperature}
                </div>
              </div>
            ))
          )}
        </div>

        {/* 편집 모달 */}
        {editingProvider && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-medium mb-4">공급자 설정 편집</h3>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.target);
                  const updateData = {
                    display_name: formData.get('display_name'),
                    model: formData.get('model'),
                    is_active: formData.has('is_active'),
                    priority: parseInt(formData.get('priority')),
                    max_tokens: parseInt(formData.get('max_tokens')),
                    temperature: parseFloat(formData.get('temperature'))
                  };
                  
                  const newApiKey = formData.get('api_key');
                  if (newApiKey) {
                    updateData.api_key = newApiKey;
                  }
                  
                  handleUpdateProvider(editingProvider.id, updateData);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    표시 이름
                  </label>
                  <input
                    name="display_name"
                    type="text"
                    defaultValue={editingProvider.display_name}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    required
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">
                      모델 선택
                    </label>
                    <button
                      type="button"
                      onClick={() => loadDynamicModels(editingProvider.provider_name)}
                      disabled={loadingModels[editingProvider.provider_name]}
                      className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                      title="최신 모델 목록 불러오기"
                    >
                      {loadingModels[editingProvider.provider_name] ? '로딩...' : '🔄 새로고침'}
                    </button>
                  </div>
                  <select
                    name="model"
                    defaultValue={editingProvider.model || getAvailableModels(editingProvider.provider_name)[0]?.value}
                    className="w-full p-2 border border-gray-300 rounded-lg"
                    required
                  >
                    {getAvailableModels(editingProvider.provider_name).map(model => (
                      <option key={model.value} value={model.value} title={model.description}>
                        {model.label}
                      </option>
                    ))}
                  </select>
                  {loadingModels[editingProvider.provider_name] && (
                    <div className="text-xs text-gray-500 mt-1">
                      최신 모델 목록을 불러오는 중...
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API 키 (변경하려면 입력)
                  </label>
                  <input
                    name="api_key"
                    type="password"
                    placeholder="새 API 키를 입력하세요"
                    className="w-full p-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      우선순위
                    </label>
                    <input
                      name="priority"
                      type="number"
                      defaultValue={editingProvider.priority}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                      min="1"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      최대 토큰
                    </label>
                    <input
                      name="max_tokens"
                      type="number"
                      defaultValue={editingProvider.max_tokens}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Temperature
                    </label>
                    <input
                      name="temperature"
                      type="number"
                      step="0.1"
                      min="0"
                      max="2"
                      defaultValue={editingProvider.temperature}
                      className="w-full p-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div className="flex items-center">
                  <input
                    name="is_active"
                    type="checkbox"
                    defaultChecked={editingProvider.is_active}
                    className="mr-2"
                  />
                  <label className="text-sm text-gray-700">활성화</label>
                </div>

                <div className="flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setEditingProvider(null)}
                    className="px-4 py-2 bg-gray-500 text-white border border-gray-500 rounded-lg hover:bg-gray-600"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    저장
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIProviderManagement;