import React, { useState, useEffect } from 'react';
import './SmartModelTester.css';

const SmartModelTester = ({ availableModels }) => {
  const [testConfig, setTestConfig] = useState({
    selectedModels: [],
    testScenarios: [],
    autoOptimize: true,
    contextAware: true
  });
  const [testResults, setTestResults] = useState([]);
  const [testing, setTesting] = useState(false);
  const [testProgress, setTestProgress] = useState(0);
  const [smartRecommendations, setSmartRecommendations] = useState([]);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8002';

  // 기본 테스트 시나리오들
  const defaultScenarios = [
    {
      id: 'evaluation_basic',
      name: '기본 평가 시나리오',
      prompt: '다음 기업의 기술력을 평가해주세요: 인공지능 기반 의료진단 솔루션을 개발하는 스타트업으로, 자체 개발한 딥러닝 알고리즘을 보유하고 있습니다.',
      expectedTokens: 200,
      category: 'evaluation'
    },
    {
      id: 'analysis_complex',
      name: '복합 분석 시나리오',
      prompt: '제출된 사업계획서를 바탕으로 시장성, 기술성, 사업성을 종합 분석하고 각 항목별 점수와 개선 방안을 제시해주세요.',
      expectedTokens: 400,
      category: 'analysis'
    },
    {
      id: 'summary_concise',
      name: '간결한 요약 시나리오',
      prompt: '20페이지 분량의 기술개발계획서 내용을 3가지 핵심 포인트로 요약해주세요.',
      expectedTokens: 150,
      category: 'summary'
    },
    {
      id: 'recommendation_strategic',
      name: '전략적 추천 시나리오',
      prompt: '중소기업의 디지털 전환을 위한 우선순위와 단계별 실행 계획을 추천해주세요.',
      expectedTokens: 300,
      category: 'recommendation'
    }
  ];

  useEffect(() => {
    setTestConfig(prev => ({
      ...prev,
      testScenarios: defaultScenarios
    }));
  }, []);

  const handleModelToggle = (modelId) => {
    setTestConfig(prev => ({
      ...prev,
      selectedModels: prev.selectedModels.includes(modelId)
        ? prev.selectedModels.filter(id => id !== modelId)
        : [...prev.selectedModels, modelId]
    }));
  };

  const handleScenarioToggle = (scenarioId) => {
    setTestConfig(prev => ({
      ...prev,
      testScenarios: prev.testScenarios.map(scenario =>
        scenario.id === scenarioId
          ? { ...scenario, selected: !scenario.selected }
          : scenario
      )
    }));
  };

  const runSmartTest = async () => {
    if (testConfig.selectedModels.length === 0) {
      alert('테스트할 모델을 선택해주세요');
      return;
    }

    const selectedScenarios = testConfig.testScenarios.filter(s => s.selected);
    if (selectedScenarios.length === 0) {
      alert('테스트 시나리오를 선택해주세요');
      return;
    }

    try {
      setTesting(true);
      setTestProgress(0);
      setTestResults([]);

      const token = localStorage.getItem('token');
      const totalTests = testConfig.selectedModels.length * selectedScenarios.length;
      let completedTests = 0;

      const results = [];

      for (const modelId of testConfig.selectedModels) {
        for (const scenario of selectedScenarios) {
          try {
            // 개별 모델 테스트
            const testResponse = await fetch(`${BACKEND_URL}/api/ai-models/test`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                model_id: modelId,
                test_prompt: scenario.prompt,
                parameters: testConfig.autoOptimize ? { temperature: 0.7, max_tokens: scenario.expectedTokens } : {}
              })
            });

            if (testResponse.ok) {
              const result = await testResponse.json();
              
              // 품질 점수 계산 (실제로는 더 정교한 알고리즘 사용)
              const qualityScore = calculateQualityScore(result.test_result, scenario);
              
              results.push({
                modelId,
                scenarioId: scenario.id,
                scenarioName: scenario.name,
                result: result.test_result,
                qualityScore,
                category: scenario.category
              });
            }

            completedTests++;
            setTestProgress((completedTests / totalTests) * 100);

            // 진행 상황 업데이트를 위한 짧은 지연
            await new Promise(resolve => setTimeout(resolve, 100));

          } catch (error) {
            console.error(`테스트 실패 - Model: ${modelId}, Scenario: ${scenario.id}`, error);
          }
        }
      }

      setTestResults(results);
      
      // 스마트 추천 생성
      if (testConfig.contextAware) {
        generateSmartRecommendations(results);
      }

    } catch (error) {
      console.error('스마트 테스트 실행 오류:', error);
      alert('테스트 실행에 실패했습니다');
    } finally {
      setTesting(false);
      setTestProgress(0);
    }
  };

  const calculateQualityScore = (testResult, scenario) => {
    // 실제로는 더 정교한 품질 평가 알고리즘 사용
    // 현재는 간단한 휴리스틱 사용
    const response = testResult.response || '';
    const responseLength = response.length;
    const expectedLength = scenario.expectedTokens * 4; // 대략적인 문자 수 추정
    
    let score = 0.5; // 기본 점수
    
    // 응답 길이 적절성 (0.3점)
    const lengthRatio = responseLength / expectedLength;
    if (lengthRatio >= 0.7 && lengthRatio <= 1.3) {
      score += 0.3;
    } else if (lengthRatio >= 0.5 && lengthRatio <= 1.5) {
      score += 0.2;
    } else {
      score += 0.1;
    }
    
    // 응답 시간 (0.2점)
    const responseTime = testResult.response_time || 0;
    if (responseTime < 2.0) {
      score += 0.2;
    } else if (responseTime < 4.0) {
      score += 0.1;
    }
    
    // 기본 품질 점수 반영
    score = Math.min(score + (testResult.quality_score || 0), 1.0);
    
    return score;
  };

  const generateSmartRecommendations = (results) => {
    const recommendations = [];
    
    // 모델별 성능 분석
    const modelPerformance = {};
    results.forEach(result => {
      if (!modelPerformance[result.modelId]) {
        modelPerformance[result.modelId] = {
          totalScore: 0,
          count: 0,
          categories: {}
        };
      }
      
      modelPerformance[result.modelId].totalScore += result.qualityScore;
      modelPerformance[result.modelId].count++;
      
      if (!modelPerformance[result.modelId].categories[result.category]) {
        modelPerformance[result.modelId].categories[result.category] = {
          totalScore: 0,
          count: 0
        };
      }
      
      modelPerformance[result.modelId].categories[result.category].totalScore += result.qualityScore;
      modelPerformance[result.modelId].categories[result.category].count++;
    });
    
    // 최고 성능 모델 추천
    let bestModel = null;
    let bestAvgScore = 0;
    
    Object.entries(modelPerformance).forEach(([modelId, perf]) => {
      const avgScore = perf.totalScore / perf.count;
      if (avgScore > bestAvgScore) {
        bestAvgScore = avgScore;
        bestModel = modelId;
      }
    });
    
    if (bestModel) {
      const model = availableModels.find(m => m.model_id === bestModel);
      recommendations.push({
        type: 'best_overall',
        title: '전체 최고 성능 모델',
        model: model?.display_name || bestModel,
        score: bestAvgScore,
        description: `모든 테스트 시나리오에서 평균 ${(bestAvgScore * 100).toFixed(1)}% 성능을 보여주었습니다.`
      });
    }
    
    // 카테고리별 최적 모델 추천
    const categories = ['evaluation', 'analysis', 'summary', 'recommendation'];
    categories.forEach(category => {
      let bestCategoryModel = null;
      let bestCategoryScore = 0;
      
      Object.entries(modelPerformance).forEach(([modelId, perf]) => {
        if (perf.categories[category]) {
          const avgScore = perf.categories[category].totalScore / perf.categories[category].count;
          if (avgScore > bestCategoryScore) {
            bestCategoryScore = avgScore;
            bestCategoryModel = modelId;
          }
        }
      });
      
      if (bestCategoryModel) {
        const model = availableModels.find(m => m.model_id === bestCategoryModel);
        recommendations.push({
          type: 'best_category',
          title: `${getCategoryName(category)} 최적 모델`,
          model: model?.display_name || bestCategoryModel,
          category,
          score: bestCategoryScore,
          description: `${getCategoryName(category)} 작업에서 ${(bestCategoryScore * 100).toFixed(1)}% 성능을 달성했습니다.`
        });
      }
    });
    
    setSmartRecommendations(recommendations);
  };

  const getCategoryName = (category) => {
    const names = {
      'evaluation': '평가',
      'analysis': '분석',
      'summary': '요약',
      'recommendation': '추천'
    };
    return names[category] || category;
  };

  const getModelDisplayName = (modelId) => {
    const model = availableModels.find(m => m.model_id === modelId);
    return model?.display_name || modelId;
  };

  const exportResults = () => {
    const data = {
      testConfig,
      testResults,
      smartRecommendations,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ai-model-test-results-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="smart-model-tester">
      <div className="tester-header">
        <h3>🧪 스마트 모델 테스터</h3>
        <p>다양한 시나리오로 AI 모델을 종합 테스트하고 최적 모델을 찾으세요</p>
      </div>

      <div className="test-configuration">
        <div className="config-section">
          <h4>📋 테스트 설정</h4>
          
          <div className="config-options">
            <label className="config-option">
              <input
                type="checkbox"
                checked={testConfig.autoOptimize}
                onChange={(e) => setTestConfig(prev => ({...prev, autoOptimize: e.target.checked}))}
              />
              자동 매개변수 최적화
            </label>
            
            <label className="config-option">
              <input
                type="checkbox"
                checked={testConfig.contextAware}
                onChange={(e) => setTestConfig(prev => ({...prev, contextAware: e.target.checked}))}
              />
              컨텍스트 인식 분석
            </label>
          </div>
        </div>

        <div className="model-selection">
          <h4>🤖 테스트 모델 선택</h4>
          <div className="model-grid">
            {availableModels.map(model => (
              <div 
                key={model.model_id}
                className={`model-selector-card ${testConfig.selectedModels.includes(model.model_id) ? 'selected' : ''}`}
                onClick={() => handleModelToggle(model.model_id)}
              >
                <div className="model-info">
                  <h5>{model.display_name}</h5>
                  <p>{model.provider.toUpperCase()}</p>
                </div>
                <div className="model-stats">
                  <span>품질: {(model.quality_score * 100).toFixed(0)}%</span>
                  <span>속도: {(model.speed_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="scenario-selection">
          <h4>📝 테스트 시나리오 선택</h4>
          <div className="scenario-grid">
            {testConfig.testScenarios.map(scenario => (
              <div 
                key={scenario.id}
                className={`scenario-card ${scenario.selected ? 'selected' : ''}`}
                onClick={() => handleScenarioToggle(scenario.id)}
              >
                <div className="scenario-header">
                  <h5>{scenario.name}</h5>
                  <span className="scenario-category">{getCategoryName(scenario.category)}</span>
                </div>
                <p className="scenario-prompt">{scenario.prompt}</p>
                <div className="scenario-meta">
                  <span>예상 토큰: {scenario.expectedTokens}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="test-actions">
          <button
            onClick={runSmartTest}
            disabled={testing || testConfig.selectedModels.length === 0}
            className="run-test-btn"
          >
            {testing ? `⏳ 테스트 진행 중... ${testProgress.toFixed(0)}%` : '🚀 스마트 테스트 시작'}
          </button>
          
          {testResults.length > 0 && (
            <button
              onClick={exportResults}
              className="export-results-btn"
            >
              📊 결과 내보내기
            </button>
          )}
        </div>

        {testing && (
          <div className="test-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${testProgress}%` }}
              ></div>
            </div>
            <p>테스트 진행 중: {testProgress.toFixed(0)}%</p>
          </div>
        )}
      </div>

      {testResults.length > 0 && (
        <div className="test-results">
          <h4>📊 테스트 결과</h4>
          
          <div className="results-summary">
            <div className="summary-stats">
              <div className="stat-item">
                <span className="stat-label">총 테스트:</span>
                <span className="stat-value">{testResults.length}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">평균 품질:</span>
                <span className="stat-value">
                  {(testResults.reduce((sum, r) => sum + r.qualityScore, 0) / testResults.length * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          <div className="results-table">
            <table>
              <thead>
                <tr>
                  <th>모델</th>
                  <th>시나리오</th>
                  <th>카테고리</th>
                  <th>품질 점수</th>
                  <th>응답 시간</th>
                  <th>비용</th>
                </tr>
              </thead>
              <tbody>
                {testResults.map((result, index) => (
                  <tr key={index}>
                    <td>{getModelDisplayName(result.modelId)}</td>
                    <td>{result.scenarioName}</td>
                    <td>{getCategoryName(result.category)}</td>
                    <td>
                      <div className="quality-score">
                        <div 
                          className="score-bar"
                          style={{ width: `${result.qualityScore * 100}%` }}
                        ></div>
                        <span>{(result.qualityScore * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td>{result.result.response_time?.toFixed(2)}초</td>
                    <td>${result.result.cost?.toFixed(6)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {smartRecommendations.length > 0 && (
        <div className="smart-recommendations">
          <h4>🎯 스마트 추천</h4>
          <div className="recommendations-grid">
            {smartRecommendations.map((rec, index) => (
              <div key={index} className={`recommendation-card ${rec.type}`}>
                <div className="rec-header">
                  <h5>{rec.title}</h5>
                  <div className="rec-score">
                    {(rec.score * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="rec-content">
                  <p><strong>추천 모델:</strong> {rec.model}</p>
                  <p>{rec.description}</p>
                  {rec.category && (
                    <span className="rec-category">{getCategoryName(rec.category)} 특화</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartModelTester;