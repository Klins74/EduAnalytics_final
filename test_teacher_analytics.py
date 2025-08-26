#!/usr/bin/env python3
"""
Тест Teacher Analytics API для проверки функциональности аналитики преподавателя.
"""
import requests
import json

def test_teacher_analytics():
    """Тестирует эндпоинт Teacher Analytics API."""
    
    # Получаем токен для admin
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)

    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return

    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    print('👨‍🏫 Testing Teacher Analytics API...')

    # Тестируем обзор преподавателя
    print('\n1. Testing teacher overview...')
    teacher_id = 1  # admin user
    teacher_res = requests.get(f'http://localhost:8000/api/analytics/teacher/{teacher_id}/overview', headers=headers)
    print(f'   Teacher overview: {teacher_res.status_code}')
    
    if teacher_res.status_code == 200:
        teacher_data = teacher_res.json()
        print(f'   ✅ Teacher analytics: {teacher_data["overview"]["total_courses"]} courses, {teacher_data["overview"]["total_assignments"]} assignments')
        print(f'   📊 Pending submissions: {teacher_data["overview"]["pending_submissions"]}')
        print(f'   📈 Average grade: {teacher_data["overview"]["average_grade"]}%')
        
        if teacher_data["courses"]:
            print(f'   📚 Courses: {len(teacher_data["courses"])} found')
            for course in teacher_data["courses"][:3]:  # Показываем первые 3
                print(f'      - {course["title"]}')
        else:
            print('   ⚠️ No courses found for teacher')
    else:
        print(f'   ❌ Error: {teacher_res.text}')

    print('\n🎉 Teacher Analytics API test completed!')


if __name__ == '__main__':
    test_teacher_analytics()

