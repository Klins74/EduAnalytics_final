import React, { useState } from 'react';
import Icon from '../../components/AppIcon';
import Image from '../../components/AppImage';

const StudentActivityTable = ({ studentsData, onStudentClick }) => {
  const [sortBy, setSortBy] = useState('lastActivity');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const sortedStudents = [...studentsData].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];

    if (sortBy === 'lastActivity') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const paginatedStudents = sortedStudents.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(sortedStudents.length / itemsPerPage);

  const getEngagementColor = (status) => {
    const colors = {
      active: 'text-success bg-success-50',
      moderate: 'text-warning bg-warning-50',
      low: 'text-error bg-error-50'
    };
    return colors[status] || 'text-text-secondary bg-background';
  };

  const getEngagementLabel = (status) => {
    const labels = {
      active: 'Активный',
      moderate: 'Умеренный',
      low: 'Низкий'
    };
    return labels[status] || status;
  };

  const getRiskColor = (score) => {
    if (score < 0.3) return 'text-success bg-success-50';
    if (score < 0.7) return 'text-warning bg-warning-50';
    return 'text-error bg-error-50';
  };

  const getRiskLabel = (score) => {
    if (score < 0.3) return 'Низкий';
    if (score < 0.7) return 'Средний';
    return 'Высокий';
  };

  const formatLastActivity = (date) => {
    const now = new Date();
    const diff = now - new Date(date);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return 'Только что';
    if (minutes < 60) return `${minutes} мин назад`;
    if (hours < 24) return `${hours} ч назад`;
    return `${days} дн назад`;
  };

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <div className="p-6 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-heading font-medium text-text-primary mb-1">
              Список студентов
            </h3>
            <p className="text-sm text-text-secondary">
              {sortedStudents.length} студентов найдено
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-background transition-colors duration-150">
              <Icon name="Download" size={14} className="mr-1" />
              Экспорт
            </button>
            <button className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary-700 transition-colors duration-150 hover-lift">
              <Icon name="Plus" size={14} className="mr-1" />
              Добавить
            </button>
          </div>
        </div>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-background">
            <tr>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-primary hover:text-primary transition-colors duration-150"
                >
                  <span>Студент</span>
                  <Icon name="ArrowUpDown" size={14} />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <span className="text-sm font-medium text-text-primary">Группа</span>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('lastActivity')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-primary hover:text-primary transition-colors duration-150"
                >
                  <span>Последняя активность</span>
                  <Icon name="ArrowUpDown" size={14} />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('engagementStatus')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-primary hover:text-primary transition-colors duration-150"
                >
                  <span>Вовлеченность</span>
                  <Icon name="ArrowUpDown" size={14} />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('aiRiskScore')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-primary hover:text-primary transition-colors duration-150"
                >
                  <span>AI-риск</span>
                  <Icon name="ArrowUpDown" size={14} />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('averageScore')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-primary hover:text-primary transition-colors duration-150"
                >
                  <span>Средний балл</span>
                  <Icon name="ArrowUpDown" size={14} />
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <span className="text-sm font-medium text-text-primary">Действия</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {paginatedStudents.map((student) => (
              <tr
                key={student.id}
                className="hover:bg-background transition-colors duration-150 cursor-pointer"
                onClick={() => onStudentClick(student)}
              >
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <Image
                        src={student.avatar}
                        alt={student.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                      {student.engagementStatus === 'active' && (
                        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-success border-2 border-surface rounded-full" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-text-primary">{student.name}</p>
                      <p className="text-sm text-text-secondary">{student.totalActivities} активностей</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-text-primary">{student.group}</span>
                </td>
                <td className="px-6 py-4">
                  <span className="text-sm text-text-primary">
                    {formatLastActivity(student.lastActivity)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEngagementColor(student.engagementStatus)}`}>
                    {getEngagementLabel(student.engagementStatus)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(student.aiRiskScore)}`}>
                    {getRiskLabel(student.aiRiskScore)}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-text-primary">
                      {student.averageScore.toFixed(1)}
                    </span>
                    <div className="w-16 h-2 bg-background rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-300"
                        style={{ width: `${(student.averageScore / 5) * 100}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onStudentClick(student);
                      }}
                      className="p-1.5 hover:bg-primary-50 rounded-lg transition-colors duration-150"
                    >
                      <Icon name="Eye" size={14} className="text-primary" />
                    </button>
                    <button
                      onClick={(e) => e.stopPropagation()}
                      className="p-1.5 hover:bg-background rounded-lg transition-colors duration-150"
                    >
                      <Icon name="MoreHorizontal" size={14} className="text-text-secondary" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden divide-y divide-border">
        {paginatedStudents.map((student) => (
          <div
            key={student.id}
            className="p-4 hover:bg-background transition-colors duration-150 cursor-pointer"
            onClick={() => onStudentClick(student)}
          >
            <div className="flex items-center space-x-3 mb-3">
              <div className="relative">
                <Image
                  src={student.avatar}
                  alt={student.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                {student.engagementStatus === 'active' && (
                  <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-success border-2 border-surface rounded-full" />
                )}
              </div>
              <div className="flex-1">
                <h4 className="font-medium text-text-primary">{student.name}</h4>
                <p className="text-sm text-text-secondary">{student.group}</p>
              </div>
              <button
                onClick={(e) => e.stopPropagation()}
                className="p-2 hover:bg-background rounded-lg transition-colors duration-150"
              >
                <Icon name="MoreVertical" size={16} className="text-text-secondary" />
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-text-secondary">Активность:</span>
                <p className="text-text-primary">{formatLastActivity(student.lastActivity)}</p>
              </div>
              <div>
                <span className="text-text-secondary">Средний балл:</span>
                <p className="text-text-primary font-medium">{student.averageScore.toFixed(1)}</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getEngagementColor(student.engagementStatus)}`}>
                {getEngagementLabel(student.engagementStatus)}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskColor(student.aiRiskScore)}`}>
                AI: {getRiskLabel(student.aiRiskScore)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-border">
          <div className="flex items-center justify-between">
            <p className="text-sm text-text-secondary">
              Показано {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, sortedStudents.length)} из {sortedStudents.length}
            </p>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
              >
                <Icon name="ChevronLeft" size={14} />
              </button>
              
              <div className="flex items-center space-x-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-1.5 text-sm rounded-lg transition-colors duration-150 ${
                        currentPage === page
                          ? 'bg-primary text-white' :'hover:bg-background text-text-primary'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
              >
                <Icon name="ChevronRight" size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudentActivityTable;