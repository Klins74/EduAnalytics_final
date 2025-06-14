import React from 'react';
import Icon from '../../../components/AppIcon';

const ActivityTimeline = ({ activities }) => {
  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor(diff / (1000 * 60));

    if (hours > 0) {
      return `${hours} ч. назад`;
    } else if (minutes > 0) {
      return `${minutes} мин. назад`;
    } else {
      return 'Только что';
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'assignment':
        return 'bg-success text-success-50';
      case 'lecture':
        return 'bg-primary text-primary-50';
      case 'test':
        return 'bg-accent text-accent-50';
      case 'project':
        return 'bg-secondary text-secondary-50';
      default:
        return 'bg-text-secondary text-surface';
    }
  };

  const getActivityDetails = (activity) => {
    switch (activity.type) {
      case 'assignment':
        return `Оценка: ${activity.grade}`;
      case 'lecture':
        return `Длительность: ${activity.duration} мин.`;
      case 'test':
        return `Результат: ${activity.score}%`;
      case 'project':
        return `Прогресс: ${activity.progress}%`;
      default:
        return '';
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-heading font-semibold text-text-primary">
          Временная шкала активности
        </h3>
        <button className="text-sm text-primary hover:text-primary-700 transition-colors duration-150">
          Показать все
        </button>
      </div>

      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="relative">
            {/* Timeline Line */}
            {index < activities.length - 1 && (
              <div className="absolute left-6 top-12 w-0.5 h-8 bg-border" />
            )}
            
            <div className="flex items-start space-x-4">
              {/* Icon */}
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${getActivityColor(activity.type)}`}>
                <Icon name={activity.icon} size={20} color="white" />
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-text-primary mb-1">
                      {activity.title}
                    </h4>
                    <p className="text-sm text-text-secondary mb-2">
                      {activity.subject}
                    </p>
                    {getActivityDetails(activity) && (
                      <p className="text-xs text-text-muted">
                        {getActivityDetails(activity)}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-text-muted whitespace-nowrap ml-4">
                    {formatTimeAgo(activity.timestamp)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* View More Button */}
      <div className="mt-6 pt-4 border-t border-border text-center">
        <button className="text-sm text-primary hover:text-primary-700 transition-colors duration-150 font-medium">
          Загрузить больше активности
        </button>
      </div>
    </div>
  );
};

export default ActivityTimeline;