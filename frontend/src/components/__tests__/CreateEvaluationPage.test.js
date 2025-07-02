import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import CreateEvaluationPage from '../CreateEvaluationPage';

// Mock dependencies
global.fetch = jest.fn();
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn()
};
global.alert = jest.fn();

// Mock props
const mockOnBack = jest.fn();
const mockOnEvaluationCreated = jest.fn();

describe('CreateEvaluationPage Component', () => {
  beforeEach(() => {
    fetch.mockClear();
    localStorage.getItem.mockClear();
    global.alert.mockClear();
    mockOnBack.mockClear();
    mockOnEvaluationCreated.mockClear();
  });

  const mockProject = {
    _id: 'project1',
    project_name: 'Test Project',
    template_id: 'template1'
  };

  const mockTemplate = {
    _id: 'template1',
    template_name: 'Test Template',
    criteria: [
      { criterion_name: 'Quality', max_score: 10, score_step: 1 },
      { criterion_name: 'Innovation', max_score: 20, score_step: 2 },
      { criterion_name: 'Efficiency', max_score: 15, score_step: 1 }
    ]
  };

  const mockCompanies = [
    { _id: 'company1', company_name: 'Company A' },
    { _id: 'company2', company_name: 'Company B' }
  ];

  const setupMocks = () => {
    localStorage.getItem.mockReturnValue('mock-token');
    
    // Mock template fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTemplate
    });
    
    // Mock companies fetch
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCompanies
    });
  };

  test('renders create evaluation page with project info', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    expect(screen.getByText('평가 작성')).toBeInTheDocument();
    expect(screen.getByText('Test Project')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Quality')).toBeInTheDocument();
      expect(screen.getByText('Innovation')).toBeInTheDocument();
      expect(screen.getByText('Efficiency')).toBeInTheDocument();
    });
  });

  test('handles company selection', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByLabelText('평가 대상 기업')).toBeInTheDocument();
    });
    
    const companySelect = screen.getByLabelText('평가 대상 기업');
    fireEvent.change(companySelect, { target: { value: 'company1' } });
    
    expect(companySelect.value).toBe('company1');
  });

  test('handles score input with validation', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Quality')).toBeInTheDocument();
    });
    
    const qualityInput = screen.getByLabelText('Quality 점수');
    
    // Test valid score
    fireEvent.change(qualityInput, { target: { value: '8' } });
    expect(qualityInput.value).toBe('8');
    
    // Test invalid score (over max)
    fireEvent.change(qualityInput, { target: { value: '15' } });
    fireEvent.blur(qualityInput);
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('최대 점수를 초과할 수 없습니다')
      );
    });
  });

  test('handles score step validation', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Innovation')).toBeInTheDocument();
    });
    
    const innovationInput = screen.getByLabelText('Innovation 점수');
    
    // Innovation has score_step of 2
    fireEvent.change(innovationInput, { target: { value: '5' } });
    fireEvent.blur(innovationInput);
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('2의 배수로 입력해주세요')
      );
    });
    
    // Valid score (multiple of 2)
    fireEvent.change(innovationInput, { target: { value: '6' } });
    expect(innovationInput.value).toBe('6');
  });

  test('calculates and displays total score', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Quality')).toBeInTheDocument();
    });
    
    // Enter scores
    fireEvent.change(screen.getByLabelText('Quality 점수'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Innovation 점수'), { target: { value: '16' } });
    fireEvent.change(screen.getByLabelText('Efficiency 점수'), { target: { value: '12' } });
    
    // Check total score
    expect(screen.getByText('총점: 36 / 45')).toBeInTheDocument();
  });

  test('handles comment input', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByLabelText('평가 의견')).toBeInTheDocument();
    });
    
    const commentTextarea = screen.getByLabelText('평가 의견');
    fireEvent.change(commentTextarea, { 
      target: { value: 'This is a comprehensive evaluation comment.' } 
    });
    
    expect(commentTextarea.value).toBe('This is a comprehensive evaluation comment.');
  });

  test('handles evaluation submission', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Quality')).toBeInTheDocument();
    });
    
    // Select company
    fireEvent.change(screen.getByLabelText('평가 대상 기업'), { 
      target: { value: 'company1' } 
    });
    
    // Enter scores
    fireEvent.change(screen.getByLabelText('Quality 점수'), { target: { value: '8' } });
    fireEvent.change(screen.getByLabelText('Innovation 점수'), { target: { value: '16' } });
    fireEvent.change(screen.getByLabelText('Efficiency 점수'), { target: { value: '12' } });
    
    // Enter comment
    fireEvent.change(screen.getByLabelText('평가 의견'), { 
      target: { value: 'Good performance overall.' } 
    });
    
    // Mock successful submission
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ 
        message: 'Evaluation created successfully',
        evaluation_id: 'eval123'
      })
    });
    
    // Submit evaluation
    fireEvent.click(screen.getByText('평가 제출'));
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/evaluations'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"project_id":"project1"')
        })
      );
    });
    
    expect(mockOnEvaluationCreated).toHaveBeenCalled();
  });

  test('validates required fields before submission', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('평가 제출')).toBeInTheDocument();
    });
    
    // Try to submit without selecting company
    fireEvent.click(screen.getByText('평가 제출'));
    
    expect(global.alert).toHaveBeenCalledWith('평가 대상 기업을 선택해주세요.');
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/evaluations'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  test('handles save as draft functionality', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('임시 저장')).toBeInTheDocument();
    });
    
    // Enter partial data
    fireEvent.change(screen.getByLabelText('평가 대상 기업'), { 
      target: { value: 'company1' } 
    });
    fireEvent.change(screen.getByLabelText('Quality 점수'), { target: { value: '5' } });
    
    // Mock draft save
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Draft saved successfully' })
    });
    
    // Save as draft
    fireEvent.click(screen.getByText('임시 저장'));
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/evaluations/draft'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"is_draft":true')
        })
      );
    });
  });

  test('handles back navigation', () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    fireEvent.click(screen.getByText('뒤로 가기'));
    expect(mockOnBack).toHaveBeenCalled();
  });

  test('handles error states gracefully', async () => {
    localStorage.getItem.mockReturnValue('mock-token');
    
    // Mock template fetch error
    fetch.mockRejectedValueOnce(new Error('Failed to load template'));
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('템플릿을 불러오는데 실패했습니다')
      );
    });
  });

  test('displays score guidelines', async () => {
    setupMocks();
    
    render(
      <CreateEvaluationPage
        project={mockProject}
        onBack={mockOnBack}
        onEvaluationCreated={mockOnEvaluationCreated}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText(/최대: 10점/)).toBeInTheDocument();
      expect(screen.getByText(/최대: 20점/)).toBeInTheDocument();
      expect(screen.getByText(/최대: 15점/)).toBeInTheDocument();
    });
  });
});