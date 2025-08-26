#!/usr/bin/env python3
"""
Тестирование расширенной системы уведомлений EduAnalytics
"""

import requests
import json
import time
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"
ADMIN_TOKEN = None

def get_auth_token():
    """Получить токен аутентификации для админа."""
    global ADMIN_TOKEN
    
    if ADMIN_TOKEN:
        return ADMIN_TOKEN
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin@example.com",
            "password": "admin"
        })
        
        if response.status_code == 200:
            data = response.json()
            ADMIN_TOKEN = data["access_token"]
            print(f"✅ Получен токен аутентификации: {ADMIN_TOKEN[:20]}...")
            return ADMIN_TOKEN
        else:
            print(f"❌ Ошибка аутентификации: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка при получении токена: {e}")
        return None

def test_notification_templates():
    """Тест получения шаблонов уведомлений."""
    print("\n📋 Тестирование шаблонов уведомлений...")
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/notifications/templates",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Получено {len(templates)} шаблонов:")
            for template in templates:
                print(f"  - {template['name']} ({template['event_type']})")
            return True
        else:
            print(f"❌ Ошибка получения шаблонов: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении шаблонов: {e}")
        return False

def test_available_channels():
    """Тест получения доступных каналов."""
    print("\n📡 Тестирование доступных каналов...")
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/notifications/channels",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            channels = response.json()
            print(f"✅ Доступные каналы: {', '.join(channels)}")
            return True
        else:
            print(f"❌ Ошибка получения каналов: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении каналов: {e}")
        return False

def test_available_priorities():
    """Тест получения доступных приоритетов."""
    print("\n⚡ Тестирование доступных приоритетов...")
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/notifications/priorities",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            priorities = response.json()
            print(f"✅ Доступные приоритеты: {', '.join(priorities)}")
            return True
        else:
            print(f"❌ Ошибка получения приоритетов: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении приоритетов: {e}")
        return False

def test_send_notification():
    """Тест отправки уведомления."""
    print("\n📤 Тестирование отправки уведомления...")
    
    token = get_auth_token()
    if not token:
        return False
    
    notification_data = {
        "event_type": "test_notification",
        "data": {
            "message": "Тестовое уведомление из Python скрипта",
            "timestamp": datetime.now().isoformat(),
            "test": True,
            "script": "test_notification_system.py"
        },
        "channels": ["webhook"],
        "priority": "normal",
        "recipients": [
            {
                "id": 1,
                "name": "Test User",
                "email": "test@example.com",
                "type": "user"
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/send",
            json=notification_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Уведомление отправлено успешно:")
            print(f"  - Каналы: {result.get('channels_used', [])}")
            print(f"  - Приоритет: {result.get('priority', 'unknown')}")
            print(f"  - Результаты: {result.get('results', {})}")
            return True
        else:
            print(f"❌ Ошибка отправки уведомления: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления: {e}")
        return False

def test_send_bulk_notifications():
    """Тест массовой отправки уведомлений."""
    print("\n📦 Тестирование массовой отправки уведомлений...")
    
    token = get_auth_token()
    if not token:
        return False
    
    notifications = [
        {
            "event_type": "deadline_reminder",
            "data": {
                "assignment_title": "Домашнее задание 1",
                "due_date": "2024-12-31T23:59:59Z",
                "course_name": "Математика",
                "hours_remaining": 24
            },
            "channels": ["webhook", "email"],
            "priority": "high",
            "recipients": [
                {"id": 1, "name": "Студент 1", "email": "student1@example.com"},
                {"id": 2, "name": "Студент 2", "email": "student2@example.com"}
            ]
        },
        {
            "event_type": "grade_notification",
            "data": {
                "student_name": "Иван Иванов",
                "grade_value": 85.5,
                "assignment_title": "Контрольная работа",
                "course_name": "Физика"
            },
            "channels": ["webhook"],
            "priority": "normal",
            "recipients": [
                {"id": 1, "name": "Иван Иванов", "email": "ivan@example.com"}
            ]
        }
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/notifications/send-bulk",
            json=notifications,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Массовая отправка выполнена:")
            print(f"  - Отправлено: {result.get('message', 'Unknown')}")
            print(f"  - Результаты: {len(result.get('results', []))} уведомлений")
            return True
        else:
            print(f"❌ Ошибка массовой отправки: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при массовой отправке: {e}")
        return False

def test_notification_stats():
    """Тест получения статистики уведомлений."""
    print("\n📊 Тестирование статистики уведомлений...")
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/notifications/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Статистика получена:")
            print(f"  - Всего отправлено: {stats.get('total_sent', 0)}")
            print(f"  - Всего ошибок: {stats.get('total_failed', 0)}")
            print(f"  - По каналам: {stats.get('by_channel', {})}")
            return True
        else:
            print(f"❌ Ошибка получения статистики: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")
        return False

def test_webhook_notification():
    """Тест отправки webhook уведомления."""
    print("\n🔗 Тестирование webhook уведомления...")
    
    token = get_auth_token()
    if not token:
        return False
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/n8n/notify",
            json={
                "event_type": "test_notification",
                "data": {
                    "message": "Webhook тест из Python скрипта",
                    "timestamp": datetime.now().isoformat(),
                    "test": True
                }
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook уведомление отправлено: {result.get('message', 'Success')}")
            return True
        else:
            print(f"❌ Ошибка webhook уведомления: {response.status_code}")
            print(f"  Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при отправке webhook: {e}")
        return False

def main():
    """Основная функция тестирования."""
    print("🚀 Тестирование расширенной системы уведомлений EduAnalytics")
    print("=" * 60)
    
    # Проверяем доступность сервера
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"✅ Сервер доступен: {BASE_URL}")
        else:
            print(f"❌ Сервер недоступен: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Не удается подключиться к серверу: {e}")
        return
    
    # Запускаем тесты
    tests = [
        ("Шаблоны уведомлений", test_notification_templates),
        ("Доступные каналы", test_available_channels),
        ("Доступные приоритеты", test_available_priorities),
        ("Отправка уведомления", test_send_notification),
        ("Массовая отправка", test_send_bulk_notifications),
        ("Статистика", test_notification_stats),
        ("Webhook уведомление", test_webhook_notification)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Выводим итоги
    print("\n" + "=" * 60)
    print("📋 ИТОГИ ТЕСТИРОВАНИЯ:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены успешно!")
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте логи сервера.")

if __name__ == "__main__":
    main()
