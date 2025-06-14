import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';

const LearningGoals = ({ studentId }) => {
  const [goals, setGoals] = useState([
    {
      id: 1,
      title: "Повысить средний балл до 4.5",
      description: "Улучшить успеваемость по всем предметам",
      targetValue: 4.5,
      currentValue: 4.2,
      unit: "балл",
      deadline: "31.01.2024",
      category: "academic",
      priority: "high",
      progress: 84,
      isCompleted: false
    },
    {
      id: 2,
      title: "Изучить React на продвинутом уровне",
      description: "Освоить хуки, контекст и продвинутые паттерны",
      targetValue: 100,
      currentValue: 65,
      unit: "%",
      deadline: "15.02.2024",
      category: "skill",
      priority: "medium",
      progress: 65,
      isCompleted: false
    },
    {
      id: 3,
      title: "Посетить все лекции в семестре",
      description: "100% посещаемость лекций",
      targetValue: 48,
      currentValue: 42,
      unit: "лекций",
      deadline: "31.01.2024",
      category: "attendance",
      priority: "low",
      progress: 87.5,
      isCompleted: false
    }
  ]);

  const [showAddGoal, setShowAddGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    targetValue: '',
    deadline: '',
    category: 'academic',
    priority: 'medium'
  });

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'academic':
        return 'GraduationCap';
      case 'skill':
        return 'Code';
      case 'attendance':
        return 'Calendar';
      default:
        return 'Target';
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'academic':
        return 'bg-primary-50 text-primary';
      case 'skill':
        return 'bg-secondary-50 text-secondary';
      case 'attendance':
        return 'bg-success-50 text-success';
      default:
        return 'bg-background text-text-secondary';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'border-l-error';
      case 'medium':
        return 'border-l-warning';
      case 'low':
        return 'border-l-success';
      default:
        return 'border-l-border';
    }
  };

  const handleAddGoal = (e) => {
    e.preventDefault();
    if (!newGoal.title || !newGoal.targetValue || !newGoal.deadline) return;

    const goal = {
      id: Date.now(),
      ...newGoal,
      currentValue: 0,
      unit: newGoal.category === 'academic' ? 'балл' : '%',
      progress: 0,
      isCompleted: false
    };

    setGoals([...goals, goal]);
    setNewGoal({
      title: '',
      description: '',
      targetValue: '',
      deadline: '',
      category: 'academic',
      priority: 'medium'
    });
    setShowAddGoal(false);
  };

  const toggleGoalComplete = (goalId) => {
    setGoals(goals.map(goal => 
      goal.id === goalId 
        ? { ...goal, isCompleted: !goal.isCompleted, progress: goal.isCompleted ? goal.progress : 100 }
        : goal
    ));
  };

  const deleteGoal = (goalId) => {
    setGoals(goals.filter(goal => goal.id !== goalId));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString.split('.').reverse().join('-'));
    const now = new Date();
    const diffTime = date - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'Просрочено';
    if (diffDays === 0) return 'Сегодня';
    if (diffDays === 1) return 'Завтра';
    return `${diffDays} дней`;
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6 shadow-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-heading font-semibold text-text-primary">
          Цели обучения
        </h3>
        <button
          onClick={() => setShowAddGoal(!showAddGoal)}
          className="p-2 hover:bg-background rounded-lg transition-colors duration-150 hover-lift"
        >
          <Icon name="Plus" size={16} className="text-primary" />
        </button>
      </div>

      {/* Add Goal Form */}
      {showAddGoal && (
        <div className="mb-6 p-4 bg-background rounded-lg border border-border">
          <form onSubmit={handleAddGoal} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Название цели"
                value={newGoal.title}
                onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                required
              />
            </div>
            <div>
              <textarea
                placeholder="Описание цели"
                value={newGoal.description}
                onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                rows="2"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <select
                  value={newGoal.category}
                  onChange={(e) => setNewGoal({ ...newGoal, category: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="academic">Академическая</option>
                  <option value="skill">Навыки</option>
                  <option value="attendance">Посещаемость</option>
                </select>
              </div>
              <div>
                <select
                  value={newGoal.priority}
                  onChange={(e) => setNewGoal({ ...newGoal, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="low">Низкий</option>
                  <option value="medium">Средний</option>
                  <option value="high">Высокий</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <input
                  type="number"
                  placeholder="Целевое значение"
                  value={newGoal.targetValue}
                  onChange={(e) => setNewGoal({ ...newGoal, targetValue: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  required
                />
              </div>
              <div>
                <input
                  type="date"
                  value={newGoal.deadline}
                  onChange={(e) => setNewGoal({ ...newGoal, deadline: e.target.value })}
                  className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  required
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="submit"
                className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary-700 transition-colors duration-150 hover-lift"
              >
                Добавить цель
              </button>
              <button
                type="button"
                onClick={() => setShowAddGoal(false)}
                className="px-4 py-2 bg-background text-text-secondary rounded-lg text-sm hover:bg-border-light transition-colors duration-150"
              >
                Отмена
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Goals List */}
      <div className="space-y-4">
        {goals.map((goal) => (
          <div
            key={goal.id}
            className={`border-l-4 ${getPriorityColor(goal.priority)} bg-background rounded-lg p-4 ${
              goal.isCompleted ? 'opacity-75' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start space-x-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${getCategoryColor(goal.category)}`}>
                  <Icon name={getCategoryIcon(goal.category)} size={14} />
                </div>
                <div className="flex-1">
                  <h4 className={`text-sm font-medium ${goal.isCompleted ? 'line-through text-text-muted' : 'text-text-primary'}`}>
                    {goal.title}
                  </h4>
                  <p className="text-xs text-text-secondary mt-1">{goal.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => toggleGoalComplete(goal.id)}
                  className={`p-1 rounded transition-colors duration-150 ${
                    goal.isCompleted 
                      ? 'text-success hover:bg-success-50' :'text-text-muted hover:bg-background'
                  }`}
                >
                  <Icon name={goal.isCompleted ? "CheckCircle" : "Circle"} size={14} />
                </button>
                <button
                  onClick={() => deleteGoal(goal.id)}
                  className="p-1 text-text-muted hover:text-error hover:bg-error-50 rounded transition-colors duration-150"
                >
                  <Icon name="Trash2" size={14} />
                </button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-secondary">
                  {goal.currentValue} / {goal.targetValue} {goal.unit}
                </span>
                <span className="text-xs text-text-secondary">{Math.round(goal.progress)}%</span>
              </div>
              <div className="w-full bg-border-light rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    goal.isCompleted ? 'bg-success' : 'bg-primary'
                  }`}
                  style={{ width: `${Math.min(goal.progress, 100)}%` }}
                />
              </div>
            </div>

            {/* Deadline */}
            <div className="flex items-center justify-between text-xs">
              <span className="text-text-muted">
                Срок: {goal.deadline}
              </span>
              <span className={`font-medium ${
                formatDate(goal.deadline) === 'Просрочено' ? 'text-error' :
                formatDate(goal.deadline) === 'Сегодня' || formatDate(goal.deadline) === 'Завтра' ? 'text-warning' :
                'text-text-secondary'
              }`}>
                {formatDate(goal.deadline)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {goals.length === 0 && (
        <div className="text-center py-8">
          <Icon name="Target" size={48} className="text-text-muted mx-auto mb-4" />
          <p className="text-text-secondary">Пока нет целей обучения</p>
          <p className="text-xs text-text-muted mt-1">Добавьте цель, чтобы отслеживать прогресс</p>
        </div>
      )}
    </div>
  );
};

export default LearningGoals;