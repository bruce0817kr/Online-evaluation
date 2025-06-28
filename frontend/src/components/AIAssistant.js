import React, { useState, useEffect } from 'react';

const AIAssistant = ({ user, onAnalysisComplete }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [documentText, setDocumentText] = useState('');
  const [documentType, setDocumentType] = useState('business_plan');
  const [aiStatus, setAiStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('analyze');

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';

  // AI 서비스 상태 확인
  useEffect(() => {
    checkAIStatus();
  }, []);

  const checkAIStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('인증 토큰이 없습니다.');
        return;
      }

      const response = await fetch(`${BACKEND_URL}/api/ai/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAiStatus(data.status || data);
      } else if (response.status === 401) {
        console.warn('AI 상태 확인 권한이 없습니다.');
      } else if (response.status === 404) {
        console.warn('AI 상태 API를 찾을 수 없습니다.');
      } else {
        console.error(`AI 상태 확인 실패: ${response.status}`);
      }
    } catch (error) {
      console.error('AI 상태 확인 네트워크 오류:', error);
      // 네트워크 오류 시 기본 상태 설정
      setAiStatus({
        service_status: 'degraded',
        openai_available: false,
        anthropic_available: false,
        templates_loaded: 0
      });
    }
  };

  const analyzeDocument = async () => {
    if (!documentText.trim()) {
      alert('분석할 문서 내용을 입력해주세요.');
      return;
    }

    if (documentText.length > 50000) {
      alert('문서 내용이 너무 깁니다. 50,000자 이하로 입력해주세요.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResults(null);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('로그인이 필요합니다.');
      }

      const response = await fetch(`${BACKEND_URL}/api/ai/analyze-document`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          document_text: documentText,
          document_type: documentType
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisResults(data);
        if (onAnalysisComplete) {
          onAnalysisComplete(data);
        }
      } else if (response.status === 401) {
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (response.status === 403) {
        throw new Error('AI 분석 기능에 대한 권한이 없습니다.');
      } else if (response.status === 404) {
        throw new Error('AI 분석 서비스를 사용할 수 없습니다.');
      } else if (response.status === 429) {
        throw new Error('요청이 너무 많습니다. 잠시 후 다시 시도해주세요.');
      } else if (response.status >= 500) {
        throw new Error('서버 오류가 발생했습니다. 관리자에게 문의하세요.');
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `분석 중 오류가 발생했습니다 (${response.status})`);
      }
    } catch (error) {
      console.error('AI 문서 분석 오류:', error);
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        alert('네트워크 연결을 확인해주세요.');
      } else {
        alert(`분석 오류: ${error.message}`);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const suggestScores = async () => {
    if (!analysisResults) {
      alert('먼저 문서 분석을 수행해주세요.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai/suggest-scores`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          document_analysis: analysisResults.results,
          template_type: 'digital_transformation'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisResults(prev => ({
          ...prev,
          score_suggestions: data.suggestions
        }));
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '점수 제안 중 오류가 발생했습니다.');
      }
    } catch (error) {
      alert(`점수 제안 오류: ${error.message}`);
    }
  };

  const extractInformation = async () => {
    if (!documentText.trim()) {
      alert('정보를 추출할 문서 내용을 입력해주세요.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/ai/extract-information`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          document_text: documentText,
          document_type: documentType
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisResults(prev => ({
          ...prev,
          extracted_information: data.extracted_information
        }));
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || '정보 추출 중 오류가 발생했습니다.');
      }
    } catch (error) {
      alert(`정보 추출 오류: ${error.message}`);
    }
  };

  // 권한 확인
  if (!user || !['admin', 'secretary', 'evaluator'].includes(user.role)) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">🤖 AI 평가 도우미</h2>
        <p className="text-gray-600">이 기능은 관리자, 간사, 평가위원만 사용할 수 있습니다.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">🤖 AI 평가 도우미</h2>
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 text-xs rounded-full ${
              aiStatus?.service_status === 'operational' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {aiStatus?.service_status === 'operational' ? '정상 작동' : '제한 모드'}
            </span>
          </div>
        </div>
        
        {/* 탭 네비게이션 */}
        <div className="flex space-x-4 mt-4">
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-4 py-2 rounded-lg ${
              activeTab === 'analyze' 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            문서 분석
          </button>
          <button
            onClick={() => setActiveTab('extract')}
            className={`px-4 py-2 rounded-lg ${
              activeTab === 'extract' 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            정보 추출
          </button>
          {user.role === 'evaluator' && (
            <button
              onClick={() => setActiveTab('scores')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'scores' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              점수 제안
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {/* 문서 분석 탭 */}
        {activeTab === 'analyze' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                문서 유형
              </label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg"
              >
                <option value="business_plan">사업계획서</option>
                <option value="technical_plan">기술계획서</option>
                <option value="financial_plan">재무계획서</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                문서 내용
              </label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                placeholder="분석할 문서의 내용을 입력하거나 붙여넣기 하세요..."
                className="w-full h-40 p-3 border border-gray-300 rounded-lg resize-none"
              />
            </div>

            <button
              onClick={analyzeDocument}
              disabled={isAnalyzing || !documentText.trim()}
              className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? '🔄 분석 중...' : '📊 AI 분석 시작'}
            </button>
          </div>
        )}

        {/* 정보 추출 탭 */}
        {activeTab === 'extract' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                문서 내용
              </label>
              <textarea
                value={documentText}
                onChange={(e) => setDocumentText(e.target.value)}
                placeholder="핵심 정보를 추출할 문서의 내용을 입력하세요..."
                className="w-full h-40 p-3 border border-gray-300 rounded-lg resize-none"
              />
            </div>

            <button
              onClick={extractInformation}
              disabled={!documentText.trim()}
              className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🔍 핵심 정보 추출
            </button>
          </div>
        )}

        {/* 점수 제안 탭 */}
        {activeTab === 'scores' && user.role === 'evaluator' && (
          <div className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-medium text-blue-800 mb-2">📋 평가 점수 AI 제안</h3>
              <p className="text-blue-600 text-sm">
                문서 분석 결과를 바탕으로 객관적인 평가 점수를 제안받을 수 있습니다.
                최종 점수는 평가위원의 전문적 판단에 따라 결정됩니다.
              </p>
            </div>

            <button
              onClick={suggestScores}
              disabled={!analysisResults}
              className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              🎯 AI 점수 제안 받기
            </button>

            {!analysisResults && (
              <p className="text-gray-500 text-sm text-center">
                먼저 문서 분석을 수행해주세요.
              </p>
            )}
          </div>
        )}

        {/* 분석 결과 표시 */}
        {analysisResults && (
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold">📋 분석 결과</h3>
            
            {/* 기본 분석 결과 */}
            {analysisResults.results && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium mb-3">문서 분석</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {analysisResults.results.structure_score || 0}
                    </div>
                    <div className="text-sm text-gray-600">구성도</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {analysisResults.results.innovation_score || 0}
                    </div>
                    <div className="text-sm text-gray-600">혁신성</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                      {analysisResults.results.feasibility_score || 0}
                    </div>
                    <div className="text-sm text-gray-600">실현가능성</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {analysisResults.results.market_score || 0}
                    </div>
                    <div className="text-sm text-gray-600">시장성</div>
                  </div>
                </div>

                {analysisResults.results.keywords && (
                  <div className="mb-3">
                    <h5 className="font-medium mb-2">주요 키워드</h5>
                    <div className="flex flex-wrap gap-2">
                      {analysisResults.results.keywords.map((keyword, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {analysisResults.results.summary && (
                  <div>
                    <h5 className="font-medium mb-2">분석 요약</h5>
                    <p className="text-gray-700">{analysisResults.results.summary}</p>
                  </div>
                )}
              </div>
            )}

            {/* 점수 제안 결과 */}
            {analysisResults.score_suggestions && (
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-medium mb-3">🎯 AI 점수 제안</h4>
                <div className="text-sm text-purple-600 mb-3">
                  ⚠️ 이 점수는 AI의 제안입니다. 최종 평가는 평가위원의 판단에 따라 결정됩니다.
                </div>
                <div className="space-y-2">
                  {analysisResults.score_suggestions.criteria_scores?.map((criterion, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-white rounded">
                      <span className="font-medium">{criterion.name}</span>
                      <span className="text-purple-600 font-bold">{criterion.suggested_score}점</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 추출된 정보 */}
            {analysisResults.extracted_information && (
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium mb-3">🔍 추출된 정보</h4>
                <div className="space-y-2">
                  {Object.entries(analysisResults.extracted_information).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="font-medium capitalize">{key.replace('_', ' ')}:</span>
                      <span className="text-gray-700">{JSON.stringify(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 분석 메타 정보 */}
            <div className="text-xs text-gray-500 border-t pt-3">
              <div className="flex justify-between">
                <span>AI 제공: {analysisResults.ai_provider}</span>
                <span>처리 시간: {analysisResults.processing_time?.toFixed(2)}초</span>
              </div>
            </div>
          </div>
        )}

        {/* AI 상태 정보 */}
        {aiStatus && (
          <div className="mt-6 p-4 bg-white rounded-lg border border-gray-300 shadow-sm">
            <h4 className="font-medium mb-2 text-gray-900">🔧 AI 서비스 상태</h4>
            <div className="text-sm space-y-1">
              <div className="text-gray-800">OpenAI: {aiStatus.openai_available ? '✅ 사용 가능' : '❌ 비활성화'}</div>
              <div className="text-gray-800">Claude: {aiStatus.anthropic_available ? '✅ 사용 가능' : '❌ 비활성화'}</div>
              <div className="text-gray-800">평가 템플릿: {aiStatus.templates_loaded}개 로드됨</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAssistant;