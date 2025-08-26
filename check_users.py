#!/usr/bin/env python3
"""
Проверка пользователей в системе.
"""
import requests

def check_users():
    # Получаем токен
    token_data = {'username': 'admin@example.com', 'password': 'admin'}
    token_res = requests.post('http://localhost:8000/auth/token', data=token_data)
    
    if token_res.status_code != 200:
        print(f'Auth failed: {token_res.text}')
        return
    
    token = token_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Проверяем пользователей
    users_res = requests.get('http://localhost:8000/api/users/', headers=headers)
    if users_res.status_code == 200:
        users = users_res.json()
        print('Users in system:')
        for user in users:
            print(f'  ID: {user["id"]}, Username: {user["username"]}, Role: {user["role"]}')
    else:
        print(f'Error getting users: {users_res.text}')

if __name__ == '__main__':
    check_users()
