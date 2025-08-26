import React, { useState, useEffect } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import AIChat from '../../components/ui/AIChat';
import Icon from '../../components/AppIcon';

import ProfileCard from './components/ProfileCard';
import ActivityTimeline from './components/ActivityTimeline';
import ProgressCharts from './components/ProgressCharts';
import WeeklyActivity from './components/WeeklyActivity';
import AIRecommendations from './components/AIRecommendations';
import LearningGoals from './components/LearningGoals';
import DetailedStats from './components/DetailedStats';

const StudentProfile = () => {
  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    return () => clearInterval(timer);
  }, []);

  const studentData = {
    id: 1,
    name: "Аружан Серікова",
    email: "aruzhan.serikova@edu.ru",
    studentId: "STU-2024-001",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
    course: "Информационные технологии",
    year: 3,
    group: "ИТ-21-1",
    gpa: 4.2,
    totalCredits: 180,
    completedCredits: 135,
    enrollmentDate: "01.09.2021",
    expectedGraduation: "30.06.2025",
    achievements: [
      { id: 1, title: "Семестр үздігі", date: "15.12.2023", icon: "Award" },
      { id: 2, title: "Үздік жоба", date: "20.11.2023", icon: "Trophy" },
      { id: 3, title: "Белсенді қатысушы", date: "05.10.2023", icon: "Star" }
    ],
    currentSemester: {
      number: 6,
      startDate: "01.09.2023",
      endDate: "31.01.2024",
      subjects: [
        { name: "Машиналық оқыту", grade: 4.5, credits: 6, progress: 85 },
        { name: "Дерекқорлар", grade: 4.8, credits: 5, progress: 92 },
        { name: "Веб-әзірлеу", grade: 4.2, credits: 4, progress: 78 },
        { name: "Алгоритмдер", grade: 4.6, credits: 5, progress: 88 },
        { name: "Ағылшын тілі", grade: 4.0, credits: 2, progress: 70 }
      ]
    }
  };

  const activityData = [
    {
      id: 1,
      type: "assignment",
      title: "ML бойынша зертханалық жұмыс тапсырылды",
      subject: "Машиналық оқыту",
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      grade: 4.5,
      icon: "FileCheck"
    },
    {
      id: 2,
      type: "lecture",
      title: "Дерекқорлар бойынша дәріске қатысты",
      subject: "Дерекқорлар",
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
      duration: 90,
      icon: "BookOpen"
    },
    {
      id: 3,
      type: "test",
      title: "Алгоритмдер бойынша тест өтті",
      subject: "Алгоритмдер",
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      score: 92,
      icon: "CheckCircle"
    },
    {
      id: 4,
      type: "project",
      title: "Веб-әзірлеу бойынша жобамен жұмыс басталды",
      subject: "Веб-әзірлеу",
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
      progress: 25,
      icon: "Code"
    }
  ];

  const weeklyStats = {
    totalHours: 28.5,
    completedTasks: 12,
    attendedLectures: 8,
    averageGrade: 4.4,
    engagementRating: 87,
    weeklyGoal: 30,
    dailyActivity: [
      { day: "Пн", hours: 4.5, tasks: 2 },
      { day: "Вт", hours: 3.2, tasks: 1 },
      { day: "Ср", hours: 5.1, tasks: 3 },
      { day: "Чт", hours: 4.8, tasks: 2 },
      { day: "Пт", hours: 6.2, tasks: 3 },
      { day: "Сб", hours: 2.8, tasks: 1 },
      { day: "Вс", hours: 1.9, tasks: 0 }
    ]
  };

  const aiRecommendations = [
    {
      id: 1,
      type: "improvement",
      title: "Ағылшын тілін жақсарту",
      description: `Нәтижелеріңізді талдау негізінде ағылшын тілін үйренуге көбірек көңіл бөлу ұсынылады. Тіл үйренуге арналған интерактивті қосымшаларды қолданып көріңіз.`,
      priority: "high",
      subject: "Ағылшын тілі",
      estimatedTime: "30 мин/күн",
      icon: "TrendingUp"
    },
    {
      id: 2,
      type: "strength",
      title: "Дерекқорлар бойынша үздік нәтиже",
      description: `Дерекқорлар бойынша көрсеткіштеріңіз керемет! Біліміңізді бекіту үшін бағдарламалау олимпиадасына қатысу мүмкіндігін қарастырыңыз.`,
      priority: "medium",
      subject: "Дерекқорлар",
      estimatedTime: "2 сағат/апта",
      icon: "Award"
    },
    {
      id: 3,
      type: "schedule",
      title: "Кестені оңтайландыру",
      description: `Талдау сіздің таңертеңгі уақытта өнімді екеніңізді көрсетеді. Күрделі тапсырмаларды 9:00-ден 12:00-ге дейін жоспарлау ұсынылады.`,
      priority: "low",
      subject: "Жалпы",
      estimatedTime: "Тұрақты",
      icon: "Clock"
    }
  ];

  const formatTime = (date) => {
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      
      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />
          
          {/* Welcome Section */}
          <div className="mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h1 className="text-3xl font-heading font-bold text-text-primary mb-2">
                  Қош келдіңіз, {studentData.name.split(' ')[0]}!
                </h1>
                <p className="text-text-secondary">
                  Бүгін {formatDate(currentTime)} • {formatTime(currentTime)}
                </p>
              </div>
              <div className="mt-4 lg:mt-0 flex items-center space-x-4">
                <div className="flex items-center space-x-2 bg-success-50 px-3 py-2 rounded-lg">
                  <Icon name="TrendingUp" size={16} className="text-success" />
                  <span className="text-sm font-medium text-success">
                    Орташа балл: {studentData.gpa}
                  </span>
                </div>
                <div className="flex items-center space-x-2 bg-primary-50 px-3 py-2 rounded-lg">
                  <Icon name="Target" size={16} className="text-primary" />
                  <span className="text-sm font-medium text-primary">
                    Прогресс: {Math.round((studentData.completedCredits / studentData.totalCredits) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column - Profile */}
            <div className="lg:col-span-4 space-y-6">
              <ProfileCard student={studentData} />
              <WeeklyActivity stats={weeklyStats} />
              <LearningGoals studentId={studentData.id} />
            </div>

            {/* Center Column - Activity & Progress */}
            <div className="lg:col-span-8 space-y-6">
              {/* Period Filter */}
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-text-primary">Период:</span>
                  <select
                    value={selectedPeriod}
                    onChange={(e) => setSelectedPeriod(e.target.value)}
                    className="px-3 py-1.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="day">Күн</option>
                    <option value="week">Апта</option>
                    <option value="month">Ай</option>
                    <option value="semester">Семестр</option>
                  </select>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-text-primary">Пән:</span>
                  <select
                    value={selectedSubject}
                    onChange={(e) => setSelectedSubject(e.target.value)}
                    className="px-3 py-1.5 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="all">Барлық пәндер</option>
                    {studentData.currentSemester.subjects.map((subject, index) => (
                      <option key={index} value={subject.name}>{subject.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <ActivityTimeline activities={activityData} />
              <ProgressCharts 
                subjects={studentData.currentSemester.subjects}
                selectedPeriod={selectedPeriod}
              />
              <AIRecommendations recommendations={aiRecommendations} studentId={studentData.id} />
            </div>
          </div>

          {/* Bottom Section - Detailed Statistics */}
          <div className="mt-8">
            <DetailedStats 
              student={studentData}
              selectedPeriod={selectedPeriod}
              selectedSubject={selectedSubject}
            />
          </div>
        </div>
      </main>

      <AIChat />
    </div>
  );
};

export default StudentProfile;