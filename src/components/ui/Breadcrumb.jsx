import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Icon from '../AppIcon';

const Breadcrumb = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const pathSegments = location.pathname.split('/').filter(segment => segment !== '');
  
  const breadcrumbMap = {
    '': 'Панель управления',
    'ai': 'AI-Помощник',
    'login': 'Вход в систему',
    'students': 'Студенты',
    'analytics': 'Аналитика',
    'reports': 'Отчеты',
    'monitoring': 'Мониторинг',
    'profile': 'Профиль',
    'settings': 'Настройки'
  };

  const generateBreadcrumbs = () => {
    const breadcrumbs = [
      {
        label: 'Главная',
        path: '/',
        isHome: true
      }
    ];

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const label = breadcrumbMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
      
      breadcrumbs.push({
        label,
        path: currentPath,
        isLast: index === pathSegments.length - 1
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  const handleBreadcrumbClick = (path) => {
    navigate(path);
  };

  if (location.pathname === '/login') {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm mb-6" aria-label="Breadcrumb">
      <div className="flex items-center space-x-2 overflow-x-auto">
        {breadcrumbs.map((breadcrumb, index) => (
          <React.Fragment key={breadcrumb.path}>
            {index > 0 && (
              <Icon 
                name="ChevronRight" 
                size={14} 
                className="text-text-muted flex-shrink-0" 
              />
            )}
            
            <div className="flex items-center space-x-1 flex-shrink-0">
              {breadcrumb.isHome && (
                <Icon 
                  name="Home" 
                  size={14} 
                  className="text-text-secondary" 
                />
              )}
              
              {breadcrumb.isLast ? (
                <span className="text-text-primary font-medium">
                  {breadcrumb.label}
                </span>
              ) : (
                <button
                  onClick={() => handleBreadcrumbClick(breadcrumb.path)}
                  className="text-text-secondary hover:text-primary transition-colors duration-150 hover:underline"
                >
                  {breadcrumb.label}
                </button>
              )}
            </div>
          </React.Fragment>
        ))}
      </div>

      {/* Mobile Dropdown for long breadcrumbs */}
      <div className="md:hidden ml-auto">
        {breadcrumbs.length > 2 && (
          <div className="relative">
            <button className="p-1 hover:bg-background rounded transition-colors duration-150">
              <Icon name="MoreHorizontal" size={16} className="text-text-secondary" />
            </button>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Breadcrumb;