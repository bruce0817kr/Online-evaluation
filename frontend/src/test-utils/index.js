// Test utilities for React Testing Library
import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Default mock user data
export const mockUser = {
  id: 'test-user-id',
  username: 'testuser',
  role: 'admin',
  email: 'test@example.com',
  company_id: 'test-company-id',
  company_name: 'Test Company'
};

// Mock admin user
export const mockAdminUser = {
  ...mockUser,
  role: 'admin'
};

// Mock manager user
export const mockManagerUser = {
  ...mockUser,
  role: 'secretary',
  username: 'testmanager'
};

// Mock evaluator user
export const mockEvaluatorUser = {
  ...mockUser,
  role: 'evaluator',
  username: 'testevaluator'
};

// Mock user context
const MockUserContext = React.createContext();

export const MockUserProvider = ({ children, user }) => {
  const defaultUser = user || mockUser;
  return (
    <MockUserContext.Provider value={{ user: defaultUser, setUser: jest.fn() }}>
      {children}
    </MockUserContext.Provider>
  );
};

// Mock notification context
const MockNotificationContext = React.createContext();

export const MockNotificationProvider = ({ children, notifications = [] }) => {
  const mockNotificationValue = {
    notifications,
    isConnected: true,
    connectionStatus: 'connected',
    addNotification: jest.fn(),
    markAsRead: jest.fn(),
    markAllAsRead: jest.fn(),
    removeNotification: jest.fn(),
    clearAllNotifications: jest.fn(),
    joinRoom: jest.fn(),
    leaveRoom: jest.fn(),
    sendMessage: jest.fn(),
    connectWebSocket: jest.fn(),
    disconnectWebSocket: jest.fn(),
    unreadCount: notifications.filter(n => !n.read).length
  };

  return (
    <MockNotificationContext.Provider value={mockNotificationValue}>
      {children}
    </MockNotificationContext.Provider>
  );
};

