import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import KPICard from '../dashboard/components/KPICard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import QuickActions from '../dashboard/components/QuickActions';
import Icon from '../../components/AppIcon';

const StudentDashboard = () => {
  const { t } = useTranslation();
  const [studentData, setStudentData] = useState(null);
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendSeries, setTrendSeries] = useState([]);
  const [forecastSeries, setForecastSeries] = useState([]);
  const [stats, setStats] = useState({
    totalCourses: 0,
    totalAssignments: 0,
    completedAssignments: 0,
    averageGrade: 0,
    pendingDeadlines: 0
  });

  useEffect(() => {
    fetchStudentData();
  }, []);

  const fetchStudentData = async () => {
    try {
      setLoading(true);
      
      // Получаем данные студента (в реальном приложении - из контекста пользователя)
      const studentId = 1; // TODO: Получать из контекста пользователя
      
      // Получаем аналитику студента
      const analyticsResponse = await fetch(`http://localhost:8000/api/analytics/students/${studentId}/performance`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (analyticsResponse.ok) {
        const analyticsData = await analyticsResponse.json();
        setStats(prev => ({
          ...prev,
          totalCourses: analyticsData.overall_performance.courses_count || 0,
          totalAssignments: analyticsData.overall_performance.total_assignments || 0,
          completedAssignments: analyticsData.overall_performance.total_submissions || 0,
          averageGrade: analyticsData.overall_performance.overall_average_grade || 0
        }));
      }

      // Получаем курсы студента
      const coursesResponse = await fetch('http://localhost:8000/api/courses/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (coursesResponse.ok) {
        const coursesData = await coursesResponse.json();
        setCourses(coursesData.courses || []);
      }

      // Получаем задания
      const assignmentsResponse = await fetch('http://localhost:8000/api/assignments/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (assignmentsResponse.ok) {
        const assignmentsData = await assignmentsResponse.json();
        setAssignments(assignmentsData.assignments || []);
        
        // Подсчитываем pending deadlines
        const now = new Date();
        const pendingCount = assignmentsData.assignments?.filter(
          assignment => new Date(assignment.due_date) > now
        ).length || 0;
        
        setStats(prev => ({ ...prev, pendingDeadlines: pendingCount }));
      }

      // Получаем сдачи студента
      const submissionsResponse = await fetch('http://localhost:8000/api/submissions/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (submissionsResponse.ok) {
        const submissionsData = await submissionsResponse.json();
        setSubmissions(submissionsData.submissions || []);
      }

      // Тренды студента (за 30 дней, недельные бакеты)
      const trendsRes = await fetch(`http://localhost:8000/api/analytics/students/${studentId}/trends?days=30&bucket=week`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}` }
      });
      if (trendsRes.ok) {
        const data = await trendsRes.json();
        const series = (data.series || []).map(p => ({
          date: new Date(p.bucket_start).toLocaleDateString('ru-RU'),
          submissions: p.submissions,
          average_grade: p.average_grade,
          on_time_rate: p.on_time_rate
        }));
        setTrendSeries(series);
      }

      // Прогноз успеваемости
      const forecastRes = await fetch(`http://localhost:8000/api/analytics/predict/performance?scope=student&target_id=${studentId}&horizon_days=14&bucket=day`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}` }
      });
      if (forecastRes.ok) {
        const data = await forecastRes.json();
        const series = (data.forecast || []).map(p => ({ index: p.index, pred_submissions: p.pred_submissions, pred_avg_grade: p.pred_avg_grade }));
        setForecastSeries(series);
      }

      // Моковые данные студента для демонстрации
      setStudentData({
        id: studentId,
        name: "Аружан Серікова",
        email: "aruzhan.serikova@edu.ru",
        studentId: "STU-2024-001",
        course: "Информационные технологии",
        year: 3,
        group: "ИТ-21-1",
        gpa: 4.2
      });

    } catch (error) {
      console.error('Error fetching student data:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: t('student.viewAssignments'),
      description: t('student.viewAssignmentsDesc'),
      icon: '📝',
      action: () => window.location.href = '/student/assignments',
      color: 'bg-blue-500'
    },
    {
      title: t('student.submitWork'),
      description: t('student.submitWorkDesc'),
      icon: '📤',
      action: () => window.location.href = '/student/submit',
      color: 'bg-green-500'
    },
    {
      title: t('student.viewGrades'),
      description: t('student.viewGradesDesc'),
      icon: '📊',
      action: () => window.location.href = '/student/grades',
      color: 'bg-purple-500'
    },
    {
      title: t('student.askAI'),
      description: t('student.askAIDesc'),
      icon: '🤖',
      action: () => window.location.href = '/ai',
      color: 'bg-orange-500'
    }
  ];

  const upcomingDeadlines = assignments
    .filter(assignment => new Date(assignment.due_date) > new Date())
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .slice(0, 3);

  const recentSubmissions = submissions
    .filter(sub => sub.student_id === studentData?.id)
    .sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at))
    .slice(0, 3);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <Sidebar />
          <div className="flex-1 p-6">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-32 bg-gray-200 rounded"></div>
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-80 bg-gray-200 rounded"></div>
                <div className="h-80 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <div className="flex-1 p-6">
          {/* Заголовок */}
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {t('student.dashboardTitle')}, {studentData?.name.split(' ')[0]}!
                </h1>
                <p className="text-gray-600">
                  {t('student.dashboardSubtitle')}
                </p>
              </div>
              <div className="mt-4 lg:mt-0 flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-green-50 px-3 py-2 rounded-lg">
                  <Icon name="TrendingUp" size={16} className="text-green-600" />
                  <span className="text-sm font-medium text-green-600">
                    GPA: {studentData?.gpa}
                  </span>
                </div>
                <div className="flex items-center space-x-2 bg-blue-50 px-3 py-2 rounded-lg">
                  <Icon name="Target" size={16} className="text-blue-600" />
                  <span className="text-sm font-medium text-blue-600">
                    {studentData?.course} • {studentData?.year} курс
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* KPI карточки */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard
              title={t('student.totalCourses')}
              value={stats.totalCourses}
              icon="📚"
              color="blue"
              change="+1"
              changeType="positive"
            />
            <KPICard
              title={t('student.totalAssignments')}
              value={stats.totalAssignments}
              icon="📝"
              color="green"
              change="+3"
              changeType="positive"
            />
            <KPICard
              title={t('student.completedAssignments')}
              value={stats.completedAssignments}
              icon="✅"
              color="yellow"
              change="+2"
              changeType="positive"
            />
            <KPICard
              title={t('student.averageGrade')}
              value={`${stats.averageGrade}%`}
              icon="📊"
              color="purple"
              change="+2.1%"
              changeType="positive"
            />
          </div>

          {/* Основной контент */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Быстрые действия */}
            <div className="lg:col-span-1">
              <QuickActions actions={quickActions} />
            </div>

            {/* Тренды успеваемости */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Тренды успеваемости</h3>
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendSeries} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis dataKey="date" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="left" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis yAxisId="right" orientation="right" stroke="#6B7280" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip />
                      <Line yAxisId="left" type="monotone" dataKey="submissions" stroke="#1E40AF" strokeWidth={3} dot={{ r: 3 }} name="Сдачи" />
                      <Line yAxisId="right" type="monotone" dataKey="average_grade" stroke="#F59E0B" strokeWidth={3} dot={{ r: 3 }} name="Средняя оценка" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>

          {/* Прогноз производительности */}
          {forecastSeries.length > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Прогноз на 14 дней</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Ожидаемые сдачи в день</div>
                    <div className="text-2xl font-semibold text-gray-900">{forecastSeries[0].pred_submissions}</div>
                  </div>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="text-sm text-gray-500 mb-1">Прогноз средней оценки</div>
                    <div className="text-2xl font-semibold text-gray-900">{forecastSeries[0].pred_avg_grade}%</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Upcoming Deadlines */}
          {upcomingDeadlines.length > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {t('student.upcomingDeadlines')} ({upcomingDeadlines.length})
                  </h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {upcomingDeadlines.map(assignment => {
                      const course = courses.find(c => c.id === assignment.course_id);
                      const daysLeft = Math.ceil((new Date(assignment.due_date) - new Date()) / (1000 * 60 * 60 * 24));
                      
                      return (
                        <div key={assignment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                              <span className="text-red-600">⏰</span>
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">{assignment.title}</h4>
                              <p className="text-sm text-gray-500">
                                {course?.title || 'Unknown Course'} • Due: {new Date(assignment.due_date).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-sm font-medium ${
                              daysLeft <= 3 ? 'text-red-600' : daysLeft <= 7 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                              {daysLeft === 0 ? t('student.dueToday') : 
                               daysLeft === 1 ? t('student.dueTomorrow') : 
                               `${daysLeft} ${t('student.daysLeft')}`}
                            </div>
                            <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                              {t('student.viewAssignment')}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Recent Submissions */}
          {recentSubmissions.length > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {t('student.recentSubmissions')}
                  </h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {recentSubmissions.map(submission => {
                      const assignment = assignments.find(a => a.id === submission.assignment_id);
                      const course = courses.find(c => c.id === assignment?.course_id);
                      
                      return (
                        <div key={submission.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                              <span className="text-green-600">📤</span>
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">
                                {assignment?.title || 'Unknown Assignment'}
                              </h4>
                              <p className="text-sm text-gray-500">
                                {course?.title || 'Unknown Course'} • Submitted: {new Date(submission.submitted_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-sm font-medium ${
                              submission.status === 'submitted' ? 'text-yellow-600' : 
                              submission.status === 'graded' ? 'text-green-600' : 'text-gray-600'
                            }`}>
                              {submission.status === 'submitted' ? t('student.submitted') :
                               submission.status === 'graded' ? t('student.graded') : submission.status}
                            </div>
                            {submission.grades?.length > 0 && (
                              <div className="text-sm text-gray-900 mt-1">
                                {t('student.grade')}: {submission.grades[0].score}%
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Insights */}
          <div className="mt-8">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t('student.aiInsights')}
                </h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Icon name="TrendingUp" size={16} className="text-blue-600" />
                      <span className="text-sm font-medium text-blue-600">{t('student.improvement')}</span>
                    </div>
                    <p className="text-sm text-blue-800">
                      {t('student.improvementDesc')}
                    </p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Icon name="Award" size={16} className="text-green-600" />
                      <span className="text-sm font-medium text-green-600">{t('student.strength')}</span>
                    </div>
                    <p className="text-sm text-green-800">
                      {t('student.strengthDesc')}
                    </p>
                  </div>
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <Icon name="Clock" size={16} className="text-purple-600" />
                      <span className="text-sm font-medium text-purple-600">{t('student.schedule')}</span>
                    </div>
                    <p className="text-sm text-purple-800">
                      {t('student.scheduleDesc')}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
