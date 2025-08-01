// src/components/ProtectedRoute.jsx

import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

const ProtectedRoute = () => {
  // Проверяем, есть ли токен в localStorage
  const token = localStorage.getItem('accessToken');

  // Если токен есть, разрешаем доступ к вложенным роутам (страницам)
  // Outlet — это специальный компонент, который отображает дочерний роут
  if (token) {
    return <Outlet />;
  }

  // Если токена нет, принудительно перенаправляем на страницу входа
  return <Navigate to="/login" />;
};

export default ProtectedRoute;