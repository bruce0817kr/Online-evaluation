import React, { useEffect, useState } from 'react';
import { useNotifications } from './NotificationProvider';

const ToastNotification = () => {
  const { notifications } = useNotifications();
  const [toastQueue, setToastQueue] = useState([]);

  // 새로운 알림을 토스트로 표시
  useEffect(() => {
    const recentNotifications = notifications
      .filter(notification => {
        const now = new Date();
        const notificationTime = new Date(notification.timestamp);
        const diffInSeconds = (now - notificationTime) / 1000;
        
        // 최근 5초 이내의 중요한 알림만 토스트로 표시
        return diffInSeconds <= 5 && 
               ['urgent', 'high'].includes(notification.priority) &&
               notification.type !== 'connection_established';
      });

    if (recentNotifications.length > 0) {
      const newToasts = recentNotifications.map(notification => ({
        ...notification,
        toastId: `toast-${notification.id}`,
        showTime: 5000 // 5초간 표시
      }));

      setToastQueue(prev => [...prev, ...newToasts].slice(-3)); // 최대 3개까지
    }
  }, [notifications]);

  // 토스트 자동 제거
  useEffect(() => {
    toastQueue.forEach(toast => {
      const timer = setTimeout(() => {
        setToastQueue(prev => prev.filter(t => t.toastId !== toast.toastId));
      }, toast.showTime);

      return () => clearTimeout(timer);
    });
  }, [toastQueue]);

  const removeToast = (toastId) => {
    setToastQueue(prev => prev.filter(t => t.toastId !== toastId));
  };

  const getToastStyles = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500 border-red-600';
      case 'high':
        return 'bg-orange-500 border-orange-600';
      case 'medium':
        return 'bg-blue-500 border-blue-600';
      default:
        return 'bg-gray-500 border-gray-600';
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
      default: return '🔔';
    }
  };

  if (toastQueue.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toastQueue.map((toast, index) => (
        <div
          key={toast.toastId}
          className={`
            transform transition-all duration-300 ease-in-out
            ${index === 0 ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
            max-w-sm w-full text-white rounded-lg shadow-lg border-l-4 p-4
            ${getToastStyles(toast.priority)}
          `}
          style={{
            animation: 'slideInRight 0.3s ease-out'
          }}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <span className="text-lg">{getTypeIcon(toast.type)}</span>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium">
                {toast.title || '새 알림'}
              </p>
              <p className="text-sm opacity-90 mt-1">
                {toast.message}
              </p>
            </div>
            <div className="flex-shrink-0 ml-2">
              <button
                onClick={() => removeToast(toast.toastId)}
                className="text-white hover:text-gray-200 transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      ))}
      
      <style jsx>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default ToastNotification;