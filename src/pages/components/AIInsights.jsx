import React, { useState, useEffect } from 'react';
import Icon from '../../components/AppIcon';
import { getAiInsights } from '../../api/mockApi.js';

const AIInsights = ({ activeTab }) => {
  const [insights, setInsights] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchInsights = async () => {
      setIsLoading(true);
      try {
        const newInsights = await getAiInsights(activeTab);
        setInsights(newInsights);
      } catch (error) {
        console.error("Ошибка загрузки AI инсайтов:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInsights();
  }, [activeTab]); // Зависимость от activeTab

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
    performance: [ { label: 'Средний балл', value: '4,05', change: '+0,15', positive: true }, { label: 'Отличников', value: '245', change: '+12', positive: true }, { label: 'Неуспевающих', value: '34', change: '-8', positive: true } ],
    engagement: [ { label: 'Активность', value: '84,2%', change: '+3,2%', positive: true }, { label: 'Время в системе', value: '5ч 23м', change: '+32м', positive: true }, { label: 'Низкая активность', value: '23', change: '-5', positive: true } ],
    predictions: [ { label: 'Точность модели', value: '87,3%', change: '+2,1%', positive: true }, { label: 'Группа риска', value: '23', change: '-5', positive: true }, { label: 'Потенциал роста', value: '45', change: '+8', positive: true } ],
    comparative: [ { label: 'Лучший класс', value: '11А', change: '4,5', positive: true }, { label: 'Разрыв', value: '0,6', change: '-0,2', positive: true }, { label: 'Улучшений', value: '4/6', change: '+2', positive: true } ]
  };

  const currentMetrics = keyMetrics[activeTab] || [];

  return (
    <div className="space-y-6">
      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
            <Icon name="Brain" size={20} color="white" />
          </div>
          <div>
            <h3 className="font-heading font-medium text-text-primary">AI-Аналитик</h3>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-warning animate-pulse' : 'bg-success'}`} />
              <span className="text-sm text-text-secondary">{isLoading ? 'Анализирует...' : 'Активен'}</span>
            </div>
          </div>
        </div>
        <div className="text-sm text-text-secondary">
          Последний анализ: {new Date().toLocaleString('ru-RU')}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-4">
        <h3 className="font-heading font-medium text-text-primary mb-4">Ключевые метрики</h3>
        <div className="space-y-3">
          {currentMetrics.map((metric, index) => (
            <div key={index} className="flex items-center justify-between">
              <span className="text-sm text-text-secondary">{metric.label}</span>
              <div className="text-right">
                <div className="font-semibold text-text-primary">{metric.value}</div>
                <div className={`text-xs flex items-center space-x-1 ${metric.positive ? 'text-success' : 'text-error'}`}>
                  <Icon name={metric.positive ? "ArrowUp" : "ArrowDown"} size={12} />
                  <span>{metric.change}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading font-medium text-text-primary">AI-Инсайты</h3>
        </div>

        {isLoading ? (
          <div className="space-y-4 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="p-3 border border-gray-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200"></div>
                  <div className="flex-1 space-y-2 py-1">
                    <div className="h-3 bg-gray-200 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
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
                      <h4 className="font-medium text-sm text-text-primary truncate">{insight.title}</h4>
                      <span className="text-xs text-text-muted ml-2">{insight.confidence}%</span>
                    </div>
                    <p className="text-xs text-text-secondary mb-2 leading-relaxed">{insight.content}</p>
                    {insight.recommendation && (
                      <div className="bg-background rounded p-2 mb-2">
                        <div className="flex items-start space-x-2">
                          <Icon name="Lightbulb" size={12} className="text-accent mt-0.5 flex-shrink-0" />
                          <p className="text-xs text-text-secondary">{insight.recommendation}</p>
                        </div>
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded-full ${getInsightColor(insight.priority)}`}>{getPriorityLabel(insight.priority)}</span>
                      {insight.actionable && (<button className="text-xs text-primary hover:text-primary-700 font-medium">Действие</button>)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AIInsights;