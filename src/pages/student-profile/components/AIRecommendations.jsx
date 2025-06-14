import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

const AIRecommendations = ({ recommendations }) => {
  const [expandedCard, setExpandedCard] = useState(null);

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'border-error bg-error-50 text-error';
      case 'medium':
        return 'border-warning bg-warning-50 text-warning';
      case 'low':
        return 'border-success bg-success-50 text-success';
      default:
        return 'border-border bg-background text-text-secondary';
    }
  };

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 'high':
        return 'Высокий приоритет';
      case 'medium':
        return 'Средний приоритет';
      case 'low':
        return 'Низкий приоритет';
      default:
        return 'Обычный';
    }
  };

  const getRecommendationTypeIcon = (type) => {
    switch (type) {
      case 'improvement':
        return 'TrendingUp';
      case 'strength':
        return 'Award';
      case 'schedule':
        return 'Clock';
      default:
        return 'Lightbulb';
    }
  };

  const toggleExpanded = (id) => {
    setExpandedCard(expandedCard === id ? null : id);
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
            <Icon name="Bot" size={16} color="white" />
          </div>
          <h3 className="text-lg font-heading font-semibold text-text-primary">
            AI-Рекомендации
          </h3>
        </div>
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 bg-secondary rounded-full ai-pulse" />
          <span className="text-xs text-text-secondary">Обновлено сейчас</span>
        </div>
      </div>

      <div className="space-y-4">
        {recommendations.map((recommendation) => (
          <div
            key={recommendation.id}
            className="border border-border rounded-lg p-4 hover:shadow-card transition-all duration-150 hover-lift"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon 
                    name={getRecommendationTypeIcon(recommendation.type)} 
                    size={18} 
                    className="text-primary" 
                  />
                </div>
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-text-primary mb-1">
                    {recommendation.title}
                  </h4>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(recommendation.priority)}`}>
                      {getPriorityLabel(recommendation.priority)}
                    </span>
                    <span className="text-xs text-text-muted">
                      {recommendation.subject}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => toggleExpanded(recommendation.id)}
                className="p-1 hover:bg-background rounded transition-colors duration-150"
              >
                <Icon 
                  name={expandedCard === recommendation.id ? "ChevronUp" : "ChevronDown"} 
                  size={16} 
                  className="text-text-secondary" 
                />
              </button>
            </div>

            {/* Collapsed View */}
            {expandedCard !== recommendation.id && (
              <p className="text-sm text-text-secondary line-clamp-2">
                {recommendation.description.split('\n')[0]}
              </p>
            )}

            {/* Expanded View */}
            {expandedCard === recommendation.id && (
              <div className="space-y-4">
                <p className="text-sm text-text-secondary leading-relaxed">
                  {recommendation.description}
                </p>
                
                <div className="flex items-center justify-between pt-3 border-t border-border-light">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-1">
                      <Icon name="Clock" size={14} className="text-text-muted" />
                      <span className="text-xs text-text-muted">
                        {recommendation.estimatedTime}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Icon name="BookOpen" size={14} className="text-text-muted" />
                      <span className="text-xs text-text-muted">
                        {recommendation.subject}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button className="px-3 py-1.5 text-xs bg-background hover:bg-border-light rounded-lg transition-colors duration-150 text-text-secondary">
                      Отложить
                    </button>
                    <button className="px-3 py-1.5 text-xs bg-primary hover:bg-primary-700 text-white rounded-lg transition-colors duration-150 hover-lift">
                      Применить
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* AI Insights Summary */}
      <div className="mt-6 pt-4 border-t border-border">
        <div className="bg-gradient-to-r from-secondary-50 to-primary-50 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-secondary to-primary rounded-full flex items-center justify-center flex-shrink-0">
              <Icon name="Sparkles" size={16} color="white" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-text-primary mb-1">
                Персональный анализ
              </h4>
              <p className="text-xs text-text-secondary">
                На основе анализа вашей активности за последние 30 дней, AI выявил 3 ключевые области для улучшения и 2 сильные стороны для развития.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIRecommendations;