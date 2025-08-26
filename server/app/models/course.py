from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Course(Base):
    """
    Модель курса в системе образовательной аналитики.
    
    Курс представляет собой учебную дисциплину, которую ведет преподаватель.
    Каждый курс имеет определенный период проведения (start_date - end_date)
    и может содержать множество заданий и студентов.
    
    Attributes:
        id: Уникальный идентификатор курса
        title: Название курса
        description: Описание курса и его содержания
        start_date: Дата начала курса
        end_date: Дата окончания курса
        owner_id: ID преподавателя, ведущего курс (связь с таблицей users)
        created_at: Временная метка создания записи в системе
        updated_at: Временная метка последнего обновления записи
    """
    __tablename__ = "courses"
    
    # Валидация: дата начала должна быть меньше или равна дате окончания
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='check_course_dates'),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, unique=True, index=True)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # owner_id - связь с таблицей пользователей, указывает на преподавателя курса
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # created_at - автоматически устанавливается при создании записи
    # используется для аудита и отслеживания времени создания курса
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # updated_at - автоматически обновляется при изменении записи
    # позволяет отслеживать последние изменения в курсе
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    owner = relationship("User", back_populates="owned_courses")
    schedules = relationship("Schedule", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    gradebook_entries = relationship("GradebookEntry", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course")
    # Canvas-like additions
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    assignment_groups = relationship("AssignmentGroup", back_populates="course", cascade="all, delete-orphan")
    rubrics = relationship("Rubric", back_populates="course", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="course", cascade="all, delete-orphan")
    discussion_topics = relationship("DiscussionTopic", back_populates="course", cascade="all, delete-orphan")
    # enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")  # TODO: Create Enrollment model