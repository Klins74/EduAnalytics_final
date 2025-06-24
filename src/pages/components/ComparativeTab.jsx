import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Icon from '../../components/AppIcon';
import { getComparativeTabData } from '../../api/mockApi.js';

const ComparativeTab = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [comparisonType, setComparisonType] = useState('classes');
  const [selectedMetric, setSelectedMetric] = useState('performance');
  const [teacherMetric, setTeacherMetric] = useState('performance');

  const [classComparison, setClassComparison] = useState([]);
  const [subjectComparison, setSubjectComparison] = useState([]);
  const [teacherComparison, setTeacherComparison] = useState([]);
  const [timeComparison, setTimeComparison] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const data = await getComparativeTabData();
        setClassComparison(data.classComparison || []);
        setSubjectComparison(data.subjectComparison || []);
        setTeacherComparison(data.teacherComparison || []);
        setTimeComparison(data.timeComparison || []);
      } catch (error) {
        console.error("Ошибка загрузки данных для вкладки Сравнение:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const comparisonTypes = [
    { id: 'classes', label: 'По классам', icon: 'Users' },
    { id: 'subjects', label: 'По предметам', icon: 'BookOpen' },
    { id: 'teachers', label: 'По преподавателям', icon: 'UserCheck' },
    { id: 'time', label: 'По времени', icon: 'Calendar' },
  ];

  // Палитра для метрик в режиме "По классам"
  const classMetrics = [
    { id: 'performance', label: 'Успеваемость', color: '#3B82F6' }, // Blue
    { id: 'engagement', label: 'Вовлеченность', color: '#10B981' }, // Green
    { id: 'attendance', label: 'Посещаемость', color: '#F59E0B' }, // Amber
    { id: 'assignments', label: 'Задания', color: '#7C3AED' }  // Violet
  ];
  
  // Палитра для метрик в режиме "По преподавателям"
  const teacherMetrics = [
      { id: 'performance', label: 'Успеваемость', color: '#EF4444' }, // Red
      { id: 'satisfaction', label: 'Удовлетворенность', color: '#F97316' }, // Orange
  ];

  const getComparisonData = () => {
    switch (comparisonType) {
      case 'classes': return classComparison;
      case 'subjects': return subjectComparison;
      case 'teachers': return teacherComparison;
      case 'time': return timeComparison;
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
    // ... функция остается без изменений
  };

  const getWorstPerformer = (data) => {
    // ... функция остается без изменений
  };

  if (isLoading) {
      return <div>Загрузка данных для сравнения...</div>;
  }
  
  const data = getComparisonData();
  const bestPerformer = getBestPerformer(data);
  const worstPerformer = getWorstPerformer(data);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {comparisonTypes.map((type) => (
          <button
            key={type.id}
            onClick={() => setComparisonType(type.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-150 ${
              comparisonType === type.id ? 'bg-primary text-white' : 'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
            }`}
          >
            <Icon name={type.icon} size={16} />
            <span className="font-medium">{type.label}</span>
          </button>
        ))}
      </div>

      { (comparisonType === 'classes') && (
        <div className="flex flex-wrap gap-2">
          {classMetrics.map((metric) => (
            <button
              key={metric.id}
              onClick={() => setSelectedMetric(metric.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm transition-colors duration-150 ${
                selectedMetric === metric.id ? 'text-white' : 'bg-background text-text-secondary hover:bg-gray-100'
              }`}
              style={{ backgroundColor: selectedMetric === metric.id ? metric.color : undefined }}
            >
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: metric.color }} />
              <span className="font-medium">{metric.label}</span>
            </button>
          ))}
        </div>
      )}
      
      { comparisonType === 'teachers' && (
        <div className="flex flex-wrap gap-2">
          {teacherMetrics.map((metric) => (
            <button
              key={metric.id}
              onClick={() => setTeacherMetric(metric.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm transition-colors duration-150 ${
                teacherMetric === metric.id ? 'text-white' : 'bg-background text-text-secondary hover:bg-gray-100'
              }`}
              style={{ backgroundColor: teacherMetric === metric.id ? metric.color : undefined }}
            >
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: metric.color }} />
              <span className="font-medium">{metric.label}</span>
            </button>
          ))}
        </div>
      )}

      {/* Карточки с лучшим/худшим результатом */}
      {/* ... (этот JSX блок остается без изменений) ... */}

      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
          {comparisonTypes.find(t => t.id === comparisonType)?.label}
        </h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            {(() => {
              switch (comparisonType) {
                case 'teachers':
                  return (
                    <BarChart data={teacherComparison} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[3, 5]} />
                      <YAxis type="category" dataKey="teacher" width={100} tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey={teacherMetric} fill={teacherMetrics.find(m => m.id === teacherMetric)?.color} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  );
                case 'time':
                  return (
                    <BarChart data={timeComparison}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="current" fill="#8884d8" name="Текущий год" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="previous" fill="#82ca9d" name="Прошлый год" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="target" fill="#ffc658" name="Целевой показатель" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  );
                case 'subjects':
                    return (
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey={getDataKey()} tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={80} />
                            <YAxis tick={{ fontSize: 12 }} />
                            <Tooltip />
                            <Bar dataKey="average" fill="#84CC16" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    );
                case 'classes':
                default:
                  return (
                    <BarChart data={data}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey={getDataKey()} tick={{ fontSize: 12 }} angle={-45} textAnchor="end" height={80} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey={selectedMetric} fill={classMetrics.find(m => m.id === selectedMetric)?.color || '#3B82F6'} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  );
              }
            })()}
          </ResponsiveContainer>
        </div>
      </div>
      
      {/* ... остальной JSX для детальной таблицы ... */}
    </div>
  );
};

export default ComparativeTab;