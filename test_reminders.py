import requests
import json
from datetime import datetime, timedelta

# Получаем токен
auth_response = requests.post('http://localhost:8000/auth/token', data={
    'username': 'admin@example.com', 
    'password': 'admin'
})

if auth_response.status_code == 200:
    token = auth_response.json()['access_token']
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print("🔔 Тестирование системы напоминаний\n")
    
    # 1. Проверяем текущие настройки
    print("1. Получение текущих настроек напоминаний...")
    settings_response = requests.get('http://localhost:8000/api/reminders/settings', headers=headers)
    if settings_response.status_code == 200:
        settings = settings_response.json()
        print(f"✓ Найдено {len(settings)} настроек")
        for setting in settings:
            print(f"  - {setting['reminder_type']}: {'включено' if setting['is_enabled'] else 'выключено'}")
    else:
        print(f"✗ Ошибка получения настроек: {settings_response.status_code}")
    
    print()
    
    # 2. Обновляем настройку для предстоящих занятий
    print("2. Настройка напоминаний о предстоящих занятиях...")
    update_data = {
        'is_enabled': True,
        'interval_before': '1h',
        'notification_channel': 'email'
    }
    
    update_response = requests.put(
        'http://localhost:8000/api/reminders/settings/schedule_upcoming',
        headers=headers,
        json=update_data
    )
    
    if update_response.status_code == 200:
        print("✓ Настройки обновлены")
        updated_setting = update_response.json()
        print(f"  Напоминать за: {updated_setting['interval_before']}")
        print(f"  Канал: {updated_setting['notification_channel']}")
    else:
        print(f"✗ Ошибка обновления: {update_response.status_code}")
    
    print()
    
    # 3. Отправляем тестовое напоминание
    print("3. Отправка тестового напоминания...")
    test_data = {
        'reminder_type': 'schedule_upcoming',
        'notification_channel': 'email',
        'test_message': 'Это тестовое напоминание от системы EduAnalytics!'
    }
    
    test_response = requests.post(
        'http://localhost:8000/api/reminders/test',
        headers=headers,
        json=test_data
    )
    
    if test_response.status_code == 200:
        print("✓ Тестовое напоминание отправлено")
        print(f"  Ответ: {test_response.json()['message']}")
    else:
        print(f"✗ Ошибка отправки: {test_response.status_code}")
        print(f"  {test_response.text}")
    
    print()
    
    # 4. Создаем занятие для проверки автоматических напоминаний
    print("4. Создание занятия для автоматических напоминаний...")
    tomorrow = datetime.now() + timedelta(days=1)
    schedule_data = {
        'course_id': 1,
        'schedule_date': tomorrow.strftime('%Y-%m-%d'),
        'start_time': '14:00:00',
        'end_time': '15:30:00',
        'location': 'Аудитория 201',
        'instructor_id': 1,
        'lesson_type': 'lecture',
        'description': 'Тестовое занятие для проверки напоминаний',
        'is_cancelled': False
    }
    
    schedule_response = requests.post(
        'http://localhost:8000/api/schedule/',
        headers=headers,
        json=schedule_data
    )
    
    if schedule_response.status_code == 201:
        schedule = schedule_response.json()
        print(f"✓ Занятие создано с ID: {schedule['id']}")
        print(f"  Дата: {schedule['schedule_date']}")
        print(f"  Время: {schedule['start_time']}-{schedule['end_time']}")
        print("  (Напоминания должны быть автоматически запланированы)")
    else:
        print(f"✗ Ошибка создания занятия: {schedule_response.status_code}")
        print(f"  {schedule_response.text}")
    
    print()
    
    # 5. Получаем предстоящие напоминания
    print("5. Получение предстоящих напоминаний...")
    upcoming_response = requests.get(
        'http://localhost:8000/api/reminders/upcoming?days_ahead=7',
        headers=headers
    )
    
    if upcoming_response.status_code == 200:
        upcoming = upcoming_response.json()
        print(f"✓ Найдено {len(upcoming)} предстоящих напоминаний")
        for reminder in upcoming:
            print(f"  - {reminder['title']}")
            print(f"    Отправить: {reminder['send_at']}")
            print(f"    Канал: {reminder['notification_channel']}")
    else:
        print(f"✗ Ошибка получения напоминаний: {upcoming_response.status_code}")
    
    print()
    
    # 6. Получаем статистику
    print("6. Статистика напоминаний...")
    stats_response = requests.get('http://localhost:8000/api/reminders/stats', headers=headers)
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print(f"✓ Всего настроек: {stats['total_settings']}")
        print(f"✓ Включенных настроек: {stats['enabled_settings']}")
        print(f"✓ Предстоящих напоминаний: {stats['upcoming_reminders']}")
        
        print("\n  Настройки по типам:")
        for type_name, type_settings in stats['settings_by_type'].items():
            status = "включено" if type_settings['enabled'] else "выключено"
            print(f"    {type_name}: {status}")
            if type_settings['enabled']:
                print(f"      Интервал: {type_settings['interval']}")
                print(f"      Канал: {type_settings['channel']}")
    else:
        print(f"✗ Ошибка получения статистики: {stats_response.status_code}")
    
    print("\n🎉 Тестирование завершено!")
    print("\nДля проверки фронтенда откройте:")
    print("http://localhost:4028/reminders")
    
else:
    print("❌ Ошибка авторизации")
