import React, { useState, useEffect } from 'react';
import './AIModelDashboard.css';
import SmartModelTester from './SmartModelTester.js';

const AIModelDashboard = ({ user }) => {
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [performanceData, setPerformanceData] = useState({});
  const [usageSummary, setUsageSummary] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('models'); // models, performance, comparison, testing, settings

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadAvailableModels(),
        loadUsageSummary(),
        loadHealthStatus()
      ]);
    } catch (err) {
      setError('대시보드 데이터 로드에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableModels = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/available`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const models = await response.json();
        setAvailableModels(models);
        
        // Set default model if none selected
        if (!selectedModel && models.length > 0) {
          const defaultModel = models.find(m => m.is_default) || models[0];
          setSelectedModel(defaultModel);
          loadModelPerformance(defaultModel.model_id);
        }
      }
    } catch (err) {
      console.error('모델 목록 로드 실패:', err);
    }
  };

  const loadModelPerformance = async (modelId, timeframe = '7d') => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${BACKEND_URL}/api/ai-models/${modelId}/performance?timeframe=${timeframe}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        setPerformanceData(prev => ({
          ...prev,
          [modelId]: data.performance
        }));
      }
    } catch (err) {
      console.error('성능 데이터 로드 실패:', err);
    }
  };

  const loadUsageSummary = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/usage-stats/summary`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setUsageSummary(data.summary);
      }
    } catch (err) {
      console.error('사용량 요약 로드 실패:', err);
    }
  };

  const loadHealthStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/health/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setHealthStatus(data.health_status);
      }
    } catch (err) {
      console.error('건강 상태 로드 실패:', err);
    }
  };

  const handleModelSelect = (model) => {
    setSelectedModel(model);
    loadModelPerformance(model.model_id);
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

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  if (!['admin', 'secretary'].includes(user.role)) {
    return (
      <div className="ai-model-dashboard">
        <div className="access-denied">
          <h2>🚫 접근 권한 없음</h2>
          <p>AI 모델 관리 기능은 관리자와 간사만 사용할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-model-dashboard">
      <div className="dashboard-header">
        <h2>🤖 AI 모델 관리 대시보드</h2>
        <p>AI 모델을 설정하고 성능을 모니터링하세요</p>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="close-error">✕</button>
        </div>
      )}

      {/* 요약 카드 */}
      {usageSummary && (
        <div className="summary-cards">
          <div className="summary-card">
            <div className="card-icon">🤖</div>
            <div className="card-content">
              <h3>{usageSummary.total_models}</h3>
              <p>전체 모델</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon">✅</div>
            <div className="card-content">
              <h3>{usageSummary.active_models}</h3>
              <p>활성 모델</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon">📊</div>
            <div className="card-content">
              <h3>{usageSummary.total_requests.toLocaleString()}</h3>
              <p>총 요청 수</p>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <h3>{formatCurrency(usageSummary.total_cost)}</h3>
              <p>총 비용</p>
            </div>
          </div>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          🤖 모델 관리
        </button>
        <button
          className={`tab-btn ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          📊 성능 모니터링
        </button>
        <button
          className={`tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
          onClick={() => setActiveTab('comparison')}
        >
          ⚖️ 모델 비교
        </button>
        <button
          className={`tab-btn ${activeTab === 'testing' ? 'active' : ''}`}
          onClick={() => setActiveTab('testing')}
        >
          🧪 스마트 테스트
        </button>
        <button
          className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ 설정
        </button>
      </div>

      <div className="tab-content">
        {/* 모델 관리 탭 */}
        {activeTab === 'models' && (
          <div className="models-tab">
            <div className="models-grid">
              <div className="models-list">
                <h3>사용 가능한 모델</h3>
                <div className="model-cards">
                  {availableModels.map((model) => (
                    <div 
                      key={model.model_id}
                      className={`model-card ${selectedModel?.model_id === model.model_id ? 'selected' : ''}`}
                      onClick={() => handleModelSelect(model)}
                    >
                      <div className="model-header">
                        <div className={`model-icon ${model.provider}`}>
                          {getProviderIcon(model.provider)}
                        </div>
                        <div className="model-info">
                          <h4>{model.display_name}</h4>
                          <p>{model.provider.toUpperCase()}</p>
                        </div>
                        <div 
                          className="model-status"
                          style={{ backgroundColor: getStatusColor(model.status) }}
                        >
                          {model.status}
                        </div>
                      </div>
                      
                      <div className="model-metrics">
                        <div className="metric">
                          <span className="metric-label">품질:</span>
                          <div className="metric-bar">
                            <div 
                              className="metric-fill"
                              style={{ width: `${model.quality_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="metric-value">{(model.quality_score * 100).toFixed(0)}%</span>
                        </div>
                        
                        <div className="metric">
                          <span className="metric-label">속도:</span>
                          <div className="metric-bar">
                            <div 
                              className="metric-fill speed"
                              style={{ width: `${model.speed_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="metric-value">{(model.speed_score * 100).toFixed(0)}%</span>
                        </div>
                        
                        <div className="metric">
                          <span className="metric-label">비용:</span>
                          <div className="metric-bar">
                            <div 
                              className="metric-fill cost"
                              style={{ width: `${model.cost_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="metric-value">{(model.cost_score * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                      
                      <div className="model-details">
                        <p><strong>토큰당 비용:</strong> {formatCurrency(model.cost_per_token)}</p>
                        <p><strong>최대 토큰:</strong> {model.max_tokens.toLocaleString()}</p>
                        <p><strong>컨텍스트 윈도우:</strong> {model.context_window.toLocaleString()}</p>
                      </div>
                      
                      {model.is_default && (
                        <div className="default-badge">기본 모델</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              
              {selectedModel && (
                <div className="model-configuration">
                  <h3>모델 설정</h3>
                  <ModelConfigurationPanel 
                    model={selectedModel}
                    onConfigChange={(config) => {
                      // Handle configuration changes
                      console.log('Config changed:', config);
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* 성능 모니터링 탭 */}
        {activeTab === 'performance' && selectedModel && (
          <div className="performance-tab">
            <PerformanceMonitorPanel 
              model={selectedModel}
              performanceData={performanceData[selectedModel.model_id]}
              onTimeframeChange={(timeframe) => loadModelPerformance(selectedModel.model_id, timeframe)}
            />
          </div>
        )}

        {/* 모델 비교 탭 */}
        {activeTab === 'comparison' && (
          <div className="comparison-tab">
            <ModelComparisonTool 
              availableModels={availableModels}
            />
          </div>
        )}

        {/* 스마트 테스트 탭 */}
        {activeTab === 'testing' && (
          <div className="testing-tab">
            <SmartModelTester 
              availableModels={availableModels}
            />
          </div>
        )}

        {/* 설정 탭 */}
        {activeTab === 'settings' && (
          <div className="settings-tab">
            <ModelSettingsPanel 
              availableModels={availableModels}
              onSettingsChange={loadDashboardData}
            />
          </div>
        )}
      </div>
    </div>
  );
};

// 모델 설정 패널 컴포넌트
const ModelConfigurationPanel = ({ model, onConfigChange }) => {
  const [config, setConfig] = useState({
    parameters: model.parameters || {},
    status: model.status,
    is_default: model.is_default,
    cost_per_token: model.cost_per_token,
    max_tokens: model.max_tokens
  });
  const [saving, setSaving] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/${model.model_id}/configure`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const updatedModel = await response.json();
        onConfigChange(updatedModel);
        alert('모델 설정이 저장되었습니다');
      } else {
        throw new Error('설정 저장에 실패했습니다');
      }
    } catch (err) {
      console.error('설정 저장 오류:', err);
      alert('설정 저장에 실패했습니다');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="model-configuration-panel">
      <div className="config-section">
        <h4>기본 설정</h4>
        <div className="config-field">
          <label>상태:</label>
          <select 
            value={config.status} 
            onChange={(e) => setConfig(prev => ({...prev, status: e.target.value}))}
          >
            <option value="active">활성</option>
            <option value="inactive">비활성</option>
            <option value="maintenance">유지보수</option>
          </select>
        </div>
        
        <div className="config-field">
          <label>
            <input 
              type="checkbox" 
              checked={config.is_default}
              onChange={(e) => setConfig(prev => ({...prev, is_default: e.target.checked}))}
            />
            기본 모델로 설정
          </label>
        </div>
        
        <div className="config-field">
          <label>토큰당 비용:</label>
          <input 
            type="number" 
            step="0.000001"
            value={config.cost_per_token}
            onChange={(e) => setConfig(prev => ({...prev, cost_per_token: parseFloat(e.target.value)}))}
          />
        </div>
        
        <div className="config-field">
          <label>최대 토큰:</label>
          <input 
            type="number" 
            value={config.max_tokens}
            onChange={(e) => setConfig(prev => ({...prev, max_tokens: parseInt(e.target.value)}))}
          />
        </div>
      </div>

      <div className="config-section">
        <h4>모델 매개변수</h4>
        <div className="config-field">
          <label>Temperature:</label>
          <input 
            type="number" 
            min="0" 
            max="2" 
            step="0.1"
            value={config.parameters.temperature || 0.7}
            onChange={(e) => setConfig(prev => ({
              ...prev, 
              parameters: {...prev.parameters, temperature: parseFloat(e.target.value)}
            }))}
          />
        </div>
        
        <div className="config-field">
          <label>Max Tokens:</label>
          <input 
            type="number" 
            min="1" 
            max={model.max_tokens}
            value={config.parameters.max_tokens || 1000}
            onChange={(e) => setConfig(prev => ({
              ...prev, 
              parameters: {...prev.parameters, max_tokens: parseInt(e.target.value)}
            }))}
          />
        </div>
        
        <div className="config-field">
          <label>Top P:</label>
          <input 
            type="number" 
            min="0" 
            max="1" 
            step="0.1"
            value={config.parameters.top_p || 1.0}
            onChange={(e) => setConfig(prev => ({
              ...prev, 
              parameters: {...prev.parameters, top_p: parseFloat(e.target.value)}
            }))}
          />
        </div>
      </div>

      <div className="config-actions">
        <button 
          onClick={handleSaveConfig}
          disabled={saving}
          className="save-config-btn"
        >
          {saving ? '⏳ 저장 중...' : '💾 설정 저장'}
        </button>
      </div>
    </div>
  );
};

// 성능 모니터링 패널 컴포넌트
const PerformanceMonitorPanel = ({ model, performanceData, onTimeframeChange }) => {
  const [timeframe, setTimeframe] = useState('7d');

  const handleTimeframeChange = (newTimeframe) => {
    setTimeframe(newTimeframe);
    onTimeframeChange(newTimeframe);
  };

  if (!performanceData) {
    return <div className="loading">성능 데이터를 로드하는 중...</div>;
  }

  return (
    <div className="performance-monitor-panel">
      <div className="performance-header">
        <h3>{model.display_name} 성능 모니터링</h3>
        <div className="timeframe-selector">
          <button 
            className={timeframe === '1d' ? 'active' : ''}
            onClick={() => handleTimeframeChange('1d')}
          >
            1일
          </button>
          <button 
            className={timeframe === '7d' ? 'active' : ''}
            onClick={() => handleTimeframeChange('7d')}
          >
            7일
          </button>
          <button 
            className={timeframe === '30d' ? 'active' : ''}
            onClick={() => handleTimeframeChange('30d')}
          >
            30일
          </button>
        </div>
      </div>

      <div className="performance-metrics">
        <div className="metric-card">
          <h4>총 요청 수</h4>
          <div className="metric-value">{performanceData.total_requests?.toLocaleString() || 0}</div>
        </div>
        
        <div className="metric-card">
          <h4>평균 응답 시간</h4>
          <div className="metric-value">{performanceData.avg_response_time?.toFixed(2) || 0}초</div>
        </div>
        
        <div className="metric-card">
          <h4>오류율</h4>
          <div className="metric-value">{((performanceData.error_rate || 0) * 100).toFixed(1)}%</div>
        </div>
        
        <div className="metric-card">
          <h4>총 비용</h4>
          <div className="metric-value">
            {new Intl.NumberFormat('ko-KR', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 4
            }).format(performanceData.total_cost || 0)}
          </div>
        </div>
      </div>

      {performanceData.recommendations && performanceData.recommendations.length > 0 && (
        <div className="recommendations">
          <h4>추천사항</h4>
          <ul>
            {performanceData.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// 모델 비교 도구 컴포넌트
const ModelComparisonTool = ({ availableModels }) => {
  const [selectedModels, setSelectedModels] = useState([]);
  const [testPrompt, setTestPrompt] = useState('');
  const [comparisonResults, setComparisonResults] = useState([]);
  const [comparing, setComparing] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const runComparison = async () => {
    if (selectedModels.length < 2) {
      alert('비교를 위해서는 최소 2개의 모델을 선택해주세요');
      return;
    }

    if (!testPrompt.trim()) {
      alert('테스트 프롬프트를 입력해주세요');
      return;
    }

    try {
      setComparing(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/compare`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model_ids: selectedModels,
          test_prompt: testPrompt,
          task_type: 'evaluation'
        })
      });

      if (response.ok) {
        const results = await response.json();
        setComparisonResults(results);
      } else {
        throw new Error('비교 실행에 실패했습니다');
      }
    } catch (err) {
      console.error('모델 비교 오류:', err);
      alert('모델 비교에 실패했습니다');
    } finally {
      setComparing(false);
    }
  };

  return (
    <div className="model-comparison-tool">
      <h3>모델 성능 비교</h3>
      
      <div className="model-selector">
        <h4>비교할 모델 선택</h4>
        <div className="model-checkboxes">
          {availableModels.map(model => (
            <label key={model.model_id} className="model-checkbox">
              <input 
                type="checkbox"
                checked={selectedModels.includes(model.model_id)}
                onChange={() => handleModelToggle(model.model_id)}
              />
              <span>{model.display_name}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="prompt-input">
        <h4>테스트 프롬프트</h4>
        <textarea 
          value={testPrompt}
          onChange={(e) => setTestPrompt(e.target.value)}
          placeholder="모델들을 테스트할 프롬프트를 입력하세요..."
          rows={4}
        />
      </div>

      <div className="comparison-actions">
        <button 
          onClick={runComparison}
          disabled={comparing || selectedModels.length < 2 || !testPrompt.trim()}
          className="run-comparison-btn"
        >
          {comparing ? '⏳ 비교 실행 중...' : '🔬 비교 실행'}
        </button>
      </div>

      {comparisonResults.length > 0 && (
        <div className="comparison-results">
          <h4>비교 결과</h4>
          <div className="results-grid">
            {comparisonResults.map((result) => (
              <div key={result.model_id} className="result-card">
                <div className="result-header">
                  <h5>{availableModels.find(m => m.model_id === result.model_id)?.display_name}</h5>
                  {result.error && <span className="error-badge">오류 발생</span>}
                </div>
                
                {!result.error ? (
                  <>
                    <div className="result-response">
                      <p><strong>응답:</strong></p>
                      <div className="response-text">{result.response}</div>
                    </div>
                    
                    <div className="result-metrics">
                      <div className="metric">
                        <span>응답 시간:</span>
                        <span>{result.response_time.toFixed(2)}초</span>
                      </div>
                      <div className="metric">
                        <span>토큰 수:</span>
                        <span>{result.token_count}</span>
                      </div>
                      <div className="metric">
                        <span>비용:</span>
                        <span>{new Intl.NumberFormat('ko-KR', {
                          style: 'currency',
                          currency: 'USD',
                          minimumFractionDigits: 6
                        }).format(result.cost)}</span>
                      </div>
                      <div className="metric">
                        <span>품질 점수:</span>
                        <span>{(result.quality_score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="error-message">
                    <p><strong>오류:</strong> {result.error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// 모델 설정 패널 컴포넌트
const ModelSettingsPanel = ({ availableModels, onSettingsChange }) => {
  const [recommendationRequest, setRecommendationRequest] = useState({
    budget: 'medium',
    quality_level: 'medium',
    speed_requirement: 'medium',
    task_type: 'evaluation',
    estimated_tokens: 1000,
    estimated_requests_per_month: 100
  });
  const [recommendation, setRecommendation] = useState(null);
  const [gettingRecommendation, setGettingRecommendation] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  const getRecommendation = async () => {
    try {
      setGettingRecommendation(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-models/recommend`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(recommendationRequest)
      });

      if (response.ok) {
        const result = await response.json();
        setRecommendation(result);
      } else {
        throw new Error('추천 요청에 실패했습니다');
      }
    } catch (err) {
      console.error('모델 추천 오류:', err);
      alert('모델 추천에 실패했습니다');
    } finally {
      setGettingRecommendation(false);
    }
  };

  return (
    <div className="model-settings-panel">
      <div className="settings-section">
        <h3>🎯 스마트 모델 추천</h3>
        <p>사용 환경에 맞는 최적의 AI 모델을 추천받으세요</p>
        
        <div className="recommendation-form">
          <div className="form-row">
            <div className="form-field">
              <label>예산 수준:</label>
              <select 
                value={recommendationRequest.budget}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, budget: e.target.value}))}
              >
                <option value="low">낮음 (비용 우선)</option>
                <option value="medium">보통 (균형)</option>
                <option value="high">높음 (품질 우선)</option>
              </select>
            </div>
            
            <div className="form-field">
              <label>품질 요구사항:</label>
              <select 
                value={recommendationRequest.quality_level}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, quality_level: e.target.value}))}
              >
                <option value="low">기본</option>
                <option value="medium">표준</option>
                <option value="high">최고 품질</option>
              </select>
            </div>
            
            <div className="form-field">
              <label>속도 요구사항:</label>
              <select 
                value={recommendationRequest.speed_requirement}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, speed_requirement: e.target.value}))}
              >
                <option value="low">느림 (정확도 우선)</option>
                <option value="medium">보통</option>
                <option value="high">빠름 (속도 우선)</option>
              </select>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-field">
              <label>작업 유형:</label>
              <select 
                value={recommendationRequest.task_type}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, task_type: e.target.value}))}
              >
                <option value="evaluation">평가</option>
                <option value="summary">요약</option>
                <option value="analysis">분석</option>
                <option value="translation">번역</option>
                <option value="recommendation">추천</option>
              </select>
            </div>
            
            <div className="form-field">
              <label>예상 토큰 수:</label>
              <input 
                type="number"
                value={recommendationRequest.estimated_tokens}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, estimated_tokens: parseInt(e.target.value)}))}
              />
            </div>
            
            <div className="form-field">
              <label>월간 예상 요청 수:</label>
              <input 
                type="number"
                value={recommendationRequest.estimated_requests_per_month}
                onChange={(e) => setRecommendationRequest(prev => ({...prev, estimated_requests_per_month: parseInt(e.target.value)}))}
              />
            </div>
          </div>
          
          <button 
            onClick={getRecommendation}
            disabled={gettingRecommendation}
            className="get-recommendation-btn"
          >
            {gettingRecommendation ? '⏳ 분석 중...' : '🎯 최적 모델 추천받기'}
          </button>
        </div>

        {recommendation && (
          <div className="recommendation-result">
            <h4>추천 결과</h4>
            <div className="recommendation-card">
              <div className="recommended-model">
                <h5>
                  {availableModels.find(m => m.model_id === recommendation.model_id)?.display_name}
                </h5>
                <div className="recommendation-confidence">
                  신뢰도: {(recommendation.confidence * 100).toFixed(0)}%
                </div>
              </div>
              
              <div className="recommendation-details">
                <p><strong>추천 이유:</strong> {recommendation.reasoning}</p>
                <p><strong>예상 월간 비용:</strong> {new Intl.NumberFormat('ko-KR', {
                  style: 'currency',
                  currency: 'USD'
                }).format(recommendation.estimated_cost)}</p>
                <p><strong>예상 품질:</strong> {(recommendation.estimated_quality * 100).toFixed(0)}%</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIModelDashboard;