import React, { useState, useEffect } from 'react';
import './EvaluationCriteriaForm.css';

const EvaluationCriteriaForm = ({ 
  onSave, 
  onCancel, 
  initialCriteria = [], 
  mode = 'create', // 'create' or 'edit'
  evaluationId = null 
}) => {
  const [criteriaList, setCriteriaList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [previewMode, setPreviewMode] = useState(false);

  // 기본 평가 기준 템플릿
  const defaultTemplates = {
    startup: [
      { name: '사업성', max_score: 25, bonus: false, description: '사업 모델의 실현 가능성과 수익성' },
      { name: '혁신성', max_score: 25, bonus: false, description: '기술적 혁신도와 창의성' },
      { name: '성장성', max_score: 25, bonus: false, description: '향후 성장 가능성과 확장성' },
      { name: '팀 역량', max_score: 20, bonus: false, description: '팀의 전문성과 실행 능력' },
      { name: '특별 가점', max_score: 5, bonus: true, description: '특별한 성과나 우수 사항' }
    ],
    innovation: [
      { name: '기술 혁신도', max_score: 30, bonus: false, description: '기술의 혁신성과 차별성' },
      { name: '시장 파급력', max_score: 25, bonus: false, description: '시장에 미치는 영향력' },
      { name: '상용화 가능성', max_score: 20, bonus: false, description: '실제 상용화 및 사업화 가능성' },
      { name: '기술 완성도', max_score: 20, bonus: false, description: '기술 개발 수준과 완성도' },
      { name: '우수성 가점', max_score: 5, bonus: true, description: '특별한 우수성과 추가 평가 요소' }
    ],
    general: [
      { name: '종합 평가', max_score: 100, bonus: false, description: '전반적인 종합 평가' }
    ]
  };

  useEffect(() => {
    if (initialCriteria && initialCriteria.length > 0) {
      setCriteriaList(initialCriteria);
    } else {
      setCriteriaList([{ name: '', max_score: 0, bonus: false, description: '', weight: 1.0, category: '' }]);
    }
  }, [initialCriteria]);

  const addCriterion = () => {
    setCriteriaList(prev => [
      ...prev,
      { name: '', max_score: 0, bonus: false, description: '', weight: 1.0, category: '' }
    ]);
  };

  const removeCriterion = (index) => {
    if (criteriaList.length > 1) {
      setCriteriaList(prev => prev.filter((_, i) => i !== index));
    }
  };

  const updateCriterion = (index, updates) => {
    setCriteriaList(prev =>
      prev.map((criterion, i) =>
        i === index ? { ...criterion, ...updates } : criterion
      )
    );
  };

  const loadTemplate = (templateKey) => {
    const template = defaultTemplates[templateKey];
    if (template) {
      setCriteriaList(template);
    }
  };

  const calculateTotalScore = () => {
    return criteriaList.reduce((total, criterion) => {
      if (criterion.bonus) return total; // 가점 항목은 총점에서 제외
      return total + (criterion.max_score || 0);
    }, 0);
  };

  const calculateBonusScore = () => {
    return criteriaList.reduce((total, criterion) => {
      if (!criterion.bonus) return total;
      return total + (criterion.max_score || 0);
    }, 0);
  };

  const validateCriteria = () => {
    const errors = [];
    
    criteriaList.forEach((criterion, index) => {
      if (!criterion.name.trim()) {
        errors.push(`항목 ${index + 1}: 항목명이 필요합니다.`);
      }
      if (!criterion.max_score || criterion.max_score <= 0) {
        errors.push(`항목 ${index + 1}: 유효한 배점이 필요합니다.`);
      }
      if (criterion.max_score > 100) {
        errors.push(`항목 ${index + 1}: 배점은 100점을 초과할 수 없습니다.`);
      }
    });

    const validCriteria = criteriaList.filter(c => c.name.trim() && c.max_score > 0);
    if (validCriteria.length === 0) {
      errors.push('최소 1개의 유효한 평가 항목이 필요합니다.');
    }

    return errors;
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');

    try {
      const errors = validateCriteria();
      if (errors.length > 0) {
        throw new Error(errors.join('\\n'));
      }

      const validCriteria = criteriaList.filter(c => c.name.trim() && c.max_score > 0);
      
      if (onSave) {
        await onSave(validCriteria);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = () => {
    setPreviewMode(!previewMode);
  };

  if (previewMode) {
    return (
      <div className="evaluation-criteria-form">
        <div className="form-header">
          <h2>평가 기준 미리보기</h2>
          <button 
            className="preview-btn"
            onClick={handlePreview}
          >
            편집 모드로 돌아가기
          </button>
        </div>

        <div className="criteria-preview">
          <div className="score-summary">
            <div className="score-item">
              <span className="label">기본 총점:</span>
              <span className="value">{calculateTotalScore()}점</span>
            </div>
            <div className="score-item">
              <span className="label">가점 총점:</span>
              <span className="value">+{calculateBonusScore()}점</span>
            </div>
            <div className="score-item total">
              <span className="label">최대 가능 점수:</span>
              <span className="value">{calculateTotalScore() + calculateBonusScore()}점</span>
            </div>
          </div>

          <div className="criteria-list-preview">
            {criteriaList.map((criterion, index) => (
              <div key={index} className={`criterion-preview ${criterion.bonus ? 'bonus' : ''}`}>
                <div className="criterion-info">
                  <h4>
                    {criterion.name}
                    {criterion.bonus && <span className="bonus-badge">가점</span>}
                  </h4>
                  <div className="score-info">
                    <span className="max-score">{criterion.max_score}점</span>
                    {criterion.weight !== 1.0 && (
                      <span className="weight">가중치: {criterion.weight}</span>
                    )}
                  </div>
                  {criterion.category && (
                    <div className="category-tag">{criterion.category}</div>
                  )}
                  {criterion.description && (
                    <p className="description">{criterion.description}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="form-actions">
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
            type="button"
            className="save-btn"
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? '저장 중...' : '평가 기준 저장'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="evaluation-criteria-form">
      <div className="form-header">
        <h2>{mode === 'edit' ? '평가 기준 수정' : '평가 기준 설정'}</h2>
        <div className="header-actions">
          <button 
            className="preview-btn"
            onClick={handlePreview}
          >
            미리보기
          </button>
        </div>
      </div>

      {error && (
        <div className="error-alert">
          <span className="error-icon">⚠️</span>
          {error.split('\\n').map((line, index) => (
            <div key={index}>{line}</div>
          ))}
        </div>
      )}

      {/* 템플릿 선택 */}
      <div className="template-section">
        <h3>템플릿 사용</h3>
        <div className="template-buttons">
          <button 
            type="button" 
            className="template-btn"
            onClick={() => loadTemplate('startup')}
          >
            스타트업 평가
          </button>
          <button 
            type="button" 
            className="template-btn"
            onClick={() => loadTemplate('innovation')}
          >
            혁신 기술 평가
          </button>
          <button 
            type="button" 
            className="template-btn"
            onClick={() => loadTemplate('general')}
          >
            일반 평가
          </button>
        </div>
      </div>

      {/* 점수 요약 */}
      <div className="score-summary">
        <div className="score-item">
          <span className="label">기본 총점:</span>
          <span className="value">{calculateTotalScore()}점</span>
        </div>
        <div className="score-item">
          <span className="label">가점 총점:</span>
          <span className="value">+{calculateBonusScore()}점</span>
        </div>
        <div className="score-item total">
          <span className="label">최대 가능 점수:</span>
          <span className="value">{calculateTotalScore() + calculateBonusScore()}점</span>
        </div>
      </div>

      {/* 평가 항목 목록 */}
      <div className="criteria-section">
        <h3>평가 항목</h3>
        
        {criteriaList.map((criterion, index) => (
          <div key={index} className="criterion-item">
            <div className="criterion-header">
              <h4>항목 {index + 1}</h4>
              {criteriaList.length > 1 && (
                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => removeCriterion(index)}
                >
                  삭제
                </button>
              )}
            </div>

            <div className="criterion-fields">
              <div className="field-row">
                <div className="form-group">
                  <label>항목명 *</label>
                  <input
                    type="text"
                    value={criterion.name}
                    onChange={(e) => updateCriterion(index, { name: e.target.value })}
                    placeholder="예: 혁신성, 사업성, 기술력"
                  />
                </div>

                <div className="form-group">
                  <label>카테고리</label>
                  <select
                    value={criterion.category || ''}
                    onChange={(e) => updateCriterion(index, { category: e.target.value })}
                  >
                    <option value="">선택 안함</option>
                    <option value="기술">기술</option>
                    <option value="사업">사업</option>
                    <option value="팀">팀</option>
                    <option value="시장">시장</option>
                    <option value="기타">기타</option>
                  </select>
                </div>
              </div>

              <div className="field-row">
                <div className="form-group">
                  <label>배점 *</label>
                  <input
                    type="number"
                    value={criterion.max_score}
                    onChange={(e) => updateCriterion(index, { max_score: parseInt(e.target.value) || 0 })}
                    min="1"
                    max="100"
                    placeholder="최대 점수"
                  />
                </div>

                <div className="form-group">
                  <label>가중치</label>
                  <input
                    type="number"
                    step="0.1"
                    value={criterion.weight || 1.0}
                    onChange={(e) => updateCriterion(index, { weight: parseFloat(e.target.value) || 1.0 })}
                    min="0.1"
                    max="3.0"
                    placeholder="1.0"
                  />
                </div>
              </div>

              <div className="form-group checkbox-group">
                <label>
                  <input
                    type="checkbox"
                    checked={criterion.bonus || false}
                    onChange={(e) => updateCriterion(index, { bonus: e.target.checked })}
                  />
                  가점 항목
                </label>
              </div>

              <div className="form-group">
                <label>항목 설명</label>
                <textarea
                  value={criterion.description || ''}
                  onChange={(e) => updateCriterion(index, { description: e.target.value })}
                  placeholder="평가 항목에 대한 상세 설명"
                  rows="2"
                />
              </div>
            </div>
          </div>
        ))}

        <button
          type="button"
          className="add-criterion-btn"
          onClick={addCriterion}
        >
          + 평가 항목 추가
        </button>
      </div>

      {/* 액션 버튼 */}
      <div className="form-actions">
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
          type="button"
          className="save-btn"
          onClick={handleSave}
          disabled={loading}
        >
          {loading ? '저장 중...' : '평가 기준 저장'}
        </button>
      </div>
    </div>
  );
};

export default EvaluationCriteriaForm;
