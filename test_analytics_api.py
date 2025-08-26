#!/usr/bin/env python3
"""
Тест Analytics API для проверки функциональности аналитики.
"""
import requests
import json
import uuid
from datetime import datetime, timedelta

def test_analytics_api():
    """Тестирует основные эндпоинты Analytics API."""
    
    # Получаем токен для admin
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)

    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return

    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    print('📊 Testing Analytics API...')

    # 1. Тестируем общую сводку системы
    print('\n1. Testing system summary...')
    summary_res = requests.get('http://localhost:8000/api/analytics/dashboard/summary', headers=headers)
    print(f'   System summary: {summary_res.status_code}')
    
    if summary_res.status_code == 200:
        summary_data = summary_res.json()
        print(f'   ✅ System overview: {summary_data["system_overview"]["total_courses"]} courses, {summary_data["system_overview"]["total_students"]} students')
    else:
        print(f'   ❌ Error: {summary_res.text}')

    # 2. Создаем тестовый курс для аналитики
    print('\n2. Creating test course for analytics...')
    unique_title = f'Analytics Test Course {uuid.uuid4().hex[:8]}'
    course_data = {
        'title': unique_title,
        'description': 'Test course for analytics testing',
        'start_date': '2024-01-01T00:00:00',
        'end_date': '2024-12-31T23:59:59',
        'owner_id': 1
    }
    
    course_res = requests.post('http://localhost:8000/api/courses/', json=course_data, headers=headers)
    if course_res.status_code == 201:
        course_id = course_res.json()['id']
        print(f'   ✅ Created course ID: {course_id}')
    else:
        print(f'   ❌ Error creating course: {course_res.text}')
        return

    # 3. Создаем тестовое задание
    print('\n3. Creating test assignment...')
    assignment_data = {
        'title': 'Analytics Test Assignment',
        'description': 'Test assignment for analytics',
        'course_id': course_id,
        'due_date': '2024-06-15T23:59:59'
    }
    
    assignment_res = requests.post('http://localhost:8000/api/assignments/', json=assignment_data, headers=headers)
    if assignment_res.status_code == 201:
        assignment_id = assignment_res.json()['id']
        print(f'   ✅ Created assignment ID: {assignment_id}')
    else:
        print(f'   ❌ Error creating assignment: {assignment_res.text}')
        return

    # 4. Тестируем аналитику курса
    print('\n4. Testing course overview analytics...')
    course_analytics_res = requests.get(f'http://localhost:8000/api/analytics/courses/{course_id}/overview', headers=headers)
    print(f'   Course overview: {course_analytics_res.status_code}')
    
    if course_analytics_res.status_code == 200:
        course_analytics = course_analytics_res.json()
        print(f'   ✅ Course analytics: {course_analytics["overview"]["assignments_count"]} assignments, {course_analytics["overview"]["students_count"]} students')
    else:
        print(f'   ❌ Error: {course_analytics_res.text}')

    # 5. Тестируем аналитику заданий курса
    print('\n5. Testing course assignments analytics...')
    assignments_analytics_res = requests.get(f'http://localhost:8000/api/analytics/courses/{course_id}/assignments', headers=headers)
    print(f'   Assignments analytics: {assignments_analytics_res.status_code}')
    
    if assignments_analytics_res.status_code == 200:
        assignments_analytics = assignments_analytics_res.json()
        print(f'   ✅ Assignments analytics: {len(assignments_analytics["assignments_analytics"])} assignments analyzed')
    else:
        print(f'   ❌ Error: {assignments_analytics_res.text}')

    # 6. Тестируем аналитику студента (если есть студенты в системе)
    print('\n6. Testing student performance analytics...')
    # Сначала получаем список студентов
    students_res = requests.get('http://localhost:8000/api/students/', headers=headers)
    if students_res.status_code == 200:
        students = students_res.json()
        if students:
            student_id = students[0]['id']
            student_analytics_res = requests.get(f'http://localhost:8000/api/analytics/students/{student_id}/performance', headers=headers)
            print(f'   Student performance: {student_analytics_res.status_code}')
            
            if student_analytics_res.status_code == 200:
                student_analytics = student_analytics_res.json()
                print(f'   ✅ Student analytics: {student_analytics["overall_performance"]["total_submissions"]} submissions')
            else:
                print(f'   ❌ Error: {student_analytics_res.text}')
        else:
            print('   ⚠️ No students found in system')
    else:
        print(f'   ❌ Error getting students: {students_res.text}')

    print('\n🎉 Analytics API test completed!')


if __name__ == '__main__':
    test_analytics_api()

