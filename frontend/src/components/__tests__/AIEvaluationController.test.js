import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders, setupFetchMock, mockAdminUser, mockApiResponses, clearAllMocks, expectAuthenticatedApiCall } from '../../test-utils';
import AIEvaluationController from '../AIEvaluationController';

// Mock CSS import
jest.mock('../AIEvaluationController.css', () => ({}));

describe('AIEvaluationController Component', () => {
  beforeEach(() => {
    clearAllMocks();
    localStorage.getItem.mockReturnValue('mock-jwt-token');
  });

  const mockEvaluations = [
    {
      _id: '1',
      project_name: 'AI Project 1',
      company_name: 'Tech Corp',
      status: 'pending',
      ai_settings: {
        model: 'gpt-4',
        temperature: 0.7,
        auto_evaluate: true
      }
    },
    {
      _id: '2',
      project_name: 'AI Project 2',
      company_name: 'Innovation Inc',
      status: 'in_progress',
      ai_settings: {
        model: 'claude-2',
        temperature: 0.5,
        auto_evaluate: false
      }
    }
  ];

  test('renders AI evaluation controller interface', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    expect(screen.getByText('AI 평가 컨트롤러')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
      expect(screen.getByText('AI Project 2')).toBeInTheDocument();
    });
  });

  test('handles AI model selection', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    const modelSelect = screen.getAllByLabelText('AI 모델')[0];
    fireEvent.change(modelSelect, { target: { value: 'gpt-3.5-turbo' } });
    
    expect(modelSelect.value).toBe('gpt-3.5-turbo');
  });

  test('handles temperature adjustment', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    const temperatureSlider = screen.getAllByLabelText('Temperature')[0];
    fireEvent.change(temperatureSlider, { target: { value: '0.9' } });
    
    expect(temperatureSlider.value).toBe('0.9');
  });

  test('handles auto-evaluation toggle', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    const autoEvalCheckbox = screen.getAllByLabelText('자동 평가')[0];
    expect(autoEvalCheckbox).toBeChecked();
    
    fireEvent.click(autoEvalCheckbox);
    expect(autoEvalCheckbox).not.toBeChecked();
  });

  test('handles manual AI evaluation trigger', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    // Mock AI evaluation response
    setupFetchMock({
        evaluation_id: '1',
        ai_scores: { quality: 8, innovation: 9 },
        ai_feedback: 'Good performance overall'
      });

    const evaluateButton = screen.getAllByText('AI 평가 실행')[0];
    fireEvent.click(evaluateButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ai/evaluate'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"evaluation_id":"1"')
        })
      );
    });
  });

  test('displays AI evaluation results', async () => {
    const evaluationsWithResults = [{
      ...mockEvaluations[0],
      ai_results: {
        scores: { quality: 8, innovation: 9 },
        feedback: 'Excellent work',
        confidence: 0.95
      }
    }];

    setupFetchMock(evaluationsWithResults);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI 평가 결과')).toBeInTheDocument();
      expect(screen.getByText('Excellent work')).toBeInTheDocument();
      expect(screen.getByText('신뢰도: 95%')).toBeInTheDocument();
    });
  });

  test('handles batch AI evaluation', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    // Select multiple evaluations
    const checkboxes = screen.getAllByRole('checkbox', { name: /선택/ });
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);

    // Mock batch evaluation response
    setupFetchMock({
        processed: 2,
        results: [
          { evaluation_id: '1', status: 'success' },
          { evaluation_id: '2', status: 'success' }
        ]
      });

    const batchButton = screen.getByText('선택 항목 일괄 AI 평가');
    fireEvent.click(batchButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ai/batch-evaluate'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"evaluation_ids":["1","2"]')
        })
      );
    });
  });

  test('handles AI settings update', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    // Update settings
    const modelSelect = screen.getAllByLabelText('AI 모델')[0];
    fireEvent.change(modelSelect, { target: { value: 'claude-2' } });

    // Mock settings update
    setupFetchMock({ message: 'Settings updated' });

    const saveButton = screen.getAllByText('설정 저장')[0];
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ai/settings'),
        expect.objectContaining({
          method: 'PUT',
          body: expect.stringContaining('"model":"claude-2"')
        })
      );
    });
  });

  test('displays evaluation progress', async () => {
    const evaluationsInProgress = [{
      ...mockEvaluations[1],
      ai_progress: {
        current_step: 'analyzing',
        progress: 45,
        estimated_time: 30
      }
    }];

    setupFetchMock(evaluationsInProgress);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('분석 중...')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument();
      expect(screen.getByText('예상 시간: 30초')).toBeInTheDocument();
    });
  });

  test('handles AI evaluation cancellation', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 2')).toBeInTheDocument();
    });

    // Mock cancellation
    setupFetchMock({ message: 'Evaluation cancelled' });

    const cancelButton = screen.getAllByText('취소')[1];
    fireEvent.click(cancelButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ai/evaluate/2/cancel'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  test('handles error states gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('평가 목록을 불러올 수 없습니다')).toBeInTheDocument();
    });
  });

  test('displays AI model comparison', async () => {
    setupFetchMock(mockEvaluations);

    renderWithProviders(<AIEvaluationController user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('AI Project 1')).toBeInTheDocument();
    });

    // Toggle comparison mode
    fireEvent.click(screen.getByText('모델 비교'));
    
    // Mock comparison data
    setupFetchMock({
        models: ['gpt-4', 'claude-2'],
        comparison: {
          accuracy: { 'gpt-4': 0.92, 'claude-2': 0.89 },
          speed: { 'gpt-4': 2.3, 'claude-2': 1.8 },
          cost: { 'gpt-4': 0.03, 'claude-2': 0.02 }
        }
      });

    await waitFor(() => {
      expect(screen.getByText('모델 성능 비교')).toBeInTheDocument();
      expect(screen.getByText('정확도')).toBeInTheDocument();
      expect(screen.getByText('속도')).toBeInTheDocument();
      expect(screen.getByText('비용')).toBeInTheDocument();
    });
  });
});