const API_BASE = 'http://localhost:8000/api';

const authHeaders = () => {
  const token = localStorage.getItem('accessToken');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const getCurrentUser = async () => {
  const res = await fetch(`${API_BASE}/users/me`, { headers: authHeaders() });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
};

export default { getCurrentUser };



