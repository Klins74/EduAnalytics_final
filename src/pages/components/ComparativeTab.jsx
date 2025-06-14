import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import Icon from '../../components/AppIcon';

const ComparativeTab = ({ period, analysisType }) => {
  const [comparisonType, setComparisonType] = useState('classes');
  const [selectedMetric, setSelectedMetric] = useState('performance');

  const classComparison = [
    { class: '10А', performance: 4.3, engagement: 87, attendance: 94, assignments: 91 },
    { class: '10Б', performance: 4.1, engagement: 82, attendance: 89, assignments: 88 },
    { class: '10В', performance: 3.9, engagement: 78, attendance: 85, assignments: 82 },
    { class: '11А', performance: 4.5, engagement: 91, attendance: 96, assignments: 94 },
    { class: '11Б', performance: 4.2, engagement: 85, attendance: 92, assignments: 89 },
    { class: '11В', performance: 4.0, engagement: 80, attendance: 87, assignments: 85 }
  ];

  const subjectComparison = [
    { subject: 'Математика', class10: 4.2, class11: 4.4, average: 4.3 },
    { subject: 'Физика', class10: 3.8, class11: 4.1, average: 3.95 },
    { subject: 'Химия', class10: 4.0, class11: 4.3, average: 4.15 },
    { subject: 'Биология', class10: 4.3, class11: 4.5, average: 4.4 },
    { subject: 'История', class10: 3.9, class11: 4.2, average: 4.05 },
    { subject: 'Литература', class10: 4.1, class11: 4.4, average: 4.25 }
  ];

  const teacherComparison = [
    { teacher: 'Иванова М.П.', subject: 'Математика', performance: 4.3, satisfaction: 4.5, classes: 3 },
    { teacher: 'Петров А.С.', subject: 'Физика', performance: 3.9, satisfaction: 4.2, classes: 2 },
    { teacher: 'Сидорова Е.В.', subject: 'Химия', performance: 4.1, satisfaction: 4.4, classes: 2 },
    { teacher: 'Козлов Д.И.', subject: 'Биология', performance: 4.4, satisfaction: 4.6, classes: 3 },
    { teacher: 'Морозова А.Н.', subject: 'История', performance: 4.0, satisfaction: 4.3, classes: 4 },
    { teacher: 'Федоров С.М.', subject: 'Литература', performance: 4.2, satisfaction: 4.5, classes: 3 }
  ];

  const timeComparison = [
    { period: 'Сентябрь', current: 3.8, previous: 3.6, target: 4.0 },
    { period: 'Октябрь', current: 3.9, previous: 3.7, target: 4.0 },
    { period: 'Ноябрь', current: 4.0, previous: 3.8, target: 4.1 },
    { period: 'Декабрь', current: 4.1, previous: 3.9, target: 4.1 },
    { period: 'Январь', current: 4.2, previous: 4.0, target: 4.2 },
    { period: 'Февраль', current: 4.1, previous: 4.1, target: 4.2 },
    { period: 'Март', current: 4.3, previous: 4.2, target: 4.3 }
  ];

  const performanceCorrelation = [
    { engagement: 95, performance: 4.8, student: 'Отличник' },
    { engagement: 88, performance: 4.5, student: 'Хорошист' },
    { engagement: 82, performance: 4.2, student: 'Хорошист' },
    { engagement: 75, performance: 3.9, student: 'Средний' },
    { engagement: 68, performance: 3.6, student: 'Средний' },
    { engagement: 55, performance: 3.2, student: 'Слабый' },
    { engagement: 42, performance: 2.8, student: 'Слабый' },
    { engagement: 35, performance: 2.5, student: 'Критический' }
  ];

  const comparisonTypes = [
    { id: 'classes', label: 'По классам', icon: 'Users' },
    { id: 'subjects', label: 'По предметам', icon: 'BookOpen' },
    { id: 'teachers', label: 'По преподавателям', icon: 'UserCheck' },
    { id: 'time', label: 'По времени', icon: 'Calendar' },
    { id: 'correlation', label: 'Корреляции', icon: 'GitBranch' }
  ];

  const metrics = [
    { id: 'performance', label: 'Успеваемость', color: '#3B82F6' },
    { id: 'engagement', label: 'Вовлеченность', color: '#10B981' },
    { id: 'attendance', label: 'Посещаемость', color: '#F59E0B' },
    { id: 'assignments', label: 'Задания', color: '#7C3AED' }
  ];

  const getComparisonData = () => {
    switch (comparisonType) {
      case 'classes': return classComparison;
      case 'subjects': return subjectComparison;
      case 'teachers': return teacherComparison;
      case 'time': return timeComparison;
      case 'correlation': return performanceCorrelation;
      default: return classComparison;
    }
  };

  const getDataKey = () => {
    if (comparisonType === 'subjects') return 'subject';
    if (comparisonType === 'teachers') return 'teacher';
    if (comparisonType === 'time') return 'period';
    return 'class';
  };

  const getBestPerformer = (data) => {
    if (comparisonType === 'correlation') return null;
    
    const sortedData = [...data].sort((a, b) => {
      const aValue = a[selectedMetric] || a.performance || 0;
      const bValue = b[selectedMetric] || b.performance || 0;
      return bValue - aValue;
    });
    
    return sortedData[0];
  };

  const getWorstPerformer = (data) => {
    if (comparisonType === 'correlation') return null;
    
    const sortedData = [...data].sort((a, b) => {
      const aValue = a[selectedMetric] || a.performance || 0;
      const bValue = b[selectedMetric] || b.performance || 0;
      return aValue - bValue;
    });
    
    return sortedData[0];
  };

  const data = getComparisonData();
  const bestPerformer = getBestPerformer(data);
  const worstPerformer = getWorstPerformer(data);

  return (
    <div className="space-y-6">
      {/* Comparison Type Selector */}
      <div className="flex flex-wrap gap-2">
        {comparisonTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setComparisonType(type.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-150 ${
              comparisonType === type.id
                ? 'bg-primary text-white' :'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
            }`}
          >
            <Icon name={type.icon} size={16} />
            <span className="font-medium">{type.label}</span>
          </button>
        ))}
      </div>

      {/* Metric Selector for non-correlation views */}
      {comparisonType !== 'correlation' && comparisonType !== 'time' && (
        <div className="flex flex-wrap gap-2">
          {metrics.map((metric) => (
            <button
              key={metric.id}
              onClick={() => setSelectedMetric(metric.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm transition-colors duration-150 ${
                selectedMetric === metric.id
                  ? 'text-white' :'bg-background text-text-secondary hover:bg-gray-100'
              }`}
              style={{
                backgroundColor: selectedMetric === metric.id ? metric.color : undefined
              }}
            >
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: metric.color }}
              />
              <span className="font-medium">{metric.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Performance Insights */}
      {bestPerformer && worstPerformer && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-success-50 border border-success-100 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Icon name="Trophy" size={20} className="text-success" />
              <h3 className="font-medium text-success">Лучший результат</h3>
            </div>
            <p className="text-text-primary font-semibold">
              {bestPerformer[getDataKey()]}
            </p>
            <p className="text-sm text-text-secondary">
              {selectedMetric === 'performance' ? 'Средний балл' : 
               selectedMetric === 'engagement' ? 'Вовлеченность' :
               selectedMetric === 'attendance' ? 'Посещаемость' : 'Выполнение заданий'}: {' '}
              {bestPerformer[selectedMetric] || bestPerformer.performance}
              {selectedMetric === 'performance' ? '' : '%'}
            </p>
          </div>
          
          <div className="bg-error-50 border border-error-100 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Icon name="AlertTriangle" size={20} className="text-error" />
              <h3 className="font-medium text-error">Требует внимания</h3>
            </div>
            <p className="text-text-primary font-semibold">
              {worstPerformer[getDataKey()]}
            </p>
            <p className="text-sm text-text-secondary">
              {selectedMetric === 'performance' ? 'Средний балл' : 
               selectedMetric === 'engagement' ? 'Вовлеченность' :
               selectedMetric === 'attendance' ? 'Посещаемость' : 'Выполнение заданий'}: {' '}
              {worstPerformer[selectedMetric] || worstPerformer.performance}
              {selectedMetric === 'performance' ? '' : '%'}
            </p>
          </div>
        </div>
      )}

      {/* Main Comparison Chart */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
          {comparisonTypes.find(t => t.id === comparisonType)?.label}
        </h3>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            {comparisonType === 'correlation' ? (
              <ScatterChart data={performanceCorrelation}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                  dataKey="engagement" 
                  name="Вовлеченность"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Вовлеченность (%)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  dataKey="performance" 
                  name="Успеваемость"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Успеваемость', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value, name) => [
                    value, 
                    name === 'engagement' ? 'Вовлеченность (%)' : 'Успеваемость'
                  ]}
                  labelFormatter={(label, payload) => 
                    payload && payload[0] ? `Тип студента: ${payload[0].payload.student}` : ''
                  }
                />
                <Scatter 
                  dataKey="performance" 
                  fill="#3B82F6"
                  r={8}
                />
              </ScatterChart>
            ) : comparisonType === 'time' ? (
              <BarChart data={timeComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="current" fill="#3B82F6" name="Текущий год" radius={[4, 4, 0, 0]} />
                <Bar dataKey="previous" fill="#10B981" name="Прошлый год" radius={[4, 4, 0, 0]} />
                <Bar dataKey="target" fill="#F59E0B" name="Целевой показатель" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : (
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                  dataKey={getDataKey()} 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar 
                  dataKey={comparisonType === 'subjects' ? 'average' : 
                           comparisonType === 'teachers' ? 'performance' : 
                           selectedMetric} 
                  fill={metrics.find(m => m.id === selectedMetric)?.color || '#3B82F6'}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detailed Comparison Table */}
      {comparisonType !== 'correlation' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Детальное сравнение
          </h3>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 font-medium text-text-primary">
                    {comparisonType === 'classes' ? 'Класс' :
                     comparisonType === 'subjects' ? 'Предмет' :
                     comparisonType === 'teachers' ? 'Преподаватель' : 'Период'}
                  </th>
                  {comparisonType === 'subjects' ? (
                    <>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">10 класс</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">11 класс</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Среднее</th>
                    </>
                  ) : comparisonType === 'teachers' ? (
                    <>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Предмет</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Успеваемость</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Удовлетворенность</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Классов</th>
                    </>
                  ) : comparisonType === 'time' ? (
                    <>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Текущий</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Прошлый</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Цель</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Изменение</th>
                    </>
                  ) : (
                    <>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Успеваемость</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Вовлеченность</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Посещаемость</th>
                      <th className="text-right py-3 px-4 font-medium text-text-primary">Задания</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {data.map((item, index) => (
                  <tr key={index} className="border-b border-border-light hover:bg-background transition-colors duration-150">
                    <td className="py-3 px-4 font-medium text-text-primary">
                      {item[getDataKey()]}
                    </td>
                    {comparisonType === 'subjects' ? (
                      <>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.class10}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.class11}</td>
                        <td className="text-right py-3 px-4 font-semibold text-text-primary">{item.average}</td>
                      </>
                    ) : comparisonType === 'teachers' ? (
                      <>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.subject}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.performance}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.satisfaction}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.classes}</td>
                      </>
                    ) : comparisonType === 'time' ? (
                      <>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.current}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.previous}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.target}</td>
                        <td className="text-right py-3 px-4">
                          <div className={`flex items-center justify-end space-x-1 ${
                            item.current > item.previous ? 'text-success' : 'text-error'
                          }`}>
                            <Icon 
                              name={item.current > item.previous ? "ArrowUp" : "ArrowDown"} 
                              size={14} 
                            />
                            <span className="font-medium">
                              {Math.abs(item.current - item.previous).toFixed(1)}
                            </span>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.performance}</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.engagement}%</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.attendance}%</td>
                        <td className="text-right py-3 px-4 text-text-secondary">{item.assignments}%</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Correlation Analysis */}
      {comparisonType === 'correlation' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Анализ корреляций
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-primary-50 border border-primary-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="TrendingUp" size={16} className="text-primary" />
                <span className="font-medium text-primary">Сильная корреляция</span>
              </div>
              <p className="text-sm text-text-secondary">
                Коэффициент корреляции между вовлеченностью и успеваемостью: 0,87
              </p>
            </div>
            
            <div className="bg-success-50 border border-success-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="Target" size={16} className="text-success" />
                <span className="font-medium text-success">Пороговое значение</span>
              </div>
              <p className="text-sm text-text-secondary">
                Минимальная вовлеченность для успеваемости выше 4,0: 75%
              </p>
            </div>
            
            <div className="bg-error-50 border border-error-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="AlertTriangle" size={16} className="text-error" />
                <span className="font-medium text-error">Зона риска</span>
              </div>
              <p className="text-sm text-text-secondary">
                Студенты с вовлеченностью ниже 50% имеют высокий риск неуспеваемости
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComparativeTab;