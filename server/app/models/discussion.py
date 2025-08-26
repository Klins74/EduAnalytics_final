from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DiscussionTopic(Base):
    """Discussion topic in a course (Canvas-like)."""
    __tablename__ = "discussion_topics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    published = Column(Boolean, default=True, nullable=False)
    locked = Column(Boolean, default=False, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="discussion_topics")
    author = relationship("User", foreign_keys=[author_id])
    entries = relationship("DiscussionEntry", back_populates="topic", cascade="all, delete-orphan")


class DiscussionEntry(Base):
    """Entry (post) in a discussion topic."""
    __tablename__ = "discussion_entries"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("discussion_topics.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("discussion_entries.id"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    topic = relationship("DiscussionTopic", back_populates="entries")
    user = relationship("User", foreign_keys=[user_id])
    parent = relationship("DiscussionEntry", remote_side=[id])




