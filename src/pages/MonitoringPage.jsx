// src/pages/MonitoringPage.jsx

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom'; // Импортируем useNavigate
import { motion, AnimatePresence } from 'framer-motion';
import Header from 'components/ui/Header';
import Sidebar from 'components/ui/Sidebar';
import Breadcrumb from 'components/ui/Breadcrumb';
import FilterPanel from 'pages/components/FilterPanel';
import StudentActivityTable from 'pages/components/StudentActivityTable';
import StudentDetailModal from 'pages/components/StudentDetailModal';

const MonitoringPage = () => {
  const navigate = useNavigate(); // Инициализируем useNavigate
  const [isLoading, setIsLoading] = useState(true);
  const [allStudents, setAllStudents] = useState([]);

  const [filters, setFilters] = useState({
    group: 'all',
    subject: 'all',
    timeRange: 'today',
    activityType: 'all',
    engagementStatus: 'all'
  });

  const [selectedStudent, setSelectedStudent] = useState(null);

  useEffect(() => {
    // --- НОВАЯ ЛОГИКА ЗАГРУЗКИ ДАННЫХ С СЕРВЕРА ---
    const fetchStudentsData = async () => {
      setIsLoading(true);
      const token = localStorage.getItem('accessToken');
      if (!token) {
        navigate('/login');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/students', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.status === 401) {
          navigate('/login');
          return;
        }

        if (!response.ok) {
          throw new Error('Не удалось загрузить список студентов');
        }

        const data = await response.json();
        setAllStudents(data);
      } catch (error) {
        console.error("Ошибка при загрузке студентов:", error);
        setAllStudents([]);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchStudentsData();
  }, [navigate]); // Добавляем navigate в зависимости

  const filteredStudents = useMemo(() => {
    if (isLoading) return [];
    return allStudents.filter(student => {
      const groupMatch = filters.group === 'all' || student.group === filters.group;
      const subjectMatch = filters.subject === 'all' || student.subjects.includes(filters.subject);
      const engagementMatch = filters.engagementStatus === 'all' || student.engagementStatus === filters.engagementStatus;
      
      return groupMatch && subjectMatch && engagementMatch;
    });
  }, [filters, allStudents, isLoading]);
  
  // Компонент-заглушка на время загрузки
  if (isLoading) {
    return (
        <div className="min-h-screen bg-background">
            <Header />
            <Sidebar />
            <main className="pt-16 lg:ml-60">
                <div className="p-6">Загрузка данных о студентах...</div>
            </main>
        </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <Sidebar />
      <main className="pt-16 lg:ml-60 transition-all duration-300">
        <div className="p-6">
          <Breadcrumb />
          <div className="mb-6">
            <h1 className="text-3xl font-heading font-semibold text-text-primary">
              Мониторинг студентов
            </h1>
            <p className="text-text-secondary mt-2">
              Анализируйте активность и успеваемость студентов в реальном времени.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1">
              <FilterPanel 
                filters={filters} 
                onFilterChange={setFilters} 
                studentsData={allStudents}
              />
            </div>

            <div className="lg:col-span-3">
              <StudentActivityTable 
                studentsData={filteredStudents} 
                onStudentClick={setSelectedStudent} 
              />
            </div>
          </div>
        </div>
      </main>
      
      <AnimatePresence>
        {selectedStudent && (
          <StudentDetailModal 
            student={selectedStudent} 
            onClose={() => setSelectedStudent(null)} 
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default MonitoringPage;