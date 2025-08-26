from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from enum import Enum as PyEnum


class LessonType(str, PyEnum):
    """Типы занятий."""
    LECTURE = "lecture"
    SEMINAR = "seminar"
    LABORATORY = "laboratory"
    PRACTICAL = "practical"
    EXAM = "exam"
    CONSULTATION = "consultation"
    OTHER = "other"


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
        lesson_type: Тип занятия (лекция, семинар, лаб. работа и т.д.)
        description: Описание занятия, тема
        notes: Дополнительные заметки
        is_cancelled: Отменено ли занятие
        created_at: Временная метка создания записи
        updated_at: Временная метка последнего обновления
    """
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    schedule_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(200), nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_type = Column(String(20), default="lecture", nullable=False)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_cancelled = Column(Integer, default=0, nullable=False)  # 0 = активно, 1 = отменено
    # Ссылка на аудиторию (опционально)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=True)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    course = relationship("Course", back_populates="schedules")
    instructor = relationship("User", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")


class Event(Base):
    """
    Модель событий и мероприятий.
    
    Дополнительные события, не связанные напрямую с расписанием занятий,
    такие как экзамены, конференции, мероприятия и т.д.
    
    Attributes:
        id: Уникальный идентификатор события
        title: Название события
        description: Описание события
        event_date: Дата события
        start_time: Время начала
        end_time: Время окончания
        location: Место проведения
        organizer_id: Организатор события
        is_public: Публичное ли событие
        created_at: Временная метка создания
        updated_at: Временная метка обновления
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(200), nullable=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Integer, default=1, nullable=False)  # 0 = приватное, 1 = публичное
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    organizer = relationship("User", foreign_keys=[organizer_id])


class Classroom(Base):
    """
    Модель аудиторий/классов.
    
    Описывает доступные аудитории для проведения занятий
    с их характеристиками и вместимостью.
    
    Attributes:
        id: Уникальный идентификатор аудитории
        name: Название/номер аудитории
        building: Здание
        floor: Этаж
        capacity: Вместимость
        equipment: Доступное оборудование
        is_available: Доступна ли аудитория
        created_at: Временная метка создания
        updated_at: Временная метка обновления
    """
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    building = Column(String(100), nullable=True)
    floor = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=True)
    equipment = Column(Text, nullable=True)  # JSON строка с оборудованием
    is_available = Column(Integer, default=1, nullable=False)  # 0 = недоступна, 1 = доступна
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Обратная связь с расписанием
    schedules = relationship("Schedule", back_populates="classroom")