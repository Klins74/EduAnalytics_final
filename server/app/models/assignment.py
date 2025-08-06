from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.db.base import Base


class Assignment(Base):
    """
    Модель задания в рамках курса.
    
    Задание представляет собой учебную работу, которую студенты должны выполнить
    в рамках определенного курса. Каждое задание имеет дедлайн и связано с конкретным курсом.
    Задания могут иметь различные типы (домашнее задание, лабораторная работа, проект и т.д.).
    
    Связь с курсом: каждое задание принадлежит одному курсу (course_id),
    и дедлайн задания должен находиться в пределах периода проведения курса.
    
    Attributes:
        id: Уникальный идентификатор задания
        title: Название задания
        description: Подробное описание задания и требований
        due_date: Дедлайн сдачи задания
        course_id: ID курса, к которому относится задание
        created_at: Временная метка создания задания
        updated_at: Временная метка последнего обновления
    """
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    
    # course_id - связь с таблицей курсов
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    course = relationship("Course", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")
    gradebook_entries = relationship("GradebookEntry", back_populates="assignment", cascade="all, delete-orphan")
    
    @validates('due_date')
    def validate_due_date(self, key, due_date):
        """
        Валидация дедлайна: должен быть в пределах периода курса.
        Проверка выполняется на уровне ORM при установке значения.
        """
        if self.course:
            if due_date < self.course.start_date or due_date > self.course.end_date:
                raise ValueError(
                    f"Дедлайн задания должен быть в пределах курса "
                    f"({self.course.start_date} - {self.course.end_date})"
                )
        return due_date