import React, { useState } from 'react';
import Icon from '../../components/AppIcon';
import Image from '../../components/AppImage';

const StudentDetailModal = ({ student, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!student) return null;

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
    <div className="space-y-6">
      {/* Weekly Activity Chart */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Активность за неделю</h4>
        <div className="flex items-end space-x-2 h-32 mb-2">
          {student.weeklyActivity.map((activity, index) => {
            const maxActivity = Math.max(...student.weeklyActivity);
            const height = (activity / maxActivity) * 100;
            const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-primary rounded-sm opacity-80 hover:opacity-100 transition-opacity duration-150"
                  style={{ 
                    height: `${height}%`,
                    minHeight: activity > 0 ? '8px' : '2px'
                  }}
                  title={`${activity} активностей в ${days[index]}`}
                />
                <span className="text-xs text-text-muted mt-1">{days[index]}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Activities */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Последние активности</h4>
        <div className="space-y-3">
          {student.recentActivities.map((activity, index) => (
            <div key={index} className="flex items-center space-x-3 p-3 bg-background rounded-lg">
              <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center">
                <Icon 
                  name={activity.type === 'test' ? 'FileText' : activity.type === 'homework' ? 'BookOpen' : 'HelpCircle'} 
                  size={16} 
                  className="text-primary" 
                />
              </div>
              <div className="flex-1">
                <p className="font-medium text-text-primary">
                  {activity.type === 'test' ? 'Тест' : activity.type === 'homework' ? 'Домашнее задание' : 'Викторина'}
                </p>
                <p className="text-sm text-text-secondary">{activity.subject}</p>
              </div>
              <div className="text-right">
                <p className="font-medium text-text-primary">{activity.score}%</p>
                <p className="text-xs text-text-secondary">{formatLastActivity(activity.time)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPerformanceTab = () => (
    <div className="space-y-6">
      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-background rounded-lg p-4">
          <h4 className="font-medium text-text-primary mb-3">Общая успеваемость</h4>
          <div className="flex items-center space-x-3">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-text-secondary">Средний балл</span>
                <span className="font-medium text-text-primary">{student.averageScore.toFixed(1)}/5.0</span>
              </div>
              <div className="w-full h-2 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${(student.averageScore / 5) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-background rounded-lg p-4">
          <h4 className="font-medium text-text-primary mb-3">Активность</h4>
          <div className="flex items-center space-x-3">
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-text-secondary">Выполнено заданий</span>
                <span className="font-medium text-text-primary">{student.totalActivities}</span>
              </div>
              <div className="w-full h-2 bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-success rounded-full transition-all duration-300"
                  style={{ width: `${Math.min((student.totalActivities / 60) * 100, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Subject Performance */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Успеваемость по предметам</h4>
        <div className="space-y-3">
          {student.subjects.map((subject, index) => {
            const score = 3.5 + Math.random() * 1.5; // Mock score
            return (
              <div key={index} className="flex items-center justify-between p-3 bg-background rounded-lg">
                <span className="font-medium text-text-primary">{subject}</span>
                <div className="flex items-center space-x-3">
                  <div className="w-24 h-2 bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-300"
                      style={{ width: `${(score / 5) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-text-primary w-8">
                    {score.toFixed(1)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const renderAIInsightsTab = () => (
    <div className="space-y-6">
      {/* AI Risk Assessment */}
      <div className="bg-background rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-3">
          <Icon name="Bot" size={20} className="text-secondary" />
          <h4 className="font-medium text-text-primary">AI-анализ рисков</h4>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary">Общий риск</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(student.aiRiskScore)}`}>
              {getRiskLabel(student.aiRiskScore)}
            </span>
          </div>
          <div className="w-full h-2 bg-border rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${
                student.aiRiskScore < 0.3 ? 'bg-success' : 
                student.aiRiskScore < 0.7 ? 'bg-warning' : 'bg-error'
              }`}
              style={{ width: `${student.aiRiskScore * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* AI Recommendations */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Рекомендации AI</h4>
        <div className="space-y-3">
          <div className="flex items-start space-x-3 p-3 bg-primary-50 rounded-lg">
            <Icon name="Lightbulb" size={16} className="text-primary mt-0.5" />
            <div>
              <p className="text-sm font-medium text-text-primary">Увеличить взаимодействие</p>
              <p className="text-xs text-text-secondary mt-1">
                Студент показывает снижение активности. Рекомендуется индивидуальная работа.
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 p-3 bg-success-50 rounded-lg">
            <Icon name="TrendingUp" size={16} className="text-success mt-0.5" />
            <div>
              <p className="text-sm font-medium text-text-primary">Сильные стороны</p>
              <p className="text-xs text-text-secondary mt-1">
                Отличные результаты по программированию. Можно использовать как наставника.
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3 p-3 bg-warning-50 rounded-lg">
            <Icon name="AlertTriangle" size={16} className="text-warning mt-0.5" />
            <div>
              <p className="text-sm font-medium text-text-primary">Области для улучшения</p>
              <p className="text-xs text-text-secondary mt-1">
                Необходимо больше внимания математическим дисциплинам.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Behavioral Patterns */}
      <div>
        <h4 className="font-medium text-text-primary mb-3">Поведенческие паттерны</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-background rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <Icon name="Clock" size={14} className="text-primary" />
              <span className="text-sm font-medium text-text-primary">Время активности</span>
            </div>
            <p className="text-xs text-text-secondary">
              Наиболее активен в утренние часы (9:00-12:00)
            </p>
          </div>
          
          <div className="bg-background rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <Icon name="Target" size={14} className="text-primary" />
              <span className="text-sm font-medium text-text-primary">Предпочтения</span>
            </div>
            <p className="text-xs text-text-secondary">
              Предпочитает практические задания теоретическим
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-1100 flex items-center justify-center p-4">
      <div className="bg-surface rounded-lg shadow-elevated w-full max-w-4xl max-h-[90vh] overflow-hidden">
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
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'overview' && renderOverviewTab()}
          {activeTab === 'activity' && renderActivityTab()}
          {activeTab === 'performance' && renderPerformanceTab()}
          {activeTab === 'ai-insights' && renderAIInsightsTab()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-border">
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
      </div>
    </div>
  );
};

export default StudentDetailModal;