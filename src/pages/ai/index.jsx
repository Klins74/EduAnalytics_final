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

const AIPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: `Добро пожаловать в AI-помощник EduAnalytics! Я специализируюсь на анализе образовательных данных и могу помочь вам с:

• Анализом успеваемости студентов
• Выявлением паттернов обучения
• Генерацией персонализированных отчетов
• Рекомендациями по улучшению образовательного процесса

Чем могу помочь сегодня?`,
      timestamp: new Date(Date.now() - 300000),
      hasInteractiveElements: true
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedContext, setSelectedContext] = useState('overview');
  const [searchHistory, setSearchHistory] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
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

    // Simulate AI response with educational context
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: generateContextualAIResponse(inputValue),
        timestamp: new Date(),
        hasInteractiveElements: Math.random() > 0.5,
        chartData: Math.random() > 0.7 ? generateMockChartData() : null
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 2000);
  };

  const generateContextualAIResponse = (userInput) => {
    const responses = {
      'успеваемость': `Анализ успеваемости показывает следующие тенденции:

📊 **Общая статистика:**
• Средний балл: 4.2/5.0 (+0.3 к прошлому месяцу)
• Процент успешных студентов: 87%
• Активность участия: 78%

🎯 **Ключевые инсайты:**
• Студенты лучше справляются с практическими заданиями
• Снижение активности в пятницу на 23%
• Рост вовлеченности после внедрения интерактивных элементов`,

      'отчет': `Генерирую персонализированный отчет...

📈 **Аналитический отчет за период:**
• Обработано данных: 15,847 взаимодействий
• Выявлено паттернов: 23 значимых тренда
• Рекомендации: 8 приоритетных действий

🔍 **Основные находки:**
• Пиковая активность: 10:00-12:00 и 14:00-16:00
• Наиболее эффективные материалы: видеолекции (92% завершений)
• Проблемные области: математические концепции требуют дополнительной поддержки`,

      'рекомендации': `На основе анализа данных предлагаю следующие рекомендации:

🎯 **Приоритетные действия:**
1. Увеличить количество интерактивных элементов в курсах
2. Внедрить систему микрообучения для сложных тем
3. Организовать дополнительные консультации по математике

📚 **Педагогические интервенции:**
• Персонализированные траектории обучения для 12 студентов
• Групповые проекты для повышения коллаборации
• Геймификация для увеличения мотивации`,

      'default': `Проанализировал ваш запрос и нашел релевантную информацию:

📊 Данные обновлены: ${new Date().toLocaleString('ru-RU')}
🎯 Найдено паттернов: ${Math.floor(Math.random() * 15) + 5}
📈 Уровень достоверности: ${Math.floor(Math.random() * 20) + 80}%

Могу предоставить более детальный анализ по конкретным аспектам. Что вас интересует больше всего?`
    };

    const lowerInput = userInput.toLowerCase();
    if (lowerInput.includes('успеваемость') || lowerInput.includes('оценки')) {
      return responses.успеваемость;
    } else if (lowerInput.includes('отчет') || lowerInput.includes('статистика')) {
      return responses.отчет;
    } else if (lowerInput.includes('рекомендации') || lowerInput.includes('советы')) {
      return responses.рекомендации;
    }
    return responses.default;
  };

  const generateMockChartData = () => {
    return {
      type: 'line',
      data: Array.from({ length: 7 }, (_, i) => ({
        day: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][i],
        value: Math.floor(Math.random() * 100) + 50
      }))
    };
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
          
          {/* Page Header */}
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
              </div>
            </div>
          </div>

          {/* Main Chat Interface */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Chat Area - 8 columns */}
            <div className="lg:col-span-8">
              <div className="bg-surface border border-border rounded-lg shadow-card h-[600px] flex flex-col">
                {/* Chat Header */}
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
                    <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150">
                      <Icon name="Search" size={16} className="text-text-secondary" />
                    </button>
                    <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150">
                      <Icon name="MoreVertical" size={16} className="text-text-secondary" />
                    </button>
                  </div>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-3xl ${message.type === 'user' ? 'ml-12' : 'mr-12'}`}>
                        {message.type === 'ai' && (
                          <div className="flex items-center space-x-2 mb-2">
                            <div className="w-6 h-6 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
                              <Icon name="Bot" size={12} color="white" />
                            </div>
                            <span className="text-xs text-text-secondary">AI-помощник</span>
                            <span className="text-xs text-text-muted">•</span>
                            <span className="text-xs text-text-muted">{formatTime(message.timestamp)}</span>
                          </div>
                        )}
                        
                        <div
                          className={`px-4 py-3 rounded-lg ${
                            message.type === 'user' ?'bg-primary text-white' :'bg-background border border-border text-text-primary'
                          }`}
                        >
                          <div className="whitespace-pre-line">{message.content}</div>
                          
                          {/* Interactive Elements for AI messages */}
                          {message.type === 'ai' && message.hasInteractiveElements && (
                            <div className="mt-3 pt-3 border-t border-border-light">
                              <div className="flex flex-wrap gap-2">
                                <button className="px-3 py-1 bg-primary-50 text-primary text-xs rounded-full hover:bg-primary-100 transition-colors duration-150">
                                  Подробнее
                                </button>
                                <button className="px-3 py-1 bg-success-50 text-success text-xs rounded-full hover:bg-success-100 transition-colors duration-150">
                                  Экспорт данных
                                </button>
                                <button className="px-3 py-1 bg-accent-50 text-accent text-xs rounded-full hover:bg-accent-100 transition-colors duration-150">
                                  Создать отчет
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Chart Data Visualization */}
                          {message.chartData && (
                            <div className="mt-3 p-3 bg-background rounded border">
                              <h4 className="text-sm font-medium text-text-primary mb-2">Динамика активности</h4>
                              <div className="h-32 flex items-end space-x-2">
                                {message.chartData.data.map((item, index) => (
                                  <div key={index} className="flex-1 flex flex-col items-center">
                                    <div
                                      className="w-full bg-primary rounded-t"
                                      style={{ height: `${(item.value / 150) * 100}%` }}
                                    />
                                    <span className="text-xs text-text-secondary mt-1">{item.day}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
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

                  {/* Typing Indicator */}
                  {isTyping && (
                    <div className="flex justify-start">
                      <div className="max-w-3xl mr-12">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="w-6 h-6 bg-gradient-to-br from-secondary to-secondary-500 rounded-full flex items-center justify-center">
                            <Icon name="Bot" size={12} color="white" />
                          </div>
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

                {/* Quick Suggestions */}
                {messages.length === 1 && (
                  <div className="px-4 py-2 border-t border-border">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {quickSuggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleQuickSuggestion(suggestion.text)}
                          className="flex items-center space-x-2 p-2 text-left bg-background hover:bg-primary-50 rounded-lg transition-colors duration-150 text-sm"
                        >
                          <Icon name={suggestion.icon} size={16} className="text-primary" />
                          <span className="text-text-secondary">{suggestion.text}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Input Area */}
                <div className="p-4 border-t border-border">
                  <form onSubmit={handleSendMessage} className="flex space-x-3">
                    <div className="flex-1 relative">
                      <input
                        ref={inputRef}
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Задайте вопрос об образовательных данных..."
                        className="w-full px-4 py-3 pr-12 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
                      />
                      <VoiceInput
                        onTranscript={handleVoiceInput}
                        isActive={isVoiceActive}
                        setIsActive={setIsVoiceActive}
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={!inputValue.trim()}
                      className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 hover-lift flex items-center space-x-2"
                    >
                      <Icon name="Send" size={16} />
                      <span className="hidden sm:inline">Отправить</span>
                    </button>
                  </form>
                </div>
              </div>
            </div>

            {/* Context Panel - 4 columns */}
            <div className="lg:col-span-4">
              <ContextPanel 
                selectedContext={selectedContext}
                onContextChange={setSelectedContext}
              />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-6">
            <QuickActions onActionClick={handleQuickSuggestion} />
          </div>

          {/* Chat History */}
          <div className="mt-6">
            <ChatHistory 
              searchQuery={searchHistory}
              onSearchChange={setSearchHistory}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AIPage;