#!/usr/bin/env python3
"""
Конфигурация системы уведомлений EduAnalytics

Этот файл содержит все настройки для системы уведомлений,
включая webhook URLs, интервалы проверки, шаблоны сообщений и т.д.
"""

from typing import List, Dict, Any
from pydantic import BaseSettings, validator
from enum import Enum

class NotificationChannel(str, Enum):
    """Каналы доставки уведомлений"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    """Приоритеты уведомлений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationEventType(str, Enum):
    """Типы событий для уведомлений"""
    DEADLINE_APPROACHING = "deadline_approaching"
    GRADE_CREATED = "grade_created"
    GRADE_UPDATED = "grade_updated"
    FEEDBACK_CREATED = "feedback_created"
    SCHEDULE_CREATED = "schedule_created"
    SCHEDULE_UPDATED = "schedule_updated"
    SUBMISSION_CREATED = "submission_created"
    ASSIGNMENT_CREATED = "assignment_created"
    COURSE_ENROLLMENT = "course_enrollment"
    SYSTEM_MAINTENANCE = "system_maintenance"

class NotificationSettings(BaseSettings):
    """Основные настройки системы уведомлений"""
    
    # Общие настройки
    ENABLE_NOTIFICATIONS: bool = True
    DEFAULT_TIMEZONE: str = "Europe/Moscow"
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 5
    
    # Webhook настройки
    WEBHOOK_URL: str = "http://localhost:5678/webhook/eduanalytics-webhook"
    WEBHOOK_TIMEOUT: int = 30
    WEBHOOK_SECRET: str = ""  # Секрет для подписи webhook'ов
    WEBHOOK_VERIFY_SSL: bool = True
    
    # Настройки проверки дедлайнов
    DEADLINE_CHECK_ENABLED: bool = True
    DEADLINE_CHECK_INTERVAL: int = 3600  # секунды (1 час)
    DEADLINE_NOTIFICATION_DAYS: List[int] = [7, 3, 1]  # дни до дедлайна
    DEADLINE_CHECK_TIME: str = "09:00"  # время ежедневной проверки
    
    # Настройки rate limiting
    RATE_LIMIT_ENABLED: bool = True
    MAX_NOTIFICATIONS_PER_USER_PER_HOUR: int = 50
    MAX_NOTIFICATIONS_PER_USER_PER_DAY: int = 200
    
    # Настройки логирования
    LOG_NOTIFICATIONS: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/notifications.log"
    
    # Настройки каналов доставки
    ENABLED_CHANNELS: List[NotificationChannel] = [
        NotificationChannel.EMAIL,
        NotificationChannel.WEBHOOK
    ]
    
    # Email настройки
    EMAIL_ENABLED: bool = True
    EMAIL_SERVICE: str = "emailjs"  # emailjs, smtp, sendgrid
    EMAIL_SERVICE_ID: str = ""
    EMAIL_USER_ID: str = ""
    EMAIL_ACCESS_TOKEN: str = ""
    
    # SMTP настройки (если используется)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    
    # Telegram настройки
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # SMS настройки
    SMS_ENABLED: bool = False
    SMS_SERVICE: str = "twilio"  # twilio, nexmo
    SMS_API_KEY: str = ""
    SMS_API_SECRET: str = ""
    SMS_FROM_NUMBER: str = ""
    
    # Push уведомления
    PUSH_ENABLED: bool = False
    PUSH_SERVICE: str = "firebase"  # firebase, onesignal
    PUSH_API_KEY: str = ""
    PUSH_PROJECT_ID: str = ""
    
    # Slack настройки
    SLACK_ENABLED: bool = False
    SLACK_WEBHOOK_URL: str = ""
    SLACK_CHANNEL: str = "#notifications"
    
    # Discord настройки
    DISCORD_ENABLED: bool = False
    DISCORD_WEBHOOK_URL: str = ""
    
    class Config:
        env_file = ".env"
        env_prefix = "NOTIFICATION_"
    
    @validator('DEADLINE_NOTIFICATION_DAYS')
    def validate_deadline_days(cls, v):
        if not v or not all(isinstance(day, int) and day > 0 for day in v):
            raise ValueError('DEADLINE_NOTIFICATION_DAYS должен содержать положительные числа')
        return sorted(v, reverse=True)  # Сортируем по убыванию
    
    @validator('WEBHOOK_URL')
    def validate_webhook_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('WEBHOOK_URL должен начинаться с http:// или https://')
        return v

