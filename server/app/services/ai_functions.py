from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime, timedelta
from app.services.ai_function_calling import function_registry


# Функция для получения информации о курсе
async def get_course_info(course_id: int) -> Dict[str, Any]:
    """Get information about a course"""
    try:
        # В реальном приложении здесь был бы запрос к базе данных
        # Для демонстрации возвращаем моковые данные
        courses = {
            1: {"id": 1, "name": "Математика", "description": "Высшая математика для инженеров", "students_count": 45},
            2: {"id": 2, "name": "Физика", "description": "Общая физика", "students_count": 38},
            3: {"id": 3, "name": "Программирование", "description": "Основы программирования на Python", "students_count": 62},
        }
        
        if course_id in courses:
            return courses[course_id]
        return {"error": "Курс не найден"}
    except Exception as e:
        return {"error": str(e)}


# Функция для получения статистики успеваемости студента
async def get_student_performance(student_id: int, course_id: Optional[int] = None) -> Dict[str, Any]:
    """Get student performance statistics"""
    try:
        # В реальном приложении здесь был бы запрос к базе данных
        # Для демонстрации возвращаем моковые данные
        performances = {
            1: {
                "student_id": 1,
                "name": "Иванов Иван",
                "average_grade": 4.2,
                "attendance": 85,
                "completed_assignments": 12,
                "total_assignments": 15,
                "courses": {
                    1: {"grade": 4.5, "attendance": 90},
                    2: {"grade": 3.8, "attendance": 75},
                }
            },
            2: {
                "student_id": 2,
                "name": "Петров Петр",
                "average_grade": 3.8,
                "attendance": 70,
                "completed_assignments": 10,
                "total_assignments": 15,
                "courses": {
                    1: {"grade": 3.5, "attendance": 65},
                    3: {"grade": 4.2, "attendance": 80},
                }
            }
        }
        
        if student_id not in performances:
            return {"error": "Студент не найден"}
            
        result = performances[student_id].copy()
        
        if course_id is not None:
            if course_id in result.get("courses", {}):
                result["course_performance"] = result["courses"][course_id]
            else:
                result["course_performance"] = {"error": "Курс не найден для этого студента"}
                
        return result
    except Exception as e:
        return {"error": str(e)}


# Функция для получения свободных слотов для расписания
async def get_available_slots(instructor_id: int, date: Optional[str] = None) -> Dict[str, Any]:
    """Get available time slots for an instructor on a specific date"""
    try:
        # Если дата не указана, используем завтрашний день
        if not date:
            tomorrow = datetime.now() + timedelta(days=1)
            date = tomorrow.strftime("%Y-%m-%d")
            
        # В реальном приложении здесь был бы запрос к базе данных
        # Для демонстрации возвращаем моковые данные
        instructors = {
            1: {"id": 1, "name": "Сидоров А.А.", "department": "Математика"},
            2: {"id": 2, "name": "Кузнецова Е.В.", "department": "Физика"},
        }
        
        # Занятые слоты (в реальности из базы данных)
        busy_slots = {
            1: {
                "2023-09-15": [{"start": "09:00", "end": "10:30"}, {"start": "13:00", "end": "14:30"}],
                "2023-09-16": [{"start": "11:00", "end": "12:30"}],
            },
            2: {
                "2023-09-15": [{"start": "10:00", "end": "11:30"}, {"start": "15:00", "end": "16:30"}],
                "2023-09-16": [],
            }
        }
        
        if instructor_id not in instructors:
            return {"error": "Преподаватель не найден"}
            
        # Рабочее время с 9:00 до 18:00
        working_hours = {
            "start": "09:00",
            "end": "18:00",
        }
        
        # Получаем занятые слоты для преподавателя на указанную дату
        instructor_busy_slots = busy_slots.get(instructor_id, {}).get(date, [])
        
        # Генерируем все возможные слоты с шагом 1.5 часа
        all_slots = []
        slot_start = datetime.strptime(working_hours["start"], "%H:%M")
        slot_end = datetime.strptime(working_hours["end"], "%H:%M")
        
        while slot_start < slot_end:
            slot_end_time = slot_start + timedelta(hours=1, minutes=30)
            if slot_end_time <= slot_end:
                all_slots.append({
                    "start": slot_start.strftime("%H:%M"),
                    "end": slot_end_time.strftime("%H:%M")
                })
            slot_start = slot_start + timedelta(hours=1, minutes=30)
            
        # Фильтруем занятые слоты
        available_slots = []
        for slot in all_slots:
            is_available = True
            for busy in instructor_busy_slots:
                busy_start = datetime.strptime(busy["start"], "%H:%M")
                busy_end = datetime.strptime(busy["end"], "%H:%M")
                slot_start = datetime.strptime(slot["start"], "%H:%M")
                slot_end = datetime.strptime(slot["end"], "%H:%M")
                
                # Проверяем пересечение
                if not (slot_end <= busy_start or slot_start >= busy_end):
                    is_available = False
                    break
                    
            if is_available:
                available_slots.append(slot)
                
        return {
            "instructor": instructors[instructor_id],
            "date": date,
            "available_slots": available_slots
        }
    except Exception as e:
        return {"error": str(e)}


# Функция для получения прогноза успеваемости
async def predict_performance(student_id: int, course_id: int) -> Dict[str, Any]:
    """Predict student performance for a course"""
    try:
        # В реальном приложении здесь был бы запрос к модели ML
        # Для демонстрации возвращаем моковые данные
        predictions = {
            (1, 1): {"predicted_grade": 4.3, "risk_level": "low", "recommendation": "Продолжайте в том же духе"},
            (1, 2): {"predicted_grade": 3.9, "risk_level": "medium", "recommendation": "Обратите внимание на домашние задания"},
            (2, 1): {"predicted_grade": 3.2, "risk_level": "high", "recommendation": "Требуется дополнительная консультация"},
            (2, 3): {"predicted_grade": 4.0, "risk_level": "low", "recommendation": "Продолжайте в том же духе"},
        }
        
        key = (student_id, course_id)
        if key in predictions:
            return {
                "student_id": student_id,
                "course_id": course_id,
                "prediction": predictions[key]
            }
        return {"error": "Нет данных для прогноза"}
    except Exception as e:
        return {"error": str(e)}


# Регистрируем функции
function_registry.register(
    name="get_course_info",
    description="Получить информацию о курсе по его ID",
    parameters={
        "course_id": {
            "type": "integer",
            "description": "ID курса"
        }
    },
    implementation=get_course_info
)

function_registry.register(
    name="get_student_performance",
    description="Получить статистику успеваемости студента",
    parameters={
        "student_id": {
            "type": "integer",
            "description": "ID студента"
        },
        "course_id": {
            "type": "integer",
            "description": "ID курса (опционально)",
            "required": False
        }
    },
    implementation=get_student_performance
)

function_registry.register(
    name="get_available_slots",
    description="Получить доступные временные слоты для преподавателя на указанную дату",
    parameters={
        "instructor_id": {
            "type": "integer",
            "description": "ID преподавателя"
        },
        "date": {
            "type": "string",
            "description": "Дата в формате YYYY-MM-DD (опционально)",
            "required": False
        }
    },
    implementation=get_available_slots
)

function_registry.register(
    name="predict_performance",
    description="Предсказать успеваемость студента по курсу",
    parameters={
        "student_id": {
            "type": "integer",
            "description": "ID студента"
        },
        "course_id": {
            "type": "integer",
            "description": "ID курса"
        }
    },
    implementation=predict_performance
)

