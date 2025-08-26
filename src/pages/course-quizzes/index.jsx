import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import { quizApi } from '../../api/quizApi';
import userApi from '../../api/userApi';

const CourseQuizzes = () => {
	const { courseId } = useParams();
	const [quizzes, setQuizzes] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [creating, setCreating] = useState(false);
	const [form, setForm] = useState({ title: '', description: '', time_limit: null, attempts_allowed: 1 });
	const [currentUser, setCurrentUser] = useState(null);

	useEffect(() => {
		userApi.getCurrentUser().then(setCurrentUser).catch(() => {});
	}, []);
	const [submitting, setSubmitting] = useState(false);
	const [query, setQuery] = useState('');

	const loadQuizzes = async () => {
		try {
			setLoading(true);
			const data = await quizApi.getQuizzesByCourse(courseId);
			setQuizzes(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить квизы.');
			console.error('getQuizzesByCourse error', e);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadQuizzes();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [courseId]);

	const filtered = useMemo(() => {
		if (!query) return quizzes;
		const q = query.toLowerCase();
		return quizzes.filter(qz => (qz.title || '').toLowerCase().includes(q) || (qz.description || '').toLowerCase().includes(q));
	}, [quizzes, query]);

	const handleCreate = async (e) => {
		e.preventDefault();
		if (!form.title.trim()) return;
		try {
			setSubmitting(true);
			await quizApi.createQuiz({
				course_id: Number(courseId),
				title: form.title.trim(),
				description: form.description,
				time_limit: form.time_limit ? Number(form.time_limit) : null,
				attempts_allowed: Number(form.attempts_allowed) || 1,
			});
			setForm({ title: '', description: '', time_limit: null, attempts_allowed: 1 });
			setCreating(false);
			await loadQuizzes();
		} catch (e) {
			setError('Не удалось создать квиз.');
			console.error('createQuiz error', e);
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<div className="min-h-screen bg-gray-50">
			<Header />
			<div className="flex">
				<Sidebar />
				<div className="flex-1 p-6">
					<div className="flex items-center justify-between mb-6">
						<div>
							<h1 className="text-2xl font-semibold text-gray-900">Квизы курса #{courseId}</h1>
							<p className="text-gray-500 mt-1">Управляйте квизами курса и создавайте новые.</p>
						</div>
						<Link to={`/courses/${courseId}`} className="text-blue-600 hover:text-blue-800">← Назад к курсу</Link>
					</div>

					<div className="mb-6 flex flex-col md:flex-row md:items-center md:space-x-4 space-y-3 md:space-y-0">
						<div className="relative w-full md:w-80">
							<input
								type="text"
								placeholder="Поиск по заголовку или описанию..."
								value={query}
								onChange={(e) => setQuery(e.target.value)}
								className="w-full border border-gray-200 bg-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<button onClick={() => setCreating(v => !v)} className="inline-flex items-center justify-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">{creating ? 'Отменить' : 'Новый квиз'}</button>
					</div>

					{creating && (
						<MotionFade>
							<form onSubmit={handleCreate} className="bg-white rounded-lg shadow p-4 mb-6 space-y-3">
								<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
									<div>
										<label className="block text-sm text-gray-700 mb-1">Название</label>
										<input type="text" value={form.title} onChange={(e) => setForm(s => ({ ...s, title: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
									<div>
										<label className="block text-sm text-gray-700 mb-1">Ограничение по времени (мин)</label>
										<input type="number" value={form.time_limit || ''} onChange={(e) => setForm(s => ({ ...s, time_limit: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
								</div>
								<div>
									<label className="block text-sm text-gray-700 mb-1">Описание</label>
									<textarea rows={4} value={form.description} onChange={(e) => setForm(s => ({ ...s, description: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
								</div>
								<div className="flex items-center justify-between">
									<label className="inline-flex items-center space-x-2 text-sm text-gray-700">
										<span>Разрешено попыток:</span>
										<input type="number" min={1} value={form.attempts_allowed} onChange={(e) => setForm(s => ({ ...s, attempts_allowed: e.target.value }))} className="w-20 border border-gray-200 rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</label>
									<div className="space-x-2">
										<button type="button" onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border">Отмена</button>
										<button disabled={submitting} type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Сохранение...' : 'Создать'}</button>
									</div>
								</div>
							</form>
						</MotionFade>
					)}

					{loading ? (
						<Loader />
					) : error ? (
						<div className="text-red-600">{error}</div>
					) : filtered.length === 0 ? (
						<EmptyState message={query ? 'Ничего не найдено.' : 'Квизов пока нет.'} />
					) : (
						<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
							{filtered.map((qz, index) => (
								<MotionFade key={qz.id} delay={index * 0.05}>
									<div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4 h-full flex flex-col">
										<h3 className="text-lg font-semibold text-gray-900 mb-1">{qz.title}</h3>
										<p className="text-sm text-gray-600 flex-1">{qz.description || 'Нет описания'}</p>
										<div className="mt-4 text-xs text-gray-400">ID: {qz.id}</div>
									</div>
								</MotionFade>
							))}
						</div>
					)}
				</div>
			</div>
		</div>
	);
};

export default CourseQuizzes;
