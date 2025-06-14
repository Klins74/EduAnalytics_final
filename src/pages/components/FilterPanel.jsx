import React from 'react';
import Icon from '../../components/AppIcon';

const FilterPanel = ({ filters, onFilterChange, studentsData, onClose }) => {
  const groups = [...new Set(studentsData.map(student => student.group))];
  const subjects = [...new Set(studentsData.flatMap(student => student.subjects))];

  const handleFilterUpdate = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    onFilterChange(newFilters);
    if (onClose) onClose();
  };

  const getEngagementCount = (status) => {
    return studentsData.filter(student => student.engagementStatus === status).length;
  };

  const getRiskCount = (level) => {
    const ranges = {
      low: [0, 0.3],
      medium: [0.3, 0.7],
      high: [0.7, 1]
    };
    const [min, max] = ranges[level];
    return studentsData.filter(student => student.aiRiskScore >= min && student.aiRiskScore < max).length;
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="font-heading font-medium text-text-primary">Фильтры</h3>
        <button
          onClick={() => onFilterChange({ group: 'all', subject: 'all', timeRange: 'today', activityType: 'all', engagementStatus: 'all' })}
          className="text-sm text-primary hover:text-primary-700 transition-colors duration-150"
        >
          Сбросить
        </button>
      </div>

      {/* Groups Filter */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          Группа
        </label>
        <select
          value={filters.group}
          onChange={(e) => handleFilterUpdate('group', e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
        >
          <option value="all">Все группы</option>
          {groups.map(group => (
            <option key={group} value={group}>{group}</option>
          ))}
        </select>
      </div>

      {/* Subjects Filter */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          Предмет
        </label>
        <select
          value={filters.subject}
          onChange={(e) => handleFilterUpdate('subject', e.target.value)}
          className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
        >
          <option value="all">Все предметы</option>
          {subjects.map(subject => (
            <option key={subject} value={subject}>{subject}</option>
          ))}
        </select>
      </div>

      {/* Time Range Filter */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          Период времени
        </label>
        <div className="space-y-2">
          {[
            { value: 'today', label: 'Сегодня' },
            { value: 'week', label: 'Эта неделя' },
            { value: 'month', label: 'Этот месяц' },
            { value: 'semester', label: 'Семестр' }
          ].map(option => (
            <label key={option.value} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="timeRange"
                value={option.value}
                checked={filters.timeRange === option.value}
                onChange={(e) => handleFilterUpdate('timeRange', e.target.value)}
                className="text-primary focus:ring-primary"
              />
              <span className="text-sm text-text-primary">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Activity Type Filter */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-2">
          Тип активности
        </label>
        <div className="space-y-2">
          {[
            { value: 'all', label: 'Все типы', icon: 'Activity' },
            { value: 'test', label: 'Тесты', icon: 'FileText' },
            { value: 'homework', label: 'Домашние задания', icon: 'BookOpen' },
            { value: 'quiz', label: 'Викторины', icon: 'HelpCircle' },
            { value: 'project', label: 'Проекты', icon: 'Folder' }
          ].map(option => (
            <label key={option.value} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="activityType"
                value={option.value}
                checked={filters.activityType === option.value}
                onChange={(e) => handleFilterUpdate('activityType', e.target.value)}
                className="text-primary focus:ring-primary"
              />
              <Icon name={option.icon} size={14} className="text-text-secondary" />
              <span className="text-sm text-text-primary">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Engagement Status */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-3">
          Уровень вовлеченности
        </label>
        <div className="space-y-2">
          <button
            onClick={() => handleFilterUpdate('engagementStatus', 'all')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-150 ${
              filters.engagementStatus === 'all' ?'bg-primary text-white' :'bg-background hover:bg-primary-50 text-text-primary'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Icon name="Users" size={14} />
              <span className="text-sm">Все студенты</span>
            </div>
            <span className="text-xs">{studentsData.length}</span>
          </button>
          
          <button
            onClick={() => handleFilterUpdate('engagementStatus', 'active')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-150 ${
              filters.engagementStatus === 'active' ?'bg-success text-white' :'bg-background hover:bg-success-50 text-text-primary'
            }`}
          >
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-success rounded-full" />
              <span className="text-sm">Активные</span>
            </div>
            <span className="text-xs">{getEngagementCount('active')}</span>
          </button>
          
          <button
            onClick={() => handleFilterUpdate('engagementStatus', 'moderate')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-150 ${
              filters.engagementStatus === 'moderate' ?'bg-warning text-white' :'bg-background hover:bg-warning-50 text-text-primary'
            }`}
          >
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-warning rounded-full" />
              <span className="text-sm">Умеренные</span>
            </div>
            <span className="text-xs">{getEngagementCount('moderate')}</span>
          </button>
          
          <button
            onClick={() => handleFilterUpdate('engagementStatus', 'low')}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-150 ${
              filters.engagementStatus === 'low' ?'bg-error text-white' :'bg-background hover:bg-error-50 text-text-primary'
            }`}
          >
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-error rounded-full" />
              <span className="text-sm">Низкие</span>
            </div>
            <span className="text-xs">{getEngagementCount('low')}</span>
          </button>
        </div>
      </div>

      {/* AI Risk Assessment */}
      <div>
        <label className="block text-sm font-medium text-text-primary mb-3">
          AI-оценка риска
        </label>
        <div className="space-y-2">
          <div className="flex items-center justify-between px-3 py-2 bg-success-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Icon name="Shield" size={14} className="text-success" />
              <span className="text-sm text-text-primary">Низкий риск</span>
            </div>
            <span className="text-xs text-text-secondary">{getRiskCount('low')}</span>
          </div>
          
          <div className="flex items-center justify-between px-3 py-2 bg-warning-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Icon name="AlertTriangle" size={14} className="text-warning" />
              <span className="text-sm text-text-primary">Средний риск</span>
            </div>
            <span className="text-xs text-text-secondary">{getRiskCount('medium')}</span>
          </div>
          
          <div className="flex items-center justify-between px-3 py-2 bg-error-50 rounded-lg">
            <div className="flex items-center space-x-2">
              <Icon name="AlertCircle" size={14} className="text-error" />
              <span className="text-sm text-text-primary">Высокий риск</span>
            </div>
            <span className="text-xs text-text-secondary">{getRiskCount('high')}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterPanel;