import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import notificationsApi, { NOTIFICATION_STATUS, notificationUtils } from '../../api/notificationsApi';

/**
 * Компонент выпадающего списка уведомлений (мини-версия)
 */
const NotificationDropdown = ({ isOpen, onClose, onOpenCenter, className = '' }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  // Загрузка последних уведомлений
  const loadRecentNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await notificationsApi.getNotifications({
        page: 1,
        per_page: 5, // Показываем только последние 5
        status: null // Все статусы
      });
      
      setNotifications(response.notifications || []);
      setUnreadCount(response.unread_count || 0);
    } catch (err) {
      console.error('Error loading recent notifications:', err);
      setError('Не удалось загрузить уведомления');
    } finally {
      setLoading(false);
    }
  };

  // Загружаем при открытии
  useEffect(() => {
    if (isOpen) {
      loadRecentNotifications();
    }
  }, [isOpen]);

  // Закрытие при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  // Отметить как прочитанное
  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationsApi.markAsRead(notificationId);
      setNotifications(prev => 
        prev.map(n => 
          n.id === notificationId 
            ? { ...n, status: NOTIFICATION_STATUS.READ, is_read: true }
            : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        ref={dropdownRef}
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -10, scale: 0.95 }}
        className={`absolute top-full right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 ${className}`}
      >
        {/* Заголовок */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">
            Уведомления
            {unreadCount > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs font-medium px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <i className="fas fa-times text-sm"></i>
          </button>
        </div>

        {/* Содержимое */}
        <div className="max-h-96 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-sm text-gray-600">Загрузка...</span>
            </div>
          ) : error ? (
            <div className="p-4 text-center text-red-600 text-sm">
              <i className="fas fa-exclamation-triangle mb-2"></i>
              <p>{error}</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <i className="fas fa-bell-slash text-2xl mb-2"></i>
              <p className="text-sm">Нет уведомлений</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {notifications.map((notification) => (
                <NotificationDropdownItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={handleMarkAsRead}
                />
              ))}
            </div>
          )}
        </div>

        {/* Футер */}
        {notifications.length > 0 && (
          <div className="p-3 border-t border-gray-200 bg-gray-50">
            <button
              onClick={() => {
                onOpenCenter();
                onClose();
              }}
              className="w-full text-center text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Показать все уведомления
            </button>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * Компонент элемента уведомления в выпадающем списке
 */
const NotificationDropdownItem = ({ notification, onMarkAsRead }) => {
  const isUnread = notification.status === NOTIFICATION_STATUS.UNREAD;
  const typeIcon = notificationUtils.getTypeIcon(notification.notification_type);
  const priorityColor = notificationUtils.getPriorityColor(notification.priority);
  const formattedDate = notificationUtils.formatDate(notification.created_at);

  const handleClick = () => {
    if (isUnread) {
      onMarkAsRead(notification.id);
    }
    
    // Если есть ссылка на действие, переходим по ней
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`p-3 hover:bg-gray-50 cursor-pointer transition-colors duration-200 ${
        isUnread ? 'bg-blue-50 border-l-2 border-l-blue-500' : ''
      }`}
    >
      <div className="flex items-start space-x-3">
        {/* Иконка типа */}
        <div className={`flex-shrink-0 mt-1 ${priorityColor}`}>
          <i className={`${typeIcon} text-sm`}></i>
        </div>

        {/* Содержимое */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h4 className={`text-sm font-medium text-gray-900 truncate ${isUnread ? 'font-semibold' : ''}`}>
                {notification.title}
              </h4>
              <p className="text-xs text-gray-600 line-clamp-2 mt-1">
                {notification.message}
              </p>
              <div className="flex items-center space-x-2 mt-2">
                <span className="text-xs text-gray-500">{formattedDate}</span>
                {notification.priority !== 'normal' && (
                  <span className={`px-1.5 py-0.5 rounded text-xs font-medium text-white ${
                    notification.priority === 'urgent' ? 'bg-red-500' :
                    notification.priority === 'high' ? 'bg-orange-500' :
                    'bg-gray-400'
                  }`}>
                    {notification.priority === 'urgent' ? 'Срочно' :
                     notification.priority === 'high' ? 'Важно' : 'Низкий'}
                  </span>
                )}
              </div>
            </div>

            {/* Индикатор непрочитанного */}
            {isUnread && (
              <div className="flex-shrink-0 ml-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationDropdown;


