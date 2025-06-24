import React from 'react';
import Header from '../components/ui/Header';
import Sidebar from '../components/ui/Sidebar';
import Breadcrumb from '../components/ui/Breadcrumb';

const MonitoringPage = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />
          <h1 className="text-3xl font-heading font-semibold text-text-primary">
            Страница Аналитика и Отчетов
          </h1>
          <p className="text-text-secondary mt-2">
            Здесь будет содержимое страницы мониторинга...
          </p>
        </div>
      </main>
    </div>
  );
};

export default MonitoringPage;