const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

function getAuthHeader() {
	const token = localStorage.getItem('accessToken') || localStorage.getItem('token') || '';
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiRequest(path, { method = 'GET', headers = {}, body } = {}) {
	const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
	const init = {
		method,
		headers: {
			'Content-Type': 'application/json',
			...getAuthHeader(),
			...headers,
		},
	};
	if (body !== undefined) {
		init.body = typeof body === 'string' ? body : JSON.stringify(body);
	}
	const res = await fetch(url, init);
	if (res.status === 401) {
		try {
			localStorage.removeItem('accessToken');
			localStorage.removeItem('token');
		} catch (_) {}
		if (typeof window !== 'undefined') {
			window.location.href = '/login';
		}
		const err = new Error('Unauthorized');
		err.status = 401;
		throw err;
	}
	if (!res.ok) {
		const text = await res.text().catch(() => '');
		const err = new Error(`API ${method} ${path} failed: ${res.status} ${text}`);
		err.status = res.status;
		throw err;
	}
	const contentType = res.headers.get('content-type') || '';
	if (contentType.includes('application/json')) {
		return res.json();
	}
	return res.text();
}

export const api = {
	get: (path, opts) => apiRequest(path, { ...opts, method: 'GET' }),
	post: (path, body, opts) => apiRequest(path, { ...opts, method: 'POST', body }),
	put: (path, body, opts) => apiRequest(path, { ...opts, method: 'PUT', body }),
	del: (path, opts) => apiRequest(path, { ...opts, method: 'DELETE' }),
};
