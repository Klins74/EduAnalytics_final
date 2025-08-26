// src/pages/ai/index.jsx

import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import Icon from '../../components/AppIcon';
import ChatHistory from './components/ChatHistory';
import ContextPanel from './components/ContextPanel';
import QuickActions from './components/QuickActions';
import VoiceInput from './components/VoiceInput';
import AIAnalytics from './components/AIAnalytics';
import AIRecommendations from './components/AIRecommendations';

const AIPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: `Добро пожаловать в AI-помощник EduAnalytics! Чем могу помочь сегодня?`,
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedContext, setSelectedContext] = useState('overview');
  const [searchHistory, setSearchHistory] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [analysisContext, setAnalysisContext] = useState({ type: 'student', id: 1 });
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load history from localStorage once
  useEffect(() => {
    try {
      const raw = localStorage.getItem('ai_chat_history');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed.map(m => ({ ...m, timestamp: new Date(m.timestamp) })));
        }
      }
    } catch (_) {}
  }, []);

  // Persist history
  useEffect(() => {
    try {
      localStorage.setItem('ai_chat_history', JSON.stringify(messages));
    } catch (_) {}
  }, [messages]);

  // --- ГЛАВНОЕ ИЗМЕНЕНИЕ: ФУНКЦИЯ ОБНОВЛЕНА ДЛЯ РАБОТЫ С РЕАЛЬНЫМ API ---
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isTyping) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');
    setIsTyping(true);

    const token = localStorage.getItem('accessToken');
    if (!token) {
        navigate('/login');
        return;
    }

    try {
      // Create placeholder AI message
      const aiId = Date.now() + 1;
      setMessages(prev => [...prev, { id: aiId, type: 'ai', content: '', timestamp: new Date() }]);

      // Prepare context payload
      const scope = analysisContext?.type || 'general';
      const payload = {
        message: currentInput,
        scope,
        student_id: scope === 'student' ? Number(analysisContext.id) : undefined,
        course_id: scope === 'course' ? Number(analysisContext.id) : undefined,
      };

      const response = await fetch('http://localhost:8000/api/ai/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (response.status === 401) {
        navigate('/login');
        return;
      }

      if (!response.ok || !response.body) {
        throw new Error('Ошибка ответа от AI-сервиса');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';
        for (const part of parts) {
          const lines = part.split('\n');
          let isEnd = false;
          for (const line of lines) {
            if (line.startsWith('event: end')) {
              isEnd = true;
            } else if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[END]') continue;
              setMessages(prev => prev.map(m => m.id === aiId ? { ...m, content: (m.content || '') + data } : m));
            }
          }
          if (isEnd) {
            // finalize
          }
        }
      }

    } catch (error) {
        console.error("Ошибка AI-чата:", error);
        const errorResponse = {
            id: Date.now() + 1,
            type: 'ai',
            content: 'К сожалению, произошла ошибка. Попробуйте позже.',
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorResponse]);
    } finally {
        setIsTyping(false);
    }
  };

  const clearHistory = () => {
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: `Добро пожаловать в AI-помощник EduAnalytics! Чем могу помочь сегодня?`,
        timestamp: new Date(),
      }
    ]);
    try { localStorage.removeItem('ai_chat_history'); } catch (_) {}
  };

  const quickSuggestions = [
    { text: 'Анализ успеваемости за месяц', icon: 'TrendingUp' },
    { text: 'Отчет по активности студентов', icon: 'Users' },
    { text: 'Рекомендации по улучшению курса', icon: 'Lightbulb' },
    { text: 'Прогноз результатов экзаменов', icon: 'Target' }
  ];

  const handleQuickSuggestion = (suggestion) => {
    setInputValue(suggestion);
    inputRef.current?.focus();
  };

  const handleVoiceInput = (transcript) => {
    setInputValue(transcript);
    setIsVoiceActive(false);
  };

  const fetchAnalyticsData = () => {
    // Эта функция будет вызываться при изменении контекста анализа
    // Компоненты AIAnalytics и AIRecommendations автоматически обновятся
    console.log('Analytics context updated:', analysisContext);
  };

  const formatTime = (date) => {
    return date.toLocaleString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      
      <main className="lg:ml-60 pt-16">
        <div className="p-6">
          <Breadcrumb />
          
          <div className="mb-6">
            <div className="flex items-center space-x-3 mb-2">
              <div className="w-10 h-10 bg-gradient-to-br from-secondary to-secondary-500 rounded-lg flex items-center justify-center">
                <Icon name="Bot" size={24} color="white" />
              </div>
              <div>
                <h1 className="text-2xl font-heading font-semibold text-text-primary">
                  AI-чат и интеллектуальные рекомендации
                </h1>
                <p className="text-text-secondary">
                  Персонализированные образовательные инсайты на основе NLP-анализа
                </p>
              </div>
              <div className="ml-auto flex items-center space-x-2">
                <div className="w-3 h-3 bg-success rounded-full ai-pulse" />
                <span className="text-sm text-text-secondary">AI активен</span>
                <button onClick={clearHistory} className="px-2 py-1 text-xs border rounded hover:bg-background">Очистить</button>
              </div>
            </div>
          </div>

          {/* Контекст анализа */}
          <div className="mb-6 bg-surface border border-border rounded-lg p-4">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-text-primary">Контекст анализа:</span>
              <select
                value={analysisContext.type}
                onChange={(e) => setAnalysisContext(prev => ({ ...prev, type: e.target.value }))}
                className="px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="student">Студент</option>
                <option value="course">Курс</option>
              </select>
              <input
                type="number"
                placeholder="ID"
                value={analysisContext.id}
                onChange={(e) => setAnalysisContext(prev => ({ ...prev, id: parseInt(e.target.value) || 1 }))}
                className="px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary w-20"
              />
              <button
                onClick={fetchAnalyticsData}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 transition-colors duration-150"
              >
                Обновить
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8">
              <div className="bg-surface border border-border rounded-lg shadow-card h-[600px] flex flex-col">
                <div className="flex items-center justify-between p-4 border-b border-border">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
                      <Icon name="Bot" size={16} color="white" />
                    </div>
                    <div>
                      <h3 className="font-heading font-medium text-text-primary">EduAnalytics AI</h3>
                      <span className="text-xs text-text-secondary">Специалист по образовательной аналитике</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150"><Icon name="Search" size={16} className="text-text-secondary" /></button>
                    <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150"><Icon name="MoreVertical" size={16} className="text-text-secondary" /></button>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-3xl ${message.type === 'user' ? 'ml-12' : 'mr-12'}`}>
                        {message.type === 'ai' && (
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="w-6 h-6 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center"><Icon name="Bot" size={12} color="white" /></div>
                            <span className="text-xs text-text-secondary">AI-помощник</span>
                            <span className="text-xs text-text-muted">•</span>
                            <span className="text-xs text-text-muted">{formatTime(message.timestamp)}</span>
                          </div>
                        )}
                        <div className={`px-4 py-3 rounded-lg ${message.type === 'user' ? 'bg-primary text-white' : 'bg-background border border-border text-text-primary'}`}>
                          <div className="whitespace-pre-line">{message.content}</div>
                        </div>
                        {message.type === 'user' && (
                          <div className="flex items-center justify-end space-x-2 mt-1">
                            <span className="text-xs text-text-muted">{formatTime(message.timestamp)}</span>
                            <Icon name="Check" size={12} className="text-success" />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="max-w-3xl mr-12">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-6 h-6 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center"><Icon name="Bot" size={12} color="white" /></div>
                          <span className="text-xs text-text-secondary">AI-помощник печатает...</span>
                        </div>
                        <div className="bg-background border border-border rounded-lg px-4 py-3">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                            <div className="w-2 h-2 bg-text-secondary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="px-4 py-2 border-t border-border">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {quickSuggestions.map((suggestion, index) => (
                        <button key={index} onClick={() => handleQuickSuggestion(suggestion.text)} className="flex items-center space-x-2 p-2 text-left bg-background hover:bg-primary-50 rounded-lg transition-colors duration-150 text-sm">
                            <Icon name={suggestion.icon} size={16} className="text-primary" />
                            <span className="text-text-secondary">{suggestion.text}</span>
                        </button>
                        ))}
                    </div>
                </div>

                <div className="p-4 border-t border-border">
                  <form onSubmit={handleSendMessage} className="flex space-x-3">
                    <div className="flex-1 relative">
                      <input ref={inputRef} type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} placeholder="Задайте вопрос об образовательных данных..." className="w-full px-4 py-3 pr-12 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"/>
                      <VoiceInput onTranscript={handleVoiceInput} isActive={isVoiceActive} setIsActive={setIsVoiceActive}/>
                    </div>
                    <button type="submit" disabled={!inputValue.trim() || isTyping} className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 hover-lift flex items-center space-x-2">
                      <Icon name="Send" size={16} />
                      <span className="hidden sm:inline">Отправить</span>
                    </button>
                  </form>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 space-y-4">
              <ContextPanel selectedContext={selectedContext} onContextChange={setSelectedContext}/>
              
              {/* AI Analytics */}
              <AIAnalytics 
                studentId={analysisContext.type === 'student' ? analysisContext.id : null}
                courseId={analysisContext.type === 'course' ? analysisContext.id : null}
              />
              
              {/* AI Recommendations */}
              <AIRecommendations 
                studentId={analysisContext.type === 'student' ? analysisContext.id : null}
                courseId={analysisContext.type === 'course' ? analysisContext.id : null}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AIPage;