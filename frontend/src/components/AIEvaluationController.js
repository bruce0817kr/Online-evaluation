import React, { useState, useEffect } from 'react';
import './AIEvaluationController.css';

const AIEvaluationController = ({ user }) => {
  const [activeTab, setActiveTab] = useState('execute'); // execute, jobs, results, settings
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // AI 평가 실행 상태
  const [evaluations, setEvaluations] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [aiProviders, setAiProviders] = useState([]);
  const [selectedEvaluations, setSelectedEvaluations] = useState([]);
  const [evaluationConfig, setEvaluationConfig] = useState({
    template_id: '',
    ai_provider: '',
    ai_model: '',
    evaluation_mode: 'comprehensive',
    include_file_analysis: true,
    custom_prompt: ''
  });
  
  // 작업 관리 상태
  const [aiJobs, setAiJobs] = useState([]);
  const [jobDetails, setJobDetails] = useState({});
  
  // 결과 관리 상태
  const [evaluationResults, setEvaluationResults] = useState({});
  const [selectedResult, setSelectedResult] = useState(null);
  
  // 설정 상태
  const [jobConfig, setJobConfig] = useState({
    max_concurrent_evaluations: 3,
    timeout_minutes: 30,
    retry_count: 2,
    quality_threshold: 0.8,
    auto_approve: false
  });

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  useEffect(() => {
    loadInitialData();
    
    // 5초마다 작업 상태 업데이트
    const interval = setInterval(loadAIJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadInitialData = async () => {
    await Promise.all([
      loadEvaluations(),
      loadTemplates(),
      loadAIProviders(),
      loadAIJobs()
    ]);
  };

  const loadEvaluations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/evaluations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setEvaluations(data);
      }
    } catch (err) {
      console.error('평가 목록 로드 실패:', err);
    }
  };

  const loadTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('템플릿 목록 로드 실패:', err);
    }
  };

  const loadAIProviders = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('인증 토큰이 없습니다.');
        setAiProviders([]);
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/providers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAiProviders(Array.isArray(data.providers) ? data.providers : []);
      } else if (response.status === 404) {
        console.warn('AI 공급자 API를 찾을 수 없습니다.');
        setAiProviders([]);
      } else {
        console.error(`AI 공급자 목록 로드 실패: ${response.status}`);
        setAiProviders([]);
      }
    } catch (err) {
      console.error('AI 공급자 목록 로드 네트워크 오류:', err);
      setAiProviders([]);
    }
  };

  const loadAIJobs = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/jobs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAiJobs(data.jobs || []);
      }
    } catch (err) {
      console.error('AI 작업 목록 로드 실패:', err);
    }
  };

  const loadJobDetails = async (jobId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/jobs/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setJobDetails(prev => ({ ...prev, [jobId]: data.job }));
      }
    } catch (err) {
      console.error('작업 상세 정보 로드 실패:', err);
    }
  };

  const executeAIEvaluation = async () => {
    try {
      setLoading(true);
      setError(null);

      if (selectedEvaluations.length === 0) {
        throw new Error('평가를 선택해주세요.');
      }

      if (!evaluationConfig.template_id) {
        throw new Error('평가 템플릿을 선택해주세요.');
      }

      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/execute`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          evaluation_ids: selectedEvaluations,
          template_id: evaluationConfig.template_id,
          ai_provider: evaluationConfig.ai_provider,
          ai_model: evaluationConfig.ai_model,
          evaluation_mode: evaluationConfig.evaluation_mode,
          include_file_analysis: evaluationConfig.include_file_analysis,
          custom_prompt: evaluationConfig.custom_prompt,
          ...jobConfig
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`AI 평가가 시작되었습니다. 작업 ID: ${data.job_id}`);
        setActiveTab('jobs'); // 작업 현황 탭으로 이동
        loadAIJobs();
        
        // 선택 초기화
        setSelectedEvaluations([]);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'AI 평가 실행에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cancelAIJob = async (jobId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('AI 평가 작업이 취소되었습니다.');
        loadAIJobs();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '작업 취소에 실패했습니다');
      }
    } catch (err) {
      alert(`작업 취소 오류: ${err.message}`);
    }
  };

  const approveAIResult = async (evaluationId, action, reason = '', scoreAdjustments = null) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai-evaluation/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          evaluation_id: evaluationId,
          action: action,
          reason: reason,
          score_adjustments: scoreAdjustments
        })
      });

      if (response.ok) {
        alert(`AI 평가 결과가 ${action === 'approve' ? '승인' : '거부'}되었습니다.`);
        loadAIJobs();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '승인/거부 처리에 실패했습니다');
      }
    } catch (err) {
      alert(`처리 오류: ${err.message}`);
    }
  };

  const handleEvaluationSelection = (evaluationId, selected) => {
    if (selected) {
      setSelectedEvaluations(prev => [...prev, evaluationId]);
    } else {
      setSelectedEvaluations(prev => prev.filter(id => id !== evaluationId));
    }
  };

  const handleSelectAll = (selected) => {
    if (selected) {
      setSelectedEvaluations(evaluations.map(evaluation => evaluation.id || evaluation._id));
    } else {
      setSelectedEvaluations([]);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'processing': return '⚙️';
      case 'completed': return '✅';
      case 'completed_with_errors': return '⚠️';
      case 'failed': return '❌';
      case 'cancelled': return '🚫';
      default: return '❓';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return '대기 중';
      case 'processing': return '처리 중';
      case 'completed': return '완료';
      case 'completed_with_errors': return '일부 오류와 함께 완료';
      case 'failed': return '실패';
      case 'cancelled': return '취소됨';
      default: return '알 수 없음';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '알 수 없음';
    try {
      return new Date(dateString).toLocaleString('ko-KR');
    } catch {
      return '알 수 없음';
    }
  };

  if (!['admin', 'secretary'].includes(user.role)) {
    return (
      <div className="ai-evaluation-controller">
        <div className="access-denied">
          <h2>🚫 접근 권한 없음</h2>
          <p>AI 평가 제어 기능은 관리자와 간사만 사용할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="ai-evaluation-controller">
      <div className="controller-header">
        <h2>🤖 AI 평가 제어 시스템</h2>
        <p>AI를 활용한 자동 평가 실행 및 결과 관리</p>
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
          className={`tab-btn ${activeTab === 'execute' ? 'active' : ''}`}
          onClick={() => setActiveTab('execute')}
        >
          🚀 AI 평가 실행
        </button>
        <button
          className={`tab-btn ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          📊 작업 현황
        </button>
        <button
          className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
        >
          📋 결과 관리
        </button>
        <button
          className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          ⚙️ 설정
        </button>
      </div>

      <div className="tab-content">
        {/* AI 평가 실행 탭 */}
        {activeTab === 'execute' && (
          <div className="execute-tab">
            <h3>AI 평가 실행</h3>
            <p>선택한 평가들에 대해 AI 자동 평가를 실행합니다.</p>

            {/* AI 설정 */}
            <div className="ai-config">
              <h4>AI 설정</h4>
              <div className="config-grid">
                <div className="config-item">
                  <label>평가 템플릿 *</label>
                  <select
                    value={evaluationConfig.template_id}
                    onChange={(e) => setEvaluationConfig(prev => ({
                      ...prev,
                      template_id: e.target.value
                    }))}
                  >
                    <option value="">템플릿 선택</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="config-item">
                  <label>AI 공급자</label>
                  <select
                    value={evaluationConfig.ai_provider}
                    onChange={(e) => setEvaluationConfig(prev => ({
                      ...prev,
                      ai_provider: e.target.value
                    }))}
                  >
                    <option value="">자동 선택</option>
                    {aiProviders.map(provider => (
                      <option key={provider.name} value={provider.name}>
                        {provider.display_name || provider.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="config-item">
                  <label>평가 모드</label>
                  <select
                    value={evaluationConfig.evaluation_mode}
                    onChange={(e) => setEvaluationConfig(prev => ({
                      ...prev,
                      evaluation_mode: e.target.value
                    }))}
                  >
                    <option value="comprehensive">종합 평가</option>
                    <option value="quick">빠른 평가</option>
                    <option value="detailed">상세 평가</option>
                  </select>
                </div>

                <div className="config-item checkbox-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={evaluationConfig.include_file_analysis}
                      onChange={(e) => setEvaluationConfig(prev => ({
                        ...prev,
                        include_file_analysis: e.target.checked
                      }))}
                    />
                    파일 분석 포함
                  </label>
                </div>
              </div>

              <div className="custom-prompt">
                <label>커스텀 프롬프트 (선택사항)</label>
                <textarea
                  value={evaluationConfig.custom_prompt}
                  onChange={(e) => setEvaluationConfig(prev => ({
                    ...prev,
                    custom_prompt: e.target.value
                  }))}
                  placeholder="추가적인 평가 지침을 입력하세요..."
                  rows="4"
                />
              </div>
            </div>

            {/* 평가 선택 */}
            <div className="evaluation-selection">
              <div className="selection-header">
                <h4>평가 선택</h4>
                <div className="selection-actions">
                  <button
                    onClick={() => handleSelectAll(true)}
                    className="select-btn"
                  >
                    전체 선택
                  </button>
                  <button
                    onClick={() => handleSelectAll(false)}
                    className="deselect-btn"
                  >
                    전체 해제
                  </button>
                  <span className="selection-count">
                    {selectedEvaluations.length}개 선택됨
                  </span>
                </div>
              </div>

              <div className="evaluation-list">
                {evaluations.map(evaluation => (
                  <div key={evaluation.id || evaluation._id} className="evaluation-item">
                    <label>
                      <input
                        type="checkbox"
                        checked={selectedEvaluations.includes(evaluation.id || evaluation._id)}
                        onChange={(e) => handleEvaluationSelection(
                          evaluation.id || evaluation._id,
                          e.target.checked
                        )}
                      />
                      <div className="evaluation-info">
                        <h5>{evaluation.company_name || '알 수 없음'}</h5>
                        <p>평가자: {evaluation.evaluator_name || '알 수 없음'}</p>
                        <p>상태: {evaluation.status || '알 수 없음'}</p>
                        <p>생성일: {formatDate(evaluation.created_at)}</p>
                        {evaluation.ai_evaluation_approved && (
                          <span className="ai-badge approved">AI 평가 승인됨</span>
                        )}
                        {evaluation.ai_evaluation_rejected && (
                          <span className="ai-badge rejected">AI 평가 거부됨</span>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="execute-actions">
              <button
                onClick={executeAIEvaluation}
                disabled={loading || selectedEvaluations.length === 0 || !evaluationConfig.template_id}
                className="execute-btn"
              >
                {loading ? '⏳ 실행 중...' : `🚀 선택된 ${selectedEvaluations.length}개 평가 AI 분석 실행`}
              </button>
            </div>
          </div>
        )}

        {/* 작업 현황 탭 */}
        {activeTab === 'jobs' && (
          <div className="jobs-tab">
            <h3>AI 평가 작업 현황</h3>
            <p>실행 중이거나 완료된 AI 평가 작업들을 관리합니다.</p>

            <div className="jobs-list">
              {aiJobs.length === 0 ? (
                <div className="empty-jobs">
                  <p>진행 중인 AI 평가 작업이 없습니다.</p>
                </div>
              ) : (
                aiJobs.map(job => (
                  <div key={job.job_id} className={`job-card ${job.status}`}>
                    <div className="job-header">
                      <div className="job-status">
                        {getStatusIcon(job.status)} {getStatusText(job.status)}
                      </div>
                      <div className="job-id">
                        ID: {job.job_id.slice(0, 8)}...
                      </div>
                    </div>

                    <div className="job-details">
                      <div className="job-info">
                        <p>평가 수: {job.total_evaluations}개</p>
                        <p>완료: {job.completed_evaluations}개</p>
                        <p>실패: {job.failed_evaluations}개</p>
                        <p>생성일: {formatDate(job.started_at)}</p>
                        {job.completed_at && (
                          <p>완료일: {formatDate(job.completed_at)}</p>
                        )}
                        {job.average_score && (
                          <p>평균 점수: {job.average_score.toFixed(1)}점</p>
                        )}
                      </div>

                      {job.status === 'processing' && (
                        <div className="progress-section">
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{width: `${job.progress || 0}%`}}
                            ></div>
                          </div>
                          <span className="progress-text">{job.progress || 0}%</span>
                        </div>
                      )}

                      {job.error_messages && job.error_messages.length > 0 && (
                        <div className="error-messages">
                          <h5>오류 메시지:</h5>
                          {job.error_messages.slice(0, 3).map((error, index) => (
                            <p key={index} className="error-text">{error}</p>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="job-actions">
                      {job.status === 'processing' && (
                        <button
                          onClick={() => cancelAIJob(job.job_id)}
                          className="cancel-btn"
                        >
                          🚫 취소
                        </button>
                      )}
                      <button
                        onClick={() => loadJobDetails(job.job_id)}
                        className="details-btn"
                      >
                        📊 상세보기
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* 결과 관리 탭 */}
        {activeTab === 'results' && (
          <div className="results-tab">
            <h3>AI 평가 결과 관리</h3>
            <p>AI 평가 결과를 검토하고 승인/거부할 수 있습니다.</p>

            <div className="results-list">
              {evaluations
                .filter(evaluation => evaluation.ai_total_score || evaluation.ai_scores)
                .map(evaluation => (
                  <div key={evaluation.id || evaluation._id} className="result-card">
                    <div className="result-header">
                      <h4>{evaluation.company_name || '알 수 없음'}</h4>
                      <div className="result-status">
                        {evaluation.ai_evaluation_approved && (
                          <span className="status-badge approved">✅ 승인됨</span>
                        )}
                        {evaluation.ai_evaluation_rejected && (
                          <span className="status-badge rejected">❌ 거부됨</span>
                        )}
                        {!evaluation.ai_evaluation_approved && !evaluation.ai_evaluation_rejected && (
                          <span className="status-badge pending">⏳ 검토 대기</span>
                        )}
                      </div>
                    </div>

                    <div className="result-details">
                      <p>AI 총점: {evaluation.ai_total_score?.toFixed(1) || '알 수 없음'}점</p>
                      <p>평가자: {evaluation.evaluator_name || '알 수 없음'}</p>
                      <p>생성일: {formatDate(evaluation.created_at)}</p>
                    </div>

                    {!evaluation.ai_evaluation_approved && !evaluation.ai_evaluation_rejected && (
                      <div className="approval-actions">
                        <button
                          onClick={() => approveAIResult(evaluation.id || evaluation._id, 'approve')}
                          className="approve-btn"
                        >
                          ✅ 승인
                        </button>
                        <button
                          onClick={() => approveAIResult(evaluation.id || evaluation._id, 'reject', '검토 필요')}
                          className="reject-btn"
                        >
                          ❌ 거부
                        </button>
                      </div>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* 설정 탭 */}
        {activeTab === 'settings' && (
          <div className="settings-tab">
            <h3>AI 평가 설정</h3>
            <p>AI 평가 작업의 기본 설정을 관리합니다.</p>

            <div className="settings-form">
              <div className="setting-group">
                <h4>작업 설정</h4>
                
                <div className="setting-item">
                  <label>동시 실행 평가 수</label>
                  <input
                    type="number"
                    value={jobConfig.max_concurrent_evaluations}
                    onChange={(e) => setJobConfig(prev => ({
                      ...prev,
                      max_concurrent_evaluations: parseInt(e.target.value)
                    }))}
                    min="1"
                    max="10"
                  />
                  <small>동시에 처리할 수 있는 평가 수 (1-10)</small>
                </div>

                <div className="setting-item">
                  <label>타임아웃 (분)</label>
                  <input
                    type="number"
                    value={jobConfig.timeout_minutes}
                    onChange={(e) => setJobConfig(prev => ({
                      ...prev,
                      timeout_minutes: parseInt(e.target.value)
                    }))}
                    min="5"
                    max="120"
                  />
                  <small>평가당 최대 처리 시간 (5-120분)</small>
                </div>

                <div className="setting-item">
                  <label>재시도 횟수</label>
                  <input
                    type="number"
                    value={jobConfig.retry_count}
                    onChange={(e) => setJobConfig(prev => ({
                      ...prev,
                      retry_count: parseInt(e.target.value)
                    }))}
                    min="0"
                    max="5"
                  />
                  <small>실패 시 재시도 횟수 (0-5회)</small>
                </div>

                <div className="setting-item">
                  <label>품질 임계값</label>
                  <input
                    type="number"
                    step="0.1"
                    value={jobConfig.quality_threshold}
                    onChange={(e) => setJobConfig(prev => ({
                      ...prev,
                      quality_threshold: parseFloat(e.target.value)
                    }))}
                    min="0.1"
                    max="1.0"
                  />
                  <small>AI 평가 결과의 최소 신뢰도 (0.1-1.0)</small>
                </div>

                <div className="setting-item checkbox-item">
                  <label>
                    <input
                      type="checkbox"
                      checked={jobConfig.auto_approve}
                      onChange={(e) => setJobConfig(prev => ({
                        ...prev,
                        auto_approve: e.target.checked
                      }))}
                    />
                    자동 승인
                  </label>
                  <small>품질 임계값 이상의 결과를 자동으로 승인</small>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIEvaluationController;