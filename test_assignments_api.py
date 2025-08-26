#!/usr/bin/env python3
"""
Тест Assignments API для проверки функциональности.
"""
import requests
import json
from datetime import datetime, timedelta

def test_assignments_api():
    # Получаем токен
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)
    
    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return
    
    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print('🧪 Testing Assignments API...')
    
    # Сначала создаем курс для заданий
    print('1. Creating course for assignments...')
    import uuid
    unique_title = f'Course for Assignments Test {uuid.uuid4().hex[:8]}'
    course_data = {
        'title': unique_title,
        'description': 'Test course for assignments',
        'start_date': '2024-01-01T00:00:00',
        'end_date': '2024-12-31T23:59:59',
        'owner_id': 1
    }
    
    course_res = requests.post('http://localhost:8000/api/courses/', json=course_data, headers=headers)
    if course_res.status_code != 201:
        print(f'   ❌ Failed to create course: {course_res.text}')
        return
    
    course = course_res.json()
    course_id = course['id']
    print(f'   ✅ Created course ID: {course_id}')
    
    # Тестируем создание задания
    print('2. Creating assignment...')
    assignment_data = {
        'title': 'Test Assignment',
        'description': 'This is a test assignment',
        'course_id': course_id,
        'due_date': '2024-06-15T23:59:59'
    }
    
    create_res = requests.post(
        'http://localhost:8000/api/assignments/', 
        json=assignment_data, 
        headers=headers
    )
    print(f'   Create assignment: {create_res.status_code}')
    
    if create_res.status_code == 201:
        assignment = create_res.json()
        assignment_id = assignment['id']
        print(f'   ✅ Created assignment ID: {assignment_id}')
        
        # Тестируем получение задания
        print('3. Getting assignment...')
        get_res = requests.get(f'http://localhost:8000/api/assignments/{assignment_id}', headers=headers)
        print(f'   Get assignment: {get_res.status_code}')
        if get_res.status_code == 200:
            print('   ✅ Assignment retrieved successfully')
        
        # Тестируем список заданий
        print('4. Getting assignments list...')
        list_res = requests.get('http://localhost:8000/api/assignments/', headers=headers)
        print(f'   List assignments: {list_res.status_code}')
        if list_res.status_code == 200:
            assignments_data = list_res.json()
            total = assignments_data.get('total', 0)
            print(f'   ✅ Total assignments: {total}')
        
        # Тестируем фильтрацию по курсу
        print('5. Getting assignments by course...')
        course_filter_res = requests.get(f'http://localhost:8000/api/assignments/?course_id={course_id}', headers=headers)
        print(f'   Filter by course: {course_filter_res.status_code}')
        if course_filter_res.status_code == 200:
            filtered_data = course_filter_res.json()
            print(f'   ✅ Course assignments: {filtered_data.get("total", 0)}')
        
        # Тестируем обновление задания
        print('6. Updating assignment...')
        update_data = {'description': 'Updated assignment description'}
        update_res = requests.put(f'http://localhost:8000/api/assignments/{assignment_id}', json=update_data, headers=headers)
        print(f'   Update assignment: {update_res.status_code}')
        if update_res.status_code == 200:
            print('   ✅ Assignment updated successfully')
        
        # Тестируем задания курса через courses API
        print('7. Getting course assignments via courses API...')
        course_assignments_res = requests.get(f'http://localhost:8000/api/courses/{course_id}/assignments', headers=headers)
        print(f'   Course assignments: {course_assignments_res.status_code}')
        if course_assignments_res.status_code == 200:
            course_assignments = course_assignments_res.json()
            assignments_count = len(course_assignments.get('assignments', []))
            print(f'   ✅ Course has {assignments_count} assignments')
        
        print('\n🎉 Assignments API test completed!')
        
    else:
        print(f'   ❌ Error creating assignment: {create_res.text}')

if __name__ == '__main__':
    test_assignments_api()
