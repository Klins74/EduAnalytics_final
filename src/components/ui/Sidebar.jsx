import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Icon from '../AppIcon';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Панель управления',
      path: '/',
      icon: 'LayoutDashboard',
      requiredRole: 'all',
      contextualTooltip: 'Центральная панель управления системой'
    },
    {
      id: 'courses',
      label: 'Курсы',
      path: '/courses',
      icon: 'BookOpen',
      requiredRole: 'all',
      contextualTooltip: 'Список курсов и переход к разделам курса'
    },
    {
      id: 'schedule',
      label: 'Расписание',
      path: '/schedule',
      icon: 'Calendar',
      requiredRole: 'all',
      contextualTooltip: 'Расписание занятий и событий'
    },
    {
      id: 'quiz',
      label: 'Квизы',
      path: '/quiz',
      icon: 'ListChecks',
      requiredRole: 'all',
      contextualTooltip: 'Создание и прохождение квизов'
    },
    {
      id: 'monitoring',
      label: 'Мониторинг студентов',
      path: '/monitoring',
      icon: 'Users',
      requiredRole: 'all',
      contextualTooltip: 'Отслеживание активности студентов'
    },
    {
      id: 'analytics',
      label: 'Аналитика и отчеты',
      path: '/analytics',
      icon: 'BarChart3',
      requiredRole: 'all',
      contextualTooltip: 'Аналитические панели и отчеты'
    },
    {
      id: 'ai-assistant',
      label: 'AI-помощник',
      path: '/ai',
      icon: 'Bot',
      requiredRole: 'all',
      contextualTooltip: 'Интеллектуальный помощник для анализа данных'
    }
  ];

  const handleNavigation = (path) => {
    navigate(path);
    setIsMobileOpen(false);
  };

  const isActiveRoute = (path) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const toggleMobile = () => {
    setIsMobileOpen(!isMobileOpen);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleMobile}
        className="fixed top-4 left-4 z-1100 p-2 bg-surface border border-border rounded-lg shadow-card lg:hidden"
      >
        <Icon name="Menu" size={20} className="text-text-primary" />
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-900 lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-16 left-0 h-[calc(100vh-4rem)] bg-surface border-r border-border z-900
          transition-all duration-300 ease-in-out
          ${isCollapsed ? 'w-16' : 'w-60'}
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          lg:fixed
        `}
      >
        <div className="flex flex-col h-full">
          {/* Collapse Toggle */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            {!isCollapsed && (
              <h2 className="font-heading font-medium text-text-primary">Навигация</h2>
            )}
            <button
              onClick={toggleCollapse}
              className="p-1.5 hover:bg-background rounded-lg transition-colors duration-150 hover-lift hidden lg:block"
            >
              <Icon 
                name={isCollapsed ? "ChevronRight" : "ChevronLeft"} 
                size={16} 
                className="text-text-secondary" 
              />
            </button>
          </div>

          {/* Navigation Menu */}
          <nav className="flex-1 p-4 space-y-2">
            {menuItems.map((item) => {
              const isActive = isActiveRoute(item.path);
              
              return (
                <div key={item.id} className="relative group">
                  <button
                    onClick={() => handleNavigation(item.path)}
                    className={`
                      w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-150
                      hover-lift group
                      ${isActive 
                        ? 'bg-primary text-white shadow-card' 
                        : 'text-text-primary hover:bg-background hover:text-primary'
                      }
                      ${isCollapsed ? 'justify-center' : 'justify-start'}
                    `}
                  >
                    <Icon 
                      name={item.icon} 
                      size={20} 
                      className={`
                        ${isActive ? 'text-white' : 'text-text-secondary group-hover:text-primary'}
                        transition-colors duration-150
                      `}
                    />
                    {!isCollapsed && (
                      <span className="font-medium text-sm">{item.label}</span>
                    )}
                    
                    {/* AI Indicator for AI Assistant */}
                    {item.id === 'ai-assistant' && !isCollapsed && (
                      <div className="ml-auto">
                        <div className="w-2 h-2 bg-secondary rounded-full ai-pulse" />
                      </div>
                    )}
                  </button>

                  {/* Tooltip for collapsed state */}
                  {isCollapsed && (
                    <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 px-2 py-1 bg-text-primary text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none whitespace-nowrap z-1100">
                      {item.label}
                      <div className="absolute right-full top-1/2 transform -translate-y-1/2 border-4 border-transparent border-r-text-primary" />
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          {/* Bottom Section */}
          <div className="p-4 border-t border-border">
            {!isCollapsed && (
              <div className="bg-primary-50 rounded-lg p-3 mb-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Icon name="Lightbulb" size={16} className="text-primary" />
                  <span className="text-sm font-medium text-primary">Совет</span>
                </div>
                <p className="text-xs text-text-secondary">
                  Используйте AI-помощника для быстрого анализа данных студентов
                </p>
              </div>
            )}
            
            <button
              className={`
                w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-150
                text-text-secondary hover:bg-background hover:text-primary hover-lift
                ${isCollapsed ? 'justify-center' : 'justify-start'}
              `}
            >
              <Icon name="Settings" size={20} />
              {!isCollapsed && (
                <span className="font-medium text-sm">Настройки</span>
              )}
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Spacer */}
      <div className={`${isCollapsed ? 'lg:ml-16' : 'lg:ml-60'} transition-all duration-300`} />
    </>
  );
};

export default Sidebar;