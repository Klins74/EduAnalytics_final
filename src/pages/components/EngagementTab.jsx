import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import Icon from '../../components/AppIcon';
import { getEngagementTabData } from '../../api/mockApi.js';

const EngagementTab = ({ period, analysisType }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [engagementData, setEngagementData] = useState([]);
  const [activityHeatmap, setActivityHeatmap] = useState([]);
  const [engagementMetrics, setEngagementMetrics] = useState([]);
  const [topEngagedStudents, setTopEngagedStudents] = useState([]);
  const [lowEngagementStudents, setLowEngagementStudents] = useState([]);

  const [selectedView, setSelectedView] = useState('overview');

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const data = await getEngagementTabData();
        setEngagementData(data.engagementData || []);
        setActivityHeatmap(data.activityHeatmap || []);
        setEngagementMetrics(data.engagementMetrics || []);
        setTopEngagedStudents(data.topEngagedStudents || []);
        setLowEngagementStudents(data.lowEngagementStudents || []);
      } catch (error) {
        console.error("Ошибка загрузки данных для вкладки Вовлеченность:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

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

  if (isLoading) {
    return (
      <div className="space-y-6 p-4">
        <div className="h-10 bg-gray-200 rounded-lg animate-pulse w-1/2"></div>
        <div className="h-32 bg-gray-200 rounded-lg animate-pulse"></div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-80 bg-gray-200 rounded-lg animate-pulse"></div>
          <div className="h-80 bg-gray-200 rounded-lg animate-pulse"></div>
        </div>
      </div>
    );
  }

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
        {/* ... Содержимое KPI остается без изменений ... */}
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
                  <Area type="monotone" dataKey="online" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} name="Онлайн активность"/>
                  <Area type="monotone" dataKey="offline" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} name="Офлайн активность"/>
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
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
                  <Radar name="Вовлеченность" dataKey="value" stroke="#7C3AED" fill="#7C3AED" fillOpacity={0.3} strokeWidth={2}/>
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