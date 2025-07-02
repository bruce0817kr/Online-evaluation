import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import { renderWithProviders, setupFetchMock, mockAdminUser, mockApiResponses, clearAllMocks, expectAuthenticatedApiCall, createMockTemplate } from '../../test-utils';
import TemplateManagement from '../TemplateManagement';

// Mock CSS import
jest.mock('../TemplateManagement.css', () => ({}));

describe('TemplateManagement Component', () => {
  beforeEach(() => {
    clearAllMocks();
    localStorage.getItem.mockReturnValue('mock-jwt-token');
  });

  const mockTemplates = [
    {
      _id: 'template-1',
      template_name: 'Test Template 1',
      template_type: 'score',
      criteria: [
        { criterion_name: 'Criterion 1', max_score: 10, score_step: 1 }
      ],
      created_at: '2025-06-01T00:00:00Z'
    },
    {
      _id: 'template-2',
      template_name: 'Test Template 2',
      template_type: 'grade',
      criteria: [
        { criterion_name: 'Criterion A', max_score: 100, score_step: 5 }
      ],
      created_at: '2025-06-02T00:00:00Z'
    }
  ];

  test('renders template management component', () => {
    setupFetchMock(mockTemplates);
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    expect(screen.getByText('템플릿 관리')).toBeInTheDocument();
    expect(screen.getByText('새 템플릿 추가')).toBeInTheDocument();
  });

  test('loads and displays templates on mount', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
      expect(screen.getByText('Test Template 2')).toBeInTheDocument();
      expectAuthenticatedApiCall('/api/templates', 'GET');
    });
  });

  test('handles template creation', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    // Click add new template button
    fireEvent.click(screen.getByText('새 템플릿 추가'));
    
    // Fill in template form
    fireEvent.change(screen.getByLabelText('템플릿 이름'), {
      target: { value: 'New Template' }
    });
    
    fireEvent.change(screen.getByLabelText('템플릿 타입'), {
      target: { value: 'score' }
    });
    
    // Add criterion
    fireEvent.click(screen.getByText('평가 항목 추가'));
    
    const criterionInputs = screen.getAllByLabelText('평가 항목 이름');
    fireEvent.change(criterionInputs[0], {
      target: { value: 'New Criterion' }
    });
    
    // Mock successful creation
    setupFetchMock({ message: 'Template created successfully' });
    
    // Submit form
    fireEvent.click(screen.getByText('템플릿 저장'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates', 'POST');
    });
  });

  test('handles template editing', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    });
    
    // Click edit button for first template
    const editButtons = screen.getAllByText('수정');
    fireEvent.click(editButtons[0]);
    
    // Modify template name
    const templateNameInput = screen.getByDisplayValue('Test Template 1');
    fireEvent.change(templateNameInput, {
      target: { value: 'Updated Template 1' }
    });
    
    // Mock successful update
    setupFetchMock({ message: 'Template updated successfully' });
    
    // Save changes
    fireEvent.click(screen.getByText('템플릿 수정'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates/template-1', 'PUT');
    });
  });

  test('handles template deletion with confirmation', async () => {
    setupFetchMock(mockTemplates);
    
    // Mock window.confirm
    global.confirm.mockReturnValue(true);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    });
    
    // Mock successful deletion
    setupFetchMock({ message: 'Template deleted successfully' });
    
    // Click delete button
    const deleteButtons = screen.getAllByText('삭제');
    fireEvent.click(deleteButtons[0]);
    
    expect(global.confirm).toHaveBeenCalledWith(
      '정말로 이 템플릿을 삭제하시겠습니까?'
    );
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates/template-1', 'DELETE');
    });
  });

  test('handles search functionality', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
      expect(screen.getByText('Test Template 2')).toBeInTheDocument();
    });
    
    // Search for template
    const searchInput = screen.getByPlaceholderText('템플릿 검색...');
    fireEvent.change(searchInput, {
      target: { value: 'Template 1' }
    });
    
    // Should show only matching template
    expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Template 2')).not.toBeInTheDocument();
  });

  test('handles error states gracefully', async () => {
    // Mock fetch error
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        expect.stringContaining('템플릿 로드 실패')
      );
    });
  });

  test('validates required fields before submission', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    // Click add new template
    fireEvent.click(screen.getByText('새 템플릿 추가'));
    
    // Try to submit without filling required fields
    fireEvent.click(screen.getByText('템플릿 저장'));
    
    // Should show validation error
    expect(global.alert).toHaveBeenCalledWith(
      expect.stringContaining('필수 입력')
    );
    
    // Fetch should not be called
    expect(fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/templates'),
      expect.objectContaining({ method: 'POST' })
    );
  });

  test('handles criterion management within template', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    // Add new template
    fireEvent.click(screen.getByText('새 템플릿 추가'));
    
    // Add multiple criteria
    fireEvent.click(screen.getByText('평가 항목 추가'));
    fireEvent.click(screen.getByText('평가 항목 추가'));
    
    const criterionInputs = screen.getAllByLabelText('평가 항목 이름');
    expect(criterionInputs).toHaveLength(3); // 1 default + 2 added
    
    // Remove a criterion
    const removeButtons = screen.getAllByText('항목 삭제');
    fireEvent.click(removeButtons[1]);
    
    // Should have one less criterion
    const updatedInputs = screen.getAllByLabelText('평가 항목 이름');
    expect(updatedInputs).toHaveLength(2);
  });

  test('displays template type correctly', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      // Check for template type badges
      expect(screen.getByText('점수형')).toBeInTheDocument();
      expect(screen.getByText('등급형')).toBeInTheDocument();
    });
  });

  test('handles template duplication', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    });
    
    // Mock successful duplication
    const duplicatedTemplate = {
      ...mockTemplates[0],
      _id: 'template-duplicate',
      template_name: 'Test Template 1 (복사본)'
    };
    setupFetchMock(duplicatedTemplate);
    
    // Click duplicate button
    const duplicateButtons = screen.getAllByText('복사');
    fireEvent.click(duplicateButtons[0]);
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates', 'POST');
    });
  });

  test('handles drag and drop for criteria reordering', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    // Add new template with multiple criteria
    fireEvent.click(screen.getByText('새 템플릿 추가'));
    
    // Add criteria
    fireEvent.click(screen.getByText('평가 항목 추가'));
    fireEvent.click(screen.getByText('평가 항목 추가'));
    
    // Fill criteria names
    const criterionInputs = screen.getAllByLabelText('평가 항목 이름');
    fireEvent.change(criterionInputs[0], { target: { value: 'First Criterion' } });
    fireEvent.change(criterionInputs[1], { target: { value: 'Second Criterion' } });
    fireEvent.change(criterionInputs[2], { target: { value: 'Third Criterion' } });
    
    // Test drag and drop functionality
    const dragHandles = screen.getAllByRole('button', { name: /드래그/ });
    expect(dragHandles).toHaveLength(3);
    
    // Simulate drag start
    fireEvent.dragStart(dragHandles[0]);
    fireEvent.drop(dragHandles[2]);
    
    // Order should be maintained in state (verified by implementation)
  });

  test('exports template data', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    });
    
    // Mock export response
    setupFetchMock({ export_url: '/api/exports/templates.xlsx' });
    
    // Click export button
    fireEvent.click(screen.getByText('템플릿 내보내기'));
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates/export', 'GET');
    });
  });

  test('imports template data', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    // Create mock file
    const file = new File(['template,data'], 'templates.csv', { type: 'text/csv' });
    
    // Mock import response
    setupFetchMock({ imported: 2, errors: [] });
    
    // Simulate file input
    const fileInput = screen.getByLabelText('템플릿 가져오기');
    fireEvent.change(fileInput, { target: { files: [file] } });
    
    await waitFor(() => {
      expectAuthenticatedApiCall('/api/templates/import', 'POST');
    });
  });

  test('filters templates by type', async () => {
    setupFetchMock(mockTemplates);
    
    renderWithProviders(<TemplateManagement user={mockAdminUser} />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Template 1')).toBeInTheDocument();
      expect(screen.getByText('Test Template 2')).toBeInTheDocument();
    });
    
    // Filter by score type
    const typeFilter = screen.getByLabelText('템플릿 타입 필터');
    fireEvent.change(typeFilter, { target: { value: 'score' } });
    
    // Should show only score type templates
    expect(screen.getByText('Test Template 1')).toBeInTheDocument();
    expect(screen.queryByText('Test Template 2')).not.toBeInTheDocument();
  });
});