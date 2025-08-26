import { api } from './client';

export async function listCourses({ skip = 0, limit = 100, owner_id } = {}) {
	const params = new URLSearchParams();
	params.set('skip', String(skip));
	params.set('limit', String(limit));
	if (owner_id) params.set('owner_id', String(owner_id));
	return api.get(`/courses/?${params.toString()}`);
}

export async function getCourse(courseId) {
	return api.get(`/courses/${courseId}`);
}
