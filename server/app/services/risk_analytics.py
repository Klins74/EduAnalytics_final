"""
Сервис для анализа рисков и улучшенной аналитики трендов
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Уровни риска"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskFactor(str, Enum):
    """Факторы риска"""
    LOW_SUBMISSION_RATE = "low_submission_rate"
    DECLINING_GRADES = "declining_grades"
    FREQUENT_LATE_SUBMISSIONS = "frequent_late_submissions"
    LONG_INACTIVITY = "long_inactivity"
    MISSED_DEADLINES = "missed_deadlines"
    BELOW_AVERAGE_PERFORMANCE = "below_average_performance"
    INCONSISTENT_PERFORMANCE = "inconsistent_performance"
    NO_RECENT_ACTIVITY = "no_recent_activity"


class PerformanceStatus(str, Enum):
    """Статусы успеваемости"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    AT_RISK = "at_risk"


class RiskAnalyticsService:
    """Сервис для анализа рисков и улучшенной аналитики"""
    
    def __init__(self):
        self.grade_thresholds = {
            PerformanceStatus.EXCELLENT: 90,
            PerformanceStatus.GOOD: 75,
            PerformanceStatus.AVERAGE: 60,
            PerformanceStatus.POOR: 40
        }
        
        self.risk_weights = {
            RiskFactor.LOW_SUBMISSION_RATE: 0.25,
            RiskFactor.DECLINING_GRADES: 0.20,
            RiskFactor.FREQUENT_LATE_SUBMISSIONS: 0.15,
            RiskFactor.LONG_INACTIVITY: 0.15,
            RiskFactor.MISSED_DEADLINES: 0.10,
            RiskFactor.BELOW_AVERAGE_PERFORMANCE: 0.10,
            RiskFactor.INCONSISTENT_PERFORMANCE: 0.05
        }

    def forecast_average_grade(self, series: List[Dict[str, Any]], horizon: int = 8, method: str = "combo") -> List[Dict[str, float]]:
        """Прогноз среднего балла.
        methods:
        - ma: скользящая средняя по последним N точкам
        - ewma: экспоненциальное сглаживание (alpha)
        - holt: двухпараметрическое (уровень+тренд) упрощенное сглаживание
        - combo: ewma + линейный тренд (по умолчанию)
        """
        # Извлекаем числовой ряд
        values = [float(pt.get('average_grade', 0) or 0) for pt in series if pt.get('average_grade') is not None]
        if not values:
            return [{"pred_avg_grade": 0.0} for _ in range(max(1, horizon))]

        def clamp(v: float) -> float:
            return max(0.0, min(100.0, v))

        if method == "ma":
            window = min(5, len(values)) or 1
            avg = sum(values[-window:]) / window
            return [{"pred_avg_grade": round(clamp(avg), 2)} for _ in range(horizon)]

        if method == "ewma":
            alpha = 0.3
            s = values[0]
            for v in values[1:]:
                s = alpha * v + (1 - alpha) * s
            return [{"pred_avg_grade": round(clamp(s), 2)} for _ in range(horizon)]

        if method == "holt":
            # Простая версия Holt (level + trend)
            alpha = 0.4
            beta = 0.2
            level = values[0]
            trend = values[1] - values[0] if len(values) >= 2 else 0.0
            for v in values[1:]:
                prev_level = level
                level = alpha * v + (1 - alpha) * (level + trend)
                trend = beta * (level - prev_level) + (1 - beta) * trend
            return [
                {"pred_avg_grade": round(clamp(level + i * trend), 2)}
                for i in range(1, horizon + 1)
            ]

        # combo (default): EWMA + линейный тренд по последним точкам
        alpha = 0.3
        s = values[0]
        for v in values[1:]:
            s = alpha * v + (1 - alpha) * s

        trend = 0.0
        if len(values) >= 2:
            n = min(8, len(values))
            recent = values[-n:]
            x = list(range(n))
            mean_x = sum(x) / n
            mean_y = sum(recent) / n
            cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, recent))
            var = sum((xi - mean_x) ** 2 for xi in x) or 1.0
            slope = cov / var
            trend = slope

        last = values[-1]
        base = (s + last) / 2
        return [
            {"pred_avg_grade": round(clamp(base + i * trend), 2)}
            for i in range(1, horizon + 1)
        ]
    
    def calculate_student_risk_score(
        self,
        student_data: Dict[str, Any],
        course_averages: Dict[str, float],
        trend_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Вычисляет комплексный риск-скор для студента
        
        Args:
            student_data: Данные студента (оценки, сдачи, etc.)
            course_averages: Средние показатели по курсу
            trend_data: Данные трендов (опционально)
            
        Returns:
            Dict с риск-скором, уровнем риска и факторами
        """
        risk_factors = []
        risk_score = 0.0
        
        # 1. Анализ submission rate
        submission_rate = student_data.get('submission_rate', 0)
        if submission_rate < 50:
            risk_factors.append(RiskFactor.LOW_SUBMISSION_RATE)
            risk_score += self.risk_weights[RiskFactor.LOW_SUBMISSION_RATE] * (1 - submission_rate / 100)
        
        # 2. Анализ средней оценки
        avg_grade = student_data.get('average_grade', 0)
        course_avg_grade = course_averages.get('average_grade', 75)
        
        if avg_grade < 60:
            risk_factors.append(RiskFactor.BELOW_AVERAGE_PERFORMANCE)
            risk_score += self.risk_weights[RiskFactor.BELOW_AVERAGE_PERFORMANCE] * (1 - avg_grade / 100)
        
        # 3. Анализ своевременности
        on_time_rate = student_data.get('on_time_rate', 100)
        if on_time_rate < 70:
            risk_factors.append(RiskFactor.FREQUENT_LATE_SUBMISSIONS)
            risk_score += self.risk_weights[RiskFactor.FREQUENT_LATE_SUBMISSIONS] * (1 - on_time_rate / 100)
        
        # 4. Анализ трендов (если доступны)
        if trend_data:
            trend_analysis = self._analyze_trends(trend_data)
            if trend_analysis['declining_grades']:
                risk_factors.append(RiskFactor.DECLINING_GRADES)
                risk_score += self.risk_weights[RiskFactor.DECLINING_GRADES] * trend_analysis['decline_severity']
            
            if trend_analysis['long_inactivity']:
                risk_factors.append(RiskFactor.LONG_INACTIVITY)
                risk_score += self.risk_weights[RiskFactor.LONG_INACTIVITY] * trend_analysis['inactivity_severity']
        
        # 5. Анализ консистентности (если есть список оценок)
        grades_list = student_data.get('grades_list', [])
        if len(grades_list) > 2:
            consistency_score = self._calculate_consistency(grades_list)
            if consistency_score < 0.7:  # Низкая консистентность
                risk_factors.append(RiskFactor.INCONSISTENT_PERFORMANCE)
                risk_score += self.risk_weights[RiskFactor.INCONSISTENT_PERFORMANCE] * (1 - consistency_score)
        
        # 6. Отсутствие активности
        if student_data.get('submitted_assignments', 0) == 0:
            risk_factors.append(RiskFactor.NO_RECENT_ACTIVITY)
            risk_score += 0.3  # Высокий вес для полного отсутствия активности
        
        # Определяем уровень риска
        risk_level = self._determine_risk_level(risk_score)
        
        # Определяем статус успеваемости
        performance_status = self._determine_performance_status(avg_grade, risk_factors)
        
        return {
            'risk_score': round(risk_score, 3),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'performance_status': performance_status,
            'recommendations': self._generate_recommendations(risk_factors, student_data)
        }
    
    def calculate_course_risk_distribution(
        self, 
        students_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Анализ распределения рисков по курсу"""
        risk_distribution = {level.value: 0 for level in RiskLevel}
        performance_distribution = {status.value: 0 for status in PerformanceStatus}
        
        total_students = len(students_data)
        at_risk_students = []
        
        # Вычисляем средние показатели курса для сравнения
        course_averages = self._calculate_course_averages(students_data)
        
        for student in students_data:
            risk_analysis = self.calculate_student_risk_score(student, course_averages)
            
            risk_level = risk_analysis['risk_level']
            performance_status = risk_analysis['performance_status']
            
            risk_distribution[risk_level] += 1
            performance_distribution[performance_status] += 1
            
            if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                at_risk_students.append({
                    'student_id': student.get('student_id'),
                    'student_name': student.get('student_name'),
                    'risk_analysis': risk_analysis
                })
        
        # Конвертируем в проценты
        risk_percentages = {
            level: round((count / total_students) * 100, 1) if total_students > 0 else 0
            for level, count in risk_distribution.items()
        }
        
        performance_percentages = {
            status: round((count / total_students) * 100, 1) if total_students > 0 else 0
            for status, count in performance_distribution.items()
        }
        
        return {
            'total_students': total_students,
            'course_averages': course_averages,
            'risk_distribution': {
                'counts': risk_distribution,
                'percentages': risk_percentages
            },
            'performance_distribution': {
                'counts': performance_distribution,
                'percentages': performance_percentages
            },
            'at_risk_students': sorted(at_risk_students, 
                                     key=lambda x: x['risk_analysis']['risk_score'], 
                                     reverse=True),
            'insights': self._generate_course_insights(risk_distribution, performance_distribution, total_students)
        }
    
    def analyze_submission_patterns(
        self, 
        submissions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Анализ паттернов сдач"""
        if not submissions_data:
            return {'pattern': 'no_data', 'insights': []}
        
        # Группируем сдачи по дням недели и времени
        weekday_distribution = [0] * 7  # Пн-Вс
        hour_distribution = [0] * 24
        
        late_submissions = 0
        total_submissions = len(submissions_data)
        
        for submission in submissions_data:
            submitted_at = submission.get('submitted_at')
            due_date = submission.get('due_date')
            
            if submitted_at:
                if isinstance(submitted_at, str):
                    submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                
                weekday_distribution[submitted_at.weekday()] += 1
                hour_distribution[submitted_at.hour] += 1
                
                if due_date and submitted_at > due_date:
                    late_submissions += 1
        
        # Определяем паттерны
        peak_weekday = weekday_distribution.index(max(weekday_distribution))
        peak_hour = hour_distribution.index(max(hour_distribution))
        late_rate = (late_submissions / total_submissions) * 100 if total_submissions > 0 else 0
        
        # Определяем тип паттерна
        pattern_type = self._determine_submission_pattern(weekday_distribution, hour_distribution)
        
        return {
            'pattern_type': pattern_type,
            'total_submissions': total_submissions,
            'late_submissions': late_submissions,
            'late_rate': round(late_rate, 1),
            'peak_weekday': peak_weekday,  # 0=Понедельник, 6=Воскресенье
            'peak_hour': peak_hour,
            'weekday_distribution': weekday_distribution,
            'hour_distribution': hour_distribution,
            'insights': self._generate_submission_insights(pattern_type, late_rate, peak_weekday, peak_hour)
        }
    
    def _analyze_trends(self, trend_data: List[Dict]) -> Dict[str, Any]:
        """Анализ трендов для выявления рисков"""
        if len(trend_data) < 3:
            return {'declining_grades': False, 'long_inactivity': False}
        
        grades = [point.get('average_grade', 0) for point in trend_data if point.get('average_grade', 0) > 0]
        submissions = [point.get('submissions', 0) for point in trend_data]
        
        # Проверяем тренд оценок
        declining_grades = False
        decline_severity = 0.0
        
        if len(grades) >= 3:
            recent_avg = statistics.mean(grades[-3:])
            earlier_avg = statistics.mean(grades[:-3]) if len(grades) > 3 else statistics.mean(grades)
            
            if recent_avg < earlier_avg * 0.85:  # Снижение более чем на 15%
                declining_grades = True
                decline_severity = (earlier_avg - recent_avg) / earlier_avg
        
        # Проверяем инактивность
        long_inactivity = False
        inactivity_severity = 0.0
        
        recent_submissions = submissions[-5:] if len(submissions) >= 5 else submissions
        if sum(recent_submissions) == 0 and len(recent_submissions) >= 3:
            long_inactivity = True
            inactivity_severity = len([s for s in recent_submissions if s == 0]) / len(recent_submissions)
        
        return {
            'declining_grades': declining_grades,
            'decline_severity': decline_severity,
            'long_inactivity': long_inactivity,
            'inactivity_severity': inactivity_severity
        }
    
    def _calculate_consistency(self, grades: List[float]) -> float:
        """Вычисляет консистентность оценок (0-1, где 1 = очень консистентно)"""
        if len(grades) < 2:
            return 1.0
        
        mean_grade = statistics.mean(grades)
        if mean_grade == 0:
            return 0.0
        
        # Используем коэффициент вариации
        std_dev = statistics.stdev(grades) if len(grades) > 1 else 0
        cv = std_dev / mean_grade if mean_grade > 0 else 1.0
        
        # Преобразуем в консистентность (меньше вариация = больше консистентность)
        consistency = max(0, 1 - cv)
        return consistency
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Определяет уровень риска на основе скора"""
        if risk_score >= 0.7:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _determine_performance_status(self, avg_grade: float, risk_factors: List[RiskFactor]) -> PerformanceStatus:
        """Определяет статус успеваемости"""
        # Сначала проверяем критические риски
        critical_risks = [
            RiskFactor.NO_RECENT_ACTIVITY,
            RiskFactor.LOW_SUBMISSION_RATE,
            RiskFactor.DECLINING_GRADES
        ]
        
        if any(factor in risk_factors for factor in critical_risks):
            return PerformanceStatus.AT_RISK
        
        # Затем по оценкам
        if avg_grade >= self.grade_thresholds[PerformanceStatus.EXCELLENT]:
            return PerformanceStatus.EXCELLENT
        elif avg_grade >= self.grade_thresholds[PerformanceStatus.GOOD]:
            return PerformanceStatus.GOOD
        elif avg_grade >= self.grade_thresholds[PerformanceStatus.AVERAGE]:
            return PerformanceStatus.AVERAGE
        else:
            return PerformanceStatus.POOR
    
    def _calculate_course_averages(self, students_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Вычисляет средние показатели по курсу"""
        if not students_data:
            return {}
        
        grades = [s.get('average_grade', 0) for s in students_data if s.get('average_grade', 0) > 0]
        submission_rates = [s.get('submission_rate', 0) for s in students_data]
        on_time_rates = [s.get('on_time_rate', 0) for s in students_data if s.get('on_time_rate') is not None]
        
        return {
            'average_grade': round(statistics.mean(grades), 2) if grades else 0,
            'average_submission_rate': round(statistics.mean(submission_rates), 2) if submission_rates else 0,
            'average_on_time_rate': round(statistics.mean(on_time_rates), 2) if on_time_rates else 0,
            'median_grade': round(statistics.median(grades), 2) if grades else 0
        }
    
    def _determine_submission_pattern(self, weekday_dist: List[int], hour_dist: List[int]) -> str:
        """Определяет тип паттерна сдач"""
        total = sum(weekday_dist)
        if total == 0:
            return 'no_submissions'
        
        # Анализ по дням недели
        weekend_submissions = weekday_dist[5] + weekday_dist[6]  # Сб + Вс
        weekend_rate = weekend_submissions / total
        
        # Анализ по времени
        late_night_submissions = sum(hour_dist[22:24]) + sum(hour_dist[0:6])  # 22:00-06:00
        late_night_rate = late_night_submissions / total
        
        if weekend_rate > 0.4:
            return 'weekend_heavy'
        elif late_night_rate > 0.3:
            return 'night_owl'
        elif max(weekday_dist) / total > 0.5:
            return 'single_day_focused'
        else:
            return 'balanced'
    
    def _generate_recommendations(self, risk_factors: List[RiskFactor], student_data: Dict) -> List[str]:
        """Генерирует рекомендации на основе факторов риска"""
        recommendations = []
        
        if RiskFactor.LOW_SUBMISSION_RATE in risk_factors:
            recommendations.append("Необходимо увеличить количество сдаваемых заданий")
        
        if RiskFactor.DECLINING_GRADES in risk_factors:
            recommendations.append("Обратить внимание на снижение качества работ")
        
        if RiskFactor.FREQUENT_LATE_SUBMISSIONS in risk_factors:
            recommendations.append("Улучшить планирование времени для своевременной сдачи")
        
        if RiskFactor.LONG_INACTIVITY in risk_factors:
            recommendations.append("Возобновить активное участие в курсе")
        
        if RiskFactor.BELOW_AVERAGE_PERFORMANCE in risk_factors:
            recommendations.append("Рекомендуется дополнительная помощь преподавателя")
        
        if RiskFactor.INCONSISTENT_PERFORMANCE in risk_factors:
            recommendations.append("Стабилизировать качество выполнения заданий")
        
        if RiskFactor.NO_RECENT_ACTIVITY in risk_factors:
            recommendations.append("КРИТИЧНО: Необходимо немедленно связаться со студентом")
        
        return recommendations
    
    def _generate_course_insights(
        self, 
        risk_distribution: Dict[str, int], 
        performance_distribution: Dict[str, int], 
        total_students: int
    ) -> List[str]:
        """Генерирует инсайты по курсу"""
        insights = []
        
        if total_students == 0:
            return ["Нет данных о студентах"]
        
        high_risk_count = risk_distribution.get(RiskLevel.HIGH, 0) + risk_distribution.get(RiskLevel.CRITICAL, 0)
        high_risk_rate = (high_risk_count / total_students) * 100
        
        if high_risk_rate > 25:
            insights.append(f"ВНИМАНИЕ: {high_risk_rate:.1f}% студентов находятся в группе высокого риска")
        
        excellent_count = performance_distribution.get(PerformanceStatus.EXCELLENT, 0)
        excellent_rate = (excellent_count / total_students) * 100
        
        if excellent_rate > 50:
            insights.append(f"Отличные результаты: {excellent_rate:.1f}% студентов показывают отличную успеваемость")
        elif excellent_rate < 10:
            insights.append("Низкий процент отличников - возможно, курс слишком сложный")
        
        poor_count = performance_distribution.get(PerformanceStatus.POOR, 0)
        poor_rate = (poor_count / total_students) * 100
        
        if poor_rate > 30:
            insights.append(f"Требуется вмешательство: {poor_rate:.1f}% студентов показывают плохие результаты")
        
        return insights
    
    def _generate_submission_insights(
        self, 
        pattern_type: str, 
        late_rate: float, 
        peak_weekday: int, 
        peak_hour: int
    ) -> List[str]:
        """Генерирует инсайты по паттернам сдач"""
        insights = []
        
        weekday_names = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
        
        if pattern_type == 'weekend_heavy':
            insights.append("Студенты часто сдают задания в выходные - возможно, не хватает времени в будни")
        elif pattern_type == 'night_owl':
            insights.append("Много ночных сдач - студенты откладывают задания до последнего момента")
        elif pattern_type == 'single_day_focused':
            insights.append(f"Пик активности в {weekday_names[peak_weekday]} - возможно, связано с расписанием")
        
        if late_rate > 30:
            insights.append(f"Высокий процент опозданий ({late_rate:.1f}%) - стоит пересмотреть дедлайны")
        elif late_rate < 5:
            insights.append("Отличная дисциплина - студенты сдают вовремя")
        
        if 9 <= peak_hour <= 17:
            insights.append("Пик активности в рабочие часы - хорошая организация времени")
        elif peak_hour >= 22 or peak_hour <= 6:
            insights.append("Пик активности ночью - возможны проблемы с планированием времени")
        
        return insights


# Создаем глобальный экземпляр сервиса
risk_analytics_service = RiskAnalyticsService()


