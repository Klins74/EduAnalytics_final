from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum
from datetime import datetime


class OperationType(enum.Enum):
    """Типы операций для audit trail."""
    create = "create"
    update = "update"
    delete = "delete"


class GradebookEntry(Base):
    """Модель записи в электронном журнале.
    
    Хранит оценки студентов по курсам и заданиям.
    Поддерживает как оценки за конкретные задания, так и общие оценки по курсу.
    """
    __tablename__ = "gradebook_entries"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=True, index=True)
    grade_value = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="gradebook_entries")
    student = relationship("User", foreign_keys=[student_id], back_populates="gradebook_entries_as_student")
    assignment = relationship("Assignment", back_populates="gradebook_entries")
    creator = relationship("User", foreign_keys=[created_by], back_populates="gradebook_entries_as_creator")
    history = relationship("GradebookHistory", back_populates="entry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GradebookEntry(id={self.id}, student_id={self.student_id}, grade={self.grade_value})>"


class GradebookHistory(Base):
    """Модель истории изменений записей в электронном журнале.
    
    Audit trail для отслеживания всех изменений оценок.
    """
    __tablename__ = "gradebook_history"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("gradebook_entries.id"), nullable=False, index=True)
    course_id = Column(Integer, nullable=False)
    student_id = Column(Integer, nullable=False)
    assignment_id = Column(Integer, nullable=True)
    grade_value = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    operation = Column(SQLEnum(OperationType), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    entry = relationship("GradebookEntry", back_populates="history")
    changed_by_user = relationship("User", back_populates="gradebook_history_changes")

    def __repr__(self):
        return f"<GradebookHistory(id={self.id}, entry_id={self.entry_id}, operation={self.operation.value})>"