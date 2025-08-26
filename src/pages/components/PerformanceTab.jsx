import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import Icon from '../../components/AppIcon';
import { analyticsApi } from '../../api/analyticsApi';
import { listCourses } from '../../api/courseApi';

const PerformanceTab = ({ period, analysisType }) => {
  const [selectedMetric, setSelectedMetric] = useState('grades');
  const [drillDownData, setDrillDownData] = useState(null);
  const [courseId, setCourseId] = useState('1');
  const [courses, setCourses] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [overview, setOverview] = useState(null);
  const [assignmentPerformance, setAssignmentPerformance] = useState([]);
  const [onTimePct, setOnTimePct] = useState(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await listCourses({ limit: 50 });
        if (!mounted) return;
        const items = Array.isArray(data?.courses) ? data.courses : Array.isArray(data) ? data : [];
        setCourses(items);
        if (items.length > 0 && (!courseId || courseId === '1')) {
          setCourseId(String(items[0].id));
        }
      } catch (e) {
        // тихо игнорируем ошибки загрузки списка курсов
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const id = Number(courseId);
        const [ovw, assignments] = await Promise.all([
          analyticsApi.getCourseOverview(id),
          analyticsApi.getCourseAssignmentsAnalytics(id)
        ]);
        setOverview(ovw?.overview || null);
        const list = (assignments?.assignments_analytics || []).map(a => ({ subject: a.title, average: a.statistics?.average_grade ?? 0 }));
        setAssignmentPerformance(list);
        const sums = (assignments?.assignments_analytics || []).reduce((acc, a) => {
          const s = a.statistics || {};
          acc.on += Number(s.on_time_submissions || 0);
          acc.late += Number(s.late_submissions || 0);
          return acc;
        }, { on: 0, late: 0 });
        const total = sums.on + sums.late;
        setOnTimePct(total > 0 ? Math.round((sums.on / total) * 100) : null);
      } catch (e) {
        console.error('Ошибка загрузки аналитики курса:', e);
        setOverview(null);
        setAssignmentPerformance([]);
        setOnTimePct(null);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [courseId]);

  const gradeDistribution = [
    { grade: '5', count: 245, percentage: 32.1 },
    { grade: '4', count: 298, percentage: 39.0 },
    { grade: '3', count: 187, percentage: 24.5 },
    { grade: '2', count: 34, percentage: 4.4 }
  ];

  const trendData = [
    { month: 'Сен', performance: 3.7 },
    { month: 'Окт', performance: 3.8 },
    { month: 'Ноя', performance: 3.9 },
    { month: 'Дек', performance: 4.0 },
    { month: 'Янв', performance: 4.1 },
    { month: 'Фев', performance: 4.0 },
    { month: 'Мар', performance: 4.2 }
  ];

  const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444'];

  const handleDrillDown = (subject) => {
    const mockDetailData = {
      subject,
      classes: [
        { class: '10А', average: 4.5, students: 28 },
        { class: '10Б', average: 4.1, students: 26 },
        { class: '10В', average: 3.8, students: 24 }
      ],
      topStudents: [
        { name: 'Алихан Берік', grade: 4.8 },
        { name: 'Айзере Асқар', grade: 4.7 },
        { name: 'Нұрлан Оспанов', grade: 4.6 }
      ],
      strugglingStudents: [
        { name: 'Диас Ертаев', grade: 3.2 },
        { name: 'Анель Маратова', grade: 3.1 }
      ]
    };
    setDrillDownData(mockDetailData);
  };

  const metrics = [
    { id: 'grades', label: 'Оценки', icon: 'Award' },
    { id: 'attendance', label: 'Посещаемость', icon: 'Calendar' },
    { id: 'assignments', label: 'Задания', icon: 'FileText' },
    { id: 'tests', label: 'Тесты', icon: 'CheckSquare' }
  ];

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-text-secondary">Курс:</label>
        <select value={courseId} onChange={(e) => setCourseId(e.target.value)} className="px-3 py-2 border border-border rounded-lg bg-background">
          {courses.map(c => (
            <option key={c.id} value={c.id}>{c.title || `Курс #${c.id}`}</option>
          ))}
        </select>
        <span className="text-xs text-text-secondary">ID: {courseId}</span>
        {isLoading && <span className="text-xs text-text-secondary">Загрузка…</span>}
      </div>
      {/* Metric Selector */}
      <div className="flex flex-wrap gap-2">
        {metrics.map((metric) => (
          <button
            key={metric.id}
            onClick={() => setSelectedMetric(metric.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-150 ${
              selectedMetric === metric.id
                ? 'bg-primary text-white' :'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
            }`}
          >
            <Icon name={metric.icon} size={16} />
            <span className="font-medium">{metric.label}</span>
          </button>
        ))}
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Средний балл</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">{overview ? (Number(overview.average_grade || 0).toFixed(2)) : '—'}</p>
            </div>
            <div className="w-12 h-12 bg-success-100 rounded-full flex items-center justify-center">
              <Icon name="TrendingUp" size={24} className="text-success" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+0,15</span>
            <span className="text-sm text-text-muted">за месяц</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Вовремя сдано</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">{onTimePct !== null ? `${onTimePct}%` : '—'}</p>
            </div>
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <Icon name="Award" size={24} className="text-primary" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+2,1%</span>
            <span className="text-sm text-text-muted">за месяц</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Отличников</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">245</p>
            </div>
            <div className="w-12 h-12 bg-accent-100 rounded-full flex items-center justify-center">
              <Icon name="Star" size={24} className="text-accent" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowUp" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">+12</span>
            <span className="text-sm text-text-muted">за месяц</span>
          </div>
        </div>

        <div className="bg-background border border-border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-secondary">Неуспевающих</p>
              <p className="text-2xl font-heading font-semibold text-text-primary">34</p>
            </div>
            <div className="w-12 h-12 bg-error-100 rounded-full flex items-center justify-center">
              <Icon name="AlertTriangle" size={24} className="text-error" />
            </div>
          </div>
          <div className="flex items-center space-x-1 mt-2">
            <Icon name="ArrowDown" size={14} className="text-success" />
            <span className="text-sm text-success font-medium">-8</span>
            <span className="text-sm text-text-muted">за месяц</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance by Subject */}
        <div className="bg-background border border-border rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-heading font-medium text-text-primary">
              Успеваемость по заданиям
            </h3>
            <button className="text-primary hover:text-primary-700 text-sm font-medium">
              Подробнее
            </button>
          </div>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={assignmentPerformance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis 
                  dataKey="subject" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value, name) => [value, 'Средний балл']}
                  labelFormatter={(label) => `Предмет: ${label}`}
                />
                <Bar 
                  dataKey="average" 
                  fill="#3B82F6" 
                  radius={[4, 4, 0, 0]}
                  onClick={(data) => handleDrillDown(data.subject)}
                  style={{ cursor: 'pointer' }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Grade Distribution */}
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Распределение оценок
          </h3>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={gradeDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="count"
                >
                  {gradeDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name, props) => [value, `Оценка ${props.payload.grade}`]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mt-4">
            {gradeDistribution.map((item, index) => (
              <div key={item.grade} className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index] }}
                />
                <span className="text-sm text-text-secondary">
                  Оценка {item.grade}: {item.percentage}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Trend */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
          Динамика успеваемости
        </h3>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} domain={[3.5, 4.5]} />
              <Tooltip 
                formatter={(value) => [value, 'Средний балл']}
                labelFormatter={(label) => `Месяц: ${label}`}
              />
              <Line 
                type="monotone" 
                dataKey="performance" 
                stroke="#3B82F6" 
                strokeWidth={3}
                dot={{ fill: '#3B82F6', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Drill Down Modal */}
      {drillDownData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-1100 p-4">
          <div className="bg-surface rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h3 className="text-xl font-heading font-semibold text-text-primary">
                Детальная аналитика: {drillDownData.subject}
              </h3>
              <button
                onClick={() => setDrillDownData(null)}
                className="p-2 hover:bg-background rounded-lg transition-colors duration-150"
              >
                <Icon name="X" size={20} className="text-text-secondary" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div>
                <h4 className="font-medium text-text-primary mb-3">По классам</h4>
                <div className="space-y-2">
                  {drillDownData.classes.map((cls) => (
                    <div key={cls.class} className="flex items-center justify-between p-3 bg-background rounded-lg">
                      <span className="font-medium">{cls.class}</span>
                      <div className="text-right">
                        <div className="font-semibold text-text-primary">{cls.average}</div>
                        <div className="text-sm text-text-secondary">{cls.students} студентов</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-text-primary mb-3">Лучшие студенты</h4>
                  <div className="space-y-2">
                    {drillDownData.topStudents.map((student, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-success-50 rounded">
                        <span className="text-sm">{student.name}</span>
                        <span className="font-semibold text-success">{student.grade}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-text-primary mb-3">Требуют внимания</h4>
                  <div className="space-y-2">
                    {drillDownData.strugglingStudents.map((student, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-error-50 rounded">
                        <span className="text-sm">{student.name}</span>
                        <span className="font-semibold text-error">{student.grade}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceTab;