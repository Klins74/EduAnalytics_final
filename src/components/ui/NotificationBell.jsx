import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import notificationsApi from '../../api/notificationsApi';
import NotificationCenter from './NotificationCenter';
import NotificationDropdown from './NotificationDropdown';

/**
 * Компонент колокольчика уведомлений для навигационной панели
 */
const NotificationBell = ({ className = '' }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [showCenter, setShowCenter] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  // Загрузка количества непрочитанных уведомлений
  const loadUnreadCount = async () => {
    try {
      setLoading(true);
      const response = await notificationsApi.getUnreadCount();
      setUnreadCount(response.unread_count || 0);
    } catch (err) {
      console.error('Error loading unread count:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загружаем при монтировании компонента
  useEffect(() => {
    loadUnreadCount();
  }, []);

  // Периодическое обновление счетчика
  useEffect(() => {
    const interval = setInterval(loadUnreadCount, 30000); // Каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  // Обновляем счетчик при закрытии центра уведомлений
  const handleCenterClose = () => {
    setShowCenter(false);
    loadUnreadCount();
  };

  const handleClick = () => {
    setShowDropdown(!showDropdown);
  };

  const handleOpenCenter = () => {
    setShowCenter(true);
    setShowDropdown(false);
  };

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className={`relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200 ${className}`}
        title="Уведомления"
      >
        {/* Иконка колокольчика */}
        <div className="relative">
          {loading ? (
            <i className="fas fa-spinner fa-spin text-lg"></i>
          ) : (
            <i className="fas fa-bell text-lg"></i>
          )}
          
          {/* Счетчик непрочитанных */}
          <AnimatePresence>
            {unreadCount > 0 && (
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                className="absolute -top-1 -right-1 min-w-[18px] h-[18px] bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center"
              >
                {unreadCount > 99 ? '99+' : unreadCount}
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Индикатор новых уведомлений */}
          {unreadCount > 0 && (
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full opacity-75"
            />
          )}
        </div>
      </button>

      {/* Выпадающий список уведомлений */}
      <NotificationDropdown
        isOpen={showDropdown}
        onClose={() => setShowDropdown(false)}
        onOpenCenter={handleOpenCenter}
      />

      {/* Центр уведомлений */}
      <AnimatePresence>
        {showCenter && (
          <NotificationCenter
            isOpen={showCenter}
            onClose={handleCenterClose}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationBell;
