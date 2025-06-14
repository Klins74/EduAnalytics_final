import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import Icon from '../../../components/AppIcon';

const ActivityChart = ({ data, timeRange }) => {
  const [chartType, setChartType] = useState('line');
  const [activeMetric, setActiveMetric] = useState('students');

  const metrics = [
    { key: 'students', label: 'Студенты', color: '#1E40AF', icon: 'Users' },
    { key: 'sessions', label: 'Сессии', color: '#10B981', icon: 'Activity' },
    { key: 'engagement', label: 'Вовлеченность', color: '#F59E0B', icon: 'TrendingUp' }
  ];

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface border border-border rounded-lg p-3 shadow-elevated">
          <p className="text-sm font-medium text-text-primary mb-2">{`Дата: ${label}`}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: entry.color }}
              ></div>
              <span className="text-sm text-text-secondary">{entry.name}:</span>
              <span className="text-sm font-medium text-text-primary">
                {entry.name === 'Вовлеченность' ? `${entry.value}%` : entry.value.toLocaleString('ru-RU')}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const getTimeRangeLabel = (range) => {
    const labels = {
      '24h': 'за последние 24 часа',
      '7d': 'за последние 7 дней',
      '30d': 'за последний месяц',
      '90d': 'за последние 3 месяца'
    };
    return labels[range] || labels['7d'];
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-6">
        <div>
          <h3 className="text-lg font-heading font-medium text-text-primary mb-1">
            Активность студентов
          </h3>
          <p className="text-sm text-text-secondary">
            Динамика активности {getTimeRangeLabel(timeRange)}
          </p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 lg:mt-0">
          {/* Metric Selector */}
          <div className="flex items-center space-x-2">
            {metrics.map((metric) => (
              <button
                key={metric.key}
                onClick={() => setActiveMetric(metric.key)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                  activeMetric === metric.key
                    ? 'bg-primary text-white' :'text-text-secondary hover:text-text-primary hover:bg-background'
                }`}
              >
                <Icon name={metric.icon} size={14} />
                <span className="hidden sm:inline">{metric.label}</span>
              </button>
            ))}
          </div>
          
          {/* Chart Type Toggle */}
          <div className="flex items-center space-x-1 bg-background border border-border rounded-lg p-1">
            <button
              onClick={() => setChartType('line')}
              className={`p-1.5 rounded transition-colors duration-150 ${
                chartType === 'line' ? 'bg-surface text-primary' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <Icon name="TrendingUp" size={16} />
            </button>
            <button
              onClick={() => setChartType('bar')}
              className={`p-1.5 rounded transition-colors duration-150 ${
                chartType === 'bar' ? 'bg-surface text-primary' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              <Icon name="BarChart3" size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Chart Container */}
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'line' ? (
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey="date" 
                stroke="#6B7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#6B7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toLocaleString('ru-RU')}
              />
              <Tooltip content={<CustomTooltip />} />
              {activeMetric === 'students' && (
                <Line 
                  type="monotone" 
                  dataKey="students" 
                  stroke="#1E40AF" 
                  strokeWidth={3}
                  dot={{ fill: '#1E40AF', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#1E40AF', strokeWidth: 2 }}
                  name="Студенты"
                />
              )}
              {activeMetric === 'sessions' && (
                <Line 
                  type="monotone" 
                  dataKey="sessions" 
                  stroke="#10B981" 
                  strokeWidth={3}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#10B981', strokeWidth: 2 }}
                  name="Сессии"
                />
              )}
              {activeMetric === 'engagement' && (
                <Line 
                  type="monotone" 
                  dataKey="engagement" 
                  stroke="#F59E0B" 
                  strokeWidth={3}
                  dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, stroke: '#F59E0B', strokeWidth: 2 }}
                  name="Вовлеченность"
                />
              )}
            </LineChart>
          ) : (
            <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis 
                dataKey="date" 
                stroke="#6B7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#6B7280"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toLocaleString('ru-RU')}
              />
              <Tooltip content={<CustomTooltip />} />
              {activeMetric === 'students' && (
                <Bar 
                  dataKey="students" 
                  fill="#1E40AF" 
                  radius={[4, 4, 0, 0]}
                  name="Студенты"
                />
              )}
              {activeMetric === 'sessions' && (
                <Bar 
                  dataKey="sessions" 
                  fill="#10B981" 
                  radius={[4, 4, 0, 0]}
                  name="Сессии"
                />
              )}
              {activeMetric === 'engagement' && (
                <Bar 
                  dataKey="engagement" 
                  fill="#F59E0B" 
                  radius={[4, 4, 0, 0]}
                  name="Вовлеченность"
                />
              )}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Chart Summary */}
      <div className="mt-6 pt-4 border-t border-border">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {metrics.map((metric) => {
            const currentValue = data[data.length - 1][metric.key];
            const previousValue = data[data.length - 2][metric.key];
            const change = ((currentValue - previousValue) / previousValue * 100).toFixed(1);
            const isPositive = change > 0;
            
            return (
              <div key={metric.key} className="text-center">
                <div className="flex items-center justify-center space-x-1 mb-1">
                  <Icon name={metric.icon} size={16} style={{ color: metric.color }} />
                  <span className="text-sm font-medium text-text-primary">{metric.label}</span>
                </div>
                <div className="text-lg font-semibold text-text-primary">
                  {metric.key === 'engagement' 
                    ? `${currentValue}%` 
                    : currentValue.toLocaleString('ru-RU')
                  }
                </div>
                <div className={`text-xs ${isPositive ? 'text-success' : 'text-error'}`}>
                  {isPositive ? '+' : ''}{change}% за период
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ActivityChart;