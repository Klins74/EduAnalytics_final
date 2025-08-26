// src/api/analyticsApi.js

const API_BASE_URL = 'http://localhost:8000/api/analytics';

const handleResponse = async (response) => {
	if (!response.ok) {
		let message = `HTTP ${response.status}`;
		try {
			const errorData = await response.json();
			message = errorData.detail || message;
		} catch (_) {}
		throw new Error(message);
	}
	return await response.json();
};

const getToken = () => {
	return localStorage.getItem('accessToken') || localStorage.getItem('token');
};

const getHeaders = () => {
	const token = getToken();
	return {
		'Content-Type': 'application/json',
		...(token && { 'Authorization': `Bearer ${token}` })
	};
};

export const analyticsApi = {
	getCourseTrends: async (courseId, { days = 30, bucket = 'week' } = {}) => {
		const url = `${API_BASE_URL}/courses/${courseId}/trends?days=${days}&bucket=${bucket}`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},

	getStudentTrends: async (studentId, { days = 30, bucket = 'week' } = {}) => {
		const url = `${API_BASE_URL}/students/${studentId}/trends?days=${days}&bucket=${bucket}`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},

	getStudentPerformance: async (studentId) => {
		const url = `${API_BASE_URL}/students/${studentId}/performance`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},

	predictPerformance: async ({ scope, targetId, horizonDays = 14, bucket = 'day' }) => {
		const params = new URLSearchParams({
			scope,
			target_id: String(targetId),
			horizon_days: String(horizonDays),
			bucket,
		});
		const url = `${API_BASE_URL}/predict/performance?${params.toString()}`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},

	getCourseOverview: async (courseId) => {
		const url = `${API_BASE_URL}/courses/${courseId}/overview`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},

	getCourseAssignmentsAnalytics: async (courseId) => {
		const url = `${API_BASE_URL}/courses/${courseId}/assignments`;
		const response = await fetch(url, { headers: getHeaders() });
		return handleResponse(response);
	},
};

export default analyticsApi;


