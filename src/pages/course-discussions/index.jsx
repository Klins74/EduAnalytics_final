import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import discussionApi from '../../api/discussionApi';

const CourseDiscussions = () => {
	const { courseId } = useParams();
	const [topics, setTopics] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [query, setQuery] = useState('');
	const [creating, setCreating] = useState(false);
	const [form, setForm] = useState({ title: '', content: '', locked: false });
	const [submitting, setSubmitting] = useState(false);

	const loadTopics = async () => {
		try {
			setLoading(true);
			const data = await discussionApi.listTopics(courseId);
			setTopics(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить обсуждения.');
			console.error('listTopics error', e);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadTopics();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [courseId]);

	const filtered = useMemo(() => {
		if (!query) return topics;
		const q = query.toLowerCase();
		return topics.filter(t => (t.title || '').toLowerCase().includes(q) || (t.content || '').toLowerCase().includes(q));
	}, [topics, query]);

	const handleCreate = async (e) => {
		e.preventDefault();
		if (!form.title.trim()) return;
		try {
			setSubmitting(true);
			await discussionApi.createTopic({
				course_id: Number(courseId),
				title: form.title.trim(),
				content: form.content,
				locked: !!form.locked,
			});
			setForm({ title: '', content: '', locked: false });
			setCreating(false);
			await loadTopics();
		} catch (e) {
			setError('Не удалось создать обсуждение.');
			console.error('createTopic error', e);
		} finally {
			setSubmitting(false);
		}
	};

	const toggleLock = async (topic) => {
		try {
			await discussionApi.lockTopic(topic.id, !topic.locked);
			await loadTopics();
		} catch (e) {
			setError('Не удалось изменить статус темы.');
			console.error('lockTopic error', e);
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
							<h1 className="text-2xl font-semibold text-gray-900">Обсуждения курса #{courseId}</h1>
							<p className="text-gray-500 mt-1">Создавайте темы для обсуждений и ведите диалог со студентами.</p>
						</div>
						<Link to={`/courses/${courseId}`} className="text-blue-600 hover:text-blue-800">← Назад к курсу</Link>
					</div>

					<div className="mb-6 flex flex-col md:flex-row md:items-center md:space-x-4 space-y-3 md:space-y-0">
						<div className="relative w-full md:w-80">
							<input
								type="text"
								placeholder="Поиск по заголовку или содержанию..."
								value={query}
								onChange={(e) => setQuery(e.target.value)}
								className="w-full border border-gray-200 bg-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
							/>
						</div>
						<button
							onClick={() => setCreating(v => !v)}
							className="inline-flex items-center justify-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
						>
							{creating ? 'Отменить' : 'Новая тема'}
						</button>
					</div>

					{creating && (
						<MotionFade>
							<form onSubmit={handleCreate} className="bg-white rounded-lg shadow p-4 mb-6 space-y-3">
								<div>
									<label className="block text-sm text-gray-700 mb-1">Заголовок</label>
									<input
										type="text"
										value={form.title}
										onChange={(e) => setForm(s => ({ ...s, title: e.target.value }))}
										className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</div>
								<div>
									<label className="block text-sm text-gray-700 mb-1">Содержимое</label>
									<textarea
										rows={6}
										value={form.content}
										onChange={(e) => setForm(s => ({ ...s, content: e.target.value }))}
										className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</div>
								<div className="flex items-center justify-between">
									<label className="inline-flex items-center space-x-2">
										<input
											type="checkbox"
											checked={form.locked}
											onChange={(e) => setForm(s => ({ ...s, locked: e.target.checked }))}
											className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
										/>
										<span>Заблокировано</span>
									</label>
									<div className="space-x-2">
										<button type="button" onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border">Отмена</button>
										<button disabled={submitting} type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
											{submitting ? 'Сохранение...' : 'Создать'}
										</button>
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
						<EmptyState message={query ? 'Ничего не найдено.' : 'Тем пока нет.'} />
					) : (
						<div className="space-y-4">
							{filtered.map((t, index) => (
								<MotionFade key={t.id} delay={index * 0.05}>
									<div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
										<div className="flex items-start justify-between">
											<div>
												<h3 className="text-lg font-semibold text-gray-900">{t.title}</h3>
												<p className="text-sm text-gray-600 mt-1">{(t.content || '').slice(0, 220)}{(t.content || '').length > 220 ? '…' : ''}</p>
											</div>
											<div className="space-x-2">
												<button onClick={() => toggleLock(t)} className="px-3 py-1 text-sm rounded border">
													{t.locked ? 'Разблокировать' : 'Заблокировать'}
												</button>
											</div>
										</div>
										<div className="mt-3 text-xs text-gray-400">ID: {t.id}</div>
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

export default CourseDiscussions;
