from app.db.base import Base
from app.models.student import Student
from app.models.group import Group
from app.db.session import engine

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()