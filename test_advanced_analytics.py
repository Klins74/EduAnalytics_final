#!/usr/bin/env python3
"""
Тест Advanced Analytics API: тренды и прогноз.
"""
import requests
import json

BASE = 'http://localhost:8000'
API = f'{BASE}/api'
AN = f'{API}/analytics'


def get_token():
    r = requests.post(f'{BASE}/auth/token', data={'username': 'admin@example.com', 'password': 'admin'})
    r.raise_for_status()
    return r.json()['access_token']


def print_json(title, data, limit=None):
    print(title)
    if limit is not None and isinstance(data, list):
        print(json.dumps(data[:limit], indent=2, ensure_ascii=False, default=str))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def main():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    print('⚙️ Testing Advanced Analytics API...')

    # Student trends
    print('\n1) GET /api/analytics/students/1/trends')
    r = requests.get(f'{AN}/students/1/trends', params={'days': 30, 'bucket': 'week'}, headers=headers)
    print(f'   Status: {r.status_code}')
    if r.ok:
        data = r.json()
        print(f"   ✅ Points: {len(data.get('series', []))}")
        if data.get('series'):
            print_json('   Sample point:', data['series'][0])
    else:
        print(f'   ❌ Error: {r.text}')

    # Student forecast
    print('\n2) GET /api/analytics/predict/performance?scope=student&target_id=1')
    r = requests.get(f'{AN}/predict/performance', params={'scope': 'student', 'target_id': 1, 'horizon_days': 14, 'bucket': 'day'}, headers=headers)
    print(f'   Status: {r.status_code}')
    if r.ok:
        data = r.json()
        print(f"   ✅ Forecast points: {len(data.get('forecast', []))}")
        if data.get('forecast'):
            print_json('   Sample forecast:', data['forecast'][0])
    else:
        print(f'   ❌ Error: {r.text}')

    # Try to fetch a course for trends
    print('\n3) Try course trends on the first available course')
    cr = requests.get(f'{API}/courses/', headers=headers)
    if cr.ok:
        courses = cr.json().get('courses') or []
        if courses:
            course_id = courses[0]['id']
            print(f'   Using course_id={course_id}')
            r = requests.get(f'{AN}/courses/{course_id}/trends', params={'days': 30, 'bucket': 'week'}, headers=headers)
            print(f'   Trends status: {r.status_code}')
            if r.ok:
                data = r.json()
                print(f"   ✅ Points: {len(data.get('series', []))}")
            else:
                print(f'   ❌ Error: {r.text}')

            r = requests.get(f'{AN}/predict/performance', params={'scope': 'course', 'target_id': course_id, 'horizon_days': 14, 'bucket': 'day'}, headers=headers)
            print(f'   Forecast status: {r.status_code}')
            if r.ok:
                data = r.json()
                print(f"   ✅ Forecast points: {len(data.get('forecast', []))}")
            else:
                print(f'   ❌ Error: {r.text}')
        else:
            print('   ⚠️ No courses available to test course trends')
    else:
        print('   ⚠️ Unable to fetch courses list')

    print('\n🎉 Advanced Analytics API tests completed!')


if __name__ == '__main__':
    main()

