// src/pages/login/index.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../../components/AppIcon';


const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: 'admin@example.com',
    password: 'admin'
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email мекенжайын енгізіңіз';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email мекенжайын дұрыс енгізіңіз';
    }

    if (!formData.password) {
      newErrors.password = 'Құпия сөзді енгізіңіз';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setIsLoading(true);
    setErrors({}); // Сбрасываем старые ошибки

    // FastAPI OAuth2PasswordRequestForm ожидает данные в формате form-data,
    // а не JSON. Поэтому мы используем FormData.
    const formBody = new FormData();
    formBody.append('username', formData.email);
    formBody.append('password', formData.password);

    try {
      const response = await fetch('http://localhost:8000/api/auth/token', {
        method: 'POST',
        body: formBody,
      });

      if (!response.ok) {
        // Если сервер вернул ошибку (например, 401 Unauthorized)
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка аутентификации');
      }

      const data = await response.json();
      
      // Сохраняем токен в localStorage для будущих запросов
      localStorage.setItem('accessToken', data.access_token);
      
      // Перенаправляем пользователя на главную страницу
      navigate('/');

    } catch (error) {
      setErrors({
        general: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    alert('Құпия сөзді қалпына келтіру функциясы жүйенің толық нұсқасында қолжетімді болады');
  };

  const handleExternalLogin = (provider) => {
    alert(`${provider} арқылы кіру жүйенің толық нұсқасында қолжетімді болады`);
  };

  const features = [
    {
      icon: 'BarChart3',
      title: 'Нақты уақыттағы аналитика',
      description: 'Студенттердің белсенділігін бақылап, білім беру деректерін нақты уақыт режимінде талдаңыз'
    },
    {
      icon: 'Bot',
      title: 'AI-көмекші',
      description: 'Жасанды интеллект пен машиналық оқытуды қолдана отырып, деректерді интеллектуалды талдау'
    },
    {
      icon: 'Users',
      title: 'Студенттер мониторингі',
      description: 'Оқушылардың үлгерімі мен оқу процесіне қатысуын кешенді бақылау'
    },
    {
      icon: 'TrendingUp',
      title: 'Болжамды аналитика',
      description: 'Мінез-құлық үлгілерін талдау негізінде білім беру нәтижелерін болжау'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl bg-surface rounded-2xl shadow-elevated overflow-hidden">
        <div className="flex flex-col lg:flex-row min-h-[600px]">
          {/* Login Form Section */}
          <div className="flex-1 flex items-center justify-center p-8 lg:p-12">
            <div className="w-full max-w-md">
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Icon name="GraduationCap" size={32} color="white" />
                </div>
                <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">
                  EduAnalytics AI
                </h1>
                <p className="text-text-secondary">
                  Білім беру аналитикасының интеллектуалды жүйесі
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                {errors.general && (
                  <div className="bg-error-50 border border-error-100 rounded-lg p-4 flex items-start space-x-3">
                    <Icon name="AlertCircle" size={20} className="text-error flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-error font-medium">Кіру қатесі</p>
                      <p className="text-sm text-error mt-1">{errors.general}</p>
                    </div>
                  </div>
                )}

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                    Email мекенжайы
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Icon name="Mail" size={20} className="text-text-secondary" />
                    </div>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-150 ${
                        errors.email ? 'border-error bg-error-50' : 'border-border bg-background'
                      }`}
                      placeholder="Email поштаңызды енгізіңіз"
                      autoComplete="email"
                    />
                  </div>
                  {errors.email && (
                    <p className="mt-2 text-sm text-error flex items-center space-x-1">
                      <Icon name="AlertCircle" size={16} />
                      <span>{errors.email}</span>
                    </p>
                  )}
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                    Құпия сөз
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Icon name="Lock" size={20} className="text-text-secondary" />
                    </div>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="password"
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      className={`w-full pl-10 pr-12 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-150 ${
                        errors.password ? 'border-error bg-error-50' : 'border-border bg-background'
                      }`}
                      placeholder="Құпия сөзді енгізіңіз"
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    >
                      <Icon 
                        name={showPassword ? 'EyeOff' : 'Eye'} 
                        size={20} 
                        className="text-text-secondary hover:text-text-primary transition-colors duration-150" 
                      />
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-2 text-sm text-error flex items-center space-x-1">
                      <Icon name="AlertCircle" size={16} />
                      <span>{errors.password}</span>
                    </p>
                  )}
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleForgotPassword}
                    className="text-sm text-primary hover:text-primary-700 transition-colors duration-150"
                  >
                    Құпия сөзді ұмыттыңыз ба?
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-primary text-white py-3 px-4 rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 font-medium hover-lift flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Кіруде...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="LogIn" size={20} />
                      <span>Кіру</span>
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Information Panel */}
          <div className="flex-1 bg-gradient-to-br from-primary to-secondary p-8 lg:p-12 text-white">
            <div className="h-full flex flex-col justify-center">
              <div className="mb-8">
                <h2 className="text-3xl font-heading font-bold mb-4">
                  Білім берудің болашағына қош келдіңіз
                </h2>
                <p className="text-lg opacity-90 mb-8">
                  Жасанды интеллект пен машиналық оқытуды қолдана отырып, білім беру деректерін талдауға арналған революциялық платформа
                </p>
              </div>

              <div className="space-y-6">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    <div className="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Icon name={feature.icon} size={24} color="white" />
                    </div>
                    <div>
                      <h3 className="font-heading font-semibold text-lg mb-2">{feature.title}</h3>
                      <p className="opacity-90 text-sm leading-relaxed">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;