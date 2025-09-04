import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import remindersApi, { 
  REMINDER_TYPES, 
  REMINDER_INTERVALS, 
  NOTIFICATION_CHANNELS,
  reminderUtils 
} from '../../api/remindersApi';
import ReminderSettingCard from './ReminderSettingCard';
import UpcomingReminders from './UpcomingReminders';
import ReminderTestPanel from './ReminderTestPanel';

/**
 * Основной компонент настроек напоминаний
 */
const ReminderSettings = ({ className = '' }) => {
  const [settings, setSettings] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('settings');

  // Загрузка данных
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [settingsData, statsData] = await Promise.all([
        remindersApi.getReminderSettings(),
        remindersApi.getReminderStats()
      ]);
      
      setSettings(settingsData);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading reminder data:', err);
      setError('Не удалось загрузить настройки напоминаний');
    } finally {
      setLoading(false);
    }
  };

  // Обновление отдельной настройки
  const handleSettingUpdate = async (reminderType, updatedSetting) => {
    try {
      setSaving(true);
      setError(null);
      
      const newSetting = await remindersApi.updateReminderSetting(reminderType, updatedSetting);
      
      // Обновляем локальное состояние
      setSettings(prev => 
        prev.map(setting => 
          setting.reminder_type === reminderType ? newSetting : setting
        )
      );
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      
      // Обновляем статистику
      const newStats = await remindersApi.getReminderStats();
      setStats(newStats);
      
    } catch (err) {
      console.error('Error updating reminder setting:', err);
      setError('Не удалось сохранить настройку');
    } finally {
      setSaving(false);
    }
  };

  // Массовое обновление всех настроек
  const handleBulkUpdate = async (preferences) => {
    try {
      setSaving(true);
      setError(null);
      
      const updatedSettings = await remindersApi.updateReminderPreferences(preferences);
      setSettings(updatedSettings);
      
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      
      // Обновляем статистику
      const newStats = await remindersApi.getReminderStats();
      setStats(newStats);
      
    } catch (err) {
      console.error('Error updating reminder preferences:', err);
      setError('Не удалось сохранить настройки');
    } finally {
      setSaving(false);
    }
  };

  // Быстрые действия
  const handleQuickAction = async (action) => {
    const preferences = {};
    
    // Формируем настройки на основе действия
    Object.values(REMINDER_TYPES).forEach(type => {
      const typeKey = type.replace('_', '_');
      
      switch (action) {
        case 'enable_all':
          preferences[`${typeKey}_enabled`] = true;
          break;
        case 'disable_all':
          preferences[`${typeKey}_enabled`] = false;
          break;
        case 'email_all':
          preferences[`${typeKey}_enabled`] = true;
          preferences[`${typeKey}_channel`] = NOTIFICATION_CHANNELS.EMAIL;
          break;
        case 'in_app_all':
          preferences[`${typeKey}_enabled`] = true;
          preferences[`${typeKey}_channel`] = NOTIFICATION_CHANNELS.IN_APP;
          break;
      }
      
      // Устанавливаем интервалы по умолчанию
      if (action !== 'disable_all') {
        if (type === REMINDER_TYPES.SCHEDULE_UPCOMING) {
          preferences[`${typeKey}_interval`] = REMINDER_INTERVALS.HOUR_1;
        } else if (type === REMINDER_TYPES.ASSIGNMENT_DUE) {
          preferences[`${typeKey}_interval`] = REMINDER_INTERVALS.DAY_1;
        }
      }
    });
    
    await handleBulkUpdate(preferences);
  };

  if (loading) {
    return (
      <div className={`p-6 ${className}`}>
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-600">Загрузка настроек...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Заголовок */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Настройки напоминаний
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Управляйте уведомлениями о расписании и дедлайнах
            </p>
          </div>
          
          {stats && (
            <div className="flex items-center space-x-4 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.enabled_settings}
                </div>
                <div className="text-gray-500">Включено</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {stats.upcoming_reminders}
                </div>
                <div className="text-gray-500">Предстоящих</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Сообщения об ошибках и успехе */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-6 mt-4 p-4 bg-red-50 border-l-4 border-red-400 text-red-700"
          >
            <div className="flex items-center">
              <i className="fas fa-exclamation-triangle mr-2"></i>
              {error}
            </div>
          </motion.div>
        )}
        
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mx-6 mt-4 p-4 bg-green-50 border-l-4 border-green-400 text-green-700"
          >
            <div className="flex items-center">
              <i className="fas fa-check mr-2"></i>
              Настройки успешно сохранены!
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Вкладки */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('settings')}
          className={`py-3 px-6 text-sm font-medium border-b-2 ${
            activeTab === 'settings'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <i className="fas fa-cog mr-2"></i>
          Настройки
        </button>
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`py-3 px-6 text-sm font-medium border-b-2 ${
            activeTab === 'upcoming'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <i className="fas fa-clock mr-2"></i>
          Предстоящие ({stats?.upcoming_reminders || 0})
        </button>
        <button
          onClick={() => setActiveTab('test')}
          className={`py-3 px-6 text-sm font-medium border-b-2 ${
            activeTab === 'test'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <i className="fas fa-flask mr-2"></i>
          Тест
        </button>
      </div>

      {/* Содержимое вкладок */}
      <div className="p-6">
        {activeTab === 'settings' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Быстрые действия */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Быстрые действия
              </h3>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => handleQuickAction('enable_all')}
                  disabled={saving}
                  className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 disabled:opacity-50"
                >
                  <i className="fas fa-check mr-1"></i>
                  Включить все
                </button>
                <button
                  onClick={() => handleQuickAction('disable_all')}
                  disabled={saving}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 disabled:opacity-50"
                >
                  <i className="fas fa-times mr-1"></i>
                  Отключить все
                </button>
                <button
                  onClick={() => handleQuickAction('email_all')}
                  disabled={saving}
                  className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 disabled:opacity-50"
                >
                  <i className="fas fa-envelope mr-1"></i>
                  Email для всех
                </button>
                <button
                  onClick={() => handleQuickAction('in_app_all')}
                  disabled={saving}
                  className="px-3 py-1 text-sm bg-orange-100 text-orange-700 rounded-md hover:bg-orange-200 disabled:opacity-50"
                >
                  <i className="fas fa-bell mr-1"></i>
                  В приложении для всех
                </button>
              </div>
            </div>

            {/* Карточки настроек */}
            <div className="grid gap-4">
              {Object.values(REMINDER_TYPES).map(reminderType => {
                const setting = settings.find(s => s.reminder_type === reminderType) || {
                  reminder_type: reminderType,
                  is_enabled: false,
                  interval_before: REMINDER_INTERVALS.HOUR_1,
                  notification_channel: NOTIFICATION_CHANNELS.EMAIL
                };

                return (
                  <ReminderSettingCard
                    key={reminderType}
                    setting={setting}
                    onUpdate={(updatedSetting) => handleSettingUpdate(reminderType, updatedSetting)}
                    saving={saving}
                  />
                );
              })}
            </div>
          </motion.div>
        )}

        {activeTab === 'upcoming' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <UpcomingReminders />
          </motion.div>
        )}

        {activeTab === 'test' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <ReminderTestPanel />
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default ReminderSettings;


