#!/usr/bin/env python3
"""
Тест Courses API для проверки функциональности.
"""
import requests
import json

def test_courses_api():
    # Получаем токен
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)
    
    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return
    
    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Тестируем создание курса
    course_data = {
        'title': 'Test Course API 2024',
        'description': 'Test course for API testing',
        'start_date': '2024-01-01T00:00:00',
        'end_date': '2024-12-31T23:59:59',
        'owner_id': 1
    }
    
    print('🧪 Testing Courses API...')
    print('1. Creating course...')
    res = requests.post('http://localhost:8000/api/courses/', json=course_data, headers=headers)
    print(f'   Create course: {res.status_code}')
    
    if res.status_code == 201:
        course = res.json()
        course_id = course['id']
        print(f'   ✅ Created course ID: {course_id}')
        
        # Тестируем получение курса
        print('2. Getting course...')
        get_res = requests.get(f'http://localhost:8000/api/courses/{course_id}', headers=headers)
        print(f'   Get course: {get_res.status_code}')
        if get_res.status_code == 200:
            print('   ✅ Course retrieved successfully')
        
        # Тестируем список курсов
        print('3. Getting courses list...')
        list_res = requests.get('http://localhost:8000/api/courses/', headers=headers)
        print(f'   List courses: {list_res.status_code}')
        if list_res.status_code == 200:
            courses_data = list_res.json()
            total = courses_data.get('total', 0)
            print(f'   ✅ Total courses: {total}')
        
        # Тестируем аналитику курса
        print('4. Getting course analytics...')
        analytics_res = requests.get(f'http://localhost:8000/api/courses/{course_id}/analytics', headers=headers)
        print(f'   Course analytics: {analytics_res.status_code}')
        if analytics_res.status_code == 200:
            analytics = analytics_res.json()
            print(f'   ✅ Analytics: {analytics["course_title"]} - {analytics["students_count"]} students')
        
        # Тестируем задания курса
        print('5. Getting course assignments...')
        assignments_res = requests.get(f'http://localhost:8000/api/courses/{course_id}/assignments', headers=headers)
        print(f'   Course assignments: {assignments_res.status_code}')
        if assignments_res.status_code == 200:
            assignments = assignments_res.json()
            print(f'   ✅ Assignments: {len(assignments.get("assignments", []))} items')
        
        # Тестируем обновление курса
        print('6. Updating course...')
        update_data = {'description': 'Updated description'}
        update_res = requests.put(f'http://localhost:8000/api/courses/{course_id}', json=update_data, headers=headers)
        print(f'   Update course: {update_res.status_code}')
        if update_res.status_code == 200:
            print('   ✅ Course updated successfully')
        
        print('\n🎉 Courses API test completed!')
        
    else:
        print(f'   ❌ Error creating course: {res.text}')

if __name__ == '__main__':
    test_courses_api()
