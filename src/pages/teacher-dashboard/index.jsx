import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import KPICard from '../dashboard/components/KPICard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import QuickActions from '../dashboard/components/QuickActions';

const TeacherDashboard = () => {
  const { t } = useTranslation();
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendSeries, setTrendSeries] = useState([]);
  const [forecastSeries, setForecastSeries] = useState([]);
  const [notifyStatus, setNotifyStatus] = useState("");
  const [schedule, setSchedule] = useState([]);
  const [scheduleRange, setScheduleRange] = useState('week'); // day | week
  const [scheduleStatus, setScheduleStatus] = useState("");
  const [stats, setStats] = useState({
    totalCourses: 0,
    totalStudents: 0,
    pendingSubmissions: 0,
    averageGrade: 0
  });

  useEffect(() => {
    fetchTeacherData();
  }, []);

  const loadSchedule = async (rangeOverride) => {
    try {
      const range = rangeOverride || scheduleRange;
      const now = new Date();
      const dateFrom = now.toISOString().slice(0,10);
      const to = new Date(now);
      if (range === 'week') {
        to.setDate(now.getDate() + 7);
      }
      const dateTo = to.toISOString().slice(0,10);
      const scheduleRes = await fetch(`http://localhost:8000/api/schedule?date_from=${dateFrom}&date_to=${dateTo}&limit=20`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}` }
      });
      if (scheduleRes.ok) {
        const data = await scheduleRes.json();
        setSchedule(data.schedules || []);
      } else {
        console.error('Failed to load schedule:', scheduleRes.status);
      }
    } catch (error) {
      console.error('Error loading schedule:', error);
    }
  };

  const fetchTeacherData = async () => {
    try {
      setLoading(true);
      
      // Получаем обзор преподавателя (включает курсы, статистику)
      const teacherId = 1; // TODO: Получать из контекста пользователя
      const teacherResponse = await fetch(`http://localhost:8000/api/analytics/teacher/${teacherId}/overview`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (teacherResponse.ok) {
        const teacherData = await teacherResponse.json();
        setCourses(teacherData.courses || []);
        setStats(prev => ({
          ...prev,
          totalCourses: teacherData.overview.total_courses,
          totalStudents: 0, // TODO: Добавить подсчет студентов
          pendingSubmissions: teacherData.overview.pending_submissions,
          averageGrade: teacherData.overview.average_grade
        }));

        // Если есть курсы, подгружаем тренды и прогноз по первому курсу
        if ((teacherData.courses || []).length > 0) {
          const courseId = teacherData.courses[0].id;
          const trendsRes = await fetch(`http://localhost:8000/api/analytics/courses/${courseId}/trends?days=30&bucket=week`, {
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

          const forecastRes = await fetch(`http://localhost:8000/api/analytics/predict/performance?scope=course&target_id=${courseId}&horizon_days=14&bucket=day`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}` }
          });
          if (forecastRes.ok) {
            const data = await forecastRes.json();
            const series = (data.forecast || []).map(p => ({ index: p.index, pred_submissions: p.pred_submissions, pred_avg_grade: p.pred_avg_grade }));
            setForecastSeries(series);
          }
        }
      }

      // Получаем задания для отображения в pending submissions
      const assignmentsResponse = await fetch('http://localhost:8000/api/assignments/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (assignmentsResponse.ok) {
        const assignmentsData = await assignmentsResponse.json();
        setAssignments(assignmentsData.assignments || []);
      }

      // Получаем сдачи для отображения деталей
      const submissionsResponse = await fetch('http://localhost:8000/api/submissions/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token')}`
        }
      });
      
      if (submissionsResponse.ok) {
        const submissionsData = await submissionsResponse.json();
        setSubmissions(submissionsData.submissions || []);
      }

      // Получаем ближайшие занятия
      await loadSchedule();

    } catch (error) {
      console.error('Error fetching teacher data:', error);
    } finally {
      setLoading(false);
    }
  };
  const notifyScheduleChange = async (item) => {
    try {
      setScheduleStatus('Отправка уведомления...');
      const payload = {
        event_type: 'schedule_updated',
        data: {
          schedule_id: item.id,
          course_name: item.course?.title,
          course_id: item.course_id,
          schedule_date: String(item.schedule_date),
          start_time: String(item.start_time),
          end_time: String(item.end_time),
          location: item.location,
          instructor_name: item.instructor ? `${item.instructor.first_name} ${item.instructor.last_name}` : undefined,
          change_type: 'manual_notify',
        },
        channels: ['webhook'],
        priority: 'high'
      };
      const res = await fetch('http://localhost:8000/api/notifications/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token') || ''}`
        },
        body: JSON.stringify(payload)
      });
      const text = await res.text();
      if (res.ok) {
        setScheduleStatus('Уведомление отправлено');
      } else if (res.status === 401) {
        setScheduleStatus('Не авторизован. Войдите под админом/преподавателем.');
      } else {
        setScheduleStatus(`Ошибка (${res.status}): ${text}`);
      }
    } catch (e) {
      setScheduleStatus(`Ошибка: ${e.message}`);
    } finally {
      setTimeout(() => setScheduleStatus(""), 4000);
    }
  };

  const sendTestNotification = async (channel) => {
    try {
      setNotifyStatus(`Отправка ${channel}...`);
      const res = await fetch(`http://localhost:8000/api/notifications/test?channel=${channel}` , {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token') || ''}`
        }
      });
      const text = await res.text();
      if (res.ok) {
        setNotifyStatus(`Успех: ${channel}`);
      } else if (res.status === 401) {
        setNotifyStatus('Не авторизован. Войдите под админом/преподавателем.');
      } else {
        setNotifyStatus(`Ошибка (${res.status}): ${text}`);
      }
    } catch (e) {
      setNotifyStatus(`Ошибка: ${e.message}`);
    } finally {
      setTimeout(() => setNotifyStatus(""), 5000);
    }
  };

  const quickActions = [
    {
      title: t('teacher.createCourse'),
      description: t('teacher.createCourseDesc'),
      icon: '📚',
      action: () => window.location.href = '/teacher/courses/create',
      color: 'bg-blue-500'
    },
    {
      title: t('teacher.createAssignment'),
      description: t('teacher.createAssignmentDesc'),
      icon: '📝',
      action: () => window.location.href = '/teacher/assignments/create',
      color: 'bg-green-500'
    },
    {
      title: t('teacher.gradeSubmissions'),
      description: t('teacher.gradeSubmissionsDesc'),
      icon: '✅',
      action: () => window.location.href = '/teacher/submissions',
      color: 'bg-yellow-500'
    },
    {
      title: t('teacher.viewAnalytics'),
      description: t('teacher.viewAnalyticsDesc'),
      icon: '📊',
      action: () => window.location.href = '/teacher/analytics',
      color: 'bg-purple-500'
    }
  ];

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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {t('teacher.dashboardTitle')}
            </h1>
            <p className="text-gray-600">
              {t('teacher.dashboardSubtitle')}
            </p>
          </div>

          {/* KPI карточки */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <KPICard
              title={t('teacher.totalCourses')}
              value={stats.totalCourses}
              icon="📚"
              color="blue"
              change="+2"
              changeType="positive"
            />
            <KPICard
              title={t('teacher.totalStudents')}
              value={stats.totalStudents}
              icon="👥"
              color="green"
              change="+15"
              changeType="positive"
            />
            <KPICard
              title={t('teacher.pendingSubmissions')}
              value={stats.pendingSubmissions}
              icon="⏳"
              color="yellow"
              change="+5"
              changeType="neutral"
            />
            <KPICard
              title={t('teacher.averageGrade')}
              value={`${stats.averageGrade}%`}
              icon="📊"
              color="purple"
              change="+3.2%"
              changeType="positive"
            />
          </div>

          {/* Основной контент */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Быстрые действия */}
            <div className="lg:col-span-1">
              <QuickActions actions={quickActions} />
            </div>

            {/* Тренды по курсу (по первому курсу) */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Тренды курса</h3>
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

          {/* Прогноз по курсу */}
          {forecastSeries.length > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Прогноз по курсу на 14 дней</h3>
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

          {/* Ближайшие занятия */}
          <div className="mt-8">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Ближайшие занятия</h3>
                <div className="flex gap-2 text-sm">
                  <button onClick={() => { setScheduleRange('day'); loadSchedule('day'); }} className={`px-3 py-1 rounded ${scheduleRange==='day'?'bg-blue-600 text-white':'bg-gray-100 text-gray-700'}`}>День</button>
                  <button onClick={() => { setScheduleRange('week'); loadSchedule('week'); }} className={`px-3 py-1 rounded ${scheduleRange==='week'?'bg-blue-600 text-white':'bg-gray-100 text-gray-700'}`}>Неделя</button>
                </div>
              </div>
              <div className="p-6">
                {schedule.length > 0 ? (
                  <div className="space-y-4">
                    {schedule.map(item => (
                      <div key={item.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                            <span className="text-indigo-600">📅</span>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{item.course?.title || `Курс #${item.course_id}`}</h4>
                            <p className="text-sm text-gray-500">
                              {new Date(item.schedule_date).toLocaleDateString()} • {item.start_time}–{item.end_time} • {item.location || '—'}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-500">{item.lesson_type}</div>
                          <button onClick={() => notifyScheduleChange(item)} className="mt-2 px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">Сообщить об изменении</button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-gray-500">Нет занятий в выбранном диапазоне</div>
                )}
                {scheduleStatus && (
                  <div className="mt-3 text-sm text-gray-700">{scheduleStatus}</div>
                )}
              </div>
            </div>
          </div>

          {/* Последние курсы */}
          <div className="mt-8">
            {/* Тестовые уведомления */}
            <div className="bg-white rounded-lg shadow mb-8">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Тестовые уведомления</h3>
              </div>
              <div className="p-6">
                <div className="flex flex-wrap gap-3">
                  <button onClick={() => sendTestNotification('webhook')} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Webhook</button>
                  <button onClick={() => sendTestNotification('email')} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Email</button>
                  <button onClick={() => sendTestNotification('sms')} className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700">SMS</button>
                  <button onClick={() => sendTestNotification('push')} className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">Push</button>
                </div>
                {notifyStatus && (
                  <div className="mt-3 text-sm text-gray-700">{notifyStatus}</div>
                )}
                <div className="mt-2 text-xs text-gray-500">Требуется авторизация. Токен берётся из localStorage('token').</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t('teacher.recentCourses')}
                </h3>
              </div>
              <div className="p-6">
                {courses.length > 0 ? (
                  <div className="space-y-4">
                    {courses.slice(0, 5).map(course => (
                      <div key={course.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50">
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <span className="text-blue-600 text-xl">📚</span>
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900">{course.title}</h4>
                            <p className="text-sm text-gray-500">{course.description}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-500">
                            {new Date(course.start_date).toLocaleDateString()}
                          </div>
                          <div className="text-sm font-medium text-gray-900">
                            {course.students_count || 0} {t('teacher.students')}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-400 text-6xl mb-4">📚</div>
                    <p className="text-gray-500">{t('teacher.noCoursesYet')}</p>
                    <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                      {t('teacher.createFirstCourse')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Pending Submissions */}
          {stats.pendingSubmissions > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {t('teacher.pendingSubmissionsTitle')} ({stats.pendingSubmissions})
                  </h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    {submissions
                      .filter(sub => sub.status === 'submitted' && !sub.grades?.length)
                      .slice(0, 3)
                      .map(submission => (
                        <div key={submission.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                              <span className="text-yellow-600">⏳</span>
                            </div>
                            <div>
                              <h4 className="font-medium text-gray-900">
                                {assignments.find(a => a.id === submission.assignment_id)?.title || 'Unknown Assignment'}
                              </h4>
                              <p className="text-sm text-gray-500">
                                Submitted: {new Date(submission.submitted_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          <button className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700">
                            {t('teacher.gradeNow')}
                          </button>
                        </div>
                      ))}
                  </div>
                  {stats.pendingSubmissions > 3 && (
                    <div className="mt-4 text-center">
                      <button className="text-blue-600 hover:text-blue-800 font-medium">
                        {t('teacher.viewAllSubmissions')} ({stats.pendingSubmissions})
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeacherDashboard;

