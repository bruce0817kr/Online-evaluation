import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

const NotificationContext = createContext();

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

const NotificationProvider = ({ children, user }) => {
  const [notifications, setNotifications] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8019';
  const WS_URL = BACKEND_URL.replace('http', 'ws');

  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now() + Math.random(),
      timestamp: new Date(),
      read: false,
      ...notification
    };
    
    setNotifications(prev => [newNotification, ...prev].slice(0, 50)); // 최대 50개 유지
    
    // 브라우저 알림 표시 (권한이 있는 경우)
    if (Notification.permission === 'granted' && notification.priority === 'urgent') {
      new Notification(notification.title || '새 알림', {
        body: notification.message,
        icon: '/favicon.ico',
        tag: newNotification.id
      });
    }
  };

  const markAsRead = (notificationId) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId ? { ...notif, read: true } : notif
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, read: true }))
    );
  };

  const removeNotification = (notificationId) => {
    setNotifications(prev =>
      prev.filter(notif => notif.id !== notificationId)
    );
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  const connectWebSocket = () => {
    if (!user || !user.id) {
      console.warn('사용자 정보가 없어 WebSocket 연결을 시작할 수 없습니다');
      return;
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws/${user.id}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket 연결됨');
        setIsConnected(true);
        setConnectionStatus('connected');
        
        // 하트비트 시작
        startHeartbeat();
        
        // 프로젝트 방 참가 (사용자가 속한 프로젝트가 있다면)
        if (user.projects && user.projects.length > 0) {
          user.projects.forEach(projectId => {
            ws.send(JSON.stringify({
              type: 'join_room',
              room_id: `project:${projectId}`
            }));
          });
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            // 하트비트 응답
            return;
          }
          
          // 알림 추가
          addNotification(data);
          
        } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('❌ WebSocket 연결 종료:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus('disconnected');
        stopHeartbeat();
        
        // 자동 재연결 (5초 후)
        if (event.code !== 1000) { // 정상 종료가 아닌 경우
          setConnectionStatus('reconnecting');
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 WebSocket 재연결 시도');
            connectWebSocket();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket 오류:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      setConnectionStatus('error');
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'User logout');
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    stopHeartbeat();
    setIsConnected(false);
    setConnectionStatus('disconnected');
  };

  const startHeartbeat = () => {
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30초마다 핑
  };

  const stopHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const joinRoom = (roomId) => {
    sendMessage({ type: 'join_room', room_id: roomId });
  };

  const leaveRoom = (roomId) => {
    sendMessage({ type: 'leave_room', room_id: roomId });
  };

  // 브라우저 알림 권한 요청
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return Notification.permission === 'granted';
  };

  useEffect(() => {
    if (user && user.id) {
      // 브라우저 알림 권한 요청
      requestNotificationPermission();
      
      // WebSocket 연결
      connectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [user]);

  // 윈도우 언로드 시 정리
  useEffect(() => {
    const handleBeforeUnload = () => {
      disconnectWebSocket();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  const value = {
    notifications,
    isConnected,
    connectionStatus,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    joinRoom,
    leaveRoom,
    sendMessage,
    connectWebSocket,
    disconnectWebSocket,
    unreadCount: notifications.filter(n => !n.read).length
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider;