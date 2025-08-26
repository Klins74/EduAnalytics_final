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
import SchedulePage from "pages/schedule";
import QuizPage from "pages/quiz";
import CoursesList from "pages/courses";
import CourseDetail from "pages/courses/detail";
import CoursePages from "pages/course-pages";
import CourseDiscussions from "pages/course-discussions";
import CourseModules from "pages/course-modules";
import AssignmentGroups from "pages/assignment-groups";
import CourseQuizzes from "pages/course-quizzes";

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
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/quiz" element={<QuizPage />} />

            {/* Курсы и разделы курса */}
            <Route path="/courses" element={<CoursesList />} />
            <Route path="/courses/:courseId" element={<CourseDetail />} />
            <Route path="/courses/:courseId/pages" element={<CoursePages />} />
            <Route path="/courses/:courseId/discussions" element={<CourseDiscussions />} />
            <Route path="/courses/:courseId/modules" element={<CourseModules />} />
            <Route path="/courses/:courseId/assignment-groups" element={<AssignmentGroups />} />
            <Route path="/courses/:courseId/quizzes" element={<CourseQuizzes />} />
          </Route>
          
          <Route path="*" element={<NotFound />} />
        </RouterRoutes>
      </Sentry.ErrorBoundary>
    </BrowserRouter>
  );
};

export default Routes;