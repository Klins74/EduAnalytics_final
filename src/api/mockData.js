// src/api/mockData.js

export const kpiData = [
  { id: 'students', title: 'Всего студентов', value: '2,847', change: '+12%', changeType: 'positive', icon: 'Users', color: 'primary', description: 'Активных студентов в системе' },
  { id: 'activity', title: 'Активность', value: '89.2%', change: '+5.3%', changeType: 'positive', icon: 'Activity', color: 'success', description: 'Средняя активность за неделю' },
  { id: 'performance', title: 'Успеваемость', value: '4.2', change: '+0.3', changeType: 'positive', icon: 'TrendingUp', color: 'accent', description: 'Средний балл по системе' },
  { id: 'alerts', title: 'Предупреждения', value: '23', change: '-8', changeType: 'negative', icon: 'AlertTriangle', color: 'warning', description: 'Требуют внимания' }
];

export const activityData = [
  { date: '01.12', students: 2340, sessions: 4200, engagement: 85 }, { date: '02.12', students: 2456, sessions: 4350, engagement: 87 }, { date: '03.12', students: 2398, sessions: 4180, engagement: 82 },
  { date: '04.12', students: 2567, sessions: 4520, engagement: 89 }, { date: '05.12', students: 2634, sessions: 4680, engagement: 91 }, { date: '06.12', students: 2589, sessions: 4590, engagement: 88 },
  { date: '07.12', students: 2847, sessions: 4920, engagement: 92 }
];

export const studentsData = [
    { id: 1, name: 'Мәриәм Сұлтанова', avatar: 'https://i.pravatar.cc/150?img=1', group: 'ИТ-21-1', totalActivities: 48, lastActivity: new Date(Date.now() - 3600000), engagementStatus: 'active', aiRiskScore: 0.2, averageScore: 4.5, subjects: ['Математика', 'Физика', 'Программирование'], weeklyActivity: [5, 6, 7, 5, 8, 2, 1], recentActivities: [{type: 'test', subject: 'Математика', score: 90, time: new Date(Date.now() - 3600000)}, {type: 'homework', subject: 'Программирование', score: 95, time: new Date(Date.now() - 86400000)}] },
    { id: 2, name: 'Қаржаубаева Аружан', avatar: 'https://i.pravatar.cc/150?img=2', group: 'ИТ-21-2', totalActivities: 32, lastActivity: new Date(Date.now() - 90000000), engagementStatus: 'moderate', aiRiskScore: 0.5, averageScore: 3.8, subjects: ['Химия', 'Биология', 'Ағылшын тілі'], weeklyActivity: [4, 4, 5, 6, 3, 0, 0], recentActivities: [{type: 'homework', subject: 'Ағылшын тілі', score: 80, time: new Date(Date.now() - 90000000)}, {type: 'quiz', subject: 'Химия', score: 72, time: new Date(Date.now() - 172800000)}] },
    { id: 3, name: 'Қуанышев Асылхан', avatar: 'https://i.pravatar.cc/150?img=3', group: 'ИТ-21-1', totalActivities: 15, lastActivity: new Date(Date.now() - 260000000), engagementStatus: 'low', aiRiskScore: 0.8, averageScore: 3.1, subjects: ['Математика', 'Тарих', 'Дерекқорлар'], weeklyActivity: [2, 1, 3, 2, 1, 0, 0], recentActivities: [{type: 'test', subject: 'Тарих', score: 65, time: new Date(Date.now() - 260000000)}]  },
    { id: 4, name: 'Имаш Тимур', avatar: 'https://i.pravatar.cc/150?img=4', group: 'ФМ-20-1', totalActivities: 55, lastActivity: new Date(Date.now() - 1800000), engagementStatus: 'active', aiRiskScore: 0.1, averageScore: 4.8, subjects: ['Физика', 'Жоғары математика'], weeklyActivity: [8, 7, 8, 9, 6, 3, 2], recentActivities: [{type: 'test', subject: 'Жоғары математика', score: 98, time: new Date(Date.now() - 1800000)}] },
    { id: 5, name: 'Нуралнова Алия', avatar: 'https://i.pravatar.cc/150?img=5', group: 'ИТ-21-2', totalActivities: 28, lastActivity: new Date(Date.now() - 180000000), engagementStatus: 'moderate', aiRiskScore: 0.4, averageScore: 4.0, subjects: ['Программирование', 'Ағылшын тілі'], weeklyActivity: [3, 4, 3, 5, 4, 1, 1], recentActivities: [{type: 'homework', subject: 'Программирование', score: 85, time: new Date(Date.now() - 180000000)}]  },
    { id: 6, name: 'Муканова Айгерім', avatar: 'https://i.pravatar.cc/150?img=6', group: 'ФМ-20-1', totalActivities: 21, lastActivity: new Date(Date.now() - 432000000), engagementStatus: 'low', aiRiskScore: 0.7, averageScore: 3.4, subjects: ['Физика', 'Ықтималдықтар теориясы'], weeklyActivity: [1, 2, 2, 1, 3, 0, 0], recentActivities: [{type: 'quiz', subject: 'Ықтималдықтар теориясы', score: 55, time: new Date(Date.now() - 432000000)}] },
];

export const performanceData = [
    { subject: 'Математика', average: 4.2, students: 156, trend: 0.3 }, { subject: 'Физика', average: 3.8, students: 142, trend: -0.1 },
    { subject: 'Химия', average: 4.0, students: 134, trend: 0.2 }, { subject: 'Биология', average: 4.3, students: 148, trend: 0.4 },
    { subject: 'Тарих', average: 3.9, students: 167, trend: 0.1 }, { subject: 'Әдебиет', average: 4.1, students: 159, trend: 0.2 }
];

export const gradeDistribution = [
    { grade: '5', count: 245, percentage: 32.1 }, { grade: '4', count: 298, percentage: 39.0 },
    { grade: '3', count: 187, percentage: 24.5 }, { grade: '2', count: 34, percentage: 4.4 }
];

export const trendData = [
    { month: 'Қыр', performance: 3.7 }, { month: 'Қаз', performance: 3.8 }, { month: 'Қар', performance: 3.9 },
    { month: 'Жел', performance: 4.0 }, { month: 'Қаң', performance: 4.1 }, { month: 'Ақп', performance: 4.0 },
    { month: 'Нау', performance: 4.2 }
];

export const engagementData = [
    { day: 'Дс', online: 85, offline: 78, participation: 82 }, { day: 'Сс', online: 88, offline: 82, participation: 85 },
    { day: 'Ср', online: 92, offline: 85, participation: 88 }, { day: 'Бс', online: 87, offline: 80, participation: 84 },
    { day: 'Жм', online: 83, offline: 76, participation: 79 }, { day: 'Сб', online: 45, offline: 35, participation: 40 },
    { day: 'Жс', online: 32, offline: 28, participation: 30 }
];

export const activityHeatmap = [
    { hour: '08:00', Mon: 45, Tue: 52, Wed: 48, Thu: 51, Fri: 46, Sat: 12, Sun: 8 }, { hour: '09:00', Mon: 78, Tue: 82, Wed: 85, Thu: 79, Fri: 76, Sat: 25, Sun: 15 },
    { hour: '10:00', Mon: 92, Tue: 95, Wed: 98, Thu: 94, Fri: 89, Sat: 35, Sun: 22 }, { hour: '11:00', Mon: 88, Tue: 91, Wed: 94, Thu: 90, Fri: 85, Sat: 42, Sun: 28 },
    { hour: '12:00', Mon: 85, Tue: 88, Wed: 91, Thu: 87, Fri: 82, Sat: 38, Sun: 25 }, { hour: '13:00', Mon: 72, Tue: 75, Wed: 78, Thu: 74, Fri: 69, Sat: 45, Sun: 32 },
    { hour: '14:00', Mon: 68, Tue: 71, Wed: 74, Thu: 70, Fri: 65, Sat: 48, Sun: 35 }, { hour: '15:00', Mon: 82, Tue: 85, Wed: 88, Thu: 84, Fri: 79, Sat: 52, Sun: 38 },
    { hour: '16:00', Mon: 76, Tue: 79, Wed: 82, Thu: 78, Fri: 73, Sat: 48, Sun: 34 }, { hour: '17:00', Mon: 65, Tue: 68, Wed: 71, Thu: 67, Fri: 62, Sat: 42, Sun: 28 }
];

export const engagementMetrics = [
    { metric: 'Чаттағы белсенділік', value: 85, fullMark: 100 }, { metric: 'Сауалнамаға қатысу', value: 78, fullMark: 100 },
    { metric: 'Тапсырмаларды орындау', value: 92, fullMark: 100 }, { metric: 'Жүйедегі уақыт', value: 88, fullMark: 100 },
    { metric: 'Материалдармен жұмыс', value: 76, fullMark: 100 }, { metric: 'Кері байланыс', value: 82, fullMark: 100 }
];

export const topEngagedStudents = [
    { name: 'Айзере Асқар', score: 95, activities: 156, timeSpent: '8с 45м' }, { name: 'Алихан Берік', score: 92, activities: 142, timeSpent: '7с 32м' },
    { name: 'Амина Смағұлова', score: 89, activities: 138, timeSpent: '7с 18м' }, { name: 'Санжар Қайратов', score: 87, activities: 134, timeSpent: '6с 54м' },
    { name: 'Нұрлан Оспанов', score: 85, activities: 129, timeSpent: '6с 41м' }
];

export const lowEngagementStudents = [
    { name: 'Арман Серіков', score: 42, activities: 23, timeSpent: '1с 15м', risk: 'high' }, { name: 'Камила Ермекова', score: 38, activities: 19, timeSpent: '0с 58м', risk: 'high' },
    { name: 'Диас Ертаев', score: 45, activities: 28, timeSpent: '1с 32м', risk: 'medium' }, { name: 'Анель Маратова', score: 48, activities: 31, timeSpent: '1с 45м', risk: 'medium' }
];

export const classComparisonData = [
  { class: '10А', performance: 4.3, engagement: 87, attendance: 94, assignments: 91 }, { class: '10Б', performance: 4.1, engagement: 82, attendance: 89, assignments: 88 },
  { class: '10В', performance: 3.9, engagement: 78, attendance: 85, assignments: 82 }, { class: '11А', performance: 4.5, engagement: 91, attendance: 96, assignments: 94 },
  { class: '11Б', performance: 4.2, engagement: 85, attendance: 92, assignments: 89 }, { class: '11В', performance: 4.0, engagement: 80, attendance: 87, assignments: 85 }
];

export const subjectComparisonData = [
  { subject: 'Математика', class10: 4.2, class11: 4.4, average: 4.3 }, { subject: 'Физика', class10: 3.8, class11: 4.1, average: 3.95 },
  { subject: 'Химия', class10: 4.0, class11: 4.3, average: 4.15 }, { subject: 'Биология', class10: 4.3, class11: 4.5, average: 4.4 },
  { subject: 'Тарих', class10: 3.9, class11: 4.2, average: 4.05 }, { subject: 'Әдебиет', class10: 4.1, class11: 4.4, average: 4.25 }
];

export const teacherComparisonData = [
  { teacher: 'Серікова А.Б.', subject: 'Математика', performance: 4.3, satisfaction: 4.5, classes: 3 }, { teacher: 'Оспанов Н.К.', subject: 'Физика', performance: 3.9, satisfaction: 4.2, classes: 2 },
  { teacher: 'Ермекова К.С.', subject: 'Химия', performance: 4.1, satisfaction: 4.4, classes: 2 }, { teacher: 'Асқар А.Е.', subject: 'Биология', performance: 4.4, satisfaction: 4.6, classes: 3 },
  { teacher: 'Маратова А.Д.', subject: 'Тарих', performance: 4.0, satisfaction: 4.3, classes: 4 }, { teacher: 'Берік А.Н.', subject: 'Әдебиет', performance: 4.2, satisfaction: 4.5, classes: 3 }
];

export const timeComparisonData = [
  { period: 'Қыркүйек', current: 3.8, previous: 3.6, target: 4.0 }, { period: 'Қазан', current: 3.9, previous: 3.7, target: 4.0 },
  { period: 'Қараша', current: 4.0, previous: 3.8, target: 4.1 }, { period: 'Желтоқсан', current: 4.1, previous: 3.9, target: 4.1 },
  { period: 'Қаңтар', current: 4.2, previous: 4.0, target: 4.2 }, { period: 'Ақпан', current: 4.1, previous: 4.1, target: 4.2 },
  { period: 'Наурыз', current: 4.3, previous: 4.2, target: 4.3 }
];

export const insightsByTab = {
  performance: [
    { id: 1, type: 'trend', title: 'Положительная динамика', content: `Средний балл по математике вырос на 0,3 пункта за последний месяц.`, confidence: 92, priority: 'high', actionable: true, recommendation: 'Рекомендуется распространить успешные методики на другие предметы' },
    { id: 2, type: 'alert', title: 'Снижение в 10В классе', content: `Обнаружено снижение успеваемости в 10В классе на 0,2 балла.`, confidence: 87, priority: 'medium', actionable: true, recommendation: 'Провести индивидуальные беседы с отстающими студентами' },
  ],
  engagement: [
    { id: 4, type: 'insight', title: 'Пиковая активность', content: `Максимальная вовлеченность студентов наблюдается в среду с 10:00 до 12:00.`, confidence: 94, priority: 'high', actionable: true, recommendation: 'Планировать сложные темы на время пиковой активности' },
    { id: 5, type: 'alert', title: 'Снижение в выходные', content: `Активность студентов в выходные дни упала на 35%.`, confidence: 89, priority: 'medium', actionable: true, recommendation: 'Внедрить геймификацию для поддержания интереса' },
  ],
  predictions: [
    { id: 7, type: 'prediction', title: 'Риск неуспеваемости', content: `Модель выявила 23 студента с высоким риском снижения успеваемости.`, confidence: 91, priority: 'high', actionable: true, recommendation: 'Немедленно начать индивидуальную работу с группой риска' },
  ],
  comparative: [
    { id: 10, type: 'comparison', title: 'Лидер по эффективности', content: `11А класс показывает лучшие результаты по всем метрикам.`, confidence: 95, priority: 'high', actionable: true, recommendation: 'Провести мастер-класс с преподавателем 11А класса' },
  ]
};