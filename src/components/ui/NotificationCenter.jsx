import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import notificationsApi, { NOTIFICATION_STATUS, notificationUtils } from '../../api/notificationsApi';
import NotificationItem from './NotificationItem';
import NotificationFilters from './NotificationFilters';
import NotificationPreferences from './NotificationPreferences';

/**
 * Центр уведомлений - основной компонент для управления in-app уведомлениями
 */
const NotificationCenter = ({ isOpen, onClose, className = '' }) => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [stats, setStats] = useState(null);
  const [selectedTab, setSelectedTab] = useState('all');
  const [showPreferences, setShowPreferences] = useState(false);
  const [selectedNotifications, setSelectedNotifications] = useState([]);
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  
  // Параметры запроса
  const [filters, setFilters] = useState({
    status: null,
    notification_type: null,
    page: 1,
    per_page: 20
  });
  
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 20,
    has_next: false,
    has_prev: false
  });

  const centerRef = useRef(null);

  // Загрузка уведомлений
  const loadNotifications = async (newFilters = {}) => {
    try {
      setLoading(true);
      setError(null);
      
      const requestFilters = { ...filters, ...newFilters };
      
      // Устанавливаем статус на основе выбранной вкладки
      if (selectedTab === 'unread') {
        requestFilters.status = NOTIFICATION_STATUS.UNREAD;
      } else if (selectedTab === 'archived') {
        requestFilters.status = NOTIFICATION_STATUS.ARCHIVED;
      } else {
        requestFilters.status = null;
      }

      const response = await notificationsApi.getNotifications(requestFilters);
      
      setNotifications(response.notifications || []);
      setPagination({
        total: response.total,
        page: response.page,
        per_page: response.per_page,
        has_next: response.has_next,
        has_prev: response.has_prev
      });
      setUnreadCount(response.unread_count || 0);

    } catch (err) {
      console.error('Error loading notifications:', err);
      setError('Не удалось загрузить уведомления');
    } finally {
      setLoading(false);
    }
  };

  // Загрузка статистики
  const loadStats = async () => {
    try {
      const statsData = await notificationsApi.getStats();
      setStats(statsData);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  // Загрузка количества непрочитанных
  const loadUnreadCount = async () => {
    try {
      const response = await notificationsApi.getUnreadCount();
      setUnreadCount(response.unread_count || 0);
    } catch (err) {
      console.error('Error loading unread count:', err);
    }
  };

  // Эффекты
  useEffect(() => {
    if (isOpen) {
      loadNotifications();
      loadStats();
    }
  }, [isOpen, selectedTab]);

  useEffect(() => {
    // Обновляем количество непрочитанных каждые 30 секунд
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Обработчики событий
  const handleTabChange = (tab) => {
    setSelectedTab(tab);
    setFilters({ ...filters, page: 1 });
    setSelectedNotifications([]);
  };

  const handleFilterChange = (newFilters) => {
    setFilters({ ...filters, ...newFilters, page: 1 });
    loadNotifications(newFilters);
  };

  const handlePageChange = (newPage) => {
    const newFilters = { ...filters, page: newPage };
    setFilters(newFilters);
    loadNotifications(newFilters);
  };

  const handleNotificationAction = async (notificationId, action) => {
    try {
      let updatedNotification;
      
      switch (action) {
        case 'mark_read':
          updatedNotification = await notificationsApi.markAsRead(notificationId);
          break;
        case 'archive':
          updatedNotification = await notificationsApi.archiveNotification(notificationId);
          break;
        case 'delete':
          await notificationsApi.deleteNotification(notificationId);
          setNotifications(prev => prev.filter(n => n.id !== notificationId));
          loadUnreadCount();
          return;
      }

      if (updatedNotification) {
        setNotifications(prev => 
          prev.map(n => n.id === notificationId ? updatedNotification : n)
        );
        loadUnreadCount();
      }
    } catch (err) {
      console.error('Error performing notification action:', err);
      setError('Не удалось выполнить действие');
    }
  };

  const handleSelectNotification = (notificationId, selected) => {
    if (selected) {
      setSelectedNotifications(prev => [...prev, notificationId]);
    } else {
      setSelectedNotifications(prev => prev.filter(id => id !== notificationId));
    }
  };

  const handleSelectAll = () => {
    if (selectedNotifications.length === notifications.length) {
      setSelectedNotifications([]);
    } else {
      setSelectedNotifications(notifications.map(n => n.id));
    }
  };

  const handleBulkAction = async (action) => {
    if (selectedNotifications.length === 0) return;

    try {
      setBulkActionLoading(true);
      await notificationsApi.bulkAction({
        notification_ids: selectedNotifications,
        action
      });

      setSelectedNotifications([]);
      loadNotifications();
      loadUnreadCount();
    } catch (err) {
      console.error('Error performing bulk action:', err);
      setError('Не удалось выполнить массовое действие');
    } finally {
      setBulkActionLoading(false);
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      loadNotifications();
      loadUnreadCount();
    } catch (err) {
      console.error('Error marking all as read:', err);
      setError('Не удалось отметить все как прочитанные');
    }
  };

  // Закрытие при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (centerRef.current && !centerRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
    >
      <motion.div
        ref={centerRef}
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className={`bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col ${className}`}
      >
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Центр уведомлений
            </h2>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-sm font-medium px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={handleMarkAllAsRead}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Прочитать все
            </button>
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              title="Настройки"
            >
              <i className="fas fa-cog"></i>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>

        {/* Вкладки */}
        <div className="flex border-b border-gray-200 px-6">
          <button
            onClick={() => handleTabChange('all')}
            className={`py-3 px-4 text-sm font-medium border-b-2 ${
              selectedTab === 'all'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Все ({stats?.total_notifications || 0})
          </button>
          <button
            onClick={() => handleTabChange('unread')}
            className={`py-3 px-4 text-sm font-medium border-b-2 ${
              selectedTab === 'unread'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Непрочитанные ({unreadCount})
          </button>
          <button
            onClick={() => handleTabChange('archived')}
            className={`py-3 px-4 text-sm font-medium border-b-2 ${
              selectedTab === 'archived'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Архив ({stats?.archived_count || 0})
          </button>
        </div>

        {/* Настройки уведомлений */}
        <AnimatePresence>
          {showPreferences && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-b border-gray-200"
            >
              <NotificationPreferences onClose={() => setShowPreferences(false)} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Фильтры и массовые действия */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <NotificationFilters
              filters={filters}
              onFilterChange={handleFilterChange}
            />
            
            {selectedNotifications.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  Выбrano: {selectedNotifications.length}
                </span>
                <button
                  onClick={() => handleBulkAction('mark_read')}
                  disabled={bulkActionLoading}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
                >
                  Прочитать
                </button>
                <button
                  onClick={() => handleBulkAction('archive')}
                  disabled={bulkActionLoading}
                  className="text-sm text-orange-600 hover:text-orange-800 font-medium disabled:opacity-50"
                >
                  Архивировать
                </button>
                <button
                  onClick={() => handleBulkAction('delete')}
                  disabled={bulkActionLoading}
                  className="text-sm text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
                >
                  Удалить
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Список уведомлений */}
        <div className="flex-1 overflow-y-auto">
          {error && (
            <div className="p-4 bg-red-50 border-l-4 border-red-400">
              <div className="text-red-700">{error}</div>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <i className="fas fa-bell-slash text-4xl mb-4"></i>
              <p className="text-lg font-medium">Нет уведомлений</p>
              <p className="text-sm">
                {selectedTab === 'unread' 
                  ? 'Все уведомления прочитаны' 
                  : selectedTab === 'archived'
                  ? 'Нет архивированных уведомлений'
                  : 'У вас пока нет уведомлений'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {notifications.length > 0 && (
                <div className="p-4 bg-gray-50 border-b border-gray-200">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={selectedNotifications.length === notifications.length}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600">Выбрать все</span>
                  </label>
                </div>
              )}
              
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  selected={selectedNotifications.includes(notification.id)}
                  onSelect={(selected) => handleSelectNotification(notification.id, selected)}
                  onAction={(action) => handleNotificationAction(notification.id, action)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Пагинация */}
        {notifications.length > 0 && (pagination.has_prev || pagination.has_next) && (
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Показано {notifications.length} из {pagination.total}
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={!pagination.has_prev}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Назад
                </button>
                <span className="px-3 py-1 text-sm text-gray-600">
                  Страница {pagination.page}
                </span>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={!pagination.has_next}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Вперед
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
};

export default NotificationCenter;


