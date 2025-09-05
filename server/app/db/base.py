from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all model modules so Alembic can detect them
from app.models import user, group, student, grade, gradebook, feedback
# Ensure related models are registered for relationship() resolution
from app.models import user_preferences  # registers UserPreferences
from app.models import course, assignment, submission  # common core models used in tests