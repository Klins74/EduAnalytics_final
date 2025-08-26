from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Module(Base):
    """Course Module groups content items in a sequenced flow (Canvas-like)."""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    position = Column(Integer, default=0, index=True)
    published = Column(Boolean, default=False, nullable=False)
    unlock_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    course = relationship("Course", back_populates="modules")
    items = relationship("ModuleItem", back_populates="module", cascade="all, delete-orphan")


class ModuleItemType(str, PyEnum):
    """Supported module item types (subset of Canvas)."""
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"
    PAGE = "page"
    FILE = "file"
    DISCUSSION = "discussion"
    EXTERNAL_URL = "external_url"


class ModuleItem(Base):
    """An item inside a Module which points to some content by type and id."""
    __tablename__ = "module_items"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    type = Column(Enum(ModuleItemType), nullable=False)
    content_id = Column(Integer, nullable=True, index=True)  # points to resource id (assignment, quiz, etc.)
    position = Column(Integer, default=0, index=True)
    indent = Column(Integer, default=0)
    published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    module = relationship("Module", back_populates="items")




