import React, { useEffect, useState } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import { listCourses } from '../../api/courseApi';
import { Link } from 'react-router-dom';

const CoursesList = () => {
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState('');
	const [courses, setCourses] = useState([]);

	useEffect(() => {
		let mounted = true;
		(async () => {
			try {
				setLoading(true);
				const data = await listCourses();
				if (!mounted) return;
				setCourses(data?.courses || []);
			} catch (e) {
				setError(e.message || 'Ошибка загрузки курсов');
			} finally {
				setLoading(false);
			}
		})();
		return () => { mounted = false; };
	}, []);

	return (
		<div className="min-h-screen bg-gray-50">
			<Header />
			<div className="flex">
				<Sidebar />
				<div className="flex-1 p-6">
					<MotionFade>
						<h1 className="text-2xl font-semibold text-gray-900 mb-4">Курсы</h1>
					</MotionFade>
					<div className="bg-white rounded-lg shadow p-6">
						{loading ? (
							<Loader />
						) : error ? (
							<div className="text-red-600">{error}</div>
						) : courses.length === 0 ? (
							<EmptyState title="Курсов нет" description="Создайте курс в админ-панели или назначьте себя владельцем." />
						) : (
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
								{courses.map((c, i) => (
									<MotionFade key={c.id} delay={i * 0.05}>
										<Link to={`/courses/${c.id}`} className="block border rounded-lg p-5 hover:shadow-md transition-shadow">
											<div className="text-lg font-medium text-gray-900">{c.title}</div>
											<div className="text-sm text-gray-500 mt-1 line-clamp-2">{c.description || 'Без описания'}</div>
											<div className="text-xs text-gray-400 mt-2">ID: {c.id}</div>
										</Link>
									</MotionFade>
								))}
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
};

export default CoursesList;
