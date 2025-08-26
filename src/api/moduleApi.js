const API_BASE = 'http://localhost:8000/api';

const authHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const jsonHeaders = () => ({ 'Content-Type': 'application/json', ...authHeaders() });

const request = async (url, options = {}) => {
  const res = await fetch(url, options);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
};

const moduleApi = {
  listModules: (courseId) => request(`${API_BASE}/modules/course/${courseId}`, { headers: authHeaders() }),
  createModule: (data) => request(`${API_BASE}/modules/`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  addModuleItem: (moduleId, data) => request(`${API_BASE}/modules/${moduleId}/items`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  listAssignmentGroups: (courseId) => request(`${API_BASE}/assignment-groups/course/${courseId}`, { headers: authHeaders() }),
  createAssignmentGroup: (data) => request(`${API_BASE}/assignment-groups/`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  listRubrics: (courseId) => request(`${API_BASE}/rubrics/course/${courseId}`, { headers: authHeaders() }),
  createRubric: (data) => request(`${API_BASE}/rubrics/`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
};

export default moduleApi;




