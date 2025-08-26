import requests
import json

BASE_URL = "http://localhost:8000"

def test_course_api():
    # 1. Получить токен админа
    print("1. Получаю токен админа...")
    response = requests.post(
        f"{BASE_URL}/api/auth/token",
        data={"username": "admin@example.com", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print("Ошибка получения токена")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Получить информацию о текущем пользователе
    print("\n2. Получаю информацию о пользователе...")
    response = requests.get(f"{BASE_URL}/api/users/me", headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print("Ошибка получения информации о пользователе")
        return
    
    admin_user = response.json()
    print(f"Admin user ID: {admin_user['id']}")
    
    # 3. Попробовать создать курс
    print("\n3. Создаю курс...")
    course_payload = {
        "title": "Test Course",
        "description": "Test course description",
        "start_date": "2025-01-01T00:00:00",
        "end_date": "2025-12-31T23:59:59",
        "owner_id": admin_user["id"],
    }
    
    print(f"Course payload: {json.dumps(course_payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/courses/", 
        json=course_payload, 
        headers=headers, 
        timeout=30
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_course_api()

