from typing import Dict, Any, List, Optional
import httpx
from app.services.ai_function_calling import function_registry


# Функция для получения сравнительного анализа успеваемости студентов
async def compare_students_performance(student_id1: int, student_id2: int, course_id: Optional[int] = None) -> Dict[str, Any]:
    """Compare performance of two students"""
    try:
        # В реальном приложении здесь был бы запрос к базе данных
        # Для демонстрации возвращаем моковые данные
        students = {
            1: {
                "id": 1, 
                "name": "Иванов Иван", 
                "avg_grade": 4.2,
                "courses": {
                    1: {"grade": 4.5, "attendance": 90, "completed_assignments": 8, "total_assignments": 10},
                    2: {"grade": 3.8, "attendance": 75, "completed_assignments": 6, "total_assignments": 10},
                }
            },
            2: {
                "id": 2, 
                "name": "Петров Петр", 
                "avg_grade": 3.8,
                "courses": {
                    1: {"grade": 3.5, "attendance": 65, "completed_assignments": 5, "total_assignments": 10},
                    3: {"grade": 4.2, "attendance": 80, "completed_assignments": 7, "total_assignments": 10},
                }
            }
        }
        
        if student_id1 not in students or student_id2 not in students:
            return {"error": "Один или оба студента не найдены"}
            
        student1 = students[student_id1]
        student2 = students[student_id2]
        
        comparison = {
            "student1": {
                "id": student1["id"],
                "name": student1["name"],
                "avg_grade": student1["avg_grade"]
            },
            "student2": {
                "id": student2["id"],
                "name": student2["name"],
                "avg_grade": student2["avg_grade"]
            },
            "diff": {
                "avg_grade": round(student1["avg_grade"] - student2["avg_grade"], 1)
            }
        }
        
        # Если указан конкретный курс, добавляем сравнение по нему
        if course_id is not None:
            if course_id in student1.get("courses", {}) and course_id in student2.get("courses", {}):
                course1 = student1["courses"][course_id]
                course2 = student2["courses"][course_id]
                
                comparison["course"] = {
                    "id": course_id,
                    "student1": course1,
                    "student2": course2,
                    "diff": {
                        "grade": round(course1["grade"] - course2["grade"], 1),
                        "attendance": course1["attendance"] - course2["attendance"],
                        "completed_assignments": course1["completed_assignments"] - course2["completed_assignments"]
                    }
                }
            else:
                comparison["course"] = {"error": "Один или оба студента не записаны на указанный курс"}
                
        return comparison
    except Exception as e:
        return {"error": str(e)}


# Функция для получения рекомендаций по улучшению успеваемости
async def get_performance_recommendations(student_id: int) -> Dict[str, Any]:
    """Get recommendations for improving student performance"""
    try:
        # В реальном приложении здесь был бы анализ данных студента
        # Для демонстрации возвращаем моковые данные
        recommendations = {
            1: {
                "student_id": 1,
                "name": "Иванов Иван",
                "recommendations": [
                    {
                        "type": "attendance",
                        "description": "Улучшить посещаемость по курсу Физика",
                        "priority": "medium"
                    },
                    {
                        "type": "assignments",
                        "description": "Сдать оставшиеся задания по курсу Программирование",
                        "priority": "high"
                    }
                ]
            },
            2: {
                "student_id": 2,
                "name": "Петров Петр",
                "recommendations": [
                    {
                        "type": "attendance",
                        "description": "Улучшить посещаемость по курсу Математика",
                        "priority": "high"
                    },
                    {
                        "type": "study_group",
                        "description": "Присоединиться к учебной группе по курсу Физика",
                        "priority": "medium"
                    },
                    {
                        "type": "consultation",
                        "description": "Записаться на консультацию к преподавателю по курсу Математика",
                        "priority": "medium"
                    }
                ]
            }
        }
        
        if student_id not in recommendations:
            return {"error": "Студент не найден"}
            
        return recommendations[student_id]
    except Exception as e:
        return {"error": str(e)}


# Функция для получения тенденций успеваемости по группе
async def get_group_performance_trends(group_id: int, period: Optional[str] = "semester") -> Dict[str, Any]:
    """Get performance trends for a student group"""
    try:
        # В реальном приложении здесь был бы запрос к базе данных
        # Для демонстрации возвращаем моковые данные
        groups = {
            1: {
                "id": 1,
                "name": "Группа 101",
                "trends": {
                    "semester": {
                        "avg_grade": [3.8, 3.9, 4.0, 4.1],
                        "attendance": [75, 78, 80, 82],
                        "assignments_completion": [70, 75, 80, 85],
                        "months": ["Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
                    },
                    "year": {
                        "avg_grade": [3.7, 3.8, 3.9, 4.0, 4.1],
                        "attendance": [72, 75, 78, 80, 82],
                        "assignments_completion": [65, 70, 75, 80, 85],
                        "quarters": ["Q1", "Q2", "Q3", "Q4", "Q1 (текущий)"]
                    }
                },
                "risk_students": [
                    {"id": 3, "name": "Сидоров Сидор", "risk_factor": "high", "reason": "Низкая посещаемость"},
                    {"id": 5, "name": "Кузнецова Анна", "risk_factor": "medium", "reason": "Несданные задания"}
                ]
            },
            2: {
                "id": 2,
                "name": "Группа 202",
                "trends": {
                    "semester": {
                        "avg_grade": [4.0, 4.1, 4.2, 4.1],
                        "attendance": [80, 82, 85, 83],
                        "assignments_completion": [75, 80, 85, 82],
                        "months": ["Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
                    },
                    "year": {
                        "avg_grade": [3.9, 4.0, 4.1, 4.2, 4.1],
                        "attendance": [78, 80, 82, 85, 83],
                        "assignments_completion": [70, 75, 80, 85, 82],
                        "quarters": ["Q1", "Q2", "Q3", "Q4", "Q1 (текущий)"]
                    }
                },
                "risk_students": [
                    {"id": 12, "name": "Смирнов Алексей", "risk_factor": "medium", "reason": "Снижение успеваемости"}
                ]
            }
        }
        
        if group_id not in groups:
            return {"error": "Группа не найдена"}
            
        group = groups[group_id]
        
        if period not in group["trends"]:
            return {"error": f"Данные за период {period} не найдены"}
            
        return {
            "group_id": group["id"],
            "name": group["name"],
            "period": period,
            "trends": group["trends"][period],
            "risk_students": group["risk_students"]
        }
    except Exception as e:
        return {"error": str(e)}


# Регистрируем функции
function_registry.register(
    name="compare_students_performance",
    description="Сравнить успеваемость двух студентов",
    parameters={
        "student_id1": {
            "type": "integer",
            "description": "ID первого студента"
        },
        "student_id2": {
            "type": "integer",
            "description": "ID второго студента"
        },
        "course_id": {
            "type": "integer",
            "description": "ID курса для сравнения (опционально)",
            "required": False
        }
    },
    implementation=compare_students_performance
)

function_registry.register(
    name="get_performance_recommendations",
    description="Получить рекомендации по улучшению успеваемости студента",
    parameters={
        "student_id": {
            "type": "integer",
            "description": "ID студента"
        }
    },
    implementation=get_performance_recommendations
)

function_registry.register(
    name="get_group_performance_trends",
    description="Получить тенденции успеваемости по группе",
    parameters={
        "group_id": {
            "type": "integer",
            "description": "ID группы"
        },
        "period": {
            "type": "string",
            "description": "Период анализа (semester или year)",
            "required": False
        }
    },
    implementation=get_group_performance_trends
)
