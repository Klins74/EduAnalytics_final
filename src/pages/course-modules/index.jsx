import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import moduleApi from '../../api/moduleApi';

const typeLabels = {
	page: 'Страница',
	assignment: 'Задание',
	quiz: 'Квиз',
};

const CourseModules = () => {
	const { courseId } = useParams();
	const [modules, setModules] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [creating, setCreating] = useState(false);
	const [form, setForm] = useState({ title: '', position: 0 });
	const [submitting, setSubmitting] = useState(false);

	const [itemForm, setItemForm] = useState({ type: 'page', title: '', content: '', page_id: null, assignment_id: null, quiz_id: null });
	const [selectedModule, setSelectedModule] = useState(null);
	const [addingItem, setAddingItem] = useState(false);

	const loadModules = async () => {
		try {
			setLoading(true);
			const data = await moduleApi.listModules(courseId);
			setModules(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить модули.');
			console.error('listModules error', e);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadModules();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [courseId]);

	const handleCreate = async (e) => {
		e.preventDefault();
		if (!form.title.trim()) return;
		try {
			setSubmitting(true);
			await moduleApi.createModule({ course_id: Number(courseId), title: form.title.trim(), position: Number(form.position) || 0 });
			setForm({ title: '', position: 0 });
			setCreating(false);
			await loadModules();
		} catch (e) {
			setError('Не удалось создать модуль.');
			console.error('createModule error', e);
		} finally {
			setSubmitting(false);
		}
	};

	const handleAddItem = async (e) => {
		e.preventDefault();
		if (!selectedModule) return;
		try {
			setSubmitting(true);
			await moduleApi.addModuleItem(selectedModule.id, {
				type: itemForm.type,
				title: itemForm.title,
				content: itemForm.content,
				page_id: itemForm.page_id,
				assignment_id: itemForm.assignment_id,
				quiz_id: itemForm.quiz_id,
			});
			setItemForm({ type: 'page', title: '', content: '', page_id: null, assignment_id: null, quiz_id: null });
			setAddingItem(false);
			await loadModules();
		} catch (e) {
			setError('Не удалось добавить элемент.');
			console.error('addModuleItem error', e);
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
							<h1 className="text-2xl font-semibold text-gray-900">Модули курса #{courseId}</h1>
							<p className="text-gray-500 mt-1">Структурируйте курс по модулям и добавляйте элементы.</p>
						</div>
						<Link to={`/courses/${courseId}`} className="text-blue-600 hover:text-blue-800">← Назад к курсу</Link>
					</div>

					<div className="mb-6 flex items-center space-x-3">
						<button onClick={() => setCreating(v => !v)} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">{creating ? 'Отменить' : 'Новый модуль'}</button>
						{selectedModule && (
							<button onClick={() => setAddingItem(v => !v)} className="px-4 py-2 rounded-lg border">{addingItem ? 'Отменить' : `Добавить элемент в "${selectedModule.title}"`}</button>
						)}
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
										<label className="block text-sm text-gray-700 mb-1">Позиция</label>
										<input type="number" value={form.position} onChange={(e) => setForm(s => ({ ...s, position: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
								</div>
								<div className="flex items-center justify-end space-x-2">
									<button type="button" onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border">Отмена</button>
									<button disabled={submitting} type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Сохранение...' : 'Создать'}</button>
								</div>
							</form>
						</MotionFade>
					)}

					{addingItem && selectedModule && (
						<MotionFade>
							<form onSubmit={handleAddItem} className="bg-white rounded-lg shadow p-4 mb-6 space-y-3">
								<div className="grid grid-cols-1 md:grid-cols-3 gap-3">
									<div>
										<label className="block text-sm text-gray-700 mb-1">Тип</label>
										<select value={itemForm.type} onChange={(e) => setItemForm(s => ({ ...s, type: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent">
											<option value="page">Страница</option>
											<option value="assignment">Задание</option>
											<option value="quiz">Квиз</option>
										</select>
									</div>
									<div>
										<label className="block text-sm text-gray-700 mb-1">Заголовок</label>
										<input type="text" value={itemForm.title} onChange={(e) => setItemForm(s => ({ ...s, title: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
									<div>
										<label className="block text-sm text-gray-700 mb-1">Контент (опц.)</label>
										<input type="text" value={itemForm.content} onChange={(e) => setItemForm(s => ({ ...s, content: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
								</div>
								<div className="flex items-center justify-end space-x-2">
									<button type="button" onClick={() => setAddingItem(false)} className="px-4 py-2 rounded-lg border">Отмена</button>
									<button disabled={submitting} type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Добавление...' : 'Добавить'}</button>
								</div>
							</form>
						</MotionFade>
					)}

					{loading ? (
						<Loader />
					) : error ? (
						<div className="text-red-600">{error}</div>
					) : modules.length === 0 ? (
						<EmptyState message="Модулей пока нет." />
					) : (
						<div className="space-y-4">
							{modules.map((m, index) => (
								<MotionFade key={m.id} delay={index * 0.05}>
									<div className="bg-white rounded-lg shadow">
										<div className="px-4 py-3 border-b flex items-center justify-between">
											<div className="font-semibold text-gray-900">{m.title}</div>
											<button onClick={() => { setSelectedModule(m); setAddingItem(true); }} className="text-blue-600 hover:text-blue-800 text-sm">+ Добавить элемент</button>
										</div>
										<div className="divide-y">
											{(m.items || []).length === 0 ? (
												<div className="px-4 py-3 text-gray-500 text-sm">Нет элементов</div>
											) : (
												m.items.map((it) => (
													<div key={it.id} className="px-4 py-3 flex items-center justify-between">
														<div>
															<div className="text-gray-900">{it.title}</div>
															<div className="text-xs text-gray-500">{typeLabels[it.type] || it.type} • ID: {it.id}</div>
														</div>
														<Link to={it.type === 'page' ? `/courses/${courseId}/pages` : it.type === 'quiz' ? `/courses/${courseId}/quizzes` : `/courses/${courseId}` } className="text-blue-600 hover:text-blue-800 text-sm">Открыть</Link>
													</div>
												))
											)}
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

export default CourseModules;
