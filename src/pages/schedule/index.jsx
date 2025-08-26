import React, { useEffect, useMemo, useState } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import ScheduleForm from './components/ScheduleForm';
import ScheduleCalendar from './components/ScheduleCalendar';
import { useCallback } from 'react';

const SchedulePage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null);
  const [courses, setCourses] = useState([]);
  const [instructors, setInstructors] = useState([]);
  const [filters, setFilters] = useState({
    course_id: '',
    instructor_id: '',
    date_from: '',
    date_to: ''
  });
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'calendar'
  const [aiSuggestions, setAiSuggestions] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  const headers = useMemo(() => ({
    'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token') || ''}`,
    'Content-Type': 'application/json'
  }), []);

  const loadFiltersData = async () => {
    try {
      // Courses
      const cr = await fetch('http://localhost:8000/api/courses/', { headers });
      if (cr.ok) {
        const data = await cr.json();
        setCourses(data.courses || []);
      } else {
        console.error('Failed to load courses:', cr.status);
      }
      
      // Users (teachers)
      const ur = await fetch('http://localhost:8000/api/users/', { headers });
      if (ur.ok) {
        const data = await ur.json();
        setInstructors((data || []).filter(u => u.role === 'teacher' || u.role === 'admin'));
      } else {
        console.error('Failed to load users:', ur.status);
      }
    } catch (error) {
      console.error('Error loading filters data:', error);
      setError('Ошибка загрузки данных для фильтров');
    }
  };

  const getAuthHeaders = useCallback(() => ({
    'Authorization': `Bearer ${localStorage.getItem('accessToken') || localStorage.getItem('token') || ''}`,
    'Content-Type': 'application/json'
  }), []);

  const requestAiSlots = async () => {
    if (!filters.instructor_id || !filters.date_from) {
      alert('Выберите преподавателя и дату (поле "С") для подбора слотов');
      return;
    }
    try {
      setAiLoading(true);
      setAiSuggestions([]);
      const params = new URLSearchParams({
        schedule_date: filters.date_from,
        instructor_id: String(filters.instructor_id),
        duration_minutes: '90'
      });
      const r = await fetch(`http://localhost:8000/api/schedule/ai-free-slots?${params.toString()}`, { headers: getAuthHeaders() });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(`${r.status} ${t}`);
      }
      const data = await r.json();
      setAiSuggestions(Array.isArray(data.suggestions) ? data.suggestions : []);
    } catch (e) {
      console.error('AI slots error', e);
      alert('Не удалось получить свободные слоты');
    } finally {
      setAiLoading(false);
    }
  };

  const quickAiCreate = async (slot) => {
    if (!filters.course_id || !filters.instructor_id || !filters.date_from) {
      alert('Выберите курс, преподавателя и дату');
      return;
    }
    try {
      const payload = {
        course_id: Number(filters.course_id),
        instructor_id: Number(filters.instructor_id),
        schedule_date: filters.date_from,
        start_time: `${slot.start_time}:00`,
        end_time: `${slot.end_time}:00`,
        lesson_type: 'lecture'
      };
      const r = await fetch('http://localhost:8000/api/schedule/ai-create', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
      });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(`${r.status} ${t}`);
      }
      await loadSchedule();
      alert('Занятие создано');
    } catch (e) {
      console.error('AI create error', e);
      alert('Не удалось создать занятие');
    }
  };

  const loadSchedule = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      if (filters.course_id) params.set('course_id', filters.course_id);
      if (filters.instructor_id) params.set('instructor_id', filters.instructor_id);
      if (filters.date_from) params.set('date_from', filters.date_from);
      if (filters.date_to) params.set('date_to', filters.date_to);
      
      const r = await fetch(`http://localhost:8000/api/schedule?${params.toString()}`, { headers });
      if (r.ok) {
        const data = await r.json();
        setItems(data.schedules || []);
      } else {
        setError(`Ошибка загрузки расписания: ${r.status}`);
      }
    } catch (error) {
      console.error('Error loading schedule:', error);
      setError('Ошибка подключения к серверу при загрузке расписания');
    }
    setLoading(false);
  };

  useEffect(() => {
    loadFiltersData();
    loadSchedule();
  }, []);

  const handleCreate = async (payload) => {
    try {
      const r = await fetch('http://localhost:8000/api/schedule/', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });
      if (r.ok) {
        setShowForm(false);
        setEditItem(null);
        await loadSchedule();
      } else {
        const t = await r.text();
        alert(`Ошибка создания: ${r.status} ${t}`);
      }
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Ошибка подключения к серверу при создании расписания');
    }
  };

  const handleUpdate = async (id, payload) => {
    try {
      const r = await fetch(`http://localhost:8000/api/schedule/${id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });
      if (r.ok) {
        setShowForm(false);
        setEditItem(null);
        await loadSchedule();
      } else {
        const t = await r.text();
        alert(`Ошибка обновления: ${r.status} ${t}`);
      }
    } catch (error) {
      console.error('Error updating schedule:', error);
      alert('Ошибка подключения к серверу при обновлении расписания');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Удалить занятие?')) return;
    try {
      const r = await fetch(`http://localhost:8000/api/schedule/${id}`, {
        method: 'DELETE',
        headers
      });
      if (r.status === 204) {
        await loadSchedule();
      } else {
        const t = await r.text();
        alert(`Ошибка удаления: ${r.status} ${t}`);
      }
    } catch (error) {
      console.error('Error deleting schedule:', error);
      alert('Ошибка подключения к серверу при удалении расписания');
    }
  };

  const openCreate = () => { setEditItem(null); setShowForm(true); };
  const openEdit = (item) => { setEditItem(item); setShowForm(true); };

  const toolbar = (
    <div className="flex flex-col gap-4">
      {/* View Mode Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            Список
          </button>
          <button
            onClick={() => setViewMode('calendar')}
            className={`px-4 py-2 rounded ${viewMode === 'calendar' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}
          >
            Календарь
          </button>
        </div>
        <button onClick={openCreate} className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">Добавить</button>
      </div>
      
      {/* Filters */}
      {(
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-sm text-gray-700 mb-1">Курс</label>
            <select value={filters.course_id} onChange={(e)=>setFilters({...filters, course_id:e.target.value})} className="border rounded px-3 py-2">
              <option value="">Все</option>
              {courses.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Преподаватель</label>
            <select value={filters.instructor_id} onChange={(e)=>setFilters({...filters, instructor_id:e.target.value})} className="border rounded px-3 py-2">
              <option value="">Все</option>
              {instructors.map(u => <option key={u.id} value={u.id}>{u.username}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">С</label>
            <input type="date" value={filters.date_from} onChange={(e)=>setFilters({...filters, date_from:e.target.value})} className="border rounded px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">По</label>
            <input type="date" value={filters.date_to} onChange={(e)=>setFilters({...filters, date_to:e.target.value})} className="border rounded px-3 py-2" />
          </div>
          <button onClick={loadSchedule} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Применить</button>
          <button onClick={requestAiSlots} className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">AI слоты</button>
        </div>
      )}

      {/* AI Suggestions */}
      {aiLoading && <div className="text-sm text-gray-500">AI подбирает свободные слоты…</div>}
      {aiSuggestions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-600">Рекомендованные слоты:</span>
          {aiSuggestions.map((s, idx) => (
            <button key={idx} onClick={() => quickAiCreate(s)} className="px-3 py-1.5 text-sm rounded border hover:bg-gray-50">
              {s.start_time}–{s.end_time} • создать
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <div className="flex-1 p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-gray-900 mb-2">Расписание</h1>
            {toolbar}
          </div>

          {loading ? (
            <div className="text-gray-500">Загрузка...</div>
          ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : viewMode === 'calendar' ? (
            <ScheduleCalendar
              items={items}
              onEdit={openEdit}
              onDelete={handleDelete}
            />
          ) : (
            <div className="bg-white rounded-lg shadow">
              <div className="divide-y">
                {items.length === 0 && (
                  <div className="p-6 text-gray-500">Нет записей</div>
                )}
                {items.map(item => (
                  <div key={item.id} className="p-4 flex items-start justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{item.course?.title || `Курс #${item.course_id}`}</div>
                      <div className="text-sm text-gray-500">{item.schedule_date} • {item.start_time}–{item.end_time} • {item.location || '—'} • {item.lesson_type}</div>
                      {item.description && (
                        <div className="text-sm text-gray-600 mt-1">{item.description}</div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button onClick={()=>openEdit(item)} className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700">Изменить</button>
                      <button onClick={()=>handleDelete(item.id)} className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700">Удалить</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {showForm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">{editItem ? 'Редактировать занятие' : 'Добавить занятие'}</h2>
                  <button onClick={()=>{setShowForm(false); setEditItem(null);}} className="text-gray-500 hover:text-gray-700">✕</button>
                </div>
                <ScheduleForm
                  initialValues={editItem}
                  courses={courses}
                  instructors={instructors}
                  submitting={false}
                  onCancel={()=>{setShowForm(false); setEditItem(null);}}
                  onSubmit={(payload)=> editItem ? handleUpdate(editItem.id, payload) : handleCreate(payload)}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchedulePage;



