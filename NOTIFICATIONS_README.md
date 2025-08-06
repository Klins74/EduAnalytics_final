# Система уведомлений EduAnalytics

Эта система предоставляет комплексное решение для отправки уведомлений о различных событиях в образовательной платформе EduAnalytics.

## Возможности

### Типы уведомлений

1. **Уведомления о дедлайнах** (`deadline_approaching`)
   - Автоматическая проверка приближающихся дедлайнов
   - Настраиваемые интервалы уведомлений (7, 3, 1 день)
   - Отправка студентам и преподавателям

2. **Уведомления об оценках** (`grade_created`, `grade_updated`)
   - Мгновенные уведомления при выставлении оценок
   - Информация о задании, оценке и преподавателе

3. **Уведомления об обратной связи** (`feedback_created`)
   - Уведомления при добавлении комментариев к работам
   - Детали о работе и авторе комментария

4. **Уведомления о расписании** (`schedule_created`, `schedule_updated`)
   - Информирование об изменениях в расписании
   - Детали о времени, месте и изменениях

## Архитектура

### Компоненты системы

1. **NotificationService** (`server/app/services/notification.py`)
   - Центральный сервис для отправки уведомлений
   - Поддержка webhook'ов и legacy форматов
   - Методы для каждого типа уведомлений

2. **DeadlineChecker** (`server/app/tasks/deadline_checker.py`)
   - Фоновая задача для проверки дедлайнов
   - Планировщик для периодических проверок
   - Настраиваемые интервалы уведомлений

3. **CRUD интеграции**
   - `feedback.py` - уведомления при создании обратной связи
   - `gradebook.py` - уведомления при работе с оценками
   - `schedule.py` - уведомления при изменении расписания

## Настройка

### 1. Конфигурация webhook'ов

В файле `server/app/core/config.py` добавьте:

```python
class Settings(BaseSettings):
    # ... существующие настройки
    
    # Настройки уведомлений
    WEBHOOK_URL: str = "http://localhost:5678/webhook/eduanalytics-webhook"
    WEBHOOK_TIMEOUT: int = 30
    ENABLE_NOTIFICATIONS: bool = True
    
    # Настройки проверки дедлайнов
    DEADLINE_CHECK_INTERVAL: int = 3600  # секунды (1 час)
    DEADLINE_NOTIFICATION_DAYS: List[int] = [7, 3, 1]  # дни до дедлайна
```

### 2. Запуск планировщика дедлайнов

В файле `server/main.py` добавьте:

```python
from app.tasks import start_deadline_scheduler

@app.on_event("startup")
async def startup_event():
    # ... существующий код
    
    # Запуск планировщика дедлайнов
    if settings.ENABLE_NOTIFICATIONS:
        start_deadline_scheduler()
```

### 3. Настройка n8n workflow

1. Импортируйте `n8n_workflow_example.json` в n8n
2. Настройте credentials для:
   - Email сервиса (EmailJS или SMTP)
   - Telegram Bot (если используется)
3. Обновите URL webhook'а в настройках
4. Активируйте workflow

## Использование

### Отправка уведомлений вручную

```python
from app.services.notification import NotificationService

notification_service = NotificationService()

# Уведомление о дедлайне
notification_service.send_deadline_notification(
    student_id=1,
    assignment_id=1,
    days_remaining=3
)

# Уведомление об оценке
notification_service.send_grade_notification(
    student_id=1,
    assignment_id=1,
    grade_value=85,
    teacher_id=1
)
```

### Проверка дедлайнов

```python
from app.tasks.deadline_checker import DeadlineChecker

checker = DeadlineChecker()

# Проверка всех дедлайнов
checker.check_deadlines()

# Проверка конкретного задания
checker.check_single_assignment(assignment_id=1)
```

## Структура данных уведомлений

