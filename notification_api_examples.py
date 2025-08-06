#!/usr/bin/env python3
"""
Примеры использования API для тестирования системы уведомлений EduAnalytics

Этот файл содержит примеры HTTP запросов для тестирования различных
типов уведомлений в системе EduAnalytics.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Базовый URL API
BASE_URL = "http://localhost:8000/api/v1"

# Заголовки для запросов
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_ACCESS_TOKEN"  # Замените на реальный токен
}

def create_test_data():
    """
    Создание тестовых данных для демонстрации уведомлений
    """
    print("=== Создание тестовых данных ===")
    
    # 1. Создание курса
    course_data = {
        "name": "Тестовый курс программирования",
        "description": "Курс для тестирования системы уведомлений",
        "code": "TEST-PROG-001"
    }
    
    response = requests.post(f"{BASE_URL}/courses/", 
                           headers=HEADERS, 
                           json=course_data)
    if response.status_code == 201:
        course = response.json()
        print(f"✅ Курс создан: {course['name']} (ID: {course['id']})")
    else:
        print(f"❌ Ошибка создания курса: {response.text}")
        return None
    
    # 2. Создание студента
    student_data = {
        "username": "test_student",
        "email": "student@test.com",
        "first_name": "Тестовый",
        "last_name": "Студент",
        "role": "student"
    }
    
    response = requests.post(f"{BASE_URL}/users/", 
                           headers=HEADERS, 
                           json=student_data)
    if response.status_code == 201:
        student = response.json()
        print(f"✅ Студент создан: {student['first_name']} {student['last_name']} (ID: {student['id']})")
    else:
        print(f"❌ Ошибка создания студента: {response.text}")
        return None
    
    # 3. Создание преподавателя
    teacher_data = {
        "username": "test_teacher",
        "email": "teacher@test.com",
        "first_name": "Тестовый",
        "last_name": "Преподаватель",
        "role": "teacher"
    }
    
    response = requests.post(f"{BASE_URL}/users/", 
                           headers=HEADERS, 
                           json=teacher_data)
    if response.status_code == 201:
        teacher = response.json()
        print(f"✅ Преподаватель создан: {teacher['first_name']} {teacher['last_name']} (ID: {teacher['id']})")
    else:
        print(f"❌ Ошибка создания преподавателя: {response.text}")
        return None
    
    # 4. Создание задания с дедлайном
    due_date = (datetime.now() + timedelta(days=3)).isoformat()
    assignment_data = {
        "title": "Тестовое задание",
        "description": "Задание для тестирования уведомлений о дедлайнах",
        "course_id": course['id'],
        "due_date": due_date,
        "max_score": 100
    }
    
    response = requests.post(f"{BASE_URL}/assignments/", 
                           headers=HEADERS, 
                           json=assignment_data)
    if response.status_code == 201:
        assignment = response.json()
        print(f"✅ Задание создано: {assignment['title']} (ID: {assignment['id']})")
        print(f"   Дедлайн: {assignment['due_date']}")
    else:
        print(f"❌ Ошибка создания задания: {response.text}")
        return None
    
    return {
        "course": course,
        "student": student,
        "teacher": teacher,
        "assignment": assignment
    }

def test_grade_notification(test_data: Dict[str, Any]):
    """
    Тестирование уведомлений об оценках
    """
    print("\n=== Тестирование уведомлений об оценках ===")
    
    # Создание записи в журнале оценок
    grade_data = {
        "student_id": test_data['student']['id'],
        "assignment_id": test_data['assignment']['id'],
        "score": 85,
        "comment": "Хорошая работа, но есть замечания по оформлению"
    }
    
    response = requests.post(f"{BASE_URL}/gradebook/entries/", 
                           headers=HEADERS, 
                           json=grade_data)
    
    if response.status_code == 201:
        grade = response.json()
        print(f"✅ Оценка выставлена: {grade['score']} баллов")
        print(f"   Студент: {test_data['student']['first_name']} {test_data['student']['last_name']}")
        print(f"   Задание: {test_data['assignment']['title']}")
        print(f"   Комментарий: {grade['comment']}")
        print("📧 Уведомление о новой оценке должно быть отправлено")
    else:
        print(f"❌ Ошибка выставления оценки: {response.text}")

def test_feedback_notification(test_data: Dict[str, Any]):
    """
    Тестирование уведомлений об обратной связи
    """
    print("\n=== Тестирование уведомлений об обратной связи ===")
    
    # Сначала создаем работу студента
    submission_data = {
        "assignment_id": test_data['assignment']['id'],
        "student_id": test_data['student']['id'],
        "content": "Решение тестового задания",
        "file_path": "/uploads/test_submission.pdf"
    }
    
    response = requests.post(f"{BASE_URL}/submissions/", 
                           headers=HEADERS, 
                           json=submission_data)
    
    if response.status_code == 201:
        submission = response.json()
        print(f"✅ Работа студента создана (ID: {submission['id']})")
        
        # Теперь добавляем обратную связь
        feedback_data = {
            "submission_id": submission['id'],
            "author_id": test_data['teacher']['id'],
            "content": "Отличное решение! Код чистый и хорошо структурированный. Рекомендую добавить больше комментариев.",
            "rating": 4
        }
        
        response = requests.post(f"{BASE_URL}/feedback/", 
                               headers=HEADERS, 
                               json=feedback_data)
        
        if response.status_code == 201:
            feedback = response.json()
            print(f"✅ Обратная связь добавлена (ID: {feedback['id']})")
            print(f"   Автор: {test_data['teacher']['first_name']} {test_data['teacher']['last_name']}")
            print(f"   Рейтинг: {feedback['rating']}/5")
            print(f"   Комментарий: {feedback['content'][:50]}...")
            print("📧 Уведомление об обратной связи должно быть отправлено")
        else:
            print(f"❌ Ошибка добавления обратной связи: {response.text}")
    else:
        print(f"❌ Ошибка создания работы: {response.text}")

def test_schedule_notification(test_data: Dict[str, Any]):
    """
    Тестирование уведомлений о расписании
    """
    print("\n=== Тестирование уведомлений о расписании ===")
    
    # Создание записи в расписании
    schedule_date = (datetime.now() + timedelta(days=1)).date().isoformat()
    schedule_data = {
        "course_id": test_data['course']['id'],
        "instructor_id": test_data['teacher']['id'],
        "date": schedule_date,
        "start_time": "10:00:00",
        "end_time": "11:30:00",
        "location": "Аудитория 101",
        "description": "Лекция по основам программирования"
    }
    
    response = requests.post(f"{BASE_URL}/schedules/", 
                           headers=HEADERS, 
                           json=schedule_data)
    
    if response.status_code == 201:
        schedule = response.json()
        print(f"✅ Расписание создано (ID: {schedule['id']})")
        print(f"   Дата: {schedule['date']}")
        print(f"   Время: {schedule['start_time']} - {schedule['end_time']}")
        print(f"   Место: {schedule['location']}")
        print(f"   Описание: {schedule['description']}")
        print("📧 Уведомление о новом расписании должно быть отправлено")
        
        # Обновление расписания
        update_data = {
            "location": "Аудитория 205 (изменено)",
            "description": "Лекция перенесена в другую аудиторию"
        }
        
        response = requests.patch(f"{BASE_URL}/schedules/{schedule['id']}", 
                                headers=HEADERS, 
                                json=update_data)
        
        if response.status_code == 200:
            updated_schedule = response.json()
            print(f"✅ Расписание обновлено")
            print(f"   Новое место: {updated_schedule['location']}")
            print(f"   Новое описание: {updated_schedule['description']}")
            print("📧 Уведомление об изменении расписания должно быть отправлено")
        else:
            print(f"❌ Ошибка обновления расписания: {response.text}")
    else:
        print(f"❌ Ошибка создания расписания: {response.text}")

def test_deadline_checker():
    """
    Тестирование проверки дедлайнов
    """
    print("\n=== Тестирование проверки дедлайнов ===")
    
    # Прямой вызов проверки дедлайнов через API (если есть такой endpoint)
    response = requests.post(f"{BASE_URL}/tasks/check-deadlines", 
                           headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Проверка дедлайнов выполнена")
        print(f"   Найдено заданий с приближающимися дедлайнами: {result.get('assignments_checked', 0)}")
        print(f"   Отправлено уведомлений: {result.get('notifications_sent', 0)}")
        print("📧 Уведомления о дедлайнах должны быть отправлены")
    else:
        print(f"❌ Ошибка проверки дедлайнов: {response.text}")
        print("ℹ️  Возможно, endpoint не реализован. Проверка дедлайнов работает в фоновом режиме.")

def test_webhook_endpoint():
    """
    Тестирование webhook endpoint (симуляция n8n)
    """
    print("\n=== Тестирование webhook endpoint ===")
    
    # Пример данных уведомления
    test_notification = {
        "event_type": "test_notification",
        "timestamp": datetime.now().isoformat() + "Z",
        "message": "Тестовое уведомление для проверки webhook",
        "test_data": {
            "student_name": "Тестовый Студент",
            "course_name": "Тестовый курс"
        }
    }
    
    # Отправка на webhook URL (замените на ваш URL)
    webhook_url = "http://localhost:5678/webhook/eduanalytics-webhook"
    
    try:
        response = requests.post(webhook_url, 
                               json=test_notification, 
                               timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Webhook успешно получил уведомление")
            print(f"   Ответ: {response.text}")
        else:
            print(f"❌ Webhook вернул ошибку: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к webhook: {e}")
        print("ℹ️  Убедитесь, что n8n запущен и webhook настроен")

def main():
    """
    Основная функция для запуска всех тестов
    """
    print("🚀 Запуск тестирования системы уведомлений EduAnalytics")
    print("=" * 60)
    
    # Создание тестовых данных
    test_data = create_test_data()
    
    if not test_data:
        print("❌ Не удалось создать тестовые данные. Завершение тестирования.")
        return
    
    # Тестирование различных типов уведомлений
    test_grade_notification(test_data)
    test_feedback_notification(test_data)
    test_schedule_notification(test_data)
    test_deadline_checker()
    test_webhook_endpoint()
    
    print("\n" + "=" * 60)
    print("✅ Тестирование завершено!")
    print("\nПроверьте:")
    print("1. Логи сервера на наличие сообщений об отправке уведомлений")
    print("2. n8n workflow на получение webhook'ов")
    print("3. Настроенные каналы доставки (email, telegram и т.д.)")

if __name__ == "__main__":
    main()

# Дополнительные утилиты для отладки

def check_notification_service_health():
    """
    Проверка состояния сервиса уведомлений
    """
    print("\n=== Проверка состояния сервиса уведомлений ===")
    
    # Проверка доступности API
    try:
        response = requests.get(f"{BASE_URL}/health", headers=HEADERS, timeout=5)
        if response.status_code == 200:
            print("✅ API сервер доступен")
        else:
            print(f"⚠️  API сервер вернул код: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API сервер недоступен: {e}")
    
    # Проверка webhook endpoint
    webhook_url = "http://localhost:5678/webhook/eduanalytics-webhook"
    try:
        response = requests.get(webhook_url, timeout=5)
        print("✅ Webhook endpoint доступен")
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook endpoint недоступен: {e}")
        print("ℹ️  Убедитесь, что n8n запущен")

def send_test_notification(event_type: str, **kwargs):
    """
    Отправка тестового уведомления
    """
    notification_data = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat() + "Z",
        **kwargs
    }
    
    webhook_url = "http://localhost:5678/webhook/eduanalytics-webhook"
    
    try:
        response = requests.post(webhook_url, json=notification_data, timeout=10)
        print(f"✅ Уведомление '{event_type}' отправлено: {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        return None

# Примеры использования утилит:
# check_notification_service_health()
# send_test_notification("test_event", message="Тестовое сообщение")