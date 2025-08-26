import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import MotionFade from '../../components/ui/motion/MotionFade';
import Loader from '../../components/ui/Loader';
import { getCourse } from '../../api/courseApi';
import { analyticsApi } from '../../api/analyticsApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const CourseDetail = () => {
	const { courseId } = useParams();
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [course, setCourse] = useState(null);
	const [trendLoading, setTrendLoading] = useState(false);
	const [trendError, setTrendError] = useState('');
	const [trendSeries, setTrendSeries] = useState([]);
	const [bucket, setBucket] = useState('week');
	const [horizon, setHorizon] = useState('month');
	const [forecast, setForecast] = useState([]);
	const [assignments, setAssignments] = useState([]);
	const [sortKey, setSortKey] = useState('average_grade');
	const [sortDir, setSortDir] = useState('desc');

	useEffect(() => {
		let mounted = true;
		(async () => {
			try {
				setLoading(true);
				const data = await getCourse(courseId);
				if (!mounted) return;
				setCourse(data);
			} catch (e) {
				setError(e.message || 'Ошибка загрузки курса');
			} finally {
				setLoading(false);
			}
		})();
		return () => { mounted = false; };
	}, [courseId]);

	useEffect(() => {
		let mounted = true;
		(async () => {
			try {
				setTrendLoading(true);
				setTrendError('');
				const id = Number(courseId);
				const trends = await analyticsApi.getCourseTrends(id, { days: 60, bucket });
				if (!mounted) return;
				setTrendSeries(Array.isArray(trends.series) ? trends.series : []);
				const horizonDays = horizon === 'week' ? 7 : horizon === 'month' ? 30 : 90;
				const pred = await analyticsApi.predictPerformance({ scope: 'course', targetId: id, horizonDays, bucket: bucket === 'week' ? 'week' : 'day' });
				if (!mounted) return;
				setForecast(Array.isArray(pred.forecast) ? pred.forecast : []);
				const a = await analyticsApi.getCourseAssignmentsAnalytics(id);
				if (!mounted) return;
				setAssignments(Array.isArray(a.assignments_analytics) ? a.assignments_analytics : []);
			} catch (e) {
				setTrendError(e.message || 'Не удалось загрузить тренды');
			} finally {
				setTrendLoading(false);
			}
		})();
		return () => { mounted = false; };
	}, [courseId, bucket, horizon]);

	return (
		<div className="min-h-screen bg-gray-50">
			<Header />
			<div className="flex">
				<Sidebar />
				<div className="flex-1 p-6">
					<MotionFade>
						<h1 className="text-2xl font-semibold text-gray-900 mb-4">Курс #{courseId}</h1>
					</MotionFade>
					<div className="bg-white rounded-lg shadow p-6">
						{loading ? (
							<Loader />
						) : error ? (
							<div className="text-red-600">{error}</div>
						) : (
							<>
								<MotionFade>
									<div className="mb-6">
										<div className="text-lg font-medium text-gray-900">{course?.title || '—'}</div>
										<div className="text-sm text-gray-500 mt-1">{course?.description || 'Без описания'}</div>
									</div>
								</MotionFade>
								<div className="grid grid-cols-1 gap-4 mb-6">
									<div className="bg-white rounded-lg border p-4">
										<div className="flex items-center justify-between mb-3">
											<div className="text-base font-medium text-gray-900">Аналитика курса</div>
											<div className="flex items-center gap-2">
												<select value={bucket} onChange={(e) => setBucket(e.target.value)} className="border rounded px-2 py-1 text-sm">
													<option value="day">Дни</option>
													<option value="week">Недели</option>
												</select>
												<select value={horizon} onChange={(e) => setHorizon(e.target.value)} className="border rounded px-2 py-1 text-sm">
													<option value="week">1 неделя</option>
													<option value="month">1 месяц</option>
													<option value="quarter">3 месяца</option>
												</select>
											</div>
										</div>
										{trendLoading ? (
											<div className="h-64 flex items-center justify-center text-gray-500">Загрузка аналитики…</div>
										) : trendError ? (
											<div className="text-red-600 text-sm">{trendError}</div>
										) : (
											<div className="h-72">
												<ResponsiveContainer width="100%" height="100%">
													<LineChart data={trendSeries}>
														<CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
														<XAxis dataKey="bucket_start" tick={{ fontSize: 12 }} />
														<YAxis tick={{ fontSize: 12 }} />
														<Tooltip />
														<Line type="monotone" dataKey="submissions" stroke="#7C3AED" strokeWidth={2} dot={false} name="Сдачи" />
														<Line type="monotone" dataKey="average_grade" stroke="#3B82F6" strokeWidth={3} dot={{ r: 3 }} name="Средний балл" />
														<Line type="monotone" dataKey="on_time_rate" stroke="#10B981" strokeWidth={2} dot={false} name="Своевременность, %" />
													</LineChart>
												</ResponsiveContainer>
											</div>
										)}
										<div className="mt-4 text-sm text-gray-600">Прогноз на горизонт: {forecast.length} точек</div>
									</div>
								</div>

								{/* Assignments analytics table */}
								<div className="bg-white rounded-lg border p-4 mb-6">
									<div className="flex items-center justify-between mb-3">
										<div className="text-base font-medium text-gray-900">Задания курса</div>
										<div className="flex items-center gap-2 text-sm">
											<label>Сортировать по:</label>
											<select value={sortKey} onChange={(e)=>setSortKey(e.target.value)} className="border rounded px-2 py-1">
												<option value="average_grade">Средний балл</option>
												<option value="total_submissions">Сдачи</option>
												<option value="on_time_submissions">Вовремя</option>
												<option value="late_submissions">Опоздания</option>
											</select>
											<select value={sortDir} onChange={(e)=>setSortDir(e.target.value)} className="border rounded px-2 py-1">
												<option value="desc">По убыванию</option>
												<option value="asc">По возрастанию</option>
											</select>
										</div>
									</div>
									<div className="overflow-x-auto">
										<table className="min-w-full text-sm">
											<thead>
												<tr className="text-left text-gray-600">
													<th className="p-2">Задание</th>
													<th className="p-2">Дедлайн</th>
													<th className="p-2">Сдачи</th>
													<th className="p-2">Средний балл</th>
													<th className="p-2">Вовремя</th>
													<th className="p-2">Опоздания</th>
												</tr>
											</thead>
											<tbody>
												{[...assignments].sort((a,b)=>{
													const av = (a.statistics||{});
													const bv = (b.statistics||{});
													const get = k => Number(av[k] ?? 0) - Number(bv[k] ?? 0);
													const diff = sortKey === 'average_grade' ? (Number(av.average_grade||0) - Number(bv.average_grade||0)) : get(sortKey);
													return sortDir === 'asc' ? diff : -diff;
												}).map((a)=> (
													<tr key={a.assignment_id} className="border-t">
														<td className="p-2">{a.title}</td>
														<td className="p-2">{a.due_date ? String(a.due_date).slice(0,10) : '—'}</td>
														<td className="p-2">{a.statistics?.total_submissions ?? 0}</td>
														<td className="p-2">{(a.statistics?.average_grade ?? 0).toFixed(2)}</td>
														<td className="p-2">{a.statistics?.on_time_submissions ?? 0}</td>
														<td className="p-2">{a.statistics?.late_submissions ?? 0}</td>
													</tr>
												))}
											</tbody>
										</table>
									</div>
								</div>

								<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
									<MotionFade delay={0.05}><Link to={`/courses/${courseId}/pages`} className="block bg-gray-50 border rounded-lg p-6 hover:shadow-md transition-shadow">Страницы</Link></MotionFade>
									<MotionFade delay={0.1}><Link to={`/courses/${courseId}/discussions`} className="block bg-gray-50 border rounded-lg p-6 hover:shadow-md transition-shadow">Обсуждения</Link></MotionFade>
									<MotionFade delay={0.15}><Link to={`/courses/${courseId}/modules`} className="block bg-gray-50 border rounded-lg p-6 hover:shadow-md transition-shadow">Модули</Link></MotionFade>
									<MotionFade delay={0.2}><Link to={`/courses/${courseId}/assignment-groups`} className="block bg-gray-50 border rounded-lg p-6 hover:shadow-md transition-shadow">Группы заданий</Link></MotionFade>
									<MotionFade delay={0.25}><Link to={`/courses/${courseId}/quizzes`} className="block bg-gray-50 border rounded-lg p-6 hover:shadow-md transition-shadow">Квизы</Link></MotionFade>
								</div>
							</>
						)}
					</div>
				</div>
			</div>
		</div>
	);
};

export default CourseDetail;
