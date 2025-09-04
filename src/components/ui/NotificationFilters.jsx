import React from 'react';
import { NOTIFICATION_TYPES, NOTIFICATION_PRIORITY, notificationUtils } from '../../api/notificationsApi';

/**
 * Компонент фильтров для уведомлений
 */
const NotificationFilters = ({ filters, onFilterChange, className = '' }) => {
  const handleFilterChange = (key, value) => {
    onFilterChange({
      ...filters,
      [key]: value === '' ? null : value,
      page: 1 // Сбрасываем страницу при изменении фильтров
    });
  };

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      {/* Фильтр по типу */}
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">
          Тип:
        </label>
        <select
          value={filters.notification_type || ''}
          onChange={(e) => handleFilterChange('notification_type', e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Все типы</option>
          {Object.entries(NOTIFICATION_TYPES).map(([key, value]) => (
            <option key={value} value={value}>
              {notificationUtils.getTypeText(value)}
            </option>
          ))}
        </select>
      </div>

      {/* Фильтр по приоритету */}
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">
          Приоритет:
        </label>
        <select
          value={filters.priority || ''}
          onChange={(e) => handleFilterChange('priority', e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Все приоритеты</option>
          <option value={NOTIFICATION_PRIORITY.LOW}>Низкий</option>
          <option value={NOTIFICATION_PRIORITY.NORMAL}>Обычный</option>
          <option value={NOTIFICATION_PRIORITY.HIGH}>Высокий</option>
          <option value={NOTIFICATION_PRIORITY.URGENT}>Срочный</option>
        </select>
      </div>

      {/* Количество элементов на странице */}
      <div className="flex items-center space-x-2">
        <label className="text-sm font-medium text-gray-700">
          Показывать:
        </label>
        <select
          value={filters.per_page || 20}
          onChange={(e) => handleFilterChange('per_page', parseInt(e.target.value))}
          className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value={10}>10</option>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </div>

      {/* Включать истекшие */}
      <div className="flex items-center space-x-2">
        <label className="flex items-center space-x-1 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={filters.include_expired || false}
            onChange={(e) => handleFilterChange('include_expired', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span>Включать истекшие</span>
        </label>
      </div>

      {/* Кнопка сброса фильтров */}
      {(filters.notification_type || filters.priority || filters.include_expired) && (
        <button
          onClick={() => onFilterChange({
            ...filters,
            notification_type: null,
            priority: null,
            include_expired: false,
            page: 1
          })}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Сбросить фильтры
        </button>
      )}
    </div>
  );
};

export default NotificationFilters;


