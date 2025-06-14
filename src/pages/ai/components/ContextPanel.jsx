import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

const ContextPanel = ({ selectedContext, onContextChange }) => {
  const [expandedSection, setExpandedSection] = useState('overview');

  const contextData = {
    overview: {
      title: 'Обзор системы',
      data: {
        totalStudents: 1247,
        activeToday: 892,
        avgPerformance: 4.2,
        completionRate: 87,
        lastUpdate: new Date()
      }
    },
    performance: {
      title: 'Успеваемость',
      data: {
        topPerformers: [
          { name: 'Иванов А.А.', score: 4.9, trend: 'up' },
          { name: 'Петрова М.С.', score: 4.8, trend: 'up' },
          { name: 'Сидоров И.П.', score: 4.7, trend: 'stable' }
        ],
        needsAttention: [
          { name: 'Козлов Д.В.', score: 2.1, trend: 'down' },
          { name: 'Морозова Е.А.', score: 2.3, trend: 'down' }
        ]
      }
    },
    activity: {
      title: 'Активность',
      data: {
        peakHours: ['10:00-12:00', '14:00-16:00'],
        mostActive: 'Понедельник',
        leastActive: 'Пятница',
        avgSessionTime: '45 мин'
      }
    },
    insights: {
      title: 'Инсайты',
      data: {
        patterns: [
          'Студенты лучше усваивают материал в утренние часы',
          'Интерактивные задания повышают вовлеченность на 34%',
          'Групповые проекты улучшают результаты на 28%'
        ],
        recommendations: [
          'Увеличить количество практических заданий',
          'Внедрить систему peer-review',
          'Добавить геймификацию в курсы'
        ]
      }
    }
  };

  const contextTabs = [
    { id: 'overview', label: 'Обзор', icon: 'BarChart3' },
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'activity', label: 'Активность', icon: 'Activity' },
    { id: 'insights', label: 'Инсайты', icon: 'Lightbulb' }
  ];

  const formatLastUpdate = (date) => {
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return 'TrendingUp';
      case 'down': return 'TrendingDown';
      default: return 'Minus';
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up': return 'text-success';
      case 'down': return 'text-error';
      default: return 'text-text-secondary';
    }
  };

  return (
    <div className="space-y-4">
      {/* Context Tabs */}
      <div className="bg-surface border border-border rounded-lg shadow-card">
        <div className="p-4 border-b border-border">
          <h3 className="font-heading font-medium text-text-primary mb-3">Контекстные данные</h3>
          <div className="grid grid-cols-2 gap-2">
            {contextTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onContextChange(tab.id)}
                className={`flex items-center space-x-2 p-2 rounded-lg transition-colors duration-150 text-sm ${
                  selectedContext === tab.id
                    ? 'bg-primary text-white' :'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
                }`}
              >
                <Icon name={tab.icon} size={16} />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Context Content */}
        <div className="p-4">
          {selectedContext === 'overview' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-2xl font-bold text-primary">
                    {contextData.overview.data.totalStudents.toLocaleString('ru-RU')}
                  </div>
                  <div className="text-xs text-text-secondary">Всего студентов</div>
                </div>
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-2xl font-bold text-success">
                    {contextData.overview.data.activeToday}
                  </div>
                  <div className="text-xs text-text-secondary">Активны сегодня</div>
                </div>
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-2xl font-bold text-accent">
                    {contextData.overview.data.avgPerformance}
                  </div>
                  <div className="text-xs text-text-secondary">Средний балл</div>
                </div>
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-2xl font-bold text-secondary">
                    {contextData.overview.data.completionRate}%
                  </div>
                  <div className="text-xs text-text-secondary">Завершение</div>
                </div>
              </div>
              <div className="text-xs text-text-muted">
                Обновлено: {formatLastUpdate(contextData.overview.data.lastUpdate)}
              </div>
            </div>
          )}

          {selectedContext === 'performance' && (
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-text-primary mb-2 text-sm">Лучшие студенты</h4>
                <div className="space-y-2">
                  {contextData.performance.data.topPerformers.map((student, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-background rounded">
                      <span className="text-sm text-text-primary">{student.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-text-primary">{student.score}</span>
                        <Icon 
                          name={getTrendIcon(student.trend)} 
                          size={12} 
                          className={getTrendColor(student.trend)} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-text-primary mb-2 text-sm">Требуют внимания</h4>
                <div className="space-y-2">
                  {contextData.performance.data.needsAttention.map((student, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-error-50 rounded">
                      <span className="text-sm text-text-primary">{student.name}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-error">{student.score}</span>
                        <Icon 
                          name={getTrendIcon(student.trend)} 
                          size={12} 
                          className={getTrendColor(student.trend)} 
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {selectedContext === 'activity' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-3">
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-sm font-medium text-text-primary mb-1">Пиковые часы</div>
                  <div className="text-xs text-text-secondary">
                    {contextData.activity.data.peakHours.join(', ')}
                  </div>
                </div>
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-sm font-medium text-text-primary mb-1">Самый активный день</div>
                  <div className="text-xs text-success">{contextData.activity.data.mostActive}</div>
                </div>
                <div className="bg-background p-3 rounded-lg">
                  <div className="text-sm font-medium text-text-primary mb-1">Средняя сессия</div>
                  <div className="text-xs text-text-secondary">{contextData.activity.data.avgSessionTime}</div>
                </div>
              </div>
            </div>
          )}

          {selectedContext === 'insights' && (
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-text-primary mb-2 text-sm">Выявленные паттерны</h4>
                <div className="space-y-2">
                  {contextData.insights.data.patterns.map((pattern, index) => (
                    <div key={index} className="flex items-start space-x-2 p-2 bg-background rounded">
                      <Icon name="TrendingUp" size={12} className="text-primary mt-0.5 flex-shrink-0" />
                      <span className="text-xs text-text-secondary">{pattern}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-medium text-text-primary mb-2 text-sm">Рекомендации</h4>
                <div className="space-y-2">
                  {contextData.insights.data.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-2 p-2 bg-accent-50 rounded">
                      <Icon name="Lightbulb" size={12} className="text-accent mt-0.5 flex-shrink-0" />
                      <span className="text-xs text-text-secondary">{recommendation}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Updates */}
      <div className="bg-surface border border-border rounded-lg shadow-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-text-primary text-sm">Обновления в реальном времени</h4>
          <div className="w-2 h-2 bg-success rounded-full ai-pulse" />
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center space-x-2 p-2 bg-background rounded text-xs">
            <Icon name="User" size={12} className="text-primary" />
            <span className="text-text-secondary">Студент Иванов И.И. завершил тест</span>
            <span className="text-text-muted ml-auto">2 мин</span>
          </div>
          <div className="flex items-center space-x-2 p-2 bg-background rounded text-xs">
            <Icon name="BookOpen" size={12} className="text-success" />
            <span className="text-text-secondary">Новый материал добавлен в курс</span>
            <span className="text-text-muted ml-auto">5 мин</span>
          </div>
          <div className="flex items-center space-x-2 p-2 bg-background rounded text-xs">
            <Icon name="AlertTriangle" size={12} className="text-warning" />
            <span className="text-text-secondary">Низкая активность в группе ИТ-22</span>
            <span className="text-text-muted ml-auto">8 мин</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextPanel;