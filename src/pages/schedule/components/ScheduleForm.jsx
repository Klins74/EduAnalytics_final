import React, { useEffect, useState } from 'react';

const LESSON_TYPES = [
  { value: 'lecture', label: 'Лекция' },
  { value: 'seminar', label: 'Семинар' },
  { value: 'laboratory', label: 'Лабораторная' },
  { value: 'practical', label: 'Практическое' },
  { value: 'exam', label: 'Экзамен' },
  { value: 'consultation', label: 'Консультация' },
  { value: 'other', label: 'Другое' }
];

const toHHMMSS = (value) => {
  if (!value) return '';
  // Accepts "HH:MM" or "HH:MM:SS"
  const parts = String(value).split(':');
  if (parts.length === 2) return `${parts[0].padStart(2,'0')}:${parts[1].padStart(2,'0')}:00`;
  if (parts.length === 3) return `${parts[0].padStart(2,'0')}:${parts[1].padStart(2,'0')}:${parts[2].padStart(2,'0')}`;
  return value;
};

const ScheduleForm = ({
  initialValues,
  courses,
  instructors,
  onCancel,
  onSubmit,
  submitting
}) => {
  const [values, setValues] = useState({
    course_id: '',
    schedule_date: '',
    start_time: '09:00',
    end_time: '10:30',
    location: '',
    instructor_id: '',
    lesson_type: 'lecture',
    description: '',
    notes: '',
    is_cancelled: false,
    classroom_id: ''
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (initialValues) {
      setValues({
        course_id: initialValues.course_id ?? '',
        schedule_date: String(initialValues.schedule_date ?? '').slice(0,10),
        start_time: String(initialValues.start_time ?? '09:00').slice(0,5),
        end_time: String(initialValues.end_time ?? '10:30').slice(0,5),
        location: initialValues.location ?? '',
        instructor_id: initialValues.instructor_id ?? '',
        lesson_type: initialValues.lesson_type ?? 'lecture',
        description: initialValues.description ?? '',
        notes: initialValues.notes ?? '',
        is_cancelled: Boolean(initialValues.is_cancelled) ?? false,
        classroom_id: initialValues.classroom_id ?? ''
      });
    }
  }, [initialValues]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    // Validate times
    const start = toHHMMSS(values.start_time);
    const end = toHHMMSS(values.end_time);
    if (end <= start) {
      setError('Время окончания должно быть больше времени начала');
      return;
    }
    const payload = {
      course_id: Number(values.course_id),
      schedule_date: values.schedule_date,
      start_time: start,
      end_time: end,
      location: values.location || null,
      instructor_id: Number(values.instructor_id),
      lesson_type: values.lesson_type,
      description: values.description || null,
      notes: values.notes || null,
      is_cancelled: Boolean(values.is_cancelled),
      classroom_id: values.classroom_id ? Number(values.classroom_id) : null
    };
    onSubmit && onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <div className="text-sm text-red-600">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-gray-700 mb-1">Курс</label>
          <select name="course_id" value={values.course_id} onChange={handleChange} required className="w-full border rounded px-3 py-2">
            <option value="">Выберите курс</option>
            {courses.map(c => (
              <option key={c.id} value={c.id}>{c.title}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Преподаватель</label>
          <select name="instructor_id" value={values.instructor_id} onChange={handleChange} required className="w-full border rounded px-3 py-2">
            <option value="">Выберите преподавателя</option>
            {instructors.map(u => (
              <option key={u.id} value={u.id}>{u.username}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-700 mb-1">Дата</label>
          <input type="date" name="schedule_date" value={values.schedule_date} onChange={handleChange} required className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Начало</label>
          <input type="time" name="start_time" value={values.start_time} onChange={handleChange} required className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Окончание</label>
          <input type="time" name="end_time" value={values.end_time} onChange={handleChange} required className="w-full border rounded px-3 py-2" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-700 mb-1">Аудитория</label>
          <input type="text" name="location" value={values.location} onChange={handleChange} placeholder="Аудитория 101" className="w-full border rounded px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm text-gray-700 mb-1">Тип занятия</label>
          <select name="lesson_type" value={values.lesson_type} onChange={handleChange} className="w-full border rounded px-3 py-2">
            {LESSON_TYPES.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center pt-6">
          <label className="inline-flex items-center space-x-2 text-sm text-gray-700">
            <input type="checkbox" name="is_cancelled" checked={values.is_cancelled} onChange={handleChange} />
            <span>Отменено</span>
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm text-gray-700 mb-1">Описание</label>
        <textarea name="description" value={values.description} onChange={handleChange} rows={3} className="w-full border rounded px-3 py-2" />
      </div>
      <div>
        <label className="block text-sm text-gray-700 mb-1">Заметки</label>
        <textarea name="notes" value={values.notes} onChange={handleChange} rows={2} className="w-full border rounded px-3 py-2" />
      </div>

      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="px-4 py-2 rounded border">Отмена</button>
        <button type="submit" disabled={submitting} className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700">
          {submitting ? 'Сохранение...' : 'Сохранить'}
        </button>
      </div>
    </form>
  );
};

export default ScheduleForm;



