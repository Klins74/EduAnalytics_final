import React from 'react';
import Icon from '../../components/AppIcon';

const LiveMetrics = ({ studentsData }) => {
  const totalStudents = studentsData.length;
  const activeStudents = studentsData.filter(s => s.engagementStatus === 'active').length;
  const atRiskStudents = studentsData.filter(s => s.aiRiskScore > 0.6).length;
  const averageScore = studentsData.reduce((acc, s) => acc + s.averageScore, 0) / totalStudents || 0;

  const metrics = [
    {
      title: 'Всего студентов',
      value: totalStudents,
      icon: 'Users',
      color: 'primary',
      bgColor: 'bg-primary-50',
      textColor: 'text-primary',
      change: '+2',
      changeType: 'positive'
    },
    {
      title: 'Активные сейчас',
      value: activeStudents,
      icon: 'Activity',
      color: 'success',
      bgColor: 'bg-success-50',
      textColor: 'text-success',
      change: '+5',
      changeType: 'positive'
    },
    {
      title: 'Требуют внимания',
      value: atRiskStudents,
      icon: 'AlertTriangle',
      color: 'error',
      bgColor: 'bg-error-50',
      textColor: 'text-error',
      change: '-1',
      changeType: 'negative'
    },
    {
      title: 'Средний балл',
      value: averageScore.toFixed(1),
      icon: 'TrendingUp',
      color: 'secondary',
      bgColor: 'bg-secondary-50',
      textColor: 'text-secondary',
      change: '+0.2',
      changeType: 'positive'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <div key={index} className="bg-surface border border-border rounded-lg p-4 hover:shadow-card transition-shadow duration-150">
          <div className="flex items-center justify-between mb-3">
            <div className={`w-10 h-10 ${metric.bgColor} rounded-lg flex items-center justify-center`}>
              <Icon name={metric.icon} size={20} className={metric.textColor} />
            </div>
            <div className="flex items-center space-x-1">
              <span className={`text-xs font-medium ${
                metric.changeType === 'positive' ? 'text-success' : 'text-error'
              }`}>
                {metric.change}
              </span>
              <Icon 
                name={metric.changeType === 'positive' ? 'TrendingUp' : 'TrendingDown'} 
                size={12} 
                className={metric.changeType === 'positive' ? 'text-success' : 'text-error'} 
              />
            </div>
          </div>
          
          <div>
            <h3 className="text-2xl font-heading font-semibold text-text-primary mb-1">
              {metric.value}
            </h3>
            <p className="text-sm text-text-secondary">{metric.title}</p>
          </div>

          {/* Real-time indicator */}
          {metric.title === 'Активные сейчас' && (
            <div className="flex items-center space-x-1 mt-2">
              <div className="w-2 h-2 bg-success rounded-full ai-pulse" />
              <span className="text-xs text-text-muted">Обновлено сейчас</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default LiveMetrics;