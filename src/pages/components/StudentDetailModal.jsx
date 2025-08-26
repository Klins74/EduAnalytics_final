// src/pages/components/StudentDetailModal.jsx

import React, { useState, useEffect } from 'react';
import Icon from '../../components/AppIcon';
import Image from '../../components/AppImage';
import { motion } from 'framer-motion';
import { analyticsApi } from '../../api/analyticsApi';

const StudentDetailModal = ({ student, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [perfLoading, setPerfLoading] = useState(false);
  const [perfError, setPerfError] = useState('');
  const [overview, setOverview] = useState(null);
  const [coursesPerformance, setCoursesPerformance] = useState([]);

  if (!student) return null;

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setPerfLoading(true);
        setPerfError('');
        const s = await analyticsApi.getStudentPerformance(student.id);
        if (!mounted) return;
        const ovw = s?.overall_performance || null;
        setOverview(ovw);
        setCoursesPerformance(Array.isArray(s?.courses_performance) ? s.courses_performance : []);
      } catch (e) {
        setPerfError('Не удалось загрузить аналитику студента');
      } finally {
        setPerfLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [student?.id]);

  const tabs = [
    { id: 'overview', label: 'Обзор', icon: 'User' },
    { id: 'activity', label: 'Активность', icon: 'Activity' },
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'ai-insights', label: 'AI-анализ', icon: 'Bot' }
  ];

  const getEngagementColor = (status) => {
    const colors = {
      active: 'text-success bg-success-50',
      moderate: 'text-warning bg-warning-50',
      low: 'text-error bg-error-50'
    };
    return colors[status] || 'text-text-secondary bg-background';
  };

  const getEngagementLabel = (status) => {
    const labels = {
      active: 'Активный',
      moderate: 'Умеренный',
      low: 'Низкий'
    };
    return labels[status] || status;
  };

  const getRiskColor = (score) => {
    if (score < 0.3) return 'text-success bg-success-50';
    if (score < 0.7) return 'text-warning bg-warning-50';
    return 'text-error bg-error-50';
  };

  const getRiskLabel = (score) => {
    if (score < 0.3) return 'Низкий риск';
    if (score < 0.7) return 'Средний риск';
    return 'Высокий риск';
  };

  const formatLastActivity = (date) => {
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Только что';
    if (minutes < 60) return `${minutes} мин назад`;
    if (hours < 24) return `${hours} ч назад`;
    return `${days} дн назад`;
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Student Info */}
      <div className="flex items-start space-x-4">
        <div className="relative">
          <Image
            src={student.avatar}
            alt={student.name}
            className="w-20 h-20 rounded-full object-cover"
          />
          {student.engagementStatus === 'active' && (
            <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-success border-2 border-surface rounded-full" />
          )}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-heading font-semibold text-text-primary mb-1">
            {student.name}
          </h3>
          <p className="text-text-secondary mb-2">Группа: {student.group}</p>
          <div className="flex items-center space-x-4">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getEngagementColor(student.engagementStatus)}`}>
              {getEngagementLabel(student.engagementStatus)}
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(student.aiRiskScore)}`}>
              {getRiskLabel(student.aiRiskScore)}
            </span>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="text-2xl font-heading font-semibold text-text-primary mb-1">
            {student.totalActivities}
          </div>
          <div className="text-sm text-text-secondary">Всего активностей</div>
        </div>
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="text-2xl font-heading font-semibold text-text-primary mb-1">
            {student.averageScore.toFixed(1)}
          </div>
          <div className="text-sm text-text-secondary">Средний балл</div>
        </div>
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="text-2xl font-heading font-semibold text-text-primary mb-1">
            {student.subjects.length}
          </div>
          <div className="text-sm text-text-secondary">Предметов</div>
        </div>
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="text-2xl font-heading font-semibold text-text-primary mb-1">
            {formatLastActivity(student.lastActivity)}
          </div>
          <div className="text-sm text-text-secondary">Последняя активность</div>
        </div>
      </div>

      {/* Subjects */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Изучаемые предметы</h4>
        <div className="flex flex-wrap gap-2">
          {student.subjects.map((subject, index) => (
            <span
              key={index}
              className="px-3 py-1 bg-primary-50 text-primary rounded-full text-sm"
            >
              {subject}
            </span>
          ))}
        </div>
      </div>
    </div>
  );

  const renderActivityTab = () => (
    <div className="space-y-4">
        {/* ... Содержимое вкладки "Активность" (оставляем как было) ... */}
        <h4>Здесь будет активность студента...</h4>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-4">
      {perfLoading ? (
        <div className="text-sm text-text-secondary">Загрузка аналитики успеваемости…</div>
      ) : perfError ? (
        <div className="text-sm text-error">{perfError}</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-background rounded-lg p-4 text-center">
              <div className="text-2xl font-heading font-semibold text-text-primary mb-1">{overview?.total_submissions ?? 0}</div>
              <div className="text-sm text-text-secondary">Сдач всего</div>
            </div>
            <div className="bg-background rounded-lg p-4 text-center">
              <div className="text-2xl font-heading font-semibold text-text-primary mb-1">{overview?.total_assignments ?? 0}</div>
              <div className="text-sm text-text-secondary">Заданий всего</div>
            </div>
            <div className="bg-background rounded-lg p-4 text-center">
              <div className="text-2xl font-heading font-semibold text-text-primary mb-1">{(overview?.overall_average_grade ?? 0).toFixed(2)}</div>
              <div className="text-sm text-text-secondary">Средний балл</div>
            </div>
            <div className="bg-background rounded-lg p-4 text-center">
              <div className="text-2xl font-heading font-semibold text-text-primary mb-1">{overview?.courses_count ?? 0}</div>
              <div className="text-sm text-text-secondary">Курсов</div>
            </div>
          </div>

          <div className="bg-background border border-border rounded-lg">
            <div className="px-4 py-3 border-b border-border text-sm font-medium text-text-primary">По курсам</div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-text-secondary">
                    <th className="p-2">Курс</th>
                    <th className="p-2">Сдач</th>
                    <th className="p-2">Средний балл</th>
                    <th className="p-2">Своевременность</th>
                  </tr>
                </thead>
                <tbody>
                  {coursesPerformance.map((c) => (
                    <tr key={c.course_id} className="border-t border-border">
                      <td className="p-2">{c.course_title}</td>
                      <td className="p-2">{c.submissions_count ?? 0}</td>
                      <td className="p-2">{(c.average_grade ?? 0).toFixed(2)}</td>
                      <td className="p-2">{(c.on_time_rate ?? 0).toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderAIInsightsTab = () => (
    <div className="space-y-4">
        {/* ... Содержимое вкладки "AI-анализ" (оставляем как было) ... */}
        <h4>Здесь будут AI-инсайты...</h4>
    </div>
  );

  return (
    <motion.div
      className="fixed inset-0 bg-black bg-opacity-50 z-1100 flex items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="bg-surface rounded-lg shadow-elevated w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col"
        initial={{ scale: 0.9, y: -20, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.9, y: 20, opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={(e) => e.stopPropagation()} // Предотвращаем закрытие по клику на само окно
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-heading font-semibold text-text-primary">
            Профиль студента
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-background rounded-lg transition-colors duration-150"
          >
            <Icon name="X" size={20} className="text-text-secondary" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 border-b-2 font-medium text-sm transition-colors duration-150 ${
                  activeTab === tab.id
                    ? 'border-primary text-primary' :'border-transparent text-text-secondary hover:text-text-primary'
                }`}
              >
                <Icon name={tab.icon} size={16} />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto">
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'activity' && renderActivityTab()}
          {activeTab === 'performance' && renderPerformanceTab()}
          {activeTab === 'ai-insights' && renderAIInsightsTab()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-border mt-auto">
          <button
            onClick={onClose}
            className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors duration-150"
          >
            Закрыть
          </button>
          <button className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 transition-colors duration-150 hover-lift">
            Отправить сообщение
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default StudentDetailModal;