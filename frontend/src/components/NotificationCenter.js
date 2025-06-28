import React, { useState } from 'react';
import { useNotifications } from './NotificationProvider';

const NotificationCenter = () => {
  const {
    notifications,
    isConnected,
    connectionStatus,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    unreadCount
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('all'); // all, unread, urgent

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return '#10B981'; // green
      case 'connecting': 
      case 'reconnecting': return '#F59E0B'; // yellow
      case 'error': return '#EF4444'; // red
      default: return '#6B7280'; // gray
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return '연결됨';
      case 'connecting': return '연결 중';
      case 'reconnecting': return '재연결 중';
      case 'error': return '연결 오류';
      default: return '연결 안됨';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'urgent': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return 'ℹ️';
      case 'low': return '💡';
      default: return '📢';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'assignment_update': return '📋';
      case 'evaluation_complete': return '✅';
      case 'deadline_reminder': return '⏰';
      case 'project_update': return '📁';
      case 'system_maintenance': return '🔧';
      case 'admin_broadcast': return '📢';
      case 'connection_established': return '🔗';
      default: return '🔔';
    }
  };

  const formatTimestamp = (timestamp) => {
    const now = new Date();
    const notificationTime = new Date(timestamp);
    const diffInMinutes = Math.floor((now - notificationTime) / (1000 * 60));

    if (diffInMinutes < 1) return '방금 전';
    if (diffInMinutes < 60) return `${diffInMinutes}분 전`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}시간 전`;
    return notificationTime.toLocaleDateString('ko-KR');
  };

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') return !notification.read;
    if (filter === 'urgent') return notification.priority === 'urgent';
    return true;
  });

  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
  };

  return (
    <div className="relative">
      {/* 알림 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
        title="알림"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-5 5V11a7.002 7.002 0 00-13.984-.216A7.028 7.028 0 001 11v6h5m9 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        
        {/* 미읽음 알림 배지 */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* 알림 패널 */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* 헤더 */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">알림</h3>
              <div className="flex items-center space-x-2">
                {/* 연결 상태 표시 */}
                <div
                  className="flex items-center space-x-1 text-sm"
                  title={`실시간 알림 ${getStatusText()}`}
                >
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: getStatusColor() }}
                  />
                  <span className="text-gray-500">{getStatusText()}</span>
                </div>
                
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* 필터 버튼들 */}
            <div className="flex space-x-2 mt-3">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 text-sm rounded-full ${
                  filter === 'all'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                전체
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-3 py-1 text-sm rounded-full ${
                  filter === 'unread'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                미읽음 ({unreadCount})
              </button>
              <button
                onClick={() => setFilter('urgent')}
                className={`px-3 py-1 text-sm rounded-full ${
                  filter === 'urgent'
                    ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                긴급
              </button>
            </div>

            {/* 액션 버튼들 */}
            {notifications.length > 0 && (
              <div className="flex space-x-2 mt-3">
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  모두 읽음
                </button>
                <button
                  onClick={clearAllNotifications}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  모두 삭제
                </button>
              </div>
            )}
          </div>

          {/* 알림 목록 */}
          <div className="max-h-96 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                {filter === 'unread' ? '새로운 알림이 없습니다' : '알림이 없습니다'}
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {filteredNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        <span className="text-xl">
                          {getTypeIcon(notification.type)}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {notification.title || '알림'}
                          </p>
                          <div className="flex items-center space-x-1">
                            <span className="text-lg">
                              {getPriorityIcon(notification.priority)}
                            </span>
                            {!notification.read && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full" />
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {notification.message}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <p className="text-xs text-gray-500">
                            {formatTimestamp(notification.timestamp)}
                          </p>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeNotification(notification.id);
                            }}
                            className="text-xs text-gray-400 hover:text-red-600"
                          >
                            삭제
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;