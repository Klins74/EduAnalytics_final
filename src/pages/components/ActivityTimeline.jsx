import React, { useState } from 'react';
import Icon from '../../components/AppIcon';

const ActivityTimeline = ({ studentsData }) => {
  const [selectedTimeRange, setSelectedTimeRange] = useState('today');

  // Generate timeline data based on student activities
  const generateTimelineData = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const timelineData = hours.map(hour => {
      const activities = [];
      
      // Simulate activities for each hour
      studentsData.forEach(student => {
        student.recentActivities?.forEach(activity => {
          const activityHour = activity.time.getHours();
          if (activityHour === hour) {
            activities.push({
              ...activity,
              studentName: student.name,
              studentId: student.id
            });
          }
        });
      });

      return {
        hour,
        activities,
        count: activities.length,
        types: {
          test: activities.filter(a => a.type === 'test').length,
          homework: activities.filter(a => a.type === 'homework').length,
          quiz: activities.filter(a => a.type === 'quiz').length,
          project: activities.filter(a => a.type === 'project').length
        }
      };
    });

    return timelineData;
  };

  const timelineData = generateTimelineData();
  const maxActivities = Math.max(...timelineData.map(d => d.count));

  const getActivityColor = (type) => {
    const colors = {
      test: 'bg-primary',
      homework: 'bg-success',
      quiz: 'bg-warning',
      project: 'bg-secondary'
    };
    return colors[type] || 'bg-gray-400';
  };

  const getActivityIcon = (type) => {
    const icons = {
      test: 'FileText',
      homework: 'BookOpen',
      quiz: 'HelpCircle',
      project: 'Folder'
    };
    return icons[type] || 'Activity';
  };

  const formatHour = (hour) => {
    return `${hour.toString().padStart(2, '0')}:00`;
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-heading font-medium text-text-primary mb-1">
            Временная шкала активности
          </h3>
          <p className="text-sm text-text-secondary">
            Распределение активности студентов по времени
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(e.target.value)}
            className="px-3 py-1.5 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
          >
            <option value="today">Сегодня</option>
            <option value="yesterday">Вчера</option>
            <option value="week">Эта неделя</option>
          </select>
          
          <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150">
            <Icon name="RefreshCw" size={16} className="text-text-secondary" />
          </button>
        </div>
      </div>

      {/* Timeline Chart */}
      <div className="mb-6">
        <div className="flex items-end space-x-1 h-32 mb-2">
          {timelineData.map((data, index) => (
            <div key={index} className="flex-1 flex flex-col items-center">
              <div className="w-full flex flex-col justify-end h-24 space-y-0.5">
                {data.count > 0 && (
                  <div
                    className="w-full bg-primary rounded-sm opacity-80 hover:opacity-100 transition-opacity duration-150 cursor-pointer"
                    style={{ 
                      height: `${(data.count / maxActivities) * 100}%`,
                      minHeight: data.count > 0 ? '4px' : '0px'
                    }}
                    title={`${data.count} активностей в ${formatHour(data.hour)}`}
                  />
                )}
              </div>
              <span className="text-xs text-text-muted mt-1">
                {data.hour % 4 === 0 ? formatHour(data.hour) : ''}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Activity Types Legend */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        {[
          { type: 'test', label: 'Тесты', color: 'bg-primary' },
          { type: 'homework', label: 'Домашние задания', color: 'bg-success' },
          { type: 'quiz', label: 'Викторины', color: 'bg-warning' },
          { type: 'project', label: 'Проекты', color: 'bg-secondary' }
        ].map(item => {
          const totalCount = timelineData.reduce((sum, data) => sum + data.types[item.type], 0);
          return (
            <div key={item.type} className="flex items-center space-x-2">
              <div className={`w-3 h-3 ${item.color} rounded-sm`} />
              <span className="text-sm text-text-primary">{item.label}</span>
              <span className="text-xs text-text-secondary">({totalCount})</span>
            </div>
          );
        })}
      </div>

      {/* Peak Activity Hours */}
      <div className="bg-background rounded-lg p-4">
        <h4 className="text-sm font-medium text-text-primary mb-2">
          Пиковые часы активности
        </h4>
        <div className="flex items-center space-x-4">
          {timelineData
            .sort((a, b) => b.count - a.count)
            .slice(0, 3)
            .map((data, index) => (
              <div key={index} className="flex items-center space-x-2">
                <Icon name="Clock" size={14} className="text-primary" />
                <span className="text-sm text-text-primary">
                  {formatHour(data.hour)}
                </span>
                <span className="text-xs text-text-secondary">
                  ({data.count} активностей)
                </span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default ActivityTimeline;