import React from 'react';
import * as Sentry from '@sentry/react';

const SentryTest = () => {
  const triggerError = () => {
    try {
      // Генерируем ошибку для тестирования Sentry
      throw new Error('Тестовая ошибка для Sentry');
    } catch (error) {
      // Отправляем ошибку в Sentry
      Sentry.captureException(error);
      // Показываем сообщение пользователю
      alert('Тестовая ошибка отправлена в Sentry!');
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow-sm">
      <h3 className="text-lg font-medium mb-2">Тестирование Sentry</h3>
      <p className="text-gray-600 mb-4">
        Нажмите кнопку ниже, чтобы сгенерировать тестовую ошибку и отправить её в Sentry.
      </p>
      <button
        onClick={triggerError}
        className="bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-4 rounded transition-colors duration-200"
      >
        Сгенерировать ошибку
      </button>
    </div>
  );
};

export default SentryTest;