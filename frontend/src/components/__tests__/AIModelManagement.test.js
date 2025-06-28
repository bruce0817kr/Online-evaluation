/**
 * Test Suite for AI Model Management Component
 * Unit and integration tests for the React component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import AIModelManagement from '../AIModelManagement';

// Mock fetch API
global.fetch = jest.fn();

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(() => 'mock-token'),
  setItem: jest.fn(),
  clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock environment variable
process.env.REACT_APP_BACKEND_URL = 'http://localhost:8002';

describe('AIModelManagement Component', () => {
  const mockAdminUser = {
    user_id: 'admin1',
    login_id: 'admin',
    name: 'Admin User',
    role: 'admin',
    company_id: 'comp1'
  };

  const mockSecretaryUser = {
    user_id: 'sec1',
    login_id: 'secretary',
    name: 'Secretary User',
    role: 'secretary',
    company_id: 'comp1'
  };

  const mockEvaluatorUser = {
    user_id: 'eval1',
    login_id: 'evaluator',
    name: 'Evaluator User',
    role: 'evaluator',
    company_id: 'comp1'
  };

  const mockModels = [
    {
      model_id: 'gpt-4',
      provider: 'openai',
      model_name: 'gpt-4',
      display_name: 'GPT-4',
      status: 'active',
      cost_per_token: 0.00003,
      max_tokens: 8192,
      context_window: 8192,
      capabilities: ['text-generation', 'analysis'],
      quality_score: 0.95,
      speed_score: 0.7,
      cost_score: 0.3,
      reliability_score: 0.9,
      is_default: true
    },
    {
      model_id: 'claude-3',
      provider: 'anthropic',
      model_name: 'claude-3-opus',
      display_name: 'Claude 3 Opus',
      status: 'active',
      cost_per_token: 0.00005,
      max_tokens: 4096,
      context_window: 200000,
      capabilities: ['text-generation', 'analysis', 'coding'],
      quality_score: 0.98,
      speed_score: 0.6,
      cost_score: 0.2,
      reliability_score: 0.95,
      is_default: false
    }
  ];

  const mockTemplates = [
    {
      name: 'openai-gpt4-evaluation',
      provider: 'openai',
      display_name: 'GPT-4 평가 전문가',
      description: '고품질 평가 작업을 위한 GPT-4 모델',
      capabilities: ['text-generation', 'evaluation', 'analysis', 'korean']
    },
    {
      name: 'budget-efficient',
      provider: 'openai',
      display_name: '경제적 대량 평가',
      description: '비용 효율적인 대량 평가용 모델',
      capabilities: ['text-generation', 'evaluation', 'batch-processing']
    }
  ];

  beforeEach(() => {
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    
    // Default mock responses
    fetch.mockImplementation((url) => {
      if (url.includes('/api/ai-models/available')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockModels)
        });
      }
      if (url.includes('/api/ai-models/templates/list')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ templates: mockTemplates })
        });
      }
      return Promise.resolve({
        ok: false,
        json: () => Promise.resolve({ detail: 'Not found' })
      });
    });
  });

  describe('Access Control', () => {
    test('renders access denied for evaluator users', () => {
      render(<AIModelManagement user={mockEvaluatorUser} />);
      
      expect(screen.getByText('🚫 접근 권한 없음')).toBeInTheDocument();
      expect(screen.getByText(/관리자와 간사만 사용할 수 있습니다/)).toBeInTheDocument();
    });

    test('allows access for admin users', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        expect(screen.getByText('🤖 AI 모델 관리')).toBeInTheDocument();
        expect(screen.queryByText('🚫 접근 권한 없음')).not.toBeInTheDocument();
      });
    });

    test('allows access for secretary users', async () => {
      render(<AIModelManagement user={mockSecretaryUser} />);
      
      await waitFor(() => {
        expect(screen.getByText('🤖 AI 모델 관리')).toBeInTheDocument();
        expect(screen.queryByText('🚫 접근 권한 없음')).not.toBeInTheDocument();
      });
    });
  });

  describe('Tab Navigation', () => {
    test('displays all three tabs', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        expect(screen.getByText('🔧 모델 관리')).toBeInTheDocument();
        expect(screen.getByText('📋 템플릿')).toBeInTheDocument();
        expect(screen.getByText('🧪 연결 테스트')).toBeInTheDocument();
      });
    });

    test('switches between tabs correctly', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Default is manage tab
      await waitFor(() => {
        expect(screen.getByText('➕ 새 모델 생성')).toBeInTheDocument();
      });
      
      // Switch to templates tab
      fireEvent.click(screen.getByText('📋 템플릿'));
      expect(screen.getByText('📋 모델 템플릿')).toBeInTheDocument();
      
      // Switch to test tab
      fireEvent.click(screen.getByText('🧪 연결 테스트'));
      expect(screen.getByText('🧪 모델 연결 테스트')).toBeInTheDocument();
    });
  });

  describe('Model Management Tab', () => {
    test('displays model cards correctly', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        // Check GPT-4 card
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText(/OPENAI - gpt-4/)).toBeInTheDocument();
        expect(screen.getByText('기본 모델')).toBeInTheDocument();
        
        // Check Claude 3 card
        expect(screen.getByText('Claude 3 Opus')).toBeInTheDocument();
        expect(screen.getByText(/ANTHROPIC - claude-3-opus/)).toBeInTheDocument();
      });
    });

    test('opens create modal when clicking new model button', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('➕ 새 모델 생성'));
      });
      
      expect(screen.getByText('➕ 새 AI 모델 생성')).toBeInTheDocument();
      expect(screen.getByLabelText('모델 ID *')).toBeInTheDocument();
    });

    test('creates new model successfully', async () => {
      const user = userEvent.setup();
      
      fetch.mockImplementationOnce((url) => {
        if (url.includes('/api/ai-models/create')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              model: {
                model_id: 'new-model',
                provider: 'novita',
                display_name: 'New Test Model'
              }
            })
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockModels)
        });
      });
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Open create modal
      await waitFor(() => {
        fireEvent.click(screen.getByText('➕ 새 모델 생성'));
      });
      
      // Fill form
      await user.type(screen.getByLabelText('모델 ID *'), 'new-model');
      await user.selectOptions(screen.getByLabelText('제공업체 *'), 'novita');
      await user.type(screen.getByLabelText('모델명 *'), 'deepseek-r1');
      await user.type(screen.getByLabelText('표시명 *'), 'New Test Model');
      
      // Submit
      fireEvent.click(screen.getByText('모델 생성'));
      
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/ai-models/create'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json'
            })
          })
        );
      });
    });

    test('opens edit modal when clicking edit button', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        const editButtons = screen.getAllByText('✏️ 수정');
        fireEvent.click(editButtons[0]);
      });
      
      expect(screen.getByText(/✏️ 모델 편집:/)).toBeInTheDocument();
    });

    test('deletes model with confirmation', async () => {
      window.confirm = jest.fn(() => true);
      
      fetch.mockImplementationOnce((url) => {
        if (url.includes('/api/ai-models/') && url.includes('DELETE')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({})
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockModels)
        });
      });
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        // Find non-default model's delete button
        const deleteButtons = screen.getAllByText('🗑️ 삭제');
        const enabledDeleteButton = deleteButtons.find(btn => !btn.disabled);
        fireEvent.click(enabledDeleteButton);
      });
      
      expect(window.confirm).toHaveBeenCalledWith('정말로 이 모델을 삭제하시겠습니까?');
    });

    test('prevents deleting default models', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        // Find GPT-4 card (default model)
        const gpt4Card = screen.getByText('GPT-4').closest('.model-management-card');
        const deleteButton = within(gpt4Card).getByText('🗑️ 삭제');
        
        expect(deleteButton).toBeDisabled();
      });
    });
  });

  describe('Templates Tab', () => {
    test('displays template cards', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Switch to templates tab
      fireEvent.click(screen.getByText('📋 템플릿'));
      
      await waitFor(() => {
        expect(screen.getByText('GPT-4 평가 전문가')).toBeInTheDocument();
        expect(screen.getByText('경제적 대량 평가')).toBeInTheDocument();
      });
    });

    test('creates model from template', async () => {
      fetch.mockImplementationOnce((url) => {
        if (url.includes('/api/ai-models/templates/') && url.includes('/create')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              model: {
                model_id: 'template-created',
                display_name: 'Template Created Model'
              }
            })
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ templates: mockTemplates })
        });
      });
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Switch to templates tab
      fireEvent.click(screen.getByText('📋 템플릿'));
      
      await waitFor(() => {
        const createButtons = screen.getAllByText('🚀 템플릿으로 생성');
        fireEvent.click(createButtons[0]);
      });
      
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/ai-models/templates/'),
          expect.objectContaining({
            method: 'POST'
          })
        );
      });
    });
  });

  describe('Connection Test Tab', () => {
    test('displays only active models for testing', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Switch to test tab
      fireEvent.click(screen.getByText('🧪 연결 테스트'));
      
      await waitFor(() => {
        // Both models are active, so both should appear
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText('Claude 3 Opus')).toBeInTheDocument();
      });
    });

    test('performs connection test', async () => {
      fetch.mockImplementationOnce((url) => {
        if (url.includes('/test-connection')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              is_healthy: true,
              health_score: 0.95,
              avg_response_time: 1.2,
              successful_tests: 4,
              total_tests: 4
            })
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockModels)
        });
      });
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Switch to test tab
      fireEvent.click(screen.getByText('🧪 연결 테스트'));
      
      await waitFor(() => {
        const testButtons = screen.getAllByText('🔗 연결 테스트');
        fireEvent.click(testButtons[0]);
      });
      
      await waitFor(() => {
        expect(screen.getByText('✅')).toBeInTheDocument();
        expect(screen.getByText('연결 성공')).toBeInTheDocument();
        expect(screen.getByText(/건강도: 95%/)).toBeInTheDocument();
      });
    });

    test('shows error state for failed connection', async () => {
      fetch.mockImplementationOnce((url) => {
        if (url.includes('/test-connection')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              is_healthy: false,
              health_score: 0.2,
              successful_tests: 1,
              total_tests: 4
            })
          });
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockModels)
        });
      });
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      // Switch to test tab
      fireEvent.click(screen.getByText('🧪 연결 테스트'));
      
      await waitFor(() => {
        const testButtons = screen.getAllByText('🔗 연결 테스트');
        fireEvent.click(testButtons[0]);
      });
      
      await waitFor(() => {
        expect(screen.getByText('❌')).toBeInTheDocument();
        expect(screen.getByText('연결 불안정')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message on API failure', async () => {
      fetch.mockImplementationOnce(() => 
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'API Error' })
        })
      );
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        expect(screen.getByText(/모델 목록을 불러오는데 실패했습니다/)).toBeInTheDocument();
      });
    });

    test('closes error message when clicking X', async () => {
      fetch.mockImplementationOnce(() => 
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'API Error' })
        })
      );
      
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        const errorMessage = screen.getByText(/모델 목록을 불러오는데 실패했습니다/);
        expect(errorMessage).toBeInTheDocument();
        
        const closeButton = screen.getByText('✕');
        fireEvent.click(closeButton);
        
        expect(errorMessage).not.toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    test('disables buttons during loading', async () => {
      render(<AIModelManagement user={mockAdminUser} />);
      
      await waitFor(() => {
        const refreshButton = screen.getByText('🔄 새로고침');
        
        // Initially not disabled
        expect(refreshButton).not.toBeDisabled();
        
        // Click to trigger loading
        fireEvent.click(refreshButton);
        
        // Should be disabled during loading
        expect(refreshButton).toBeDisabled();
      });
    });
  });
});