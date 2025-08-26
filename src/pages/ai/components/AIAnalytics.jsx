import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';

const AIAnalytics = ({ studentId, courseId }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('month');

  useEffect(() => {
    if (studentId || courseId) {
      fetchAnalyticsData();
    }
  }, [studentId, courseId, selectedPeriod]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      
      if (studentId) {
        // Получаем аналитику студента
        const response = await fetch(`http://localhost:8000/api/analytics/students/${studentId}/performance`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setAnalyticsData(data);
        }
      } else if (courseId) {
        // Получаем аналитику курса
        const response = await fetch(`http://localhost:8000/api/analytics/courses/${courseId}/overview`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          setAnalyticsData(data);
        }
      }
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateAIInsights = () => {
    if (!analyticsData) return [];

    const insights = [];
    
    if (studentId && analyticsData.overall_performance) {
      const { overall_average_grade, total_submissions, total_assignments } = analyticsData.overall_performance;
      
      // Анализ успеваемости
      if (overall_average_grade >= 85) {
        insights.push({
          type: 'excellent',
          title: 'Отличная успеваемость',
          description: 'Студент показывает высокие результаты. Рекомендуется поддерживать текущий уровень и ставить более амбициозные цели.',
          icon: 'Award',
          priority: 'high'
        });
      } else if (overall_average_grade >= 70) {
        insights.push({
          type: 'good',
          title: 'Хорошая успеваемость',
          description: 'Результаты выше среднего. Есть потенциал для улучшения в определенных областях.',
          icon: 'TrendingUp',
          priority: 'medium'
        });
      } else {
        insights.push({
          type: 'needs_improvement',
          title: 'Требует внимания',
          description: 'Необходимо выявить проблемные области и разработать план улучшения.',
          icon: 'AlertTriangle',
          priority: 'high'
        });
      }

      // Анализ активности
      const submissionRate = (total_submissions / total_assignments) * 100;
      if (submissionRate < 80) {
        insights.push({
          type: 'activity',
          title: 'Низкая активность',
          description: `Выполнено только ${submissionRate.toFixed(1)}% заданий. Рекомендуется увеличить вовлеченность.`,
          icon: 'Activity',
          priority: 'medium'
        });
      }

      // Анализ по курсам
      if (analyticsData.courses_performance) {
        const weakCourses = analyticsData.courses_performance.filter(
          course => course.average_grade < 70
        );
        
        if (weakCourses.length > 0) {
          insights.push({
            type: 'weak_subjects',
            title: 'Слабые предметы',
            description: `Выявлено ${weakCourses.length} курсов с низкой успеваемостью. Требуется дополнительная поддержка.`,
            icon: 'BookOpen',
            priority: 'high'
          });
        }
      }
    }

    if (courseId && analyticsData) {
      const { total_students, total_assignments, average_grade } = analyticsData;
      
      // Анализ курса
      if (average_grade < 70) {
        insights.push({
          type: 'course_improvement',
          title: 'Курс требует улучшения',
          description: 'Средняя успеваемость ниже ожидаемой. Рекомендуется пересмотреть методику преподавания.',
          icon: 'Settings',
          priority: 'high'
        });
      }

      if (total_students > 0) {
        insights.push({
          type: 'course_stats',
          title: 'Статистика курса',
          description: `Курс посещают ${total_students} студентов, ${total_assignments} заданий.`,
          icon: 'Users',
          priority: 'low'
        });
      }
    }

    return insights;
  };

  const getInsightColor = (type) => {
    switch (type) {
      case 'excellent': return 'border-green-200 bg-green-50';
      case 'good': return 'border-blue-200 bg-blue-50';
      case 'needs_improvement': return 'border-red-200 bg-red-50';
      case 'activity': return 'border-yellow-200 bg-yellow-50';
      case 'weak_subjects': return 'border-orange-200 bg-orange-50';
      case 'course_improvement': return 'border-purple-200 bg-purple-50';
      case 'course_stats': return 'border-gray-200 bg-gray-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getInsightIconColor = (type) => {
    switch (type) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'needs_improvement': return 'text-red-600';
      case 'activity': return 'text-yellow-600';
      case 'weak_subjects': return 'text-orange-600';
      case 'course_improvement': return 'text-purple-600';
      case 'course_stats': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="bg-surface border border-border rounded-lg shadow-card p-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const insights = generateAIInsights();

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading font-medium text-text-primary">AI-анализ</h3>
        <div className="flex items-center space-x-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-2 py-1 text-xs border border-border rounded focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="week">Неделя</option>
            <option value="month">Месяц</option>
            <option value="semester">Семестр</option>
          </select>
        </div>
      </div>

      {insights.length > 0 ? (
        <div className="space-y-3">
          {insights.map((insight, index) => (
            <div
              key={index}
              className={`border rounded-lg p-3 ${getInsightColor(insight.type)}`}
            >
              <div className="flex items-start space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getInsightColor(insight.type).replace('border-', 'bg-').replace('-200', '-100')}`}>
                  <Icon name={insight.icon} size={16} className={getInsightIconColor(insight.type)} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-medium text-text-primary">
                      {insight.title}
                    </h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(insight.priority)}`}>
                      {insight.priority === 'high' ? 'Высокий' : 
                       insight.priority === 'medium' ? 'Средний' : 'Низкий'}
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary leading-relaxed">
                    {insight.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-6">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Icon name="Bot" size={24} className="text-gray-400" />
          </div>
          <p className="text-sm text-text-secondary">
            {studentId ? 'Недостаточно данных для анализа' : 'Выберите курс для анализа'}
          </p>
        </div>
      )}

      {analyticsData && (
        <div className="mt-4 pt-4 border-t border-border">
          <h4 className="text-sm font-medium text-text-primary mb-2">Ключевые метрики</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {studentId && analyticsData.overall_performance && (
              <>
                <div className="bg-background rounded p-2">
                  <span className="text-text-secondary">Средняя оценка:</span>
                  <div className="font-medium text-text-primary">
                    {analyticsData.overall_performance.overall_average_grade?.toFixed(1) || 0}%
                  </div>
                </div>
                <div className="bg-background rounded p-2">
                  <span className="text-text-secondary">Выполнено заданий:</span>
                  <div className="font-medium text-text-primary">
                    {analyticsData.overall_performance.total_submissions || 0}
                  </div>
                </div>
              </>
            )}
            {courseId && (
              <>
                <div className="bg-background rounded p-2">
                  <span className="text-text-secondary">Студентов:</span>
                  <div className="font-medium text-text-primary">
                    {analyticsData.total_students || 0}
                  </div>
                </div>
                <div className="bg-background rounded p-2">
                  <span className="text-text-secondary">Заданий:</span>
                  <div className="font-medium text-text-primary">
                    {analyticsData.total_assignments || 0}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAnalytics;

