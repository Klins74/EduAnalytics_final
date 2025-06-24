// src/api/mockApi.js

import { 
  kpiData, 
  activityData, 
  studentsData, 
  performanceData, 
  gradeDistribution, 
  trendData,
  engagementData,
  activityHeatmap,
  engagementMetrics,
  topEngagedStudents,
  lowEngagementStudents,
  classComparisonData,
  subjectComparisonData,
  teacherComparisonData,
  timeComparisonData,
  insightsByTab
} from './mockData.js';

const mockFetch = (data, delay = 500) => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(data);
    }, delay);
  });
};

export const getKpiData = (timeRange) => {
  return mockFetch(kpiData);
};

export const getActivityData = (timeRange) => {
  return mockFetch(activityData);
};

export const getStudentsData = () => {
  return mockFetch(studentsData);
};

export const getPerformanceTabData = () => {
  const data = {
    performanceData,
    gradeDistribution,
    trendData,
  };
  return mockFetch(data);
};

export const getEngagementTabData = () => {
  const data = {
    engagementData,
    activityHeatmap,
    engagementMetrics,
    topEngagedStudents,
    lowEngagementStudents,
  };
  return mockFetch(data);
};

export const getComparativeTabData = () => {
  const data = {
    classComparison: classComparisonData,
    subjectComparison: subjectComparisonData,
    teacherComparison: teacherComparisonData,
    timeComparison: timeComparisonData,
  };
  return mockFetch(data);
};

export const getAiInsights = (tab) => {
  const data = insightsByTab[tab] || [];
  return mockFetch(data, 800);
};

// --- НЕДОСТАЮЩАЯ ЛОГИКА ДЛЯ AI-ЧАТА ---

// Эта функция будет нашей имитацией "мозга" AI
const generateContextualAIResponse = (userInput) => {
    const responses = {
        'успеваемость': `Анализ успеваемости показывает следующие тенденции:\n\n📊 **Общая статистика:**\n• Средний балл: 4.2/5.0\n• Процент успешных студентов: 87%\n\n🎯 **Ключевые инсайты:**\n• Студенты лучше справляются с практическими заданиями\n• Снижение активности в пятницу на 23%`,
        'отчет': `Генерирую персонализированный отчет...\n\n📈 **Аналитический отчет за период:**\n• Обработано данных: 15,847 взаимодействий\n• Выявлено паттернов: 23 значимых тренда`,
        'рекомендации': `На основе анализа данных предлагаю следующие рекомендации:\n\n🎯 **Приоритетные действия:**\n1. Увеличить количество интерактивных элементов в курсах\n2. Внедрить систему микрообучения для сложных тем`,
        'default': `Проанализировал ваш запрос. Могу предоставить более детальный анализ по конкретным аспектам. Что вас интересует больше всего?`
    };
    const lowerInput = userInput.toLowerCase();
    if (lowerInput.includes('успеваемость') || lowerInput.includes('оценки')) {
        return responses.успеваемость;
    } else if (lowerInput.includes('отчет') || lowerInput.includes('статистика')) {
        return responses.отчет;
    } else if (lowerInput.includes('рекомендации') || lowerInput.includes('советы')) {
        return responses.рекомендации;
    }
    return responses.default;
};

// А это наша "ручка" API для чата, которую искал компонент
export const getAiChatResponse = (userInput) => {
  const responseText = generateContextualAIResponse(userInput);
  // Имитируем "размышления" AI с помощью задержки
  return mockFetch(responseText, 1500); 
};