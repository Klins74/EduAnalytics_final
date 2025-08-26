from typing import Optional


# Простая централизованная проверка прав для AI-инструментов

_ROLE_PERMISSIONS = {
    "admin": {
        "read_course_analytics": True,
        "read_student_analytics": True,
        "read_schedule": True,
        "create_schedule": True,
    },
    "teacher": {
        "read_course_analytics": True,
        "read_student_analytics": True,  # ограничение на чужих студентов применяется снаружи
        "read_schedule": True,
        "create_schedule": True,
    },
    "student": {
        "read_course_analytics": False,
        "read_student_analytics": True,  # только свои данные (валидируется на уровне API)
        "read_schedule": True,
        "create_schedule": False,
    },
    None: {  # гость/неопределено
        "read_course_analytics": False,
        "read_student_analytics": False,
        "read_schedule": False,
        "create_schedule": False,
    },
}


def is_allowed(role: Optional[str], action: str) -> bool:
    role_key = (role or None)
    perms = _ROLE_PERMISSIONS.get(role_key) or _ROLE_PERMISSIONS[None]
    return bool(perms.get(action, False))


