import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { notificationUtils, NOTIFICATION_STATUS } from '../../api/notificationsApi';

/**
 * Компонент отдельного уведомления
 */
const NotificationItem = ({ 
  notification, 
  selected, 
  onSelect, 
  onAction,
  className = '' 
}) => {
  const [actionLoading, setActionLoading] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const handleAction = async (action) => {
    setActionLoading(action);
    try {
      await onAction(action);
    } finally {
      setActionLoading(null);
    }
  };

  const handleClick = (e) => {
    // Если кликнули не по чекбоксу или кнопкам действий
    if (!e.target.closest('input') && !e.target.closest('button')) {
      setExpanded(!expanded);
      
      // Если уведомление непрочитанное, отмечаем как прочитанное
      if (notification.status === NOTIFICATION_STATUS.UNREAD) {
        handleAction('mark_read');
      }
    }
  };

  const isUnread = notification.status === NOTIFICATION_STATUS.UNREAD;
  const isArchived = notification.status === NOTIFICATION_STATUS.ARCHIVED;
  const typeIcon = notificationUtils.getTypeIcon(notification.notification_type);
  const priorityColor = notificationUtils.getPriorityColor(notification.priority);
  const typeText = notificationUtils.getTypeText(notification.notification_type);
  const formattedDate = notificationUtils.formatDate(notification.created_at);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`
        relative p-4 hover:bg-gray-50 cursor-pointer transition-colors duration-200
        ${isUnread ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''}
        ${isArchived ? 'opacity-75' : ''}
        ${selected ? 'bg-blue-100' : ''}
        ${className}
      `}
      onClick={handleClick}
    >
      <div className="flex items-start space-x-3">
        {/* Чекбокс для выбора */}
        <div className="flex-shrink-0 pt-1">
          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => onSelect(e.target.checked)}
            onClick={(e) => e.stopPropagation()}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
        </div>

        {/* Иконка типа */}
        <div className={`flex-shrink-0 pt-1 ${priorityColor}`}>
          <i className={`${typeIcon} text-lg`}></i>
        </div>

        {/* Основное содержимое */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              {/* Заголовок */}
              <h4 className={`text-sm font-medium text-gray-900 truncate ${isUnread ? 'font-semibold' : ''}`}>
                {notification.title}
              </h4>
              
              {/* Метаинформация */}
              <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                <span className="bg-gray-100 px-2 py-1 rounded-full">
                  {typeText}
                </span>
                <span>{formattedDate}</span>
                {notification.priority !== 'normal' && (
                  <span className={`px-2 py-1 rounded-full text-white text-xs font-medium ${
                    notification.priority === 'urgent' ? 'bg-red-500' :
                    notification.priority === 'high' ? 'bg-orange-500' :
                    'bg-gray-400'
                  }`}>
                    {notification.priority === 'urgent' ? 'Срочно' :
                     notification.priority === 'high' ? 'Важно' : 'Низкий'}
                  </span>
                )}
                {isUnread && (
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                )}
              </div>
              
              {/* Краткое сообщение */}
              <p className={`mt-2 text-sm text-gray-600 ${expanded ? '' : 'line-clamp-2'}`}>
                {notification.message}
              </p>
              
              {/* Развернутая информация */}
              {expanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 space-y-2"
                >
                  {/* Дополнительные метаданные */}
                  {notification.metadata && Object.keys(notification.metadata).length > 0 && (
                    <div className="p-3 bg-gray-100 rounded-lg">
                      <h5 className="text-xs font-medium text-gray-700 mb-2">Дополнительная информация:</h5>
                      <div className="space-y-1 text-xs text-gray-600">
                        {Object.entries(notification.metadata).map(([key, value]) => (
                          <div key={key} className="flex justify-between">
                            <span className="font-medium">{key}:</span>
                            <span>{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Ссылка на действие */}
                  {notification.action_url && (
                    <div>
                      <a
                        href={notification.action_url}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Перейти к действию
                        <i className="fas fa-external-link-alt ml-1 text-xs"></i>
                      </a>
                    </div>
                  )}
                  
                  {/* Временные метки */}
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Создано: {new Date(notification.created_at).toLocaleString('ru-RU')}</div>
                    {notification.read_at && (
                      <div>Прочитано: {new Date(notification.read_at).toLocaleString('ru-RU')}</div>
                    )}
                    {notification.archived_at && (
                      <div>Архивировано: {new Date(notification.archived_at).toLocaleString('ru-RU')}</div>
                    )}
                    {notification.expires_at && (
                      <div className={notification.is_expired ? 'text-red-500' : ''}>
                        Истекает: {new Date(notification.expires_at).toLocaleString('ru-RU')}
                        {notification.is_expired && ' (истекло)'}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </div>

            {/* Действия */}
            <div className="flex-shrink-0 ml-4">
              <div className="flex items-center space-x-1">
                {/* Кнопка развернуть/свернуть */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpanded(!expanded);
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title={expanded ? "Свернуть" : "Развернуть"}
                >
                  <i className={`fas fa-chevron-${expanded ? 'up' : 'down'} text-xs`}></i>
                </button>

                {/* Отметить как прочитанное/непрочитанное */}
                {!isArchived && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAction(isUnread ? 'mark_read' : 'mark_unread');
                    }}
                    disabled={actionLoading === 'mark_read' || actionLoading === 'mark_unread'}
                    className="p-1 text-gray-400 hover:text-blue-600 rounded disabled:opacity-50"
                    title={isUnread ? "Отметить как прочитанное" : "Отметить как непрочитанное"}
                  >
                    {actionLoading === 'mark_read' || actionLoading === 'mark_unread' ? (
                      <i className="fas fa-spinner fa-spin text-xs"></i>
                    ) : (
                      <i className={`fas ${isUnread ? 'fa-eye' : 'fa-eye-slash'} text-xs`}></i>
                    )}
                  </button>
                )}

                {/* Архивировать */}
                {!isArchived && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAction('archive');
                    }}
                    disabled={actionLoading === 'archive'}
                    className="p-1 text-gray-400 hover:text-orange-600 rounded disabled:opacity-50"
                    title="Архивировать"
                  >
                    {actionLoading === 'archive' ? (
                      <i className="fas fa-spinner fa-spin text-xs"></i>
                    ) : (
                      <i className="fas fa-archive text-xs"></i>
                    )}
                  </button>
                )}

                {/* Удалить */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm('Вы уверены, что хотите удалить это уведомление?')) {
                      handleAction('delete');
                    }
                  }}
                  disabled={actionLoading === 'delete'}
                  className="p-1 text-gray-400 hover:text-red-600 rounded disabled:opacity-50"
                  title="Удалить"
                >
                  {actionLoading === 'delete' ? (
                    <i className="fas fa-spinner fa-spin text-xs"></i>
                  ) : (
                    <i className="fas fa-trash text-xs"></i>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default NotificationItem;