// Simple render function with basic providers
export const renderWithProviders = (
  ui,
  {
    user = mockUser,
    notifications = [],
    initialEntries = ['/'],
    ...renderOptions
  } = {}
) => {
  function Wrapper({ children }) {
    return (
      <BrowserRouter>
        <MockUserProvider user={user}>
          <MockNotificationProvider notifications={notifications}>
            {children}
          </MockNotificationProvider>
        </MockUserProvider>
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Custom render for components that need routing
export const renderWithRouter = (
  ui,
  {
    initialEntries = ['/'],
    ...renderOptions
  } = {}
) => {
  function Wrapper({ children }) {
    return (
      <BrowserRouter>
        {children}
      </BrowserRouter>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock API responses
export const mockApiResponses = {
  templates: [
    {
      _id: 'template-1',
      template_name: 'Test Template 1',
      template_type: 'score',
      criteria: [
        { criterion_name: 'Quality', max_score: 10, score_step: 1 }
      ],
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      _id: 'template-2',
      template_name: 'Test Template 2',
      template_type: 'grade',
      criteria: [
        { criterion_name: 'Performance', max_score: 100, score_step: 5 }
      ],
      created_at: '2025-01-02T00:00:00Z'
    }
  ],
  evaluations: [
    {
      _id: 'eval-1',
      template_id: 'template-1',
      evaluator_id: 'test-user-id',
      project_id: 'project-1',
      scores: { 'Quality': 8 },
      status: 'completed',
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      _id: 'eval-2',
      template_id: 'template-2',
      evaluator_id: 'test-user-id',
      project_id: 'project-2',
      scores: { 'Performance': 85 },
      status: 'draft',
      created_at: '2025-01-02T00:00:00Z'
    }
  ],
  projects: [
    {
      _id: 'project-1',
      project_name: 'Test Project 1',
      company_id: 'test-company-id',
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      _id: 'project-2',
      project_name: 'Test Project 2',
      company_id: 'test-company-id',
      created_at: '2025-01-02T00:00:00Z'
    }
  ],
  companies: [
    {
      _id: 'test-company-id',
      company_name: 'Test Company',
      created_at: '2025-01-01T00:00:00Z'
    }
  ]
};

// Fetch mock setup helper
export const setupFetchMock = (data, options = {}) => {
  const { 
    ok = true, 
    status = 200, 
    delay = 0 
  } = options;

  const mockResponse = {
    ok,
    status,
    json: jest.fn(async () => {
      if (delay) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
      return data;
    }),
    text: jest.fn(async () => JSON.stringify(data)),
    blob: jest.fn(async () => new Blob([JSON.stringify(data)])),
    arrayBuffer: jest.fn(async () => new ArrayBuffer(0)),
    clone: jest.fn(function() { return this; })
  };

  fetch.mockResolvedValue(mockResponse);
  return mockResponse;
};

// Setup fetch error mock
export const setupFetchError = (error = new Error('Network error')) => {
  fetch.mockRejectedValue(error);
  return error;
};

// Clear all mocks helper
export const clearAllMocks = () => {
  jest.clearAllMocks();
  fetch.mockClear();
  if (localStorage.getItem) localStorage.getItem.mockClear();
  if (localStorage.setItem) localStorage.setItem.mockClear();
  if (localStorage.removeItem) localStorage.removeItem.mockClear();
  if (localStorage.clear) localStorage.clear.mockClear();
  if (global.alert) global.alert.mockClear();
  if (global.confirm) global.confirm.mockClear();
};

// Simulate user interactions
export const userInteractions = {
  login: (username = 'testuser', password = 'password123') => {
    localStorage.getItem.mockImplementation((key) => {
      if (key === 'token') return 'mock-jwt-token';
      if (key === 'user') return JSON.stringify(mockUser);
      return null;
    });
  },
  
  logout: () => {
    localStorage.getItem.mockReturnValue(null);
    localStorage.removeItem.mockImplementation(() => {});
  }
};

// Wait for API calls to complete
export const waitForApiCall = (apiUrl, method = 'GET') => {
  return new Promise((resolve) => {
    const checkFetch = () => {
      const calls = fetch.mock.calls;
      const matchingCall = calls.find(call => 
        call[0].includes(apiUrl) && 
        (!call[1] || call[1].method === method)
      );
      
      if (matchingCall) {
        resolve(matchingCall);
      } else {
        setTimeout(checkFetch, 10);
      }
    };
    checkFetch();
  });
};

// Create test data generators
export const createMockTemplate = (overrides = {}) => ({
  _id: `template-${Date.now()}`,
  template_name: 'Mock Template',
  template_type: 'score',
  criteria: [
    { criterion_name: 'Test Criterion', max_score: 10, score_step: 1 }
  ],
  created_at: new Date().toISOString(),
  ...overrides
});

export const createMockEvaluation = (overrides = {}) => ({
  _id: `eval-${Date.now()}`,
  template_id: 'template-1',
  evaluator_id: 'test-user-id',
  project_id: 'project-1',
  scores: { 'Test Criterion': 8 },
  status: 'completed',
  created_at: new Date().toISOString(),
  ...overrides
});

export const createMockProject = (overrides = {}) => ({
  _id: `project-${Date.now()}`,
  project_name: 'Mock Project',
  company_id: 'test-company-id',
  description: 'Test project description',
  created_at: new Date().toISOString(),
  ...overrides
});

// Test assertions helpers
export const expectApiCall = (url, method = 'GET', headers = {}) => {
  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining(url),
    expect.objectContaining({
      method,
      headers: expect.objectContaining(headers)
    })
  );
};

export const expectAuthenticatedApiCall = (url, method = 'GET') => {
  expectApiCall(url, method, {
    'Authorization': 'Bearer mock-jwt-token'
  });
};

// Export everything for easy imports
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';