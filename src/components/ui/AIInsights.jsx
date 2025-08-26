import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const AIInsights = ({ studentId, courseId, context }) => {
  const { t } = useTranslation();
  const [insights, setInsights] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!studentId && !courseId && !context) return;
    
    const fetchInsights = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const token = localStorage.getItem('accessToken') || localStorage.getItem('token');
        if (!token) {
          setError('Не авторизован');
          setLoading(false);
          return;
        }
        
        const response = await fetch('http://localhost:8000/api/ai/function', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            message: generatePrompt(studentId, courseId, context),
            student_id: studentId,
            course_id: courseId,
            context: context
          })
        });
        
        if (!response.ok) {
          throw new Error(`Ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        setInsights(data.reply);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchInsights();
  }, [studentId, courseId, context]);
  
  const generatePrompt = (studentId, courseId, context) => {
    if (studentId && courseId) {
      return `Проанализируй успеваемость студента ${studentId} по курсу ${courseId} и дай рекомендации по улучшению.`;
    } else if (studentId) {
      return `Дай общий анализ успеваемости студента ${studentId} и основные рекомендации.`;
    } else if (courseId) {
      return `Проанализируй общую успеваемость по курсу ${courseId} и выдели основные тенденции.`;
    } else if (context === 'teacher-dashboard') {
      return 'Какие основные тенденции в успеваемости студентов можно выделить на данный момент?';
    } else {
      return 'Дай общий анализ успеваемости и основные рекомендации.';
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h3 className="text-lg font-semibold mb-3">{t('aiInsights.title')}</h3>
      
      {loading ? (
        <div className="flex justify-center items-center py-6">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      ) : error ? (
        <div className="text-red-500 py-2">{error}</div>
      ) : (
        <div className="prose prose-sm max-w-none">
          {insights ? (
            <div dangerouslySetInnerHTML={{ __html: insights.replace(/\n/g, '<br/>') }} />
          ) : (
            <p className="text-gray-500">{t('aiInsights.noData')}</p>
          )}
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500">
        {t('aiInsights.poweredBy')} Ollama
      </div>
    </div>
  );
};

export default AIInsights;
