import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  REMINDER_INTERVALS, 
  NOTIFICATION_CHANNELS,
  reminderUtils 
} from '../../api/remindersApi';

/**
 * Компонент карточки настройки напоминания
 */
const ReminderSettingCard = ({ setting, onUpdate, saving, className = '' }) => {
  const [localSetting, setLocalSetting] = useState(setting);
  const [expanded, setExpanded] = useState(false);

  const typeName = reminderUtils.getReminderTypeName(setting.reminder_type);
  const typeDescription = reminderUtils.getReminderTypeDescription(setting.reminder_type);
  const typeIcon = reminderUtils.getReminderTypeIcon(setting.reminder_type);

  // Обработка изменений настроек
  const handleChange = (field, value) => {
    const updatedSetting = { ...localSetting, [field]: value };
    setLocalSetting(updatedSetting);
    
    // Автоматически сохраняем изменения
    onUpdate({
      is_enabled: updatedSetting.is_enabled,
      interval_before: updatedSetting.interval_before,
      notification_channel: updatedSetting.notification_channel
    });
  };

  const handleToggle = () => {
    handleChange('is_enabled', !localSetting.is_enabled);
  };

  return (
    <motion.div
      layout
      className={`bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow duration-200 ${className}`}
    >
      {/* Заголовок карточки */}
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* Иконка типа */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              localSetting.is_enabled ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'
            }`}>
              <i className={`${typeIcon} text-lg`}></i>
            </div>
            
            {/* Название и описание */}
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-gray-900 truncate">
                {typeName}
              </h3>
              <p className="text-xs text-gray-500 truncate">
                {typeDescription}
              </p>
            </div>
          </div>

          {/* Переключатель и статус */}
          <div className="flex items-center space-x-3">
            {/* Краткая информация */}
            {localSetting.is_enabled && (
              <div className="text-xs text-gray-500 text-right hidden sm:block">
                <div>{reminderUtils.getIntervalName(localSetting.interval_before)}</div>
                <div className="flex items-center">
                  <i className={`${reminderUtils.getChannelIcon(localSetting.notification_channel)} mr-1`}></i>
                  {reminderUtils.getChannelName(localSetting.notification_channel)}
                </div>
              </div>
            )}

            {/* Переключатель */}
            <label 
              className="relative inline-flex items-center cursor-pointer"
              onClick={(e) => e.stopPropagation()}
            >
              <input
                type="checkbox"
                checked={localSetting.is_enabled}
                onChange={handleToggle}
                disabled={saving}
                className="sr-only"
              />
              <div className={`w-11 h-6 rounded-full transition-colors duration-200 ${
                localSetting.is_enabled ? 'bg-blue-600' : 'bg-gray-200'
              } ${saving ? 'opacity-50' : ''}`}>
                <div className={`w-5 h-5 bg-white rounded-full shadow transform transition-transform duration-200 ${
                  localSetting.is_enabled ? 'translate-x-5' : 'translate-x-0'
                } mt-0.5 ml-0.5`}></div>
              </div>
            </label>

            {/* Индикатор развертывания */}
            <i className={`fas fa-chevron-down text-gray-400 transition-transform duration-200 ${
              expanded ? 'transform rotate-180' : ''
            }`}></i>
          </div>
        </div>
      </div>

      {/* Развернутые настройки */}
      {expanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="border-t border-gray-100 bg-gray-50"
        >
          <div className="p-4 space-y-4">
            {/* Интервал напоминания (только для некоторых типов) */}
            {(setting.reminder_type === 'schedule_upcoming' || setting.reminder_type === 'assignment_due') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Напомнить за:
                </label>
                <select
                  value={localSetting.interval_before}
                  onChange={(e) => handleChange('interval_before', e.target.value)}
                  disabled={!localSetting.is_enabled || saving}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  {Object.entries(REMINDER_INTERVALS).map(([key, value]) => (
                    <option key={value} value={value}>
                      {reminderUtils.getIntervalName(value)}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Канал уведомления */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Способ уведомления:
              </label>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(NOTIFICATION_CHANNELS).map(([key, value]) => (
                  <label
                    key={value}
                    className={`relative flex items-center p-3 border rounded-md cursor-pointer transition-colors duration-200 ${
                      localSetting.notification_channel === value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    } ${(!localSetting.is_enabled || saving) ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <input
                      type="radio"
                      name={`channel-${setting.reminder_type}`}
                      value={value}
                      checked={localSetting.notification_channel === value}
                      onChange={(e) => handleChange('notification_channel', e.target.value)}
                      disabled={!localSetting.is_enabled || saving}
                      className="sr-only"
                    />
                    <div className="flex items-center space-x-2">
                      <i className={`${reminderUtils.getChannelIcon(value)} ${reminderUtils.getChannelColor(value)}`}></i>
                      <span className="text-sm font-medium text-gray-900">
                        {reminderUtils.getChannelName(value)}
                      </span>
                    </div>
                    {localSetting.notification_channel === value && (
                      <div className="absolute top-2 right-2">
                        <i className="fas fa-check text-blue-500 text-xs"></i>
                      </div>
                    )}
                  </label>
                ))}
              </div>
            </div>

            {/* Дополнительная информация */}
            <div className="text-xs text-gray-500 bg-white p-3 rounded-md">
              <div className="flex items-start space-x-2">
                <i className="fas fa-info-circle mt-0.5"></i>
                <div>
                  <p className="font-medium mb-1">О этом типе напоминаний:</p>
                  <p>{typeDescription}</p>
                  {setting.reminder_type === 'schedule_upcoming' && (
                    <p className="mt-1">
                      Напоминания отправляются только для занятий, которые начинаются в рабочие дни.
                    </p>
                  )}
                  {setting.reminder_type === 'assignment_due' && (
                    <p className="mt-1">
                      Напоминания отправляются для всех активных заданий с установленным дедлайном.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Статус сохранения */}
            {saving && (
              <div className="flex items-center justify-center py-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span className="ml-2 text-sm text-gray-600">Сохранение...</span>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default ReminderSettingCard;


