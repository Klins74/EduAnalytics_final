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

const pageApi = {
  listPages: (courseId) => request(`${API_BASE}/pages/course/${courseId}`, { headers: authHeaders() }),
  createPage: (data) => request(`${API_BASE}/pages/`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  updatePage: (pageId, data) => request(`${API_BASE}/pages/${pageId}`, { method: 'PUT', headers: jsonHeaders(), body: JSON.stringify(data) }),
  getPage: (pageId) => request(`${API_BASE}/pages/${pageId}`, { headers: authHeaders() }),
  deletePage: (pageId) => request(`${API_BASE}/pages/${pageId}`, { method: 'DELETE', headers: authHeaders() }),
  publishPage: (pageId, published) => request(`${API_BASE}/pages/${pageId}`, { 
    method: 'PUT', 
    headers: jsonHeaders(), 
    body: JSON.stringify({ published }) 
  }),
  searchPages: (courseId, query) => request(`${API_BASE}/pages/course/${courseId}/search?q=${encodeURIComponent(query)}`, { headers: authHeaders() }),
};

export default pageApi;


