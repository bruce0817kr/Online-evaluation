import React, { useEffect, useState } from "react";
import CreateEvaluationPage from "./CreateEvaluationPage.js";

const EvaluationManagement = ({ user }) => {
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedEvaluation, setSelectedEvaluation] = useState(null);
  const [currentView, setCurrentView] = useState('list'); // 'list', 'create', 'detail'
  const [filters, setFilters] = useState({
    project_id: '',
    status: '',
    evaluator_id: ''
  });
  const [projects, setProjects] = useState([]);
  const [evaluators, setEvaluators] = useState([]);
  
  // Excel 업로드 관련 상태
  const [showExcelUpload, setShowExcelUpload] = useState(false);
  const [excelFile, setExcelFile] = useState(null);
  const [excelValidation, setExcelValidation] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    fetchEvaluations();
    fetchProjects();
    fetchEvaluators();
  }, []);
  
  useEffect(() => {
    fetchEvaluations();
  }, [filters]);
  const fetchEvaluations = async () => {
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("token");
      const params = new URLSearchParams();
      if (filters.project_id) params.append('project_id', filters.project_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.evaluator_id) params.append('evaluator_id', filters.evaluator_id);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019'}/api/evaluations?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const errorMessage = errData.detail || `평가 목록 조회 실패 (${response.status})`;
        throw new Error(errorMessage);
      }
      const data = await response.json();
      setEvaluations(data);
    } catch (err) {
      const userFriendlyMessage = err.message.includes('Failed to fetch') 
        ? '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.'
        : err.message || '평가 목록을 불러오는 중 오류가 발생했습니다.';
      setError(userFriendlyMessage);
      console.error('평가 목록 조회 오류:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019'}/api/projects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('프로젝트 목록 조회 실패:', err);
    }
  };
  
  const fetchEvaluators = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019'}/api/evaluators`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setEvaluators(data);
      }
    } catch (err) {
      console.error('평가위원 목록 조회 실패:', err);
    }
  };

  const handleEvaluationCreated = () => {
    setCurrentView('list');
    fetchEvaluations(); // Refresh the list
  };
  
  const handleDeleteEvaluation = async (evaluationId) => {
    if (!window.confirm('정말로 이 평가를 삭제하시겠습니까?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8081'}/api/evaluations/${evaluationId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        alert('평가가 성공적으로 삭제되었습니다.');
        fetchEvaluations();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '삭제에 실패했습니다.');
      }
    } catch (err) {
      alert(`삭제 오류: ${err.message}`);
    }
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'assigned': return 'bg-yellow-100 text-yellow-800';
      case 'in_progress': return 'bg-blue-100 text-blue-800';
      case 'submitted': return 'bg-green-100 text-green-800';
      case 'reviewed': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };
  
  const getStatusText = (status) => {
    switch (status) {
      case 'assigned': return '배정됨';
      case 'in_progress': return '진행중';
      case 'submitted': return '제출완료';
      case 'reviewed': return '검토완료';
      default: return status;
    }
  };

  // Excel 템플릿 다운로드
  const downloadExcelTemplate = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8081'}/api/evaluations/download-template`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) {
        throw new Error('템플릿 다운로드에 실패했습니다.');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'evaluation_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`템플릿 다운로드 오류: ${err.message}`);
    }
  };

  // Excel 파일 선택 처리
  const handleExcelFileSelect = (file) => {
    if (!file) return;
    
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('Excel 파일(.xlsx, .xls)만 업로드할 수 있습니다.');
      return;
    }
    
    setExcelFile(file);
    setExcelValidation(null);
    setUploadResult(null);
    validateExcelFile(file);
  };

  // Excel 파일 유효성 검증
  const validateExcelFile = async (file) => {
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8081'}/api/evaluations/validate-excel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const result = await response.json();
      setExcelValidation(result);
    } catch (err) {
      setExcelValidation({
        valid: false,
        errors: [`유효성 검증 오류: ${err.message}`],
        warnings: [],
        preview: {}
      });
    }
  };

  // Excel 파일 업로드
  const handleExcelUpload = async () => {
    if (!excelFile || !excelValidation?.valid) {
      alert('유효한 Excel 파일을 선택해주세요.');
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      const token = localStorage.getItem("token");
      const formData = new FormData();
      formData.append('file', excelFile);
      
      // 진행률 시뮬레이션
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 500);
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8081'}/api/evaluations/bulk-upload-excel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      const result = await response.json();
      setUploadResult(result);
      
      if (response.ok && result.success_count > 0) {
        alert(`Excel 업로드 완료! ${result.success_count}개의 평가가 생성되었습니다.`);
        fetchEvaluations(); // 목록 새로고침
        resetExcelUpload();
      } else {
        console.error('업로드 실패:', result);
      }
    } catch (err) {
      setUploadResult({
        success_count: 0,
        failed_count: 1,
        errors: [{ error: `업로드 오류: ${err.message}` }]
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Excel 업로드 상태 초기화
  const resetExcelUpload = () => {
    setExcelFile(null);
    setExcelValidation(null);
    setUploadProgress(0);
    setUploadResult(null);
    setIsUploading(false);
    setShowExcelUpload(false);
  };

  // 드래그 앤 드롭 이벤트 처리
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleExcelFileSelect(files[0]);
    }
  };

  if (user.role !== 'admin' && user.role !== 'secretary') {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">평가 관리</h2>
        <p className="text-gray-600">이 기능은 관리자와 간사만 사용할 수 있습니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600 font-medium">평가 목록 로딩 중...</span>
      </div>
    );
  }
  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">평가 관리</h2>
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
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
                      setError('');
                      fetchEvaluations();
                    }}
                    className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-red-100 to-red-200 text-red-800 font-medium rounded-md hover:from-red-200 hover:to-red-300 transform hover:scale-105 transition-all duration-200 text-sm"
                  >
                    <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    다시 시도
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show CreateEvaluationPage when currentView is 'create'
  if (currentView === 'create') {
    return (
      <CreateEvaluationPage 
        user={user}
        onEvaluationCreated={handleEvaluationCreated}
        onCancel={() => setCurrentView('list')}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">평가 관리</h2>
          <div className="flex space-x-3">
            <button
              onClick={() => setCurrentView('create')}
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              새 평가 개설
            </button>
            <button
              onClick={() => setShowExcelUpload(!showExcelUpload)}
              className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white font-medium rounded-lg hover:from-emerald-700 hover:to-emerald-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
              Excel 일괄 업로드
            </button>
          </div>
        </div>
        
        {/* Excel 업로드 섹션 */}
        {showExcelUpload && (
          <div className="mb-6 p-6 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-blue-900">Excel 일괄 업로드</h3>
              <button
                onClick={resetExcelUpload}
                className="text-blue-600 hover:text-blue-800"
              >
                ✕
              </button>
            </div>
            
            {/* 템플릿 다운로드 */}
            <div className="mb-4">
              <button
                onClick={downloadExcelTemplate}
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white font-medium rounded-lg hover:from-indigo-700 hover:to-indigo-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Excel 템플릿 다운로드
              </button>
              <p className="text-sm text-gray-600 mt-2">
                템플릿을 다운로드하여 평가 정보를 입력한 후 업로드해주세요.
              </p>
            </div>
            
            {/* 파일 업로드 영역 */}
            <div 
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragActive 
                  ? 'border-blue-400 bg-blue-100' 
                  : 'border-gray-300 hover:border-blue-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {excelFile ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-center space-x-2">
                    <span className="text-green-600">✓</span>
                    <span className="font-medium">{excelFile.name}</span>
                    <span className="text-gray-500">({(excelFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                  </div>
                  
                  {/* 유효성 검증 결과 */}
                  {excelValidation && (
                    <div className="text-left">
                      {excelValidation.valid ? (
                        <div className="bg-green-100 border border-green-300 rounded p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-green-600">✓</span>
                            <span className="font-medium text-green-800">유효성 검증 통과</span>
                          </div>
                          
                          {/* 미리보기 정보 */}
                          {excelValidation.preview && (
                            <div className="text-sm text-gray-700">
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <strong>평가 정보:</strong>
                                  <ul className="list-disc ml-4">
                                    <li>제목: {excelValidation.preview.evaluation_info?.title}</li>
                                    <li>설명: {excelValidation.preview.evaluation_info?.description}</li>
                                  </ul>
                                </div>
                                <div>
                                  <strong>데이터 요약:</strong>
                                  <ul className="list-disc ml-4">
                                    <li>기업 수: {excelValidation.preview.total_companies}개</li>
                                    <li>평가 기준: {excelValidation.preview.total_criteria}개</li>
                                  </ul>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="bg-red-100 border border-red-300 rounded p-3">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-red-600">✗</span>
                            <span className="font-medium text-red-800">유효성 검증 실패</span>
                          </div>
                          <ul className="list-disc ml-4 text-sm text-red-700">
                            {excelValidation.errors.map((error, idx) => (
                              <li key={idx}>{error}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* 경고 메시지 */}
                      {excelValidation.warnings && excelValidation.warnings.length > 0 && (
                        <div className="bg-yellow-100 border border-yellow-300 rounded p-3 mt-2">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-yellow-600">⚠</span>
                            <span className="font-medium text-yellow-800">주의사항</span>
                          </div>
                          <ul className="list-disc ml-4 text-sm text-yellow-700">
                            {excelValidation.warnings.map((warning, idx) => (
                              <li key={idx}>{warning}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* 업로드 진행률 */}
                  {isUploading && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                      <p className="text-sm text-gray-600 mt-1">업로드 중... {uploadProgress}%</p>
                    </div>
                  )}
                  
                  {/* 업로드 결과 */}
                  {uploadResult && (
                    <div className="text-left">
                      {uploadResult.success_count > 0 ? (
                        <div className="bg-green-100 border border-green-300 rounded p-3">
                          <div className="font-medium text-green-800">
                            ✓ 업로드 완료: {uploadResult.success_count}개 평가 생성됨
                          </div>
                          {uploadResult.created_evaluation_ids && (
                            <div className="text-sm text-gray-700 mt-2">
                              생성된 평가 ID: {uploadResult.created_evaluation_ids.join(', ')}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="bg-red-100 border border-red-300 rounded p-3">
                          <div className="font-medium text-red-800">업로드 실패</div>
                          {uploadResult.errors && uploadResult.errors.length > 0 && (
                            <ul className="list-disc ml-4 text-sm text-red-700 mt-2">
                              {uploadResult.errors.map((error, idx) => (
                                <li key={idx}>{error.error || error}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* 업로드 버튼 */}
                  <div className="flex space-x-3">
                    <button
                      onClick={handleExcelUpload}
                      disabled={!excelValidation?.valid || isUploading}
                      className={`inline-flex items-center px-4 py-2 font-medium rounded-lg transition-all duration-200 ${
                        excelValidation?.valid && !isUploading
                          ? 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white hover:from-emerald-700 hover:to-emerald-800 transform hover:scale-105 shadow-md hover:shadow-lg'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {isUploading ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          업로드 중...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          평가 생성
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setExcelFile(null);
                        setExcelValidation(null);
                        setUploadResult(null);
                      }}
                      className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-gray-500 to-gray-600 text-white font-medium rounded-lg hover:from-gray-600 hover:to-gray-700 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      파일 제거
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="mb-4">
                    <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                      <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <div className="text-lg font-medium text-gray-700 mb-2">
                    Excel 파일을 드래그하여 놓거나 클릭하여 선택하세요
                  </div>
                  <div className="text-sm text-gray-500 mb-4">
                    지원 형식: .xlsx, .xls (최대 10MB)
                  </div>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => handleExcelFileSelect(e.target.files[0])}
                    className="hidden"
                    id="excel-upload"
                  />
                  <label
                    htmlFor="excel-upload"
                    className="cursor-pointer inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                    </svg>
                    파일 선택
                  </label>
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* 필터링 섹션 */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-medium mb-3">필터 및 검색</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">프로젝트</label>
              <select
                value={filters.project_id}
                onChange={(e) => setFilters(prev => ({ ...prev, project_id: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="">전체 프로젝트</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="">전체 상태</option>
                <option value="assigned">배정됨</option>
                <option value="in_progress">진행중</option>
                <option value="submitted">제출완료</option>
                <option value="reviewed">검토완료</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">평가위원</label>
              <select
                value={filters.evaluator_id}
                onChange={(e) => setFilters(prev => ({ ...prev, evaluator_id: e.target.value }))}
                className="w-full p-2 border border-gray-300 rounded-lg"
              >
                <option value="">전체 평가위원</option>
                {evaluators.map(evaluator => (
                  <option key={evaluator.id} value={evaluator.id}>{evaluator.user_name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        {evaluations.length === 0 ? (
          <p className="text-gray-500 text-center py-8">등록된 평가가 없습니다.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평가 ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">프로젝트명</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">기업명</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">평가위원</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">생성일</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">작업</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {evaluations.map((evalItem) => (
                  <tr key={evalItem.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {evalItem.id ? evalItem.id.slice(0, 8) + '...' : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{evalItem.project_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{evalItem.company_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{evalItem.evaluator_name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(evalItem.status)}`}>
                        {getStatusText(evalItem.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {evalItem.created_at ? new Date(evalItem.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => setSelectedEvaluation(evalItem)}
                        className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-indigo-100 to-indigo-200 text-indigo-700 font-medium rounded-md hover:from-indigo-200 hover:to-indigo-300 transform hover:scale-105 transition-all duration-200 mr-2"
                      >
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        상세
                      </button>
                      {(user.role === 'admin' || user.role === 'secretary') && (
                        <button
                          onClick={() => handleDeleteEvaluation(evalItem.id)}
                          className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-red-100 to-red-200 text-red-700 font-medium rounded-md hover:from-red-200 hover:to-red-300 transform hover:scale-105 transition-all duration-200"
                        >
                          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          삭제
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {/* 평가 상세 모달 */}
      {selectedEvaluation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4">
            <h3 className="text-lg font-semibold mb-4">평가 상세</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><b>평가 ID:</b> {selectedEvaluation.id}</div>
                <div><b>상태:</b> <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(selectedEvaluation.status)}`}>{getStatusText(selectedEvaluation.status)}</span></div>
                <div><b>프로젝트:</b> {selectedEvaluation.project_name}</div>
                <div><b>기업:</b> {selectedEvaluation.company_name}</div>
                <div><b>평가위원:</b> {selectedEvaluation.evaluator_name}</div>
                <div><b>생성일:</b> {selectedEvaluation.created_at ? new Date(selectedEvaluation.created_at).toLocaleDateString() : '-'}</div>
                {selectedEvaluation.evaluation_date && (
                  <div><b>제출일:</b> {new Date(selectedEvaluation.evaluation_date).toLocaleDateString()}</div>
                )}
              </div>
              
              {selectedEvaluation.scores && Object.keys(selectedEvaluation.scores).length > 0 && (
                <div>
                  <b>평가 점수:</b>
                  <div className="bg-gray-50 p-3 rounded mt-2">
                    {Object.entries(selectedEvaluation.scores).map(([key, value]) => (
                      <div key={key} className="flex justify-between py-1">
                        <span>{key}:</span>
                        <span className="font-medium">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedEvaluation.comments && (
                <div>
                  <b>종합 의견:</b>
                  <div className="bg-gray-50 p-3 rounded mt-2 text-sm">{selectedEvaluation.comments}</div>
                </div>
              )}
            </div>
            <div className="flex justify-between pt-6">
              <div>
                {(user.role === 'admin' || user.role === 'secretary') && (
                  <button
                    onClick={() => {
                      handleDeleteEvaluation(selectedEvaluation.id);
                      setSelectedEvaluation(null);
                    }}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white font-medium rounded-lg hover:from-red-700 hover:to-red-800 transform hover:scale-105 transition-all duration-200 shadow-md hover:shadow-lg"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    삭제
                  </button>
                )}
              </div>
              <div className="space-x-3">
                <button
                  type="button"
                  onClick={() => setSelectedEvaluation(null)}
                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-gray-100 to-gray-200 border border-gray-300 text-gray-700 font-medium rounded-lg hover:from-gray-200 hover:to-gray-300 transform hover:scale-105 transition-all duration-200 shadow-sm hover:shadow-md"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  닫기
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationManagement;
