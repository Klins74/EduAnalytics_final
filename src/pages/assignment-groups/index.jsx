import React, { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import moduleApi from '../../api/moduleApi';

const AssignmentGroups = () => {
	const { courseId } = useParams();
	const [groups, setGroups] = useState([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [creating, setCreating] = useState(false);
	const [form, setForm] = useState({ name: '', weight: 0 });
	const [submitting, setSubmitting] = useState(false);
	const [query, setQuery] = useState('');

	const loadGroups = async () => {
		try {
			setLoading(true);
			const data = await moduleApi.listAssignmentGroups(courseId);
			setGroups(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить группы заданий.');
			console.error('listAssignmentGroups error', e);
		} finally {
			setLoading(false);
		}
	};

	useEffect(() => {
		loadGroups();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [courseId]);

	const filtered = useMemo(() => {
		if (!query) return groups;
		const q = query.toLowerCase();
		return groups.filter(g => (g.name || '').toLowerCase().includes(q));
	}, [groups, query]);

	const handleCreate = async (e) => {
		e.preventDefault();
		if (!form.name.trim()) return;
		try {
			setSubmitting(true);
			await moduleApi.createAssignmentGroup({ course_id: Number(courseId), name: form.name.trim(), weight: Number(form.weight) || 0 });
			setForm({ name: '', weight: 0 });
			setCreating(false);
			await loadGroups();
		} catch (e) {
			setError('Не удалось создать группу.');
			console.error('createAssignmentGroup error', e);
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
							<h1 className="text-2xl font-semibold text-gray-900">Группы заданий курса #{courseId}</h1>
							<p className="text-gray-500 mt-1">Группируйте задания и задавайте вес в оценке.</p>
						</div>
						<Link to={`/courses/${courseId}`} className="text-blue-600 hover:text-blue-800">← Назад к курсу</Link>
					</div>

					<div className="mb-6 flex flex-col md:flex-row md:items-center md:space-x-4 space-y-3 md:space-y-0">
						<div className="relative w-full md:w-80">
							<input type="text" placeholder="Поиск по названию..." value={query} onChange={(e) => setQuery(e.target.value)} className="w-full border border-gray-200 bg-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
						</div>
						<button onClick={() => setCreating(v => !v)} className="inline-flex items-center justify-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">{creating ? 'Отменить' : 'Новая группа'}</button>
					</div>

					{creating && (
						<MotionFade>
							<form onSubmit={handleCreate} className="bg-white rounded-lg shadow p-4 mb-6 space-y-3">
								<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
									<div>
										<label className="block text-sm text-gray-700 mb-1">Название</label>
										<input type="text" value={form.name} onChange={(e) => setForm(s => ({ ...s, name: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
									<div>
										<label className="block text-sm text-gray-700 mb-1">Вес, %</label>
										<input type="number" min={0} max={100} value={form.weight} onChange={(e) => setForm(s => ({ ...s, weight: e.target.value }))} className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
									</div>
								</div>
								<div className="flex items-center justify-end space-x-2">
									<button type="button" onClick={() => setCreating(false)} className="px-4 py-2 rounded-lg border">Отмена</button>
									<button disabled={submitting} type="submit" className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">{submitting ? 'Сохранение...' : 'Создать'}</button>
								</div>
							</form>
						</MotionFade>
					)}

					{loading ? (
						<Loader />
					) : error ? (
						<div className="text-red-600">{error}</div>
					) : filtered.length === 0 ? (
						<EmptyState message={query ? 'Ничего не найдено.' : 'Групп пока нет.'} />
					) : (
						<div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
							{filtered.map((g, index) => (
								<MotionFade key={g.id} delay={index * 0.05}>
									<div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4 h-full flex flex-col">
										<h3 className="text-lg font-semibold text-gray-900 mb-1">{g.name}</h3>
										<p className="text-sm text-gray-600 flex-1">Вес: {g.weight ?? 0}%</p>
										<div className="mt-4 text-xs text-gray-400">ID: {g.id}</div>
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

export default AssignmentGroups;
