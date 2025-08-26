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

const discussionApi = {
  listTopics: (courseId) => request(`${API_BASE}/discussions/course/${courseId}`, { headers: authHeaders() }),
  createTopic: (data) => request(`${API_BASE}/discussions/`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  createEntry: (topicId, data) => request(`${API_BASE}/discussions/${topicId}/entries`, { method: 'POST', headers: jsonHeaders(), body: JSON.stringify(data) }),
  getTopic: (topicId) => request(`${API_BASE}/discussions/${topicId}`, { headers: authHeaders() }),
  updateTopic: (topicId, data) => request(`${API_BASE}/discussions/${topicId}`, { method: 'PUT', headers: jsonHeaders(), body: JSON.stringify(data) }),
  deleteTopic: (topicId) => request(`${API_BASE}/discussions/${topicId}`, { method: 'DELETE', headers: authHeaders() }),
  lockTopic: (topicId, locked) => request(`${API_BASE}/discussions/${topicId}`, { 
    method: 'PUT', 
    headers: jsonHeaders(), 
    body: JSON.stringify({ locked }) 
  }),
  getEntry: (entryId) => request(`${API_BASE}/discussions/entries/${entryId}`, { headers: authHeaders() }),
  updateEntry: (entryId, data) => request(`${API_BASE}/discussions/entries/${entryId}`, { method: 'PUT', headers: jsonHeaders(), body: JSON.stringify(data) }),
  deleteEntry: (entryId) => request(`${API_BASE}/discussions/entries/${entryId}`, { method: 'DELETE', headers: authHeaders() }),
  searchTopics: (courseId, query) => request(`${API_BASE}/discussions/course/${courseId}/search?q=${encodeURIComponent(query)}`, { headers: authHeaders() }),
};

export default discussionApi;


