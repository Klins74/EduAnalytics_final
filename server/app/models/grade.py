from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Grade(Base):
    """
    Модель оценки за сдачу задания.
    
    Представляет оценку, которую преподаватель ставит студенту
    за выполненное задание. Связана с конкретной сдачей (submission).
    
    Attributes:
        id: Уникальный идентификатор оценки
        score: Оценка от 0 до 100
        feedback: Комментарий преподавателя
        graded_at: Время выставления оценки
        graded_by: ID преподавателя, выставившего оценку
        submission_id: ID сдачи задания, за которую выставлена оценка
    """
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=False)  # Оценка от 0 до 100
    feedback = Column(String(1000), nullable=True)  # Комментарий преподавателя
    graded_at = Column(DateTime, default=func.now(), nullable=False)
    
    # graded_by - ID преподавателя, выставившего оценку
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # submission_id - связь с таблицей сдач заданий
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)

    # Связи
    grader = relationship("User", foreign_keys=[graded_by])
    submission = relationship("Submission", back_populates="grades")