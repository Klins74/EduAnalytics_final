import React, { useState, useRef, useEffect } from 'react';
import Icon from '../AppIcon';

const AIChat = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: 'Привет! Я ваш AI-помощник для анализа образовательных данных. Чем могу помочь?',
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  // Intent modal state
  const [showIntentModal, setShowIntentModal] = useState(false);
  const [intentLoading, setIntentLoading] = useState(false);
  const [intentError, setIntentError] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [intentForm, setIntentForm] = useState({
    course_id: '',
    instructor_id: '',
    schedule_date: '',
    start_time: '',
    end_time: '',
    location: '',
    lesson_type: 'lecture',
    description: 'Создано через AI'
  });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      if (!token) {
        const aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: 'Требуется авторизация. Пожалуйста, войдите в систему.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
        setIsTyping(false);
        return;
      }

      const scope = (() => {
        const p = window.location.pathname || '';
        if (p.includes('student')) return 'student';
        if (p.includes('teacher')) return 'teacher';
        if (p.includes('schedule')) return 'schedule';
        if (p.includes('analytics')) return 'analytics';
        return 'general';
      })();

      const contextPayload = {
        context: `Page: ${window.location.pathname} | Title: ${document.title}`,
        scope
      };

      // Включить стриминг при длинных запросах
      const useStream = inputValue.length > 120;
      const url = useStream ? 'http://localhost:8000/api/ai/chat/stream' : 'http://localhost:8000/api/ai/chat';
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: inputValue, ...contextPayload })
      });

      if (!useStream) {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.reply || 'Пустой ответ от AI',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      } else {
        // Чтение SSE-потока
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let accumulated = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';
          for (const part of parts) {
            if (part.startsWith('data: ')) {
              const chunk = part.replace(/^data: /, '');
              if (chunk !== '[END]') accumulated += chunk;
            }
          }
        }
        const aiResponse = {
          id: Date.now() + 1,
          type: 'ai',
          content: accumulated || 'Пустой ответ от AI',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, aiResponse]);
      }

      // Try intent extraction for actionable commands (e.g., create schedule)
      try {
        setIntentLoading(true);
        setIntentError('');
        const intentRes = await fetch('http://localhost:8000/api/ai/intent', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message: currentInput })
        });
        if (intentRes.ok) {
          const intent = await intentRes.json();
          if (intent.action === 'create_schedule') {
            // Prefill modal with intent params
            const p = intent.params || {};
            setIntentForm(prev => ({
              ...prev,
              course_id: String(p.course_id ?? prev.course_id ?? ''),
              instructor_id: String(p.instructor_id ?? prev.instructor_id ?? ''),
              schedule_date: p.schedule_date ?? prev.schedule_date ?? '',
              start_time: p.start_time ?? prev.start_time ?? '',
              end_time: p.end_time ?? prev.end_time ?? '',
              location: p.location ?? prev.location ?? '',
              lesson_type: p.lesson_type ?? prev.lesson_type ?? 'lecture',
              description: p.description ?? prev.description ?? 'Создано через AI'
            }));
            setShowIntentModal(true);
          }
        }
      } catch (ie) {
        setIntentError(String(ie));
      } finally {
        setIntentLoading(false);
      }
    } catch (err) {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: `Ошибка AI: ${String(err)}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
    } finally {
      setIsTyping(false);
    }
  };

  const fetchFreeSlots = async () => {
    try {
      setSlotsLoading(true);
      setSuggestions([]);
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      if (!token) throw new Error('Требуется авторизация');
      const params = new URLSearchParams({
        schedule_date: intentForm.schedule_date,
        instructor_id: String(intentForm.instructor_id || ''),
        duration_minutes: '90'
      });
      const r = await fetch(`http://localhost:8000/api/schedule/ai-free-slots?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setSuggestions(data.suggestions || []);
    } catch (e) {
      setIntentError(String(e));
    } finally {
      setSlotsLoading(false);
    }
  };

  const submitCreateSchedule = async () => {
    try {
      setCreateLoading(true);
      setIntentError('');
      const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
      if (!token) throw new Error('Требуется авторизация');
      const payload = {
        course_id: Number(intentForm.course_id),
        instructor_id: Number(intentForm.instructor_id),
        schedule_date: intentForm.schedule_date,
        start_time: intentForm.start_time,
        end_time: intentForm.end_time,
        location: intentForm.location || undefined,
        lesson_type: intentForm.lesson_type || 'lecture',
        description: intentForm.description || 'Создано через AI'
      };
      const r = await fetch('http://localhost:8000/api/schedule/ai-create', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const text = await r.text();
      if (!r.ok) throw new Error(text || `HTTP ${r.status}`);
      // Success feedback in chat
      const resp = {
        id: Date.now() + 2,
        type: 'ai',
        content: `Занятие создано. Ответ сервера: ${text}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, resp]);
      setShowIntentModal(false);
    } catch (e) {
      setIntentError(String(e));
    } finally {
      setCreateLoading(false);
    }
  };

  // удалена заглушка generateAIResponse — теперь используется реальный API

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
    setIsMinimized(false);
    if (!isExpanded) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const toggleMinimized = () => {
    setIsMinimized(!isMinimized);
    if (isMinimized) {
      setIsExpanded(false);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const quickActions = [
    { label: 'Анализ успеваемости', icon: 'TrendingUp' },
    { label: 'Отчет по активности', icon: 'Activity' },
    { label: 'Прогноз результатов', icon: 'Target' },
    { label: 'Рекомендации', icon: 'Lightbulb' },
  ];

  return (
    <>
      {/* Mobile Full Screen Modal */}
      {isExpanded && (
        <div className="fixed inset-0 bg-surface z-1100 lg:hidden">
          <div className="flex flex-col h-full">
            {/* Mobile Header */}
            <div className="flex items-center justify-between p-4 border-b border-border bg-surface">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
                  <Icon name="Bot" size={16} color="white" />
                </div>
                <div>
                  <h3 className="font-heading font-medium text-text-primary">AI-Помощник</h3>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-success rounded-full ai-pulse" />
                    <span className="text-xs text-text-secondary">Онлайн</span>
                  </div>
                </div>
              </div>
              <button
                onClick={toggleExpanded}
                className="p-2 hover:bg-background rounded-lg transition-colors duration-150"
              >
                <Icon name="X" size={20} className="text-text-secondary" />
              </button>
            </div>

            {/* Mobile Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      message.type === 'user' ?'bg-primary text-white' :'bg-background text-text-primary border border-border'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <span className="text-xs opacity-70 mt-1 block">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-background border border-border rounded-lg px-4 py-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                      <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Mobile Input */}
            <div className="p-4 border-t border-border bg-surface">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Задайте вопрос..."
                  className="flex-1 px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={!inputValue.trim()}
                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 hover-lift"
                >
                  <Icon name="Send" size={16} />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Desktop Widget */}
      <div className="hidden lg:block">
        {/* Minimized State */}
        {isMinimized && (
          <button
            onClick={toggleMinimized}
            className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-secondary to-secondary-500 text-white rounded-full shadow-elevated hover:shadow-lg transition-all duration-300 hover-lift z-800"
          >
            <Icon name="Bot" size={24} />
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-success rounded-full ai-pulse" />
          </button>
        )}

        {/* Expanded Widget */}
        {!isMinimized && (
          <div
            className={`fixed bottom-6 right-6 bg-surface border border-border rounded-lg shadow-elevated transition-all duration-300 z-800 ${
              isExpanded ? 'w-96 h-[500px]' : 'w-80 h-16'
            }`}
          >
            {/* Widget Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
                  <Icon name="Bot" size={16} color="white" />
                </div>
                {(isExpanded || !isExpanded) && (
                  <div>
                    <h3 className="font-heading font-medium text-sm text-text-primary">AI-Помощник</h3>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-success rounded-full ai-pulse" />
                      <span className="text-xs text-text-secondary">Онлайн</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={toggleExpanded}
                  className="p-1.5 hover:bg-background rounded transition-colors duration-150"
                >
                  <Icon 
                    name={isExpanded ? "Minimize2" : "Maximize2"} 
                    size={14} 
                    className="text-text-secondary" 
                  />
                </button>
                <button
                  onClick={toggleMinimized}
                  className="p-1.5 hover:bg-background rounded transition-colors duration-150"
                >
                  <Icon name="Minus" size={14} className="text-text-secondary" />
                </button>
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <>
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 h-80">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                          message.type === 'user' ?'bg-primary text-white' :'bg-background text-text-primary border border-border'
                        }`}
                      >
                        <p>{message.content}</p>
                        <span className="text-xs opacity-70 mt-1 block">
                          {formatTime(message.timestamp)}
                        </span>
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="bg-background border border-border rounded-lg px-3 py-2">
                        <div className="flex space-x-1">
                          <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" />
                          <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                          <div className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Quick Actions */}
                <div className="px-4 py-2 border-t border-border">
                  <div className="grid grid-cols-2 gap-2">
                    {quickActions.map((action, index) => (
                      <button
                        key={index}
                        onClick={() => setInputValue(action.label)}
                        className="flex items-center space-x-2 px-2 py-1.5 text-xs bg-background hover:bg-primary-50 rounded transition-colors duration-150"
                      >
                        <Icon name={action.icon} size={12} className="text-primary" />
                        <span className="text-text-secondary">{action.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Input */}
                <div className="p-4 border-t border-border">
                  <form onSubmit={handleSendMessage} className="flex space-x-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Задайте вопрос..."
                      className="flex-1 px-3 py-2 text-sm border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                    />
                    <button
                      type="submit"
                      disabled={!inputValue.trim()}
                      className="px-3 py-2 bg-primary text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 hover-lift"
                    >
                      <Icon name="Send" size={14} />
                    </button>
                  </form>
                </div>
                {/* Intent Modal */}
                {showIntentModal && (
                  <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-900">
                    <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-4">
                      <div className="flex justify-between items-center mb-3">
                        <h3 className="text-lg font-semibold">Подтвердить создание занятия</h3>
                        <button onClick={() => setShowIntentModal(false)} className="p-1 hover:bg-gray-100 rounded">✕</button>
                      </div>
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <input className="border rounded px-2 py-1" placeholder="Курс ID" value={intentForm.course_id} onChange={e=>setIntentForm({...intentForm, course_id: e.target.value})} />
                          <input className="border rounded px-2 py-1" placeholder="Преподаватель ID" value={intentForm.instructor_id} onChange={e=>setIntentForm({...intentForm, instructor_id: e.target.value})} />
                          <input className="border rounded px-2 py-1" type="date" value={intentForm.schedule_date} onChange={e=>setIntentForm({...intentForm, schedule_date: e.target.value})} />
                          <input className="border rounded px-2 py-1" placeholder="Аудитория" value={intentForm.location} onChange={e=>setIntentForm({...intentForm, location: e.target.value})} />
                          <input className="border rounded px-2 py-1" placeholder="Начало (HH:MM)" value={intentForm.start_time} onChange={e=>setIntentForm({...intentForm, start_time: e.target.value})} />
                          <input className="border rounded px-2 py-1" placeholder="Окончание (HH:MM)" value={intentForm.end_time} onChange={e=>setIntentForm({...intentForm, end_time: e.target.value})} />
                        </div>
                        {intentError && <div className="text-sm text-red-600">{intentError}</div>}
                        <div className="flex items-center gap-2">
                          <button className="px-3 py-2 bg-primary text-white rounded disabled:opacity-50" disabled={createLoading} onClick={submitCreateSchedule} type="button">
                            {createLoading ? 'Создаю...' : 'Создать'}
                          </button>
                          <button className="px-3 py-2 bg-gray-200 rounded disabled:opacity-50" disabled={slotsLoading} onClick={fetchFreeSlots} type="button">
                            {slotsLoading ? 'Ищу слоты...' : 'Предложить другое время'}
                          </button>
                        </div>
                        {suggestions.length > 0 && (
                          <div className="mt-2">
                            <div className="text-sm text-gray-600 mb-1">Свободные варианты:</div>
                            <div className="flex flex-wrap gap-2">
                              {suggestions.map((s, idx) => (
                                <button key={idx} onClick={()=>setIntentForm({...intentForm, start_time: s.start_time, end_time: s.end_time})} className="px-2 py-1 bg-gray-100 rounded border">
                                  {s.start_time} — {s.end_time}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Mobile FAB */}
      {!isExpanded && (
        <button
          onClick={toggleExpanded}
          className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-secondary to-secondary-500 text-white rounded-full shadow-elevated hover:shadow-lg transition-all duration-300 hover-lift z-800 lg:hidden"
        >
          <Icon name="Bot" size={24} />
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-success rounded-full ai-pulse" />
        </button>
      )}
    </>
  );
};

export default AIChat;