import React, { useState, useEffect } from 'react';
import EvaluationCriteriaForm from './EvaluationCriteriaForm.js';
import './CreateEvaluationPage.css';

const CreateEvaluationPage = ({ user, onEvaluationCreated, onCancel }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    companiesText: '',
    status: 'draft'
  });
  
  const [criteriaList, setCriteriaList] = useState([
    { name: '', max_score: 0, bonus: false, description: '' }
  ]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const steps = [
    { number: 1, title: '기본 정보', description: '평가 제목, 설명, 대상 기업 설정' },
    { number: 2, title: '평가 기준', description: '평가 항목 및 점수 시스템 설정' },
    { number: 3, title: '검토 및 생성', description: '설정 내용 확인 및 평가 생성' }
  ];

  const updateCriterion = (index, updates) => {
    setCriteriaList(prev => 
      prev.map((criterion, i) => 
        i === index ? { ...criterion, ...updates } : criterion
      )
    );
  };

  const addCriterion = () => {
    setCriteriaList(prev => [
      ...prev, 
      { name: '', max_score: 0, bonus: false, description: '' }
    ]);
  };
  const removeCriterion = (index) => {
    if (criteriaList.length > 1) {
      setCriteriaList(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleStepNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleStepPrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const validateStep1 = () => {
    const errors = [];
    if (!formData.title.trim()) {
      errors.push('평가 제목을 입력해주세요.');
    }
    if (!formData.companiesText.trim()) {
      errors.push('대상 기업을 입력해주세요.');
    }
    return errors;
  };

  const validateStep2 = () => {
    const validCriteria = criteriaList.filter(c => c.name.trim() && c.max_score > 0);
    if (validCriteria.length === 0) {
      return ['최소 1개의 평가 항목을 설정해주세요.'];
    }
    return [];
  };

  const handleCriteriaSave = (savedCriteria) => {
    setCriteriaList(savedCriteria);
    handleStepNext();
  };

  const handleStep1Submit = (e) => {
    e.preventDefault();
    const errors = validateStep1();
    if (errors.length > 0) {
      setError(errors.join('\n'));
      return;
    }
    setError('');
    handleStepNext();
  };
  const handleSubmit = async () => {
    setLoading(true);
    setError('');

    try {
      // 최종 검증
      const step1Errors = validateStep1();
      const step2Errors = validateStep2();
      const allErrors = [...step1Errors, ...step2Errors];
      
      if (allErrors.length > 0) {
        throw new Error(allErrors.join('\n'));
      }

      // 기업 목록 파싱 (개행 또는 쉼표로 구분)
      const companies = formData.companiesText
        .split(/[\r\n,]+/)
        .map(company => company.trim())
        .filter(company => company.length > 0);

      // 유효한 평가 기준만 필터링
      const validCriteria = criteriaList.filter(c => c.name.trim() && c.max_score > 0);

      // API 요청 데이터 구성
      const payload = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        companies: companies,
        criteria: validCriteria,
        status: formData.status
      };

      // JWT 토큰 가져오기
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('로그인이 필요합니다.');
      }

      // API 호출
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019'}/api/evaluations`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '평가 생성에 실패했습니다.');
      }

      const result = await response.json();
      
      // 성공 처리
      alert('평가가 성공적으로 생성되었습니다.');
      
      // 부모 컴포넌트에 알림
      if (onEvaluationCreated) {
        onEvaluationCreated(result);
      }

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="create-evaluation-page">
      <div className="page-header">
        <h1>새 평가 생성</h1>
        <div className="steps-indicator">
          {steps.map((step) => (
            <div 
              key={step.number}
              className={`step ${currentStep === step.number ? 'active' : ''} ${currentStep > step.number ? 'completed' : ''}`}
            >
              <div className="step-number">{step.number}</div>
              <div className="step-info">
                <div className="step-title">{step.title}</div>
                <div className="step-description">{step.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error.split('\n').map((line, index) => (
            <div key={index}>{line}</div>
          ))}
        </div>
      )}

      <div className="step-content">
        {currentStep === 1 && (
          <form onSubmit={handleStep1Submit} className="evaluation-form">
            <div className="form-section">
              <h2>평가 기본 정보</h2>
              
              <div className="form-group">
                <label htmlFor="title">평가 제목 *</label>
                <input
                  type="text"
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="예: 2025년 상반기 혁신기업 평가"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">평가 설명</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="평가의 목적과 개요를 입력하세요."
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label htmlFor="status">평가 상태</label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                >
                  <option value="draft">초안</option>
                  <option value="active">활성</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="companies">대상 기업 *</label>
                <textarea
                  id="companies"
                  value={formData.companiesText}
                  onChange={(e) => setFormData(prev => ({ ...prev, companiesText: e.target.value }))}
                  placeholder="기업명을 한 줄에 하나씩 또는 쉼표로 구분하여 입력하세요.&#10;예:&#10;삼성전자&#10;LG전자&#10;현대자동차"
                  rows="6"
                  required
                />
                <div className="form-help">
                  기업명을 개행(엔터) 또는 쉼표(,)로 구분하여 입력하세요.
                </div>
              </div>
            </div>

            <div className="step-actions">
              {onCancel && (
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={onCancel}
                >
                  취소
                </button>
              )}
              <button
                type="submit"
                className="next-btn"
              >
                다음 단계
              </button>
            </div>
          </form>
        )}

        {currentStep === 2 && (
          <EvaluationCriteriaForm
            initialCriteria={criteriaList}
            onSave={handleCriteriaSave}
            onCancel={handleStepPrev}
            mode="create"
          />
        )}

        {currentStep === 3 && (
          <div className="review-section">
            <h2>설정 내용 검토</h2>
            
            <div className="review-card">
              <h3>평가 기본 정보</h3>
              <div className="review-item">
                <span className="label">제목:</span>
                <span className="value">{formData.title}</span>
              </div>
              {formData.description && (
                <div className="review-item">
                  <span className="label">설명:</span>
                  <span className="value">{formData.description}</span>
                </div>
              )}
              <div className="review-item">
                <span className="label">상태:</span>
                <span className="value">{formData.status === 'draft' ? '초안' : '활성'}</span>
              </div>
              <div className="review-item">
                <span className="label">대상 기업:</span>
                <span className="value">
                  {formData.companiesText
                    .split(/[\r\n,]+/)
                    .map(company => company.trim())
                    .filter(company => company.length > 0)
                    .join(', ')}
                </span>
              </div>
            </div>

            <div className="review-card">
              <h3>평가 기준</h3>
              <div className="criteria-summary">
                <div className="score-totals">
                  <span>기본 총점: {criteriaList.filter(c => !c.bonus).reduce((sum, c) => sum + (c.max_score || 0), 0)}점</span>
                  <span>가점 총점: +{criteriaList.filter(c => c.bonus).reduce((sum, c) => sum + (c.max_score || 0), 0)}점</span>
                </div>
                <div className="criteria-list">
                  {criteriaList.filter(c => c.name.trim() && c.max_score > 0).map((criterion, index) => (
                    <div key={index} className={`criterion-item ${criterion.bonus ? 'bonus' : ''}`}>
                      <span className="criterion-name">
                        {criterion.name}
                        {criterion.bonus && <span className="bonus-badge">가점</span>}
                      </span>
                      <span className="criterion-score">{criterion.max_score}점</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="step-actions">
              <button
                type="button"
                className="prev-btn"
                onClick={handleStepPrev}
              >
                이전 단계
              </button>
              <button
                type="button"
                className="create-btn"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? '생성 중...' : '평가 생성'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CreateEvaluationPage;
