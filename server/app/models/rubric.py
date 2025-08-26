from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Rubric(Base):
    """Rubric used for grading assignments (Canvas-like)."""
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_points = Column(Float, nullable=False, default=100.0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="rubrics")
    criteria = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id"), nullable=False, index=True)
    description = Column(String(500), nullable=False)
    points = Column(Float, nullable=False, default=0.0)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    rubric = relationship("Rubric", back_populates="criteria")


