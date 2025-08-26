import React, { useState, useMemo } from 'react';

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

const LESSON_TYPE_COLORS = {
  lecture: 'bg-blue-100 text-blue-800 border-blue-200',
  seminar: 'bg-green-100 text-green-800 border-green-200',
  laboratory: 'bg-purple-100 text-purple-800 border-purple-200',
  practical: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  exam: 'bg-red-100 text-red-800 border-red-200',
  consultation: 'bg-gray-100 text-gray-800 border-gray-200',
  other: 'bg-indigo-100 text-indigo-800 border-indigo-200'
};

const LESSON_TYPE_LABELS = {
  lecture: 'Лекция',
  seminar: 'Семинар',
  laboratory: 'Лабораторная',
  practical: 'Практическое',
  exam: 'Экзамен',
  consultation: 'Консультация',
  other: 'Другое'
};

const ScheduleCalendar = ({ items, onEdit, onDelete }) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);

  const monthStart = useMemo(() => {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    return date;
  }, [currentDate]);

  const monthEnd = useMemo(() => {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    return date;
  }, [currentDate]);

  const calendarDays = useMemo(() => {
    const days = [];
    const start = new Date(monthStart);
    const end = new Date(monthEnd);
    
    // Начинаем с понедельника
    const startDay = start.getDay() || 7;
    start.setDate(start.getDate() - startDay + 1);
    
    // Заканчиваем воскресеньем
    const endDay = end.getDay() || 7;
    end.setDate(end.getDate() + (7 - endDay));
    
    const current = new Date(start);
    while (current <= end) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    
    return days;
  }, [monthStart, monthEnd]);

  const itemsByDate = useMemo(() => {
    const map = {};
    items.forEach(item => {
      const dateKey = item.schedule_date;
      if (!map[dateKey]) {
        map[dateKey] = [];
      }
      map[dateKey].push(item);
    });
    return map;
  }, [items]);

  const handlePrevMonth = () => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() - 1);
    setCurrentDate(newDate);
  };

  const handleNextMonth = () => {
    const newDate = new Date(currentDate);
    newDate.setMonth(newDate.getMonth() + 1);
    setCurrentDate(newDate);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const formatTime = (time) => {
    return time.slice(0, 5);
  };

  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const isCurrentMonth = (date) => {
    return date.getMonth() === currentDate.getMonth();
  };

  const getDateKey = (date) => {
    return date.toISOString().slice(0, 10);
  };

  const selectedDateItems = selectedDate ? itemsByDate[getDateKey(selectedDate)] || [] : [];

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
          </h2>
          <div className="flex gap-2">
            <button
              onClick={handlePrevMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button
              onClick={handleToday}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Сегодня
            </button>
            <button
              onClick={handleNextMonth}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="p-6">
        {/* Days of week */}
        <div className="grid grid-cols-7 gap-px mb-2">
          {DAYS.map(day => (
            <div key={day} className="text-center text-sm font-medium text-gray-700 py-2">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="grid grid-cols-7 gap-px bg-gray-200">
          {calendarDays.map((date, index) => {
            const dateKey = getDateKey(date);
            const dayItems = itemsByDate[dateKey] || [];
            const isSelected = selectedDate && getDateKey(selectedDate) === dateKey;
            
            return (
              <div
                key={index}
                onClick={() => setSelectedDate(date)}
                className={`
                  bg-white p-2 min-h-[100px] cursor-pointer hover:bg-gray-50 transition-colors
                  ${!isCurrentMonth(date) ? 'text-gray-400' : ''}
                  ${isToday(date) ? 'bg-blue-50' : ''}
                  ${isSelected ? 'ring-2 ring-blue-500' : ''}
                `}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-sm font-medium ${isToday(date) ? 'text-blue-600' : ''}`}>
                    {date.getDate()}
                  </span>
                  {dayItems.length > 0 && (
                    <span className="text-xs text-gray-500">
                      {dayItems.length} зан.
                    </span>
                  )}
                </div>
                
                {/* Show first 2 items */}
                <div className="space-y-1">
                  {dayItems.slice(0, 2).map((item, i) => (
                    <div
                      key={i}
                      className={`text-xs p-1 rounded border ${LESSON_TYPE_COLORS[item.lesson_type] || LESSON_TYPE_COLORS.other}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onEdit && onEdit(item);
                      }}
                    >
                      <div className="font-medium truncate">
                        {formatTime(item.start_time)} • {item.course?.title || `Курс #${item.course_id}`}
                      </div>
                    </div>
                  ))}
                  {dayItems.length > 2 && (
                    <div className="text-xs text-gray-500 text-center">
                      +{dayItems.length - 2} еще
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Date Details */}
      {selectedDate && (
        <div className="border-t border-gray-200 px-6 py-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            {selectedDate.toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </h3>
          {selectedDateItems.length > 0 ? (
            <div className="space-y-2">
              {selectedDateItems.map((item) => (
                <div
                  key={item.id}
                  className={`p-3 rounded-lg border ${LESSON_TYPE_COLORS[item.lesson_type] || LESSON_TYPE_COLORS.other}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-medium">
                        {formatTime(item.start_time)} - {formatTime(item.end_time)}
                      </div>
                      <div className="text-sm mt-1">
                        {item.course?.title || `Курс #${item.course_id}`}
                      </div>
                      {item.location && (
                        <div className="text-sm text-gray-600 mt-1">
                          📍 {item.location}
                        </div>
                      )}
                      {item.description && (
                        <div className="text-sm text-gray-600 mt-1">
                          {item.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-500 mt-1">
                        {LESSON_TYPE_LABELS[item.lesson_type] || item.lesson_type}
                      </div>
                    </div>
                    <div className="flex gap-1 ml-2">
                      <button
                        onClick={() => onEdit && onEdit(item)}
                        className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                        title="Редактировать"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => onDelete && onDelete(item.id)}
                        className="p-1 hover:bg-white hover:bg-opacity-50 rounded"
                        title="Удалить"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500">
              Нет занятий на эту дату
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ScheduleCalendar;
