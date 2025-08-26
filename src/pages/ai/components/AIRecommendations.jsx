import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';

const AIRecommendations = ({ courseId, studentId }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    if (courseId || studentId) {
      generateRecommendations();
    }
  }, [courseId, studentId]);

  const generateRecommendations = async () => {
    try {
      setLoading(true);
      
      let analyticsData = null;
      
      if (courseId) {
        // Получаем аналитику курса
        const response = await fetch(`http://localhost:8000/api/analytics/courses/${courseId}/overview`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          analyticsData = await response.json();
        }
      } else if (studentId) {
        // Получаем аналитику студента
        const response = await fetch(`http://localhost:8000/api/analytics/students/${studentId}/performance`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
          }
        });
        
        if (response.ok) {
          analyticsData = await response.json();
        }
      }

      if (analyticsData) {
        const generatedRecs = generateCourseRecommendations(analyticsData);
        setRecommendations(generatedRecs);
      }
    } catch (error) {
      console.error('Error generating recommendations:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateCourseRecommendations = (data) => {
    const recs = [];

    if (courseId && data) {
      // Рекомендации для курса
      const { total_students, total_assignments, average_grade } = data;
      
      if (average_grade < 70) {
        recs.push({
          id: 1,
          category: 'performance',
          title: 'Улучшить методику преподавания',
          description: 'Средняя успеваемость ниже ожидаемой. Рекомендуется пересмотреть подход к объяснению материала.',
          impact: 'high',
          effort: 'medium',
          timeline: '2-3 недели',
          icon: 'BookOpen',
          actions: [
            'Добавить больше практических примеров',
            'Использовать интерактивные методы обучения',
            'Внедрить систему обратной связи'
          ]
        });
      }

      if (total_assignments < 5) {
        recs.push({
          id: 2,
          category: 'engagement',
          title: 'Увеличить количество заданий',
          description: 'Недостаточно заданий для закрепления материала. Рекомендуется добавить разнообразные типы работ.',
          impact: 'medium',
          effort: 'low',
          timeline: '1 неделя',
          icon: 'FileText',
          actions: [
            'Добавить домашние задания',
            'Создать проектные работы',
            'Включить тесты для самопроверки'
          ]
        });
      }

      if (total_students > 30) {
        recs.push({
          id: 3,
          category: 'management',
          title: 'Оптимизировать управление большими группами',
          description: 'Большое количество студентов требует особого подхода к организации учебного процесса.',
          impact: 'medium',
          effort: 'high',
          timeline: '3-4 недели',
          icon: 'Users',
          actions: [
            'Разделить на подгруппы',
            'Внедрить систему peer-review',
            'Использовать групповые проекты'
          ]
        });
      }

      // Общие рекомендации для курса
      recs.push({
        id: 4,
        category: 'general',
        title: 'Добавить геймификацию',
        description: 'Внедрение элементов игры может повысить мотивацию и вовлеченность студентов.',
        impact: 'high',
        effort: 'medium',
        timeline: '2-3 недели',
        icon: 'Gamepad2',
        actions: [
          'Система баллов и достижений',
          'Рейтинги и соревнования',
          'Интерактивные квесты'
        ]
      });

    } else if (studentId && data) {
      // Рекомендации для студента
      const { overall_performance, courses_performance } = data;
      
      if (overall_performance.overall_average_grade < 75) {
        recs.push({
          id: 1,
          category: 'study',
          title: 'Улучшить стратегию обучения',
          description: 'Текущие результаты показывают необходимость изменения подхода к учебе.',
          impact: 'high',
          effort: 'medium',
          timeline: '2-4 недели',
          icon: 'Target',
          actions: [
            'Составить детальный план обучения',
            'Выделить больше времени на сложные темы',
            'Использовать различные методы запоминания'
          ]
        });
      }

      if (courses_performance) {
        const weakCourses = courses_performance.filter(course => course.average_grade < 70);
        if (weakCourses.length > 0) {
          recs.push({
            id: 2,
            category: 'subjects',
            title: 'Фокус на слабых предметах',
            description: `Выявлено ${weakCourses.length} курсов, требующих дополнительного внимания.`,
            impact: 'high',
            effort: 'high',
            timeline: '4-6 недель',
            icon: 'AlertTriangle',
            actions: [
              'Дополнительные занятия по проблемным темам',
              'Поиск дополнительных ресурсов',
              'Обращение за помощью к преподавателям'
            ]
          });
        }
      }

      // Рекомендации по тайм-менеджменту
      recs.push({
        id: 3,
        category: 'time',
        title: 'Оптимизировать расписание',
        description: 'Эффективное планирование времени поможет улучшить результаты обучения.',
        impact: 'medium',
        effort: 'low',
        timeline: '1 неделя',
        icon: 'Clock',
        actions: [
          'Составить еженедельное расписание',
          'Выделить приоритетные задачи',
          'Использовать техники Pomodoro'
        ]
      });
    }

    return recs;
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'performance': return 'border-blue-200 bg-blue-50';
      case 'engagement': return 'border-green-200 bg-green-50';
      case 'management': return 'border-purple-200 bg-purple-50';
      case 'general': return 'border-orange-200 bg-orange-50';
      case 'study': return 'border-indigo-200 bg-indigo-50';
      case 'subjects': return 'border-red-200 bg-red-50';
      case 'time': return 'border-yellow-200 bg-yellow-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getEffortColor = (effort) => {
    switch (effort) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const categories = [
    { id: 'all', label: 'Все', icon: 'List' },
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'engagement', label: 'Вовлеченность', icon: 'Users' },
    { id: 'management', label: 'Управление', icon: 'Settings' },
    { id: 'study', label: 'Обучение', icon: 'BookOpen' },
    { id: 'subjects', label: 'Предметы', icon: 'FileText' },
    { id: 'time', label: 'Время', icon: 'Clock' }
  ];

  const filteredRecommendations = selectedCategory === 'all' 
    ? recommendations 
    : recommendations.filter(rec => rec.category === selectedCategory);

  if (loading) {
    return (
      <div className="bg-surface border border-border rounded-lg shadow-card p-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading font-medium text-text-primary">AI-рекомендации</h3>
        <div className="flex items-center space-x-2">
          <Icon name="Lightbulb" size={16} className="text-yellow-500" />
          <span className="text-xs text-text-secondary">AI-powered</span>
        </div>
      </div>

      {/* Фильтры по категориям */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category.id)}
              className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors duration-150 ${
                selectedCategory === category.id
                  ? 'bg-primary text-white'
                  : 'bg-background text-text-secondary hover:bg-primary-50'
              }`}
            >
              <Icon name={category.icon} size={12} />
              <span>{category.label}</span>
            </button>
          ))}
        </div>
      </div>

      {filteredRecommendations.length > 0 ? (
        <div className="space-y-4">
          {filteredRecommendations.map((recommendation) => (
            <div
              key={recommendation.id}
              className={`border rounded-lg p-4 ${getCategoryColor(recommendation.category)}`}
            >
              <div className="flex items-start space-x-3 mb-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getCategoryColor(recommendation.category).replace('border-', 'bg-').replace('-200', '-100')}`}>
                  <Icon name={recommendation.icon} size={18} className="text-text-primary" />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-text-primary mb-1">
                    {recommendation.title}
                  </h4>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {recommendation.description}
                  </p>
                </div>
              </div>

              {/* Метаданные рекомендации */}
              <div className="flex items-center space-x-3 mb-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(recommendation.impact)}`}>
                  Влияние: {recommendation.impact === 'high' ? 'Высокое' : 
                           recommendation.impact === 'medium' ? 'Среднее' : 'Низкое'}
                </span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getEffortColor(recommendation.effort)}`}>
                  Усилия: {recommendation.effort === 'high' ? 'Высокие' : 
                          recommendation.effort === 'medium' ? 'Средние' : 'Низкие'}
                </span>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-600">
                  Срок: {recommendation.timeline}
                </span>
              </div>

              {/* Конкретные действия */}
              <div className="bg-background rounded-lg p-3">
                <h5 className="text-sm font-medium text-text-primary mb-2">Конкретные действия:</h5>
                <ul className="space-y-1">
                  {recommendation.actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-2 text-sm text-text-secondary">
                      <Icon name="CheckCircle" size={14} className="text-success mt-0.5 flex-shrink-0" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Icon name="CheckCircle" size={24} className="text-gray-400" />
          </div>
          <p className="text-sm text-text-secondary">
            {selectedCategory === 'all' 
              ? 'Нет рекомендаций для отображения'
              : `Нет рекомендаций в категории "${categories.find(c => c.id === selectedCategory)?.label}"`
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default AIRecommendations;

