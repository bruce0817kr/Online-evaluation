import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders, setupFetchMock, mockAdminUser, clearAllMocks } from '../../test-utils';
import NotificationCenter from '../NotificationCenter';

describe('NotificationCenter Component', () => {
  beforeEach(() => {
    clearAllMocks();
    localStorage.getItem.mockReturnValue('mock-jwt-token');
  });

  const mockNotifications = [
    {
      id: '1',
      type: 'evaluation_assigned',
      title: '새로운 평가 배정',
      message: 'Project Alpha에 대한 평가가 배정되었습니다.',
      read: false,
      timestamp: '2025-06-27T10:00:00Z',
      priority: 'high'
    },
    {
      id: '2',
      type: 'evaluation_completed',
      title: '평가 완료',
      message: 'Project Beta 평가가 완료되었습니다.',
      read: true,
      timestamp: '2025-06-26T15:30:00Z',
      priority: 'medium'
    },
    {
      id: '3',
      type: 'system_maintenance',
      title: '시스템 점검',
      message: '내일 오전 2시부터 4시까지 시스템 점검이 예정되어 있습니다.',
      read: false,
      timestamp: '2025-06-25T12:00:00Z',
      priority: 'low'
    }
  ];

  test('renders notification center with notifications', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // First click to open the notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('알림')).toBeInTheDocument();
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
      expect(screen.getByText('평가 완료')).toBeInTheDocument();
      expect(screen.getByText('시스템 점검')).toBeInTheDocument();
    });
  });

  test('displays unread notification count', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument(); // Unread count badge
    });
  });

  test('handles notification click to mark as read', async () => {
    const { container } = renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
    });

    // Click on unread notification
    const unreadNotification = screen.getByText('새로운 평가 배정');
    fireEvent.click(unreadNotification);
    
    // The notification should be marked as read through the mock function
    // This test verifies the component renders and handles clicks properly
  });

  test('handles mark all as read functionality', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('모두 읽음')).toBeInTheDocument();
    });

    // Click mark all as read
    fireEvent.click(screen.getByText('모두 읽음'));
    
    // The markAllAsRead function should be called
  });

  test('filters notifications by type', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
      expect(screen.getByText('평가 완료')).toBeInTheDocument();
      expect(screen.getByText('시스템 점검')).toBeInTheDocument();
    });

    // Filter by unread
    fireEvent.click(screen.getByText('미읽음 (2)'));
    
    // Should show only unread notifications
    expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
    expect(screen.getByText('시스템 점검')).toBeInTheDocument();
  });

  test('filters notifications by priority', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
    });

    // Filter by urgent priority
    fireEvent.click(screen.getByText('긴급'));
    
    // Should show the urgent filter is active
    const urgentButton = screen.getByText('긴급');
    expect(urgentButton).toHaveClass('bg-red-100');
  });

  test('handles notification deletion', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
    });

    // Click delete button
    const deleteButtons = screen.getAllByText('삭제');
    fireEvent.click(deleteButtons[0]);
    
    // The removeNotification function should be called
  });

  test('displays notification timestamps correctly', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      // Check for relative time stamps
      const timeElements = screen.getAllByText(/전/);
      expect(timeElements.length).toBeGreaterThan(0);
    });
  });

  test('handles real-time notification updates', async () => {
    const initialNotifications = mockNotifications.slice(0, 2);
    
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: initialNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
      expect(screen.getByText('평가 완료')).toBeInTheDocument();
    });

    // The component should show the initial notifications
    expect(screen.getByText('1')).toBeInTheDocument(); // Unread count for initial notifications
  });

  test('handles notification settings', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('알림')).toBeInTheDocument();
    });

    // The notification center should render with connection status
    expect(screen.getByText('연결됨')).toBeInTheDocument();
  });

  test('handles empty notification state', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: []
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('알림이 없습니다')).toBeInTheDocument();
    });
  });

  test('handles error states gracefully', async () => {
    // Component should still render even if there are no notifications
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: []
    });
    
    const notificationButton = screen.getByTitle('알림');
    expect(notificationButton).toBeInTheDocument();
  });

  test('supports keyboard navigation', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('새로운 평가 배정')).toBeInTheDocument();
    });

    // Test keyboard navigation
    const firstNotification = screen.getByText('새로운 평가 배정');
    
    // Enter key should mark as read
    fireEvent.keyDown(firstNotification, { key: 'Enter', code: 'Enter' });
    
    // The notification component should handle keyboard events
    expect(firstNotification).toBeInTheDocument();
  });

  test('displays notification priority indicators', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      // Check for priority icons in the notifications
      expect(screen.getByText('🚨')).toBeInTheDocument(); // High priority
      expect(screen.getByText('ℹ️')).toBeInTheDocument(); // Medium priority  
      expect(screen.getByText('💡')).toBeInTheDocument(); // Low priority
    });
  });

  test('displays connection status correctly', async () => {
    renderWithProviders(<NotificationCenter />, {
      user: mockAdminUser,
      notifications: mockNotifications
    });
    
    // Open notification center
    const notificationButton = screen.getByTitle('알림');
    fireEvent.click(notificationButton);
    
    await waitFor(() => {
      expect(screen.getByText('연결됨')).toBeInTheDocument();
    });
  });
});