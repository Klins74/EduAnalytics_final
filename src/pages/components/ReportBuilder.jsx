import React, { useState } from 'react';
import Icon from '../../components/AppIcon';

const ReportBuilder = ({ isOpen, onClose }) => {
  const [reportName, setReportName] = useState('');
  const [selectedComponents, setSelectedComponents] = useState([]);
  const [reportType, setReportType] = useState('standard');
  const [schedule, setSchedule] = useState('manual');
  const [recipients, setRecipients] = useState([]);
  const [currentStep, setCurrentStep] = useState(1);

  const reportTypes = [
    { id: 'standard', label: 'Стандартный отчет', description: 'Основные метрики успеваемости и вовлеченности' },
    { id: 'detailed', label: 'Детальный анализ', description: 'Углубленный анализ с AI-инсайтами' },
    { id: 'comparative', label: 'Сравнительный отчет', description: 'Сравнение между классами, периодами или предметами' },
    { id: 'predictive', label: 'Прогнозный отчет', description: 'Прогнозы и рекомендации на основе ML-моделей' }
  ];

  const availableComponents = [
    { id: 'performance', label: 'Успеваемость', icon: 'TrendingUp', category: 'metrics' },
    { id: 'engagement', label: 'Вовлеченность', icon: 'Activity', category: 'metrics' },
    { id: 'attendance', label: 'Посещаемость', icon: 'Calendar', category: 'metrics' },
    { id: 'assignments', label: 'Выполнение заданий', icon: 'FileText', category: 'metrics' },
    { id: 'grade-distribution', label: 'Распределение оценок', icon: 'PieChart', category: 'charts' },
    { id: 'trend-analysis', label: 'Анализ трендов', icon: 'LineChart', category: 'charts' },
    { id: 'heatmap', label: 'Тепловая карта активности', icon: 'Grid3X3', category: 'charts' },
    { id: 'student-ranking', label: 'Рейтинг студентов', icon: 'Trophy', category: 'tables' },
    { id: 'risk-analysis', label: 'Анализ рисков', icon: 'AlertTriangle', category: 'ai' },
    { id: 'predictions', label: 'Прогнозы', icon: 'Target', category: 'ai' },
    { id: 'recommendations', label: 'Рекомендации', icon: 'Lightbulb', category: 'ai' }
  ];

  const scheduleOptions = [
    { id: 'manual', label: 'Вручную', description: 'Создать отчет сейчас' },
    { id: 'daily', label: 'Ежедневно', description: 'Автоматическая отправка каждый день' },
    { id: 'weekly', label: 'Еженедельно', description: 'Автоматическая отправка каждую неделю' },
    { id: 'monthly', label: 'Ежемесячно', description: 'Автоматическая отправка каждый месяц' }
  ];

  const recipientRoles = [
    { id: 'administrators', label: 'Администраторы', count: 3 },
    { id: 'teachers', label: 'Преподаватели', count: 24 },
    { id: 'parents', label: 'Родители', count: 156 },
    { id: 'students', label: 'Студенты', count: 342 }
  ];

  const handleComponentToggle = (componentId) => {
    setSelectedComponents(prev => 
      prev.includes(componentId)
        ? prev.filter(id => id !== componentId)
        : [...prev, componentId]
    );
  };

  const handleRecipientToggle = (roleId) => {
    setRecipients(prev => 
      prev.includes(roleId)
        ? prev.filter(id => id !== roleId)
        : [...prev, roleId]
    );
  };

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGenerate = () => {
    // Simulate report generation
    console.log('Generating report:', {
      name: reportName,
      type: reportType,
      components: selectedComponents,
      schedule,
      recipients
    });
    onClose();
  };

  const getComponentsByCategory = (category) => {
    return availableComponents.filter(comp => comp.category === category);
  };

  const categories = [
    { id: 'metrics', label: 'Метрики', icon: 'BarChart3' },
    { id: 'charts', label: 'Графики', icon: 'PieChart' },
    { id: 'tables', label: 'Таблицы', icon: 'Table' },
    { id: 'ai', label: 'AI-анализ', icon: 'Brain' }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-1100 p-4">
      <div className="bg-surface rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-heading font-semibold text-text-primary">
              Конструктор отчетов
            </h2>
            <p className="text-sm text-text-secondary mt-1">
              Создайте настраиваемый отчет с помощью drag-and-drop
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-background rounded-lg transition-colors duration-150"
          >
            <Icon name="X" size={20} className="text-text-secondary" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-border">
          <div className="flex items-center space-x-4">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep 
                    ? 'bg-primary text-white' :'bg-border text-text-muted'
                }`}>
                  {step}
                </div>
                {step < 4 && (
                  <div className={`w-12 h-0.5 mx-2 ${
                    step < currentStep ? 'bg-primary' : 'bg-border'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-sm">
            <span className={currentStep >= 1 ? 'text-primary font-medium' : 'text-text-muted'}>
              Тип отчета
            </span>
            <span className={currentStep >= 2 ? 'text-primary font-medium' : 'text-text-muted'}>
              Компоненты
            </span>
            <span className={currentStep >= 3 ? 'text-primary font-medium' : 'text-text-muted'}>
              Настройки
            </span>
            <span className={currentStep >= 4 ? 'text-primary font-medium' : 'text-text-muted'}>
              Подтверждение
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* Step 1: Report Type */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Название отчета
                </label>
                <input
                  type="text"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  placeholder="Введите название отчета..."
                  className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-4">
                  Тип отчета
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {reportTypes.map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setReportType(type.id)}
                      className={`p-4 border rounded-lg text-left transition-colors duration-150 ${
                        reportType === type.id
                          ? 'border-primary bg-primary-50' :'border-border hover:border-primary-300'
                      }`}
                    >
                      <h3 className="font-medium text-text-primary mb-1">{type.label}</h3>
                      <p className="text-sm text-text-secondary">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Components */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-text-primary mb-4">
                  Выберите компоненты отчета
                </h3>
                <p className="text-sm text-text-secondary mb-6">
                  Перетащите компоненты в нужном порядке или используйте чекбоксы для выбора
                </p>
              </div>

              {categories.map((category) => (
                <div key={category.id} className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <Icon name={category.icon} size={16} className="text-primary" />
                    <h4 className="font-medium text-text-primary">{category.label}</h4>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {getComponentsByCategory(category.id).map((component) => (
                      <div
                        key={component.id}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors duration-150 ${
                          selectedComponents.includes(component.id)
                            ? 'border-primary bg-primary-50' :'border-border hover:border-primary-300'
                        }`}
                        onClick={() => handleComponentToggle(component.id)}
                      >
                        <div className="flex items-center space-x-2">
                          <Icon name={component.icon} size={16} className="text-text-secondary" />
                          <span className="text-sm font-medium text-text-primary">
                            {component.label}
                          </span>
                          {selectedComponents.includes(component.id) && (
                            <Icon name="Check" size={14} className="text-primary ml-auto" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Step 3: Settings */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-text-primary mb-4">
                  Расписание отправки
                </label>
                <div className="space-y-3">
                  {scheduleOptions.map((option) => (
                    <button
                      key={option.id}
                      onClick={() => setSchedule(option.id)}
                      className={`w-full p-3 border rounded-lg text-left transition-colors duration-150 ${
                        schedule === option.id
                          ? 'border-primary bg-primary-50' :'border-border hover:border-primary-300'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <div className={`w-4 h-4 rounded-full border-2 ${
                          schedule === option.id
                            ? 'border-primary bg-primary' :'border-border'
                        }`}>
                          {schedule === option.id && (
                            <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                          )}
                        </div>
                        <div>
                          <h4 className="font-medium text-text-primary">{option.label}</h4>
                          <p className="text-sm text-text-secondary">{option.description}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-4">
                  Получатели отчета
                </label>
                <div className="space-y-2">
                  {recipientRoles.map((role) => (
                    <div
                      key={role.id}
                      className="flex items-center justify-between p-3 border border-border rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={recipients.includes(role.id)}
                          onChange={() => handleRecipientToggle(role.id)}
                          className="w-4 h-4 text-primary border-border rounded focus:ring-primary"
                        />
                        <span className="font-medium text-text-primary">{role.label}</span>
                      </div>
                      <span className="text-sm text-text-secondary">{role.count} получателей</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Confirmation */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="bg-background border border-border rounded-lg p-4">
                <h3 className="font-medium text-text-primary mb-4">Сводка отчета</h3>
                
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Название:</span>
                    <span className="font-medium text-text-primary">{reportName || 'Без названия'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Тип:</span>
                    <span className="font-medium text-text-primary">
                      {reportTypes.find(t => t.id === reportType)?.label}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Компонентов:</span>
                    <span className="font-medium text-text-primary">{selectedComponents.length}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Расписание:</span>
                    <span className="font-medium text-text-primary">
                      {scheduleOptions.find(s => s.id === schedule)?.label}
                    </span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Получателей:</span>
                    <span className="font-medium text-text-primary">
                      {recipients.reduce((total, roleId) => {
                        const role = recipientRoles.find(r => r.id === roleId);
                        return total + (role ? role.count : 0);
                      }, 0)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-secondary-50 border border-secondary-100 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Icon name="Info" size={16} className="text-secondary mt-0.5" />
                  <div>
                    <h4 className="font-medium text-secondary mb-1">Информация</h4>
                    <p className="text-sm text-text-secondary">
                      Отчет будет сгенерирован с использованием актуальных данных. 
                      Время генерации может составлять от 30 секунд до 2 минут в зависимости 
                      от сложности и объема данных.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className="flex items-center space-x-2 px-4 py-2 text-text-secondary hover:text-text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
          >
            <Icon name="ChevronLeft" size={16} />
            <span>Назад</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors duration-150"
            >
              Отмена
            </button>
            
            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                disabled={currentStep === 1 && !reportName.trim()}
                className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 hover-lift"
              >
                <span>Далее</span>
                <Icon name="ChevronRight" size={16} />
              </button>
            ) : (
              <button
                onClick={handleGenerate}
                className="flex items-center space-x-2 px-4 py-2 bg-success text-white rounded-lg hover:bg-success-600 transition-colors duration-150 hover-lift"
              >
                <Icon name="FileText" size={16} />
                <span>Создать отчет</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportBuilder;