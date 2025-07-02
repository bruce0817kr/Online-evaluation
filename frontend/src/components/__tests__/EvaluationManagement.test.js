import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import { renderWithProviders, setupFetchMock, mockAdminUser, mockApiResponses, clearAllMocks, expectAuthenticatedApiCall, createMockEvaluation } from '../../test-utils';
import EvaluationManagement from '../EvaluationManagement';

// Mock CSS import
jest.mock('../EvaluationManagement.css', () => ({}));

describe('EvaluationManagement Component', () => {
  beforeEach(() => {
    clearAllMocks();
    localStorage.getItem.mockReturnValue('mock-jwt-token');
  });

  const mockEvaluations = [
    {
      _id: 'eval-1',
      template_id: 'template-1',
      evaluator_id: 'user-1',
      project_id: 'project-1',
      project_name: 'Test Project 1',
      company_name: 'Test Company',
      template_name: 'Test Template',
      evaluator_name: 'Test Evaluator',
      scores: { 'Quality': 8, 'Performance': 9 },
      status: 'completed',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T12:00:00Z'
    },
    {
      _id: 'eval-2',
      template_id: 'template-2',
      evaluator_id: 'user-2',
      project_id: 'project-2',
      project_name: 'Test Project 2',
      company_name: 'Test Company 2',
      template_name: 'Test Template 2',
      evaluator_name: 'Test Evaluator 2',
      scores: { 'Innovation': 7 },
      status: 'draft',
      created_at: '2025-01-02T00:00:00Z',
      updated_at: '2025-01-02T10:00:00Z'
    }
  ];

  test('renders evaluation management component', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    expect(screen.getByText('평가 관리')).toBeInTheDocument();
    expect(screen.getByText('새 평가 생성')).toBeInTheDocument();
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations', 'GET');
    });
  });

  test('loads and displays evaluations', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('Test Project 2')).toBeInTheDocument();
      expect(screen.getByText('완료')).toBeInTheDocument();
      expect(screen.getByText('초안')).toBeInTheDocument();
    });
  });

  test('filters evaluations by status', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('Test Project 2')).toBeInTheDocument();
    });
    
    // Filter by completed status
    const statusFilter = screen.getByLabelText('상태 필터');
    fireEvent.change(statusFilter, { target: { value: 'completed' } });
    
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Project 2')).not.toBeInTheDocument();
  });

  test('searches evaluations by project name', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('Test Project 2')).toBeInTheDocument();
    });
    
    // Search for specific project
    const searchInput = screen.getByPlaceholderText('프로젝트 검색...');
    fireEvent.change(searchInput, { target: { value: 'Project 1' } });
    
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Project 2')).not.toBeInTheDocument();
  });

  test('opens evaluation details modal', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Click on evaluation to view details
    fireEvent.click(screen.getByText('Test Project 1'));
    
    await waitFor(() => {
      expect(screen.getByText('평가 상세 정보')).toBeInTheDocument();
      expect(screen.getByText('Quality: 8')).toBeInTheDocument();
      expect(screen.getByText('Performance: 9')).toBeInTheDocument();
    });
  });

  test('handles evaluation deletion', async () => {
    setupFetchMock(mockEvaluations);
    global.confirm.mockReturnValue(true);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Mock successful deletion
    setupFetchMock({ message: 'Evaluation deleted successfully' });
    
    // Click delete button
    const deleteButtons = screen.getAllByText('삭제');
    fireEvent.click(deleteButtons[0]);
    
    expect(global.confirm).toHaveBeenCalledWith(
      '정말로 이 평가를 삭제하시겠습니까?'
    );
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations/eval-1', 'DELETE');
    });
  });

  test('handles evaluation export', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Mock export response
    setupFetchMock({ export_url: '/api/exports/evaluation-eval-1.pdf' });
    
    // Click export button
    const exportButtons = screen.getAllByText('내보내기');
    fireEvent.click(exportButtons[0]);
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations/eval-1/export', 'GET');
    });
  });

  test('handles bulk operations', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Select multiple evaluations
    const checkboxes = screen.getAllByRole('checkbox', { name: /선택/ });
    fireEvent.click(checkboxes[0]);
    fireEvent.click(checkboxes[1]);
    
    // Mock bulk export response
    setupFetchMock({ export_url: '/api/exports/bulk-evaluations.zip' });
    
    // Click bulk export
    fireEvent.click(screen.getByText('선택 항목 내보내기'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations/bulk-export', 'POST');
    });
  });

  test('handles evaluation status update', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 2')).toBeInTheDocument();
    });
    
    // Mock status update response
    setupFetchMock({ message: 'Status updated successfully' });
    
    // Change status from draft to completed
    const statusSelects = screen.getAllByLabelText('상태 변경');
    fireEvent.change(statusSelects[1], { target: { value: 'completed' } });
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations/eval-2', 'PUT');
    });
  });

  test('displays score statistics', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Click statistics button
    fireEvent.click(screen.getByText('통계 보기'));
    
    await waitFor(() => {
      expect(screen.getByText('평가 통계')).toBeInTheDocument();
      expect(screen.getByText('평균 점수')).toBeInTheDocument();
      expect(screen.getByText('완료율')).toBeInTheDocument();
    });
  });

  test('handles date range filtering', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Set date range
    const startDateInput = screen.getByLabelText('시작 날짜');
    const endDateInput = screen.getByLabelText('종료 날짜');
    
    fireEvent.change(startDateInput, { target: { value: '2025-01-01' } });
    fireEvent.change(endDateInput, { target: { value: '2025-01-01' } });
    
    // Apply filter
    fireEvent.click(screen.getByText('필터 적용'));
    
    // Should show only evaluations within date range
    expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Project 2')).not.toBeInTheDocument();
  });

  test('handles evaluation assignment', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Mock evaluator list
    const mockEvaluators = [
      { id: 'user-3', name: 'New Evaluator', role: 'Evaluator' }
    ];
    setupFetchMock(mockEvaluators);
    
    // Click reassign button
    const reassignButtons = screen.getAllByText('재배정');
    fireEvent.click(reassignButtons[0]);
    
    await waitFor(() => {
      expect(screen.getByText('평가자 재배정')).toBeInTheDocument();
      expectAuthenticatedApiCall('/api/users', 'GET');
    });
    
    // Select new evaluator
    const evaluatorSelect = screen.getByLabelText('새 평가자');
    fireEvent.change(evaluatorSelect, { target: { value: 'user-3' } });
    
    // Mock assignment response
    setupFetchMock({ message: 'Evaluator assigned successfully' });
    
    // Confirm assignment
    fireEvent.click(screen.getByText('배정 확인'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations/eval-1/assign', 'PUT');
    });
  });

  test('handles error states gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('평가 목록을 불러올 수 없습니다')).toBeInTheDocument();
    });
  });

  test('handles pagination', async () => {
    // Create array of 50 evaluations for pagination testing
    const manyEvaluations = Array.from({ length: 50 }, (_, i) => ({
      ...mockEvaluations[0],
      _id: `eval-${i + 1}`,
      project_name: `Test Project ${i + 1}`
    }));
    
    setupFetchMock({
      evaluations: manyEvaluations.slice(0, 20),
      total: 50,
      page: 1,
      pages: 3
    });
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
      expect(screen.getByText('1 / 3 페이지')).toBeInTheDocument();
    });
    
    // Go to next page
    fireEvent.click(screen.getByText('다음'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations?page=2', 'GET');
    });
  });

  test('handles sorting', async () => {
    setupFetchMock(mockEvaluations);
    
    renderWithProviders(<EvaluationManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Project 1')).toBeInTheDocument();
    });
    
    // Sort by date
    const sortSelect = screen.getByLabelText('정렬 기준');
    fireEvent.change(sortSelect, { target: { value: 'created_at_desc' } });
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/evaluations?sort=created_at_desc', 'GET');
    });
  });
});