import React, { useState, useEffect } from 'react';
import Icon from '../../components/AppIcon';

const AIInsights = ({ activeTab, period }) => {
  const [insights, setInsights] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    generateInsights();
  }, [activeTab, period]);

  const generateInsights = () => {
    setIsLoading(true);
    
    // Simulate AI processing
    setTimeout(() => {
      const newInsights = getInsightsForTab(activeTab);
      setInsights(newInsights);
      setIsLoading(false);
    }, 1500);
  };

  const getInsightsForTab = (tab) => {
    const insightsByTab = {
      performance: [
        {
          id: 1,
          type: 'trend',
          title: 'Положительная динамика',
          content: `Средний балл по математике вырос на 0,3 пункта за последний месяц. Это связано с внедрением новых интерактивных методов обучения.`,
          confidence: 92,
          priority: 'high',
          actionable: true,
          recommendation: 'Рекомендуется распространить успешные методики на другие предметы'
        },
        {
          id: 2,
          type: 'alert',
          title: 'Снижение в 10В классе',
          content: `Обнаружено снижение успеваемости в 10В классе на 0,2 балла. Основная причина - увеличение количества пропусков занятий.`,
          confidence: 87,
          priority: 'medium',
          actionable: true,
          recommendation: 'Провести индивидуальные беседы с отстающими студентами'
        },
        {
          id: 3,
          type: 'prediction',
          title: 'Прогноз на следующий месяц',
          content: `С вероятностью 85% ожидается улучшение общей успеваемости на 0,15 балла при сохранении текущих тенденций.`,
          confidence: 85,
          priority: 'low',
          actionable: false,
          recommendation: null
        }
      ],
      engagement: [
        {
          id: 4,
          type: 'insight',
          title: 'Пиковая активность',
          content: `Максимальная вовлеченность студентов наблюдается в среду с 10:00 до 12:00. В это время активность на 23% выше среднего.`,
          confidence: 94,
          priority: 'high',
          actionable: true,
          recommendation: 'Планировать сложные темы на время пиковой активности'
        },
        {
          id: 5,
          type: 'alert',
          title: 'Снижение в выходные',
          content: `Активность студентов в выходные дни упала на 35%. Это может указывать на недостаток мотивации к самостоятельному обучению.`,
          confidence: 89,
          priority: 'medium',
          actionable: true,
          recommendation: 'Внедрить геймификацию для поддержания интереса'
        },
        {
          id: 6,
          type: 'pattern',
          title: 'Корреляция с погодой',
          content: `Обнаружена слабая корреляция между вовлеченностью и погодными условиями. В солнечные дни активность выше на 8%.`,
          confidence: 73,
          priority: 'low',
          actionable: false,
          recommendation: null
        }
      ],
      predictions: [
        {
          id: 7,
          type: 'prediction',
          title: 'Риск неуспеваемости',
          content: `Модель выявила 23 студента с высоким риском снижения успеваемости в следующем месяце. Точность прогноза 91%.`,
          confidence: 91,
          priority: 'high',
          actionable: true,
          recommendation: 'Немедленно начать индивидуальную работу с группой риска'
        },
        {
          id: 8,
          type: 'forecast',
          title: 'Сезонные изменения',
          content: `Ожидается традиционное снижение активности на 12-15% в период весенних каникул. Рекомендуется подготовить дополнительные мотивационные материалы.`,
          confidence: 88,
          priority: 'medium',
          actionable: true,
          recommendation: 'Подготовить интерактивные задания на каникулы'
        },
        {
          id: 9,
          type: 'opportunity',
          title: 'Потенциал роста',
          content: `Выявлено 45 студентов со скрытым потенциалом для перехода в категорию отличников при правильной мотивации.`,
          confidence: 82,
          priority: 'medium',
          actionable: true,
          recommendation: 'Создать программу развития для талантливых студентов'
        }
      ],
      comparative: [
        {
          id: 10,
          type: 'comparison',
          title: 'Лидер по эффективности',
          content: `11А класс показывает лучшие результаты по всем метрикам. Их методы можно адаптировать для других классов.`,
          confidence: 95,
          priority: 'high',
          actionable: true,
          recommendation: 'Провести мастер-класс с преподавателем 11А класса'
        },
        {
          id: 11,
          type: 'gap',
          title: 'Значительный разрыв',
          content: `Разрыв в успеваемости между лучшим и худшим классом составляет 0,6 балла. Это выше нормального диапазона.`,
          confidence: 93,
          priority: 'medium',
          actionable: true,
          recommendation: 'Разработать план выравнивания уровня знаний'
        },
        {
          id: 12,
          type: 'trend',
          title: 'Улучшение динамики',
          content: `За последние 3 месяца разрыв между классами сократился на 0,2 балла, что указывает на эффективность принятых мер.`,
          confidence: 87,
          priority: 'low',
          actionable: false,
          recommendation: null
        }
      ]
    };

    return insightsByTab[tab] || [];
  };

  const getInsightIcon = (type) => {
    switch (type) {
      case 'trend': return 'TrendingUp';
      case 'alert': return 'AlertTriangle';
      case 'prediction': return 'Target';
      case 'insight': return 'Lightbulb';
      case 'pattern': return 'GitBranch';
      case 'forecast': return 'CloudRain';
      case 'opportunity': return 'Star';
      case 'comparison': return 'BarChart3';
      case 'gap': return 'Gap';
      default: return 'Brain';
    }
  };

  const getInsightColor = (priority) => {
    switch (priority) {
      case 'high': return 'border-error bg-error-50 text-error';
      case 'medium': return 'border-warning bg-warning-50 text-warning';
      case 'low': return 'border-primary bg-primary-50 text-primary';
      default: return 'border-border bg-background text-text-secondary';
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 'high': return 'Высокий приоритет';
      case 'medium': return 'Средний приоритет';
      case 'low': return 'Низкий приоритет';
      default: return 'Информационный';
    }
  };

  const keyMetrics = {
    performance: [
      { label: 'Средний балл', value: '4,05', change: '+0,15', positive: true },
      { label: 'Отличников', value: '245', change: '+12', positive: true },
      { label: 'Неуспевающих', value: '34', change: '-8', positive: true }
    ],
    engagement: [
      { label: 'Активность', value: '84,2%', change: '+3,2%', positive: true },
      { label: 'Время в системе', value: '5ч 23м', change: '+32м', positive: true },
      { label: 'Низкая активность', value: '23', change: '-5', positive: true }
    ],
    predictions: [
      { label: 'Точность модели', value: '87,3%', change: '+2,1%', positive: true },
      { label: 'Группа риска', value: '23', change: '-5', positive: true },
      { label: 'Потенциал роста', value: '45', change: '+8', positive: true }
    ],
    comparative: [
      { label: 'Лучший класс', value: '11А', change: '4,5', positive: true },
      { label: 'Разрыв', value: '0,6', change: '-0,2', positive: true },
      { label: 'Улучшений', value: '4/6', change: '+2', positive: true }
    ]
  };

  const currentMetrics = keyMetrics[activeTab] || [];

  return (
    <div className="space-y-6">
      {/* AI Status */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
            <Icon name="Brain" size={20} color="white" />
          </div>
          <div>
            <h3 className="font-heading font-medium text-text-primary">AI-Аналитик</h3>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success rounded-full ai-pulse" />
              <span className="text-sm text-text-secondary">Активен</span>
            </div>
          </div>
        </div>
        
        <div className="text-sm text-text-secondary">
          Последний анализ: {new Date().toLocaleString('ru-RU')}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h3 className="font-heading font-medium text-text-primary mb-4">Ключевые метрики</h3>
        
        <div className="space-y-3">
          {currentMetrics.map((metric, index) => (
            <div key={index} className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">{metric.label}</span>
              <div className="text-right">
                <div className="font-semibold text-text-primary">{metric.value}</div>
                <div className={`text-xs flex items-center space-x-1 ${
                  metric.positive ? 'text-success' : 'text-error'
                }`}>
                  <Icon 
                    name={metric.positive ? "ArrowUp" : "ArrowDown"} 
                    size={12} 
                  />
                  <span>{metric.change}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading font-medium text-text-primary">AI-Инсайты</h3>
          <button
            onClick={generateInsights}
            disabled={isLoading}
            className="flex items-center space-x-1 text-sm text-primary hover:text-primary-700 disabled:opacity-50"
          >
            <Icon 
              name="RefreshCw" 
              size={14} 
              className={isLoading ? 'animate-spin' : ''} 
            />
            <span>Обновить</span>
          </button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-border rounded w-3/4 mb-2" />
                <div className="h-3 bg-border rounded w-full mb-1" />
                <div className="h-3 bg-border rounded w-2/3" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {insights.map((insight) => (
              <div key={insight.id} className="border border-border rounded-lg p-3">
                <div className="flex items-start space-x-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${getInsightColor(insight.priority)}`}>
                    <Icon name={getInsightIcon(insight.type)} size={14} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-sm text-text-primary truncate">
                        {insight.title}
                      </h4>
                      <span className="text-xs text-text-muted ml-2">
                        {insight.confidence}%
                      </span>
                    </div>
                    
                    <p className="text-xs text-text-secondary mb-2 leading-relaxed">
                      {insight.content}
                    </p>
                    
                    {insight.recommendation && (
                      <div className="bg-background rounded p-2 mb-2">
                        <div className="flex items-start space-x-2">
                          <Icon name="Lightbulb" size={12} className="text-accent mt-0.5 flex-shrink-0" />
                          <p className="text-xs text-text-secondary">
                            {insight.recommendation}
                          </p>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded-full ${getInsightColor(insight.priority)}`}>
                        {getPriorityLabel(insight.priority)}
                      </span>
                      
                      {insight.actionable && (
                        <button className="text-xs text-primary hover:text-primary-700 font-medium">
                          Действие
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <h3 className="font-heading font-medium text-text-primary mb-4">Быстрые действия</h3>
        
        <div className="space-y-2">
          <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150 text-sm">
            <Icon name="FileText" size={14} className="text-text-secondary" />
            <span className="text-text-secondary">Создать отчет</span>
          </button>
          
          <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150 text-sm">
            <Icon name="Bell" size={14} className="text-text-secondary" />
            <span className="text-text-secondary">Настроить уведомления</span>
          </button>
          
          <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150 text-sm">
            <Icon name="Download" size={14} className="text-text-secondary" />
            <span className="text-text-secondary">Экспорт данных</span>
          </button>
          
          <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150 text-sm">
            <Icon name="Settings" size={14} className="text-text-secondary" />
            <span className="text-text-secondary">Настройки AI</span>
          </button>
        </div>
      </div>

      {/* AI Tips */}
      <div className="bg-gradient-to-br from-secondary-50 to-primary-50 border border-secondary-100 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
            <Icon name="Sparkles" size={16} color="white" />
          </div>
          <div>
            <h4 className="font-medium text-secondary mb-1">Совет дня</h4>
            <p className="text-sm text-text-secondary">
              Используйте корреляционный анализ для выявления скрытых связей между 
              различными метриками успеваемости и поведенческими паттернами студентов.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIInsights;