import os
import sys
import json
import datetime
import requests

API = os.environ.get('API_URL', 'http://localhost:8000')
FRONTEND = os.environ.get('FRONTEND_URL', 'http://localhost:4028')
USERNAME = os.environ.get('TEST_USERNAME', 'admin@example.com')
PASSWORD = os.environ.get('TEST_PASSWORD', 'admin')

session = requests.Session()
session.headers.update({'Accept': 'application/json'})

results = {}

def log(name, ok, info=None):
    results[name] = {
        'ok': bool(ok),
        'info': info or ''
    }
    status = 'OK' if ok else 'FAIL'
    print(f"[{status}] {name}: {info or ''}")


def get(url, **kwargs):
    return session.get(url, timeout=30, **kwargs)

def post(url, **kwargs):
    return session.post(url, timeout=30, **kwargs)


def test_frontend_pages():
    pages = [
        f"{FRONTEND}/test-schedule.html",
        f"{FRONTEND}/test-dashboards.html",
    ]
    for url in pages:
        try:
            r = requests.get(url, timeout=15)
            log(f"Page {url}", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            log(f"Page {url}", False, str(e))


def login():
    url = f"{API}/api/auth/token"
    try:
        r = post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data={
            'username': USERNAME,
            'password': PASSWORD
        })
        if r.status_code != 200:
            log('Login', False, f"HTTP {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        token = data.get('access_token')
        if not token:
            log('Login', False, 'No access_token in response')
            return None
        session.headers['Authorization'] = f"Bearer {token}"
        log('Login', True, 'Token acquired')
        return token
    except Exception as e:
        log('Login', False, str(e))
        return None


def test_courses():
    url = f"{API}/api/courses/"
    try:
        r = get(url)
        if r.status_code != 200:
            log('Courses API', False, f"HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        courses = data.get('courses') if isinstance(data, dict) else data
        courses = courses or []
        log('Courses API', True, f"count={len(courses)}")
        return courses
    except Exception as e:
        log('Courses API', False, str(e))
        return []


def test_users():
    url = f"{API}/api/users/"
    try:
        r = get(url)
        if r.status_code != 200:
            log('Users API', False, f"HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        users = data if isinstance(data, list) else data.get('users', [])
        log('Users API', True, f"count={len(users)}")
        return users
    except Exception as e:
        log('Users API', False, str(e))
        return []


def test_schedule_list():
    url = f"{API}/api/schedule"
    try:
        r = get(url)
        if r.status_code != 200:
            log('Schedule List', False, f"HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
        schedules = data.get('schedules', [])
        log('Schedule List', True, f"count={len(schedules)}")
        return schedules
    except Exception as e:
        log('Schedule List', False, str(e))
        return []


def test_schedule_create(courses, users):
    # Pick sample course and teacher
    course_id = courses[0]['id'] if courses else 1
    teacher_id = None
    for u in users:
        role = (u.get('role') or '').lower()
        if role in ('teacher', 'admin'):
            teacher_id = u.get('id')
            break
    if teacher_id is None:
        teacher_id = 1

    # Try multiple candidate time slots for tomorrow to avoid conflicts
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    candidate_slots = [
        ("17:00", "18:30"),
        ("19:00", "20:30"),
        ("15:00", "16:30"),
    ]

    url = f"{API}/api/schedule/"
    for start_time, end_time in candidate_slots:
        payload = {
            'course_id': int(course_id),
            'instructor_id': int(teacher_id),
            'schedule_date': tomorrow,
            'start_time': start_time,
            'end_time': end_time,
            'location': 'Аудитория 101',
            'lesson_type': 'lecture',
            'description': 'Тестовое занятие',
            'notes': 'Создано автотестом'
        }
        try:
            r = post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
            if r.status_code == 200:
                data = r.json()
                log('Schedule Create', True, f"id={data.get('id')} {tomorrow} {start_time}-{end_time}")
                return data
            else:
                # keep trying next slot
                continue
        except Exception:
            continue
    log('Schedule Create', False, "Нет свободного слота из предложенных")
    return None


def test_teacher_analytics():
    url = f"{API}/api/analytics/teacher/1/overview"
    try:
        r = get(url)
        log('Teacher Analytics', r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        log('Teacher Analytics', False, str(e))


def test_student_performance():
    url = f"{API}/api/analytics/students/1/performance"
    try:
        r = get(url)
        log('Student Performance', r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        log('Student Performance', False, str(e))


def test_ai_chat():
    url = f"{API}/api/ai/chat"
    try:
        r = post(url, headers={'Content-Type': 'application/json'}, data=json.dumps({'message': 'Привет, как дела?'}))
        log('AI Chat', r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        log('AI Chat', False, str(e))


def main():
    print('=== Frontend pages ===')
    test_frontend_pages()

    print('\n=== API auth ===')
    token = login()
    if not token:
        print('\nRESULT: FAILED (auth)')
        sys.exit(1)

    print('\n=== Basic APIs ===')
    courses = test_courses()
    users = test_users()
    schedules = test_schedule_list()

    print('\n=== Schedule create ===')
    created = test_schedule_create(courses, users)

    print('\n=== Analytics APIs ===')
    test_teacher_analytics()
    test_student_performance()

    print('\n=== AI API ===')
    test_ai_chat()

    ok_count = sum(1 for v in results.values() if v['ok'])
    total = len(results)
    print(f"\nRESULT: {ok_count}/{total} OK")
    # Exit non-zero if any critical fail
    critical = ['Login', 'Courses API', 'Users API', 'Schedule List']
    if any(not results.get(k, {}).get('ok') for k in critical):
        sys.exit(2)


if __name__ == '__main__':
    main()
