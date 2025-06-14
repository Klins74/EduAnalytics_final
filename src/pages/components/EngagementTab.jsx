import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import Icon from '../../components/AppIcon';

const EngagementTab = ({ period, analysisType }) => {
  const [selectedView, setSelectedView] = useState('overview');

  const engagementData = [
    { day: 'Пн', online: 85, offline: 78, participation: 82 },
    { day: 'Вт', online: 88, offline: 82, participation: 85 },
    { day: 'Ср', online: 92, offline: 85, participation: 88 },
    { day: 'Чт', online: 87, offline: 80, participation: 84 },
    { day: 'Пт', online: 83, offline: 76, participation: 79 },
    { day: 'Сб', online: 45, offline: 35, participation: 40 },
    { day: 'Вс', online: 32, offline: 28, participation: 30 }
  ];

  const activityHeatmap = [
    { hour: '08:00', Mon: 45, Tue: 52, Wed: 48, Thu: 51, Fri: 46, Sat: 12, Sun: 8 },
    { hour: '09:00', Mon: 78, Tue: 82, Wed: 85, Thu: 79, Fri: 76, Sat: 25, Sun: 15 },
    { hour: '10:00', Mon: 92, Tue: 95, Wed: 98, Thu: 94, Fri: 89, Sat: 35, Sun: 22 },
    { hour: '11:00', Mon: 88, Tue: 91, Wed: 94, Thu: 90, Fri: 85, Sat: 42, Sun: 28 },
    { hour: '12:00', Mon: 85, Tue: 88, Wed: 91, Thu: 87, Fri: 82, Sat: 38, Sun: 25 },
    { hour: '13:00', Mon: 72, Tue: 75, Wed: 78, Thu: 74, Fri: 69, Sat: 45, Sun: 32 },
    { hour: '14:00', Mon: 68, Tue: 71, Wed: 74, Thu: 70, Fri: 65, Sat: 48, Sun: 35 },
    { hour: '15:00', Mon: 82, Tue: 85, Wed: 88, Thu: 84, Fri: 79, Sat: 52, Sun: 38 },
    { hour: '16:00', Mon: 76, Tue: 79, Wed: 82, Thu: 78, Fri: 73, Sat: 48, Sun: 34 },
    { hour: '17:00', Mon: 65, Tue: 68, Wed: 71, Thu: 67, Fri: 62, Sat: 42, Sun: 28 }
  ];

  const engagementMetrics = [
    { metric: 'Активность в чате', value: 85, fullMark: 100 },
    { metric: 'Участие в опросах', value: 78, fullMark: 100 },
    { metric: 'Выполнение заданий', value: 92, fullMark: 100 },
    { metric: 'Время в системе', value: 88, fullMark: 100 },
    { metric: 'Взаимодействие с материалами', value: 76, fullMark: 100 },
    { metric: 'Обратная связь', value: 82, fullMark: 100 }
  ];

  const topEngagedStudents = [
    { name: 'Петрова Мария', score: 95, activities: 156, timeSpent: '8ч 45м' },
    { name: 'Иванов Алексей', score: 92, activities: 142, timeSpent: '7ч 32м' },
    { name: 'Сидорова Анна', score: 89, activities: 138, timeSpent: '7ч 18м' },
    { name: 'Козлов Дмитрий', score: 87, activities: 134, timeSpent: '6ч 54м' },
    { name: 'Морозов Игорь', score: 85, activities: 129, timeSpent: '6ч 41м' }
  ];

  const lowEngagementStudents = [
    { name: 'Волков Сергей', score: 42, activities: 23, timeSpent: '1ч 15м', risk: 'high' },
    { name: 'Лебедева Ольга', score: 38, activities: 19, timeSpent: '0ч 58м', risk: 'high' },
    { name: 'Новиков Павел', score: 45, activities: 28, timeSpent: '1ч 32м', risk: 'medium' },
    { name: 'Федорова Елена', score: 48, activities: 31, timeSpent: '1ч 45м', risk: 'medium' }
  ];

  const getHeatmapColor = (value) => {
    if (value >= 80) return 'bg-success';
    if (value >= 60) return 'bg-accent';
    if (value >= 40) return 'bg-warning';
    return 'bg-error';
  };

  const getHeatmapOpacity = (value) => {
    return Math.max(0.1, value / 100);
  };

  const views = [
    { id: 'overview', label: 'Обзор', icon: 'BarChart3' },
    { id: 'heatmap', label: 'Тепловая карта', icon: 'Grid3X3' },
    { id: 'students', label: 'По студентам', icon: 'Users' }
  ];

  return (
    <div className="space-y-6">
      {/* View Selector */}
      <div className="flex flex-wrap gap-2">
        {views.map((view) => (
          <button
            key={view.id}
            onClick={() => setSelectedView(view.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-150 ${
              selectedView === view.id
                ? 'bg-primary text-white' :'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
            }`}
          >
            <Icon name={view.icon} size={16} />
            <span className="font-medium">{view.label}</span>
          </button>
        ))}
      </div>

      {/* Engagement KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Средняя вовлеченность</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">84,2%</p>
            </div>
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <Icon name="Activity" size={24} className="text-primary" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+3,2%</span>
            <span className="text-sm text-text-muted">за неделю</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Активных студентов</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">642</p>
            </div>
            <div className="w-12 h-12 bg-success-100 rounded-full flex items-center justify-center">
              <Icon name="Users" size={24} className="text-success" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+18</span>
            <span className="text-sm text-text-muted">за неделю</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Среднее время в системе</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">5ч 23м</p>
            </div>
            <div className="w-12 h-12 bg-accent-100 rounded-full flex items-center justify-center">
              <Icon name="Clock" size={24} className="text-accent" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+32м</span>
            <span className="text-sm text-text-muted">за неделю</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Низкая активность</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">23</p>
            </div>
            <div className="w-12 h-12 bg-error-100 rounded-full flex items-center justify-center">
              <Icon name="AlertTriangle" size={24} className="text-error" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowDown" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">-5</span>
            <span className="text-sm text-text-muted">за неделю</span>
          </div>
        </div>
      </div>

      {selectedView === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Weekly Engagement Trend */}
          <div className="bg-background border border-border rounded-lg p-6">
            <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
              Динамика вовлеченности по дням
            </h3>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={engagementData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="online" 
                    stackId="1"
                    stroke="#3B82F6" 
                    fill="#3B82F6" 
                    fillOpacity={0.6}
                    name="Онлайн активность"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="offline" 
                    stackId="1"
                    stroke="#10B981" 
                    fill="#10B981" 
                    fillOpacity={0.6}
                    name="Офлайн активность"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Engagement Radar */}
          <div className="bg-background border border-border rounded-lg p-6">
            <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
              Метрики вовлеченности
            </h3>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={engagementMetrics}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Radar
                    name="Вовлеченность"
                    dataKey="value"
                    stroke="#7C3AED"
                    fill="#7C3AED"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {selectedView === 'heatmap' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Тепловая карта активности по времени
          </h3>
          
          <div className="overflow-x-auto">
            <div className="min-w-[600px]">
              <div className="grid grid-cols-8 gap-1 mb-2">
                <div className="text-xs font-medium text-text-secondary p-2">Время</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Пн</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Вт</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Ср</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Чт</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Пт</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Сб</div>
                <div className="text-xs font-medium text-text-secondary p-2 text-center">Вс</div>
              </div>
              
              {activityHeatmap.map((row) => (
                <div key={row.hour} className="grid grid-cols-8 gap-1 mb-1">
                  <div className="text-xs text-text-secondary p-2 font-medium">{row.hour}</div>
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                    <div
                      key={day}
                      className={`p-2 rounded text-xs text-center font-medium text-white ${getHeatmapColor(row[day])}`}
                      style={{ opacity: getHeatmapOpacity(row[day]) }}
                      title={`${row.hour} - ${row[day]}: ${row[day]}% активность`}
                    >
                      {row[day]}%
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
          
          <div className="flex items-center justify-center space-x-4 mt-4 text-xs">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-error rounded opacity-30" />
              <span className="text-text-secondary">Низкая (0-40%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-warning rounded opacity-60" />
              <span className="text-text-secondary">Средняя (40-60%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-accent rounded opacity-80" />
              <span className="text-text-secondary">Высокая (60-80%)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success rounded" />
              <span className="text-text-secondary">Очень высокая (80-100%)</span>
            </div>
          </div>
        </div>
      )}

      {selectedView === 'students' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Engaged Students */}
          <div className="bg-background border border-border rounded-lg p-6">
            <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
              Самые активные студенты
            </h3>
            
            <div className="space-y-3">
              {topEngagedStudents.map((student, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-success text-white rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{student.name}</p>
                      <p className="text-sm text-text-secondary">
                        {student.activities} активностей • {student.timeSpent}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-success">{student.score}%</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Low Engagement Students */}
          <div className="bg-background border border-border rounded-lg p-6">
            <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
              Требуют внимания
            </h3>
            
            <div className="space-y-3">
              {lowEngagementStudents.map((student, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-error-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium text-white ${
                      student.risk === 'high' ? 'bg-error' : 'bg-warning'
                    }`}>
                      <Icon name="AlertTriangle" size={16} />
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{student.name}</p>
                      <p className="text-sm text-text-secondary">
                        {student.activities} активностей • {student.timeSpent}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-semibold ${
                      student.risk === 'high' ? 'text-error' : 'text-warning'
                    }`}>
                      {student.score}%
                    </div>
                    <div className={`text-xs px-2 py-1 rounded-full ${
                      student.risk === 'high' ? 'bg-error text-white' : 'bg-warning text-white'
                    }`}>
                      {student.risk === 'high' ? 'Высокий риск' : 'Средний риск'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EngagementTab;