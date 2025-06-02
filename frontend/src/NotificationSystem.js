// 실시간 알림 시스템
import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const connectWebSocket = () => {
    if (!user.id) return;

    try {
      const wsUrl = `ws://localhost:8080/ws/${user.id}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('🔗 WebSocket 연결됨');
        setIsConnected(true);
        setConnectionStatus('connected');
        
        // 연결 성공 시 ping을 보내서 연결 확인
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleNotification(message);
        } catch (error) {
          console.error('메시지 파싱 오류:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('❌ WebSocket 연결 끊어짐');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // 5초 후 재연결 시도
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket 오류:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      setConnectionStatus('error');
    }
  };

  const handleNotification = (message) => {
    switch (message.type) {
      case 'connection_established':
        addNotification({
          type: 'info',
          title: '알림 연결됨',
          message: message.message,
          duration: 3000
        });
        break;

      case 'assignment_update':
        addNotification({
          type: 'info',
          title: message.title,
          message: message.message,
          duration: 8000,
          data: message.data
        });
        break;

      case 'evaluation_complete':
        addNotification({
          type: 'success',
          title: message.title,
          message: message.message,
          duration: 6000,
          data: message.data
        });
        break;

      case 'deadline_reminder':
        addNotification({
          type: 'warning',
          title: message.title,
          message: message.message,
          duration: 10000,
          data: message.data
        });
        break;

      case 'system_maintenance':
        addNotification({
          type: 'error',
          title: message.title,
          message: message.message,
          duration: 15000
        });
        break;

      case 'project_update':
        addNotification({
          type: 'info',
          title: message.title,
          message: message.message,
          duration: 6000,
          data: message.data
        });
        break;

      case 'pong':
        console.log('📡 WebSocket 연결 확인됨');
        break;

      default:
        console.log('알 수 없는 알림 타입:', message.type);
    }
  };

  const addNotification = (notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      ...notification,
      timestamp: new Date().toISOString()
    };

    setNotifications(prev => [newNotification, ...prev]);

    // 자동 제거
    if (notification.duration) {
      setTimeout(() => {
        removeNotification(id);
      }, notification.duration);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  useEffect(() => {
    if (user.id) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [user.id]);

  const value = {
    notifications,
    isConnected,
    connectionStatus,
    addNotification,
    removeNotification,
    clearAllNotifications,
    connectWebSocket
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

// 알림 컴포넌트
export const NotificationCenter = () => {
  const { notifications, removeNotification } = useNotifications();

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.slice(0, 5).map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onRemove={removeNotification}
        />
      ))}
    </div>
  );
};

const NotificationItem = ({ notification, onRemove }) => {
  const getNotificationStyles = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-100';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900 dark:border-yellow-700 dark:text-yellow-100';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-100';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return 'ℹ️';
    }
  };

  return (
    <div className={`
      max-w-sm p-4 border rounded-lg shadow-lg transform transition-all duration-300
      ${getNotificationStyles(notification.type)}
      animate-slide-in-right
    `}>
      <div className="flex items-start">
        <span className="text-lg mr-3 flex-shrink-0">
          {getIcon(notification.type)}
        </span>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm">
            {notification.title}
          </h4>
          <p className="text-sm opacity-90 mt-1">
            {notification.message}
          </p>
          <p className="text-xs opacity-70 mt-2">
            {new Date(notification.timestamp).toLocaleTimeString('ko-KR')}
          </p>
        </div>
        <button
          onClick={() => onRemove(notification.id)}
          className="ml-2 text-lg opacity-70 hover:opacity-100 transition-opacity"
        >
          ×
        </button>
      </div>
    </div>
  );
};
