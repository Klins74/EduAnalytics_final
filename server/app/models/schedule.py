from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Schedule(Base):
    """
    Модель расписания занятий.
    
    Представляет расписание занятий для курсов с указанием времени,
    места проведения и преподавателя.
    
    Attributes:
        id: Уникальный идентификатор записи расписания
        course_id: ID курса (связь с таблицей courses)
        schedule_date: Дата проведения занятия
        start_time: Время начала занятия
        end_time: Время окончания занятия
        location: Место проведения занятия (аудитория, онлайн и т.д.)
        instructor_id: ID преподавателя (связь с таблицей users)
        created_at: Временная метка создания записи
        updated_at: Временная метка последнего обновления
    """
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    schedule_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    course = relationship("Course", back_populates="schedules")
    instructor = relationship("User", back_populates="schedules")