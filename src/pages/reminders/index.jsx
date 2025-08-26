import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';

const REMINDER_TYPES = {
  'schedule_upcoming': 'Предстоящие занятия',
  'schedule_cancelled': 'Отмена занятий',
  'schedule_changed': 'Изменения в расписании',
  'assignment_due': 'Дедлайны заданий'
};

const INTERVALS = {
  '15m': '15 минут',
  '1h': '1 час',
  '2h': '2 часа',
  '1d': '1 день',
  '3d': '3 дня',
  '1w': '1 неделя'
};

const CHANNELS = {
  'email': 'Email',
  'sms': 'SMS',
  'push': 'Push-уведомления',
  'in_app': 'В приложении'
};

const RemindersPage = () => {
  const navigate = useNavigate();
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [testStatus, setTestStatus] = useState('');

  const headers = {
    'Authorization': `Bearer ${localStorage.getItem('token') || localStorage.getItem('accessToken')}`,
    'Content-Type': 'application/json'
  };

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // Проверяем наличие токена
      const token = localStorage.getItem('token') || localStorage.getItem('accessToken');
      if (!token) {
        setError('Необходима авторизация');
        navigate('/login');
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/reminders/settings', { headers });
      
      if (response.status === 401) {
        setError('Сессия истекла. Необходимо войти заново.');
        localStorage.removeItem('token');
        localStorage.removeItem('accessToken');
        navigate('/login');
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
        setError(''); // Очищаем ошибку при успехе
      } else {
        setError(`Ошибка загрузки настроек: ${response.status}`);
      }
    } catch (err) {
      console.error('Error loading settings:', err);
      setError('Ошибка подключения к серверу');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const updateSetting = async (reminderType, updates) => {
    try {
      setSaving(true);
      const response = await fetch(`http://localhost:8000/api/reminders/settings/${reminderType}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(updates)
      });

      if (response.ok) {
        await loadSettings(); // Перезагружаем настройки
      } else {
        setError('Ошибка сохранения настроек');
      }
    } catch (err) {
      setError('Ошибка подключения к серверу');
    } finally {
      setSaving(false);
    }
  };

  const sendTestReminder = async (reminderType, channel) => {
    try {
      setTestStatus('Отправка...');
      const response = await fetch('http://localhost:8000/api/reminders/test', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          reminder_type: reminderType,
          notification_channel: channel,
          test_message: 'Это тестовое напоминание от системы EduAnalytics'
        })
      });

      if (response.ok) {
        setTestStatus('Тестовое напоминание отправлено!');
        setTimeout(() => setTestStatus(''), 3000);
      } else {
        setTestStatus('Ошибка отправки');
        setTimeout(() => setTestStatus(''), 3000);
      }
    } catch (err) {
      setTestStatus('Ошибка подключения');
      setTimeout(() => setTestStatus(''), 3000);
    }
  };

  const getSettingByType = (type) => {
    return settings.find(s => s.reminder_type === type) || {
      reminder_type: type,
      is_enabled: false,
      interval_before: '1h',
      notification_channel: 'email'
    };
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <div className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900 mb-2">Настройки напоминаний</h1>
            <p className="text-gray-600">Настройте автоматические напоминания о важных событиях</p>
          </div>

          {loading ? (
            <div className="text-gray-500">Загрузка...</div>
          ) : error ? (
            <div className="text-red-600 mb-4">
              {error}
              {(error.includes('авторизация') || error.includes('Сессия истекла')) && (
                <div className="mt-4">
                  <button
                    onClick={() => navigate('/login')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                  >
                    Войти в систему
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(REMINDER_TYPES).map(([type, label]) => {
                const setting = getSettingByType(type);
                
                return (
                  <div key={type} className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">{label}</h3>
                        <p className="text-sm text-gray-500 mt-1">
                          {type === 'schedule_upcoming' && 'Напоминания о предстоящих занятиях'}
                          {type === 'schedule_cancelled' && 'Уведомления об отмене занятий'}
                          {type === 'schedule_changed' && 'Уведомления об изменениях в расписании'}
                          {type === 'assignment_due' && 'Напоминания о приближающихся дедлайнах'}
                        </p>
                      </div>
                      
                      <div className="flex items-center">
                        <label className="inline-flex items-center">
                          <input
                            type="checkbox"
                            checked={setting.is_enabled}
                            onChange={(e) => updateSetting(type, { is_enabled: e.target.checked })}
                            disabled={saving}
                            className="rounded border-gray-300 text-blue-600 shadow-sm focus:ring-blue-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Включено</span>
                        </label>
                      </div>
                    </div>

                    {setting.is_enabled && (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Интервал напоминания (только для некоторых типов) */}
                        {(type === 'schedule_upcoming' || type === 'assignment_due') && (
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Напомнить за
                            </label>
                            <select
                              value={setting.interval_before}
                              onChange={(e) => updateSetting(type, { interval_before: e.target.value })}
                              disabled={saving}
                              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                            >
                              {Object.entries(INTERVALS).map(([value, label]) => (
                                <option key={value} value={value}>{label}</option>
                              ))}
                            </select>
                          </div>
                        )}

                        {/* Канал уведомления */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Способ уведомления
                          </label>
                          <select
                            value={setting.notification_channel}
                            onChange={(e) => updateSetting(type, { notification_channel: e.target.value })}
                            disabled={saving}
                            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                          >
                            {Object.entries(CHANNELS).map(([value, label]) => (
                              <option key={value} value={value}>{label}</option>
                            ))}
                          </select>
                        </div>

                        {/* Тестовое напоминание */}
                        <div className="flex items-end">
                          <button
                            onClick={() => sendTestReminder(type, setting.notification_channel)}
                            disabled={saving}
                            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
                          >
                            Тест
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Статус тестовых напоминаний */}
              {testStatus && (
                <div className={`p-4 rounded-md ${testStatus.includes('Ошибка') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                  {testStatus}
                </div>
              )}

              {/* Дополнительные настройки */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Дополнительные настройки</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Групповые уведомления</h4>
                      <p className="text-sm text-gray-500">Получать уведомления обо всех занятиях группы</p>
                    </div>
                    <label className="inline-flex items-center">
                      <input type="checkbox" className="rounded border-gray-300 text-blue-600" />
                      <span className="ml-2 text-sm text-gray-700">Включено</span>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Ночной режим</h4>
                      <p className="text-sm text-gray-500">Не отправлять уведомления с 22:00 до 8:00</p>
                    </div>
                    <label className="inline-flex items-center">
                      <input type="checkbox" className="rounded border-gray-300 text-blue-600" defaultChecked />
                      <span className="ml-2 text-sm text-gray-700">Включено</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Сохранение */}
              {saving && (
                <div className="text-center text-gray-500">
                  Сохранение настроек...
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RemindersPage;
