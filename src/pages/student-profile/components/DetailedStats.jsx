import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Area, AreaChart } from 'recharts';
import Icon from '../../../components/AppIcon';

const DetailedStats = ({ student, selectedPeriod, selectedSubject }) => {
  const [activeTab, setActiveTab] = useState('performance');

  const performanceData = [
    { month: 'Сен', grade: 3.8, attendance: 85, assignments: 12 },
    { month: 'Окт', grade: 4.1, attendance: 92, assignments: 15 },
    { month: 'Ноя', grade: 4.3, attendance: 88, assignments: 18 },
    { month: 'Дек', grade: 4.2, attendance: 95, assignments: 14 },
    { month: 'Янв', grade: 4.4, attendance: 90, assignments: 16 }
  ];

  const subjectPerformance = [
    { subject: 'ML', sep: 3.5, oct: 4.0, nov: 4.2, dec: 4.3, jan: 4.5 },
    { subject: 'БД', sep: 4.2, oct: 4.5, nov: 4.6, dec: 4.7, jan: 4.8 },
    { subject: 'Веб', sep: 3.8, oct: 3.9, nov: 4.0, dec: 4.1, jan: 4.2 },
    { subject: 'Алг', sep: 4.0, oct: 4.3, nov: 4.4, dec: 4.5, jan: 4.6 },
    { subject: 'Англ', sep: 3.2, oct: 3.5, nov: 3.7, dec: 3.8, jan: 4.0 }
  ];

  const activityHeatmap = [
    { day: 'Пн', hours: [2, 3, 4, 2, 3, 4, 5, 3, 4, 2, 3, 4] },
    { day: 'Вт', hours: [1, 2, 3, 4, 2, 3, 4, 5, 3, 4, 2, 3] },
    { day: 'Ср', hours: [3, 4, 5, 3, 4, 5, 6, 4, 5, 3, 4, 5] },
    { day: 'Чт', hours: [2, 3, 4, 5, 3, 4, 5, 6, 4, 5, 3, 4] },
    { day: 'Пт', hours: [4, 5, 6, 4, 5, 6, 7, 5, 6, 4, 5, 6] },
    { day: 'Сб', hours: [1, 2, 1, 2, 1, 2, 3, 2, 1, 2, 1, 2] },
    { day: 'Вс', hours: [0, 1, 0, 1, 0, 1, 2, 1, 0, 1, 0, 1] }
  ];

  const comparisonData = [
    { metric: 'Средний балл', student: 4.2, group: 3.8, percentile: 75 },
    { metric: 'Посещаемость', student: 90, group: 82, percentile: 68 },
    { metric: 'Активность', student: 87, group: 75, percentile: 82 },
    { metric: 'Задания', student: 95, group: 88, percentile: 71 }
  ];

  const learningPatterns = [
    {
      pattern: 'Утренняя продуктивность',
      description: 'Наиболее активен с 9:00 до 12:00',
      strength: 85,
      recommendation: 'Планируйте сложные задачи на утро'
    },
    {
      pattern: 'Последовательное изучение',
      description: 'Предпочитает изучать материал поэтапно',
      strength: 78,
      recommendation: 'Разбивайте большие темы на части'
    },
    {
      pattern: 'Визуальное восприятие',
      description: 'Лучше усваивает материал с диаграммами',
      strength: 92,
      recommendation: 'Используйте больше визуальных материалов'
    }
  ];

  const tabs = [
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'activity', label: 'Активность', icon: 'Activity' },
    { id: 'comparison', label: 'Сравнение', icon: 'Users' },
    { id: 'patterns', label: 'Паттерны', icon: 'Brain' }
  ];

  const getHeatmapColor = (hours) => {
    if (hours === 0) return 'bg-gray-100';
    if (hours <= 2) return 'bg-primary-100';
    if (hours <= 4) return 'bg-primary-300';
    if (hours <= 6) return 'bg-primary-500';
    return 'bg-primary-700';
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-border rounded-lg p-3 shadow-elevated">
          <p className="font-medium text-text-primary">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.name === 'grade' && '/5.0'}
              {(entry.name === 'attendance' || entry.name === 'assignments') && '%'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card">
      {/* Header */}
      <div className="p-6 border-b border-border">
        <h3 className="text-lg font-heading font-semibold text-text-primary mb-4">
          Детальная статистика
        </h3>
        
        {/* Tabs */}
        <div className="flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                activeTab === tab.id
                  ? 'bg-primary text-white shadow-card'
                  : 'bg-background text-text-secondary hover:bg-border-light hover:text-text-primary'
              }`}
            >
              <Icon name={tab.icon} size={16} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className="space-y-6">
            {/* Overall Performance Trend */}
            <div>
              <h4 className="text-md font-medium text-text-primary mb-4">
                Динамика успеваемости
              </h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Line type="monotone" dataKey="grade" stroke="#3B82F6" strokeWidth={3} dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Subject Performance */}
            <div>
              <h4 className="text-md font-medium text-text-primary mb-4">
                Успеваемость по предметам
              </h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={subjectPerformance}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="subject" tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <YAxis domain={[3, 5]} tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="jan" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="dec" stackId="2" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Activity Tab */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            {/* Activity Heatmap */}
            <div>
              <h4 className="text-md font-medium text-text-primary mb-4">
                Карта активности (последние 12 недель)
              </h4>
              <div className="overflow-x-auto">
                <div className="grid grid-cols-13 gap-1 min-w-max">
                  <div></div>
                  {Array.from({ length: 12 }, (_, i) => (
                    <div key={i} className="text-xs text-text-muted text-center p-1">
                      {i + 1}
                    </div>
                  ))}
                  {activityHeatmap.map((dayData, dayIndex) => (
                    <React.Fragment key={dayIndex}>
                      <div className="text-xs text-text-muted p-1 w-8">
                        {dayData.day}
                      </div>
                      {dayData.hours.map((hours, weekIndex) => (
                        <div
                          key={weekIndex}
                          className={`w-4 h-4 rounded-sm ${getHeatmapColor(hours)} border border-white`}
                          title={`${dayData.day}, неделя ${weekIndex + 1}: ${hours} часов`}
                        />
                      ))}
                    </React.Fragment>
                  ))}
                </div>
              </div>
              <div className="flex items-center justify-between mt-4 text-xs text-text-muted">
                <span>Меньше</span>
                <div className="flex items-center space-x-1">
                  <div className="w-3 h-3 bg-gray-100 rounded-sm" />
                  <div className="w-3 h-3 bg-primary-100 rounded-sm" />
                  <div className="w-3 h-3 bg-primary-300 rounded-sm" />
                  <div className="w-3 h-3 bg-primary-500 rounded-sm" />
                  <div className="w-3 h-3 bg-primary-700 rounded-sm" />
                </div>
                <span>Больше</span>
              </div>
            </div>

            {/* Weekly Activity Chart */}
            <div>
              <h4 className="text-md font-medium text-text-primary mb-4">
                Активность и посещаемость
              </h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#6B7280' }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="attendance" fill="#10B981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="assignments" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && (
          <div className="space-y-6">
            <h4 className="text-md font-medium text-text-primary mb-4">
              Сравнение с группой
            </h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {comparisonData.map((item, index) => (
                <div key={index} className="bg-background rounded-lg p-4 border border-border">
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium text-text-primary">{item.metric}</h5>
                    <span className="text-sm text-text-secondary">
                      {item.percentile} перцентиль
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Вы</span>
                      <span className="font-medium text-primary">{item.student}</span>
                    </div>
                    <div className="w-full bg-border-light rounded-full h-2">
                      <div 
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${(item.student / Math.max(item.student, item.group)) * 100}%` }}
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Группа</span>
                      <span className="font-medium text-text-secondary">{item.group}</span>
                    </div>
                    <div className="w-full bg-border-light rounded-full h-2">
                      <div 
                        className="bg-text-secondary h-2 rounded-full"
                        style={{ width: `${(item.group / Math.max(item.student, item.group)) * 100}%` }}
                      />
                    </div>
                  </div>
                  
                  <div className="mt-3 text-xs text-text-muted">
                    {item.student > item.group ? 'Выше среднего' : 'Ниже среднего'} на {Math.abs(item.student - item.group)} пунктов
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Patterns Tab */}
        {activeTab === 'patterns' && (
          <div className="space-y-6">
            <h4 className="text-md font-medium text-text-primary mb-4">
              Паттерны обучения
            </h4>
            
            <div className="space-y-4">
              {learningPatterns.map((pattern, index) => (
                <div key={index} className="bg-background rounded-lg p-4 border border-border">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h5 className="font-medium text-text-primary mb-1">{pattern.pattern}</h5>
                      <p className="text-sm text-text-secondary">{pattern.description}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-primary">{pattern.strength}%</div>
                      <div className="text-xs text-text-muted">сила паттерна</div>
                    </div>
                  </div>
                  
                  <div className="w-full bg-border-light rounded-full h-2 mb-3">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${pattern.strength}%` }}
                    />
                  </div>
                  
                  <div className="flex items-center space-x-2 text-sm">
                    <Icon name="Lightbulb" size={14} className="text-accent" />
                    <span className="text-text-secondary">{pattern.recommendation}</span>
                  </div>
                </div>
              ))}
            </div>
            
            {/* AI Insights */}
            <div className="bg-gradient-to-r from-secondary-50 to-primary-50 rounded-lg p-4 border border-secondary-100">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-secondary to-primary rounded-full flex items-center justify-center flex-shrink-0">
                  <Icon name="Brain" size={16} color="white" />
                </div>
                <div>
                  <h5 className="font-medium text-text-primary mb-2">AI-анализ паттернов</h5>
                  <p className="text-sm text-text-secondary mb-3">
                    На основе анализа вашего поведения за последние 3 месяца, система выявила устойчивые паттерны обучения. 
                    Ваш стиль обучения характеризуется высокой визуальной ориентацией и предпочтением утренних часов для сложных задач.
                  </p>
                  <div className="flex items-center space-x-4 text-xs text-text-muted">
                    <span>Точность прогноза: 87%</span>
                    <span>Обновлено: сегодня</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailedStats;