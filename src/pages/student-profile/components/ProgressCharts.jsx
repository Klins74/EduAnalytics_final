import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, RadialBarChart, RadialBar, PieChart, Pie, Cell } from 'recharts';
import Icon from '../../../components/AppIcon';

const ProgressCharts = ({ subjects, selectedPeriod }) => {
  const chartData = subjects.map(subject => ({
    name: subject.name.length > 15 ? subject.name.substring(0, 15) + '...' : subject.name,
    fullName: subject.name,
    grade: subject.grade,
    progress: subject.progress,
    credits: subject.credits
  }));

  const progressData = subjects.map(subject => ({
    subject: subject.name.split(' ')[0],
    progress: subject.progress
  }));

  const gradeDistribution = [
    { name: '5.0', value: 15, color: '#10B981' },
    { name: '4.5-4.9', value: 35, color: '#3B82F6' },
    { name: '4.0-4.4', value: 30, color: '#F59E0B' },
    { name: '3.5-3.9', value: 15, color: '#EF4444' },
    { name: '<3.5', value: 5, color: '#6B7280' }
  ];

  const weeklyProgress = [
    { week: 'Нед 1', hours: 25, tasks: 8 },
    { week: 'Нед 2', hours: 28, tasks: 12 },
    { week: 'Нед 3', hours: 22, tasks: 6 },
    { week: 'Нед 4', hours: 30, tasks: 15 },
    { week: 'Нед 5', hours: 26, tasks: 10 }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-border rounded-lg p-3 shadow-elevated">
          <p className="font-medium text-text-primary">{payload[0].payload.fullName || label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
              {entry.name === 'grade' && '/5.0'}
              {entry.name === 'progress' && '%'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Subject Grades Chart */}
      <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-heading font-semibold text-text-primary">
            Оценки по предметам
          </h3>
          <div className="flex items-center space-x-2">
            <Icon name="BarChart3" size={16} className="text-text-secondary" />
            <span className="text-sm text-text-secondary">Текущий семестр</span>
          </div>
        </div>
        
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 12, fill: '#6B7280' }}
                axisLine={{ stroke: '#E5E7EB' }}
              />
              <YAxis 
                domain={[0, 5]}
                tick={{ fontSize: 12, fill: '#6B7280' }}
                axisLine={{ stroke: '#E5E7EB' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="grade" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Progress and Weekly Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Progress Chart */}
        <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-heading font-semibold text-text-primary">
              Прогресс изучения
            </h3>
            <Icon name="TrendingUp" size={16} className="text-success" />
          </div>
          
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart cx="50%" cy="50%" innerRadius="20%" outerRadius="80%" data={progressData}>
                <RadialBar 
                  dataKey="progress" 
                  cornerRadius={10} 
                  fill="#3B82F6"
                  background={{ fill: '#F3F4F6' }}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 space-y-2">
            {progressData.map((item, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <span className="text-text-secondary">{item.subject}</span>
                <span className="font-medium text-text-primary">{item.progress}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Weekly Activity */}
        <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-heading font-semibold text-text-primary">
              Недельная активность
            </h3>
            <Icon name="Activity" size={16} className="text-primary" />
          </div>
          
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyProgress} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                  dataKey="week" 
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  axisLine={{ stroke: '#E5E7EB' }}
                />
                <YAxis 
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  axisLine={{ stroke: '#E5E7EB' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line 
                  type="monotone" 
                  dataKey="hours" 
                  stroke="#3B82F6" 
                  strokeWidth={3}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="tasks" 
                  stroke="#10B981" 
                  strokeWidth={3}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 flex items-center justify-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-primary rounded-full" />
              <span className="text-sm text-text-secondary">Часы</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-success rounded-full" />
              <span className="text-sm text-text-secondary">Задания</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grade Distribution */}
      <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-heading font-semibold text-text-primary">
            Распределение оценок в группе
          </h3>
          <div className="flex items-center space-x-2">
            <Icon name="Users" size={16} className="text-text-secondary" />
            <span className="text-sm text-text-secondary">Сравнение с группой</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={gradeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {gradeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="flex flex-col justify-center space-y-3">
            {gradeDistribution.map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-text-secondary">{item.name}</span>
                </div>
                <span className="text-sm font-medium text-text-primary">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressCharts;