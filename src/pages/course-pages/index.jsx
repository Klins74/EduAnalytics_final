import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import pageApi from '../../api/pageApi';

const truncate = (text, length = 160) => {
	if (!text) return '';
	return text.length > length ? `${text.slice(0, length)}…` : text;
};

const Badge = ({ children, color = 'blue' }) => (
	<span
		className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-${color}-100 text-${color}-800`}
	>
		{children}
	</span>
);

const CoursePages = () => {
	const { courseId } = useParams();
	const [pages, setPages] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [query, setQuery] = useState('');
	const [creating, setCreating] = useState(false);
	const [form, setForm] = useState({ title: '', content: '', published: false });
	const [submitting, setSubmitting] = useState(false);

	const loadPages = async () => {
		try {
			setLoading(true);
			const data = await pageApi.listPages(courseId);
			setPages(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить страницы.');
			console.error('listPages error', e);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadPages();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [courseId]);

	const filtered = useMemo(() => {
		if (!query) return pages;
		const q = query.toLowerCase();
		return pages.filter(p => (p.title || '').toLowerCase().includes(q) || (p.content || '').toLowerCase().includes(q));
	}, [pages, query]);

	const handleCreate = async (e) => {
		e.preventDefault();
		if (!form.title.trim()) return;
		try {
			setSubmitting(true);
			await pageApi.createPage({
				course_id: Number(courseId),
				title: form.title.trim(),
				content: form.content,
				published: !!form.published,
			});
			setForm({ title: '', content: '', published: false });
			setCreating(false);
			await loadPages();
		} catch (e) {
			setError('Не удалось создать страницу.');
			console.error('createPage error', e);
		} finally {
			setSubmitting(false);
		}
	};

	const togglePublished = async (page) => {
		try {
			await pageApi.updatePage(page.id, { ...page, published: !page.published });
			await loadPages();
		} catch (e) {
			setError('Не удалось изменить статус публикации.');
			console.error('updatePage error', e);
		}
	};

	const removePage = async (pageId) => {
		if (!confirm('Удалить страницу?')) return;
		try {
			await pageApi.deletePage(pageId);
			await loadPages();
		} catch (e) {
			setError('Не удалось удалить страницу.');
			console.error('deletePage error', e);
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
							<h1 className="text-2xl font-semibold text-gray-900">Страницы курса #{courseId}</h1>
							<p className="text-gray-500 mt-1">Управляйте информационными страницами, публикуйте и редактируйте контент.</p>
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
							{creating ? 'Отменить' : 'Новая страница'}
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
											checked={form.published}
											onChange={(e) => setForm(s => ({ ...s, published: e.target.checked }))}
											className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
										/>
										<span>Опубликовано</span>
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
						<EmptyState message={query ? 'Ничего не найдено.' : 'Страниц пока нет.'} />
					) : (
						<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
							{filtered.map((p, index) => (
								<MotionFade key={p.id} delay={index * 0.04}>
									<div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4 h-full flex flex-col">
										<div className="flex items-start justify-between mb-2">
											<h3 className="text-lg font-semibold text-gray-900">{p.title}</h3>
											{p.published ? <Badge color="green">Опубликовано</Badge> : <Badge color="gray">Черновик</Badge>}
										</div>
										<p className="text-sm text-gray-600 flex-1">{truncate(p.content, 220)}</p>
										<div className="mt-4 flex items-center justify-between">
											<div className="text-xs text-gray-400">ID: {p.id}</div>
											<div className="space-x-2">
												<button onClick={() => togglePublished(p)} className="px-3 py-1 text-sm rounded border">
													{p.published ? 'Снять с публикации' : 'Опубликовать'}
												</button>
												<button onClick={() => removePage(p.id)} className="px-3 py-1 text-sm rounded bg-red-50 text-red-600 hover:bg-red-100">Удалить</button>
											</div>
										</div>
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

export default CoursePages;
