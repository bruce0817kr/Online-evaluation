import React, { useState, useEffect } from 'react';
import './EvaluationPrintManager.css';

const EvaluationPrintManager = ({ user }) => {
  const [printJobs, setPrintJobs] = useState([]);
  const [selectedEvaluations, setSelectedEvaluations] = useState([]);
  const [availableEvaluations, setAvailableEvaluations] = useState([]);
  const [availableProjects, setAvailableProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('individual'); // individual, bulk, chairman
  
  // 위원장 평가표 옵션
  const [chairmanOptions, setChairmanOptions] = useState({
    project_id: '',
    include_statistics: true,
    include_rankings: true,
    include_detailed_scores: true
  });
  
  // 출력 옵션
  const [printOptions, setPrintOptions] = useState({
    include_scores: true,
    include_comments: true,
    format: 'pdf'
  });
  
  // 향상된 출력 옵션
  const [enhancedOptions, setEnhancedOptions] = useState({
    template: 'standard',
    persona: '',
    format: 'pdf',
    style_options: {
      font_family: 'Noto Sans KR',
      font_size: 10,
      color_scheme: 'professional',
      include_logo: true,
      watermark: '',
      header_style: 'modern',
      table_style: 'striped'
    },
    metadata_options: {
      include_timestamps: true,
      include_evaluator_info: true,
      include_qr_code: false,
      digital_signature: false,
      confidentiality_level: 'internal',
      document_classification: ''
    },
    content_options: {
      include_sections: ['summary', 'details', 'scores', 'comments', 'signatures'],
      include_charts: true,
      include_comparison: false,
      include_recommendations: true,
      include_appendices: false,
      summary_length: 'medium'
    }
  });
  
  // 향상된 출력 템플릿 정보
  const [exportTemplates, setExportTemplates] = useState([]);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  useEffect(() => {
    loadAvailableProjects();
    loadAvailableEvaluations();
    loadPrintJobs();
    loadEnhancedExportTemplates();
    
    // 5초마다 작업 상태 업데이트
    const interval = setInterval(loadPrintJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadAvailableEvaluations();
    }
  }, [selectedProject]);

  const loadAvailableProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableProjects(data);
      }
    } catch (err) {
      console.error('프로젝트 목록 로드 실패:', err);
    }
  };

  const loadAvailableEvaluations = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = selectedProject 
        ? `${BACKEND_URL}/api/evaluations/export-list?project_id=${selectedProject}`
        : `${BACKEND_URL}/api/evaluations/export-list`;
      
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableEvaluations(data);
      }
    } catch (err) {
      console.error('평가 목록 로드 실패:', err);
    }
  };

  const loadPrintJobs = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/evaluations/jobs`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPrintJobs(data.jobs || []);
      }
    } catch (err) {
      console.error('출력 작업 목록 로드 실패:', err);
    }
  };

  const loadEnhancedExportTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/evaluations/enhanced-export/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setExportTemplates(data.templates || []);
      }
    } catch (err) {
      console.error('향상된 출력 템플릿 로드 실패:', err);
    }
  };

  const createEnhancedExport = async () => {
    try {
      setLoading(true);
      setError(null);

      if (selectedEvaluations.length === 0) {
        throw new Error('출력할 평가를 선택해주세요.');
      }

      const token = localStorage.getItem('token');
      
      const requestData = {
        evaluation_ids: selectedEvaluations,
        export_options: enhancedOptions
      };

      const response = await fetch(`${BACKEND_URL}/api/evaluations/enhanced-export/export/${selectedEvaluations[0]}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `enhanced_evaluation_export.${enhancedOptions.format}`;
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename[^;=\\n]*=((['\"]).*?\\2|[^;\\n]*)/);
          if (matches && matches[1]) {
            filename = matches[1].replace(/['\"]/g, '');
          }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('향상된 평가표 출력이 완료되었습니다.');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '향상된 출력 작업에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generatePreview = async () => {
    try {
      if (selectedEvaluations.length === 0) {
        throw new Error('미리보기할 평가를 선택해주세요.');
      }

      const token = localStorage.getItem('token');
      
      const response = await fetch(`${BACKEND_URL}/api/evaluations/enhanced-export/preview/${selectedEvaluations[0]}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ export_options: enhancedOptions })
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewData(data);
        setShowPreview(true);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '미리보기 생성에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const applyPersonaDefaults = async (persona) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/evaluations/enhanced-export/personas/${persona}/defaults`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setEnhancedOptions(prev => ({
          ...prev,
          persona: persona,
          ...data.defaults
        }));
      }
    } catch (err) {
      console.error('페르소나 기본값 적용 실패:', err);
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
      setSelectedEvaluations(availableEvaluations.map(evaluation => evaluation.id || evaluation._id));
    } else {
      setSelectedEvaluations([]);
    }
  };

  const createPrintJob = async (printType) => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      
      let requestData;
      let endpoint = `${BACKEND_URL}/api/evaluations/print-request`;

      if (printType === 'chairman') {
        if (!selectedProject) {
          throw new Error('프로젝트를 선택해주세요.');
        }
        
        requestData = {
          project_id: selectedProject,
          include_statistics: chairmanOptions.include_statistics,
          include_rankings: chairmanOptions.include_rankings,
          include_detailed_scores: chairmanOptions.include_detailed_scores
        };
        endpoint = `${BACKEND_URL}/api/evaluations/chairman-summary`;
      } else {
        if (selectedEvaluations.length === 0) {
          throw new Error('출력할 평가를 선택해주세요.');
        }

        requestData = {
          evaluation_ids: selectedEvaluations,
          print_type: printType,
          project_id: selectedProject, // 프로젝트 정보 추가
          include_scores: printOptions.include_scores,
          include_comments: printOptions.include_comments,
          format: printOptions.format,
          template_options: {}
        };
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (response.ok) {
        const data = await response.json();
        alert('출력 작업이 시작되었습니다. 완료되면 다운로드할 수 있습니다.');
        loadPrintJobs(); // 작업 목록 새로고침
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '출력 작업 요청에 실패했습니다');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadPrintResult = async (jobId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/evaluations/download/${jobId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        // 파일명을 Content-Disposition에서 추출하거나 기본값 사용
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `evaluation_print_${jobId}.pdf`;
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
          if (matches && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
          }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        throw new Error('파일 다운로드에 실패했습니다');
      }
    } catch (err) {
      alert(`다운로드 오류: ${err.message}`);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'processing': return '⚙️';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return '대기 중';
      case 'processing': return '처리 중';
      case 'completed': return '완료';
      case 'failed': return '실패';
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

  if (!['admin', 'secretary', 'evaluator'].includes(user.role)) {
    return (
      <div className="evaluation-print-manager">
        <div className="access-denied">
          <h2>🚫 접근 권한 없음</h2>
          <p>평가표 출력 기능은 관리자, 간사, 평가위원만 사용할 수 있습니다.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="evaluation-print-manager">
      <div className="manager-header">
        <h2>📄 평가표 출력 관리</h2>
        <p>평가표를 PDF로 출력하여 다운로드하거나 저장할 수 있습니다.</p>
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
          className={`tab-btn ${activeTab === 'individual' ? 'active' : ''}`}
          onClick={() => setActiveTab('individual')}
        >
          📋 개별 평가표
        </button>
        <button
          className={`tab-btn ${activeTab === 'bulk' ? 'active' : ''}`}
          onClick={() => setActiveTab('bulk')}
        >
          📦 전체 평가표
        </button>
        {['admin', 'secretary'].includes(user.role) && (
          <button
            className={`tab-btn ${activeTab === 'chairman' ? 'active' : ''}`}
            onClick={() => setActiveTab('chairman')}
          >
            👑 위원장 종합 평가표
          </button>
        )}
        <button
          className={`tab-btn ${activeTab === 'enhanced' ? 'active' : ''}`}
          onClick={() => setActiveTab('enhanced')}
        >
          ✨ 향상된 출력
        </button>
        <button
          className={`tab-btn ${activeTab === 'jobs' ? 'active' : ''}`}
          onClick={() => setActiveTab('jobs')}
        >
          📊 작업 현황
        </button>
      </div>

      {/* 프로젝트 선택 */}
      <div className="project-selector">
        <div className="selector-group">
          <label htmlFor="project-select">📂 프로젝트 선택:</label>
          <select 
            id="project-select"
            value={selectedProject} 
            onChange={(e) => setSelectedProject(e.target.value)}
            className="project-select"
          >
            <option value="">전체 프로젝트</option>
            {availableProjects.map(project => (
              <option key={project.id || project._id} value={project.id || project._id}>
                {project.name}
              </option>
            ))}
          </select>
          <span className="project-count">
            ({selectedProject ? availableEvaluations.length : availableEvaluations.length}개 평가)
          </span>
        </div>
      </div>

      <div className="tab-content">
        {/* 개별 평가표 탭 */}
        {activeTab === 'individual' && (
          <div className="individual-print">
            <h3>개별 평가표 출력</h3>
            <p>하나의 평가표를 선택하여 PDF로 출력합니다.</p>

            <div className="print-options">
              <h4>출력 옵션</h4>
              <div className="options-grid">
                <label>
                  <input
                    type="checkbox"
                    checked={printOptions.include_scores}
                    onChange={(e) => setPrintOptions(prev => ({
                      ...prev,
                      include_scores: e.target.checked
                    }))}
                  />
                  점수 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={printOptions.include_comments}
                    onChange={(e) => setPrintOptions(prev => ({
                      ...prev,
                      include_comments: e.target.checked
                    }))}
                  />
                  코멘트 포함
                </label>
              </div>
            </div>

            <div className="evaluation-list">
              <h4>평가 선택 (1개만 선택)</h4>
              <div className="evaluation-items">
                {availableEvaluations.map((evaluation) => (
                  <div key={evaluation.id || evaluation._id} className="evaluation-item">
                    <label>
                      <input
                        type="radio"
                        name="individual-evaluation"
                        checked={selectedEvaluations.includes(evaluation.id || evaluation._id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvaluations([evaluation.id || evaluation._id]);
                          }
                        }}
                      />
                      <div className="evaluation-info">
                        <h5>{evaluation.company_name || '알 수 없음'}</h5>
                        <p>평가자: {evaluation.evaluator_name || '알 수 없음'}</p>
                        <p>상태: {evaluation.status || '알 수 없음'}</p>
                        <p>생성일: {formatDate(evaluation.created_at)}</p>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="action-buttons">
              <button
                onClick={() => createPrintJob('individual')}
                disabled={loading || selectedEvaluations.length !== 1}
                className="print-btn individual"
              >
                {loading ? '⏳ 출력 중...' : '📄 개별 평가표 출력'}
              </button>
            </div>
          </div>
        )}

        {/* 전체 평가표 탭 */}
        {activeTab === 'bulk' && (
          <div className="bulk-print">
            <h3>전체 평가표 일괄 출력</h3>
            <p>여러 평가표를 선택하여 ZIP 파일로 출력합니다.</p>

            <div className="print-options">
              <h4>출력 옵션</h4>
              <div className="options-grid">
                <label>
                  <input
                    type="checkbox"
                    checked={printOptions.include_scores}
                    onChange={(e) => setPrintOptions(prev => ({
                      ...prev,
                      include_scores: e.target.checked
                    }))}
                  />
                  점수 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={printOptions.include_comments}
                    onChange={(e) => setPrintOptions(prev => ({
                      ...prev,
                      include_comments: e.target.checked
                    }))}
                  />
                  코멘트 포함
                </label>
              </div>
            </div>

            <div className="evaluation-list">
              <div className="list-header">
                <h4>평가 선택</h4>
                <div className="select-actions">
                  <button
                    onClick={() => handleSelectAll(true)}
                    className="select-all-btn"
                  >
                    전체 선택
                  </button>
                  <button
                    onClick={() => handleSelectAll(false)}
                    className="deselect-all-btn"
                  >
                    전체 해제
                  </button>
                  <span className="selection-count">
                    {selectedEvaluations.length}개 선택됨
                  </span>
                </div>
              </div>

              <div className="evaluation-items">
                {availableEvaluations.map((evaluation) => (
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
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="action-buttons">
              <button
                onClick={() => createPrintJob('bulk')}
                disabled={loading || selectedEvaluations.length === 0}
                className="print-btn bulk"
              >
                {loading ? '⏳ 출력 중...' : `📦 선택된 ${selectedEvaluations.length}개 평가표 일괄 출력`}
              </button>
            </div>
          </div>
        )}

        {/* 위원장 종합 평가표 탭 */}
        {activeTab === 'chairman' && ['admin', 'secretary'].includes(user.role) && (
          <div className="chairman-print">
            <h3>위원장 종합 평가표</h3>
            <p>프로젝트 전체 평가 결과를 요약한 위원장용 종합 평가표를 출력합니다.</p>

            <div className="chairman-options">
              <h4>프로젝트 선택</h4>
              <select
                value={chairmanOptions.project_id}
                onChange={(e) => setChairmanOptions(prev => ({
                  ...prev,
                  project_id: e.target.value
                }))}
                className="project-select"
              >
                <option value="">프로젝트를 선택하세요</option>
                {/* 프로젝트 목록은 별도 API에서 가져와야 함 */}
                <option value="project1">스타트업 지원 프로젝트</option>
                <option value="project2">혁신기술 개발 프로젝트</option>
              </select>

              <h4>포함 옵션</h4>
              <div className="options-grid">
                <label>
                  <input
                    type="checkbox"
                    checked={chairmanOptions.include_statistics}
                    onChange={(e) => setChairmanOptions(prev => ({
                      ...prev,
                      include_statistics: e.target.checked
                    }))}
                  />
                  통계 정보 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={chairmanOptions.include_rankings}
                    onChange={(e) => setChairmanOptions(prev => ({
                      ...prev,
                      include_rankings: e.target.checked
                    }))}
                  />
                  순위 정보 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={chairmanOptions.include_detailed_scores}
                    onChange={(e) => setChairmanOptions(prev => ({
                      ...prev,
                      include_detailed_scores: e.target.checked
                    }))}
                  />
                  상세 점수 포함
                </label>
              </div>
            </div>

            <div className="action-buttons">
              <button
                onClick={() => createPrintJob('chairman')}
                disabled={loading || !chairmanOptions.project_id}
                className="print-btn chairman"
              >
                {loading ? '⏳ 출력 중...' : '👑 위원장 종합 평가표 출력'}
              </button>
            </div>
          </div>
        )}

        {/* 향상된 출력 탭 */}
        {activeTab === 'enhanced' && (
          <div className="enhanced-export">
            <h3>✨ 향상된 평가표 출력</h3>
            <p>고급 템플릿, 스타일링, 그리고 맞춤형 옵션으로 전문적인 평가표를 생성합니다.</p>

            {/* 템플릿 선택 */}
            <div className="template-selection">
              <h4>📋 템플릿 선택</h4>
              <div className="template-grid">
                {['standard', 'government', 'corporate', 'academic', 'technical'].map(template => (
                  <div 
                    key={template}
                    className={`template-card ${enhancedOptions.template === template ? 'selected' : ''}`}
                    onClick={() => setEnhancedOptions(prev => ({...prev, template}))}
                  >
                    <div className="template-icon">
                      {template === 'standard' && '📄'}
                      {template === 'government' && '🏛️'}
                      {template === 'corporate' && '🏢'}
                      {template === 'academic' && '🎓'}
                      {template === 'technical' && '⚙️'}
                    </div>
                    <h5>{template === 'standard' ? '표준' : 
                         template === 'government' ? '정부기관' : 
                         template === 'corporate' ? '기업용' : 
                         template === 'academic' ? '학술용' : '기술평가'}</h5>
                    <p className="template-desc">
                      {template === 'standard' ? '범용 표준 템플릿' : 
                       template === 'government' ? '공공기관 형식' : 
                       template === 'corporate' ? '기업 보고서 형식' : 
                       template === 'academic' ? '학술 논문 형식' : '기술 평가 형식'}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* 페르소나 선택 */}
            <div className="persona-selection">
              <h4>👤 대상자 최적화</h4>
              <div className="persona-options">
                {['', 'government_auditor', 'corporate_executive', 'academic_reviewer', 'technical_assessor'].map(persona => (
                  <button
                    key={persona || 'none'}
                    className={`persona-btn ${enhancedOptions.persona === persona ? 'selected' : ''}`}
                    onClick={() => {
                      if (persona) {
                        applyPersonaDefaults(persona);
                      } else {
                        setEnhancedOptions(prev => ({...prev, persona: ''}));
                      }
                    }}
                  >
                    {persona === '' ? '🎯 기본' : 
                     persona === 'government_auditor' ? '🏛️ 정부감사관' : 
                     persona === 'corporate_executive' ? '👔 기업임원' : 
                     persona === 'academic_reviewer' ? '🎓 학술심사위원' : '⚙️ 기술평가자'}
                  </button>
                ))}
              </div>
            </div>

            {/* 형식 및 스타일 옵션 */}
            <div className="style-options">
              <h4>🎨 스타일 옵션</h4>
              <div className="options-row">
                <div className="option-group">
                  <label>출력 형식:</label>
                  <select 
                    value={enhancedOptions.format} 
                    onChange={(e) => setEnhancedOptions(prev => ({...prev, format: e.target.value}))}
                  >
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                    <option value="word">Word</option>
                    <option value="powerpoint">PowerPoint</option>
                    <option value="html">HTML</option>
                  </select>
                </div>
                <div className="option-group">
                  <label>색상 테마:</label>
                  <select 
                    value={enhancedOptions.style_options.color_scheme} 
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      style_options: {...prev.style_options, color_scheme: e.target.value}
                    }))}
                  >
                    <option value="professional">프로페셔널</option>
                    <option value="government">정부기관</option>
                    <option value="corporate">기업용</option>
                    <option value="academic">학술용</option>
                    <option value="modern">모던</option>
                    <option value="classic">클래식</option>
                  </select>
                </div>
                <div className="option-group">
                  <label>폰트 크기:</label>
                  <input 
                    type="number" 
                    min="8" 
                    max="16" 
                    value={enhancedOptions.style_options.font_size}
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      style_options: {...prev.style_options, font_size: parseInt(e.target.value)}
                    }))}
                  />
                </div>
              </div>
              
              <div className="checkbox-options">
                <label>
                  <input
                    type="checkbox"
                    checked={enhancedOptions.style_options.include_logo}
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      style_options: {...prev.style_options, include_logo: e.target.checked}
                    }))}
                  />
                  로고 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={enhancedOptions.content_options.include_charts}
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      content_options: {...prev.content_options, include_charts: e.target.checked}
                    }))}
                  />
                  차트 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={enhancedOptions.content_options.include_recommendations}
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      content_options: {...prev.content_options, include_recommendations: e.target.checked}
                    }))}
                  />
                  AI 추천사항 포함
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={enhancedOptions.metadata_options.include_qr_code}
                    onChange={(e) => setEnhancedOptions(prev => ({
                      ...prev, 
                      metadata_options: {...prev.metadata_options, include_qr_code: e.target.checked}
                    }))}
                  />
                  QR 코드 포함
                </label>
              </div>
            </div>

            {/* 평가 선택 */}
            <div className="evaluation-selection">
              <h4>📋 평가 선택</h4>
              <div className="evaluation-items">
                {availableEvaluations.slice(0, 5).map((evaluation) => (
                  <div key={evaluation.id || evaluation._id} className="evaluation-item">
                    <label>
                      <input
                        type="radio"
                        name="enhanced-evaluation"
                        checked={selectedEvaluations.includes(evaluation.id || evaluation._id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvaluations([evaluation.id || evaluation._id]);
                          }
                        }}
                      />
                      <div className="evaluation-info">
                        <h5>{evaluation.company_name || '알 수 없음'}</h5>
                        <p>평가자: {evaluation.evaluator_name || '알 수 없음'}</p>
                        <p>상태: {evaluation.status || '알 수 없음'}</p>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            {/* 미리보기 및 출력 버튼 */}
            <div className="action-buttons">
              <button
                onClick={generatePreview}
                disabled={loading || selectedEvaluations.length === 0}
                className="preview-btn"
              >
                {loading ? '⏳ 처리 중...' : '👁️ 미리보기'}
              </button>
              <button
                onClick={createEnhancedExport}
                disabled={loading || selectedEvaluations.length === 0}
                className="enhanced-export-btn"
              >
                {loading ? '⏳ 출력 중...' : '✨ 향상된 출력 생성'}
              </button>
            </div>

            {/* 미리보기 모달 */}
            {showPreview && previewData && (
              <div className="preview-modal">
                <div className="preview-content">
                  <div className="preview-header">
                    <h4>📄 미리보기</h4>
                    <button 
                      onClick={() => setShowPreview(false)}
                      className="close-btn"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="preview-body">
                    <pre>{JSON.stringify(previewData, null, 2)}</pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 작업 현황 탭 */}
        {activeTab === 'jobs' && (
          <div className="jobs-status">
            <h3>출력 작업 현황</h3>
            <p>진행 중이거나 완료된 출력 작업들을 확인할 수 있습니다.</p>

            <div className="jobs-list">
              {printJobs.length === 0 ? (
                <div className="empty-jobs">
                  <p>진행 중인 출력 작업이 없습니다.</p>
                </div>
              ) : (
                printJobs.map((job) => (
                  <div key={job.job_id} className={`job-item ${job.status}`}>
                    <div className="job-info">
                      <div className="job-header">
                        <span className="job-status">
                          {getStatusIcon(job.status)} {getStatusText(job.status)}
                        </span>
                        <span className="job-id">ID: {job.job_id.slice(0, 8)}...</span>
                      </div>
                      
                      <div className="job-details">
                        <p>생성일: {formatDate(job.created_at)}</p>
                        {job.completed_at && (
                          <p>완료일: {formatDate(job.completed_at)}</p>
                        )}
                        {job.status === 'processing' && (
                          <div className="progress-bar">
                            <div 
                              className="progress-fill" 
                              style={{width: `${job.progress || 0}%`}}
                            ></div>
                            <span className="progress-text">{job.progress || 0}%</span>
                          </div>
                        )}
                        {job.error_message && (
                          <p className="error-message">오류: {job.error_message}</p>
                        )}
                      </div>
                    </div>

                    <div className="job-actions">
                      {job.status === 'completed' && (
                        <button
                          onClick={() => downloadPrintResult(job.job_id)}
                          className="download-btn"
                        >
                          📥 다운로드
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationPrintManager;