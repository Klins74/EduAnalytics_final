import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import Icon from '../../components/AppIcon';

const PredictionsTab = ({ period, analysisType }) => {
  const [selectedModel, setSelectedModel] = useState('performance');
  const [predictionHorizon, setPredictionHorizon] = useState('month');

  const performancePrediction = [
    { month: 'Янв', actual: 4.1, predicted: 4.1, confidence: 95 },
    { month: 'Фев', actual: 4.0, predicted: 4.0, confidence: 94 },
    { month: 'Мар', actual: 4.2, predicted: 4.1, confidence: 92 },
    { month: 'Апр', actual: null, predicted: 4.3, confidence: 88 },
    { month: 'Май', actual: null, predicted: 4.4, confidence: 85 },
    { month: 'Июн', actual: null, predicted: 4.2, confidence: 82 }
  ];

  const riskPredictions = [
    { name: 'Иванов А.', currentGrade: 4.2, predictedGrade: 3.8, riskLevel: 'medium', probability: 65 },
    { name: 'Петрова М.', currentGrade: 3.5, predictedGrade: 3.1, riskLevel: 'high', probability: 82 },
    { name: 'Сидоров Д.', currentGrade: 3.8, predictedGrade: 3.4, riskLevel: 'medium', probability: 58 },
    { name: 'Козлова Е.', currentGrade: 3.2, predictedGrade: 2.8, riskLevel: 'high', probability: 89 },
    { name: 'Морозов И.', currentGrade: 4.0, predictedGrade: 3.6, riskLevel: 'medium', probability: 71 }
  ];

  const engagementForecast = [
    { week: 'Нед 1', engagement: 85, predicted: 85 },
    { week: 'Нед 2', engagement: 82, predicted: 83 },
    { week: 'Нед 3', engagement: 88, predicted: 87 },
    { week: 'Нед 4', engagement: 84, predicted: 85 },
    { week: 'Нед 5', engagement: null, predicted: 86 },
    { week: 'Нед 6', engagement: null, predicted: 88 },
    { week: 'Нед 7', engagement: null, predicted: 87 },
    { week: 'Нед 8', engagement: null, predicted: 89 }
  ];

  const interventionRecommendations = [
    {
      student: 'Петрова Мария',
      risk: 'high',
      recommendation: 'Индивидуальные консультации по математике',
      impact: 85,
      timeline: '2 недели'
    },
    {
      student: 'Козлова Елена',
      risk: 'high',
      recommendation: 'Дополнительные практические занятия',
      impact: 78,
      timeline: '3 недели'
    },
    {
      student: 'Иванов Алексей',
      risk: 'medium',
      recommendation: 'Групповые проекты для мотивации',
      impact: 65,
      timeline: '1 месяц'
    }
  ];

  const modelAccuracy = [
    { model: 'Успеваемость', accuracy: 87.3, samples: 1250 },
    { model: 'Вовлеченность', accuracy: 82.1, samples: 980 },
    { model: 'Риск отсева', accuracy: 91.5, samples: 450 },
    { model: 'Поведенческие паттерны', accuracy: 79.8, samples: 1100 }
  ];

  const models = [
    { id: 'performance', label: 'Прогноз успеваемости', icon: 'TrendingUp' },
    { id: 'engagement', label: 'Прогноз вовлеченности', icon: 'Activity' },
    { id: 'risk', label: 'Анализ рисков', icon: 'AlertTriangle' },
    { id: 'interventions', label: 'Рекомендации', icon: 'Target' }
  ];

  const horizons = [
    { value: 'week', label: '1 неделя' },
    { value: 'month', label: '1 месяц' },
    { value: 'quarter', label: '3 месяца' },
    { value: 'semester', label: 'Семестр' }
  ];

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'text-error bg-error-50 border-error';
      case 'medium': return 'text-warning bg-warning-50 border-warning';
      case 'low': return 'text-success bg-success-50 border-success';
      default: return 'text-text-secondary bg-background border-border';
    }
  };

  const getRiskLabel = (level) => {
    switch (level) {
      case 'high': return 'Высокий риск';
      case 'medium': return 'Средний риск';
      case 'low': return 'Низкий риск';
      default: return 'Неопределен';
    }
  };

  return (
    <div className="space-y-6">
      {/* Model and Horizon Selectors */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {models.map((model) => (
            <button
              key={model.id}
              onClick={() => setSelectedModel(model.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors duration-150 ${
                selectedModel === model.id
                  ? 'bg-primary text-white' :'bg-background text-text-secondary hover:bg-primary-50 hover:text-primary'
              }`}
            >
              <Icon name={model.icon} size={16} />
              <span className="font-medium">{model.label}</span>
            </button>
          ))}
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-text-primary">Горизонт:</label>
          <select
            value={predictionHorizon}
            onChange={(e) => setPredictionHorizon(e.target.value)}
            className="px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-background"
          >
            {horizons.map(horizon => (
              <option key={horizon.value} value={horizon.value}>
                {horizon.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* AI Model Accuracy */}
      <div className="bg-background border border-border rounded-lg p-6">
        <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
          Точность моделей машинного обучения
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {modelAccuracy.map((model, index) => (
            <div key={index} className="bg-surface border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-text-primary">{model.model}</h4>
                <div className="w-8 h-8 bg-secondary-100 rounded-full flex items-center justify-center">
                  <Icon name="Brain" size={16} className="text-secondary" />
                </div>
              </div>
              <div className="text-2xl font-heading font-semibold text-secondary mb-1">
                {model.accuracy}%
              </div>
              <div className="text-sm text-text-secondary">
                {model.samples.toLocaleString('ru-RU')} образцов
              </div>
              <div className="w-full bg-border rounded-full h-2 mt-2">
                <div 
                  className="bg-secondary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${model.accuracy}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedModel === 'performance' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Прогноз успеваемости
          </h3>
          
          <div className="h-80 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={performancePrediction}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis domain={[3.5, 4.5]} tick={{ fontSize: 12 }} />
                <Tooltip 
                  formatter={(value, name) => [
                    value, 
                    name === 'actual' ? 'Фактический' : 'Прогнозируемый'
                  ]}
                />
                <Line 
                  type="monotone" 
                  dataKey="actual" 
                  stroke="#3B82F6" 
                  strokeWidth={3}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 6 }}
                  connectNulls={false}
                  name="actual"
                />
                <Line 
                  type="monotone" 
                  dataKey="predicted" 
                  stroke="#7C3AED" 
                  strokeWidth={3}
                  strokeDasharray="5 5"
                  dot={{ fill: '#7C3AED', strokeWidth: 2, r: 6 }}
                  name="predicted"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-primary-50 border border-primary-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="TrendingUp" size={16} className="text-primary" />
                <span className="font-medium text-primary">Тренд</span>
              </div>
              <p className="text-sm text-text-secondary">
                Ожидается улучшение на 0,2 балла к концу семестра
              </p>
            </div>
            
            <div className="bg-success-50 border border-success-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="Target" size={16} className="text-success" />
                <span className="font-medium text-success">Достижимость</span>
              </div>
              <p className="text-sm text-text-secondary">
                85% вероятность достижения целевого показателя 4,3
              </p>
            </div>
            
            <div className="bg-accent-50 border border-accent-100 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Icon name="AlertCircle" size={16} className="text-accent" />
                <span className="font-medium text-accent">Внимание</span>
              </div>
              <p className="text-sm text-text-secondary">
                Снижение точности прогноза после 3 месяцев
              </p>
            </div>
          </div>
        </div>
      )}

      {selectedModel === 'engagement' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Прогноз вовлеченности студентов
          </h3>
          
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={engagementForecast}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar 
                  dataKey="engagement" 
                  fill="#10B981" 
                  name="Фактическая"
                  radius={[4, 4, 0, 0]}
                />
                <Bar 
                  dataKey="predicted" 
                  fill="#7C3AED" 
                  name="Прогнозируемая"
                  radius={[4, 4, 0, 0]}
                  opacity={0.7}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {selectedModel === 'risk' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            Анализ рисков успеваемости
          </h3>
          
          <div className="space-y-4">
            {riskPredictions.map((student, index) => (
              <div key={index} className="bg-surface border border-border rounded-lg p-4">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary-600 rounded-full flex items-center justify-center text-white font-medium">
                      {student.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <h4 className="font-medium text-text-primary">{student.name}</h4>
                      <div className="flex items-center space-x-4 text-sm text-text-secondary">
                        <span>Текущий: {student.currentGrade}</span>
                        <span>Прогноз: {student.predictedGrade}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <div className="text-sm text-text-secondary">Вероятность снижения</div>
                      <div className="text-lg font-semibold text-text-primary">{student.probability}%</div>
                    </div>
                    <div className={`px-3 py-1 rounded-full border text-sm font-medium ${getRiskColor(student.riskLevel)}`}>
                      {getRiskLabel(student.riskLevel)}
                    </div>
                  </div>
                </div>
                
                <div className="mt-3">
                  <div className="w-full bg-border rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        student.riskLevel === 'high' ? 'bg-error' : 
                        student.riskLevel === 'medium' ? 'bg-warning' : 'bg-success'
                      }`}
                      style={{ width: `${student.probability}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedModel === 'interventions' && (
        <div className="bg-background border border-border rounded-lg p-6">
          <h3 className="text-lg font-heading font-medium text-text-primary mb-4">
            AI-рекомендации по вмешательству
          </h3>
          
          <div className="space-y-4">
            {interventionRecommendations.map((item, index) => (
              <div key={index} className="bg-surface border border-border rounded-lg p-4">
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-medium text-text-primary">{item.student}</h4>
                      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(item.risk)}`}>
                        {getRiskLabel(item.risk)}
                      </div>
                    </div>
                    
                    <p className="text-text-secondary mb-3">{item.recommendation}</p>
                    
                    <div className="flex items-center space-x-4 text-sm">
                      <div className="flex items-center space-x-1">
                        <Icon name="Clock" size={14} className="text-text-muted" />
                        <span className="text-text-secondary">{item.timeline}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Icon name="Target" size={14} className="text-text-muted" />
                        <span className="text-text-secondary">Эффективность: {item.impact}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-end space-y-2">
                    <button className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-700 transition-colors duration-150 hover-lift">
                      <Icon name="Play" size={16} />
                      <span className="font-medium">Применить</span>
                    </button>
                    
                    <div className="text-right">
                      <div className="text-sm text-text-secondary">Прогнозируемый эффект</div>
                      <div className="w-24 bg-border rounded-full h-2 mt-1">
                        <div 
                          className="bg-success h-2 rounded-full transition-all duration-300"
                          style={{ width: `${item.impact}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-6 p-4 bg-secondary-50 border border-secondary-100 rounded-lg">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
                <Icon name="Brain" size={16} color="white" />
              </div>
              <div>
                <h4 className="font-medium text-secondary mb-1">AI-анализ</h4>
                <p className="text-sm text-text-secondary">
                  Рекомендации основаны на анализе 15 000+ случаев успешных вмешательств. 
                  Модель учитывает индивидуальные особенности студентов, их историю обучения 
                  и текущие показатели для максимальной эффективности предлагаемых мер.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PredictionsTab;