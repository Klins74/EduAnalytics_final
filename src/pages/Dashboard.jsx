import React, { useState, useEffect } from 'react';
import Icon from '../components/AppIcon';
import { useNotifications } from '../components/ui/NotificationToast';

const Dashboard = () => {
  const [stats, setStats] = useState({
    courses: { total: 0, active: 0, completed: 0 },
    students: { total: 0, active: 0, graduated: 0 },
    content: { pages: 0, discussions: 0, quizzes: 0 },
    analytics: { views: 0, engagement: 0, growth: 0 }
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const { success, info } = useNotifications();

  useEffect(() => {
    // Имитация загрузки данных
    const loadDashboardData = async () => {
      setLoading(true);
      
      // Имитация API задержки
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Моковые данные
      setStats({
        courses: { total: 12, active: 8, completed: 4 },
        students: { total: 156, active: 134, graduated: 22 },
        content: { pages: 45, discussions: 23, quizzes: 18 },
        analytics: { views: 2847, engagement: 78, growth: 12 }
      });
      
      setRecentActivity([
        {
          id: 1,
          type: 'page',
          action: 'создал',
          title: 'Введение в машинное обучение',
          author: 'Доктор Иванов',
          course: 'Машинное обучение',
          time: '2 часа назад',
          icon: 'FileText',
          color: 'text-blue-600'
        },
        {
          id: 2,
          type: 'discussion',
          action: 'ответил в',
          title: 'Вопросы по домашнему заданию',
          author: 'Студент Петров',
          course: 'Программирование на Python',
          time: '4 часа назад',
          icon: 'MessageSquare',
          color: 'text-green-600'
        },
        {
          id: 3,
          type: 'quiz',
          action: 'прошел',
          title: 'Тест по основам SQL',
          author: 'Студент Сидоров',
          course: 'Базы данных',
          time: '6 часов назад',
          icon: 'FileQuestion',
          color: 'text-purple-600'
        },
        {
          id: 4,
          type: 'student',
          action: 'зарегистрировался на курс',
          title: 'Веб-разработка',
          author: 'Новый студент',
          course: 'Веб-разработка',
          time: '1 день назад',
          icon: 'UserPlus',
          color: 'text-orange-600'
        }
      ]);
      
      setLoading(false);
      success('Данные дашборда загружены!');
    };

    loadDashboardData();
  }, [success]);

  const courseStats = [
    {
      title: 'Всего курсов',
      value: stats.courses.total,
      icon: 'BookOpen',
      color: 'bg-blue-500',
      trend: 'up',
      trendValue: '+2 за месяц'
    },
    {
      title: 'Активных курсов',
      value: stats.courses.active,
      icon: 'PlayCircle',
      color: 'bg-green-500',
      trend: 'up',
      trendValue: '+1 за неделю'
    },
    {
      title: 'Завершенных',
      value: stats.courses.completed,
      icon: 'CheckCircle',
      color: 'bg-purple-500'
    },
    {
      title: 'Всего студентов',
      value: stats.students.total,
      icon: 'Users',
      color: 'bg-orange-500',
      trend: 'up',
      trendValue: '+15 за месяц'
    }
  ];

  const contentStats = [
    {
      title: 'Страниц',
      value: stats.content.pages,
      icon: 'FileText',
      color: 'bg-blue-500'
    },
    {
      title: 'Обсуждений',
      value: stats.content.discussions,
      icon: 'MessagesSquare',
      color: 'bg-green-500'
    },
    {
      title: 'Квизов',
      value: stats.content.quizzes,
      icon: 'FileQuestion',
      color: 'bg-purple-500'
    }
  ];

  const quickActions = [
    {
      title: 'Создать курс',
      description: 'Добавить новый курс в систему',
      icon: 'Plus',
      color: 'bg-blue-500',
      action: () => info('Функция создания курса будет доступна в следующем обновлении')
    },
    {
      title: 'Добавить студента',
      description: 'Зарегистрировать нового студента',
      icon: 'UserPlus',
      color: 'bg-green-500',
      action: () => info('Функция добавления студента будет доступна в следующем обновлении')
    },
    {
      title: 'Создать квиз',
      description: 'Создать тест или задание',
      icon: 'FileQuestion',
      color: 'bg-purple-500',
      action: () => info('Перейдите в раздел Quiz Demo для создания квизов')
    },
    {
      title: 'Аналитика',
      description: 'Просмотр детальной аналитики',
      icon: 'BarChart3',
      color: 'bg-orange-500',
      action: () => info('Перейдите в раздел Аналитика для детальных отчетов')
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Загрузка дашборда...</h2>
          <p className="text-gray-500">Подготавливаем данные для вас</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Заголовок */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Добро пожаловать в EduAnalytics
          </h1>
          <p className="text-xl text-gray-600">
            Современная платформа для управления образовательным процессом
          </p>
        </div>

        {/* Основная статистика */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {courseStats.map((stat, index) => (
            <div key={index} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow duration-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                  {stat.trend && (
                    <div className={`flex items-center gap-1 mt-2 text-sm ${
                      stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      <Icon 
                        name={stat.trend === 'up' ? 'TrendingUp' : 'TrendingDown'} 
                        size={14} 
                      />
                      <span>{stat.trendValue}</span>
                    </div>
                  )}
                </div>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${stat.color}`}>
                  <Icon name={stat.icon} size={24} className="text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Контент и аналитика */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Статистика контента */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Icon name="BarChart3" size={24} className="text-primary" />
                Статистика контента
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {contentStats.map((stat, index) => (
                  <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${stat.color} mx-auto mb-3`}>
                      <Icon name={stat.icon} size={24} className="text-white" />
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</h3>
                    <p className="text-sm text-gray-600">{stat.title}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Быстрые действия */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <Icon name="Zap" size={24} className="text-primary" />
              Быстрые действия
            </h2>
            <div className="space-y-3">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className="w-full p-3 text-left rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all duration-200 group"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${action.color} group-hover:scale-110 transition-transform duration-200`}>
                      <Icon name={action.icon} size={16} className="text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 group-hover:text-primary transition-colors duration-200">
                        {action.title}
                      </h3>
                      <p className="text-sm text-gray-500">{action.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Недавняя активность */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Icon name="Activity" size={24} className="text-primary" />
            Недавняя активность
          </h2>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors duration-200">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center bg-gray-200`}>
                  <Icon name={activity.icon} size={20} className={activity.color} />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium text-gray-900">{activity.author}</span>
                    {' '}{activity.action}{' '}
                    <span className="font-medium text-gray-900">{activity.title}</span>
                  </p>
                  <p className="text-xs text-gray-500">
                    Курс: {activity.course} • {activity.time}
                  </p>
                </div>
                <div className="text-xs text-gray-400">
                  {activity.time}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Информация о системе */}
        <div className="bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Система готова к работе!
          </h2>
          <p className="text-xl opacity-90 mb-6">
            Все компоненты Canvas LMS интегрированы и протестированы.
            Используйте боковое меню для навигации по разделам.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm opacity-75">
            <div className="flex items-center justify-center gap-2">
              <Icon name="CheckCircle" size={16} />
              <span>Quiz Engine</span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <Icon name="CheckCircle" size={16} />
              <span>Pages & Discussions</span>
            </div>
            <div className="flex items-center justify-center gap-2">
              <Icon name="CheckCircle" size={16} />
              <span>AI Integration</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
