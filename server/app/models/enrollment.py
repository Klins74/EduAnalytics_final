from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from enum import Enum


class EnrollmentRole(str, Enum):
    """Роли пользователя в курсе"""
    student = "student"
    teacher = "teacher" 
    ta = "ta"  # teaching assistant
    observer = "observer"
    designer = "designer"


class EnrollmentStatus(str, Enum):
    """Статусы записи на курс"""
    active = "active"
    inactive = "inactive"
    completed = "completed"
    dropped = "dropped"


class Enrollment(Base):
    """
    Модель записи пользователя на курс.
    Определяет роль пользователя в конкретном курсе и статус участия.
    """
    __tablename__ = "enrollments"
    
    # Уникальность: один пользователь может иметь только одну активную роль в курсе
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', 'role', name='unique_user_course_role'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Связи
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    
    # Роль и статус
    role = Column(String, nullable=False, default=EnrollmentRole.student)
    status = Column(String, nullable=False, default=EnrollmentStatus.active)
    
    # Метаданные
    enrolled_at = Column(DateTime, default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    dropped_at = Column(DateTime, nullable=True)
    
    # Дополнительные поля
    grade_override = Column(String, nullable=True)  # Переопределение итоговой оценки
    is_admin = Column(Boolean, default=False)  # Админские права в курсе
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    
    def __repr__(self):
        return f"<Enrollment(user_id={self.user_id}, course_id={self.course_id}, role={self.role}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Проверка активности записи"""
        return self.status == EnrollmentStatus.active
    
    @property
    def is_student(self) -> bool:
        """Проверка роли студента"""
        return self.role == EnrollmentRole.student
    
    @property
    def is_teacher(self) -> bool:
        """Проверка роли преподавателя"""
        return self.role == EnrollmentRole.teacher
    
    @property
    def can_grade(self) -> bool:
        """Может ли пользователь выставлять оценки"""
        return self.role in [EnrollmentRole.teacher, EnrollmentRole.ta]
    
    @property
    def can_view_all_grades(self) -> bool:
        """Может ли пользователь видеть все оценки в курсе"""
        return self.role in [EnrollmentRole.teacher, EnrollmentRole.ta, EnrollmentRole.observer]

