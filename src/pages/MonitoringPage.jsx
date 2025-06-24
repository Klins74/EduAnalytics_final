// src/pages/MonitoringPage.jsx

import React, { useState, useEffect, useMemo } from 'react';

// ИСПОЛЬЗУЕМ АБСОЛЮТНЫЕ ПУТИ ОТ ПАПКИ SRC
import { motion, AnimatePresence } from 'framer-motion';
import Header from 'components/ui/Header';
import Sidebar from 'components/ui/Sidebar';
import Breadcrumb from 'components/ui/Breadcrumb';
import FilterPanel from 'pages/components/FilterPanel';
import StudentActivityTable from 'pages/components/StudentActivityTable';
import StudentDetailModal from 'pages/components/StudentDetailModal';
import { getStudentsData } from 'api/mockApi.js'; 

const MonitoringPage = () => {
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
  const fetchData = async () => {
    setIsLoading(true);
    try { // Пытаемся выполнить код
      const students = await getStudentsData();
      setAllStudents(students || []); // Если все хорошо, сохраняем студентов
    } catch (error) { // Если произошла ошибка
      console.error("Ошибка при загрузке студентов:", error);
      setAllStudents([]); // В случае ошибки ставим пустой массив, чтобы не было сбоя
    } finally { // Этот блок выполнится в любом случае (успех или ошибка)
      setIsLoading(false); // Гарантированно убираем загрузку
    }
  };
  fetchData();
}, []); // Пустой массив [] означает, что код выполнится только один раз при загрузке страницы
  const filteredStudents = useMemo(() => {
    if (isLoading) return [];
    return allStudents.filter(student => {
      const groupMatch = filters.group === 'all' || student.group === filters.group;
      const subjectMatch = filters.subject === 'all' || student.subjects.includes(filters.subject);
      const engagementMatch = filters.engagementStatus === 'all' || student.engagementStatus === filters.engagementStatus;
      
      return groupMatch && subjectMatch && engagementMatch;
    });
  }, [filters, allStudents, isLoading]);

  console.log("--- ДЕБАГ-ИНФОРМАЦИЯ ---");
  console.log("Состояние isLoading:", isLoading);
  console.log("Фильтры, которые используются:", filters);
  console.log("Полученные студенты (allStudents):", allStudents);
  console.log("Отфильтрованные студенты (filteredStudents):", filteredStudents);
  console.log("--- КОНЕЦ ДЕБАГ-ИНФОРМАЦИИ ---");
  
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