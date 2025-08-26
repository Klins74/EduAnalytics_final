#!/usr/bin/env python3
"""
Тест Submissions API для проверки функциональности.
"""
import requests
import json
import uuid
from datetime import datetime, timedelta

def test_submissions_api():
    # Получаем токен для admin
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)
    
    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return
    
    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    print('🧪 Testing Submissions API...')
    
    # Сначала создаем курс и задание
    print('1. Creating course and assignment...')
    course_data = {
        'title': f'Course for Submissions Test {uuid.uuid4().hex[:8]}',
        'description': 'Test course for submissions',
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
    
    # Создаем задание
    assignment_data = {
        'title': 'Test Assignment for Submissions',
        'description': 'This is a test assignment for submissions',
        'course_id': course_id,
        'due_date': '2024-06-15T23:59:59'
    }
    
    assignment_res = requests.post('http://localhost:8000/api/assignments/', json=assignment_data, headers=headers)
    if assignment_res.status_code != 201:
        print(f'   ❌ Failed to create assignment: {assignment_res.text}')
        return
    
    assignment = assignment_res.json()
    assignment_id = assignment['id']
    print(f'   ✅ Created assignment ID: {assignment_id}')
    
    # Тестируем создание сдачи
    print('2. Creating submission...')
    submission_data = {
        'content': 'This is my submission content for the test assignment',
        'assignment_id': assignment_id
    }
    
    create_res = requests.post('http://localhost:8000/api/submissions/', json=submission_data, headers=headers)
    print(f'   Create submission: {create_res.status_code}')
    
    if create_res.status_code == 201:
        submission = create_res.json()
        submission_id = submission['id']
        print(f'   ✅ Created submission ID: {submission_id}')
        
        # Тестируем получение сдачи
        print('3. Getting submission...')
        get_res = requests.get(f'http://localhost:8000/api/submissions/{submission_id}', headers=headers)
        print(f'   Get submission: {get_res.status_code}')
        if get_res.status_code == 200:
            print('   ✅ Submission retrieved successfully')
        
        # Тестируем список сдач
        print('4. Getting submissions list...')
        list_res = requests.get('http://localhost:8000/api/submissions/', headers=headers)
        print(f'   List submissions: {list_res.status_code}')
        if list_res.status_code == 200:
            submissions_data = list_res.json()
            total = submissions_data.get('total', 0)
            print(f'   ✅ Total submissions: {total}')
        
        # Тестируем фильтрацию по заданию
        print('5. Getting submissions by assignment...')
        assignment_filter_res = requests.get(f'http://localhost:8000/api/submissions/?assignment_id={assignment_id}', headers=headers)
        print(f'   Filter by assignment: {assignment_filter_res.status_code}')
        if assignment_filter_res.status_code == 200:
            filtered_data = assignment_filter_res.json()
            print(f'   ✅ Assignment submissions: {filtered_data.get("total", 0)}')
        
        # Тестируем обновление сдачи
        print('6. Updating submission...')
        update_data = {'content': 'Updated submission content'}
        update_res = requests.put(f'http://localhost:8000/api/submissions/{submission_id}', json=update_data, headers=headers)
        print(f'   Update submission: {update_res.status_code}')
        if update_res.status_code == 200:
            print('   ✅ Submission updated successfully')
        
        # Тестируем выставление оценки
        print('7. Creating grade for submission...')
        grade_data = {
            'score': 85,
            'feedback': 'Good work! Keep it up.',
            'graded_by': 1,
            'submission_id': submission_id
        }
        
        grade_res = requests.post(f'http://localhost:8000/api/submissions/{submission_id}/grade', json=grade_data, headers=headers)
        print(f'   Create grade: {grade_res.status_code}')
        if grade_res.status_code == 201:
            grade = grade_res.json()
            print(f'   ✅ Grade created: {grade["score"]}/100')
        
        # Тестируем загрузку файла (создаем тестовый файл)
        print('8. Testing file upload...')
        test_file_content = b'This is a test file content for submission'
        files = {'file': ('test_submission.txt', test_file_content, 'text/plain')}
        
        upload_res = requests.post(
            f'http://localhost:8000/api/submissions/{submission_id}/upload',
            files=files,
            headers=headers
        )
        print(f'   File upload: {upload_res.status_code}')
        if upload_res.status_code == 200:
            upload_result = upload_res.json()
            print(f'   ✅ File uploaded: {upload_result["file_name"]}')
        
        print('\n🎉 Submissions API test completed!')
        
    else:
        print(f'   ❌ Error creating submission: {create_res.text}')

if __name__ == '__main__':
    test_submissions_api()