### Уведомление о дедлайне
```json
{
  "event_type": "deadline_approaching",
  "timestamp": "2024-01-15T10:30:00Z",
  "student_id": 1,
  "student_name": "Иван Иванов",
  "student_email": "ivan@example.com",
  "assignment_id": 1,
  "assignment_title": "Лабораторная работа №1",
  "course_name": "Программирование",
  "due_date": "2024-01-18T23:59:59Z",
  "days_remaining": 3
}
```

### Уведомление об оценке
```json
{
  "event_type": "grade_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "student_id": 1,
  "student_name": "Иван Иванов",
  "student_email": "ivan@example.com",
  "assignment_id": 1,
  "assignment_title": "Лабораторная работа №1",
  "course_name": "Программирование",
  "grade_value": 85,
  "teacher_id": 1,
  "teacher_name": "Петр Петров",
  "teacher_email": "petr@example.com"
}
```

### Уведомление об обратной связи
```json
{
  "event_type": "feedback_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "student_id": 1,
  "student_name": "Иван Иванов",
  "student_email": "ivan@example.com",
  "submission_id": 1,
  "submission_title": "Решение задачи",
  "assignment_title": "Лабораторная работа №1",
  "course_name": "Программирование",
  "feedback_text": "Хорошая работа, но есть замечания...",
  "author_id": 1,
  "author_name": "Петр Петров",
  "author_email": "petr@example.com"
}
```

### Уведомление о расписании
```json
{
  "event_type": "schedule_created",
  "timestamp": "2024-01-15T10:30:00Z",
  "course_id": 1,
  "course_name": "Программирование",
  "instructor_name": "Петр Петров",
  "schedule_date": "2024-01-20",
  "start_time": "10:00:00",
  "end_time": "11:30:00",
  "location": "Аудитория 101",
  "description": "Лекция по основам программирования",
  "students": [
    {
      "student_id": 1,
      "student_name": "Иван Иванов",
      "student_email": "ivan@example.com"
    }
  ]
}
```

## Мониторинг и отладка

### Логирование

Все уведомления логируются с уровнем INFO/ERROR:

```python
import logging

logger = logging.getLogger(__name__)

# Настройка логирования в main.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Проверка статуса

```python
# Проверка доступности webhook'а
from app.services.notification import NotificationService

service = NotificationService()
status = service.check_webhook_health()
print(f"Webhook status: {status}")
```

## Расширение функциональности

### Добавление нового типа уведомлений

1. Добавьте метод в `NotificationService`:

```python
def send_custom_notification(self, **kwargs):
    data = {
        "event_type": "custom_event",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **kwargs
    }
    return self.send_webhook(data)
```

2. Интегрируйте в соответствующий CRUD:

```python
# В методе создания/обновления
try:
    NotificationService().send_custom_notification(
        # параметры уведомления
    )
except Exception as e:
    logger.error(f"Failed to send notification: {e}")
```

3. Обновите n8n workflow для обработки нового типа

### Добавление новых каналов доставки

В n8n workflow добавьте новые узлы для:
- SMS уведомлений
- Push уведомлений
- Slack/Discord интеграций
- Мобильных приложений

## Безопасность

1. **Аутентификация webhook'ов**: Используйте токены или подписи для проверки подлинности
2. **Ограничение данных**: Не передавайте чувствительную информацию в уведомлениях
3. **Rate limiting**: Ограничьте частоту отправки уведомлений
4. **Логирование**: Ведите аудит всех отправленных уведомлений

## Производительность

1. **Асинхронная отправка**: Используйте фоновые задачи для отправки уведомлений
2. **Батчинг**: Группируйте уведомления для массовой отправки
3. **Кэширование**: Кэшируйте данные пользователей для уменьшения запросов к БД
4. **Мониторинг**: Отслеживайте время отклика и успешность доставки

## Поддержка

Для получения помощи:
1. Проверьте логи приложения
2. Убедитесь в корректности настроек webhook'а
3. Проверьте статус n8n workflow
4. Обратитесь к документации n8n для настройки интеграций