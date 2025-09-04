import apiClient from './client';

/**
 * API клиент для работы с in-app уведомлениями
 */
class NotificationsApi {
  /**
   * Получить список уведомлений пользователя
   * @param {Object} params - Параметры запроса
   * @param {string} [params.status] - Фильтр по статусу (unread, read, archived)
   * @param {string} [params.notification_type] - Фильтр по типу
   * @param {number} [params.page=1] - Номер страницы
   * @param {number} [params.per_page=20] - Элементов на странице
   * @param {boolean} [params.include_expired=false] - Включать истекшие
   * @returns {Promise<Object>} Список уведомлений с пагинацией
   */
  async getNotifications(params = {}) {
    const searchParams = new URLSearchParams();
    
    if (params.status) searchParams.append('status', params.status);
    if (params.notification_type) searchParams.append('notification_type', params.notification_type);
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.per_page) searchParams.append('per_page', params.per_page.toString());
    if (params.include_expired) searchParams.append('include_expired', params.include_expired.toString());

    const response = await apiClient.get(`/notifications/in-app/?${searchParams.toString()}`);
    return response.data;
  }

  /**
   * Получить количество непрочитанных уведомлений
   * @returns {Promise<Object>} Объект с полем unread_count
   */
  async getUnreadCount() {
    const response = await apiClient.get('/notifications/in-app/unread/count');
    return response.data;
  }

  /**
   * Получить статистику уведомлений
   * @returns {Promise<Object>} Статистика уведомлений
   */
  async getStats() {
    const response = await apiClient.get('/notifications/in-app/stats');
    return response.data;
  }

  /**
   * Получить конкретное уведомление
   * @param {number} notificationId - ID уведомления
   * @returns {Promise<Object>} Данные уведомления
   */
  async getNotification(notificationId) {
    const response = await apiClient.get(`/notifications/in-app/${notificationId}`);
    return response.data;
  }

  /**
   * Отметить уведомление как прочитанное
   * @param {number} notificationId - ID уведомления
   * @returns {Promise<Object>} Обновленное уведомление
   */
  async markAsRead(notificationId) {
    const response = await apiClient.patch(`/notifications/in-app/${notificationId}/read`);
    return response.data;
  }

  /**
   * Отметить все уведомления как прочитанные
   * @returns {Promise<Object>} Результат операции
   */
  async markAllAsRead() {
    const response = await apiClient.patch('/notifications/in-app/read-all');
    return response.data;
  }

  /**
   * Архивировать уведомление
   * @param {number} notificationId - ID уведомления
   * @returns {Promise<Object>} Обновленное уведомление
   */
  async archiveNotification(notificationId) {
    const response = await apiClient.patch(`/notifications/in-app/${notificationId}/archive`);
    return response.data;
  }

  /**
   * Удалить уведомление
   * @param {number} notificationId - ID уведомления
   * @returns {Promise<Object>} Результат операции
   */
  async deleteNotification(notificationId) {
    const response = await apiClient.delete(`/notifications/in-app/${notificationId}`);
    return response.data;
  }

  /**
   * Выполнить массовое действие с уведомлениями
   * @param {Object} actionData - Данные действия
   * @param {number[]} actionData.notification_ids - Массив ID уведомлений
   * @param {string} actionData.action - Действие (mark_read, mark_unread, archive, delete)
   * @returns {Promise<Object>} Результат операции
   */
  async bulkAction(actionData) {
    const response = await apiClient.post('/notifications/in-app/bulk-action', actionData);
    return response.data;
  }

  /**
   * Получить настройки уведомлений пользователя
   * @returns {Promise<Object>} Настройки уведомлений
   */
  async getPreferences() {
    const response = await apiClient.get('/notifications/in-app/preferences');
    return response.data;
  }

  /**
   * Обновить настройки уведомлений
   * @param {Object} preferences - Новые настройки
   * @returns {Promise<Object>} Обновленные настройки
   */
  async updatePreferences(preferences) {
    const response = await apiClient.put('/notifications/in-app/preferences', preferences);
    return response.data;
  }
}

// Экспортируем экземпляр API
const notificationsApi = new NotificationsApi();
export default notificationsApi;

