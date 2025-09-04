import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import remindersApi, { 
  REMINDER_TYPES, 
  NOTIFICATION_CHANNELS,
  reminderUtils 
} from '../../api/remindersApi';

/**
 * Компонент панели тестирования напоминаний
 */
const ReminderTestPanel = ({ className = '' }) => {
  const [testForm, setTestForm] = useState({
    reminder_type: REMINDER_TYPES.SCHEDULE_UPCOMING,
    notification_channel: NOTIFICATION_CHANNELS.IN_APP,
    test_message: ''
  });
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Обработка отправки тестового напоминания
  const handleSendTest = async (e) => {
    e.preventDefault();
    
    try {
      setSending(true);
      setError(null);
      setResult(null);
      
      const response = await remindersApi.sendTestReminder(testForm);
      setResult(response);
    } catch (err) {
      console.error('Error sending test reminder:', err);
      setError(err.response?.data?.detail || 'Не удалось отправить тестовое напоминание');
    } finally {
      setSending(false);
    }
  };

  // Обработка изменения формы
  const handleFormChange = (field, value) => {
    setTestForm(prev => ({ ...prev, [field]: value }));
    // Сбрасываем результаты при изменении формы
    setResult(null);
    setError(null);
  };

  return (
    <div className={`${className}`}>
      <div className="max-w-2xl mx-auto">
        {/* Заголовок */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <i className="fas fa-flask text-2xl"></i>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Тестирование напоминаний
          </h3>
          <p className="text-gray-600">
            Отправьте себе тестовое напоминание, чтобы проверить настройки
          </p>
        </div>

        {/* Форма тестирования */}
        <form onSubmit={handleSendTest} className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
          {/* Тип напоминания */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Тип напоминания
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.values(REMINDER_TYPES).map(type => (
                <label
                  key={type}
                  className={`relative flex items-center p-4 border rounded-lg cursor-pointer transition-colors duration-200 ${
                    testForm.reminder_type === type
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="reminder_type"
                    value={type}
                    checked={testForm.reminder_type === type}
                    onChange={(e) => handleFormChange('reminder_type', e.target.value)}
                    className="sr-only"
                  />
                  <div className="flex items-center space-x-3">
                    <i className={`${reminderUtils.getReminderTypeIcon(type)} text-lg ${
                      testForm.reminder_type === type ? 'text-blue-600' : 'text-gray-400'
                    }`}></i>
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {reminderUtils.getReminderTypeName(type)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {reminderUtils.getReminderTypeDescription(type)}
                      </div>
                    </div>
                  </div>
                  {testForm.reminder_type === type && (
                    <div className="absolute top-2 right-2">
                      <i className="fas fa-check text-blue-500 text-sm"></i>
                    </div>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Канал уведомления */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Канал уведомления
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.values(NOTIFICATION_CHANNELS).map(channel => (
                <label
                  key={channel}
                  className={`relative flex flex-col items-center p-4 border rounded-lg cursor-pointer transition-colors duration-200 ${
                    testForm.notification_channel === channel
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="notification_channel"
                    value={channel}
                    checked={testForm.notification_channel === channel}
                    onChange={(e) => handleFormChange('notification_channel', e.target.value)}
                    className="sr-only"
                  />
                  <i className={`${reminderUtils.getChannelIcon(channel)} text-2xl mb-2 ${
                    testForm.notification_channel === channel 
                      ? 'text-blue-600' 
                      : reminderUtils.getChannelColor(channel)
                  }`}></i>
                  <span className="text-xs font-medium text-gray-900 text-center">
                    {reminderUtils.getChannelName(channel)}
                  </span>
                  {testForm.notification_channel === channel && (
                    <div className="absolute top-1 right-1">
                      <i className="fas fa-check text-blue-500 text-xs"></i>
                    </div>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Тестовое сообщение */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тестовое сообщение (необязательно)
            </label>
            <textarea
              value={testForm.test_message}
              onChange={(e) => handleFormChange('test_message', e.target.value)}
              placeholder="Введите собственное сообщение для теста или оставьте пустым для использования стандартного"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 resize-none"
            />
            <p className="text-xs text-gray-500 mt-1">
              Если поле пустое, будет использовано стандартное сообщение для выбранного типа напоминания
            </p>
          </div>

          {/* Кнопка отправки */}
          <div className="flex justify-center">
            <button
              type="submit"
              disabled={sending}
              className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {sending ? (
                <>
                  <i className="fas fa-spinner fa-spin mr-2"></i>
                  Отправка...
                </>
              ) : (
                <>
                  <i className="fas fa-paper-plane mr-2"></i>
                  Отправить тест
                </>
              )}
            </button>
          </div>
        </form>

        {/* Результаты */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg"
            >
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center mr-3">
                  <i className="fas fa-check text-sm"></i>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-green-800">
                    Тестовое напоминание отправлено!
                  </h4>
                  <p className="text-sm text-green-700 mt-1">
                    {result.message}
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
            >
              <div className="flex items-center">
                <div className="w-8 h-8 bg-red-100 text-red-600 rounded-full flex items-center justify-center mr-3">
                  <i className="fas fa-exclamation-triangle text-sm"></i>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-red-800">
                    Ошибка отправки
                  </h4>
                  <p className="text-sm text-red-700 mt-1">
                    {error}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Информационная панель */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
              <i className="fas fa-info text-sm"></i>
            </div>
            <div className="text-sm">
              <h4 className="font-semibold text-blue-800 mb-2">
                Как работает тестирование
              </h4>
              <ul className="text-blue-700 space-y-1">
                <li>• Тестовое напоминание будет отправлено только вам</li>
                <li>• Сообщение будет доставлено через выбранный канал</li>
                <li>• Для email и SMS может потребоваться несколько минут</li>
                <li>• In-app уведомления появятся сразу в центре уведомлений</li>
                <li>• Push-уведомления требуют разрешения браузера</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReminderTestPanel;


