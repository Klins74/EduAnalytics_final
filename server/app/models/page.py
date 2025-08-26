from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Page(Base):
    """Course Page (Canvas-like wiki page)."""
    __tablename__ = "pages"
    __table_args__ = (
        UniqueConstraint("course_id", "slug", name="uq_pages_course_slug"),
    )

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    published = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="pages")
    author = relationship("User", foreign_keys=[author_id])




