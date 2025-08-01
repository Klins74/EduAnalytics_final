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
  
  // Создаем пустое состояние для данных KPI, которые придут с сервера
  const [kpiData, setKpiData] = useState([]);

  useEffect(() => {
    // Новая функция для загрузки данных с сервера
    const fetchKpiData = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('accessToken');

      // Если токена нет, не делаем запрос и перенаправляем на страницу входа
      if (!token) {
        navigate('/login');
        return;
      }
      
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/kpi', {
          headers: {
            // Отправляем токен в заголовке для аутентификации
            'Authorization': `Bearer ${token}` 
          }
        });

        if (response.status === 401) {
          // Если токен недействителен, также перенаправляем на страницу входа
          navigate('/login');
          return;
        }

        if (!response.ok) {
          throw new Error('Не удалось загрузить данные для дашборда');
        }

        const data = await response.json();
        setKpiData(data); // Сохраняем полученные с сервера данные в состояние

      } catch (error) {
        console.error("Ошибка при загрузке KPI:", error);
        // В реальном приложении здесь можно показать пользователю сообщение об ошибке
      } finally {
        setIsLoading(false); // В любом случае убираем индикатор загрузки
      }
    };

    fetchKpiData();
  }, [navigate]); // Добавляем navigate в массив зависимостей

  // Mock-данные для графика, их мы заменим на следующем шаге
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
    // TODO: В будущем здесь будет повторный запрос данных с сервера для нового диапазона
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
              
              <button
                onClick={handleExportData}
                className="flex items-center space-x-2 px-4 py-2 bg-surface border border-border text-text-primary rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
              >
                <Icon name="Download" size={16} />
                <span className="hidden sm:inline">Экспорт</span>
              </button>
              
              <button
                onClick={() => window.location.reload()}
                className="p-2 bg-surface border border-border text-text-primary rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
              >
                <Icon name="RefreshCw" size={16} />
              </button>
            </div>
          </div>

          {/* KPI Cards теперь используют данные с сервера */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
            {kpiData.map((kpi) => (
              <KPICard key={kpi.id} data={kpi} />
            ))}
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
            <div className="xl:col-span-2">
              <ActivityChart data={activityData} timeRange={timeRange} />
            </div>
            
            <div>
              <QuickActions />
            </div>
          </div>

          <div className="mb-8">
            <RecentActivity />
          </div>

          {/* ... остальная часть компонента без изменений ... */}
          
        </div>
      </main>

      <AIChat />
    </div>
  );
};

export default Dashboard;