// src/pages/index.jsx

import React, { useState } from 'react';
import Header from 'components/ui/Header';
import Sidebar from 'components/ui/Sidebar';
import Breadcrumb from 'components/ui/Breadcrumb';
import AIChat from 'components/ui/AIChat';
import Icon from 'components/AppIcon';
import PerformanceTab from './components/PerformanceTab';
import EngagementTab from './components/EngagementTab';
import PredictionsTab from './components/PredictionsTab';
import ComparativeTab from './components/ComparativeTab';
import AIInsights from './components/AIInsights';
import ReportBuilder from './components/ReportBuilder';

const AnalyticsDashboard = () => {
  const [activeTab, setActiveTab] = useState('performance');
  const [isReportBuilderOpen, setIsReportBuilderOpen] = useState(false);

  const tabs = [
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'engagement', label: 'Вовлеченность', icon: 'Activity' },
    { id: 'predictions', label: 'Прогнозы', icon: 'Target' },
    { id: 'comparative', label: 'Сравнительный анализ', icon: 'BarChart3' }
  ];

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'performance':
        return <PerformanceTab />;
      case 'engagement':
        return <EngagementTab />;
      case 'predictions':
        return <PredictionsTab />;
      case 'comparative':
        return <ComparativeTab />;
      default:
        return <PerformanceTab />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />

      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />

          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-heading font-semibold text-text-primary mb-2">
                  Аналитика и отчеты
                </h1>
                <p className="text-text-secondary">
                  Комплексная система анализа образовательных данных с AI-генерацией инсайтов
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => setIsReportBuilderOpen(true)}
                  className="flex items-center space-x-2 px-4 py-2 bg-secondary text-white rounded-lg hover:bg-secondary-500 transition-colors duration-150 hover-lift"
                >
                  <Icon name="Plus" size={16} />
                  <span className="font-medium">Создать отчет</span>
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            <div className="xl:col-span-3">
              <div className="bg-surface border border-border rounded-lg shadow-card">
                <div className="border-b border-border">
                  <nav className="flex overflow-x-auto">
                    {tabs.map((tab) => (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center space-x-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors duration-150 whitespace-nowrap ${
                          activeTab === tab.id
                            ? 'border-primary text-primary bg-primary-50' :'border-transparent text-text-secondary hover:text-text-primary hover:bg-background'
                        }`}
                      >
                        <Icon name={tab.icon} size={16} />
                        <span>{tab.label}</span>
                      </button>
                    ))}
                  </nav>
                </div>

                <div className="p-6">
                  {renderActiveTab()}
                </div>
              </div>
            </div>

            <div className="xl:col-span-1">
              <AIInsights activeTab={activeTab} />
            </div>
          </div>
        </div>
      </main>

      {isReportBuilderOpen && (
        <ReportBuilder
          isOpen={isReportBuilderOpen}
          onClose={() => setIsReportBuilderOpen(false)}
        />
      )}

      <AIChat />
    </div>
  );
};

export default AnalyticsDashboard;