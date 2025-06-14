import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../../components/AppIcon';


const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Mock credentials for different user types
  const mockCredentials = {
    admin: { email: 'admin@eduanalytics.ru', password: 'admin123', role: 'Администратор' },
    teacher: { email: 'teacher@eduanalytics.ru', password: 'teacher123', role: 'Преподаватель' },
    student: { email: 'student@eduanalytics.ru', password: 'student123', role: 'Студент' }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Введите email адрес';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Введите корректный email адрес';
    }

    if (!formData.password) {
      newErrors.password = 'Введите пароль';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
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

    // Clear error when user starts typing
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

    // Simulate API call
    setTimeout(() => {
      // Check mock credentials
      const validCredential = Object.values(mockCredentials).find(
        cred => cred.email === formData.email && cred.password === formData.password
      );

      if (validCredential) {
        // Successful login
        localStorage.setItem('user', JSON.stringify({
          email: formData.email,
          role: validCredential.role
        }));
        navigate('/');
      } else {
        // Invalid credentials
        setErrors({
          general: 'Неверный email или пароль. Используйте тестовые данные: admin@eduanalytics.ru / admin123'
        });
      }
      
      setIsLoading(false);
    }, 1500);
  };

  const handleForgotPassword = () => {
    alert('Функция восстановления пароля будет доступна в полной версии системы');
  };

  const handleExternalLogin = (provider) => {
    alert(`Вход через ${provider} будет доступен в полной версии системы`);
  };

  const features = [
    {
      icon: 'BarChart3',
      title: 'Аналитика в реальном времени',
      description: 'Отслеживайте активность студентов и анализируйте образовательные данные в режиме реального времени'
    },
    {
      icon: 'Bot',
      title: 'AI-помощник',
      description: 'Интеллектуальный анализ данных с помощью искусственного интеллекта и машинного обучения'
    },
    {
      icon: 'Users',
      title: 'Мониторинг студентов',
      description: 'Комплексное отслеживание успеваемости и вовлеченности учащихся в образовательный процесс'
    },
    {
      icon: 'TrendingUp',
      title: 'Прогнозная аналитика',
      description: 'Предсказание образовательных результатов на основе анализа поведенческих паттернов'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl bg-surface rounded-2xl shadow-elevated overflow-hidden">
        <div className="flex flex-col lg:flex-row min-h-[600px]">
          {/* Login Form Section */}
          <div className="flex-1 flex items-center justify-center p-8 lg:p-12">
            <div className="w-full max-w-md">
              {/* Logo and Title */}
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Icon name="GraduationCap" size={32} color="white" />
                </div>
                <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">
                  EduAnalytics AI
                </h1>
                <p className="text-text-secondary">
                  Интеллектуальная система образовательной аналитики
                </p>
              </div>

              {/* Login Form */}
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* General Error */}
                {errors.general && (
                  <div className="bg-error-50 border border-error-100 rounded-lg p-4 flex items-start space-x-3">
                    <Icon name="AlertCircle" size={20} className="text-error flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-error font-medium">Ошибка входа</p>
                      <p className="text-sm text-error mt-1">{errors.general}</p>
                    </div>
                  </div>
                )}

                {/* Email Field */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                    Email адрес
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
                      placeholder="Введите ваш email"
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

                {/* Password Field */}
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                    Пароль
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
                      placeholder="Введите ваш пароль"
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

                {/* Forgot Password */}
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleForgotPassword}
                    className="text-sm text-primary hover:text-primary-700 transition-colors duration-150"
                  >
                    Забыли пароль?
                  </button>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-primary text-white py-3 px-4 rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-150 font-medium hover-lift flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Вход в систему...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="LogIn" size={20} />
                      <span>Войти</span>
                    </>
                  )}
                </button>

                {/* External Login Options */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-surface text-text-secondary">или войдите через</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => handleExternalLogin('Google')}
                    className="flex items-center justify-center px-4 py-2 border border-border rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
                  >
                    <Icon name="Chrome" size={20} className="text-text-secondary" />
                    <span className="ml-2 text-sm text-text-primary">Google</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleExternalLogin('Microsoft')}
                    className="flex items-center justify-center px-4 py-2 border border-border rounded-lg hover:bg-background transition-colors duration-150 hover-lift"
                  >
                    <Icon name="Square" size={20} className="text-text-secondary" />
                    <span className="ml-2 text-sm text-text-primary">Microsoft</span>
                  </button>
                </div>

                {/* Test Credentials Info */}
                <div className="bg-primary-50 border border-primary-100 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <Icon name="Info" size={20} className="text-primary flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-primary font-medium mb-2">Тестовые данные для входа:</p>
                      <div className="space-y-1 text-xs text-primary">
                        <p><strong>Администратор:</strong> admin@eduanalytics.ru / admin123</p>
                        <p><strong>Преподаватель:</strong> teacher@eduanalytics.ru / teacher123</p>
                        <p><strong>Студент:</strong> student@eduanalytics.ru / student123</p>
                      </div>
                    </div>
                  </div>
                </div>
              </form>
            </div>
          </div>

          {/* Information Panel */}
          <div className="flex-1 bg-gradient-to-br from-primary to-secondary p-8 lg:p-12 text-white">
            <div className="h-full flex flex-col justify-center">
              <div className="mb-8">
                <h2 className="text-3xl font-heading font-bold mb-4">
                  Добро пожаловать в будущее образования
                </h2>
                <p className="text-lg opacity-90 mb-8">
                  Революционная платформа для анализа образовательных данных с использованием искусственного интеллекта и машинного обучения
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

              <div className="mt-12 pt-8 border-t border-white border-opacity-20">
                <div className="flex items-center space-x-4">
                  <div className="flex -space-x-2">
                    <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full border-2 border-white" />
                    <div className="w-8 h-8 bg-white bg-opacity-30 rounded-full border-2 border-white" />
                    <div className="w-8 h-8 bg-white bg-opacity-40 rounded-full border-2 border-white" />
                  </div>
                  <div>
                    <p className="font-medium">Более 10,000+ пользователей</p>
                    <p className="text-sm opacity-75">доверяют нашей платформе</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;