# Шаблоны уведомлений
NOTIFICATION_TEMPLATES = {
    NotificationEventType.DEADLINE_APPROACHING: {
        "email": {
            "subject": "🚨 Приближается дедлайн: {assignment_title}",
            "template_id": "deadline_template",
            "variables": [
                "student_name", "assignment_title", "course_name", 
                "due_date", "days_remaining"
            ]
        },
        "telegram": {
            "template": (
                "🚨 Напоминание о дедлайне!\n\n"
                "Задание: {assignment_title}\n"
                "Курс: {course_name}\n"
                "До сдачи осталось: {days_remaining} дн.\n"
                "Дата сдачи: {due_date}\n\n"
                "Не забудьте сдать работу вовремя!"
            )
        },
        "sms": {
            "template": (
                "Дедлайн через {days_remaining} дн.: {assignment_title}. "
                "Сдать до {due_date}"
            )
        }
    },
    
    NotificationEventType.GRADE_CREATED: {
        "email": {
            "subject": "📊 Новая оценка: {assignment_title}",
            "template_id": "grade_template",
            "variables": [
                "student_name", "assignment_title", "course_name",
                "grade_value", "teacher_name", "comment"
            ]
        },
        "telegram": {
            "template": (
                "📊 Новая оценка!\n\n"
                "Задание: {assignment_title}\n"
                "Курс: {course_name}\n"
                "Оценка: {grade_value}\n"
                "Преподаватель: {teacher_name}\n\n"
                "{comment}"
            )
        },
        "sms": {
            "template": (
                "Новая оценка {grade_value} за {assignment_title} "
                "от {teacher_name}"
            )
        }
    },
    
    NotificationEventType.FEEDBACK_CREATED: {
        "email": {
            "subject": "💬 Новый комментарий: {submission_title}",
            "template_id": "feedback_template",
            "variables": [
                "student_name", "submission_title", "assignment_title",
                "course_name", "author_name", "feedback_text"
            ]
        },
        "telegram": {
            "template": (
                "💬 Новый комментарий!\n\n"
                "Работа: {submission_title}\n"
                "Задание: {assignment_title}\n"
                "Курс: {course_name}\n"
                "Автор: {author_name}\n\n"
                "Комментарий: {feedback_text}"
            )
        }
    },
    
    NotificationEventType.SCHEDULE_CREATED: {
        "email": {
            "subject": "📅 Новое занятие: {course_name}",
            "template_id": "schedule_template",
            "variables": [
                "course_name", "instructor_name", "schedule_date",
                "start_time", "end_time", "location", "description"
            ]
        },
        "telegram": {
            "template": (
                "📅 Новое занятие!\n\n"
                "Курс: {course_name}\n"
                "Преподаватель: {instructor_name}\n"
                "Дата: {schedule_date}\n"
                "Время: {start_time} - {end_time}\n"
                "Место: {location}\n\n"
                "{description}"
            )
        }
    },
    
    NotificationEventType.SCHEDULE_UPDATED: {
        "email": {
            "subject": "📅 Изменение в расписании: {course_name}",
            "template_id": "schedule_update_template",
            "variables": [
                "course_name", "instructor_name", "schedule_date",
                "start_time", "end_time", "location", "description",
                "changes"
            ]
        },
        "telegram": {
            "template": (
                "📅 Изменение в расписании!\n\n"
                "Курс: {course_name}\n"
                "Преподаватель: {instructor_name}\n"
                "Дата: {schedule_date}\n"
                "Время: {start_time} - {end_time}\n"
                "Место: {location}\n\n"
                "Изменения:\n{changes}"
            )
        }
    }
}

# Настройки приоритетов для разных типов уведомлений
NOTIFICATION_PRIORITIES = {
    NotificationEventType.DEADLINE_APPROACHING: NotificationPriority.HIGH,
    NotificationEventType.GRADE_CREATED: NotificationPriority.NORMAL,
    NotificationEventType.GRADE_UPDATED: NotificationPriority.NORMAL,
    NotificationEventType.FEEDBACK_CREATED: NotificationPriority.NORMAL,
    NotificationEventType.SCHEDULE_CREATED: NotificationPriority.NORMAL,
    NotificationEventType.SCHEDULE_UPDATED: NotificationPriority.HIGH,
    NotificationEventType.SUBMISSION_CREATED: NotificationPriority.LOW,
    NotificationEventType.ASSIGNMENT_CREATED: NotificationPriority.NORMAL,
    NotificationEventType.COURSE_ENROLLMENT: NotificationPriority.NORMAL,
    NotificationEventType.SYSTEM_MAINTENANCE: NotificationPriority.URGENT,
}

# Настройки каналов для разных типов уведомлений
NOTIFICATION_CHANNELS = {
    NotificationEventType.DEADLINE_APPROACHING: [
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.PUSH
    ],
    NotificationEventType.GRADE_CREATED: [
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM
    ],
    NotificationEventType.GRADE_UPDATED: [
        NotificationChannel.EMAIL
    ],
    NotificationEventType.FEEDBACK_CREATED: [
        NotificationChannel.EMAIL,
        NotificationChannel.PUSH
    ],
    NotificationEventType.SCHEDULE_CREATED: [
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM
    ],
    NotificationEventType.SCHEDULE_UPDATED: [
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.PUSH
    ],
    NotificationEventType.SUBMISSION_CREATED: [
        NotificationChannel.EMAIL
    ],
    NotificationEventType.ASSIGNMENT_CREATED: [
        NotificationChannel.EMAIL
    ],
    NotificationEventType.COURSE_ENROLLMENT: [
        NotificationChannel.EMAIL
    ],
    NotificationEventType.SYSTEM_MAINTENANCE: [
        NotificationChannel.EMAIL,
        NotificationChannel.TELEGRAM,
        NotificationChannel.PUSH,
        NotificationChannel.SMS
    ],
}

