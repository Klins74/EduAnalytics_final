import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

const ChatHistory = ({ searchQuery, onSearchChange }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('week');

  const chatSessions = [
    {
      id: 1,
      title: 'Анализ успеваемости группы ИТ-21',
      date: new Date(Date.now() - 86400000),
      preview: 'Обсуждали тенденции успеваемости и выявили проблемные области в математике...',
      messagesCount: 15,
      tags: ['успеваемость', 'математика', 'ИТ-21']
    },
    {
      id: 2,
      title: 'Рекомендации по улучшению курса',
      date: new Date(Date.now() - 172800000),
      preview: 'Анализировали эффективность различных методов обучения и их влияние...',
      messagesCount: 23,
      tags: ['рекомендации', 'методики', 'эффективность']
    },
    {
      id: 3,
      title: 'Прогноз результатов экзаменов',
      date: new Date(Date.now() - 259200000),
      preview: 'Построили модель прогнозирования на основе текущих показателей...',
      messagesCount: 18,
      tags: ['прогноз', 'экзамены', 'модель']
    },
    {
      id: 4,
      title: 'Анализ активности студентов',
      date: new Date(Date.now() - 345600000),
      preview: 'Изучали паттерны активности и выявили оптимальные времена для обучения...',
      messagesCount: 12,
      tags: ['активность', 'паттерны', 'время']
    },
    {
      id: 5,
      title: 'Отчет по вовлеченности',
      date: new Date(Date.now() - 432000000),
      preview: 'Анализировали уровень вовлеченности студентов в различные активности...',
      messagesCount: 20,
      tags: ['вовлеченность', 'активности', 'отчет']
    }
  ];

  const filteredSessions = chatSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.preview.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const formatDate = (date) => {
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Вчера';
    if (diffDays <= 7) return `${diffDays} дня назад`;
    return date.toLocaleDateString('ru-RU');
  };

  const periods = [
    { value: 'day', label: 'Сегодня' },
    { value: 'week', label: 'Неделя' },
    { value: 'month', label: 'Месяц' },
    { value: 'all', label: 'Все время' }
  ];

  return (
    <div className="bg-surface border border-border rounded-lg shadow-card">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-heading font-medium text-text-primary">История диалогов</h3>
          <div className="flex items-center space-x-2">
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="text-sm border border-border rounded px-2 py-1 bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {periods.map(period => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Icon 
            name="Search" 
            size={16} 
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary" 
          />
          <input
            type="text"
            placeholder="Поиск по истории диалогов..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background text-sm"
          />
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {filteredSessions.length > 0 ? (
          <div className="divide-y divide-border">
            {filteredSessions.map((session) => (
              <div
                key={session.id}
                className="p-4 hover:bg-background transition-colors duration-150 cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-medium text-text-primary text-sm line-clamp-1">
                    {session.title}
                  </h4>
                  <span className="text-xs text-text-muted ml-2 flex-shrink-0">
                    {formatDate(session.date)}
                  </span>
                </div>
                
                <p className="text-sm text-text-secondary mb-3 line-clamp-2">
                  {session.preview}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {session.tags.slice(0, 2).map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-primary-50 text-primary text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                    {session.tags.length > 2 && (
                      <span className="text-xs text-text-muted">
                        +{session.tags.length - 2}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center space-x-1 text-text-muted">
                    <Icon name="MessageCircle" size={12} />
                    <span className="text-xs">{session.messagesCount}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center">
            <Icon name="Search" size={32} className="text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary">
              {searchQuery ? 'Диалоги не найдены' : 'История диалогов пуста'}
            </p>
            <p className="text-sm text-text-muted mt-1">
              {searchQuery ? 'Попробуйте изменить поисковый запрос' : 'Начните новый диалог с AI-помощником'}
            </p>
          </div>
        )}
      </div>

      {filteredSessions.length > 0 && (
        <div className="p-3 border-t border-border bg-background">
          <button className="w-full text-center text-sm text-primary hover:text-primary-700 transition-colors duration-150">
            Показать все диалоги ({chatSessions.length})
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatHistory;