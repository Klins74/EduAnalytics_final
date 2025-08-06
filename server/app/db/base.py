from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Import all model modules so Alembic can detect them
from app.models import user, group, student, grade, gradebook, feedback