# Настройки пользовательских предпочтений по умолчанию
DEFAULT_USER_PREFERENCES = {
    "email_notifications": True,
    "telegram_notifications": False,
    "sms_notifications": False,
    "push_notifications": True,
    "quiet_hours_enabled": True,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00",
    "weekend_notifications": False,
    "notification_frequency": "immediate",  # immediate, daily_digest, weekly_digest
    "language": "ru",
    "timezone": "Europe/Moscow"
}

# Настройки для разных ролей пользователей
ROLE_NOTIFICATION_SETTINGS = {
    "student": {
        "enabled_events": [
            NotificationEventType.DEADLINE_APPROACHING,
            NotificationEventType.GRADE_CREATED,
            NotificationEventType.GRADE_UPDATED,
            NotificationEventType.FEEDBACK_CREATED,
            NotificationEventType.SCHEDULE_CREATED,
            NotificationEventType.SCHEDULE_UPDATED,
            NotificationEventType.ASSIGNMENT_CREATED,
        ],
        "default_channels": [
            NotificationChannel.EMAIL,
            NotificationChannel.PUSH
        ]
    },
    "teacher": {
        "enabled_events": [
            NotificationEventType.SUBMISSION_CREATED,
            NotificationEventType.SCHEDULE_CREATED,
            NotificationEventType.SCHEDULE_UPDATED,
            NotificationEventType.COURSE_ENROLLMENT,
            NotificationEventType.SYSTEM_MAINTENANCE,
        ],
        "default_channels": [
            NotificationChannel.EMAIL,
            NotificationChannel.TELEGRAM
        ]
    },
    "admin": {
        "enabled_events": list(NotificationEventType),
        "default_channels": [
            NotificationChannel.EMAIL,
            NotificationChannel.TELEGRAM,
            NotificationChannel.SLACK
        ]
    }
}

# Создание экземпляра настроек
settings = NotificationSettings()

# Функции для работы с конфигурацией

def get_notification_template(event_type: NotificationEventType, channel: NotificationChannel) -> Dict[str, Any]:
    """Получить шаблон уведомления для определенного типа события и канала"""
    return NOTIFICATION_TEMPLATES.get(event_type, {}).get(channel.value, {})

def get_notification_priority(event_type: NotificationEventType) -> NotificationPriority:
    """Получить приоритет для типа уведомления"""
    return NOTIFICATION_PRIORITIES.get(event_type, NotificationPriority.NORMAL)

def get_notification_channels(event_type: NotificationEventType) -> List[NotificationChannel]:
    """Получить список каналов для типа уведомления"""
    return NOTIFICATION_CHANNELS.get(event_type, [NotificationChannel.EMAIL])

def get_user_role_settings(role: str) -> Dict[str, Any]:
    """Получить настройки уведомлений для роли пользователя"""
    return ROLE_NOTIFICATION_SETTINGS.get(role, ROLE_NOTIFICATION_SETTINGS["student"])

def is_notification_enabled(event_type: NotificationEventType, user_role: str) -> bool:
    """Проверить, включены ли уведомления для типа события и роли пользователя"""
    role_settings = get_user_role_settings(user_role)
    return event_type in role_settings.get("enabled_events", [])

def validate_configuration() -> List[str]:
    """Проверить корректность конфигурации и вернуть список ошибок"""
    errors = []
    
    if settings.ENABLE_NOTIFICATIONS:
        if not settings.WEBHOOK_URL:
            errors.append("WEBHOOK_URL не настроен")
        
        if settings.EMAIL_ENABLED and settings.EMAIL_SERVICE == "emailjs":
            if not settings.EMAIL_SERVICE_ID:
                errors.append("EMAIL_SERVICE_ID не настроен для EmailJS")
            if not settings.EMAIL_USER_ID:
                errors.append("EMAIL_USER_ID не настроен для EmailJS")
        
        if settings.EMAIL_ENABLED and settings.EMAIL_SERVICE == "smtp":
            if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
                errors.append("SMTP credentials не настроены")
        
        if settings.TELEGRAM_ENABLED and not settings.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не настроен")
        
        if settings.SMS_ENABLED and not settings.SMS_API_KEY:
            errors.append("SMS_API_KEY не настроен")
    
    return errors

# Пример использования:
if __name__ == "__main__":
    # Проверка конфигурации
    config_errors = validate_configuration()
    if config_errors:
        print("Ошибки конфигурации:")
        for error in config_errors:
            print(f"  - {error}")
    else:
        print("✅ Конфигурация корректна")
    
    # Примеры использования функций
    print(f"\nШаблон для дедлайна (email): {get_notification_template(NotificationEventType.DEADLINE_APPROACHING, NotificationChannel.EMAIL)}")
    print(f"Приоритет для оценки: {get_notification_priority(NotificationEventType.GRADE_CREATED)}")
    print(f"Каналы для расписания: {get_notification_channels(NotificationEventType.SCHEDULE_UPDATED)}")
    print(f"Настройки для студента: {get_user_role_settings('student')}")