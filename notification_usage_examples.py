#!/usr/bin/env python3
"""
Примеры использования системы уведомлений EduAnalytics

Этот файл содержит практические примеры использования всех компонентов
системы уведомлений для разработчиков.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Импорты для работы с системой уведомлений
from server.app.services.notification import NotificationService
from server.app.tasks.deadline_checker import DeadlineChecker
from server.app.crud.feedback import CRUDFeedback
from server.app.crud.gradebook import CRUDGradebook
from server.app.crud.schedule import CRUDSchedule

class NotificationExamples:
    """Класс с примерами использования системы уведомлений"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.deadline_checker = DeadlineChecker()
    
    # Примеры базовых уведомлений
    
    def example_deadline_notification(self):
        """
        Пример отправки уведомления о приближающемся дедлайне
        """
        print("=== Пример уведомления о дедлайне ===")
        
        # Данные студента и задания
        student_data = {
            "student_id": 1,
            "student_name": "Иван Иванов",
            "student_email": "ivan.ivanov@university.edu"
        }
        
        assignment_data = {
            "assignment_id": 1,
            "assignment_title": "Лабораторная работа №3: Алгоритмы сортировки",
            "course_name": "Структуры данных и алгоритмы",
            "due_date": "2024-01-25T23:59:59Z",
            "days_remaining": 3
        }
        
        # Отправка уведомления
        success = self.notification_service.send_deadline_notification(
            student_id=student_data["student_id"],
            student_name=student_data["student_name"],
            student_email=student_data["student_email"],
            assignment_id=assignment_data["assignment_id"],
            assignment_title=assignment_data["assignment_title"],
            course_name=assignment_data["course_name"],
            due_date=assignment_data["due_date"],
            days_remaining=assignment_data["days_remaining"]
        )
        
        print(f"Уведомление отправлено: {success}")
        return success
    
    def example_grade_notification(self):
        """
        Пример отправки уведомления о новой оценке
        """
        print("=== Пример уведомления об оценке ===")
        
        # Данные оценки
        grade_data = {
            "student_id": 1,
            "assignment_id": 1,
            "grade_value": 92,
            "teacher_id": 5
        }
        
        # Отправка уведомления
        success = self.notification_service.send_grade_notification(
            student_id=grade_data["student_id"],
            assignment_id=grade_data["assignment_id"],
            grade_value=grade_data["grade_value"],
            teacher_id=grade_data["teacher_id"]
        )
        
        print(f"Уведомление об оценке отправлено: {success}")
        return success
    
    def example_custom_webhook(self):
        """
        Пример отправки пользовательского webhook
        """
        print("=== Пример пользовательского webhook ===")
        
        # Пользовательские данные
        custom_data = {
            "event_type": "course_enrollment",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "student_id": 1,
            "student_name": "Мария Петрова",
            "course_id": 3,
            "course_name": "Веб-разработка",
            "enrollment_date": datetime.utcnow().date().isoformat(),
            "message": "Студент записался на новый курс",
            "priority": "medium",
            "metadata": {
                "enrollment_type": "self_enrollment",
                "payment_status": "paid",
                "start_date": "2024-02-01"
            }
        }
        
        # Отправка webhook
        success = self.notification_service.send_webhook(custom_data)
        
        print(f"Пользовательский webhook отправлен: {success}")
        return success
    
    # Примеры интеграции с CRUD операциями
    
    def example_feedback_with_notification(self, db_session):
        """
        Пример создания обратной связи с уведомлением
        """
        print("=== Пример создания обратной связи с уведомлением ===")
        
        from server.app.schemas import FeedbackCreate
        
        # Данные обратной связи
        feedback_data = FeedbackCreate(
            submission_id=1,
            author_id=2,  # ID преподавателя
            content="Отличная работа! Особенно понравился подход к решению задачи. Рекомендую обратить внимание на оптимизацию алгоритма.",
            rating=5
        )
        
        # Создание обратной связи с уведомлением
        crud_feedback = CRUDFeedback()
        feedback = crud_feedback.create_feedback(
            db=db_session,
            obj_in=feedback_data,
            send_notification=True  # Включаем уведомления
        )
        
        print(f"Обратная связь создана с ID: {feedback.id}")
        return feedback
    
    def example_grade_entry_with_notification(self, db_session, current_user):
        """
        Пример создания записи оценки с уведомлением
        """
        print("=== Пример создания оценки с уведомлением ===")
        
        from server.app.schemas import GradebookEntryCreate
        
        # Данные оценки
        grade_data = GradebookEntryCreate(
            student_id=1,
            assignment_id=1,
            score=88,
            comment="Хорошее выполнение задания. Есть небольшие замечания по стилю кода."
        )
        
        # Создание записи оценки с уведомлением
        crud_gradebook = CRUDGradebook()
        grade_entry = crud_gradebook.create_entry(
            db=db_session,
            obj_in=grade_data,
            current_user=current_user
        )
        
        print(f"Оценка создана с ID: {grade_entry.id}")
        return grade_entry
    
    def example_schedule_with_notification(self, db_session, current_user):
        """
        Пример создания расписания с уведомлением
        """
        print("=== Пример создания расписания с уведомлением ===")
        
        from server.app.schemas import ScheduleCreate
        
        # Данные расписания
        schedule_data = ScheduleCreate(
            course_id=1,
            instructor_id=2,
            date="2024-01-25",
            start_time="14:00:00",
            end_time="15:30:00",
            location="Аудитория 205",
            description="Лекция: Введение в машинное обучение"
        )
        
        # Создание расписания с уведомлением
        crud_schedule = CRUDSchedule()
        schedule = crud_schedule.create_schedule(
            db=db_session,
            obj_in=schedule_data,
            current_user=current_user
        )
        
        print(f"Расписание создано с ID: {schedule.id}")
        return schedule
    
    # Примеры проверки дедлайнов
    
    def example_deadline_check(self):
        """
        Пример запуска проверки дедлайнов
        """
        print("=== Пример проверки дедлайнов ===")
        
        # Проверка дедлайнов для разных интервалов
        intervals = [1, 3, 7]  # 1, 3 и 7 дней
        
        for interval in intervals:
            print(f"Проверка дедлайнов за {interval} дней...")
            self.deadline_checker.check_deadlines()
        
        print("Проверка дедлайнов завершена")
    
    def example_manual_deadline_check(self):
        """
        Пример ручной проверки дедлайнов для конкретного интервала
        """
        print("=== Пример ручной проверки дедлайнов ===")
        
        # Проверка дедлайнов за 3 дня
        self.deadline_checker._check_deadlines_for_interval(3)
        
        print("Ручная проверка дедлайнов завершена")
    
    # Примеры обработки ошибок
    
    def example_error_handling(self):
        """
        Пример обработки ошибок при отправке уведомлений
        """
        print("=== Пример обработки ошибок ===")
        
        # Попытка отправки уведомления с некорректными данными
        try:
            # Данные с отсутствующими обязательными полями
            incomplete_data = {
                "event_type": "test_event"
                # Отсутствует timestamp и другие поля
            }
            
            success = self.notification_service.send_webhook(incomplete_data)
            
            if not success:
                print("Уведомление не было отправлено из-за ошибки")
                # Здесь можно добавить логику повторной отправки
                # или сохранения в очередь для последующей обработки
            
        except Exception as e:
            print(f"Произошла ошибка при отправке уведомления: {e}")
            # Логирование ошибки
            # Уведомление администратора
    
    # Примеры пакетной обработки
    
    def example_batch_notifications(self):
        """
        Пример пакетной отправки уведомлений
        """
        print("=== Пример пакетной отправки уведомлений ===")
        
        # Список студентов для уведомления
        students = [
            {"id": 1, "name": "Иван Иванов", "email": "ivan@university.edu"},
            {"id": 2, "name": "Мария Петрова", "email": "maria@university.edu"},
            {"id": 3, "name": "Алексей Сидоров", "email": "alexey@university.edu"}
        ]
        
        # Общие данные задания
        assignment_info = {
            "assignment_id": 1,
            "assignment_title": "Итоговый проект",
            "course_name": "Программная инженерия",
            "due_date": "2024-01-30T23:59:59Z",
            "days_remaining": 5
        }
        
        # Отправка уведомлений всем студентам
        successful_notifications = 0
        failed_notifications = 0
        
        for student in students:
            success = self.notification_service.send_deadline_notification(
                student_id=student["id"],
                student_name=student["name"],
                student_email=student["email"],
                **assignment_info
            )
            
            if success:
                successful_notifications += 1
                print(f"✓ Уведомление отправлено: {student['name']}")
            else:
                failed_notifications += 1
                print(f"✗ Ошибка отправки: {student['name']}")
        
        print(f"\nИтого: {successful_notifications} успешно, {failed_notifications} ошибок")
    
    # Примеры асинхронной обработки
    
    async def example_async_notifications(self):
        """
        Пример асинхронной отправки уведомлений
        """
        print("=== Пример асинхронной отправки уведомлений ===")
        
        # Список уведомлений для отправки
        notifications = [
            {
                "event_type": "assignment_reminder",
                "student_id": 1,
                "message": "Напоминание о задании 1"
            },
            {
                "event_type": "assignment_reminder",
                "student_id": 2,
                "message": "Напоминание о задании 2"
            },
            {
                "event_type": "assignment_reminder",
                "student_id": 3,
                "message": "Напоминание о задании 3"
            }
        ]
        
        # Асинхронная отправка
        tasks = []
        for notification in notifications:
            # Добавляем timestamp
            notification["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            # Создаем задачу для асинхронного выполнения
            task = asyncio.create_task(
                self._send_notification_async(notification)
            )
            tasks.append(task)
        
        # Ожидаем выполнения всех задач
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обработка результатов
        successful = sum(1 for result in results if result is True)
        failed = len(results) - successful
        
        print(f"Асинхронная отправка завершена: {successful} успешно, {failed} ошибок")
    
    async def _send_notification_async(self, notification_data: Dict) -> bool:
        """
        Вспомогательный метод для асинхронной отправки уведомления
        """
        try:
            # Имитация асинхронной отправки
            await asyncio.sleep(0.1)  # Небольшая задержка
            return self.notification_service.send_webhook(notification_data)
        except Exception as e:
            print(f"Ошибка асинхронной отправки: {e}")
            return False
    
    # Примеры мониторинга и отладки
    
    def example_notification_monitoring(self):
        """
        Пример мониторинга уведомлений
        """
        print("=== Пример мониторинга уведомлений ===")
        
        # Статистика уведомлений
        stats = {
            "total_sent": 0,
            "successful": 0,
            "failed": 0,
            "by_type": {}
        }
        
        # Тестовые уведомления разных типов
        test_notifications = [
            {"event_type": "deadline_approaching", "student_id": 1},
            {"event_type": "grade_created", "student_id": 2},
            {"event_type": "feedback_created", "student_id": 3},
            {"event_type": "schedule_updated", "course_id": 1}
        ]
        
        for notification in test_notifications:
            # Добавляем обязательные поля
            notification["timestamp"] = datetime.utcnow().isoformat() + "Z"
            notification["message"] = f"Тестовое уведомление типа {notification['event_type']}"
            
            # Отправка уведомления
            success = self.notification_service.send_webhook(notification)
            
            # Обновление статистики
            stats["total_sent"] += 1
            event_type = notification["event_type"]
            
            if success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1
            
            # Статистика по типам
            if event_type not in stats["by_type"]:
                stats["by_type"][event_type] = {"sent": 0, "successful": 0}
            
            stats["by_type"][event_type]["sent"] += 1
            if success:
                stats["by_type"][event_type]["successful"] += 1
        
        # Вывод статистики
        print("\nСтатистика уведомлений:")
        print(f"Всего отправлено: {stats['total_sent']}")
        print(f"Успешно: {stats['successful']}")
        print(f"Ошибок: {stats['failed']}")
        print(f"Процент успеха: {(stats['successful'] / stats['total_sent'] * 100):.1f}%")
        
        print("\nПо типам уведомлений:")
        for event_type, type_stats in stats["by_type"].items():
            success_rate = (type_stats["successful"] / type_stats["sent"] * 100)
            print(f"  {event_type}: {type_stats['successful']}/{type_stats['sent']} ({success_rate:.1f}%)")
    
    def example_debug_webhook(self):
        """
        Пример отладки webhook
        """
        print("=== Пример отладки webhook ===")
        
        # Тестовые данные для отладки
        debug_data = {
            "event_type": "debug_test",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "debug_info": {
                "test_id": "debug_001",
                "environment": "development",
                "version": "1.0.0",
                "user_agent": "EduAnalytics-NotificationService/1.0"
            },
            "message": "Тестовое уведомление для отладки"
        }
        
        print("Отправка отладочного webhook...")
        print(f"URL: {self.notification_service.webhook_url}")
        print(f"Данные: {json.dumps(debug_data, indent=2, ensure_ascii=False)}")
        
        success = self.notification_service.send_webhook(debug_data)
        
        if success:
            print("✓ Отладочный webhook отправлен успешно")
        else:
            print("✗ Ошибка отправки отладочного webhook")
            print("Проверьте:")
            print("- URL webhook в настройках")
            print("- Доступность сервера")
            print("- Формат данных")
            print("- Логи приложения")

# Функции для демонстрации

def run_basic_examples():
    """Запуск базовых примеров"""
    examples = NotificationExamples()
    
    print("Запуск базовых примеров уведомлений...\n")
    
    # Базовые уведомления
    examples.example_deadline_notification()
    print()
    
    examples.example_grade_notification()
    print()
    
    examples.example_custom_webhook()
    print()
    
    # Проверка дедлайнов
    examples.example_deadline_check()
    print()
    
    # Обработка ошибок
    examples.example_error_handling()
    print()
    
    # Пакетная отправка
    examples.example_batch_notifications()
    print()
    
    # Мониторинг
    examples.example_notification_monitoring()
    print()
    
    # Отладка
    examples.example_debug_webhook()

async def run_async_examples():
    """Запуск асинхронных примеров"""
    examples = NotificationExamples()
    
    print("Запуск асинхронных примеров...\n")
    
    await examples.example_async_notifications()

def run_crud_examples():
    """Запуск примеров интеграции с CRUD"""
    print("Примеры интеграции с CRUD операциями")
    print("Для запуска этих примеров необходима активная сессия базы данных")
    print("Смотрите код в методах:")
    print("- example_feedback_with_notification()")
    print("- example_grade_entry_with_notification()")
    print("- example_schedule_with_notification()")

def main():
    """Главная функция для демонстрации примеров"""
    print("=" * 60)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ СИСТЕМЫ УВЕДОМЛЕНИЙ EDUANALYTICS")
    print("=" * 60)
    print()
    
    # Базовые примеры
    run_basic_examples()
    
    print("\n" + "=" * 60)
    
    # Асинхронные примеры
    asyncio.run(run_async_examples())
    
    print("\n" + "=" * 60)
    
    # CRUD примеры
    run_crud_examples()
    
    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)

if __name__ == "__main__":
    main()