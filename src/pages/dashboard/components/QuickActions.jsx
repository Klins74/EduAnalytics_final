import React from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../../../components/AppIcon';

const QuickActions = () => {
  const navigate = useNavigate();

  const actions = [
    {
      id: 'ai-analysis',
      title: 'AI Анализ',
      description: 'Запустить анализ данных студентов',
      icon: 'Bot',
      color: 'secondary',
      action: () => navigate('/ai'),
      badge: 'Новое'
    },
    {
      id: 'generate-report',
      title: 'Создать отчет',
      description: 'Сгенерировать отчет по успеваемости',
      icon: 'FileText',
      color: 'primary',
      action: () => console.log('Создание отчета...'),
      badge: null
    },
    {
      id: 'student-monitoring',
      title: 'Мониторинг студентов',
      description: 'Отслеживание активности в реальном времени',
      icon: 'Users',
      color: 'success',
      action: () => console.log('Открытие мониторинга...'),
      badge: null
    },
    {
      id: 'export-data',
      title: 'Экспорт данных',
      description: 'Выгрузить данные в Excel/CSV',
      icon: 'Download',
      color: 'accent',
      action: () => console.log('Экспорт данных...'),
      badge: null
    },
    {
      id: 'settings',
      title: 'Настройки системы',
      description: 'Конфигурация параметров',
      icon: 'Settings',
      color: 'text-secondary',
      action: () => console.log('Открытие настроек...'),
      badge: null
    },
    {
      id: 'help',
      title: 'Справка',
      description: 'Документация и поддержка',
      icon: 'HelpCircle',
      color: 'text-secondary',
      action: () => console.log('Открытие справки...'),
      badge: null
    }
  ];

  const getColorClasses = (color) => {
    const colorMap = {
      primary: 'from-primary to-primary-600',
      secondary: 'from-secondary to-purple-600',
      success: 'from-success to-emerald-600',
      accent: 'from-accent to-accent-600',
      'text-secondary': 'from-gray-400 to-gray-500'
    };
    return colorMap[color] || colorMap.primary;
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-heading font-medium text-text-primary mb-1">
            Быстрые действия
          </h3>
          <p className="text-sm text-text-secondary">
            Часто используемые функции
          </p>
        </div>
        <Icon name="Zap" size={20} className="text-accent" />
      </div>

      <div className="space-y-3">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={action.action}
            className="w-full flex items-center space-x-4 p-4 bg-background hover:bg-primary-50 border border-border-light hover:border-primary-200 rounded-lg transition-all duration-150 hover-lift text-left group"
          >
            <div className={`w-10 h-10 bg-gradient-to-br ${getColorClasses(action.color)} rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition-transform duration-150`}>
              <Icon name={action.icon} size={20} color="white" />
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h4 className="font-medium text-sm text-text-primary group-hover:text-primary transition-colors duration-150">
                  {action.title}
                </h4>
                {action.badge && (
                  <span className="px-2 py-0.5 bg-secondary text-white text-xs font-medium rounded-full">
                    {action.badge}
                  </span>
                )}
              </div>
              <p className="text-xs text-text-secondary group-hover:text-text-primary transition-colors duration-150">
                {action.description}
              </p>
            </div>
            
            <Icon 
              name="ChevronRight" 
              size={16} 
              className="text-text-muted group-hover:text-primary transition-colors duration-150 flex-shrink-0" 
            />
          </button>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-6 border-t border-border">
        <h4 className="font-medium text-sm text-text-primary mb-4">Быстрая статистика</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-background rounded-lg">
            <div className="text-lg font-semibold text-text-primary">156</div>
            <div className="text-xs text-text-secondary">Онлайн сейчас</div>
          </div>
          <div className="text-center p-3 bg-background rounded-lg">
            <div className="text-lg font-semibold text-text-primary">23</div>
            <div className="text-xs text-text-secondary">Новых заданий</div>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="mt-4 p-4 bg-gradient-to-r from-secondary-50 to-primary-50 border border-secondary-100 rounded-lg">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-gradient-to-br from-secondary to-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
            <Icon name="Lightbulb" size={16} color="white" />
          </div>
          <div>
            <h5 className="font-medium text-sm text-text-primary mb-1">AI Рекомендация</h5>
            <p className="text-xs text-text-secondary mb-2">
              Обнаружено снижение активности у 12 студентов. Рекомендуется персональное вмешательство.
            </p>
            <button 
              onClick={() => navigate('/ai')}
              className="text-xs text-secondary hover:text-secondary-500 font-medium transition-colors duration-150"
            >
              Подробнее →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;