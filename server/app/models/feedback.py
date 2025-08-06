from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Feedback(Base):
    """Модель для комментариев и обратной связи к заданиям."""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    submission_id = Column(
        Integer, 
        ForeignKey("submissions.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    submission = relationship("Submission", back_populates="feedbacks")
    author = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<Feedback(id={self.id}, submission_id={self.submission_id}, author_id={self.user_id})>"