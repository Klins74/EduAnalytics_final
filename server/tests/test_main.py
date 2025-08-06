import pytest
import httpx

BASE_URL = "http://127.0.0.1:8000"

# Проверка, что сервер работает
@pytest.mark.asyncio
async def test_root():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/")
        assert response.status_code == 200

# Проверка получения токена
@pytest.mark.asyncio
async def test_get_token():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/token",
            data={"username": "admin@example.com", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

# Пример теста защищённого эндпоинта
@pytest.mark.asyncio
async def test_protected_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/auth/token",
            data={"username": "admin@example.com", "password": "admin"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        # Пример защищённого эндпоинта (замените на актуальный)
        response = await client.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 200

# Добавьте дополнительные тесты для других эндпоинтов по аналогии