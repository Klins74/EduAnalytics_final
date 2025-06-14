import React from 'react';
import Icon from '../../../components/AppIcon';

const QuickActions = ({ onActionClick }) => {
  const quickActions = [
    {
      id: 'performance-analysis',
      title: 'Анализ успеваемости',
      description: 'Детальный анализ успеваемости студентов за выбранный период',
      icon: 'TrendingUp',
      color: 'primary',
      query: 'Проведи анализ успеваемости студентов за последний месяц'
    },
    {
      id: 'activity-report',
      title: 'Отчет по активности',
      description: 'Статистика активности и вовлеченности студентов',
      icon: 'Activity',
      color: 'success',
      query: 'Создай отчет по активности студентов с графиками'
    },
    {
      id: 'prediction-model',
      title: 'Прогнозирование результатов',
      description: 'Прогноз успеваемости на основе текущих данных',
      icon: 'Target',
      color: 'secondary',
      query: 'Построй прогноз результатов экзаменов для студентов'
    },
    {
      id: 'recommendations',
      title: 'Персональные рекомендации',
      description: 'Индивидуальные рекомендации для улучшения обучения',
      icon: 'Lightbulb',
      color: 'accent',
      query: 'Предложи персональные рекомендации для улучшения курса'
    },
    {
      id: 'pattern-analysis',
      title: 'Анализ паттернов',
      description: 'Выявление скрытых паттернов в образовательных данных',
      icon: 'Search',
      color: 'primary',
      query: 'Найди скрытые паттерны в поведении студентов'
    },
    {
      id: 'comparative-analysis',
      title: 'Сравнительный анализ',
      description: 'Сравнение показателей между группами и периодами',
      icon: 'BarChart3',
      color: 'success',
      query: 'Сравни показатели успеваемости между разными группами'
    }
  ];

  const getColorClasses = (color) => {
    const colorMap = {
      primary: 'bg-primary-50 border-primary-200 hover:bg-primary-100 text-primary',
      success: 'bg-success-50 border-success-200 hover:bg-success-100 text-success',
      secondary: 'bg-secondary-50 border-secondary-200 hover:bg-secondary-100 text-secondary',
      accent: 'bg-accent-50 border-accent-200 hover:bg-accent-100 text-accent'
    };
    return colorMap[color] || colorMap.primary;
  };

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center space-x-2">
          <Icon name="Zap" size={20} className="text-accent" />
          <h3 className="font-heading font-medium text-text-primary">Быстрые действия</h3>
        </div>
        <p className="text-sm text-text-secondary mt-1">
          Выберите готовый сценарий анализа или создайте собственный запрос
        </p>
      </div>

      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {quickActions.map((action) => (
            <button
              key={action.id}
              onClick={() => onActionClick(action.query)}
              className={`
                p-4 border-2 rounded-lg transition-all duration-200 text-left hover-lift
                ${getColorClasses(action.color)}
              `}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <Icon name={action.icon} size={24} />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-sm mb-1">{action.title}</h4>
                  <p className="text-xs opacity-80 line-clamp-2">{action.description}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Custom Query Section */}
      <div className="p-4 border-t border-border bg-background">
        <div className="flex items-center space-x-2 mb-3">
          <Icon name="Edit3" size={16} className="text-text-secondary" />
          <span className="text-sm font-medium text-text-primary">Популярные запросы</span>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {[
            'Топ-10 студентов',
            'Проблемные области',
            'Динамика по месяцам',
            'Эффективность курсов',
            'Время активности',
            'Корреляции оценок'
          ].map((query, index) => (
            <button
              key={index}
              onClick={() => onActionClick(`Анализируй ${query.toLowerCase()}`)}
              className="px-3 py-1 bg-surface border border-border rounded-full text-xs text-text-secondary hover:bg-primary-50 hover:text-primary hover:border-primary-200 transition-colors duration-150"
            >
              {query}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickActions;