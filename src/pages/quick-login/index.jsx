import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';

const QuickLoginPage = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Готов к автоматическому входу');
  const [loading, setLoading] = useState(false);

  const performAutoLogin = async () => {
    setLoading(true);
    setStatus('Выполняется автоматический вход...');
    
    try {
      const response = await fetch('http://localhost:8000/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'username=admin@example.com&password=admin'
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('accessToken', data.access_token);
        
        setStatus('✅ Вход выполнен успешно! Перенаправление...');
        
        setTimeout(() => {
          navigate('/reminders');
        }, 2000);
        
      } else {
        throw new Error(`Ошибка авторизации: ${response.status}`);
      }
      
    } catch (error) {
      console.error('Auto-login failed:', error);
      setStatus(`❌ Автовход не удался: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const goToManualLogin = () => {
    navigate('/login');
  };

  const setTokenManually = () => {
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc1NTI1NDY4MX0.XQgnRbNZHX0m5DefTojqZkKbwvcaR6jOK-7HRhueMuw';
    localStorage.setItem('accessToken', token);
    setStatus('✅ Токен установлен вручную! Перенаправление...');
    
    setTimeout(() => {
      navigate('/reminders');
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <div className="flex-1 p-6">
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                  🔐 Быстрый вход в EduAnalytics
                </h1>
                <p className="text-gray-600">
                  Выберите способ входа в систему
                </p>
              </div>

              <div className="space-y-6">
                {/* Автоматический вход */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-3">
                    🚀 Автоматический вход (РЕКОМЕНДУЕТСЯ)
                  </h3>
                  <p className="text-blue-700 mb-4">
                    Система автоматически выполнит вход с данными admin@example.com
                  </p>
                  <button
                    onClick={performAutoLogin}
                    disabled={loading}
                    className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? '⏳ Выполняется...' : '🔑 Выполнить автоматический вход'}
                  </button>
                </div>

                {/* Ручная установка токена */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-green-900 mb-3">
                    🔧 Ручная установка токена
                  </h3>
                  <p className="text-green-700 mb-4">
                    Установить готовый токен авторизации
                  </p>
                  <button
                    onClick={setTokenManually}
                    className="w-full bg-green-600 text-white py-3 px-6 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    🎯 Установить токен и войти
                  </button>
                </div>

                {/* Ручной вход */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    📝 Ручной вход
                  </h3>
                  <p className="text-gray-700 mb-4">
                    Ввести данные для входа вручную
                  </p>
                  <div className="bg-gray-100 p-4 rounded-lg mb-4">
                    <p className="text-sm text-gray-600">
                      <strong>Email:</strong> admin@example.com<br/>
                      <strong>Пароль:</strong> admin
                    </p>
                  </div>
                  <button
                    onClick={goToManualLogin}
                    className="w-full bg-gray-600 text-white py-3 px-6 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    📋 Открыть страницу входа
                  </button>
                </div>

                {/* Статус */}
                <div className="bg-white border border-gray-200 rounded-lg p-4">
                  <h4 className="font-medium text-gray-900 mb-2">Статус:</h4>
                  <div className="text-gray-700">{status}</div>
                </div>
              </div>

              {/* Информация */}
              <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h4 className="font-medium text-yellow-900 mb-2">ℹ️ Информация:</h4>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>• API сервер работает на localhost:8000</li>
                  <li>• Все сервисы запущены и работают</li>
                  <li>• После входа доступны все функции системы</li>
                  <li>• Токен сохраняется автоматически</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickLoginPage;
