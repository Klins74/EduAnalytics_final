// src/Routes.jsx

import React from "react";
import { BrowserRouter, Routes as RouterRoutes, Route } from "react-router-dom";
import ScrollToTop from "components/ScrollToTop";
import ErrorBoundary from "components/ErrorBoundary";
import * as Sentry from "@sentry/react";
import Login from "pages/login";

// Импортируем наш новый компонент
import ProtectedRoute from "components/ProtectedRoute"; 

// Правильные импорты без комментариев
import Dashboard from "pages/dashboard/index"; 
import AnalyticsDashboard from "pages/index";   
import AIAssistant from "pages/ai";
import NotFound from "pages/NotFound";
import MonitoringPage from "pages/MonitoringPage";

const Routes = () => {
  return (
    <BrowserRouter>
      <Sentry.ErrorBoundary fallback={({ error, componentStack, resetError }) => (
        <ErrorBoundary />
      )}>
        <ScrollToTop />
        <RouterRoutes>
          {/* Роут для страницы входа остается общедоступным */}
          <Route path="/login" element={<Login />} />

          {/* Создаем группу защищенных роутов */}
          <Route element={<ProtectedRoute />}>
            {/* Все роуты внутри этой группы будут доступны только авторизованным пользователям */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="/ai" element={<AIAssistant />} />
            <Route path="/monitoring" element={<MonitoringPage />} />
          </Route>
          
          <Route path="*" element={<NotFound />} />
        </RouterRoutes>
      </Sentry.ErrorBoundary>
    </BrowserRouter>
  );
};

export default Routes;