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

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        content: generateAIResponse(inputValue),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const generateAIResponse = (userInput) => {
    const responses = [
      'Анализирую данные студентов... Обнаружил интересные тенденции в успеваемости.',
      'Рекомендую обратить внимание на студентов с низкой активностью в последние 7 дней.',
      'Статистика показывает улучшение результатов после внедрения новых методик.',
      'Могу создать персонализированный отчет по любому студенту или группе.',
      'Выявлены паттерны, которые могут помочь в прогнозировании успеваемости.',
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

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