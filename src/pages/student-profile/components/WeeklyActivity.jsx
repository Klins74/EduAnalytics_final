import React from 'react';
import Icon from '../../../components/AppIcon';

const WeeklyActivity = ({ stats }) => {
  const progressPercentage = Math.round((stats.totalHours / stats.weeklyGoal) * 100);

  return (
    <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-heading font-semibold text-text-primary">
          Активность за неделю
        </h3>
        <Icon name="Calendar" size={16} className="text-text-secondary" />
      </div>

      {/* Weekly Goal Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-text-primary">Недельная цель</span>
          <span className="text-sm text-text-secondary">
            {stats.totalHours} / {stats.weeklyGoal} часов
          </span>
        </div>
        <div className="w-full bg-border-light rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              progressPercentage >= 100 ? 'bg-success' : 'bg-primary'
            }`}
            style={{ width: `${Math.min(progressPercentage, 100)}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-text-muted">{progressPercentage}% выполнено</span>
          {progressPercentage >= 100 && (
            <span className="text-xs text-success font-medium">Цель достигнута!</span>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <Icon name="CheckCircle" size={20} className="text-primary" />
          </div>
          <div className="text-2xl font-bold text-text-primary">{stats.completedTasks}</div>
          <div className="text-xs text-text-secondary">Выполнено заданий</div>
        </div>
        
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-success-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <Icon name="BookOpen" size={20} className="text-success" />
          </div>
          <div className="text-2xl font-bold text-text-primary">{stats.attendedLectures}</div>
          <div className="text-xs text-text-secondary">Посещено лекций</div>
        </div>
        
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-accent-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <Icon name="Star" size={20} className="text-accent" />
          </div>
          <div className="text-2xl font-bold text-text-primary">{stats.averageGrade}</div>
          <div className="text-xs text-text-secondary">Средний балл</div>
        </div>
        
        <div className="bg-background rounded-lg p-4 text-center">
          <div className="w-10 h-10 bg-secondary-50 rounded-full flex items-center justify-center mx-auto mb-2">
            <Icon name="TrendingUp" size={20} className="text-secondary" />
          </div>
          <div className="text-2xl font-bold text-text-primary">{stats.engagementRating}%</div>
          <div className="text-xs text-text-secondary">Вовлеченность</div>
        </div>
      </div>

      {/* Daily Activity */}
      <div>
        <h4 className="text-sm font-medium text-text-primary mb-3">Активность по дням</h4>
        <div className="space-y-2">
          {stats.dailyActivity.map((day, index) => (
            <div key={index} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-sm font-medium text-text-primary w-8">{day.day}</span>
                <div className="flex-1 bg-border-light rounded-full h-1.5 w-20">
                  <div 
                    className="bg-primary h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${(day.hours / 8) * 100}%` }}
                  />
                </div>
              </div>
              <div className="flex items-center space-x-4 text-xs text-text-secondary">
                <span>{day.hours}ч</span>
                <span>{day.tasks} заданий</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default WeeklyActivity;