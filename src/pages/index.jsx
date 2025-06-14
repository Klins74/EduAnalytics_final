import React, { useState, useEffect } from 'react';
import Header from '../components/ui/Header';
import Sidebar from '../components/ui/Sidebar';
import Breadcrumb from '../components/ui/Breadcrumb';
import AIChat from '../components/ui/AIChat';
import Icon from '../components/AppIcon';
import PerformanceTab from './components/PerformanceTab';
import EngagementTab from './components/EngagementTab';
import PredictionsTab from './components/PredictionsTab';
import ComparativeTab from './components/ComparativeTab';
import AIInsights from './components/AIInsights';
import ReportBuilder from './components/ReportBuilder';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('performance');
  const [selectedPeriod, setSelectedPeriod] = useState('month');
  const [selectedAnalysisType, setSelectedAnalysisType] = useState('detailed');
  const [isReportBuilderOpen, setIsReportBuilderOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const tabs = [
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp' },
    { id: 'engagement', label: 'Вовлеченность', icon: 'Activity' },
    { id: 'predictions', label: 'Прогнозы', icon: 'Target' },
    { id: 'comparative', label: 'Сравнительный анализ', icon: 'BarChart3' }
  ];

  const periods = [
    { value: 'week', label: 'Неделя' },
    { value: 'month', label: 'Месяц' },
    { value: 'quarter', label: 'Квартал' },
    { value: 'year', label: 'Год' },
    { value: 'custom', label: 'Произвольный период' }
  ];

  const analysisTypes = [
    { value: 'overview', label: 'Обзор' },
    { value: 'detailed', label: 'Детальный' },
    { value: 'advanced', label: 'Расширенный' }
  ];

  const handleExport = async (format) => {
    setIsExporting(true);
    // Simulate export process
    setTimeout(() => {
      setIsExporting(false);
      // Mock download
      const filename = `analytics_report_${new Date().toLocaleDateString('ru-RU').replace(/\./g, '_')}.${format}`;
      console.log(`Экспорт завершен: ${filename}`);
    }, 2000);
  };

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'performance':
        return <PerformanceTab period={selectedPeriod} analysisType={selectedAnalysisType} />;
      case 'engagement':
        return <EngagementTab period={selectedPeriod} analysisType={selectedAnalysisType} />;
      case 'predictions':
        return <PredictionsTab period={selectedPeriod} analysisType={selectedAnalysisType} />;
      case 'comparative':
        return <ComparativeTab period={selectedPeriod} analysisType={selectedAnalysisType} />;
      default:
        return <PerformanceTab period={selectedPeriod} analysisType={selectedAnalysisType} />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      
      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />
          
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
              <div>
                <h1 className="text-3xl font-heading font-semibold text-text-primary mb-2">
                  Аналитика обучения и отчеты
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
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleExport('excel')}
                    disabled={isExporting}
                    className="flex items-center space-x-2 px-4 py-2 bg-success text-white rounded-lg hover:bg-success-600 disabled:opacity-50 transition-colors duration-150 hover-lift"
                  >
                    <Icon name="FileSpreadsheet" size={16} />
                    <span className="font-medium">Excel</span>
                  </button>
                  
                  <button
                    onClick={() => handleExport('pdf')}
                    disabled={isExporting}
                    className="flex items-center space-x-2 px-4 py-2 bg-error text-white rounded-lg hover:bg-error-600 disabled:opacity-50 transition-colors duration-150 hover-lift"
                  >
                    <Icon name="FileText" size={16} />
                    <span className="font-medium">PDF</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Toolbar */}
          <div className="bg-surface border border-border rounded-lg p-4 mb-6 shadow-card">
            <div className="flex flex-col lg:flex-row lg:items-center gap-4">
              <div className="flex flex-col sm:flex-row gap-4 flex-1">
                <div className="flex flex-col space-y-1">
                  <label className="text-sm font-medium text-text-primary">Период</label>
                  <select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value)}
                    className="px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
                  >
                    {periods.map(period => (
                      <option key={period.value} value={period.value}>
                        {period.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="flex flex-col space-y-1">
                  <label className="text-sm font-medium text-text-primary">Тип анализа</label>
                  <select
                    value={selectedAnalysisType}
                    onChange={(e) => setSelectedAnalysisType(e.target.value)}
                    className="px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
                  >
                    {analysisTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              {isExporting && (
                <div className="flex items-center space-x-2 text-primary">
                  <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm font-medium">Экспорт...</span>
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
            {/* Main Content */}
            <div className="xl:col-span-3">
              {/* Tabs */}
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

            {/* AI Insights Sidebar */}
            <div className="xl:col-span-1">
              <AIInsights activeTab={activeTab} period={selectedPeriod} />
            </div>
          </div>
        </div>
      </main>

      {/* Report Builder Modal */}
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

export default Dashboard;