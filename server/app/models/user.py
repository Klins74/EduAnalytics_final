from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from enum import Enum

class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # Например: "admin", "student", "teacher"
    hashed_password = Column(String, nullable=False)
    
    # Relationships
    owned_courses = relationship("Course", back_populates="owner")
    schedules = relationship("Schedule", back_populates="instructor")
    gradebook_entries_as_student = relationship("GradebookEntry", foreign_keys="GradebookEntry.student_id", back_populates="student")
    gradebook_entries_as_creator = relationship("GradebookEntry", foreign_keys="GradebookEntry.created_by", back_populates="creator")
    gradebook_history_changes = relationship("GradebookHistory", back_populates="changed_by_user")
    reminder_settings = relationship("ReminderSettings", back_populates="user")
    created_quizzes = relationship("Quiz", back_populates="creator")