import pytest
import requests

BASE_URL = "http://localhost:8000"
USERNAME = "admin@eduanalytics.ru"
PASSWORD = "admin123"

@pytest.fixture(scope="session")
def token():
    response = requests.post(
        "http://127.0.0.1:8000/auth/token",
        data={"username": "admin@example.com", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

def test_students(token):
    headers = {"Authorization": f"Bearer {token}"}
    student_data = {"name": "Test Student", "email": "test@student.com", "group_id": 1}

    # Create
    res = requests.post(f"{BASE_URL}/api/students/", json=student_data, headers=headers)
    assert res.status_code == 200, res.text
    student = res.json()

    # Get
    res = requests.get(f"{BASE_URL}/api/students/{student['id']}", headers=headers)
    assert res.status_code == 200

    # Update
    update_data = {"name": "Updated Student", "email": "updated@student.com", "group_id": 1}
    res = requests.put(f"{BASE_URL}/api/students/{student['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    # Delete
    res = requests.delete(f"{BASE_URL}/api/students/{student['id']}", headers=headers)
    assert res.status_code == 200

def test_groups(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"name": "Test Group"}

    res = requests.post(f"{BASE_URL}/api/groups/", json=data, headers=headers)
    assert res.status_code == 200
    group = res.json()

    res = requests.get(f"{BASE_URL}/api/groups/{group['id']}", headers=headers)
    assert res.status_code == 200

    update_data = {"name": "Updated Group"}
    res = requests.put(f"{BASE_URL}/api/groups/{group['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    res = requests.delete(f"{BASE_URL}/api/groups/{group['id']}", headers=headers)
    assert res.status_code == 200

def test_users(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"username": "newuser", "email": "user@test.com", "password": "123456"}

    res = requests.post(f"{BASE_URL}/api/users/", json=data, headers=headers)
    assert res.status_code == 200
    user = res.json()

    res = requests.get(f"{BASE_URL}/api/users/{user['id']}", headers=headers)
    assert res.status_code == 200

    update_data = {"username": "updateduser", "email": "user2@test.com", "password": "123456"}
    res = requests.put(f"{BASE_URL}/api/users/{user['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    res = requests.delete(f"{BASE_URL}/api/users/{user['id']}", headers=headers)
    assert res.status_code == 200

def test_grades(token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"student_id": 1, "subject": "Math", "grade": 90}

    res = requests.post(f"{BASE_URL}/api/grades/", json=data, headers=headers)
    assert res.status_code == 200
    grade = res.json()

    res = requests.get(f"{BASE_URL}/api/grades/{grade['id']}", headers=headers)
    assert res.status_code == 200

    update_data = {"student_id": 1, "subject": "Math", "grade": 95}
    res = requests.put(f"{BASE_URL}/api/grades/{grade['id']}", json=update_data, headers=headers)
    assert res.status_code == 200

    res = requests.delete(f"{BASE_URL}/api/grades/{grade['id']}", headers=headers)
    assert res.status_code == 200