// Константы для типов уведомлений
export const NOTIFICATION_TYPES = {
  SYSTEM: 'system',
  ASSIGNMENT: 'assignment',
  GRADE: 'grade',
  DEADLINE: 'deadline',
  REMINDER: 'reminder',
  FEEDBACK: 'feedback',
  SCHEDULE: 'schedule',
  ANNOUNCEMENT: 'announcement'
};

// Константы для статусов уведомлений
export const NOTIFICATION_STATUS = {
  UNREAD: 'unread',
  READ: 'read',
  ARCHIVED: 'archived'
};

// Константы для приоритетов
export const NOTIFICATION_PRIORITY = {
  LOW: 'low',
  NORMAL: 'normal',
  HIGH: 'high',
  URGENT: 'urgent'
};

// Утилиты для работы с уведомлениями
export const notificationUtils = {
  /**
   * Получить иконку для типа уведомления
   * @param {string} type - Тип уведомления
   * @returns {string} Класс иконки
   */
  getTypeIcon(type) {
    const icons = {
      [NOTIFICATION_TYPES.SYSTEM]: 'fas fa-cog',
      [NOTIFICATION_TYPES.ASSIGNMENT]: 'fas fa-tasks',
      [NOTIFICATION_TYPES.GRADE]: 'fas fa-star',
      [NOTIFICATION_TYPES.DEADLINE]: 'fas fa-clock',
      [NOTIFICATION_TYPES.REMINDER]: 'fas fa-bell',
      [NOTIFICATION_TYPES.FEEDBACK]: 'fas fa-comment',
      [NOTIFICATION_TYPES.SCHEDULE]: 'fas fa-calendar',
      [NOTIFICATION_TYPES.ANNOUNCEMENT]: 'fas fa-bullhorn'
    };
    return icons[type] || 'fas fa-info-circle';
  },

  /**
   * Получить цвет для приоритета уведомления
   * @param {string} priority - Приоритет
   * @returns {string} Класс цвета
   */
  getPriorityColor(priority) {
    const colors = {
      [NOTIFICATION_PRIORITY.LOW]: 'text-gray-500',
      [NOTIFICATION_PRIORITY.NORMAL]: 'text-blue-500',
      [NOTIFICATION_PRIORITY.HIGH]: 'text-orange-500',
      [NOTIFICATION_PRIORITY.URGENT]: 'text-red-500'
    };
    return colors[priority] || 'text-gray-500';
  },

  /**
   * Получить текст статуса на русском языке
   * @param {string} status - Статус
   * @returns {string} Текст статуса
   */
  getStatusText(status) {
    const texts = {
      [NOTIFICATION_STATUS.UNREAD]: 'Не прочитано',
      [NOTIFICATION_STATUS.READ]: 'Прочитано',
      [NOTIFICATION_STATUS.ARCHIVED]: 'Архивировано'
    };
    return texts[status] || 'Неизвестно';
  },

  /**
   * Получить текст типа на русском языке
   * @param {string} type - Тип
   * @returns {string} Текст типа
   */
  getTypeText(type) {
    const texts = {
      [NOTIFICATION_TYPES.SYSTEM]: 'Системное',
      [NOTIFICATION_TYPES.ASSIGNMENT]: 'Задание',
      [NOTIFICATION_TYPES.GRADE]: 'Оценка',
      [NOTIFICATION_TYPES.DEADLINE]: 'Дедлайн',
      [NOTIFICATION_TYPES.REMINDER]: 'Напоминание',
      [NOTIFICATION_TYPES.FEEDBACK]: 'Отзыв',
      [NOTIFICATION_TYPES.SCHEDULE]: 'Расписание',
      [NOTIFICATION_TYPES.ANNOUNCEMENT]: 'Объявление'
    };
    return texts[type] || 'Неизвестно';
  },

  /**
   * Форматировать дату уведомления
   * @param {string} dateString - Строка даты
   * @returns {string} Отформатированная дата
   */
  formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      return 'Только что';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} ч. назад`;
    } else if (diffInHours < 48) {
      return 'Вчера';
    } else {
      return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};


