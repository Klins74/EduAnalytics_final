import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import AIChat from '../../components/ui/AIChat';
import Breadcrumb from '../../components/ui/Breadcrumb';
import Icon from '../../components/AppIcon';
import KPICard from './components/KPICard';
import ActivityChart from './components/ActivityChart';
import QuickActions from './components/QuickActions';
import RecentActivity from './components/RecentActivity';

const Dashboard = () => {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('7d');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate data loading
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  // Mock KPI data
  const kpiData = [
    {
      id: 'students',
      title: 'Всего студентов',
      value: '2,847',
      change: '+12%',
      changeType: 'positive',
      icon: 'Users',
      color: 'primary',
      description: 'Активных студентов в системе'
    },
    {
      id: 'activity',
      title: 'Активность',
      value: '89.2%',
      change: '+5.3%',
      changeType: 'positive',
      icon: 'Activity',
      color: 'success',
      description: 'Средняя активность за неделю'
    },
    {
      id: 'performance',
      title: 'Успеваемость',
      value: '4.2',
      change: '+0.3',
      changeType: 'positive',
      icon: 'TrendingUp',
      color: 'accent',
      description: 'Средний балл по системе'
    },
    {
      id: 'alerts',
      title: 'Предупреждения',
      value: '23',
      change: '-8',
      changeType: 'negative',
      icon: 'AlertTriangle',
      color: 'warning',
      description: 'Требуют внимания'
    }
  ];

  // Mock activity data for charts
  const activityData = [
    { date: '01.12', students: 2340, sessions: 4200, engagement: 85 },
    { date: '02.12', students: 2456, sessions: 4350, engagement: 87 },
    { date: '03.12', students: 2398, sessions: 4180, engagement: 82 },
    { date: '04.12', students: 2567, sessions: 4520, engagement: 89 },
    { date: '05.12', students: 2634, sessions: 4680, engagement: 91 },
    { date: '06.12', students: 2589, sessions: 4590, engagement: 88 },
    { date: '07.12', students: 2847, sessions: 4920, engagement: 92 }
  ];

  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 500);
  };

  const handleExportData = () => {
    console.log('Экспорт данных...');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <Sidebar />
        <main className="pt-16 lg:ml-60">
          <div className="p-6">
            <div className="animate-pulse space-y-6">
              <div className="h-8 bg-border rounded w-1/3"></div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-32 bg-border rounded-lg"></div>
                ))}
              </div>
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <div className="xl:col-span-2 h-80 bg-border rounded-lg"></div>
                <div className="h-80 bg-border rounded-lg"></div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      
      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />
          
          {/* Page Header */}
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-8">
            <div>
              <h1 className="text-3xl font-heading font-semibold text-text-primary mb-2">
                Панель управления
              </h1>
              <p className="text-text-secondary">
                Обзор образовательной аналитики и ключевых метрик системы
              </p>
            </div>
            
            <div className="flex items-center space-x-4 mt-4 lg:mt-0">
              {/* Time Range Selector */}
              <div className="flex items-center space-x-2 bg-surface border border-border rounded-lg p-1">
                {[
                  { value: '24h', label: '24ч' },
                  { value: '7d', label: '7д' },
                  { value: '30d', label: '30д' },
                  { value: '90d', label: '90д' }
                ].map((range) => (
                  <button
                    key={range.value}
                    onClick={() => handleTimeRangeChange(range.value)}
                    className={`px-3 py-1.5 text-sm font-medium rounded transition-colors duration-150 ${
                      timeRange === range.value
                        ? 'bg-primary text-white' :'text-text-secondary hover:text-text-primary hover:bg-background'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
              
              {/* Export Button */}
              <button
                onClick={handleExportData}
                className="flex items-center space-x-2 px-4 py-2 bg-surface border border-border text-text-primary rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
              >
                <Icon name="Download" size={16} />
                <span className="hidden sm:inline">Экспорт</span>
              </button>
              
              {/* Refresh Button */}
              <button
                onClick={() => window.location.reload()}
                className="p-2 bg-surface border border-border text-text-primary rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
              >
                <Icon name="RefreshCw" size={16} />
              </button>
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
            {kpiData.map((kpi) => (
              <KPICard key={kpi.id} data={kpi} />
            ))}
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
            {/* Activity Chart */}
            <div className="xl:col-span-2">
              <ActivityChart data={activityData} timeRange={timeRange} />
            </div>
            
            {/* Quick Actions */}
            <div>
              <QuickActions />
            </div>
          </div>

          {/* Recent Activity Table */}
          <div className="mb-8">
            <RecentActivity />
          </div>

          {/* System Status */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-surface border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-heading font-medium text-text-primary">Статус системы</h3>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-success rounded-full"></div>
                  <span className="text-sm text-success font-medium">Работает</span>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">Загрузка сервера</span>
                  <span className="text-sm font-medium text-text-primary">23%</span>
                </div>
                <div className="w-full bg-background rounded-full h-2">
                  <div className="bg-success h-2 rounded-full" style={{ width: '23%' }}></div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">Использование памяти</span>
                  <span className="text-sm font-medium text-text-primary">67%</span>
                </div>
                <div className="w-full bg-background rounded-full h-2">
                  <div className="bg-accent h-2 rounded-full" style={{ width: '67%' }}></div>
                </div>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-heading font-medium text-text-primary">AI Анализ</h3>
                <Icon name="Bot" size={20} className="text-secondary" />
              </div>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-secondary rounded-full ai-pulse"></div>
                  <span className="text-sm text-text-secondary">Обработка данных</span>
                </div>
                <p className="text-sm text-text-primary">
                  Выявлены 3 студента с риском снижения успеваемости
                </p>
                <button className="text-sm text-secondary hover:text-secondary-500 transition-colors duration-150">
                  Подробнее →
                </button>
              </div>
            </div>

            <div className="bg-surface border border-border rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-heading font-medium text-text-primary">Последнее обновление</h3>
                <Icon name="Clock" size={20} className="text-text-secondary" />
              </div>
              <div className="space-y-2">
                <p className="text-sm text-text-primary font-medium">
                  {new Date().toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'Europe/Moscow'
                  })}
                </p>
                <p className="text-xs text-text-secondary">
                  Московское время (UTC+3)
                </p>
                <p className="text-xs text-text-secondary">
                  Следующее обновление через 5 минут
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>

      <AIChat />
    </div>
  );
};

export default Dashboard;