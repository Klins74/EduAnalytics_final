import React from 'react';
import Icon from '../../../components/AppIcon';

const KPICard = ({ data }) => {
  const { title, value, change, changeType, icon, color, description } = data;

  const getColorClasses = (color) => {
    const colorMap = {
      primary: 'from-primary to-primary-600',
      success: 'from-success to-emerald-600',
      accent: 'from-accent to-accent-600',
      warning: 'from-warning to-orange-600',
      secondary: 'from-secondary to-purple-600'
    };
    return colorMap[color] || colorMap.primary;
  };

  const getChangeColor = (type) => {
    return type === 'positive' ? 'text-success' : 'text-error';
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6 hover:shadow-card transition-all duration-300 hover-lift card-elevation">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 bg-gradient-to-br ${getColorClasses(color)} rounded-lg flex items-center justify-center`}>
          <Icon name={icon} size={24} color="white" />
        </div>
        <div className={`flex items-center space-x-1 ${getChangeColor(changeType)}`}>
          <Icon 
            name={changeType === 'positive' ? 'TrendingUp' : 'TrendingDown'} 
            size={16} 
          />
          <span className="text-sm font-medium">{change}</span>
        </div>
      </div>
      
      <div className="mb-2">
        <h3 className="text-2xl font-heading font-semibold text-text-primary mb-1">
          {value}
        </h3>
        <p className="text-sm font-medium text-text-primary">{title}</p>
      </div>
      
      <p className="text-xs text-text-secondary">{description}</p>
      
      {/* Progress indicator for some metrics */}
      {(title.includes('Активность') || title.includes('Успеваемость')) && (
        <div className="mt-4">
          <div className="w-full bg-background rounded-full h-1.5">
            <div 
              className={`bg-gradient-to-r ${getColorClasses(color)} h-1.5 rounded-full transition-all duration-500`}
              style={{ 
                width: title.includes('Активность') ? '89%' : '84%' 
              }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPICard;