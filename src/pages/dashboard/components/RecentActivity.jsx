import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

// 1. Компонент теперь принимает 'activities' как проп. 
//    Добавлено значение по умолчанию `[]`, чтобы избежать ошибок, если данные еще не загрузились.
const RecentActivity = ({ activities = [] }) => {
  const [sortField, setSortField] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterType, setFilterType] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // 2. Блок с mock-данными `const recentActivities = [...]` был полностью удален.

  const activityTypes = [
    { value: 'all', label: 'Все действия', icon: 'Activity' },
    { value: 'login', label: 'Входы', icon: 'LogIn' },
    { value: 'assignment', label: 'Задания', icon: 'FileText' },
    { value: 'test', label: 'Тесты', icon: 'CheckCircle' },
    { value: 'forum', label: 'Форум', icon: 'MessageSquare' },
    { value: 'logout', label: 'Выходы', icon: 'LogOut' }
  ];

  const getActivityIcon = (type) => {
    const iconMap = {
      login: 'LogIn',
      logout: 'LogOut',
      assignment: 'FileText',
      test: 'CheckCircle',
      forum: 'MessageSquare'
    };
    return iconMap[type] || 'Activity';
  };

  const getStatusColor = (status) => {
    const colorMap = {
      success: 'text-success bg-success-50 border-success-100',
      warning: 'text-warning bg-warning-50 border-warning-100',
      error: 'text-error bg-error-50 border-error-100',
      info: 'text-primary bg-primary-50 border-primary-100'
    };
    return colorMap[status] || colorMap.info;
  };

  const getStatusLabel = (status) => {
    const labelMap = {
      success: 'Успешно',
      warning: 'Внимание',
      error: 'Ошибка',
      info: 'Информация'
    };
    return labelMap[status] || 'Неизвестно';
  };

  const formatTimestamp = (timestamp) => {
    // API возвращает время в виде строки, преобразуем его в объект Date
    const activityDate = new Date(timestamp);
    const now = new Date();
    const diff = now - activityDate;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (minutes < 1) return 'Только что';
    if (minutes < 60) {
      return `${minutes} мин назад`;
    } else if (hours < 24) {
      return `${hours} ч назад`;
    } else {
      return activityDate.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  // 3. Логика фильтрации и сортировки теперь работает с 'activities' из пропсов.
  const filteredActivities = activities.filter(activity => 
    filterType === 'all' || activity.type === filterType
  );

  const sortedActivities = [...filteredActivities].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    // Преобразуем строки времени в числа для корректной сортировки
    if (sortField === 'timestamp') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    }
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const totalPages = Math.ceil(sortedActivities.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedActivities = sortedActivities.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="bg-surface border border-border rounded-lg">
      <div className="p-6 border-b border-border">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div className="mb-4 lg:mb-0">
            <h3 className="text-lg font-heading font-medium text-text-primary mb-1">
              Последние события
            </h3>
            <p className="text-sm text-text-secondary">
              Активность студентов в реальном времени
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Icon name="Filter" size={16} className="text-text-secondary" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-1.5 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                {activityTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            <button className="flex items-center space-x-2 px-3 py-1.5 bg-background border border-border rounded-lg text-sm hover:bg-primary-50 transition-colors duration-150">
              <Icon name="RefreshCw" size={16} className="text-text-secondary" />
              <span>Обновить</span>
            </button>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-background border-b border-border">
            <tr>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('student')}
                  className="flex items-center space-x-1 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors duration-150"
                >
                  <span>СТУДЕНТ</span>
                  <Icon 
                    name={sortField === 'student' && sortDirection === 'asc' ? 'ChevronUp' : 'ChevronDown'} 
                    size={14} 
                  />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('action')}
                  className="flex items-center space-x-1 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors duration-150"
                >
                  <span>ДЕЙСТВИЕ</span>
                  <Icon 
                    name={sortField === 'action' && sortDirection === 'asc' ? 'ChevronUp' : 'ChevronDown'} 
                    size={14} 
                  />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <span className="text-xs font-medium text-text-secondary">КУРС</span>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('timestamp')}
                  className="flex items-center space-x-1 text-xs font-medium text-text-secondary hover:text-text-primary transition-colors duration-150"
                >
                  <span>ВРЕМЯ</span>
                  <Icon 
                    name={sortField === 'timestamp' && sortDirection === 'asc' ? 'ChevronUp' : 'ChevronDown'} 
                    size={14} 
                  />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <span className="text-xs font-medium text-text-secondary">СТАТУС</span>
              </th>
              <th className="px-6 py-3 text-left">
                <span className="text-xs font-medium text-text-secondary">ДЕЙСТВИЯ</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {paginatedActivities.map((activity) => (
              <tr key={activity.id} className="hover:bg-background transition-colors duration-150">
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {activity.student.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-sm text-text-primary">{activity.student}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <Icon name={getActivityIcon(activity.type)} size={16} className="text-text-secondary" />
                    <span className="text-sm text-text-primary">{activity.action}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-text-secondary">{activity.course}</span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-text-secondary">{formatTimestamp(activity.timestamp)}</span>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(activity.status)}`}>
                    {getStatusLabel(activity.status)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <button className="p-1 hover:bg-background rounded transition-colors duration-150">
                      <Icon name="Eye" size={14} className="text-text-secondary hover:text-primary" />
                    </button>
                    <button className="p-1 hover:bg-background rounded transition-colors duration-150">
                      <Icon name="MoreHorizontal" size={14} className="text-text-secondary hover:text-primary" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-border">
          <div className="flex items-center justify-between">
            <div className="text-sm text-text-secondary">
              Показано {startIndex + 1}-{Math.min(startIndex + itemsPerPage, sortedActivities.length)} из {sortedActivities.length} записей
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 bg-background border border-border rounded-lg text-sm hover:bg-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
              >
                <Icon name="ChevronLeft" size={14} />
              </button>
              
              {[...Array(totalPages)].map((_, index) => {
                const page = index + 1;
                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors duration-150 ${
                      currentPage === page
                        ? 'bg-primary text-white' :'bg-background border border-border hover:bg-primary-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 bg-background border border-border rounded-lg text-sm hover:bg-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
              >
                <Icon name="ChevronRight" size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecentActivity;