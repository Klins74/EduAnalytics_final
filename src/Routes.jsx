// src/Routes.jsx

import React from "react";
import { BrowserRouter, Routes as RouterRoutes, Route } from "react-router-dom";
import ScrollToTop from "components/ScrollToTop";
import ErrorBoundary from "components/ErrorBoundary";
import Login from "pages/login";

// Правильные импорты без комментариев
import Dashboard from "pages/dashboard/index"; 
import AnalyticsDashboard from "pages/index";   
import AIAssistant from "pages/ai";
import NotFound from "pages/NotFound";
import MonitoringPage from "pages/MonitoringPage";

const Routes = () => {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <ScrollToTop />
        <RouterRoutes>
          <Route path="/login" element={<Login />} />

          {/* Главная страница (Панель управления) */}
          <Route path="/" element={<Dashboard />} />
          
          {/* Страница с вкладками аналитики */}
          <Route path="/analytics" element={<AnalyticsDashboard />} />

          <Route path="/ai" element={<AIAssistant />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="*" element={<NotFound />} />
        </RouterRoutes>
      </ErrorBoundary>
    </BrowserRouter>
  );
};

export default Routes;