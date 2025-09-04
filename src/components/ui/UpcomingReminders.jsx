import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import remindersApi, { reminderUtils } from '../../api/remindersApi';

/**
 * Компонент для отображения предстоящих напоминаний
 */
const UpcomingReminders = ({ className = '' }) => {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [daysAhead, setDaysAhead] = useState(7);
  const [groupBy, setGroupBy] = useState('date'); // 'date', 'type', 'channel'

  // Загрузка предстоящих напоминаний
  const loadUpcomingReminders = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await remindersApi.getUpcomingReminders(daysAhead);
      setReminders(data);
    } catch (err) {
      console.error('Error loading upcoming reminders:', err);
      setError('Не удалось загрузить предстоящие напоминания');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUpcomingReminders();
  }, [daysAhead]);

  // Группировка напоминаний
  const getGroupedReminders = () => {
    if (reminders.length === 0) return {};

    const groups = {};

    reminders.forEach(reminder => {
      let groupKey;
      
      switch (groupBy) {
        case 'date':
          const date = new Date(reminder.send_at);
          groupKey = date.toLocaleDateString('ru-RU', { 
            weekday: 'long',
            day: 'numeric',
            month: 'long'
          });
          break;
        case 'type':
          groupKey = reminderUtils.getReminderTypeName(reminder.reminder_type);
          break;
        case 'channel':
          groupKey = reminderUtils.getChannelName(reminder.notification_channel);
          break;
        default:
          groupKey = 'Все';
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(reminder);
    });

    // Сортируем группы
    const sortedGroups = {};
    Object.keys(groups)
      .sort((a, b) => {
        if (groupBy === 'date') {
          // Сортируем по дате
          const dateA = new Date(groups[a][0].send_at);
          const dateB = new Date(groups[b][0].send_at);
          return dateA - dateB;
        }
        return a.localeCompare(b, 'ru');
      })
      .forEach(key => {
        // Сортируем напоминания внутри группы по времени
        sortedGroups[key] = groups[key].sort((a, b) => 
          new Date(a.send_at) - new Date(b.send_at)
        );
      });

    return sortedGroups;
  };

  const groupedReminders = getGroupedReminders();

  if (loading) {
    return (
      <div className={`${className}`}>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-gray-600">Загрузка напоминаний...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <div className="text-center py-8">
          <div className="text-red-600 mb-4">
            <i className="fas fa-exclamation-triangle text-2xl"></i>
          </div>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadUpcomingReminders}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {/* Фильтры и настройки */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">
              Период:
            </label>
            <select
              value={daysAhead}
              onChange={(e) => setDaysAhead(parseInt(e.target.value))}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={1}>1 день</option>
              <option value={3}>3 дня</option>
              <option value={7}>7 дней</option>
              <option value={14}>14 дней</option>
              <option value={30}>30 дней</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">
              Группировать по:
            </label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-3 py-1 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="date">Дате</option>
              <option value="type">Типу</option>
              <option value="channel">Каналу</option>
            </select>
          </div>
        </div>

        <div className="text-sm text-gray-500">
          Всего напоминаний: {reminders.length}
        </div>
      </div>

      {/* Список напоминаний */}
      {Object.keys(groupedReminders).length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <i className="fas fa-calendar-times text-4xl"></i>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Нет предстоящих напоминаний
          </h3>
          <p className="text-gray-500">
            На ближайшие {daysAhead} {daysAhead === 1 ? 'день' : daysAhead <= 4 ? 'дня' : 'дней'} напоминания не запланированы
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedReminders).map(([groupName, groupReminders]) => (
            <motion.div
              key={groupName}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden"
            >
              {/* Заголовок группы */}
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 flex items-center">
                  {groupBy === 'date' && <i className="fas fa-calendar mr-2"></i>}
                  {groupBy === 'type' && <i className="fas fa-tag mr-2"></i>}
                  {groupBy === 'channel' && <i className="fas fa-paper-plane mr-2"></i>}
                  {groupName}
                  <span className="ml-2 bg-gray-200 text-gray-600 text-xs font-medium px-2 py-1 rounded-full">
                    {groupReminders.length}
                  </span>
                </h3>
              </div>

              {/* Напоминания в группе */}
              <div className="divide-y divide-gray-100">
                {groupReminders.map((reminder) => (
                  <ReminderItem key={reminder.id} reminder={reminder} />
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Компонент отдельного напоминания
 */
const ReminderItem = ({ reminder }) => {
  const typeName = reminderUtils.getReminderTypeName(reminder.reminder_type);
  const typeIcon = reminderUtils.getReminderTypeIcon(reminder.reminder_type);
  const channelIcon = reminderUtils.getChannelIcon(reminder.notification_channel);
  const channelColor = reminderUtils.getChannelColor(reminder.notification_channel);
  const formattedDate = reminderUtils.formatReminderDate(reminder.send_at);
  const status = reminderUtils.getReminderStatus(reminder);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-4 hover:bg-gray-50 transition-colors duration-200"
    >
      <div className="flex items-start space-x-3">
        {/* Иконка типа */}
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
          <i className={`${typeIcon} text-sm`}></i>
        </div>

        {/* Основное содержимое */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-900 truncate">
                {reminder.title}
              </h4>
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {reminder.message}
              </p>
              
              <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                <span className="flex items-center">
                  <i className="fas fa-clock mr-1"></i>
                  {formattedDate}
                </span>
                <span className="flex items-center">
                  <i className={`${channelIcon} mr-1 ${channelColor}`}></i>
                  {reminderUtils.getChannelName(reminder.notification_channel)}
                </span>
                <span className="bg-gray-100 px-2 py-1 rounded-full">
                  {typeName}
                </span>
              </div>
            </div>

            {/* Статус */}
            <div className="flex-shrink-0 ml-4">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${status.bgColor} ${status.color}`}>
                <i className={`${status.icon} mr-1`}></i>
                {status.status}
              </span>
            </div>
          </div>

          {/* Дополнительная информация */}
          {(reminder.schedule_id || reminder.assignment_id) && (
            <div className="mt-3 text-xs text-gray-500">
              {reminder.schedule_id && (
                <span className="inline-flex items-center mr-3">
                  <i className="fas fa-calendar mr-1"></i>
                  Занятие #{reminder.schedule_id}
                </span>
              )}
              {reminder.assignment_id && (
                <span className="inline-flex items-center">
                  <i className="fas fa-tasks mr-1"></i>
                  Задание #{reminder.assignment_id}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default UpcomingReminders;


