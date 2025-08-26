import React, { useState } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Loader from '../../components/ui/Loader';
import EmptyState from '../../components/ui/EmptyState';
import MotionFade from '../../components/ui/motion/MotionFade';
import { quizApi } from '../../api/quizApi';

const QuizPage = () => {
	const [quizId, setQuizId] = useState('');
	const [attempt, setAttempt] = useState(null);
	const [questions, setQuestions] = useState([]);
	const [answers, setAnswers] = useState({});
	const [loading, setLoading] = useState(false);
	const [submitting, setSubmitting] = useState(false);
	const [error, setError] = useState('');

	const loadQuestions = async (id) => {
		try {
			setLoading(true);
			const data = await quizApi.getQuestions(id);
			setQuestions(Array.isArray(data) ? data : []);
		} catch (e) {
			setError('Не удалось загрузить вопросы.');
			console.error(e);
		} finally {
			setLoading(false);
		}
	};

	const startAttempt = async () => {
		try {
			setSubmitting(true);
			const att = await quizApi.startAttempt(Number(quizId));
			setAttempt(att);
			await loadQuestions(Number(quizId));
		} catch (e) {
			setError('Не удалось начать попытку.');
			console.error(e);
		} finally {
			setSubmitting(false);
		}
	};

	const handleChange = (q, value) => setAnswers((s) => ({ ...s, [q.id]: value }));

	const submit = async () => {
		if (!attempt) return;
		try {
			setSubmitting(true);
			const payload = Object.entries(answers)
				.map(([qid, val]) => {
					const q = questions.find((qq) => String(qq.id) === String(qid));
					if (!q) return null;
					if (q.type === 'multiple_choice') {
						return { question_id: Number(qid), selected_options: Array.isArray(val) ? val.map(Number) : [Number(val)] };
					}
					return { question_id: Number(qid), answer_text: String(val ?? '') };
				})
				.filter(Boolean);
			await quizApi.submitAttempt(attempt.id, payload);
			alert('Попытка отправлена.');
		} catch (e) {
			setError('Не удалось отправить ответы.');
			console.error(e);
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
					<h1 className="text-2xl font-semibold text-gray-900 mb-4">Мини‑демо прохождения квиза</h1>

					<div className="bg-white rounded-lg shadow p-4 mb-6">
						<div className="flex items-end space-x-3">
							<div className="flex-1">
								<label className="block text-sm text-gray-700 mb-1">ID квиза</label>
								<input value={quizId} onChange={(e) => setQuizId(e.target.value)} type="number" className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
							</div>
							<button disabled={!quizId || submitting} onClick={startAttempt} className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">Начать попытку</button>
						</div>
					</div>

					{loading ? (
						<Loader />
					) : error ? (
						<div className="text-red-600">{error}</div>
					) : attempt && questions.length > 0 ? (
						<div className="space-y-4">
							{questions.map((q, index) => (
								<MotionFade key={q.id} delay={index * 0.03}>
									<div className="bg-white rounded-lg shadow p-4">
										<div className="flex items-start justify-between">
											<div>
												<div className="text-sm text-gray-500">{q.type}</div>
												<h3 className="text-lg font-semibold text-gray-900">{q.text}</h3>
											</div>
											<div className="text-xs text-gray-400">ID: {q.id}</div>
										</div>

										{q.type === 'multiple_choice' ? (
											<div className="mt-3 space-y-2">
												{(q.options || []).map((opt) => (
													<label key={opt.id} className="flex items-center space-x-2 text-sm">
														<input
															type="checkbox"
															checked={Array.isArray(answers[q.id]) ? answers[q.id].includes(opt.id) : false}
															onChange={(e) => {
																const prev = Array.isArray(answers[q.id]) ? answers[q.id] : [];
																handleChange(q, e.target.checked ? [...prev, opt.id] : prev.filter((x) => x !== opt.id));
															}}
															className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
														/>
														<span>{opt.text}</span>
													</label>
												))}
											</div>
										) : (
											<div className="mt-3">
												<input value={answers[q.id] || ''} onChange={(e) => handleChange(q, e.target.value)} type="text" className="w-full border border-gray-200 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
											</div>
										)}
									</div>
								</MotionFade>
							))}

							<div className="pt-2">
								<button disabled={submitting} onClick={submit} className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50">Отправить ответы</button>
							</div>
						</div>
					) : attempt ? (
						<EmptyState message="Нет вопросов в квизе" />
					) : (
						<EmptyState message="Введите ID квиза и начните попытку" />
					)}
				</div>
			</div>
		</div>
	);
};

export default QuizPage;
