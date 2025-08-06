import pytest
import requests
import uuid # Импортируем для уникальных имен

BASE_URL = "http://localhost:8000"
USERNAME = "admin@eduanalytics.ru"
PASSWORD = "admin123"

@pytest.fixture(scope="session")
def token():
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": "admin@example.com", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_students(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # Сначала создаем группу для студента
    group_data = {"name": f"Test Group for Student {uuid.uuid4()}"}
    res = requests.post(f"{BASE_URL}/api/groups", json=group_data, headers=headers)
    assert res.status_code == 201, res.text
    group = res.json()
    
    # ИСПРАВЛЕНО: Добавлено обязательное поле email и используем существующий group_id
    unique_email = f"student_{uuid.uuid4()}@test.com"
    student_data = {"full_name": "Test Student", "email": unique_email, "group_id": group['id']}

    # Create
    res = requests.post(f"{BASE_URL}/api/students", json=student_data, headers=headers)
    assert res.status_code == 201, res.text
    student = res.json()

    # Get
    res = requests.get(f"{BASE_URL}/api/students/{student['id']}", headers=headers)
    assert res.status_code == 200

    # Update
    update_email = f"updated_student_{uuid.uuid4()}@test.com"
    update_data = {"full_name": "Updated Student", "email": update_email, "group_id": group['id']}
    res = requests.put(f"{BASE_URL}/api/students/{student['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    # Delete student
    res = requests.delete(f"{BASE_URL}/api/students/{student['id']}", headers=headers)
    assert res.status_code == 204
    
    # Delete group
    res = requests.delete(f"{BASE_URL}/api/groups/{group['id']}", headers=headers)
    assert res.status_code == 204

def test_groups(token):
    headers = {"Authorization": f"Bearer {token}"}
    # Используем уникальное имя, чтобы избежать конфликтов при повторных запусках
    unique_name = f"API Test Group {uuid.uuid4()}"
    group_data = {"name": unique_name} 

    # Create
    res = requests.post(f"{BASE_URL}/api/groups", json=group_data, headers=headers)
    assert res.status_code == 201, res.text
    group = res.json()

    # Get
    res = requests.get(f"{BASE_URL}/api/groups/{group['id']}", headers=headers)
    assert res.status_code == 200

    # Update
    update_data = {"name": f"Updated Group {uuid.uuid4()}"}
    res = requests.put(f"{BASE_URL}/api/groups/{group['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    # Delete
    res = requests.delete(f"{BASE_URL}/api/groups/{group['id']}", headers=headers)
    assert res.status_code == 204

def test_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    # ИСПРАВЛЕНО: Добавлено обязательное поле username
    unique_username = f"newuser_{uuid.uuid4()}"
    data = {"username": unique_username, "password": "123456", "role": "teacher"}

    res = requests.post(f"{BASE_URL}/api/users", json=data, headers=headers)
    assert res.status_code == 201, res.text
    user = res.json()

    res = requests.get(f"{BASE_URL}/api/users/{user['id']}", headers=headers)
    assert res.status_code == 200

    update_data = {"username": f"updated_{unique_username}", "role": "student"}
    res = requests.put(f"{BASE_URL}/api/users/{user['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    res = requests.delete(f"{BASE_URL}/api/users/{user['id']}", headers=headers)
    assert res.status_code == 204

def test_grades(token):
    headers = {"Authorization": f"Bearer {token}"}
    # ИСПРАВЛЕНО: Данные соответствуют схеме GradeCreate (value, subject)
    data = {"student_id": 1, "value": 5, "subject": 1}

    # Create
    res = requests.post(f"{BASE_URL}/api/grades", json=data, headers=headers)
    # ИСПРАВЛЕНО: Ожидаемый статус для создания - 201
    assert res.status_code == 201, res.text
    grade = res.json()

    # Get
    res = requests.get(f"{BASE_URL}/api/grades/{grade['id']}", headers=headers)
    assert res.status_code == 200

    # Update
    # ИСПРАВЛЕНО: Данные для обновления также должны соответствовать схеме
    update_data = {"student_id": 1, "value": 4, "subject": 1}
    res = requests.put(f"{BASE_URL}/api/grades/{grade['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    # Delete
    res = requests.delete(f"{BASE_URL}/api/grades/{grade['id']}", headers=headers)
    # ИСПРАВЛЕНО: Ожидаемый статус для успешного удаления - 204
    assert res.status_code == 204