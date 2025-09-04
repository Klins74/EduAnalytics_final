import apiClient from './client';

/**
 * API клиент для работы с напоминаниями
 */
class RemindersApi {
  /**
   * Получить все настройки напоминаний пользователя
   * @returns {Promise<Array>} Список настроек напоминаний
   */
  async getReminderSettings() {
    const response = await apiClient.get('/reminders/settings');
    return response.data;
  }

  /**
   * Получить настройку конкретного типа напоминания
   * @param {string} reminderType - Тип напоминания
   * @returns {Promise<Object>} Настройка напоминания
   */
  async getReminderSetting(reminderType) {
    const response = await apiClient.get(`/reminders/settings/${reminderType}`);
    return response.data;
  }

  /**
   * Обновить настройку конкретного типа напоминания
   * @param {string} reminderType - Тип напоминания
   * @param {Object} settings - Новые настройки
   * @returns {Promise<Object>} Обновленная настройка
   */
  async updateReminderSetting(reminderType, settings) {
    const response = await apiClient.put(`/reminders/settings/${reminderType}`, settings);
    return response.data;
  }

  /**
   * Обновить все предпочтения напоминаний пользователя
   * @param {Object} preferences - Новые предпочтения
   * @returns {Promise<Array>} Обновленные настройки
   */
  async updateReminderPreferences(preferences) {
    const response = await apiClient.put('/reminders/preferences', preferences);
    return response.data;
  }

  /**
   * Получить предстоящие напоминания
   * @param {number} daysAhead - Количество дней вперед (по умолчанию 7)
   * @returns {Promise<Array>} Список предстоящих напоминаний
   */
  async getUpcomingReminders(daysAhead = 7) {
    const response = await apiClient.get(`/reminders/upcoming?days_ahead=${daysAhead}`);
    return response.data;
  }

  /**
   * Отправить тестовое напоминание
   * @param {Object} testRequest - Параметры тестового напоминания
   * @returns {Promise<Object>} Результат отправки
   */
  async sendTestReminder(testRequest) {
    const response = await apiClient.post('/reminders/test', testRequest);
    return response.data;
  }

  /**
   * Получить статистику напоминаний
   * @returns {Promise<Object>} Статистика напоминаний
   */
  async getReminderStats() {
    const response = await apiClient.get('/reminders/stats');
    return response.data;
  }

  /**
   * Принудительно обработать готовые напоминания (только для админов)
   * @returns {Promise<Object>} Результат обработки
   */
  async processPendingReminders() {
    const response = await apiClient.post('/reminders/process');
    return response.data;
  }
}

// Экспортируем экземпляр API
const remindersApi = new RemindersApi();
export default remindersApi;

// Константы для типов напоминаний
export const REMINDER_TYPES = {
  SCHEDULE_UPCOMING: 'schedule_upcoming',
  SCHEDULE_CANCELLED: 'schedule_cancelled',
  SCHEDULE_CHANGED: 'schedule_changed',
  ASSIGNMENT_DUE: 'assignment_due'
};

// Константы для интервалов напоминаний
export const REMINDER_INTERVALS = {
  MINUTES_15: '15m',
  HOUR_1: '1h',
  HOURS_2: '2h',
  DAY_1: '1d',
  DAYS_3: '3d',
  WEEK_1: '1w'
};

// Константы для каналов уведомлений
export const NOTIFICATION_CHANNELS = {
  EMAIL: 'email',
  SMS: 'sms',
  PUSH: 'push',
  IN_APP: 'in_app'
};

