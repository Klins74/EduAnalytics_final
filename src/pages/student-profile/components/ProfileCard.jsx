import React from 'react';
import Icon from '../../../components/AppIcon';
import Image from '../../../components/AppImage';

const ProfileCard = ({ student }) => {
  const progressPercentage = Math.round((student.completedCredits / student.totalCredits) * 100);

  return (
    <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
      <div className="text-center mb-6">
        <div className="relative inline-block">
          <Image
            src={student.avatar}
            alt={student.name}
            className="w-24 h-24 rounded-full object-cover border-4 border-primary-100"
          />
          <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-success rounded-full border-4 border-surface flex items-center justify-center">
            <Icon name="CheckCircle" size={16} color="white" />
          </div>
        </div>
        <h2 className="text-xl font-heading font-semibold text-text-primary mt-4 mb-1">
          {student.name}
        </h2>
        <p className="text-text-secondary text-sm">{student.studentId}</p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between py-2 border-b border-border-light">
          <span className="text-sm text-text-secondary">Курс</span>
          <span className="text-sm font-medium text-text-primary">{student.course}</span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-border-light">
          <span className="text-sm text-text-secondary">Год обучения</span>
          <span className="text-sm font-medium text-text-primary">{student.year} курс</span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-border-light">
          <span className="text-sm text-text-secondary">Группа</span>
          <span className="text-sm font-medium text-text-primary">{student.group}</span>
        </div>
        
        <div className="flex items-center justify-between py-2 border-b border-border-light">
          <span className="text-sm text-text-secondary">Средний балл</span>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-text-primary">{student.gpa}</span>
            <div className="w-2 h-2 bg-success rounded-full" />
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-text-primary">Прогресс обучения</span>
          <span className="text-sm text-text-secondary">{progressPercentage}%</span>
        </div>
        <div className="w-full bg-border-light rounded-full h-2">
          <div 
            className="bg-gradient-to-r from-primary to-primary-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-text-muted">
          <span>{student.completedCredits} из {student.totalCredits} кредитов</span>
          <span>До выпуска: {student.expectedGraduation}</span>
        </div>
      </div>

      {/* Achievements */}
      <div className="mt-6">
        <h3 className="text-sm font-medium text-text-primary mb-3">Последние достижения</h3>
        <div className="space-y-2">
          {student.achievements.slice(0, 3).map((achievement) => (
            <div key={achievement.id} className="flex items-center space-x-3 p-2 bg-background rounded-lg">
              <div className="w-8 h-8 bg-accent-50 rounded-full flex items-center justify-center">
                <Icon name={achievement.icon} size={14} className="text-accent" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-text-primary">{achievement.title}</p>
                <p className="text-xs text-text-muted">{achievement.date}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Contact Info */}
      <div className="mt-6 pt-4 border-t border-border">
        <div className="flex items-center space-x-2 text-sm text-text-secondary">
          <Icon name="Mail" size={14} />
          <span>{student.email}</span>
        </div>
      </div>
    </div>
  );
};

export default ProfileCard;