import React from 'react';
import Icon from '../../../components/AppIcon';
import DataSourceBadge from '../../../components/ui/DataSourceBadge';

const KPICard = ({ 
  data, 
  title, 
  value, 
  change, 
  changeType, 
  icon, 
  color, 
  description,
  dataSource = 'local',
  lastUpdated = null,
  isConnected = true 
}) => {
  // Support both data object and individual props
  const cardData = data || { title, value, change, changeType, icon, color, description };
  const {
    title: cardTitle,
    value: cardValue,
    change: cardChange,
    changeType: cardChangeType,
    icon: cardIcon,
    color: cardColor,
    description: cardDescription
  } = cardData;

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
        <div className={`w-12 h-12 bg-gradient-to-br ${getColorClasses(cardColor)} rounded-lg flex items-center justify-center`}>
          <Icon name={cardIcon} size={24} color="white" />
        </div>
        <div className="flex flex-col items-end gap-2">
          <DataSourceBadge 
            source={dataSource}
            lastUpdated={lastUpdated}
            isConnected={isConnected}
          />
          <div className={`flex items-center space-x-1 ${getChangeColor(cardChangeType)}`}>
            <Icon 
              name={cardChangeType === 'positive' ? 'TrendingUp' : 'TrendingDown'} 
              size={16} 
            />
            <span className="text-sm font-medium">{cardChange}</span>
          </div>
        </div>
      </div>
      
      <div className="mb-2">
        <h3 className="text-2xl font-heading font-semibold text-text-primary mb-1">
          {cardValue}
        </h3>
        <p className="text-sm font-medium text-text-primary">{cardTitle}</p>
      </div>
      
      <p className="text-xs text-text-secondary">{cardDescription}</p>
      
      {/* Progress indicator for some metrics */}
      {(cardTitle && (cardTitle.includes('Активность') || cardTitle.includes('Успеваемость'))) && (
        <div className="mt-4">
          <div className="w-full bg-background rounded-full h-1.5">
            <div 
              className={`bg-gradient-to-r ${getColorClasses(cardColor)} h-1.5 rounded-full transition-all duration-500`}
              style={{ 
                width: cardTitle.includes('Активность') ? '89%' : '84%' 
              }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPICard;