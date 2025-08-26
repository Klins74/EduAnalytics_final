from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from enum import Enum
from app.db.base import Base


class SubmissionStatus(str, Enum):
    """Статусы сдачи задания."""
    submitted = "submitted"  # Сдано вовремя
    late = "late"  # Сдано с опозданием
    graded = "graded"  # Оценено


class Submission(Base):
    """
    Модель сдачи задания студентом.
    
    Представляет собой работу, которую студент сдает в рамках выполнения задания.
    Содержит информацию о содержании работы, времени сдачи и статусе.
    
    Содержание (content) может быть:
    - Текстовым ответом (для коротких заданий)
    - URL ссылкой на файл или репозиторий (для больших проектов)
    - Комбинацией текста и ссылок
    
    Валидация времени сдачи:
    - Если submitted_at <= assignment.due_date - статус "submitted"
    - Если submitted_at > assignment.due_date - статус "late"
    
    Attributes:
        id: Уникальный идентификатор сдачи
        content: Содержание работы (текст или URL)
        submitted_at: Время сдачи работы
        status: Статус сдачи (вовремя/с опозданием/оценено)
        student_id: ID студента, сдавшего работу
        assignment_id: ID задания, к которому относится сдача
        created_at: Время создания записи
        updated_at: Время последнего обновления
    """
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.submitted, nullable=False)
    
    # Поля для файлов
    file_path = Column(String(500), nullable=True, comment="Путь к загруженному файлу")
    file_name = Column(String(255), nullable=True, comment="Оригинальное имя файла")
    file_size = Column(Integer, nullable=True, comment="Размер файла в байтах")
    
    # student_id - связь с таблицей пользователей (студентов)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # assignment_id - связь с таблицей заданий
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Связи
    student = relationship("User", foreign_keys=[student_id])
    assignment = relationship("Assignment", back_populates="submissions")
    grades = relationship("Grade", back_populates="submission", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="submission", cascade="all, delete-orphan")
    
    @validates('submitted_at')
    def validate_submitted_at(self, key, submitted_at):
        """
        Валидация времени сдачи и автоматическое определение статуса.
        Если сдача происходит после дедлайна, статус устанавливается как "late".
        """
        if self.assignment and submitted_at > self.assignment.due_date:
            self.status = SubmissionStatus.late
        else:
            # Если статус уже не "graded", устанавливаем "submitted"
            if self.status != SubmissionStatus.graded:
                self.status = SubmissionStatus.submitted
        
        return submitted_at