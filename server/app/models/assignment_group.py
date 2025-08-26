from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AssignmentGroup(Base):
    """Groups assignments within a course with a weight (Canvas-like)."""
    __tablename__ = "assignment_groups"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    weight = Column(Float, default=1.0)  # contribution to total grade
    drop_lowest = Column(Integer, default=0)
    is_weighted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="assignment_groups")
    assignments = relationship("Assignment", back_populates="assignment_group")