// Утилиты для работы с напоминаниями
export const reminderUtils = {
  /**
   * Получить русское название типа напоминания
   * @param {string} type - Тип напоминания
   * @returns {string} Русское название
   */
  getReminderTypeName(type) {
    const names = {
      [REMINDER_TYPES.SCHEDULE_UPCOMING]: 'Предстоящие занятия',
      [REMINDER_TYPES.SCHEDULE_CANCELLED]: 'Отмененные занятия',
      [REMINDER_TYPES.SCHEDULE_CHANGED]: 'Изменения в расписании',
      [REMINDER_TYPES.ASSIGNMENT_DUE]: 'Дедлайны заданий'
    };
    return names[type] || 'Неизвестный тип';
  },

  /**
   * Получить описание типа напоминания
   * @param {string} type - Тип напоминания
   * @returns {string} Описание
   */
  getReminderTypeDescription(type) {
    const descriptions = {
      [REMINDER_TYPES.SCHEDULE_UPCOMING]: 'Напоминания о предстоящих занятиях по расписанию',
      [REMINDER_TYPES.SCHEDULE_CANCELLED]: 'Уведомления об отмененных занятиях',
      [REMINDER_TYPES.SCHEDULE_CHANGED]: 'Уведомления об изменениях времени или места занятий',
      [REMINDER_TYPES.ASSIGNMENT_DUE]: 'Напоминания о приближающихся дедлайнах заданий'
    };
    return descriptions[type] || 'Описание недоступно';
  },

  /**
   * Получить иконку для типа напоминания
   * @param {string} type - Тип напоминания
   * @returns {string} Класс иконки
   */
  getReminderTypeIcon(type) {
    const icons = {
      [REMINDER_TYPES.SCHEDULE_UPCOMING]: 'fas fa-calendar-check',
      [REMINDER_TYPES.SCHEDULE_CANCELLED]: 'fas fa-calendar-times',
      [REMINDER_TYPES.SCHEDULE_CHANGED]: 'fas fa-calendar-alt',
      [REMINDER_TYPES.ASSIGNMENT_DUE]: 'fas fa-clock'
    };
    return icons[type] || 'fas fa-bell';
  },

  /**
   * Получить русское название интервала
   * @param {string} interval - Интервал
   * @returns {string} Русское название
   */
  getIntervalName(interval) {
    const names = {
      [REMINDER_INTERVALS.MINUTES_15]: '15 минут',
      [REMINDER_INTERVALS.HOUR_1]: '1 час',
      [REMINDER_INTERVALS.HOURS_2]: '2 часа',
      [REMINDER_INTERVALS.DAY_1]: '1 день',
      [REMINDER_INTERVALS.DAYS_3]: '3 дня',
      [REMINDER_INTERVALS.WEEK_1]: '1 неделя'
    };
    return names[interval] || 'Неизвестный интервал';
  },

  /**
   * Получить русское название канала уведомлений
   * @param {string} channel - Канал
   * @returns {string} Русское название
   */
  getChannelName(channel) {
    const names = {
      [NOTIFICATION_CHANNELS.EMAIL]: 'Email',
      [NOTIFICATION_CHANNELS.SMS]: 'SMS',
      [NOTIFICATION_CHANNELS.PUSH]: 'Push-уведомления',
      [NOTIFICATION_CHANNELS.IN_APP]: 'В приложении'
    };
    return names[channel] || 'Неизвестный канал';
  },

  /**
   * Получить иконку для канала уведомлений
   * @param {string} channel - Канал
   * @returns {string} Класс иконки
   */
  getChannelIcon(channel) {
    const icons = {
      [NOTIFICATION_CHANNELS.EMAIL]: 'fas fa-envelope',
      [NOTIFICATION_CHANNELS.SMS]: 'fas fa-sms',
      [NOTIFICATION_CHANNELS.PUSH]: 'fas fa-mobile-alt',
      [NOTIFICATION_CHANNELS.IN_APP]: 'fas fa-bell'
    };
    return icons[channel] || 'fas fa-question';
  },

  /**
   * Получить цвет для канала уведомлений
   * @param {string} channel - Канал
   * @returns {string} Класс цвета
   */
  getChannelColor(channel) {
    const colors = {
      [NOTIFICATION_CHANNELS.EMAIL]: 'text-blue-500',
      [NOTIFICATION_CHANNELS.SMS]: 'text-green-500',
      [NOTIFICATION_CHANNELS.PUSH]: 'text-purple-500',
      [NOTIFICATION_CHANNELS.IN_APP]: 'text-orange-500'
    };
    return colors[channel] || 'text-gray-500';
  },

  /**
   * Форматировать дату и время напоминания
   * @param {string} dateString - Строка даты
   * @returns {string} Отформатированная дата
   */
  formatReminderDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (date - now) / (1000 * 60 * 60);

    if (diffInHours < 1 && diffInHours > 0) {
      const diffInMinutes = Math.floor((date - now) / (1000 * 60));
      return `Через ${diffInMinutes} мин.`;
    } else if (diffInHours < 24 && diffInHours > 0) {
      return `Через ${Math.floor(diffInHours)} ч.`;
    } else if (diffInHours < 0) {
      return 'Просрочено';
    } else {
      return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  },

  /**
   * Проверить, просрочено ли напоминание
   * @param {string} dateString - Строка даты
   * @returns {boolean} True если просрочено
   */
  isReminderOverdue(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    return date < now;
  },

  /**
   * Получить статус напоминания для отображения
   * @param {Object} reminder - Объект напоминания
   * @returns {Object} Объект с статусом и цветом
   */
  getReminderStatus(reminder) {
    if (reminder.is_sent) {
      return {
        status: 'Отправлено',
        color: 'text-green-500',
        bgColor: 'bg-green-100',
        icon: 'fas fa-check'
      };
    } else if (this.isReminderOverdue(reminder.send_at)) {
      return {
        status: 'Просрочено',
        color: 'text-red-500',
        bgColor: 'bg-red-100',
        icon: 'fas fa-exclamation-triangle'
      };
    } else {
      return {
        status: 'Запланировано',
        color: 'text-blue-500',
        bgColor: 'bg-blue-100',
        icon: 'fas fa-clock'
      };
    }
  }
};


