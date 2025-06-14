import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Icon from '../AppIcon';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      console.log('Searching for:', searchQuery);
    }
  };

  const handleProfileClick = () => {
    setIsProfileMenuOpen(!isProfileMenuOpen);
    setIsNotificationOpen(false);
  };

  const handleNotificationClick = () => {
    setIsNotificationOpen(!isNotificationOpen);
    setIsProfileMenuOpen(false);
  };

  const handleLogout = () => {
    navigate('/login');
    setIsProfileMenuOpen(false);
  };

  const notifications = [
    { id: 1, title: 'Новое уведомление о студенте', message: 'Студент Иванов И.И. завершил тест', time: '5 мин назад', unread: true },
    { id: 2, title: 'Системное обновление', message: 'Обновление аналитики завершено', time: '1 час назад', unread: true },
    { id: 3, title: 'Отчет готов', message: 'Месячный отчет по успеваемости', time: '2 часа назад', unread: false },
  ];

  const unreadCount = notifications.filter(n => n.unread).length;

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-surface border-b border-border z-1000">
      <div className="flex items-center justify-between h-full px-6">
        {/* Logo */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
              <Icon name="GraduationCap" size={20} color="white" />
            </div>
            <span className="font-heading font-semibold text-xl text-text-primary hidden sm:block">
              EduAnalytics
            </span>
          </div>
        </div>

        {/* Search Bar */}
        <div className="flex-1 max-w-md mx-8 hidden md:block">
          <form onSubmit={handleSearch} className="relative">
            <div className="relative">
              <Icon 
                name="Search" 
                size={20} 
                className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary" 
              />
              <input
                type="text"
                placeholder="Поиск студентов, отчетов..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-150"
              />
            </div>
          </form>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-4">
          {/* Mobile Search */}
          <button className="p-2 hover:bg-background rounded-lg transition-colors duration-150 md:hidden">
            <Icon name="Search" size={20} className="text-text-secondary" />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={handleNotificationClick}
              className="relative p-2 hover:bg-background rounded-lg transition-colors duration-150 hover-lift"
            >
              <Icon name="Bell" size={20} className="text-text-secondary" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-error text-white text-xs rounded-full flex items-center justify-center font-medium">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notifications Dropdown */}
            {isNotificationOpen && (
              <div className="absolute right-0 top-12 w-80 bg-surface border border-border rounded-lg shadow-elevated z-1100">
                <div className="p-4 border-b border-border">
                  <h3 className="font-heading font-medium text-text-primary">Уведомления</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 border-b border-border-light hover:bg-background transition-colors duration-150 cursor-pointer ${
                        notification.unread ? 'bg-primary-50' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`w-2 h-2 rounded-full mt-2 ${notification.unread ? 'bg-primary' : 'bg-border'}`} />
                        <div className="flex-1">
                          <h4 className="font-medium text-sm text-text-primary">{notification.title}</h4>
                          <p className="text-sm text-text-secondary mt-1">{notification.message}</p>
                          <span className="text-xs text-text-muted mt-2 block">{notification.time}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="p-3 border-t border-border">
                  <button className="w-full text-center text-sm text-primary hover:text-primary-700 transition-colors duration-150">
                    Показать все уведомления
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={handleProfileClick}
              className="flex items-center space-x-2 p-2 hover:bg-background rounded-lg transition-colors duration-150 hover-lift"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-accent to-accent-600 rounded-full flex items-center justify-center">
                <Icon name="User" size={16} color="white" />
              </div>
              <span className="font-medium text-sm text-text-primary hidden lg:block">
                Администратор
              </span>
              <Icon name="ChevronDown" size={16} className="text-text-secondary hidden lg:block" />
            </button>

            {/* Profile Dropdown */}
            {isProfileMenuOpen && (
              <div className="absolute right-0 top-12 w-48 bg-surface border border-border rounded-lg shadow-elevated z-1100">
                <div className="p-2">
                  <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150">
                    <Icon name="User" size={16} className="text-text-secondary" />
                    <span className="text-sm text-text-primary">Профиль</span>
                  </button>
                  <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150">
                    <Icon name="Settings" size={16} className="text-text-secondary" />
                    <span className="text-sm text-text-primary">Настройки</span>
                  </button>
                  <button className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-background rounded-lg transition-colors duration-150">
                    <Icon name="HelpCircle" size={16} className="text-text-secondary" />
                    <span className="text-sm text-text-primary">Помощь</span>
                  </button>
                  <hr className="my-2 border-border" />
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center space-x-2 px-3 py-2 text-left hover:bg-error-50 rounded-lg transition-colors duration-150 text-error"
                  >
                    <Icon name="LogOut" size={16} />
                    <span className="text-sm">Выйти</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Click outside to close dropdowns */}
      {(isProfileMenuOpen || isNotificationOpen) && (
        <div
          className="fixed inset-0 z-800"
          onClick={() => {
            setIsProfileMenuOpen(false);
            setIsNotificationOpen(false);
          }}
        />
      )}
    </header>
  );
};

export default Header;