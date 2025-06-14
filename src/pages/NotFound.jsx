import React from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../components/AppIcon';

const NotFound = () => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="w-24 h-24 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center mx-auto mb-6">
            <Icon name="AlertTriangle" size={48} color="white" />
          </div>
          <h1 className="text-6xl font-bold text-text-primary mb-4">404</h1>
          <h2 className="text-2xl font-heading font-semibold text-text-primary mb-2">
            Страница не найдена
          </h2>
          <p className="text-text-secondary mb-8">
            Запрашиваемая страница не существует или была перемещена.
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleGoHome}
            className="w-full bg-primary text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors duration-150 font-medium hover-lift"
          >
            Вернуться на главную
          </button>
          <button
            onClick={handleGoBack}
            className="w-full bg-background border border-border text-text-primary px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors duration-150 font-medium hover-lift"
          >
            Назад
          </button>
        </div>

        <div className="mt-8 pt-8 border-t border-border">
          <p className="text-sm text-text-muted">
            Если проблема повторяется, обратитесь к администратору системы
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFound;