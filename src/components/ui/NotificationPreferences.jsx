import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import notificationsApi from '../../api/notificationsApi';

/**
 * Компонент настроек уведомлений
 */
const NotificationPreferences = ({ onClose, className = '' }) => {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Загрузка текущих настроек
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await notificationsApi.getPreferences();
      setPreferences(data);
    } catch (err) {
      console.error('Error loading preferences:', err);
      setError('Не удалось загрузить настройки');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!preferences) return;

    try {
      setSaving(true);
      setError(null);
      
      await notificationsApi.updatePreferences(preferences);
      setSuccess(true);
      
      // Скрыть сообщение об успехе через 3 секунды
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError('Не удалось сохранить настройки');
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key) => {
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleTimeChange = (key, value) => {
    // Валидация времени
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    if (value === '' || timeRegex.test(value)) {
      setPreferences(prev => ({
        ...prev,
        [key]: value || null
      }));
    }
  };

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600">Загрузка настроек...</span>
        </div>
      </div>
    );
  }

  if (error && !preferences) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">
            <i className="fas fa-exclamation-triangle text-2xl"></i>
          </div>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadPreferences}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`p-6 ${className}`}
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Настройки уведомлений
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <i className="fas fa-times"></i>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border-l-4 border-red-400 text-red-700">
          {error}
        </div>
      )}

      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-4 bg-green-50 border-l-4 border-green-400 text-green-700"
        >
          Настройки успешно сохранены!
        </motion.div>
      )}

      <div className="space-y-6">
        {/* Типы уведомлений */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">
            Типы уведомлений
          </h4>
          <div className="space-y-3">
            {[
              { key: 'system_notifications', label: 'Системные уведомления', description: 'Важные системные сообщения' },
              { key: 'assignment_notifications', label: 'Уведомления о заданиях', description: 'Новые задания и изменения' },
              { key: 'grade_notifications', label: 'Уведомления об оценках', description: 'Новые оценки и комментарии' },
              { key: 'deadline_notifications', label: 'Уведомления о дедлайнах', description: 'Приближающиеся сроки сдачи' },
              { key: 'reminder_notifications', label: 'Напоминания', description: 'Персональные напоминания' },
              { key: 'feedback_notifications', label: 'Уведомления об обратной связи', description: 'Отзывы преподавателей' },
              { key: 'schedule_notifications', label: 'Уведомления о расписании', description: 'Изменения в расписании' },
              { key: 'announcement_notifications', label: 'Объявления', description: 'Важные объявления курса' }
            ].map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">
                    {label}
                  </label>
                  <p className="text-xs text-gray-500">{description}</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences?.[key] || false}
                    onChange={() => handleToggle(key)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Каналы доставки */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">
            Каналы доставки
          </h4>
          <div className="space-y-3">
            {[
              { key: 'in_app_enabled', label: 'В приложении', description: 'Показывать уведомления в интерфейсе' },
              { key: 'email_enabled', label: 'Email', description: 'Отправлять на электронную почту' },
              { key: 'push_enabled', label: 'Push-уведомления', description: 'Браузерные push-уведомления' }
            ].map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700">
                    {label}
                  </label>
                  <p className="text-xs text-gray-500">{description}</p>
                </div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences?.[key] || false}
                    onChange={() => handleToggle(key)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Тихие часы */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 mb-3">
            Тихие часы
          </h4>
          <p className="text-xs text-gray-500 mb-3">
            В это время уведомления не будут отправляться (кроме срочных)
          </p>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700">С:</label>
              <input
                type="time"
                value={preferences?.quiet_hours_start || ''}
                onChange={(e) => handleTimeChange('quiet_hours_start', e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-700">До:</label>
              <input
                type="time"
                value={preferences?.quiet_hours_end || ''}
                onChange={(e) => handleTimeChange('quiet_hours_end', e.target.value)}
                className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            {(preferences?.quiet_hours_start || preferences?.quiet_hours_end) && (
              <button
                onClick={() => {
                  setPreferences(prev => ({
                    ...prev,
                    quiet_hours_start: null,
                    quiet_hours_end: null
                  }));
                }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Очистить
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Кнопки действий */}
      <div className="flex items-center justify-end space-x-3 mt-8 pt-6 border-t border-gray-200">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
        >
          Отмена
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <i className="fas fa-spinner fa-spin mr-2"></i>
              Сохранение...
            </>
          ) : (
            'Сохранить'
          )}
        </button>
      </div>
    </motion.div>
  );
};

export default NotificationPreferences;


